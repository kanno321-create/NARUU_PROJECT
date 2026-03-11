"""
EPDL Verb Implementations

I-3.2: ExecutionCtx 기반 리팩토링
Each verb calls REAL core engines - NO MOCKS, NO DUMMIES.
Verbs are execution units that translate DSL to actual computation.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ...core.ssot.errors import raise_error
from ...engine.breaker_placer import BreakerInput, BreakerPlacer, PanelSpec
from ...engine.context import ExecutionCtx
from ...engine.enclosure_solver import EnclosureSolver
from ...engine.excel_generator import ExcelGenerator
from ...engine.pdf_converter import PDFConverter

# I-3.2: Import new BaseVerb and ExecutionCtx
from ...engine.verbs.base import BaseVerb as NewBaseVerb
from ...errors import error_codes
from ...models.enclosure import (
    AccessorySpec,
    BreakerSpec,
    CustomerRequirements,
)

logger = logging.getLogger(__name__)


class VerbExecutionError(Exception):
    """Verb execution error"""

    pass


class Verb(ABC):
    """Abstract base class for EPDL verbs"""

    @abstractmethod
    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute verb with context

        Args:
            context: Execution context with input data

        Returns:
            Execution results (stored back in context)

        Raises:
            VerbExecutionError: If execution fails
        """
        pass

    def validate_context(
        self, context: dict[str, Any], required_keys: list[str]
    ) -> None:
        """
        Validate required keys in context

        Args:
            context: Execution context
            required_keys: List of required keys

        Raises:
            VerbExecutionError: If required keys missing
        """
        missing = [key for key in required_keys if key not in context]
        if missing:
            raise VerbExecutionError(
                f"Missing required context keys: {missing}. "
                f"Available keys: {list(context.keys())}"
            )


class PickEnclosureVerb(NewBaseVerb):
    """
    PICK_ENCLOSURE - Calculate optimal enclosure size

    I-3.2: ExecutionCtx 기반 리팩토링
    """

    def __init__(self, params, *, ctx: ExecutionCtx):
        """
        Initialize PickEnclosureVerb

        Args:
            params: Verb params (SimpleNamespace for now, Pydantic later)
            ctx: ExecutionCtx (SSOT, DB, Logger, state)
        """
        super().__init__(params, ctx=ctx)
        self.solver = EnclosureSolver()

    async def run(self) -> None:
        """
        Execute enclosure calculation using REAL EnclosureSolver

        I-3.2:
        - async def run() (no asyncio.run wrapper needed)
        - ctx.state에서 입력 조회
        - ctx.state에 결과 저장 ("enclosure", "dimensions")
        """
        self.log_execution_start()

        # Validate context (필수 키 확인)
        self.validate_context(["main_breaker", "branch_breakers"])

        panel_name = getattr(self.params, "panel", "default")
        strategy = getattr(self.params, "strategy", "auto")

        self.logger.info(f"PICK_ENCLOSURE: panel={panel_name}, strategy={strategy}")

        # Get input data from ctx.state
        main_breaker = self.ctx.get_state("main_breaker")
        branch_breakers = self.ctx.get_state("branch_breakers")
        accessories = self.ctx.get_state("accessories", [])
        customer_reqs = self.ctx.get_state("customer_requirements", {})

        # Convert to proper types if needed (I-3.2: field mapping)
        if isinstance(main_breaker, dict):
            # Map 'current' -> 'current_a', 'frame' -> 'frame_af'
            main_breaker_mapped = {
                "id": main_breaker.get("id", "MAIN"),
                "model": main_breaker.get("model", "UNKNOWN"),  # Default if missing
                "poles": main_breaker.get("poles"),
                "current_a": main_breaker.get("current")
                or main_breaker.get("current_a"),
                "frame_af": main_breaker.get("frame") or main_breaker.get("frame_af"),
            }
            main_breaker = BreakerSpec(**main_breaker_mapped)

        branch_breaker_specs = []
        for idx, b in enumerate(branch_breakers):
            if isinstance(b, dict):
                # Map 'current' -> 'current_a', 'frame' -> 'frame_af'
                b_mapped = {
                    "id": b.get("id", f"BR{idx+1}"),
                    "model": b.get("model", "UNKNOWN"),
                    "poles": b.get("poles"),
                    "current_a": b.get("current") or b.get("current_a"),
                    "frame_af": b.get("frame") or b.get("frame_af"),
                }
                branch_breaker_specs.append(BreakerSpec(**b_mapped))
            else:
                branch_breaker_specs.append(b)

        accessory_specs = []
        for a in accessories:
            if isinstance(a, dict):
                accessory_specs.append(AccessorySpec(**a))
            else:
                accessory_specs.append(a)

        customer_requirements = (
            CustomerRequirements(**customer_reqs) if customer_reqs else None
        )

        # Call REAL enclosure solver (NO MOCKS!)
        # I-3.2: EnclosureSolver.solve() is async
        try:
            result = await self.solver.solve(
                main_breaker=main_breaker,
                branch_breakers=branch_breaker_specs,
                accessories=accessory_specs,
                customer_requirements=customer_requirements,
            )
        except Exception as e:
            self.logger.error(f"EnclosureSolver failed: {e}")
            raise_error(
                error_codes.ENC_002,
                "Enclosure calculation failed",
                hint="EnclosureSolver.solve() exception",
                meta={"panel": panel_name, "exception": str(e)},
            )

        # I-3.2: Store result in ctx.state (규약 준수)
        # "enclosure": 외함 객체
        # "dimensions": 외함 치수 {width_mm, height_mm, depth_mm}
        self.ctx.set_state("enclosure", result)

        if hasattr(result, "dimensions"):
            self.ctx.set_state("dimensions", result.dimensions)
        elif hasattr(result, "model_dump"):
            dumped = result.model_dump()
            if "dimensions" in dumped:
                self.ctx.set_state("dimensions", dumped["dimensions"])

        # fit_score 저장 (ASSERT verb에서 사용)
        fit_score = (
            result.quality_gate.actual if hasattr(result, "quality_gate") else None
        )
        if fit_score is not None:
            self.ctx.set_state("fit_score", fit_score)

        fit_score_str = f"{fit_score:.2f}" if fit_score is not None else "N/A"
        self.logger.info(
            f"PICK_ENCLOSURE success: panel={panel_name}, " f"fit_score={fit_score_str}"
        )

        self.log_execution_end(success=True)


class PlaceVerb(NewBaseVerb):
    """
    PLACE - Place breakers on panel

    I-3.2: ExecutionCtx 기반 리팩토링
    """

    def __init__(self, params, *, ctx: ExecutionCtx):
        """
        Initialize PlaceVerb

        Args:
            params: Verb params (SimpleNamespace for now, Pydantic later)
            ctx: ExecutionCtx (SSOT, DB, Logger, state)
        """
        super().__init__(params, ctx=ctx)
        self.placer = BreakerPlacer()

    async def run(self) -> None:
        """
        Execute breaker placement using REAL BreakerPlacer

        I-3.2:
        - Validate "enclosure" exists (선행조건)
        - ctx.state에서 입력 조회 ('breakers', 'panel_spec')
        - ctx.state["placements"]에 결과 추가
        """
        self.log_execution_start()

        # I-3.2: Validate enclosure exists (선행조건)
        if not self.ctx.has_state("enclosure"):
            raise_error(
                error_codes.VERB_001,
                "Missing enclosure for PlaceVerb",
                hint="Place requires selected enclosure (run PICK_ENCLOSURE first)",
                meta={
                    "verb": "PlaceVerb",
                    "requires": ["enclosure"],
                    "available": list(self.ctx.state.keys()),
                },
            )

        # Validate context (필수 키 확인)
        self.validate_context(["breakers", "panel_spec"])

        panel_name = getattr(self.params, "panel", "default")
        algo = getattr(self.params, "algo", "heuristic")
        seed = getattr(self.params, "seed", 42)

        self.logger.info(f"PLACE: panel={panel_name}, algo={algo}, seed={seed}")

        # Get input data from ctx.state
        breakers_data = self.ctx.get_state("breakers")
        panel_data = self.ctx.get_state("panel_spec")

        # Convert to BreakerInput list (I-3.2: field mapping)
        # BreakerInput only needs: id, poles, current_a, width_mm, height_mm, depth_mm, breaker_type
        # (No 'frame_af' or 'model' - those are for BreakerSpec)
        breakers = []
        for b in breakers_data:
            if isinstance(b, dict):
                # Map dict keys to BreakerInput fields (물리적 치수만)
                b_mapped = {
                    "id": b.get("id", "UNKNOWN"),
                    "poles": b.get("poles", 2),
                    "current_a": b.get("current_a") or b.get("current", 20),
                    "width_mm": b.get("width_mm", 50),
                    "height_mm": b.get("height_mm", 130),
                    "depth_mm": b.get("depth_mm", 60),
                    "breaker_type": b.get("breaker_type", "normal"),
                }
                breakers.append(BreakerInput(**b_mapped))
            else:
                breakers.append(b)

        # Convert to PanelSpec
        if isinstance(panel_data, dict):
            panel = PanelSpec(**panel_data)
        else:
            panel = panel_data

        # Call REAL placer (NO MOCKS!)
        try:
            placements = self.placer.place(breakers=breakers, panel=panel)
        except Exception as e:
            self.logger.error(f"BreakerPlacer failed: {e}")
            raise_error(
                error_codes.LAY_003,
                "Breaker placement failed",
                hint="BreakerPlacer.place() exception",
                meta={"panel": panel_name, "exception": str(e)},
            )

        # I-3.2: Store result in ctx.state (규약 준수)
        # "placements": list에 누적 (여러 패널 가능)
        existing_placements = self.ctx.get_state("placements", [])
        existing_placements.extend(placements)
        self.ctx.set_state("placements", existing_placements)

        self.logger.info(
            f"PLACE success: panel={panel_name}, "
            f"placed {len(placements)} breakers, total={len(existing_placements)}"
        )

        self.log_execution_end(success=True)


class RebalanceVerb(Verb):
    """REBALANCE - Optimize phase balance"""

    def __init__(self, params=None):
        # I-3: params optional with defaults (SSOT migration pending)
        from types import SimpleNamespace

        self.params = params or SimpleNamespace(
            panel="default", method="swap_local", max_iter=10
        )
        self.placer = BreakerPlacer()

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute phase rebalancing using REAL BreakerPlacer"""

        panel_name = self.params.panel
        method = self.params.method
        max_iter = self.params.max_iter

        logger.info(
            f"REBALANCE: panel={panel_name}, method={method}, max_iter={max_iter}"
        )

        # Get placements from context
        placements_key = f"placements_{panel_name}"
        if placements_key not in context:
            raise VerbExecutionError(
                f"No placements found for panel '{panel_name}'. "
                f"Run PLACE verb first."
            )

        placements = context[placements_key]

        # Call rebalancing method
        if method == "swap_local":
            rebalanced = self.placer.rebalance_local(placements, max_iter)
        elif method == "swap_window":
            rebalanced = self.placer.rebalance_window(placements, max_iter)
        else:
            raise VerbExecutionError(f"Unknown rebalance method: {method}")

        # Update context
        context[placements_key] = rebalanced

        # Calculate imbalance
        imbalance = self.placer.calculate_phase_imbalance(rebalanced)

        return {
            "status": "success",
            "panel": panel_name,
            "method": method,
            "iterations": max_iter,
            "final_imbalance_pct": imbalance,
        }


class TryVerb(Verb):
    """TRY - MILP fallback optimization"""

    def __init__(self, params=None):
        # I-3: params optional with defaults (SSOT migration pending)
        from types import SimpleNamespace

        self.params = params or SimpleNamespace(algo="cpsat", timeout_ms=30000)
        self.placer = BreakerPlacer()

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute MILP optimization fallback"""

        algo = self.params.algo
        timeout_ms = self.params.timeout_ms

        logger.info(f"TRY: algo={algo}, timeout_ms={timeout_ms}")

        # Validate context
        self.validate_context(context, ["breakers", "panel_spec"])

        breakers_data = context["breakers"]
        panel_data = context["panel_spec"]

        # Convert to proper types
        breakers = []
        for b in breakers_data:
            if isinstance(b, dict):
                breakers.append(BreakerInput(**b))
            else:
                breakers.append(b)

        if isinstance(panel_data, dict):
            panel = PanelSpec(**panel_data)
        else:
            panel = panel_data

        # Call MILP solver (OR-Tools CP-SAT)
        try:
            placements = self.placer.place_with_cpsat(
                breakers=breakers, panel=panel, timeout_seconds=timeout_ms / 1000.0
            )

            return {
                "status": "success",
                "algo": algo,
                "timeout_ms": timeout_ms,
                "placements": [
                    {
                        "breaker_id": p.breaker_id,
                        "position": p.position,
                        "phase": p.phase,
                    }
                    for p in placements
                ],
            }

        except Exception as e:
            logger.warning(f"MILP fallback failed: {e}")
            return {
                "status": "failed",
                "algo": algo,
                "error": str(e),
                "fallback_used": True,
            }


class DocExportVerb(Verb):
    """DOC_EXPORT - Generate documents (PDF/XLSX/JSON)"""

    def __init__(self, params):
        self.params = params

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute document generation using REAL generators"""

        formats = self.params.fmt

        logger.info(f"DOC_EXPORT: formats={formats}")

        # Validate context
        self.validate_context(context, ["estimate_data"])

        estimate_data = context["estimate_data"]
        output_dir = Path(context.get("output_dir", "outputs"))
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_files = []

        # Excel generation
        if "xlsx" in formats:
            try:
                excel_gen = ExcelGenerator()
                xlsx_path = (
                    output_dir / f"{estimate_data.get('quote_id', 'estimate')}.xlsx"
                )

                # Call REAL Excel generator
                excel_gen.generate(estimate_data, str(xlsx_path))
                generated_files.append(str(xlsx_path))
                logger.info(f"Excel generated: {xlsx_path}")

            except Exception as e:
                logger.error(f"Excel generation failed: {e}")
                raise VerbExecutionError(f"Excel generation failed: {e}") from e

        # PDF generation
        if "pdf" in formats:
            try:
                # First generate Excel if not already done
                if "xlsx" not in formats:
                    excel_gen = ExcelGenerator()
                    temp_xlsx = (
                        output_dir
                        / f"{estimate_data.get('quote_id', 'estimate')}_temp.xlsx"
                    )
                    excel_gen.generate(estimate_data, str(temp_xlsx))
                    xlsx_path = temp_xlsx
                else:
                    xlsx_path = Path(generated_files[0])

                # Convert to PDF
                pdf_converter = PDFConverter()
                pdf_path = (
                    output_dir / f"{estimate_data.get('quote_id', 'estimate')}.pdf"
                )
                pdf_converter.convert(str(xlsx_path), str(pdf_path))
                generated_files.append(str(pdf_path))
                logger.info(f"PDF generated: {pdf_path}")

            except Exception as e:
                logger.error(f"PDF generation failed: {e}")
                raise VerbExecutionError(f"PDF generation failed: {e}") from e

        # JSON export
        if "json" in formats:
            try:
                import json

                json_path = (
                    output_dir / f"{estimate_data.get('quote_id', 'estimate')}.json"
                )

                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(estimate_data, f, ensure_ascii=False, indent=2)

                generated_files.append(str(json_path))
                logger.info(f"JSON exported: {json_path}")

            except Exception as e:
                logger.error(f"JSON export failed: {e}")
                raise VerbExecutionError(f"JSON export failed: {e}") from e

        return {"status": "success", "formats": formats, "files": generated_files}


class AssertVerb(Verb):
    """ASSERT - Quality gate validation"""

    def __init__(self, params):
        self.params = params
        self.placer = BreakerPlacer()

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute quality gate assertions"""

        imbalance_max = self.params.imbalance_max
        violations_max = self.params.violations_max
        fit_score_min = self.params.fit_score_min

        logger.info(
            f"ASSERT: imbalance_max={imbalance_max}, "
            f"violations_max={violations_max}, fit_score_min={fit_score_min}"
        )

        failures = []

        # Check phase imbalance
        if imbalance_max is not None:
            for key in context.keys():
                if key.startswith("placements_"):
                    placements = context[key]
                    imbalance = self.placer.calculate_phase_imbalance(placements)

                    if imbalance > imbalance_max:
                        failures.append(
                            f"Phase imbalance {imbalance:.2%} exceeds limit {imbalance_max:.2%} "
                            f"for panel {key.replace('placements_', '')}"
                        )

        # Check clearance violations
        if violations_max is not None:
            for key in context.keys():
                if key.startswith("placements_"):
                    placements = context[key]
                    violations = self.placer.check_clearance_violations(placements)

                    if violations > violations_max:
                        failures.append(
                            f"Clearance violations {violations} exceeds limit {violations_max} "
                            f"for panel {key.replace('placements_', '')}"
                        )

        # Check fit score
        if fit_score_min is not None:
            for key in context.keys():
                if key.startswith("enclosure_"):
                    enclosure = context[key]
                    # I-3: QualityGateResult uses 'actual' field, not 'fit_score'
                    fit_score = (
                        enclosure.quality_gate.actual
                        if hasattr(enclosure, "quality_gate")
                        else None
                    )

                    if fit_score is not None and fit_score < fit_score_min:
                        failures.append(
                            f"Fit score {fit_score:.2f} below minimum {fit_score_min:.2f} "
                            f"for panel {key.replace('enclosure_', '')}"
                        )

        # Return results
        if failures:
            return {
                "status": "failed",
                "assertions": {
                    "imbalance_max": imbalance_max,
                    "violations_max": violations_max,
                    "fit_score_min": fit_score_min,
                },
                "failures": failures,
            }
        else:
            return {
                "status": "success",
                "assertions": {
                    "imbalance_max": imbalance_max,
                    "violations_max": violations_max,
                    "fit_score_min": fit_score_min,
                },
                "message": "All quality gates passed",
            }


# Verb factory
def create_verb(verb_name: str, params: Any) -> Verb:
    """
    Create verb instance from name and params

    Args:
        verb_name: Verb name (PLACE, REBALANCE, etc.)
        params: Verb parameters (Pydantic model)

    Returns:
        Verb instance

    Raises:
        VerbExecutionError: If unknown verb
    """
    verb_map = {
        "PLACE": PlaceVerb,
        "REBALANCE": RebalanceVerb,
        "TRY": TryVerb,
        "PICK_ENCLOSURE": PickEnclosureVerb,
        "DOC_EXPORT": DocExportVerb,
        "ASSERT": AssertVerb,
    }

    if verb_name not in verb_map:
        raise VerbExecutionError(f"Unknown verb: {verb_name}")

    return verb_map[verb_name](params)
