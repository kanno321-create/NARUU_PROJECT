"""
K-PEW Stage Runner - 8-Stage Execution Engine
Calls REAL engines (NO MOCKS!)
"""

import logging
import time
from typing import Any

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error

from ...engine.breaker_placer import BreakerPlacer
from ...errors import error_codes
from ...errors.exceptions import EstimatorError
from ..gates.validator import GateValidator
from ._async_adapter import invoke_maybe_async

logger = logging.getLogger(__name__)


class StageRunner:
    """Run individual K-PEW stages with quality gates"""

    def __init__(self):
        self.gate_validator = GateValidator()

    async def run_stage(
        self, stage_number: int, plan, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Run single stage (I-2: Async-unified)

        IMPORTANT: This method is now async and uses invoke_maybe_async() adapter
        for safe execution of both sync and async stage functions.

        Args:
            stage_number: 0~7
            plan: EPDLPlan object (or dict for now)
            context: Execution context

        Returns:
            {
                "stage_number": int,
                "stage_name": str,
                "status": "success"|"error"|"blocked"|"skipped",
                "errors": List[EstimatorError],
                "blocking_errors": List[EstimatorError],
                "output": Dict,
                "quality_gate_passed": bool,
                "duration_ms": int
            }
        """
        stage_map = {
            0: self._stage_0_pre_validation,
            1: self._stage_1_enclosure,
            2: self._stage_2_layout,
            3: self._stage_3_balance,
            4: self._stage_4_bom,
            5: self._stage_5_cost,
            6: self._stage_6_format,
            7: self._stage_7_quality,
        }

        stage_func = stage_map[stage_number]

        # I-2: Use invoke_maybe_async() adapter for safe async/sync execution
        # This prevents "asyncio.run() cannot be called from a running event loop" errors
        return await invoke_maybe_async(stage_func, plan, context)

    def _stage_0_pre_validation(self, plan, context: dict) -> dict:
        """Stage 0: Pre-Validation (INP-001~005)"""
        start = time.time()

        errors = []

        # INP-001: 외함 종류 정보 누락
        if not context.get("enclosure_type"):
            errors.append(
                EstimatorError(
                    error_code=error_codes.INP_001, phase="Stage 0: Pre-Validation"
                )
            )

        # INP-002: 외함 설치 위치 정보 누락
        if not context.get("install_location"):
            errors.append(
                EstimatorError(
                    error_code=error_codes.INP_002, phase="Stage 0: Pre-Validation"
                )
            )

        # INP-004: 메인 차단기 정보 누락
        if not context.get("main_breaker"):
            errors.append(
                EstimatorError(
                    error_code=error_codes.INP_004, phase="Stage 0: Pre-Validation"
                )
            )

        # INP-005: 분기 차단기 정보 누락
        if (
            not context.get("branch_breakers")
            or len(context.get("branch_breakers", [])) == 0
        ):
            errors.append(
                EstimatorError(
                    error_code=error_codes.INP_005, phase="Stage 0: Pre-Validation"
                )
            )

        duration_ms = max(1, int((time.time() - start) * 1000))

        blocking_errors = [e for e in errors if e.error_code.blocking]

        return {
            "stage_number": 0,
            "stage_name": "Pre-Validation",
            "status": "error" if blocking_errors else "success",
            "errors": errors,
            "blocking_errors": blocking_errors,
            "output": {},
            "quality_gate_passed": len(blocking_errors) == 0,
            "duration_ms": duration_ms,
        }

    async def _stage_1_enclosure(self, plan, context: dict) -> dict:
        """Stage 1: Enclosure (ENC-001~003, CAT-001) - I-2: Async

        I-3.2: ExecutionCtx 어댑터 패턴
        Calls REAL EnclosureSolver (NO MOCKS!)
        """
        start = time.time()

        errors = []

        # Check if PICK_ENCLOSURE verb exists in plan
        has_pick_verb = False
        if isinstance(plan, dict) and "steps" in plan:
            for step in plan.get("steps", []):
                if isinstance(step, dict) and "PICK_ENCLOSURE" in step:
                    has_pick_verb = True
                    break

        if not has_pick_verb:
            # No PICK_ENCLOSURE verb → skip stage
            return {
                "stage_number": 1,
                "stage_name": "Enclosure",
                "status": "skipped",
                "errors": [],
                "blocking_errors": [],
                "output": {},
                "quality_gate_passed": True,
                "duration_ms": 0,
            }

        # I-3.5: Wrap entire verb execution in try-catch (exception handling 확장)
        try:
            # I-3.2: Execute PickEnclosureVerb if present
            if has_pick_verb:
                from types import SimpleNamespace

                from kis_estimator_core.engine.context import ExecutionCtx
                from kis_estimator_core.engine.verbs.factory import from_spec

                # I-3.3: No need to register (REGISTRY is fixed in factory.py)

                # Extract PICK_ENCLOSURE params
                pick_step = next(
                    (s for s in plan.get("steps", []) if "PICK_ENCLOSURE" in s), {}
                )
                pick_params = pick_step.get("PICK_ENCLOSURE", {})

                # Create ExecutionCtx with ssot (SimpleNamespace for compatibility)
                ssot = SimpleNamespace()
                ctx = ExecutionCtx(ssot=ssot, db=None, logger=logger, state={})

                # Copy context data to ctx.state
                for key in [
                    "main_breaker",
                    "branch_breakers",
                    "accessories",
                    "enclosure_type",
                    "material",
                    "thickness",
                ]:
                    if key in context:
                        ctx.set_state(key, context[key])

                # Create and run verb
                spec = {"verb_name": "PICK_ENCLOSURE", "params": pick_params}
                verb = from_spec(spec, ctx=ctx)
                await verb.run()

                # Get result from ctx.state
                if not ctx.has_state("enclosure"):
                    raise_error(
                        ErrorCode.ENC_002,
                        "PickEnclosureVerb did not produce enclosure",
                        hint="Verb must store result in ctx.state['enclosure']",
                    )

                result = ctx.get_state("enclosure")

                # Copy ctx.state results to context
                context["enclosure_result"] = result
                context["enclosure"] = result
                if ctx.has_state("dimensions"):
                    context["dimensions"] = ctx.get_state("dimensions")
                if ctx.has_state("fit_score"):
                    context["fit_score"] = ctx.get_state("fit_score")

            # Validate fit_score (result already obtained from PickEnclosureVerb)
            result = context.get("enclosure_result")
            if not result:
                raise_error(
                    ErrorCode.ENC_002,
                    "Enclosure result missing after PickEnclosureVerb",
                    hint="PickEnclosureVerb should have stored result in context",
                )

            fit_score = (
                result.quality_gate.actual if hasattr(result, "quality_gate") else 0.0
            )
            is_valid, gate_errors = self.gate_validator.validate_fit_score(fit_score)
            errors.extend(gate_errors)

            # I-3.2: Store result in context for next stages (핵심!)
            context["enclosure_result"] = result
            context["enclosure"] = result  # I-3.2: BOM phase에서 사용
            if hasattr(result, "dimensions"):
                context["dimensions"] = result.dimensions

            duration_ms = max(1, int((time.time() - start) * 1000))

            blocking_errors = [e for e in errors if e.error_code.blocking]

            return {
                "stage_number": 1,
                "stage_name": "Enclosure",
                "status": "error" if blocking_errors else "success",
                "errors": errors,
                "blocking_errors": blocking_errors,
                "output": {"enclosure_result": result},
                "quality_gate_passed": is_valid,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            logger.error(f"Stage 1 failed: {e}")
            errors.append(
                EstimatorError(
                    error_code=error_codes.ENC_002,
                    phase="Stage 1: Enclosure",
                    details={"exception": str(e)},
                )
            )

            duration_ms = max(1, int((time.time() - start) * 1000))

            return {
                "stage_number": 1,
                "stage_name": "Enclosure",
                "status": "error",
                "errors": errors,
                "blocking_errors": errors,
                "output": {},
                "quality_gate_passed": False,
                "duration_ms": duration_ms,
            }

    async def _stage_2_layout(self, plan, context: dict) -> dict:
        """Stage 2: Layout (LAY-002, LAY-003) - I-2: Async

        I-3.2: ExecutionCtx 어댑터 패턴
        Calls REAL BreakerPlacer (NO MOCKS!)
        """
        start = time.time()

        errors = []

        # Check if PLACE verb exists in plan
        has_place_verb = False
        if isinstance(plan, dict) and "steps" in plan:
            for step in plan.get("steps", []):
                if isinstance(step, dict) and "PLACE" in step:
                    has_place_verb = True
                    break

        if not has_place_verb:
            # No PLACE verb → skip stage
            return {
                "stage_number": 2,
                "stage_name": "Layout",
                "status": "skipped",
                "errors": [],
                "blocking_errors": [],
                "output": {},
                "quality_gate_passed": True,
                "duration_ms": 0,
            }

        # I-3.5: Wrap entire verb execution in try-catch (exception handling 확장)
        try:
            # I-3.2: Execute PlaceVerb if present
            if has_place_verb:
                from types import SimpleNamespace

                from kis_estimator_core.engine.context import ExecutionCtx
                from kis_estimator_core.engine.verbs.factory import from_spec

                # I-3.3: No need to register (REGISTRY is fixed in factory.py)

                # Extract PLACE params
                place_step = next(
                    (s for s in plan.get("steps", []) if "PLACE" in s), {}
                )
                place_params = place_step.get("PLACE", {})

                # Create ExecutionCtx with ssot (SimpleNamespace for compatibility)
                ssot = SimpleNamespace()
                ctx = ExecutionCtx(ssot=ssot, db=None, logger=logger, state={})

                # Prepare breakers data if not present
                # BreakerInput needs: id, poles, current_a, width_mm, height_mm, depth_mm, breaker_type
                if "breakers" not in context:
                    breakers_data = []
                    if context.get("main_breaker"):
                        mb = context["main_breaker"]
                        breakers_data.append(
                            {
                                "id": "MAIN",
                                "poles": mb.get("poles", 3),
                                "current_a": mb.get("current", 100),
                                "width_mm": mb.get("width_mm", 100),
                                "height_mm": mb.get("height_mm", 130),
                                "depth_mm": mb.get("depth_mm", 60),
                                "breaker_type": mb.get("breaker_type", "normal"),
                            }
                        )
                    for idx, bb in enumerate(context.get("branch_breakers", [])):
                        breakers_data.append(
                            {
                                "id": f"BR{idx+1}",
                                "poles": bb.get("poles", 2),
                                "current_a": bb.get("current", 20),
                                "width_mm": bb.get("width_mm", 50),
                                "height_mm": bb.get("height_mm", 130),
                                "depth_mm": bb.get("depth_mm", 60),
                                "breaker_type": bb.get("breaker_type", "normal"),
                            }
                        )
                    context["breakers"] = breakers_data

                # Prepare panel_spec if not present (derive from enclosure)
                if "panel_spec" not in context:
                    enclosure = context.get("enclosure") or context.get(
                        "enclosure_result"
                    )
                    if enclosure:
                        # Extract dimensions from enclosure
                        if hasattr(enclosure, "dimensions"):
                            dims = enclosure.dimensions
                            panel_spec = {
                                "width_mm": dims.width_mm,
                                "height_mm": dims.height_mm,
                                "depth_mm": dims.depth_mm,
                                "clearance_mm": 50,
                            }
                        elif hasattr(enclosure, "model_dump"):
                            dumped = enclosure.model_dump()
                            dims = dumped.get("dimensions", {})
                            panel_spec = {
                                "width_mm": dims.get("width_mm", 600),
                                "height_mm": dims.get("height_mm", 800),
                                "depth_mm": dims.get("depth_mm", 200),
                                "clearance_mm": 50,
                            }
                        else:
                            # Fallback default
                            panel_spec = {
                                "width_mm": 600,
                                "height_mm": 800,
                                "depth_mm": 200,
                                "clearance_mm": 50,
                            }
                        context["panel_spec"] = panel_spec

                # Copy context data to ctx.state
                # PlaceVerb requires: breakers, panel_spec, enclosure (선행조건)
                for key in ["breakers", "panel_spec", "enclosure", "enclosure_result"]:
                    if key in context:
                        ctx.set_state(key, context[key])

                # Create and run verb
                spec = {"verb_name": "PLACE", "params": place_params}
                verb = from_spec(spec, ctx=ctx)
                await verb.run()

                # Get result from ctx.state
                if not ctx.has_state("placements"):
                    raise_error(
                        ErrorCode.LAY_003,
                        "PlaceVerb did not produce placements",
                        hint="Verb must store result in ctx.state['placements']",
                    )

                placements = ctx.get_state("placements")

                # Copy ctx.state results to context
                context["placements"] = placements

                duration_ms = max(1, int((time.time() - start) * 1000))

                # Validate placements (basic check)
                is_valid = len(placements) > 0
                if not is_valid:
                    errors.append(
                        EstimatorError(
                            error_code=error_codes.LAY_002,  # I-3.5: Use existing error code
                            phase="Stage 2: Layout",
                            details={"error": "PlaceVerb returned empty placements"},
                        )
                    )

                blocking_errors = [e for e in errors if e.error_code.blocking]

                return {
                    "stage_number": 2,
                    "stage_name": "Layout",
                    "status": "error" if blocking_errors else "success",
                    "errors": errors,
                    "blocking_errors": blocking_errors,
                    "output": {"placements": placements},
                    "quality_gate_passed": is_valid,
                    "duration_ms": duration_ms,
                }

        except Exception as e:
            logger.error(f"Stage 2 failed: {e}")
            errors.append(
                EstimatorError(
                    error_code=error_codes.LAY_002,  # I-3.5: Use existing error code (LAY_003 doesn't exist)
                    phase="Stage 2: Layout",
                    details={"exception": str(e)},
                )
            )

            duration_ms = max(1, int((time.time() - start) * 1000))

            return {
                "stage_number": 2,
                "stage_name": "Layout",
                "status": "error",
                "errors": errors,
                "blocking_errors": errors,
                "output": {},
                "quality_gate_passed": False,
                "duration_ms": duration_ms,
            }

    def _stage_3_balance(self, plan, context: dict) -> dict:
        """Stage 3: Balance (LAY-001, BUG-007)

        Calls REAL BreakerPlacer.validate() (NO MOCKS!)
        """
        start = time.time()

        errors = []

        # Check if REBALANCE verb exists in plan
        has_rebalance_verb = False
        if isinstance(plan, dict) and "steps" in plan:
            for step in plan.get("steps", []):
                if isinstance(step, dict) and "REBALANCE" in step:
                    has_rebalance_verb = True
                    break

        if not has_rebalance_verb:
            return {
                "stage_number": 3,
                "stage_name": "Balance",
                "status": "skipped",
                "errors": [],
                "blocking_errors": [],
                "output": {},
                "quality_gate_passed": True,
                "duration_ms": 0,
            }

        # Call REAL BreakerPlacer.validate() (NO MOCKS!)
        try:
            placements = context.get("placements", [])
            if not placements:
                raise_error(
                    ErrorCode.E_INTERNAL, "No placements found. Stage 2 must run first."
                )

            placer = BreakerPlacer()
            validation_result = placer.validate(placements=placements)

            # Extract phase loads from validation result
            # BreakerPlacer.validate() returns ValidationResult with phase_imbalance_pct
            phase_imbalance_pct = validation_result.phase_imbalance_pct

            # Calculate phase loads for gate validator
            # Note: We need actual phase loads, not just percentage
            # Let's recalculate from placements
            phase_loads = {"L1": 0.0, "L2": 0.0, "L3": 0.0}
            for p in placements:
                if (
                    hasattr(p, "position") and p.position.get("row") != 0
                ):  # Exclude main breaker
                    if hasattr(p, "poles") and p.poles >= 3:
                        per_phase = p.current_a / p.poles
                        phase_loads["L1"] += per_phase
                        phase_loads["L2"] += per_phase
                        phase_loads["L3"] += per_phase
                    elif hasattr(p, "phase") and p.phase in phase_loads:
                        phase_loads[p.phase] += p.current_a

            # Validate balance
            is_valid, gate_errors = self.gate_validator.validate_balance(phase_loads)
            errors.extend(gate_errors)

            duration_ms = max(1, int((time.time() - start) * 1000))

            blocking_errors = [e for e in errors if e.error_code.blocking]

            return {
                "stage_number": 3,
                "stage_name": "Balance",
                "status": "error" if blocking_errors else "success",
                "errors": errors,
                "blocking_errors": blocking_errors,
                "output": {
                    "validation_result": validation_result,
                    "phase_loads": phase_loads,
                    "phase_imbalance_pct": phase_imbalance_pct,
                },
                "quality_gate_passed": is_valid,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            logger.error(f"Stage 3 failed: {e}")
            errors.append(
                EstimatorError(
                    error_code=error_codes.BUG_007,
                    phase="Stage 3: Balance",
                    details={"exception": str(e)},
                )
            )

            duration_ms = max(1, int((time.time() - start) * 1000))

            return {
                "stage_number": 3,
                "stage_name": "Balance",
                "status": "error",
                "errors": errors,
                "blocking_errors": errors,
                "output": {},
                "quality_gate_passed": False,
                "duration_ms": duration_ms,
            }

    def _stage_4_bom(self, plan, context: dict) -> dict:
        """Stage 4: BOM (BUG-001~006, CAT-002~003)

        I-3.2: 선행조건 가드 추가 (enclosure 필수)
        Generates Bill of Materials (차단기 목록, 부속자재)
        Calls REAL DataTransformer (NO MOCKS!)
        """
        start = time.time()

        errors = []

        try:
            # Import REAL DataTransformer (NO MOCKS!)
            from kis_estimator_core.engine.data_transformer import DataTransformer

            # I-3.2b: SSOT DTO 정규화 (단일 진입점)
            from kis_estimator_core.engine.normalizers import normalize_ctx_state

            logger.info("[I-3.2b] Normalizing context before BOM stage...")
            normalize_ctx_state(context)
            logger.info("[I-3.2b] Context normalization complete")

            # I-3.2: 선행조건 가드 (enclosure 필수)
            enclosure = context.get("enclosure")
            if enclosure is None:
                logger.error("BOM Phase blocked: enclosure missing")
                # Use errors.append() instead of raise_error() for proper test verification
                errors.append(
                    EstimatorError(
                        error_code=error_codes.ENC_002,
                        phase="Stage 4: BOM",
                        details={
                            "error": "Enclosure missing",
                            "hint": "PickEnclosure must run before BOM phase",
                            "available_keys": list(context.keys()),
                        },
                    )
                )
                return {
                    "stage_number": 4,
                    "stage_name": "BOM",
                    "status": "error",
                    "errors": errors,
                    "blocking_errors": errors,
                    "output": {},
                    "quality_gate_passed": False,
                    "duration_ms": max(1, int((time.time() - start) * 1000)),
                }

            # Get required data from context (이미 DTO로 정규화됨)
            placements = context.get("placements", [])
            enclosure_result = (
                context.get("enclosure_result") or enclosure
            )  # I-3.2: Fallback
            breakers = context.get("breakers", [])  # I-3.2b: List[BreakerInput]

            if not placements:
                logger.warning(
                    "No placements found in context - skipping BOM generation"
                )
                return {
                    "stage_number": 4,
                    "stage_name": "BOM",
                    "status": "skipped",
                    "errors": [],
                    "blocking_errors": [],
                    "output": {},
                    "quality_gate_passed": True,
                    "duration_ms": max(1, int((time.time() - start) * 1000)),
                }

            if not enclosure_result:
                errors.append(
                    EstimatorError(
                        error_code=error_codes.ENC_002,
                        phase="Stage 4: BOM",
                        details={"error": "Enclosure result missing from context"},
                    )
                )
                return {
                    "stage_number": 4,
                    "stage_name": "BOM",
                    "status": "error",
                    "errors": errors,
                    "blocking_errors": errors,
                    "output": {},
                    "quality_gate_passed": False,
                    "duration_ms": max(1, int((time.time() - start) * 1000)),
                }

            # REAL DataTransformer with Supabase CatalogService
            transformer = DataTransformer()

            # Extract customer info from context or plan
            customer_name = context.get("customer_name", "고객명")
            project_name = context.get("project_name", "")

            # Transform to EstimateData (BOM + Cost calculation)
            estimate_data = transformer.transform(
                placements=placements,
                enclosure_result=enclosure_result,
                breakers=breakers,
                customer_name=customer_name,
                project_name=project_name,
            )

            # Store estimate_data in context for next stages
            context["estimate_data"] = estimate_data

            logger.info(f"BOM generated: {len(estimate_data.panels)} panel(s)")

            # No quality gates for BOM stage (just data transformation)
            duration_ms = max(1, int((time.time() - start) * 1000))

            return {
                "stage_number": 4,
                "stage_name": "BOM",
                "status": "success",
                "errors": errors,
                "blocking_errors": [],
                "output": {"estimate_data": estimate_data},
                "quality_gate_passed": True,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            logger.error(f"Stage 4 failed: {e}", exc_info=True)
            errors.append(
                EstimatorError(
                    error_code=error_codes.BUG_001,
                    phase="Stage 4: BOM",
                    details={"exception": str(e)},
                )
            )

            duration_ms = max(1, int((time.time() - start) * 1000))

            return {
                "stage_number": 4,
                "stage_name": "BOM",
                "status": "error",
                "errors": errors,
                "blocking_errors": errors,
                "output": {},
                "quality_gate_passed": False,
                "duration_ms": duration_ms,
            }

    def _stage_5_cost(self, plan, context: dict) -> dict:
        """Stage 5: Cost (ACC-001~004, BUS-001~004)

        Calculates cost based on BOM
        Cost calculation is ALREADY DONE in Stage 4 (DataTransformer)
        This stage validates and aggregates costs
        """
        start = time.time()

        errors = []

        try:
            # Cost is already calculated in Stage 4 (DataTransformer.transform)
            # DataTransformer uses REAL Supabase CatalogService for pricing
            estimate_data = context.get("estimate_data")

            if not estimate_data:
                logger.warning("No estimate_data found - skipping cost validation")
                return {
                    "stage_number": 5,
                    "stage_name": "Cost",
                    "status": "skipped",
                    "errors": [],
                    "blocking_errors": [],
                    "output": {},
                    "quality_gate_passed": True,
                    "duration_ms": max(1, int((time.time() - start) * 1000)),
                }

            # Aggregate costs from all panels
            total_cost = 0
            total_cost_with_vat = 0

            for panel in estimate_data.panels:
                panel_total = sum(item.amount for item in panel.items)
                total_cost += panel_total
                total_cost_with_vat += panel_total * 1.1

            logger.info(
                f"Cost calculated: {total_cost:,.0f} KRW "
                f"(VAT included: {total_cost_with_vat:,.0f} KRW)"
            )

            # Store costs in context
            context["total_cost"] = total_cost
            context["total_cost_with_vat"] = total_cost_with_vat

            # No quality gates for cost stage (validation is in Stage 7)
            duration_ms = max(1, int((time.time() - start) * 1000))

            return {
                "stage_number": 5,
                "stage_name": "Cost",
                "status": "success",
                "errors": errors,
                "blocking_errors": [],
                "output": {
                    "total_cost": total_cost,
                    "total_cost_with_vat": total_cost_with_vat,
                    "panel_count": len(estimate_data.panels),
                },
                "quality_gate_passed": True,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            logger.error(f"Stage 5 failed: {e}", exc_info=True)
            errors.append(
                EstimatorError(
                    error_code=error_codes.ACC_001,
                    phase="Stage 5: Cost",
                    details={"exception": str(e)},
                )
            )

            duration_ms = max(1, int((time.time() - start) * 1000))

            return {
                "stage_number": 5,
                "stage_name": "Cost",
                "status": "error",
                "errors": errors,
                "blocking_errors": errors,
                "output": {},
                "quality_gate_passed": False,
                "duration_ms": duration_ms,
            }

    def _stage_6_format(self, plan, context: dict) -> dict:
        """Stage 6: Format (CAL-001~002)

        Generates Excel/PDF documents
        Calls REAL EstimateFormatter (NO MOCKS!)
        """
        start = time.time()

        errors = []

        try:
            # Import REAL EstimateFormatter (NO MOCKS!)
            import tempfile
            from pathlib import Path

            from kis_estimator_core.engine.estimate_formatter import EstimateFormatter

            # Get estimate_data from context
            estimate_data = context.get("estimate_data")

            if not estimate_data:
                logger.warning("No estimate_data found - skipping format generation")
                return {
                    "stage_number": 6,
                    "stage_name": "Format",
                    "status": "skipped",
                    "errors": [],
                    "blocking_errors": [],
                    "output": {},
                    "quality_gate_passed": True,
                    "duration_ms": max(1, int((time.time() - start) * 1000)),
                }

            # Determine output path
            output_dir = context.get("output_dir")
            if not output_dir:
                # Use temp directory if no output_dir specified
                output_dir = Path(tempfile.gettempdir()) / "kis_estimates"
                output_dir.mkdir(exist_ok=True)
            else:
                output_dir = Path(output_dir)

            estimate_id = context.get("estimate_id", "TEMP")
            output_path = output_dir / f"{estimate_id}_estimate.xlsx"

            # REAL EstimateFormatter with template
            # Template path: 절대코어파일/견적서양식.xlsx
            formatter = EstimateFormatter()  # Uses default template path

            # Get required inputs from context
            placements = context.get("placements", [])
            enclosure_result = context.get("enclosure_result")
            breakers = context.get("breakers", [])

            # Format and generate Excel (REAL - NO MOCKS!)
            estimate_output = formatter.format(
                placements=placements,
                enclosure_result=enclosure_result,
                breakers=breakers,
                customer_name=context.get("customer_name", "고객명"),
                project_name=context.get("project_name", ""),
                output_path=output_path,
            )

            # Store file paths in context
            context["excel_path"] = str(estimate_output.excel_path)
            if estimate_output.pdf_path:
                context["pdf_path"] = str(estimate_output.pdf_path)

            logger.info(f"Format generated: {estimate_output.excel_path}")

            # Validate formula preservation (quality gate)
            validation_report = estimate_output.validation_report
            formula_preserved = validation_report.formula_preservation_rate >= 0.99

            if not formula_preserved:
                errors.append(
                    EstimatorError(
                        error_code=error_codes.CAL_001,
                        phase="Stage 6: Format",
                        details={
                            "formula_preservation_rate": validation_report.formula_preservation_rate,
                            "errors": validation_report.errors,
                        },
                    )
                )

            duration_ms = max(1, int((time.time() - start) * 1000))

            blocking_errors = [e for e in errors if e.error_code.blocking]

            return {
                "stage_number": 6,
                "stage_name": "Format",
                "status": "error" if blocking_errors else "success",
                "errors": errors,
                "blocking_errors": blocking_errors,
                "output": {
                    "excel_path": str(estimate_output.excel_path),
                    "pdf_path": (
                        str(estimate_output.pdf_path)
                        if estimate_output.pdf_path
                        else None
                    ),
                    "validation_report": validation_report,
                },
                "quality_gate_passed": formula_preserved,
                "duration_ms": duration_ms,
            }

        except FileNotFoundError as e:
            logger.error(f"Stage 6 failed - template not found: {e}")
            errors.append(
                EstimatorError(
                    error_code=error_codes.CAL_002,
                    phase="Stage 6: Format",
                    details={
                        "exception": str(e),
                        "error": "Template file not found (NO MOCKS!)",
                    },
                )
            )

            duration_ms = max(1, int((time.time() - start) * 1000))

            return {
                "stage_number": 6,
                "stage_name": "Format",
                "status": "error",
                "errors": errors,
                "blocking_errors": errors,
                "output": {},
                "quality_gate_passed": False,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            logger.error(f"Stage 6 failed: {e}", exc_info=True)
            errors.append(
                EstimatorError(
                    error_code=error_codes.CAL_001,
                    phase="Stage 6: Format",
                    details={"exception": str(e)},
                )
            )

            duration_ms = max(1, int((time.time() - start) * 1000))

            return {
                "stage_number": 6,
                "stage_name": "Format",
                "status": "error",
                "errors": errors,
                "blocking_errors": errors,
                "output": {},
                "quality_gate_passed": False,
                "duration_ms": duration_ms,
            }

    def _stage_7_quality(self, plan, context: dict) -> dict:
        """Stage 7: Quality (LAY-004)

        Final quality checks
        Validates all previous stages and overall system integrity
        REAL validation checks (NO MOCKS!)
        """
        start = time.time()

        errors = []
        warnings = []

        try:
            # Comprehensive quality validation across all stages
            logger.info("Running final quality checks...")

            # 1. Check Stage 1 (Enclosure) output
            enclosure_result = context.get("enclosure_result")
            if enclosure_result:
                # I-3.2b: quality_gate is QualityGateResult object, not dict
                quality_gate = getattr(enclosure_result, "quality_gate", None)
                if quality_gate:
                    fit_score = getattr(quality_gate, "actual", 0)
                else:
                    fit_score = 0

                if fit_score < 0.90:
                    errors.append(
                        EstimatorError(
                            error_code=error_codes.ENC_001,
                            phase="Stage 7: Quality",
                            details={"fit_score": fit_score, "threshold": 0.90},
                        )
                    )
                logger.info(f"Enclosure fit score: {fit_score:.2f}")

            # 2. Check Stage 2-3 (Layout + Balance) output
            placements = context.get("placements")
            if placements:
                # Validate phase balance
                phase_loads = {"L1": 0, "L2": 0, "L3": 0}
                for p in placements:
                    if hasattr(p, "position") and p.position.get("row") != 0:
                        if hasattr(p, "poles") and p.poles >= 3:
                            per_phase = p.current_a / p.poles
                            phase_loads["L1"] += per_phase
                            phase_loads["L2"] += per_phase
                            phase_loads["L3"] += per_phase
                        elif hasattr(p, "phase") and p.phase in phase_loads:
                            phase_loads[p.phase] += p.current_a

                max_load = max(phase_loads.values())
                min_load = min(phase_loads.values())
                imbalance = (
                    ((max_load - min_load) / max_load * 100) if max_load > 0 else 0
                )

                if imbalance > 4.0:
                    errors.append(
                        EstimatorError(
                            error_code=error_codes.LAY_001,
                            phase="Stage 7: Quality",
                            details={
                                "phase_imbalance_pct": imbalance,
                                "threshold": 4.0,
                            },
                        )
                    )
                elif imbalance > 3.0:
                    warnings.append(
                        f"Phase imbalance {imbalance:.1f}% (warning threshold: 3%)"
                    )

                logger.info(
                    f"Phase balance: {phase_loads}, imbalance: {imbalance:.2f}%"
                )

            # 3. Check Stage 4-5 (BOM + Cost) output
            estimate_data = context.get("estimate_data")
            total_cost = context.get("total_cost", 0)

            if estimate_data and total_cost > 0:
                logger.info(f"Total cost validated: {total_cost:,.0f} KRW")
            elif estimate_data and total_cost == 0:
                warnings.append("Total cost is zero - verify pricing data")

            # 4. Check Stage 6 (Format) output
            excel_path = context.get("excel_path")
            if excel_path:
                from pathlib import Path

                excel_file = Path(excel_path)
                if not excel_file.exists():
                    errors.append(
                        EstimatorError(
                            error_code=error_codes.CAL_002,
                            phase="Stage 7: Quality",
                            details={"error": f"Excel file not found: {excel_path}"},
                        )
                    )
                else:
                    file_size = excel_file.stat().st_size
                    logger.info(
                        f"Excel file validated: {excel_path} ({file_size} bytes)"
                    )

                    # Validate file size (should be > 10KB for real estimate)
                    if file_size < 10240:
                        warnings.append(
                            f"Excel file size suspiciously small: {file_size} bytes"
                        )

            # 5. Overall system integrity check
            required_context_keys = ["enclosure_result", "placements", "estimate_data"]
            missing_keys = [key for key in required_context_keys if key not in context]

            if missing_keys:
                warnings.append(f"Missing context data: {missing_keys}")

            # Determine final status
            has_blocking_errors = any(e.error_code.blocking for e in errors)

            duration_ms = max(1, int((time.time() - start) * 1000))

            blocking_errors = [e for e in errors if e.error_code.blocking]

            logger.info(
                f"Quality check complete: {len(errors)} errors, {len(warnings)} warnings"
            )

            return {
                "stage_number": 7,
                "stage_name": "Quality",
                "status": "error" if has_blocking_errors else "success",
                "errors": errors,
                "blocking_errors": blocking_errors,
                "output": {
                    "errors_count": len(errors),
                    "warnings_count": len(warnings),
                    "warnings": warnings,
                    "validation_summary": {
                        "enclosure_validated": bool(enclosure_result),
                        "placements_validated": bool(placements),
                        "cost_validated": total_cost > 0,
                        "excel_validated": bool(excel_path),
                    },
                },
                "quality_gate_passed": not has_blocking_errors,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            logger.error(f"Stage 7 failed: {e}", exc_info=True)
            errors.append(
                EstimatorError(
                    error_code=error_codes.LAY_004,
                    phase="Stage 7: Quality",
                    details={"exception": str(e)},
                )
            )

            duration_ms = max(1, int((time.time() - start) * 1000))

            return {
                "stage_number": 7,
                "stage_name": "Quality",
                "status": "error",
                "errors": errors,
                "blocking_errors": errors,
                "output": {},
                "quality_gate_passed": False,
                "duration_ms": duration_ms,
            }
