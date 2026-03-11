/**
 * ERP Store - Zustand 기반 상태 관리
 * FastAPI 백엔드 사용 (Supabase 제거)
 */

import { create } from 'zustand';
import {
  customerApi,
  saleApi,
  taxInvoiceApi,
  quotationApi,
  productApi,
  purchaseApi,
  paymentApi,
  dashboardApi,
} from '@/lib/api/erp-api';
import type {
  Customer,
  Product,
  Sale,
  Purchase,
  TaxInvoice,
  Quotation,
  Payment,
  DashboardStats,
} from '@/lib/api/erp-api';

// ============================================
// 타입 정의
// ============================================

interface FetchSalesOptions {
  start_date?: string;
  end_date?: string;
  customer_id?: string;
  status?: string;
}

interface FetchTaxInvoicesOptions {
  start_date?: string;
  end_date?: string;
  invoice_type?: string;
  status?: string;
}

interface FetchPurchasesOptions {
  start_date?: string;
  end_date?: string;
  supplier_id?: string;
  status?: string;
}

// ============================================
// Store State 타입
// ============================================

interface ERPState {
  // 데이터
  sales: Sale[];
  customers: Customer[];
  products: Product[];
  purchases: Purchase[];
  taxInvoices: TaxInvoice[];
  quotations: Quotation[];
  payments: Payment[];
  dashboardStats: DashboardStats | null;

  // UI 상태
  loading: boolean;
  error: string | null;

  // Actions
  fetchSales: (options?: FetchSalesOptions) => Promise<void>;
  fetchCustomers: () => Promise<void>;
  fetchProducts: () => Promise<void>;
  fetchPurchases: (options?: FetchPurchasesOptions) => Promise<void>;
  fetchTaxInvoices: (options?: FetchTaxInvoicesOptions) => Promise<void>;
  fetchQuotations: () => Promise<void>;
  fetchPayments: (options?: { start_date?: string; end_date?: string }) => Promise<void>;
  fetchDashboardStats: () => Promise<void>;

  // CRUD Actions
  createCustomer: (data: Parameters<typeof customerApi.create>[0]) => Promise<Customer>;
  updateCustomer: (id: string, data: Parameters<typeof customerApi.update>[1]) => Promise<Customer>;
  deleteCustomer: (id: string) => Promise<void>;

  createSale: (data: Parameters<typeof saleApi.create>[0]) => Promise<Sale>;
  updateSale: (id: string, data: Parameters<typeof saleApi.update>[1]) => Promise<Sale>;
  deleteSale: (id: string) => Promise<void>;

  createProduct: (data: Parameters<typeof productApi.create>[0]) => Promise<Product>;
  updateProduct: (id: string, data: Parameters<typeof productApi.update>[1]) => Promise<Product>;
  deleteProduct: (id: string) => Promise<void>;

  // 유틸리티
  clearError: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

// ============================================
// Store 생성
// ============================================

export const useERPStore = create<ERPState>((set, get) => ({
  // 초기 상태
  sales: [],
  customers: [],
  products: [],
  purchases: [],
  taxInvoices: [],
  quotations: [],
  payments: [],
  dashboardStats: null,
  loading: false,
  error: null,

  // 매출 데이터 조회
  fetchSales: async (options?: FetchSalesOptions) => {
    set({ loading: true, error: null });
    try {
      const response = await saleApi.list({
        customer_id: options?.customer_id,
        status: options?.status,
        start_date: options?.start_date,
        end_date: options?.end_date,
      });
      set({ sales: response.items || [], loading: false });
    } catch (error) {
      console.error('[ERP Store] fetchSales error:', error);
      set({
        error: error instanceof Error ? error.message : '매출 데이터 조회 실패',
        loading: false,
      });
    }
  },

  // 거래처 데이터 조회
  fetchCustomers: async () => {
    set({ loading: true, error: null });
    try {
      const response = await customerApi.list();
      set({ customers: response.items || [], loading: false });
    } catch (error) {
      console.error('[ERP Store] fetchCustomers error:', error);
      set({
        error: error instanceof Error ? error.message : '거래처 데이터 조회 실패',
        loading: false,
      });
    }
  },

  // 상품 데이터 조회
  fetchProducts: async () => {
    set({ loading: true, error: null });
    try {
      const response = await productApi.list();
      set({ products: response.items || [], loading: false });
    } catch (error) {
      console.error('[ERP Store] fetchProducts error:', error);
      set({
        error: error instanceof Error ? error.message : '상품 데이터 조회 실패',
        loading: false,
      });
    }
  },

  // 매입 데이터 조회
  fetchPurchases: async (options?: FetchPurchasesOptions) => {
    set({ loading: true, error: null });
    try {
      const response = await purchaseApi.list({
        supplier_id: options?.supplier_id,
        status: options?.status,
        start_date: options?.start_date,
        end_date: options?.end_date,
      });
      set({ purchases: response.items || [], loading: false });
    } catch (error) {
      console.error('[ERP Store] fetchPurchases error:', error);
      set({
        error: error instanceof Error ? error.message : '매입 데이터 조회 실패',
        loading: false,
      });
    }
  },

  // 세금계산서 조회
  fetchTaxInvoices: async (options?: FetchTaxInvoicesOptions) => {
    set({ loading: true, error: null });
    try {
      const response = await taxInvoiceApi.list({
        invoice_type: options?.invoice_type,
        status: options?.status,
        start_date: options?.start_date,
        end_date: options?.end_date,
      });
      set({ taxInvoices: response.items || [], loading: false });
    } catch (error) {
      console.error('[ERP Store] fetchTaxInvoices error:', error);
      set({
        error: error instanceof Error ? error.message : '세금계산서 조회 실패',
        loading: false,
      });
    }
  },

  // 견적서 조회
  fetchQuotations: async () => {
    set({ loading: true, error: null });
    try {
      const response = await quotationApi.list();
      set({ quotations: response.items || [], loading: false });
    } catch (error) {
      console.error('[ERP Store] fetchQuotations error:', error);
      set({
        error: error instanceof Error ? error.message : '견적서 조회 실패',
        loading: false,
      });
    }
  },

  // 수금/지급 조회
  fetchPayments: async (options?: { start_date?: string; end_date?: string }) => {
    set({ loading: true, error: null });
    try {
      const response = await paymentApi.list({
        start_date: options?.start_date,
        end_date: options?.end_date,
      });
      set({ payments: response.items || [], loading: false });
    } catch (error) {
      console.error('[ERP Store] fetchPayments error:', error);
      set({
        error: error instanceof Error ? error.message : '수금/지급 조회 실패',
        loading: false,
      });
    }
  },

  // 대시보드 통계 조회
  fetchDashboardStats: async () => {
    set({ loading: true, error: null });
    try {
      const stats = await dashboardApi.getStats();
      set({ dashboardStats: stats, loading: false });
    } catch (error) {
      console.error('[ERP Store] fetchDashboardStats error:', error);
      set({
        error: error instanceof Error ? error.message : '대시보드 통계 조회 실패',
        loading: false,
      });
    }
  },

  // CRUD - 거래처
  createCustomer: async (data) => {
    set({ loading: true, error: null });
    try {
      const customer = await customerApi.create(data);
      set((state) => ({
        customers: [...state.customers, customer],
        loading: false,
      }));
      return customer;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '거래처 생성 실패',
        loading: false,
      });
      throw error;
    }
  },

  updateCustomer: async (id, data) => {
    set({ loading: true, error: null });
    try {
      const customer = await customerApi.update(id, data);
      set((state) => ({
        customers: state.customers.map((c) => (c.id === id ? customer : c)),
        loading: false,
      }));
      return customer;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '거래처 수정 실패',
        loading: false,
      });
      throw error;
    }
  },

  deleteCustomer: async (id) => {
    set({ loading: true, error: null });
    try {
      await customerApi.delete(id);
      set((state) => ({
        customers: state.customers.filter((c) => c.id !== id),
        loading: false,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '거래처 삭제 실패',
        loading: false,
      });
      throw error;
    }
  },

  // CRUD - 매출
  createSale: async (data) => {
    set({ loading: true, error: null });
    try {
      const sale = await saleApi.create(data);
      set((state) => ({
        sales: [...state.sales, sale],
        loading: false,
      }));
      return sale;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '매출 생성 실패',
        loading: false,
      });
      throw error;
    }
  },

  updateSale: async (id, data) => {
    set({ loading: true, error: null });
    try {
      const sale = await saleApi.update(id, data);
      set((state) => ({
        sales: state.sales.map((s) => (s.id === id ? sale : s)),
        loading: false,
      }));
      return sale;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '매출 수정 실패',
        loading: false,
      });
      throw error;
    }
  },

  deleteSale: async (id) => {
    set({ loading: true, error: null });
    try {
      await saleApi.delete(id);
      set((state) => ({
        sales: state.sales.filter((s) => s.id !== id),
        loading: false,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '매출 삭제 실패',
        loading: false,
      });
      throw error;
    }
  },

  // CRUD - 상품
  createProduct: async (data) => {
    set({ loading: true, error: null });
    try {
      const product = await productApi.create(data);
      set((state) => ({
        products: [...state.products, product],
        loading: false,
      }));
      return product;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '상품 생성 실패',
        loading: false,
      });
      throw error;
    }
  },

  updateProduct: async (id, data) => {
    set({ loading: true, error: null });
    try {
      const product = await productApi.update(id, data);
      set((state) => ({
        products: state.products.map((p) => (p.id === id ? product : p)),
        loading: false,
      }));
      return product;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '상품 수정 실패',
        loading: false,
      });
      throw error;
    }
  },

  deleteProduct: async (id) => {
    set({ loading: true, error: null });
    try {
      await productApi.delete(id);
      set((state) => ({
        products: state.products.filter((p) => p.id !== id),
        loading: false,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '상품 삭제 실패',
        loading: false,
      });
      throw error;
    }
  },

  // 유틸리티 함수
  clearError: () => set({ error: null }),
  setLoading: (loading: boolean) => set({ loading }),
  setError: (error: string | null) => set({ error }),
}));

// ============================================
// Selector Hooks (성능 최적화)
// ============================================

export const useSales = () => useERPStore((state) => state.sales);
export const useCustomers = () => useERPStore((state) => state.customers);
export const useProducts = () => useERPStore((state) => state.products);
export const usePurchases = () => useERPStore((state) => state.purchases);
export const useTaxInvoices = () => useERPStore((state) => state.taxInvoices);
export const useQuotations = () => useERPStore((state) => state.quotations);
export const usePayments = () => useERPStore((state) => state.payments);
export const useDashboardStats = () => useERPStore((state) => state.dashboardStats);
export const useERPLoading = () => useERPStore((state) => state.loading);
export const useERPError = () => useERPStore((state) => state.error);

// ============================================
// 복합 훅 (편의 기능)
// ============================================

export const useLoadDashboardData = () => {
  const store = useERPStore();

  const loadAll = async () => {
    await Promise.all([
      store.fetchSales(),
      store.fetchCustomers(),
      store.fetchProducts(),
      store.fetchPurchases(),
      store.fetchTaxInvoices(),
      store.fetchQuotations(),
      store.fetchDashboardStats(),
    ]);
  };

  return { loadAll, loading: store.loading, error: store.error };
};

export default useERPStore;
