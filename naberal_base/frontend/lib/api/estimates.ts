/**
 * Estimates API
 * FIX-4 Pipeline estimation operations
 */

import { apiClient } from './client';
import type { PaginatedResponse } from '../types/api';
import type {
  EstimateRequest,
  EstimateResponse,
  ValidateEstimateRequest,
  ValidateEstimateResponse,
  EstimateListItem,
} from '../types/estimate';

interface EstimateListParams {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  status?: string;
  customerName?: string;
  projectName?: string;
  fromDate?: string;
  toDate?: string;
}

/**
 * Create new estimate (FIX-4 pipeline execution)
 */
export async function createEstimate(
  request: EstimateRequest,
  signal?: AbortSignal
): Promise<EstimateResponse> {
  return apiClient.post<EstimateResponse>('/v1/estimates', request, { signal });
}

/**
 * Validate estimate request without creating
 */
export async function validateEstimate(
  request: ValidateEstimateRequest,
  signal?: AbortSignal
): Promise<ValidateEstimateResponse> {
  return apiClient.post<ValidateEstimateResponse>(
    '/v1/estimates/validate',
    request,
    { signal }
  );
}

/**
 * Get estimate by ID
 */
export async function getEstimate(
  estimateId: string,
  signal?: AbortSignal
): Promise<EstimateResponse> {
  return apiClient.get<EstimateResponse>(`/v1/estimates/${estimateId}`, { signal });
}

/**
 * List estimates with filters and pagination
 */
export async function listEstimates(
  params?: EstimateListParams,
  signal?: AbortSignal
): Promise<PaginatedResponse<EstimateListItem>> {
  const queryParams = new URLSearchParams();

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.set(key, value.toString());
      }
    });
  }

  const queryString = queryParams.toString();
  const endpoint = queryString ? `/v1/estimates?${queryString}` : '/v1/estimates';

  return apiClient.get<PaginatedResponse<EstimateListItem>>(endpoint, { signal });
}

/**
 * Delete estimate by ID
 */
export async function deleteEstimate(
  estimateId: string,
  signal?: AbortSignal
): Promise<void> {
  return apiClient.delete<void>(`/v1/estimates/${estimateId}`, { signal });
}

/**
 * Get estimate evidence files
 */
export async function getEstimateEvidence(
  estimateId: string,
  signal?: AbortSignal
): Promise<{
  hash: string;
  timestamp: string;
  files: {
    input?: string;
    output?: string;
    metrics?: string;
    validation?: string;
    visual?: string;
  };
}> {
  return apiClient.get<{
    hash: string;
    timestamp: string;
    files: {
      input?: string;
      output?: string;
      metrics?: string;
      validation?: string;
      visual?: string;
    };
  }>(`/v1/estimates/${estimateId}/evidence`, { signal });
}

/**
 * Re-run pipeline for existing estimate
 */
export async function rerunEstimate(
  estimateId: string,
  options?: {
    skipValidation?: boolean;
    generatePdf?: boolean;
  },
  signal?: AbortSignal
): Promise<EstimateResponse> {
  return apiClient.post<EstimateResponse>(
    `/v1/estimates/${estimateId}/rerun`,
    options,
    { signal }
  );
}

/**
 * Get estimate summary statistics
 */
export async function getEstimateStats(
  signal?: AbortSignal
): Promise<{
  totalEstimates: number;
  totalPanels: number;
  totalValue: number;
  averageValue: number;
  todayCount: number;
  weekCount: number;
  monthCount: number;
}> {
  return apiClient.get<{
    totalEstimates: number;
    totalPanels: number;
    totalValue: number;
    averageValue: number;
    todayCount: number;
    weekCount: number;
    monthCount: number;
  }>('/v1/estimates/stats', { signal });
}

/**
 * Export estimate to Excel
 */
export async function exportEstimateToExcel(
  estimateId: string,
  signal?: AbortSignal
): Promise<Blob> {
  const response = await fetch(
    `${apiClient['baseUrl']}/v1/estimates/${estimateId}/export/excel`,
    { signal }
  );

  if (!response.ok) {
    throw new Error(`Failed to export estimate: ${response.statusText}`);
  }

  return response.blob();
}

/**
 * Export estimate to PDF
 */
export async function exportEstimateToPdf(
  estimateId: string,
  signal?: AbortSignal
): Promise<Blob> {
  const response = await fetch(
    `${apiClient['baseUrl']}/v1/estimates/${estimateId}/export/pdf`,
    { signal }
  );

  if (!response.ok) {
    throw new Error(`Failed to export estimate: ${response.statusText}`);
  }

  return response.blob();
}
