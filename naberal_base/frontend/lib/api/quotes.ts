/**
 * Quotes API
 * Quote management and approval workflow
 */

import { apiClient } from './client';
import type { PaginatedResponse } from '../types/api';
import type {
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

interface QuoteListParams {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  status?: QuoteStatus;
  customerName?: string;
  projectName?: string;
  fromDate?: string;
  toDate?: string;
}

/**
 * Create new quote from estimate
 */
export async function createQuote(
  request: QuoteCreateRequest,
  signal?: AbortSignal
): Promise<QuoteResponse> {
  return apiClient.post<QuoteResponse>('/v1/quotes', request, { signal });
}

/**
 * Get quote by ID
 */
export async function getQuote(
  quoteId: string,
  signal?: AbortSignal
): Promise<QuoteResponse> {
  return apiClient.get<QuoteResponse>(`/v1/quotes/${quoteId}`, { signal });
}

/**
 * Update quote details
 */
export async function updateQuote(
  quoteId: string,
  request: QuoteUpdateRequest,
  signal?: AbortSignal
): Promise<QuoteResponse> {
  return apiClient.put<QuoteResponse>(`/v1/quotes/${quoteId}`, request, { signal });
}

/**
 * List quotes with filters and pagination
 */
export async function listQuotes(
  params?: QuoteListParams,
  signal?: AbortSignal
): Promise<PaginatedResponse<QuoteListItem>> {
  const queryParams = new URLSearchParams();

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.set(key, value.toString());
      }
    });
  }

  const queryString = queryParams.toString();
  const endpoint = queryString ? `/v1/quotes?${queryString}` : '/v1/quotes';

  return apiClient.get<PaginatedResponse<QuoteListItem>>(endpoint, { signal });
}

/**
 * Approve quote
 */
export async function approveQuote(
  quoteId: string,
  request: QuoteApproveRequest,
  signal?: AbortSignal
): Promise<QuoteApproveResponse> {
  return apiClient.post<QuoteApproveResponse>(
    `/v1/quotes/${quoteId}/approve`,
    request,
    { signal }
  );
}

/**
 * Reject quote
 */
export async function rejectQuote(
  quoteId: string,
  reason?: string,
  signal?: AbortSignal
): Promise<QuoteResponse> {
  return apiClient.post<QuoteResponse>(
    `/v1/quotes/${quoteId}/reject`,
    { reason },
    { signal }
  );
}

/**
 * Generate PDF for quote
 */
export async function generateQuotePdf(
  quoteId: string,
  signal?: AbortSignal
): Promise<QuotePdfResponse> {
  return apiClient.post<QuotePdfResponse>(
    `/v1/quotes/${quoteId}/pdf`,
    {},
    { signal }
  );
}

/**
 * Get shareable URL for quote
 */
export async function getQuoteShareUrl(
  quoteId: string,
  expiresIn?: number,
  signal?: AbortSignal
): Promise<QuoteShareUrlResponse> {
  const body = expiresIn ? { expiresIn } : {};
  return apiClient.post<QuoteShareUrlResponse>(
    `/v1/quotes/${quoteId}/share`,
    body,
    { signal }
  );
}

/**
 * Download quote PDF
 */
export async function downloadQuotePdf(
  quoteId: string,
  signal?: AbortSignal
): Promise<Blob> {
  const response = await fetch(
    `${apiClient['baseUrl']}/v1/quotes/${quoteId}/download/pdf`,
    { signal }
  );

  if (!response.ok) {
    throw new Error(`Failed to download quote PDF: ${response.statusText}`);
  }

  return response.blob();
}

/**
 * Download quote Excel
 */
export async function downloadQuoteExcel(
  quoteId: string,
  signal?: AbortSignal
): Promise<Blob> {
  const response = await fetch(
    `${apiClient['baseUrl']}/v1/quotes/${quoteId}/download/excel`,
    { signal }
  );

  if (!response.ok) {
    throw new Error(`Failed to download quote Excel: ${response.statusText}`);
  }

  return response.blob();
}

/**
 * Delete quote
 */
export async function deleteQuote(
  quoteId: string,
  signal?: AbortSignal
): Promise<void> {
  return apiClient.delete<void>(`/v1/quotes/${quoteId}`, { signal });
}

/**
 * Get quote statistics
 */
export async function getQuoteStats(
  signal?: AbortSignal
): Promise<{
  totalQuotes: number;
  approvedQuotes: number;
  pendingQuotes: number;
  rejectedQuotes: number;
  totalValue: number;
  averageValue: number;
  todayCount: number;
  weekCount: number;
  monthCount: number;
}> {
  return apiClient.get<{
    totalQuotes: number;
    approvedQuotes: number;
    pendingQuotes: number;
    rejectedQuotes: number;
    totalValue: number;
    averageValue: number;
    todayCount: number;
    weekCount: number;
    monthCount: number;
  }>('/v1/quotes/stats', { signal });
}

/**
 * Send quote via email
 */
export async function sendQuoteEmail(
  quoteId: string,
  recipients: string[],
  message?: string,
  signal?: AbortSignal
): Promise<{ sent: boolean; timestamp: string }> {
  return apiClient.post<{ sent: boolean; timestamp: string }>(
    `/v1/quotes/${quoteId}/send`,
    { recipients, message },
    { signal }
  );
}
