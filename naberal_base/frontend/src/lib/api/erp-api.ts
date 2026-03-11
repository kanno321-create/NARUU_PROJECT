/**
 * ERP API Client
 * FastAPI 백엔드를 호출하는 ERP API 클라이언트 (Supabase 사용 안 함)
 */

import apiClient from './client';

// ============================================
// Types
// ============================================

export interface Customer {
  id: string;
  code: string | null;
  name: string;
  customer_type: string;
  grade: string;
  business_number: string | null;
  ceo_name: string | null;
  contact_person: string | null;
  phone: string | null;
  fax: string | null;
  email: string | null;
  address: string | null;
  credit_limit: string;
  current_receivable: string;  // 현재 미수금 (API에서 문자열로 반환)
  payment_terms: string | null;
  memo: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface CustomerCreate {
  code?: string;
  name: string;
  customer_type?: string;
  grade?: string;
  business_number?: string;
  ceo_name?: string;
  contact_person?: string;
  phone?: string;
  fax?: string;
  email?: string;
  address?: string;
  credit_limit?: string;
  payment_terms?: string;
  memo?: string;
  is_active?: boolean;
}

export interface CustomerUpdate {
  name?: string;
  customer_type?: string;
  grade?: string;
  business_number?: string;
  ceo_name?: string;
  contact_person?: string;
  phone?: string;
  fax?: string;
  email?: string;
  address?: string;
  credit_limit?: string;
  payment_terms?: string;
  memo?: string;
  is_active?: boolean;
}

export interface Product {
  id: string;
  code: string | null;
  name: string;
  spec: string | null;
  unit: string;
  category_id: string | null;
  purchase_price: string;
  selling_price: string;
  safety_stock: number;
  memo: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

// Extended product type for catalog search results
export interface ProductWithCatalog extends Product {
  is_catalog?: boolean;
  dimensions?: {
    width: number;
    height: number;
    depth: number;
  };
}

export interface SearchAllResponse {
  items: ProductWithCatalog[];
  total: number;
  erp_count: number;
  catalog_count: number;
}

export interface ProductCreate {
  code?: string;
  name: string;
  spec?: string;
  unit?: string;
  category_id?: string;
  purchase_price?: string;
  selling_price?: string;
  safety_stock?: number;
  memo?: string;
  is_active?: boolean;
}

export interface ProductUpdate {
  name?: string;
  spec?: string;
  unit?: string;
  category_id?: string;
  purchase_price?: string;
  selling_price?: string;
  safety_stock?: number;
  memo?: string;
  is_active?: boolean;
}

export interface SaleItem {
  id: string;
  sale_id: string | null;
  product_id: string | null;
  product_code: string | null;
  product_name: string;
  spec: string | null;
  unit: string;
  quantity: number;
  unit_price: string;
  supply_amount: string;
  tax_amount: string;
  total_amount: string;
  cost_price: string;
  memo: string | null;
  sort_order: number;
}

export interface SaleItemCreate {
  product_id?: string;
  product_code?: string;
  product_name: string;
  spec?: string;
  unit?: string;
  quantity?: number;
  unit_price?: number;
  cost_price?: number;
  memo?: string;
}

export interface Sale {
  id: string;
  sale_number: string | null;
  sale_date: string;
  customer_id: string;
  status: string;
  supply_amount: string;
  tax_amount: string;
  total_amount: string;
  cost_amount: string;
  profit_amount: string;
  memo: string | null;
  items: SaleItem[];
  customer?: Customer;
  created_at: string;
  updated_at: string | null;
}

export interface SaleCreate {
  sale_date: string;
  customer_id: string;
  status?: string;
  memo?: string;
  items: SaleItemCreate[];
}

export interface SaleUpdate {
  sale_date?: string;
  customer_id?: string;
  status?: string;
  memo?: string;
}

export interface PurchaseItem {
  id: string;
  purchase_id: string | null;
  product_id: string | null;
  product_code: string | null;
  product_name: string;
  spec: string | null;
  unit: string;
  quantity: number;
  unit_price: string;
  supply_amount: string;
  tax_amount: string;
  total_amount: string;
  memo: string | null;
  sort_order: number;
}

export interface PurchaseItemCreate {
  product_id?: string;
  product_code?: string;
  product_name: string;
  spec?: string;
  unit?: string;
  quantity?: number;
  unit_price?: string;
  memo?: string;
}

export interface Purchase {
  id: string;
  purchase_number: string | null;
  purchase_date: string;
  supplier_id: string;
  status: string;
  supply_amount: string;
  tax_amount: string;
  total_amount: string;
  memo: string | null;
  items: PurchaseItem[];
  supplier?: Customer;
  created_at: string;
  updated_at: string | null;
}

export interface PurchaseCreate {
  purchase_date: string;
  supplier_id: string;
  status?: string;
  memo?: string;
  items: PurchaseItemCreate[];
}

export interface PurchaseUpdate {
  purchase_date?: string;
  supplier_id?: string;
  status?: string;
  memo?: string;
}

export interface TaxInvoice {
  id: string;
  invoice_number: string | null;
  invoice_type: string;
  issue_date: string;
  customer_id: string;
  supply_amount: string;
  tax_amount: string;
  total_amount: string;
  status: string;
  reference_type: string | null;
  reference_id: string | null;
  memo: string | null;
  customer?: Customer;
  created_at: string;
  updated_at: string | null;
}

export interface TaxInvoiceCreate {
  invoice_number?: string;
  invoice_type?: string;
  issue_date: string;
  customer_id: string;
  supply_amount?: string;
  tax_amount?: string;
  total_amount?: string;
  status?: string;
  reference_type?: string;
  reference_id?: string;
  memo?: string;
}

export interface TaxInvoiceUpdate {
  issue_date?: string;
  status?: string;
  memo?: string;
}

export interface QuotationItem {
  id: string;
  quotation_id: string | null;
  product_id: string | null;
  product_code: string | null;
  product_name: string;
  spec: string | null;
  unit: string;
  quantity: number;
  unit_price: string;
  supply_amount: string;
  tax_amount: string;
  total_amount: string;
  memo: string | null;
  sort_order: number;
}

export interface QuotationItemCreate {
  product_id?: string;
  product_code?: string;
  product_name: string;
  spec?: string;
  unit?: string;
  quantity?: number;
  unit_price?: string;
  memo?: string;
}

export interface Quotation {
  id: string;
  quotation_number: string | null;
  quotation_date: string;
  valid_until: string | null;
  customer_id: string;
  status: string;
  supply_amount: string;
  tax_amount: string;
  total_amount: string;
  memo: string | null;
  items: QuotationItem[];
  customer?: Customer;
  created_at: string;
  updated_at: string | null;
}

export interface QuotationCreate {
  quotation_date: string;
  valid_until?: string;
  customer_id: string;
  status?: string;
  memo?: string;
  items: QuotationItemCreate[];
}

export interface QuotationUpdate {
  quotation_date?: string;
  valid_until?: string;
  status?: string;
  memo?: string;
}

export interface Payment {
  id: string;
  payment_number: string | null;
  payment_type: string;
  payment_date: string;
  customer_id: string;
  amount: string;
  payment_method: string;
  status: string;
  completed_date: string | null;
  reference_type: string | null;
  reference_id: string | null;
  memo: string | null;
  customer?: Customer;
  created_at: string;
  updated_at: string | null;
}

export interface PaymentCreate {
  payment_number?: string;
  payment_type: string;
  payment_date: string;
  customer_id: string;
  amount?: string;
  payment_method?: string;
  status?: string;
  completed_date?: string;
  reference_type?: string;
  reference_id?: string;
  memo?: string;
}

export interface PaymentUpdate {
  payment_date?: string;
  amount?: string;
  payment_method?: string;
  status?: string;
  completed_date?: string;
  memo?: string;
}

export interface DashboardStats {
  monthly_sales: string;
  monthly_purchases: string;
  total_receivables: string;
  total_payables: string;
  sales_count: number;
  purchase_count: number;
  customer_count: number;
  product_count: number;
}

export interface SalesChartData {
  period: string;
  amount: string;
}

export interface ListResponse<T> {
  items: T[];
  total: number;
}

// ============================================
// Customer API
// ============================================

export const customerApi = {
  list: async (params?: {
    search?: string;
    customer_type?: string;
    is_active?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<ListResponse<Customer>> => {
    const queryParams = new URLSearchParams();
    if (params?.search) queryParams.append('search', params.search);
    if (params?.customer_type) queryParams.append('customer_type', params.customer_type);
    if (params?.is_active !== undefined) queryParams.append('is_active', String(params.is_active));
    if (params?.skip) queryParams.append('skip', String(params.skip));
    if (params?.limit) queryParams.append('limit', String(params.limit));

    const query = queryParams.toString();
    return apiClient.get(`/v1/erp/customers${query ? `?${query}` : ''}`);
  },

  get: async (id: string): Promise<Customer> => {
    return apiClient.get(`/v1/erp/customers/${id}`);
  },

  create: async (data: CustomerCreate): Promise<Customer> => {
    return apiClient.post('/v1/erp/customers', data);
  },

  update: async (id: string, data: CustomerUpdate): Promise<Customer> => {
    return apiClient.patch(`/v1/erp/customers/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return apiClient.delete(`/v1/erp/customers/${id}`);
  },
};

// ============================================
// Product API
// ============================================

export const productApi = {
  list: async (params?: {
    search?: string;
    category_id?: string;
    is_active?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<ListResponse<Product>> => {
    const queryParams = new URLSearchParams();
    if (params?.search) queryParams.append('search', params.search);
    if (params?.category_id) queryParams.append('category_id', params.category_id);
    if (params?.is_active !== undefined) queryParams.append('is_active', String(params.is_active));
    if (params?.skip) queryParams.append('skip', String(params.skip));
    if (params?.limit) queryParams.append('limit', String(params.limit));

    const query = queryParams.toString();
    return apiClient.get(`/v1/erp/products${query ? `?${query}` : ''}`);
  },

  get: async (id: string): Promise<Product> => {
    return apiClient.get(`/v1/erp/products/${id}`);
  },

  create: async (data: ProductCreate): Promise<Product> => {
    return apiClient.post('/v1/erp/products', data);
  },

  update: async (id: string, data: ProductUpdate): Promise<Product> => {
    return apiClient.patch(`/v1/erp/products/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return apiClient.delete(`/v1/erp/products/${id}`);
  },

  // Search all products including catalog (ai_catalog_v1.json)
  searchAll: async (params: {
    search: string;
    limit?: number;
  }): Promise<SearchAllResponse> => {
    const queryParams = new URLSearchParams();
    queryParams.append('search', params.search);
    if (params.limit) queryParams.append('limit', String(params.limit));

    return apiClient.get(`/v1/erp/products/search-all?${queryParams.toString()}`);
  },
};

// ============================================
// Sale API
// ============================================

export const saleApi = {
  list: async (params?: {
    customer_id?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }): Promise<ListResponse<Sale>> => {
    const queryParams = new URLSearchParams();
    if (params?.customer_id) queryParams.append('customer_id', params.customer_id);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.skip) queryParams.append('skip', String(params.skip));
    if (params?.limit) queryParams.append('limit', String(params.limit));

    const query = queryParams.toString();
    return apiClient.get(`/v1/erp/sales${query ? `?${query}` : ''}`);
  },

  get: async (id: string): Promise<Sale> => {
    return apiClient.get(`/v1/erp/sales/${id}`);
  },

  create: async (data: SaleCreate): Promise<Sale> => {
    return apiClient.post('/v1/erp/sales', data);
  },

  update: async (id: string, data: SaleUpdate): Promise<Sale> => {
    return apiClient.patch(`/v1/erp/sales/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return apiClient.delete(`/v1/erp/sales/${id}`);
  },
};

// ============================================
// Purchase API
// ============================================

export const purchaseApi = {
  list: async (params?: {
    supplier_id?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }): Promise<ListResponse<Purchase>> => {
    const queryParams = new URLSearchParams();
    if (params?.supplier_id) queryParams.append('supplier_id', params.supplier_id);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.skip) queryParams.append('skip', String(params.skip));
    if (params?.limit) queryParams.append('limit', String(params.limit));

    const query = queryParams.toString();
    return apiClient.get(`/v1/erp/purchases${query ? `?${query}` : ''}`);
  },

  get: async (id: string): Promise<Purchase> => {
    return apiClient.get(`/v1/erp/purchases/${id}`);
  },

  create: async (data: PurchaseCreate): Promise<Purchase> => {
    return apiClient.post('/v1/erp/purchases', data);
  },

  update: async (id: string, data: PurchaseUpdate): Promise<Purchase> => {
    return apiClient.patch(`/v1/erp/purchases/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return apiClient.delete(`/v1/erp/purchases/${id}`);
  },
};

// ============================================
// Tax Invoice API
// ============================================

export const taxInvoiceApi = {
  list: async (params?: {
    customer_id?: string;
    invoice_type?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }): Promise<ListResponse<TaxInvoice>> => {
    const queryParams = new URLSearchParams();
    if (params?.customer_id) queryParams.append('customer_id', params.customer_id);
    if (params?.invoice_type) queryParams.append('invoice_type', params.invoice_type);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.skip) queryParams.append('skip', String(params.skip));
    if (params?.limit) queryParams.append('limit', String(params.limit));

    const query = queryParams.toString();
    return apiClient.get(`/v1/erp/tax-invoices${query ? `?${query}` : ''}`);
  },

  get: async (id: string): Promise<TaxInvoice> => {
    return apiClient.get(`/v1/erp/tax-invoices/${id}`);
  },

  create: async (data: TaxInvoiceCreate): Promise<TaxInvoice> => {
    return apiClient.post('/v1/erp/tax-invoices', data);
  },

  update: async (id: string, data: TaxInvoiceUpdate): Promise<TaxInvoice> => {
    return apiClient.patch(`/v1/erp/tax-invoices/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return apiClient.delete(`/v1/erp/tax-invoices/${id}`);
  },
};

// ============================================
// Quotation API
// ============================================

export const quotationApi = {
  list: async (params?: {
    customer_id?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }): Promise<ListResponse<Quotation>> => {
    const queryParams = new URLSearchParams();
    if (params?.customer_id) queryParams.append('customer_id', params.customer_id);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.skip) queryParams.append('skip', String(params.skip));
    if (params?.limit) queryParams.append('limit', String(params.limit));

    const query = queryParams.toString();
    return apiClient.get(`/v1/erp/quotations${query ? `?${query}` : ''}`);
  },

  get: async (id: string): Promise<Quotation> => {
    return apiClient.get(`/v1/erp/quotations/${id}`);
  },

  create: async (data: QuotationCreate): Promise<Quotation> => {
    return apiClient.post('/v1/erp/quotations', data);
  },

  update: async (id: string, data: QuotationUpdate): Promise<Quotation> => {
    return apiClient.patch(`/v1/erp/quotations/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return apiClient.delete(`/v1/erp/quotations/${id}`);
  },
};

// ============================================
// Payment API
// ============================================

export const paymentApi = {
  list: async (params?: {
    customer_id?: string;
    payment_type?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }): Promise<ListResponse<Payment>> => {
    const queryParams = new URLSearchParams();
    if (params?.customer_id) queryParams.append('customer_id', params.customer_id);
    if (params?.payment_type) queryParams.append('payment_type', params.payment_type);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.skip) queryParams.append('skip', String(params.skip));
    if (params?.limit) queryParams.append('limit', String(params.limit));

    const query = queryParams.toString();
    return apiClient.get(`/v1/erp/payments${query ? `?${query}` : ''}`);
  },

  get: async (id: string): Promise<Payment> => {
    return apiClient.get(`/v1/erp/payments/${id}`);
  },

  create: async (data: PaymentCreate): Promise<Payment> => {
    return apiClient.post('/v1/erp/payments', data);
  },

  update: async (id: string, data: PaymentUpdate): Promise<Payment> => {
    return apiClient.patch(`/v1/erp/payments/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return apiClient.delete(`/v1/erp/payments/${id}`);
  },
};

// ============================================
// Dashboard API
// ============================================

export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    return apiClient.get('/v1/erp/dashboard/stats');
  },

  getSalesChart: async (params?: {
    period?: 'daily' | 'weekly' | 'monthly';
    months?: number;
  }): Promise<SalesChartData[]> => {
    const queryParams = new URLSearchParams();
    if (params?.period) queryParams.append('period', params.period);
    if (params?.months) queryParams.append('months', String(params.months));

    const query = queryParams.toString();
    return apiClient.get(`/v1/erp/dashboard/sales-chart${query ? `?${query}` : ''}`);
  },
};

// ============================================
// Export all APIs
// ============================================

export default {
  customer: customerApi,
  product: productApi,
  sale: saleApi,
  purchase: purchaseApi,
  taxInvoice: taxInvoiceApi,
  quotation: quotationApi,
  payment: paymentApi,
  dashboard: dashboardApi,
};
