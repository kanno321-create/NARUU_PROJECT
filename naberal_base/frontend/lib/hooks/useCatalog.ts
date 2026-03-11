/**
 * Catalog Data Hooks
 * React Query hooks for catalog data with caching
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
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
import {
  getBreakers,
  getEnclosures,
  getAccessories,
  getCatalogStats,
  searchBreakers,
  searchEnclosures,
  searchAccessories,
} from '../api/catalog';

const CATALOG_TTL = 5 * 60 * 1000; // 5 minutes

/**
 * Hook to fetch breakers with filters and caching
 */
export function useBreakers(
  filters?: BreakerFilters,
  options?: Omit<UseQueryOptions<PaginatedResponse<BreakerCatalog>>, 'queryKey' | 'queryFn'>
) {
  return useQuery<PaginatedResponse<BreakerCatalog>>({
    queryKey: ['breakers', filters],
    queryFn: ({ signal }) => getBreakers(filters, undefined, signal),
    staleTime: CATALOG_TTL,
    gcTime: CATALOG_TTL,
    ...options,
  });
}

/**
 * Hook to search breakers by model name
 */
export function useBreakerSearch(
  query: string,
  options?: Omit<UseQueryOptions<BreakerCatalog[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery<BreakerCatalog[]>({
    queryKey: ['breakers', 'search', query],
    queryFn: ({ signal }) => searchBreakers(query, signal),
    staleTime: CATALOG_TTL,
    gcTime: CATALOG_TTL,
    enabled: query.length > 0,
    ...options,
  });
}

/**
 * Hook to fetch enclosures with filters and caching
 */
export function useEnclosures(
  filters?: EnclosureFilters,
  options?: Omit<UseQueryOptions<PaginatedResponse<EnclosureCatalog>>, 'queryKey' | 'queryFn'>
) {
  return useQuery<PaginatedResponse<EnclosureCatalog>>({
    queryKey: ['enclosures', filters],
    queryFn: ({ signal }) => getEnclosures(filters, undefined, signal),
    staleTime: CATALOG_TTL,
    gcTime: CATALOG_TTL,
    ...options,
  });
}

/**
 * Hook to search enclosures by SKU
 */
export function useEnclosureSearch(
  query: string,
  options?: Omit<UseQueryOptions<EnclosureCatalog[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery<EnclosureCatalog[]>({
    queryKey: ['enclosures', 'search', query],
    queryFn: ({ signal }) => searchEnclosures(query, signal),
    staleTime: CATALOG_TTL,
    gcTime: CATALOG_TTL,
    enabled: query.length > 0,
    ...options,
  });
}

/**
 * Hook to fetch accessories with filters and caching
 */
export function useAccessories(
  filters?: AccessoryFilters,
  options?: Omit<UseQueryOptions<PaginatedResponse<AccessoryCatalog>>, 'queryKey' | 'queryFn'>
) {
  return useQuery<PaginatedResponse<AccessoryCatalog>>({
    queryKey: ['accessories', filters],
    queryFn: ({ signal }) => getAccessories(filters, undefined, signal),
    staleTime: CATALOG_TTL,
    gcTime: CATALOG_TTL,
    ...options,
  });
}

/**
 * Hook to search accessories by model/type
 */
export function useAccessorySearch(
  query: string,
  options?: Omit<UseQueryOptions<AccessoryCatalog[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AccessoryCatalog[]>({
    queryKey: ['accessories', 'search', query],
    queryFn: ({ signal }) => searchAccessories(query, signal),
    staleTime: CATALOG_TTL,
    gcTime: CATALOG_TTL,
    enabled: query.length > 0,
    ...options,
  });
}

/**
 * Hook to fetch catalog statistics
 */
export function useCatalogStats(
  options?: Omit<UseQueryOptions<CatalogStats>, 'queryKey' | 'queryFn'>
) {
  return useQuery<CatalogStats>({
    queryKey: ['catalog', 'stats'],
    queryFn: ({ signal }) => getCatalogStats(signal),
    staleTime: CATALOG_TTL,
    gcTime: CATALOG_TTL,
    ...options,
  });
}

/**
 * Hook to get unique values for cascading filters
 */
export function useBreakerFilterOptions(filters?: Partial<BreakerFilters>) {
  const { data, isLoading } = useBreakers(filters);

  const options = {
    categories: Array.from(new Set(data?.items.map((b) => b.category) || [])),
    brands: Array.from(new Set(data?.items.map((b) => b.brand) || [])),
    series: Array.from(new Set(data?.items.map((b) => b.series) || [])),
    poles: Array.from(new Set(data?.items.map((b) => b.poles) || [])).sort(),
    frames: Array.from(new Set(data?.items.map((b) => b.frame) || [])).sort((a, b) => a - b),
    amperes: Array.from(new Set(data?.items.map((b) => b.ampere) || [])).sort((a, b) => a - b),
  };

  return { options, isLoading };
}

/**
 * Hook to get unique values for enclosure filters
 */
export function useEnclosureFilterOptions(filters?: Partial<EnclosureFilters>) {
  const { data, isLoading } = useEnclosures(filters);

  const options = {
    types: Array.from(new Set(data?.items.map((e) => e.type) || [])),
    materials: Array.from(new Set(data?.items.map((e) => e.material) || [])),
    sizes: data?.items.map((e) => ({
      id: e.id,
      size: `${e.width}×${e.height}×${e.depth}`,
      price: e.price,
    })) || [],
  };

  return { options, isLoading };
}

/**
 * Hook to get unique values for accessory filters
 */
export function useAccessoryFilterOptions(filters?: Partial<AccessoryFilters>) {
  const { data, isLoading } = useAccessories(filters);

  const options = {
    types: Array.from(new Set(data?.items.map((a) => a.type) || [])),
    models: data?.items.map((a) => ({
      id: a.id,
      model: a.model,
      spec: a.specification,
      price: a.price,
    })) || [],
  };

  return { options, isLoading };
}
