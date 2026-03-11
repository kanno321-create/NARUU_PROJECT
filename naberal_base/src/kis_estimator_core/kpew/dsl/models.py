"""
EPDL v0.9 Pydantic Models

DSL for KIS Estimator plan execution.
LLM generates ONLY plans (DSL) - NO calculations/numbers.
Core engines execute plans - ALL numerical computations.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error


class GlobalParams(BaseModel):
    """Global parameters for entire plan"""

    balance_limit: float = Field(
        ge=0, le=0.05, default=0.03, description="Maximum phase imbalance (0~5%)"
    )
    spare_ratio: float = Field(
        ge=0.1, le=0.3, default=0.2, description="Spare space ratio (10~30%)"
    )
    tab_policy: str = Field(
        default="2->1&2 | 3+->1&3", description="Excel tab parsing policy"
    )


class PlaceParams(BaseModel):
    """PLACE verb parameters - Request breaker placement"""

    panel: str = Field(description="Panel name to place breakers")
    algo: Literal["greedy"] = Field(default="greedy", description="Placement algorithm")
    seed: int | None = Field(
        default=42, description="Random seed for reproducibility"
    )


class RebalanceParams(BaseModel):
    """REBALANCE verb parameters - Request phase balance optimization"""

    panel: str = Field(description="Panel name to rebalance")
    method: Literal["swap_local", "swap_window"] = Field(
        description="Rebalancing method"
    )
    max_iter: int = Field(ge=1, le=1000, default=100, description="Maximum iterations")


class TryParams(BaseModel):
    """TRY verb parameters - Request MILP fallback optimization"""

    algo: Literal["milp"] = Field(default="milp", description="Optimization algorithm")
    timeout_ms: int = Field(
        ge=100, le=5000, default=1500, description="Timeout in milliseconds"
    )


class PickEnclosureParams(BaseModel):
    """PICK_ENCLOSURE verb parameters - Request enclosure calculation"""

    panel: str = Field(description="Panel name for enclosure")
    strategy: Literal["min_size_with_spare", "cost_then_size"] = Field(
        description="Enclosure selection strategy"
    )


class DocExportParams(BaseModel):
    """DOC_EXPORT verb parameters - Request document generation"""

    fmt: list[Literal["pdf", "xlsx", "json"]] = Field(
        min_length=1, description="Output formats"
    )

    @field_validator("fmt")
    @classmethod
    def unique_formats(cls, v: list[str]) -> list[str]:
        """Ensure unique formats"""
        if len(v) != len(set(v)):
            raise_error(ErrorCode.E_INTERNAL, "Duplicate formats not allowed")
        return v


class AssertParams(BaseModel):
    """ASSERT verb parameters - Define quality gate"""

    imbalance_max: float | None = Field(
        default=0.03, ge=0, le=0.05, description="Maximum allowed phase imbalance"
    )
    violations_max: int | None = Field(
        default=0, ge=0, description="Maximum allowed clearance violations"
    )
    fit_score_min: float | None = Field(
        default=0.90, ge=0, le=1.0, description="Minimum required fit score"
    )


class EPDLStep(BaseModel):
    """Single execution step with exactly ONE verb"""

    PLACE: PlaceParams | None = None
    REBALANCE: RebalanceParams | None = None
    TRY: TryParams | None = None
    PICK_ENCLOSURE: PickEnclosureParams | None = None
    DOC_EXPORT: DocExportParams | None = None
    ASSERT: AssertParams | None = None

    @field_validator(
        "PLACE",
        "REBALANCE",
        "TRY",
        "PICK_ENCLOSURE",
        "DOC_EXPORT",
        "ASSERT",
        mode="before",
    )
    @classmethod
    def validate_verb_params(cls, v, info):
        """Validate verb parameters"""
        # Just pass through for validation
        return v

    def model_post_init(self, __context):
        """Validate exactly one verb after model initialization"""
        verbs = ["PLACE", "REBALANCE", "TRY", "PICK_ENCLOSURE", "DOC_EXPORT", "ASSERT"]

        non_none_count = sum(1 for verb in verbs if getattr(self, verb) is not None)

        if non_none_count == 0:
            raise_error(ErrorCode.E_INTERNAL, "Step must have exactly one verb")
        if non_none_count > 1:
            raise_error(ErrorCode.E_INTERNAL, "Step can have only one verb")

    def get_verb_name(self) -> str:
        """Get the active verb name in this step"""
        verbs = ["PLACE", "REBALANCE", "TRY", "PICK_ENCLOSURE", "DOC_EXPORT", "ASSERT"]

        for verb in verbs:
            if getattr(self, verb) is not None:
                return verb

        raise_error(ErrorCode.E_INTERNAL, "No active verb found in step")

    def get_verb_params(self) -> BaseModel:
        """Get the active verb parameters"""
        verb_name = self.get_verb_name()
        return getattr(self, verb_name)


class EPDLPlan(BaseModel):
    """Complete EPDL plan with global params and steps"""

    global_params: GlobalParams = Field(alias="global")
    steps: list[EPDLStep] = Field(min_length=1)

    class Config:
        populate_by_name = True  # Allow both 'global' and 'global_params'

    def get_verb_sequence(self) -> list[str]:
        """Get ordered list of verb names in plan"""
        return [step.get_verb_name() for step in self.steps]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with 'global' key"""
        return {
            "global": self.global_params.model_dump(),
            "steps": [
                {step.get_verb_name(): step.get_verb_params().model_dump()}
                for step in self.steps
            ],
        }
