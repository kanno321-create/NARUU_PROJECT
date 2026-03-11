"""
K-PEW API Router - Plan-First Estimation Workflow

REST API endpoints for EPDL (Estimation Plan Description Language) workflow:
1. POST /v1/estimate/plan - Generate EPDL plan using Claude LLM
2. POST /v1/estimate/execute - Execute EPDL plan through 8-stage pipeline
3. GET /v1/estimate/{estimate_id} - Retrieve estimate details

REAL Supabase PostgreSQL integration - NO MOCKS, NO DUMMIES
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json
import logging
import uuid

# Database connection
from api.db import get_db

# K-PEW components
from kis_estimator_core.kpew.execution.executor import EPDLExecutor
from kis_estimator_core.errors.exceptions import PhaseBlockedError, EstimatorError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/estimate", tags=["kpew"])


# ============================================================================
# Request/Response Models
# ============================================================================


class BreakerSpec(BaseModel):
    """I-3.5: Breaker specification validation model"""

    poles: int = Field(..., ge=2, le=4, description="극수 (2/3/4)")
    current: int = Field(..., gt=0, le=1000, description="전류 (A)")
    frame: int = Field(..., gt=0, le=1000, description="프레임 (AF)")

    class Config:
        # I-3.5: Enable validation on assignment
        validate_assignment = True

    def model_post_init(self, __context):
        """I-3.5: Validate frame >= current (business rule)"""
        if self.frame < self.current:
            raise ValueError(
                f"Frame ({self.frame}AF) must be >= Current ({self.current}A). "
                f"Invalid breaker specification."
            )


class PlanRequest(BaseModel):
    """EPDL Plan Generation Request"""

    customer_name: str = Field(..., min_length=1, description="고객사명")
    project_name: str = Field(..., min_length=1, description="프로젝트명")
    enclosure_type: str = Field(default="옥내노출", description="외함 종류")
    breaker_brand: str = Field(default="상도차단기", description="차단기 브랜드")
    main_breaker: BreakerSpec = Field(..., description="메인 차단기 스펙")
    branch_breakers: List[BreakerSpec] = Field(
        ..., min_length=0, description="분기 차단기 목록"
    )
    accessories: List[Dict[str, Any]] = Field(
        default_factory=list, description="부속자재"
    )


class PlanResponse(BaseModel):
    """VerbSpec Plan Response (I-3.4)"""

    plan_id: str = Field(..., description="견적 ID (EST-YYYYMMDDHHMMSSffffff)")
    estimate_id: str = Field(..., description="견적 ID (동일)")
    verb_specs: List[Dict] = Field(..., description="생성된 VerbSpec 리스트")
    specs_count: int = Field(..., description="VerbSpec 개수")
    is_valid: bool = Field(..., description="스키마 검증 통과 여부")
    created_at: str = Field(..., description="생성 시간 (ISO 8601)")


class ExecuteRequest(BaseModel):
    """Plan Execution Request"""

    plan_id: str = Field(..., description="견적 ID (EST-YYYYMMDDHHMMSSffffff)")
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="실행 컨텍스트 (선택사항)"
    )


class ExecuteResponse(BaseModel):
    """Plan Execution Response"""

    estimate_id: str = Field(..., description="견적 ID")
    status: str = Field(..., description="실행 상태 (success|error|blocked)")
    stages_completed: int = Field(..., description="완료된 단계 수")
    total_stages: int = Field(..., description="전체 단계 수 (8)")
    excel_path: Optional[str] = Field(None, description="생성된 Excel 파일 경로")
    quality_gates: Dict[str, Any] = Field(..., description="품질 게이트 결과")
    total_duration_ms: int = Field(..., description="총 실행 시간 (ms)")
    blocking_errors: List[Dict[str, Any]] = Field(
        default_factory=list, description="차단 에러 목록"
    )


class EstimateDetailResponse(BaseModel):
    """Estimate Detail Response"""

    estimate_id: str
    plan: Dict
    created_at: Optional[str]
    execution_history: List[Dict[str, Any]]


# ============================================================================
# POST /v1/estimate/plan - Generate EPDL Plan
# POST /v1/estimate - Deprecated alias for backward compatibility
# ============================================================================


@router.post(
    "/estimate",
    response_model=PlanResponse,
    status_code=201,
    deprecated=True,
    summary="[DEPRECATED] Use /v1/estimate/plan instead",
)
@router.post("/plan", response_model=PlanResponse, status_code=201)
async def generate_plan(req: PlanRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate VerbSpec plan (I-3.4)

    Flow:
    1. Create VerbSpec list from user requirements (deterministic, no LLM)
    2. Validate VerbSpecs against SSOT models
    3. Save to Supabase (verb_plans table)
    4. Return plan_id and verb_specs

    Args:
        req: User requirements (customer, project, breakers, accessories)
        db: Database session

    Returns:
        PlanResponse with plan_id, verb_specs, specs_count

    Raises:
        HTTPException 400: VerbSpec validation failed
        HTTPException 500: Database error or internal error
    """
    try:
        # 1. Import dependencies (I-3.4)
        from kis_estimator_core.services.plan_service import PlanService
        from kis_estimator_core.repos.plan_repo import PlanRepo

        # 2. Generate VerbSpec list (deterministic, no LLM)
        try:
            # I-3.5: Convert Pydantic models to dict for PlanService
            verb_specs = PlanService.create_verb_specs(
                customer_name=req.customer_name,
                project_name=req.project_name,
                enclosure_type=req.enclosure_type,
                breaker_brand=req.breaker_brand,
                main_breaker=req.main_breaker.model_dump(),
                branch_breakers=[b.model_dump() for b in req.branch_breakers],
                accessories=req.accessories,
            )
        except Exception as e:
            logger.error(f"VerbSpec creation failed: {e}")
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "VERBSPEC_CREATION_ERROR",
                    "message": f"Failed to create VerbSpecs: {str(e)}",
                    "hint": "Check request parameters",
                    "traceId": str(uuid.uuid4()),
                    "meta": {
                        "dedupKey": "verbspec-creation-error",
                        "exception": type(e).__name__,
                    },
                },
            )

        # 3. Validate VerbSpecs
        is_valid, errors = PlanService.validate_verb_specs(verb_specs)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "VERBSPEC_VALIDATION_ERROR",
                    "message": "VerbSpec validation failed",
                    "errors": errors,
                    "hint": "Review VerbSpec structure",
                    "traceId": str(uuid.uuid4()),
                    "meta": {"dedupKey": "verbspec-validation-error"},
                },
            )

        # 4. Generate plan_id with microseconds for uniqueness (I-3.4)
        # Format: EST-YYYYMMDDHHMMSSffffff (20 chars + microseconds)
        plan_id = f"EST-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        # 5. Save to Supabase (REAL database insert!)
        try:
            repo = PlanRepo(db)
            await repo.save_plan(plan_id, verb_specs)
        except Exception as e:
            logger.error(f"Database insert failed: {e}")
            # 5xx Fail Fast: 즉시 반환, 재시도 없음
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "DB_INSERT_ERROR",
                    "message": f"Failed to save plan to database: {str(e)}",
                    "hint": "Check database connection and verb_plans table schema",
                    "traceId": str(uuid.uuid4()),
                    "meta": {
                        "dedupKey": "plan-db-insert-error",
                        "exception": type(e).__name__,
                    },
                },
            )

        # 6. Return response
        logger.info(
            f"Plan generated successfully: {plan_id}, " f"specs_count={len(verb_specs)}"
        )

        return PlanResponse(
            plan_id=plan_id,
            estimate_id=plan_id,
            verb_specs=verb_specs,
            specs_count=len(verb_specs),
            is_valid=True,
            created_at=datetime.now().isoformat() + "Z",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in generate_plan: {e}")
        # 5xx Fail Fast: 즉시 반환, 재시도 없음
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"Unexpected error in generate_plan: {str(e)}",
                "hint": "Check server logs for details",
                "traceId": str(uuid.uuid4()),
                "meta": {
                    "dedupKey": "generate-plan-internal-error",
                    "exception": type(e).__name__,
                },
            },
        )


# ============================================================================
# POST /v1/estimate/execute - Execute EPDL Plan
# ============================================================================


@router.post("/execute", response_model=ExecuteResponse, status_code=200)
async def execute_plan(req: ExecuteRequest, db: AsyncSession = Depends(get_db)):
    """
    Execute VerbSpec plan through 8-stage pipeline (I-3.4)

    Flow:
    1. Load VerbSpec list from Supabase (verb_plans table via PlanRepo)
    2. Execute 8-stage pipeline (Stage 0-7)
    3. Save execution_history to Supabase
    4. Return execution results

    Args:
        req: Execution request (plan_id, context)
        db: Database session

    Returns:
        ExecuteResponse with status, stages_completed, blocking_errors

    Raises:
        HTTPException 404: Plan not found
        HTTPException 400: Plan validation failed
        HTTPException 500: Execution error
    """
    try:
        # 1. Load VerbSpec list from PlanRepo (I-3.4)
        from kis_estimator_core.repos.plan_repo import PlanRepo

        repo = PlanRepo(db)
        verb_specs = await repo.load_plan(req.plan_id)

        if not verb_specs:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "PLAN_NOT_FOUND",
                    "message": f"Plan {req.plan_id} not found in database",
                    "hint": "Check plan_id or generate a new plan with POST /v1/estimate/plan",
                    "traceId": str(uuid.uuid4()),
                    "meta": {"dedupKey": "plan-not-found", "plan_id": req.plan_id},
                },
            )

        # 2. Wrap VerbSpecs for Executor compatibility
        # Executor expects {"steps": [...]} structure
        epdl_json = {"steps": verb_specs}

        # 2. Build execution context
        context = req.context or {}

        # Add default context if not provided
        if "enclosure_type" not in context:
            context["enclosure_type"] = "옥내노출"
        if "breaker_brand" not in context:
            context["breaker_brand"] = "상도차단기"

        # 3. Execute plan (REAL 8-stage execution!)
        executor = EPDLExecutor()

        try:
            # I-3.5: Await async execute()
            exec_result = await executor.execute(epdl_json, context)

            # 4. Save execution history to Supabase
            for stage in exec_result["stages"]:
                stage_errors = stage.get("errors", [])
                blocking_errors = stage.get("blocking_errors", [])

                # Extract error codes
                error_codes = [
                    e.error_code.code if isinstance(e, EstimatorError) else str(e)
                    for e in stage_errors
                ]

                # Build blocking errors JSON
                blocking_errors_json = [
                    {
                        "code": e.error_code.code,
                        "message": e.error_code.message,
                        "phase": e.phase,
                        "hint": e.error_code.hint,
                    }
                    for e in blocking_errors
                    if isinstance(e, EstimatorError)
                ]

                await db.execute(
                    text(
                        """
                        INSERT INTO execution_history
                        (estimate_id, stage_number, stage_name, status,
                         started_at, completed_at, duration_ms, error_codes,
                         blocking_errors, stage_output, quality_gate_passed)
                        VALUES (:estimate_id, :stage_number, :stage_name, :status,
                                timezone('utc', now()), timezone('utc', now()), :duration_ms,
                                :error_codes, :blocking_errors, :stage_output, :quality_gate_passed)
                    """
                    ),
                    {
                        "estimate_id": req.plan_id,
                        "stage_number": stage["stage_number"],
                        "stage_name": stage["stage_name"],
                        "status": stage["status"],
                        "duration_ms": stage.get("duration_ms", 0),
                        "error_codes": error_codes,
                        "blocking_errors": json.dumps(
                            blocking_errors_json, ensure_ascii=False
                        ),
                        "stage_output": json.dumps(
                            stage.get("output", {}), ensure_ascii=False
                        ),
                        "quality_gate_passed": stage.get("quality_gate_passed", False),
                    },
                )

            await db.commit()

            # 5. Return success response
            logger.info(
                f"Pipeline execution complete: {req.plan_id}, "
                f"success={exec_result['success']}, "
                f"duration={exec_result['total_duration_ms']}ms"
            )

            return ExecuteResponse(
                estimate_id=req.plan_id,
                status="success" if exec_result["success"] else "error",
                stages_completed=len(exec_result["stages"]),
                total_stages=8,
                excel_path=None,
                quality_gates={
                    "all_passed": exec_result["success"],
                    "stages": [
                        {
                            "stage": s["stage_number"],
                            "name": s["stage_name"],
                            "passed": s.get("quality_gate_passed", False),
                        }
                        for s in exec_result["stages"]
                    ],
                },
                total_duration_ms=exec_result["total_duration_ms"],
                blocking_errors=[],
            )

        except PhaseBlockedError as e:
            # Stage blocked by errors - save partial execution
            logger.warning(
                f"Pipeline blocked at {e.current_phase}: "
                f"{len(e.blocking_errors)} blocking errors"
            )

            # Save partial execution history
            # (StageRunner already saved individual stages, just commit)
            await db.commit()

            return ExecuteResponse(
                estimate_id=req.plan_id,
                status="blocked",
                stages_completed=0,  # Will be set from actual execution
                total_stages=8,
                excel_path=None,
                quality_gates={
                    "all_passed": False,
                    "stages": [],
                },  # I-3.4: Include stages field even when blocked
                total_duration_ms=0,
                blocking_errors=[
                    {
                        "code": err.error_code.code,
                        "message": err.error_code.message,
                        "phase": err.phase,
                        "hint": err.error_code.hint,
                    }
                    for err in e.blocking_errors
                ],
            )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Execution error: {e}")
        # 5xx Fail Fast: 즉시 반환, 재시도 없음
        raise HTTPException(
            status_code=500,
            detail={
                "code": "EXECUTION_ERROR",
                "message": f"Execution failed: {str(e)}",
                "hint": "Check server logs and database connection",
                "traceId": str(uuid.uuid4()),
                "meta": {"dedupKey": "execution-error", "exception": type(e).__name__},
            },
        )


# ============================================================================
# GET /v1/estimate/{estimate_id} - Retrieve Estimate
# ============================================================================


@router.get("/{estimate_id}", response_model=EstimateDetailResponse)
async def get_estimate(estimate_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve estimate details (plan + execution history)

    Args:
        estimate_id: 견적 ID (EST-YYYYMMDDHHMMSSffffff)
        db: Database session

    Returns:
        EstimateDetailResponse with plan and execution_history

    Raises:
        HTTPException 404: Estimate not found
    """
    try:
        # Load plan from epdl_plans
        plan_result = await db.execute(
            text(
                "SELECT plan_json, created_at FROM epdl_plans WHERE estimate_id = :id"
            ),
            {"id": estimate_id},
        )
        plan_row = plan_result.fetchone()

        if not plan_row:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NOT_FOUND",
                    "message": f"Estimate {estimate_id} not found",
                    "hint": "Check estimate_id or generate a new plan",
                    "traceId": str(uuid.uuid4()),
                    "meta": {
                        "dedupKey": "estimate-not-found",
                        "estimate_id": estimate_id,
                    },
                },
            )

        plan_json_str, created_at = plan_row

        # Load execution history
        history_result = await db.execute(
            text(
                """
                SELECT stage_number, stage_name, status, duration_ms,
                       quality_gate_passed, error_codes
                FROM execution_history
                WHERE estimate_id = :id
                ORDER BY stage_number
            """
            ),
            {"id": estimate_id},
        )
        history_rows = history_result.fetchall()

        return EstimateDetailResponse(
            estimate_id=estimate_id,
            plan=json.loads(plan_json_str),
            created_at=created_at.isoformat() + "Z" if created_at else None,
            execution_history=[
                {
                    "stage": row[0],
                    "name": row[1],
                    "status": row[2],
                    "duration_ms": row[3],
                    "quality_gate_passed": row[4],
                    "error_codes": row[5] or [],
                }
                for row in history_rows
            ],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving estimate {estimate_id}: {e}")
        # 5xx Fail Fast: 즉시 반환, 재시도 없음
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"Failed to retrieve estimate: {str(e)}",
                "hint": "Check server logs and database connection",
                "traceId": str(uuid.uuid4()),
                "meta": {
                    "dedupKey": "get-estimate-error",
                    "estimate_id": estimate_id,
                    "exception": type(e).__name__,
                },
            },
        )
