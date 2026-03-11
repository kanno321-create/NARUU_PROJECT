/**
 * Customers API
 * 거래처 조회 및 자동완성 기능
 */

import { apiClient } from './client';

export interface Customer {
  id: string;
  code?: string;
  name: string;
  type: '매출' | '매입' | '겸용';
  business_number?: string;
  ceo?: string;
  contact?: string;
  address?: string;
  tel?: string;
  fax?: string;
  email?: string;
  mobile?: string;
  balance?: number;
  credit_limit?: number;
  payment_terms?: string;
  bank_info?: Record<string, unknown>;
  memo?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

interface CustomerListParams {
  customer_type?: '매출' | '매입' | '겸용';
  is_active?: boolean;
  search?: string;
  skip?: number;
  limit?: number;
}

/**
 * Search customers by name (for autocomplete)
 * Uses ERP /erp/customers endpoint with search parameter
 */
export async function searchCustomers(
  search: string,
  limit: number = 10,
  signal?: AbortSignal
): Promise<Customer[]> {
  const params = new URLSearchParams();
  if (search) params.set('search', search);
  params.set('limit', limit.toString());
  params.set('is_active', 'true');

  const queryString = params.toString();
  const endpoint = `/v1/erp/customers?${queryString}`;

  return apiClient.get<Customer[]>(endpoint, { signal });
}

/**
 * List customers with filters
 */
export async function listCustomers(
  params?: CustomerListParams,
  signal?: AbortSignal
): Promise<Customer[]> {
  const queryParams = new URLSearchParams();

  if (params) {
    if (params.customer_type) queryParams.set('customer_type', params.customer_type);
    if (params.is_active !== undefined) queryParams.set('is_active', String(params.is_active));
    if (params.search) queryParams.set('search', params.search);
    if (params.skip !== undefined) queryParams.set('skip', String(params.skip));
    if (params.limit !== undefined) queryParams.set('limit', String(params.limit));
  }

  const queryString = queryParams.toString();
  const endpoint = queryString ? `/v1/erp/customers?${queryString}` : '/v1/erp/customers';

  return apiClient.get<Customer[]>(endpoint, { signal });
}

/**
 * Get customer by ID
 */
export async function getCustomer(
  customerId: string,
  signal?: AbortSignal
): Promise<Customer> {
  return apiClient.get<Customer>(`/v1/erp/customers/${customerId}`, { signal });
}
