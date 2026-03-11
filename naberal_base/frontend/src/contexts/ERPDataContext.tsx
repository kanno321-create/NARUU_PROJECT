"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";
import { fetchAPI } from "@/lib/api";

// ============= 타입 정의 =============

export interface Customer {
  id: string;
  code: string;
  name: string;
  customer_type: "매출처" | "매입처" | "매입매출처";
  grade?: string;
  business_number?: string;
  ceo_name?: string;
  contact_person?: string;
  phone?: string;
  fax?: string;
  email?: string;
  address?: string;
  credit_limit?: string;
  current_receivable?: number;
  payment_terms?: string;
  memo?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface Product {
  id: string;
  code: string;
  name: string;
  category?: string;
  specification?: string;
  unit?: string;
  purchase_price?: number;
  selling_price?: number;
  stock_quantity?: number;
  min_stock?: number;
  max_stock?: number;
  warehouse?: string;
  barcode?: string;
  memo?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface SaleItem {
  product_id: string;
  product_code: string;
  product_name: string;
  specification?: string;
  quantity: number;
  unit?: string;
  unit_price: number;
  supply_amount: number;
  tax_amount: number;
  total_amount: number;
  memo?: string;
}

export interface Sale {
  id: string;
  slip_number: string;
  slip_date: string;
  customer_id: string;
  customer_code: string;
  customer_name: string;
  sale_type: "현금" | "카드" | "외상" | "기타";
  items: SaleItem[];
  supply_total: number;
  tax_total: number;
  grand_total: number;
  received_amount?: number;
  outstanding_amount?: number;
  payment_status: "미수금" | "부분결제" | "완료";
  memo?: string;
  created_by?: string;
  created_at: string;
  updated_at?: string;
}

export interface Employee {
  id: string;
  code: string;
  name: string;
  department?: string;
  position?: string;
  phone?: string;
  email?: string;
  hire_date?: string;
  is_active: boolean;
}

export interface BankAccount {
  id: string;
  bank_name: string;
  account_number: string;
  account_holder: string;
  balance?: number;
  memo?: string;
  is_active: boolean;
}

export interface CompanyInfo {
  companyName: string;
  ceoName: string;
  businessNumber: string;
  businessType: string;
  businessCategory: string;
  zipCode: string;
  address: string;
  addressDetail: string;
  tel: string;
  fax: string;
  email: string;
  website: string;
  logo: string;
}

// ============= Context 타입 =============

interface ERPDataContextType {
  // 고객/거래처 데이터
  customers: Customer[];
  customersLoading: boolean;
  customersError: string | null;
  fetchCustomers: () => Promise<void>;
  addCustomer: (customer: Omit<Customer, "id" | "created_at" | "updated_at">) => Promise<Customer | null>;
  updateCustomer: (id: string, customer: Partial<Customer>) => Promise<Customer | null>;
  deleteCustomer: (id: string) => Promise<boolean>;
  getCustomerById: (id: string) => Customer | undefined;
  getCustomerByCode: (code: string) => Customer | undefined;
  searchCustomers: (query: string) => Customer[];

  // 상품 데이터
  products: Product[];
  productsLoading: boolean;
  productsError: string | null;
  fetchProducts: () => Promise<void>;
  addProduct: (product: Omit<Product, "id" | "created_at" | "updated_at">) => Promise<Product | null>;
  updateProduct: (id: string, product: Partial<Product>) => Promise<Product | null>;
  deleteProduct: (id: string) => Promise<boolean>;
  getProductById: (id: string) => Product | undefined;
  getProductByCode: (code: string) => Product | undefined;
  searchProducts: (query: string) => Product[];

  // 매출 데이터
  sales: Sale[];
  salesLoading: boolean;
  salesError: string | null;
  fetchSales: (params?: { start_date?: string; end_date?: string; customer_id?: string }) => Promise<void>;
  addSale: (sale: Omit<Sale, "id" | "created_at" | "updated_at">) => Promise<Sale | null>;
  updateSale: (id: string, sale: Partial<Sale>) => Promise<Sale | null>;
  deleteSale: (id: string) => Promise<boolean>;
  getSaleById: (id: string) => Sale | undefined;
  getSalesByCustomerId: (customerId: string) => Sale[];

  // 직원 데이터
  employees: Employee[];
  employeesLoading: boolean;
  fetchEmployees: () => Promise<void>;
  addEmployee: (data: Partial<Employee>) => Promise<Employee | null>;
  updateEmployee: (id: string, data: Partial<Employee>) => Promise<Employee | null>;
  deleteEmployee: (id: string) => Promise<boolean>;

  // 은행계좌 데이터
  bankAccounts: BankAccount[];
  bankAccountsLoading: boolean;
  fetchBankAccounts: () => Promise<void>;
  addBankAccount: (data: Partial<BankAccount>) => Promise<BankAccount | null>;
  updateBankAccount: (id: string, data: Partial<BankAccount>) => Promise<BankAccount | null>;
  deleteBankAccount: (id: string) => Promise<boolean>;

  // 자사 정보
  companyInfo: CompanyInfo;
  companyInfoLoading: boolean;
  fetchCompanyInfo: () => Promise<void>;
  updateCompanyInfo: (info: Partial<CompanyInfo>) => void;
  saveCompanyInfo: (info: CompanyInfo) => Promise<boolean>;

  // 유틸리티
  refreshAll: () => Promise<void>;
  isInitialized: boolean;
}

const ERPDataContext = createContext<ERPDataContextType | undefined>(undefined);

// ============= Provider 컴포넌트 =============

export function ERPDataProvider({ children }: { children: ReactNode }) {
  // 고객 상태
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [customersLoading, setCustomersLoading] = useState(false);
  const [customersError, setCustomersError] = useState<string | null>(null);

  // 상품 상태
  const [products, setProducts] = useState<Product[]>([]);
  const [productsLoading, setProductsLoading] = useState(false);
  const [productsError, setProductsError] = useState<string | null>(null);

  // 매출 상태
  const [sales, setSales] = useState<Sale[]>([]);
  const [salesLoading, setSalesLoading] = useState(false);
  const [salesError, setSalesError] = useState<string | null>(null);

  // 직원 상태
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [employeesLoading, setEmployeesLoading] = useState(false);

  // 은행계좌 상태
  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
  const [bankAccountsLoading, setBankAccountsLoading] = useState(false);

  // 자사 정보 상태 (localStorage 캐시 + DB 최종 권한)
  const [companyInfo, setCompanyInfo] = useState<CompanyInfo>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("companyInfo");
      if (saved) {
        try { return JSON.parse(saved) as CompanyInfo; } catch { /* fall through */ }
      }
    }
    return {
      companyName: "", ceoName: "", businessNumber: "", businessType: "",
      businessCategory: "", zipCode: "", address: "", addressDetail: "",
      tel: "", fax: "", email: "", website: "", logo: "",
    };
  });
  const [companyInfoLoading, setCompanyInfoLoading] = useState(false);

  const [isInitialized, setIsInitialized] = useState(false);

  // ============= 고객 API 함수 =============

  const fetchCustomers = useCallback(async () => {
    setCustomersLoading(true);
    setCustomersError(null);
    try {
      const data = await fetchAPI<any>("/v1/erp/customers?limit=5000");
      const customersData = data.items ?? data.customers ?? data;
      setCustomers(Array.isArray(customersData) ? customersData : []);
    } catch (error) {
      setCustomersError(error instanceof Error ? error.message : "알 수 없는 오류");
      console.error("고객 데이터 로드 실패:", error);
    } finally {
      setCustomersLoading(false);
    }
  }, []);

  const addCustomer = useCallback(async (customer: Omit<Customer, "id" | "created_at" | "updated_at">): Promise<Customer | null> => {
    try {
      const newCustomer = await fetchAPI<Customer>("/v1/erp/customers", {
        method: "POST",
        body: JSON.stringify(customer),
      });
      setCustomers(prev => [...prev, newCustomer]);
      return newCustomer;
    } catch (error) {
      console.error("고객 등록 실패:", error);
      return null;
    }
  }, []);

  const updateCustomer = useCallback(async (id: string, customer: Partial<Customer>): Promise<Customer | null> => {
    try {
      const updatedCustomer = await fetchAPI<Customer>(`/v1/erp/customers/${id}`, {
        method: "PUT",
        body: JSON.stringify(customer),
      });
      setCustomers(prev => prev.map(c => c.id === id ? updatedCustomer : c));
      return updatedCustomer;
    } catch (error) {
      console.error("고객 수정 실패:", error);
      return null;
    }
  }, []);

  const deleteCustomer = useCallback(async (id: string): Promise<boolean> => {
    try {
      await fetchAPI<any>(`/v1/erp/customers/${id}`, {
        method: "DELETE",
      });
      setCustomers(prev => prev.filter(c => c.id !== id));
      return true;
    } catch (error) {
      console.error("고객 삭제 실패:", error);
      return false;
    }
  }, []);

  const getCustomerById = useCallback((id: string) => {
    return customers.find(c => c.id === id);
  }, [customers]);

  const getCustomerByCode = useCallback((code: string) => {
    return customers.find(c => c.code === code);
  }, [customers]);

  const searchCustomers = useCallback((query: string) => {
    const lowerQuery = query.toLowerCase();
    return customers.filter(c =>
      c.name.toLowerCase().includes(lowerQuery) ||
      c.code.toLowerCase().includes(lowerQuery) ||
      (c.business_number && c.business_number.includes(query)) ||
      (c.phone && c.phone.includes(query))
    );
  }, [customers]);

  // ============= 상품 API 함수 =============

  const fetchProducts = useCallback(async () => {
    setProductsLoading(true);
    setProductsError(null);
    try {
      const data = await fetchAPI<any>("/v1/erp/products?limit=5000");
      const productsData = data.items ?? data.products ?? data;
      setProducts(Array.isArray(productsData) ? productsData : []);
    } catch (error) {
      setProductsError(error instanceof Error ? error.message : "알 수 없는 오류");
      console.error("상품 데이터 로드 실패:", error);
    } finally {
      setProductsLoading(false);
    }
  }, []);

  const addProduct = useCallback(async (product: Omit<Product, "id" | "created_at" | "updated_at">): Promise<Product | null> => {
    try {
      const newProduct = await fetchAPI<Product>("/v1/erp/products", {
        method: "POST",
        body: JSON.stringify(product),
      });
      setProducts(prev => [...prev, newProduct]);
      return newProduct;
    } catch (error) {
      console.error("상품 등록 실패:", error);
      return null;
    }
  }, []);

  const updateProduct = useCallback(async (id: string, product: Partial<Product>): Promise<Product | null> => {
    try {
      const updatedProduct = await fetchAPI<Product>(`/v1/erp/products/${id}`, {
        method: "PUT",
        body: JSON.stringify(product),
      });
      setProducts(prev => prev.map(p => p.id === id ? updatedProduct : p));
      return updatedProduct;
    } catch (error) {
      console.error("상품 수정 실패:", error);
      return null;
    }
  }, []);

  const deleteProduct = useCallback(async (id: string): Promise<boolean> => {
    try {
      await fetchAPI<any>(`/v1/erp/products/${id}`, {
        method: "DELETE",
      });
      setProducts(prev => prev.filter(p => p.id !== id));
      return true;
    } catch (error) {
      console.error("상품 삭제 실패:", error);
      return false;
    }
  }, []);

  const getProductById = useCallback((id: string) => {
    return products.find(p => p.id === id);
  }, [products]);

  const getProductByCode = useCallback((code: string) => {
    return products.find(p => p.code === code);
  }, [products]);

  const searchProducts = useCallback((query: string) => {
    const lowerQuery = query.toLowerCase();
    return products.filter(p =>
      p.name.toLowerCase().includes(lowerQuery) ||
      p.code.toLowerCase().includes(lowerQuery) ||
      (p.category && p.category.toLowerCase().includes(lowerQuery)) ||
      (p.barcode && p.barcode.includes(query))
    );
  }, [products]);

  // ============= 매출 API 함수 =============

  const fetchSales = useCallback(async (params?: { start_date?: string; end_date?: string; customer_id?: string }) => {
    setSalesLoading(true);
    setSalesError(null);
    try {
      const queryParams = new URLSearchParams();
      if (params?.start_date) queryParams.append("start_date", params.start_date);
      if (params?.end_date) queryParams.append("end_date", params.end_date);
      if (params?.customer_id) queryParams.append("customer_id", params.customer_id);

      const endpoint = `/v1/erp/sales${queryParams.toString() ? `?${queryParams}` : ""}`;
      const data = await fetchAPI<any>(endpoint);
      const salesData = data.items ?? data.sales ?? data;
      setSales(Array.isArray(salesData) ? salesData : []);
    } catch (error) {
      setSalesError(error instanceof Error ? error.message : "알 수 없는 오류");
      console.error("매출 데이터 로드 실패:", error);
    } finally {
      setSalesLoading(false);
    }
  }, []);

  const addSale = useCallback(async (sale: Omit<Sale, "id" | "created_at" | "updated_at">): Promise<Sale | null> => {
    try {
      const newSale = await fetchAPI<Sale>("/v1/erp/sales", {
        method: "POST",
        body: JSON.stringify(sale),
      });
      setSales(prev => [...prev, newSale]);
      return newSale;
    } catch (error) {
      console.error("매출 등록 실패:", error);
      return null;
    }
  }, []);

  const updateSale = useCallback(async (id: string, sale: Partial<Sale>): Promise<Sale | null> => {
    try {
      const updatedSale = await fetchAPI<Sale>(`/v1/erp/sales/${id}`, {
        method: "PUT",
        body: JSON.stringify(sale),
      });
      setSales(prev => prev.map(s => s.id === id ? updatedSale : s));
      return updatedSale;
    } catch (error) {
      console.error("매출 수정 실패:", error);
      return null;
    }
  }, []);

  const deleteSale = useCallback(async (id: string): Promise<boolean> => {
    try {
      await fetchAPI<any>(`/v1/erp/sales/${id}`, {
        method: "DELETE",
      });
      setSales(prev => prev.filter(s => s.id !== id));
      return true;
    } catch (error) {
      console.error("매출 삭제 실패:", error);
      return false;
    }
  }, []);

  const getSaleById = useCallback((id: string) => {
    return sales.find(s => s.id === id);
  }, [sales]);

  const getSalesByCustomerId = useCallback((customerId: string) => {
    return sales.filter(s => s.customer_id === customerId);
  }, [sales]);

  // ============= 직원 API 함수 =============

  const fetchEmployees = useCallback(async () => {
    setEmployeesLoading(true);
    try {
      const data = await fetchAPI<any>("/v1/erp/employees");
      const employeesData = Array.isArray(data) ? data : (data.employees ?? []);
      setEmployees(employeesData);
    } catch (error) {
      console.error("직원 데이터 로드 실패:", error);
    } finally {
      setEmployeesLoading(false);
    }
  }, []);

  const addEmployee = useCallback(async (empData: Partial<Employee>): Promise<Employee | null> => {
    try {
      const result = await fetchAPI<Employee>("/v1/erp/employees", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(empData),
      });
      await fetchEmployees();
      return result;
    } catch (error) {
      console.error("직원 등록 실패:", error);
      return null;
    }
  }, [fetchEmployees]);

  const updateEmployee = useCallback(async (id: string, empData: Partial<Employee>): Promise<Employee | null> => {
    try {
      const result = await fetchAPI<Employee>(`/v1/erp/employees/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(empData),
      });
      await fetchEmployees();
      return result;
    } catch (error) {
      console.error("직원 수정 실패:", error);
      return null;
    }
  }, [fetchEmployees]);

  const deleteEmployee = useCallback(async (id: string): Promise<boolean> => {
    try {
      await fetchAPI<void>(`/v1/erp/employees/${id}`, { method: "DELETE" });
      await fetchEmployees();
      return true;
    } catch (error) {
      console.error("직원 삭제 실패:", error);
      return false;
    }
  }, [fetchEmployees]);

  // ============= 은행계좌 API 함수 =============

  const fetchBankAccounts = useCallback(async () => {
    setBankAccountsLoading(true);
    try {
      const data = await fetchAPI<any>("/v1/erp/bank-accounts");
      const accountsData = Array.isArray(data) ? data : (data.accounts ?? []);
      setBankAccounts(accountsData);
    } catch (error) {
      console.error("계좌 데이터 로드 실패:", error);
    } finally {
      setBankAccountsLoading(false);
    }
  }, []);

  const addBankAccount = useCallback(async (accData: Partial<BankAccount>): Promise<BankAccount | null> => {
    try {
      const result = await fetchAPI<BankAccount>("/v1/erp/bank-accounts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          account_no: accData.account_number || accData.account_no || "",
          bank_name: accData.bank_name || "",
          account_name: accData.account_name || "",
          holder_name: accData.account_holder || accData.holder_name || "",
          balance: accData.balance || 0,
          is_active: accData.is_active !== false,
          memo: accData.memo || "",
        }),
      });
      await fetchBankAccounts();
      return result as any;
    } catch (error) {
      console.error("계좌 등록 실패:", error);
      return null;
    }
  }, [fetchBankAccounts]);

  const updateBankAccount = useCallback(async (id: string, accData: Partial<BankAccount>): Promise<BankAccount | null> => {
    try {
      const payload: Record<string, unknown> = {};
      if (accData.bank_name !== undefined) payload.bank_name = accData.bank_name;
      if (accData.account_number !== undefined) payload.account_no = accData.account_number;
      if ((accData as any).account_no !== undefined) payload.account_no = (accData as any).account_no;
      if (accData.account_holder !== undefined) payload.holder_name = accData.account_holder;
      if ((accData as any).holder_name !== undefined) payload.holder_name = (accData as any).holder_name;
      if ((accData as any).account_name !== undefined) payload.account_name = (accData as any).account_name;
      if (accData.balance !== undefined) payload.balance = accData.balance;
      if (accData.is_active !== undefined) payload.is_active = accData.is_active;
      if (accData.memo !== undefined) payload.memo = accData.memo;

      const result = await fetchAPI<BankAccount>(`/v1/erp/bank-accounts/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      await fetchBankAccounts();
      return result as any;
    } catch (error) {
      console.error("계좌 수정 실패:", error);
      return null;
    }
  }, [fetchBankAccounts]);

  const deleteBankAccount = useCallback(async (id: string): Promise<boolean> => {
    try {
      await fetchAPI<void>(`/v1/erp/bank-accounts/${id}`, { method: "DELETE" });
      await fetchBankAccounts();
      return true;
    } catch (error) {
      console.error("계좌 삭제 실패:", error);
      return false;
    }
  }, [fetchBankAccounts]);

  // ============= 자사 정보 API 함수 =============

  const fetchCompanyInfo = useCallback(async () => {
    setCompanyInfoLoading(true);
    try {
      const data = await fetchAPI<any>("/v1/erp/company");
      if (data) {
        const mapped: CompanyInfo = {
          companyName: data.name || "",
          ceoName: data.ceo || "",
          businessNumber: data.business_number || "",
          businessType: data.business_type || "",
          businessCategory: data.business_item || "",
          zipCode: "",
          address: data.address || "",
          addressDetail: "",
          tel: data.tel || "",
          fax: data.fax || "",
          email: data.email || "",
          website: "",
          logo: data.logo_path || "",
        };
        setCompanyInfo(mapped);
        localStorage.setItem("companyInfo", JSON.stringify(mapped));
      }
    } catch {
      // DB에 자사정보 미등록 → localStorage 값 유지
    } finally {
      setCompanyInfoLoading(false);
    }
  }, []);

  const updateCompanyInfo = useCallback((update: Partial<CompanyInfo>) => {
    setCompanyInfo(prev => {
      const next = { ...prev, ...update };
      localStorage.setItem("companyInfo", JSON.stringify(next));
      return next;
    });
  }, []);

  const saveCompanyInfo = useCallback(async (info: CompanyInfo): Promise<boolean> => {
    const payload = {
      business_number: info.businessNumber || "000-00-00000",
      name: info.companyName,
      ceo: info.ceoName,
      address: [info.address, info.addressDetail].filter(Boolean).join(" "),
      tel: info.tel,
      fax: info.fax,
      email: info.email,
      business_type: info.businessType,
      business_item: info.businessCategory,
      logo_path: info.logo,
    };
    try {
      // PUT으로 수정 시도, 404면 POST로 등록
      try {
        await fetchAPI<any>("/v1/erp/company", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      } catch {
        await fetchAPI<any>("/v1/erp/company", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      }
      localStorage.setItem("companyInfo", JSON.stringify(info));
      return true;
    } catch (error) {
      console.error("자사정보 저장 실패:", error);
      return false;
    }
  }, []);

  // ============= 전체 새로고침 =============

  const refreshAll = useCallback(async () => {
    await Promise.all([
      fetchCustomers(),
      fetchProducts(),
      fetchSales(),
      fetchEmployees(),
      fetchBankAccounts(),
      fetchCompanyInfo(),
    ]);
  }, [fetchCustomers, fetchProducts, fetchSales, fetchEmployees, fetchBankAccounts, fetchCompanyInfo]);

  // ============= 초기 로드 =============

  useEffect(() => {
    const initializeData = async () => {
      await refreshAll();
      setIsInitialized(true);
    };
    initializeData();
  }, [refreshAll]);

  // ERP 설정 변경 이벤트 리스너 (10개 설정 윈도우가 dispatch)
  useEffect(() => {
    const handleSettingsUpdate = () => {
      refreshAll();
    };
    window.addEventListener("kis-erp-settings-updated", handleSettingsUpdate);
    return () => {
      window.removeEventListener("kis-erp-settings-updated", handleSettingsUpdate);
    };
  }, [refreshAll]);

  const value: ERPDataContextType = {
    // 고객
    customers,
    customersLoading,
    customersError,
    fetchCustomers,
    addCustomer,
    updateCustomer,
    deleteCustomer,
    getCustomerById,
    getCustomerByCode,
    searchCustomers,
    // 상품
    products,
    productsLoading,
    productsError,
    fetchProducts,
    addProduct,
    updateProduct,
    deleteProduct,
    getProductById,
    getProductByCode,
    searchProducts,
    // 매출
    sales,
    salesLoading,
    salesError,
    fetchSales,
    addSale,
    updateSale,
    deleteSale,
    getSaleById,
    getSalesByCustomerId,
    // 직원
    employees,
    employeesLoading,
    fetchEmployees,
    addEmployee,
    updateEmployee,
    deleteEmployee,
    // 계좌
    bankAccounts,
    bankAccountsLoading,
    fetchBankAccounts,
    addBankAccount,
    updateBankAccount,
    deleteBankAccount,
    // 자사 정보
    companyInfo,
    companyInfoLoading,
    fetchCompanyInfo,
    updateCompanyInfo,
    saveCompanyInfo,
    // 유틸리티
    refreshAll,
    isInitialized,
  };

  return <ERPDataContext.Provider value={value}>{children}</ERPDataContext.Provider>;
}

// ============= Hook =============

export function useERPData() {
  const context = useContext(ERPDataContext);
  if (context === undefined) {
    throw new Error("useERPData must be used within an ERPDataProvider");
  }
  return context;
}

export default ERPDataContext;
