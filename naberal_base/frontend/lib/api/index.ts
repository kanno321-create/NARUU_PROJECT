/**
 * KIS Estimator API
 * Unified API exports for frontend consumption
 */

// Client
export { apiClient, ApiClient, ApiError } from './client';

// Health
export * from './health';

// Catalog
export * from './catalog';

// Estimates
export * from './estimates';

// Quotes
export * from './quotes';

// AI Chat
export * from './ai-chat';

// Re-export types for convenience
export type {
  ApiError as ApiErrorType,
  PaginatedResponse,
  ApiResponse,
  HealthCheckResponse,
  ValidationError,
  ValidationResult,
} from '../types/api';

export type {
  BreakerCatalog,
  EnclosureCatalog,
  AccessoryCatalog,
  BreakerFilters,
  EnclosureFilters,
  AccessoryFilters,
  CatalogStats,
} from '../types/catalog';

export type {
  EstimateRequest,
  EstimateResponse,
  ValidateEstimateRequest,
  ValidateEstimateResponse,
  EstimateListItem,
  PanelInput,
  BreakerInput,
  AccessoryInput,
  EnclosureInput,
  ValidationCheck,
  PipelineResult,
  EvidenceInfo,
} from '../types/estimate';

export type {
  QuoteCreateRequest,
  QuoteUpdateRequest,
  QuoteResponse,
  QuoteApproveRequest,
  QuoteApproveResponse,
  QuotePdfResponse,
  QuoteShareUrlResponse,
  QuoteListItem,
  QuoteStatus,
} from '../types/quote';

export type {
  ChatMessage,
  ChatRequest,
  ChatResponse,
  AiModel,
  AiIntent,
} from './ai-chat';
