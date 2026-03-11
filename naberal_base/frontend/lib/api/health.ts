/**
 * Health Check API
 * Health probe and readiness endpoints
 */

import { apiClient } from './client';
import type { HealthCheckResponse } from '../types/api';

export interface LivenessResponse {
  status: 'alive';
  timestamp: string;
}

export interface ReadinessResponse {
  status: 'ready' | 'not_ready';
  timestamp: string;
  checks: {
    database: boolean;
    cache?: boolean;
  };
}

export interface DatabaseHealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency: number;
  timestamp: string;
}

/**
 * Get overall health status
 */
export async function getHealth(signal?: AbortSignal): Promise<HealthCheckResponse> {
  return apiClient.get<HealthCheckResponse>('/v1/health', { signal });
}

/**
 * Liveness probe - returns quickly if process is alive
 */
export async function getLiveness(signal?: AbortSignal): Promise<LivenessResponse> {
  return apiClient.get<LivenessResponse>('/v1/health/live', { signal });
}

/**
 * Database health check
 */
export async function getDatabaseHealth(signal?: AbortSignal): Promise<DatabaseHealthResponse> {
  return apiClient.get<DatabaseHealthResponse>('/v1/health/db', { signal });
}

/**
 * Readiness probe - checks all dependencies
 */
export async function getReadiness(signal?: AbortSignal): Promise<ReadinessResponse> {
  return apiClient.get<ReadinessResponse>('/v1/health/readyz', { signal });
}

/**
 * Quick health check - uses liveness for fast response
 */
export async function quickHealthCheck(signal?: AbortSignal): Promise<boolean> {
  try {
    const response = await getLiveness(signal);
    return response.status === 'alive';
  } catch {
    return false;
  }
}
