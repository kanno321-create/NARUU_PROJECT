/**
 * Catalog API
 * Breaker, Enclosure, and Accessory catalog operations
 */

import { apiClient } from './client';
import type { PaginatedResponse } from '../types/api';
import type {
  BreakerCatalog,
  BreakerFilters,
  EnclosureCatalog,
  EnclosureFilters,
  AccessoryCatalog,
  AccessoryFilters,
  CatalogStats,
} from '../types/catalog';

interface CatalogListParams {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

/**
 * Get paginated breaker catalog with filters
 */
export async function getBreakers(
  filters?: BreakerFilters,
  params?: CatalogListParams,
  signal?: AbortSignal
): Promise<PaginatedResponse<BreakerCatalog>> {
  const queryParams = new URLSearchParams();

  if (params?.page) queryParams.set('page', params.page.toString());
  if (params?.pageSize) queryParams.set('pageSize', params.pageSize.toString());
  if (params?.sortBy) queryParams.set('sortBy', params.sortBy);
  if (params?.sortOrder) queryParams.set('sortOrder', params.sortOrder);

  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.set(key, value.toString());
      }
    });
  }

  const queryString = queryParams.toString();
  const endpoint = queryString ? `/v1/catalog/breakers?${queryString}` : '/v1/catalog/breakers';

  return apiClient.get<PaginatedResponse<BreakerCatalog>>(endpoint, { signal });
}

/**
 * Get single breaker by ID
 */
export async function getBreaker(
  id: string,
  signal?: AbortSignal
): Promise<BreakerCatalog> {
  return apiClient.get<BreakerCatalog>(`/v1/catalog/breakers/${id}`, { signal });
}

/**
 * Search breakers by model name
 */
export async function searchBreakers(
  query: string,
  signal?: AbortSignal
): Promise<BreakerCatalog[]> {
  const queryParams = new URLSearchParams({ search: query });
  const response = await apiClient.get<PaginatedResponse<BreakerCatalog>>(
    `/v1/catalog/breakers?${queryParams.toString()}`,
    { signal }
  );
  return response.items;
}

/**
 * Get paginated enclosure catalog with filters
 */
export async function getEnclosures(
  filters?: EnclosureFilters,
  params?: CatalogListParams,
  signal?: AbortSignal
): Promise<PaginatedResponse<EnclosureCatalog>> {
  const queryParams = new URLSearchParams();

  if (params?.page) queryParams.set('page', params.page.toString());
  if (params?.pageSize) queryParams.set('pageSize', params.pageSize.toString());
  if (params?.sortBy) queryParams.set('sortBy', params.sortBy);
  if (params?.sortOrder) queryParams.set('sortOrder', params.sortOrder);

  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.set(key, value.toString());
      }
    });
  }

  const queryString = queryParams.toString();
  const endpoint = queryString ? `/v1/catalog/enclosures?${queryString}` : '/v1/catalog/enclosures';

  return apiClient.get<PaginatedResponse<EnclosureCatalog>>(endpoint, { signal });
}

/**
 * Get single enclosure by ID
 */
export async function getEnclosure(
  id: string,
  signal?: AbortSignal
): Promise<EnclosureCatalog> {
  return apiClient.get<EnclosureCatalog>(`/v1/catalog/enclosures/${id}`, { signal });
}

/**
 * Search enclosures by SKU
 */
export async function searchEnclosures(
  query: string,
  signal?: AbortSignal
): Promise<EnclosureCatalog[]> {
  const queryParams = new URLSearchParams({ search: query });
  const response = await apiClient.get<PaginatedResponse<EnclosureCatalog>>(
    `/v1/catalog/enclosures?${queryParams.toString()}`,
    { signal }
  );
  return response.items;
}

/**
 * Get paginated accessory catalog with filters
 */
export async function getAccessories(
  filters?: AccessoryFilters,
  params?: CatalogListParams,
  signal?: AbortSignal
): Promise<PaginatedResponse<AccessoryCatalog>> {
  const queryParams = new URLSearchParams();

  if (params?.page) queryParams.set('page', params.page.toString());
  if (params?.pageSize) queryParams.set('pageSize', params.pageSize.toString());
  if (params?.sortBy) queryParams.set('sortBy', params.sortBy);
  if (params?.sortOrder) queryParams.set('sortOrder', params.sortOrder);

  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.set(key, value.toString());
      }
    });
  }

  const queryString = queryParams.toString();
  const endpoint = queryString ? `/v1/catalog/accessories?${queryString}` : '/v1/catalog/accessories';

  return apiClient.get<PaginatedResponse<AccessoryCatalog>>(endpoint, { signal });
}

/**
 * Get single accessory by ID
 */
export async function getAccessory(
  id: string,
  signal?: AbortSignal
): Promise<AccessoryCatalog> {
  return apiClient.get<AccessoryCatalog>(`/v1/catalog/accessories/${id}`, { signal });
}

/**
 * Search accessories by model/type
 */
export async function searchAccessories(
  query: string,
  signal?: AbortSignal
): Promise<AccessoryCatalog[]> {
  const queryParams = new URLSearchParams({ search: query });
  const response = await apiClient.get<PaginatedResponse<AccessoryCatalog>>(
    `/v1/catalog/accessories?${queryParams.toString()}`,
    { signal }
  );
  return response.items;
}

/**
 * Get catalog statistics
 */
export async function getCatalogStats(signal?: AbortSignal): Promise<CatalogStats> {
  return apiClient.get<CatalogStats>('/v1/catalog/stats', { signal });
}

/**
 * Get all catalog items (unified search)
 */
export async function searchCatalog(
  query: string,
  signal?: AbortSignal
): Promise<{
  breakers: BreakerCatalog[];
  enclosures: EnclosureCatalog[];
  accessories: AccessoryCatalog[];
}> {
  const queryParams = new URLSearchParams({ search: query });
  return apiClient.get<{
    breakers: BreakerCatalog[];
    enclosures: EnclosureCatalog[];
    accessories: AccessoryCatalog[];
  }>(`/v1/catalog/items?${queryParams.toString()}`, { signal });
}
