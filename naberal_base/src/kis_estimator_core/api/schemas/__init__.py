"""
API Schemas Package

OpenAPI 3.1 스키마 기반 Pydantic 모델들
"""

from kis_estimator_core.api.schemas.catalog import (
    AccessoryCatalogItem,
    AccessoryCatalogResponse,
    BreakerCatalogItem,
    BreakerCatalogResponse,
    EnclosureCatalogItem,
    EnclosureCatalogResponse,
)
from kis_estimator_core.api.schemas.estimates import (
    AccessoryInput,
    # Input Schemas
    BreakerInput,
    CustomSize,
    # Response Schemas
    DocumentUrls,
    EnclosureInput,
    EstimateOptions,
    EstimateRequest,
    EstimateResponse,
    EvidencePack,
    PanelInput,
    PipelineResults,
    # Pipeline Results
    Stage1EnclosureResult,
    Stage2BreakerResult,
    Stage3FormatResult,
    Stage4CoverResult,
    Stage5DocLintResult,
    # Validation
    ValidationChecks,
    ValidationError,
    ValidationResponse,
)
from kis_estimator_core.api.schemas.health import HealthResponse

__all__ = [
    # Health
    "HealthResponse",
    # Catalog
    "BreakerCatalogItem",
    "BreakerCatalogResponse",
    "EnclosureCatalogItem",
    "EnclosureCatalogResponse",
    "AccessoryCatalogItem",
    "AccessoryCatalogResponse",
    # Estimate Input
    "BreakerInput",
    "AccessoryInput",
    "CustomSize",
    "EnclosureInput",
    "PanelInput",
    "EstimateOptions",
    "EstimateRequest",
    # Pipeline Results
    "Stage1EnclosureResult",
    "Stage2BreakerResult",
    "Stage3FormatResult",
    "Stage4CoverResult",
    "Stage5DocLintResult",
    "PipelineResults",
    # Validation
    "ValidationChecks",
    # Response
    "DocumentUrls",
    "EvidencePack",
    "EstimateResponse",
    "ValidationError",
    "ValidationResponse",
]
