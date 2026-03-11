"""
EPDL Executor - Main K-PEW execution engine
Orchestrates 8-stage pipeline with error handling
"""

import logging
import time

from ...errors.exceptions import PhaseBlockedError
from .stage_runner import StageRunner

logger = logging.getLogger(__name__)


class EPDLExecutor:
    """Main EPDL plan executor (8 stages)"""

    def __init__(self):
        self.stage_runner = StageRunner()

    async def execute(self, epdl_json: dict, context: dict) -> dict:
        """Execute EPDL plan through 8 stages (I-3.5: Async-unified)

        Args:
            epdl_json: EPDL plan from LLM (or dict for now)
            context: Execution context (breakers, panel, etc)

        Returns:
            {
                "success": bool,
                "stages": List[Dict],  # Results from each stage
                "blocking_errors": List[EstimatorError],
                "total_duration_ms": int
            }

        Raises:
            PhaseBlockedError: If any stage has blocking errors
        """
        start = time.time()

        results = []
        all_blocking_errors = []

        # Run all 8 stages
        for stage_num in range(8):
            logger.info(f"Running Stage {stage_num}")

            # I-3.5: Await async run_stage() to ensure execution
            stage_result = await self.stage_runner.run_stage(
                stage_number=stage_num, plan=epdl_json, context=context
            )

            results.append(stage_result)

            # Check for blocking errors
            if stage_result.get("blocking_errors"):
                all_blocking_errors.extend(stage_result["blocking_errors"])

                # Block next stages
                logger.error(
                    f"Stage {stage_num} ({stage_result['stage_name']}) blocked with "
                    f"{len(stage_result['blocking_errors'])} errors"
                )

                # Raise PhaseBlockedError
                raise PhaseBlockedError(
                    blocking_errors=all_blocking_errors,
                    current_phase=stage_result["stage_name"],
                    next_phase=(
                        f"Stage {stage_num + 1}" if stage_num < 7 else "Complete"
                    ),
                )

        total_duration_ms = int((time.time() - start) * 1000)

        success = all(r["status"] in ["success", "skipped"] for r in results)

        # I-3.2: Determine overall_status (str enum for test compatibility)
        if all_blocking_errors:
            overall_status = "blocked"
        elif any(r["status"] == "error" for r in results):
            overall_status = "partial_success"
        else:
            overall_status = "success"

        logger.info(
            f"Pipeline execution complete: success={success}, "
            f"overall_status={overall_status}, duration={total_duration_ms}ms"
        )

        return {
            "success": success,
            "overall_status": overall_status,  # I-3.2: Added for test compatibility
            "stages": results,
            "blocking_errors": all_blocking_errors,
            "total_duration_ms": total_duration_ms,
        }
