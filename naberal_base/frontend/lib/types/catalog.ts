/**
 * Catalog Types
 * Breaker, Enclosure, and Accessory catalog data models
 */

export type BreakerCategory = 'MCCB' | 'ELB';
export type BreakerEconomy = 'standard' | 'economy' | 'compact';
export type BreakerBrand = 'SANGDO' | 'LS' | 'HANGUK';

export interface BreakerCatalog {
  id: string;
  model: string;
  brand: BreakerBrand;
  series: string;
  category: BreakerCategory;
  economy: BreakerEconomy;
  poles: 2 | 3 | 4;
  frame: number;
  ampere: number;
  breakingCapacity: number;
  price: number;
  width: number;
  height: number;
  depth: number;
  createdAt?: string;
  updatedAt?: string;
}

export interface BreakerFilters {
  category?: BreakerCategory;
  brand?: BreakerBrand;
  economy?: BreakerEconomy;
  poles?: number;
  frameMin?: number;
  frameMax?: number;
  ampereMin?: number;
  ampereMax?: number;
  priceMin?: number;
  priceMax?: number;
  search?: string;
}

export type EnclosureType =
  | '옥내노출'
  | '옥외노출'
  | '옥내자립'
  | '옥외자립'
  | '전주부착형'
  | 'FRP함'
  | '하이박스'
  | '매입함';

export type EnclosureMaterial =
  | 'STEEL 1.6T'
  | 'STEEL 1.0T'
  | 'SUS201 1.2T'
  | 'SUS304 1.2T';

export interface EnclosureCatalog {
  id: string;
  sku: string;
  type: EnclosureType;
  material: EnclosureMaterial;
  width: number;
  height: number;
  depth: number;
  price: number;
  ipRating?: string;
  hasBase?: boolean;
  basePrice?: number;
  createdAt?: string;
  updatedAt?: string;
}

export interface EnclosureFilters {
  type?: EnclosureType;
  material?: EnclosureMaterial;
  widthMin?: number;
  widthMax?: number;
  heightMin?: number;
  heightMax?: number;
  depthMin?: number;
  depthMax?: number;
  priceMin?: number;
  priceMax?: number;
  ipRating?: string;
  search?: string;
}

export type AccessoryType =
  | 'MAGNET'
  | 'TIMER'
  | 'VA_METER'
  | 'SPD'
  | 'METER'
  | 'ET'
  | 'NT'
  | 'BUSBAR'
  | 'TERMINAL_BLOCK'
  | 'FUSEHOLDER'
  | 'PVC_DUCT'
  | 'CABLE_WIRE'
  | 'INSULATOR'
  | 'P_COVER'
  | 'COATING';

export interface AccessoryCatalog {
  id: string;
  type: AccessoryType;
  model: string;
  specification?: string;
  price: number;
  unit: string;
  width?: number;
  height?: number;
  depth?: number;
  bundledWith?: AccessoryType[];
  createdAt?: string;
  updatedAt?: string;
}

export interface AccessoryFilters {
  type?: AccessoryType;
  priceMin?: number;
  priceMax?: number;
  search?: string;
}

export interface CatalogStats {
  breakerCount: number;
  enclosureCount: number;
  accessoryCount: number;
  lastUpdated: string;
}
