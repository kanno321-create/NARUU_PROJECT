/**
 * Core API Types
 * Contract-First response wrappers and common interfaces
 */

export interface ApiError {
  code: string;
  message: string;
  hint?: string;
  traceId?: string;
  meta?: {
    dedupKey?: string;
    [key: string]: unknown;
  };
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ApiResponse<T> {
  data: T;
  meta?: {
    timestamp: string;
    traceId?: string;
    [key: string]: unknown;
  };
}

export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version?: string;
  uptime?: number;
  checks?: {
    database?: { status: string; latency?: number };
    cache?: { status: string; latency?: number };
    [key: string]: { status: string; latency?: number } | undefined;
  };
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

export interface ValidationResult {
  valid: boolean;
  errors?: ValidationError[];
}
