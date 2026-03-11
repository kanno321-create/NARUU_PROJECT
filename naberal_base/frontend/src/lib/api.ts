
import { QuoteData } from "@/app/quote/page";

// 브라우저: Next.js rewrite 프록시(/api/v1/* → Railway), Electron: 직접 호출
const IS_ELECTRON = typeof window !== "undefined" && !!(window as any).electronAPI;
const IS_BROWSER = typeof window !== "undefined" && !IS_ELECTRON;
const API_BASE_URL = IS_BROWSER ? "/api" : (process.env.NEXT_PUBLIC_API_URL || "https://naberalproject-production.up.railway.app");

// --- Types (Matching Backend Pydantic Models) ---

export interface BreakerInput {
    breaker_type: "MCCB" | "ELB";  // 차단기 종류 (백엔드에서 모델명 자동 조회)
    ampere: number;
    poles: 2 | 3 | 4;
    quantity: number;
    model?: string;  // Optional: 백엔드에서 카탈로그 기반 자동 조회
}

export interface AccessoryInput {
    type: "magnet" | "timer" | "meter" | "spd" | "switch";
    model: string;
    quantity: number;
}

export interface CustomSize {
    width_mm: number;
    height_mm: number;
    depth_mm: number;
}

export interface EnclosureInput {
    type: "옥내노출" | "옥외노출" | "옥내자립" | "옥외자립" | "매입함" | "전주부착형" | "FRP함" | "하이박스";
    material: "STEEL 1.0T" | "STEEL 1.6T" | "STEEL 2.0T" | "SUS201 1.0T" | "SUS201 1.2T" | "SUS201 1.5T" | "SUS304 1.2T" | "SUS304 1.5T" | "SUS304 2.0T";
    custom_size?: CustomSize | null;
}

export interface PanelInput {
    panel_name?: string | null;
    main_breaker: BreakerInput;
    branch_breakers: BreakerInput[];
    accessories?: AccessoryInput[] | null;
    enclosure: EnclosureInput;
}

export interface EstimateOptions {
    breaker_brand_preference?: "SANGDO" | "LS" | null;
    use_economy_series?: boolean;
    include_evidence_pack?: boolean;
}

export interface EstimateRequest {
    customer_name: string;
    project_name?: string | null;
    panels: PanelInput[];
    options?: EstimateOptions | null;
}

// --- Response Types ---

// Line item from backend (견적 품목)
export interface LineItemResponse {
    name: string;      // 품목명
    spec: string;      // 규격
    quantity: number;  // 수량
    unit: string;      // 단위
    unit_price: number; // 단가
    supply_price: number; // 공급가액
}

// Panel response from backend (분전반별 상세 견적)
export interface PanelResponse {
    panel_id: string;
    panel_name?: string;  // 분전반명 (선택적)
    total_price: number;
    items: LineItemResponse[];
}

export interface PipelineResults {
    stage_1_enclosure: { status: "passed" | "failed"; fit_score: number; enclosure_size: number[] };
    stage_2_breaker: { status: "passed" | "failed"; phase_balance: number; clearance_violations: number; thermal_violations: number };
    stage_3_format: { status: "passed" | "failed"; formula_preservation: number };
    stage_4_cover: { status: "passed" | "failed"; cover_compliance: number };
    stage_5_doc_lint: { status: "passed" | "failed"; lint_errors: number };
}

// Note: LineItemResponse, PanelResponse are defined above

export interface ValidationChecks {
    CHK_BUNDLE_MAGNET: "passed" | "failed" | "skipped";
    CHK_BUNDLE_TIMER: "passed" | "failed" | "skipped";
    CHK_ENCLOSURE_H_FORMULA: "passed" | "failed";
    CHK_PHASE_BALANCE: "passed" | "failed";
    CHK_CLEARANCE_VIOLATIONS: "passed" | "failed";
    CHK_THERMAL_VIOLATIONS: "passed" | "failed";
    CHK_FORMULA_PRESERVATION: "passed" | "failed";
}

export interface EstimateResponse {
    id?: string;  // 견적 ID (별칭, estimate_id와 동일)
    estimate_id: string;
    status: "completed" | "failed" | "processing";
    created_at: string;
    pipeline_results: PipelineResults;
    validation_checks: ValidationChecks;
    documents?: { excel_url?: string | null; pdf_url?: string | null } | null;
    evidence?: { evidence_pack_url?: string | null; sha256?: string | null } | null;
    total_price: number;
    total_price_with_vat: number;
    panels?: PanelResponse[] | null;  // 분전반별 상세 견적 (BOM)
}

// --- API Functions ---

/**
 * localStorage에서 Bearer 토큰을 읽어 Authorization 헤더를 생성한다.
 * SSR 환경(window 없음)에서는 빈 객체를 반환하여 안전하게 건너뗴다.
 */
export function getAuthHeaders(): Record<string, string> {
    if (typeof window === "undefined") return {};
    const token = localStorage.getItem("kis-access-token");
    if (!token) return {};
    return { Authorization: `Bearer ${token}` };
}

export async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...getAuthHeaders(),
            ...options?.headers,
        },
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        // Backend returns {code, message, meta} OR {detail} format
        const message = errorData.message || (typeof errorData.detail === 'string' ? errorData.detail : errorData.detail?.message);
        throw new Error(message || `API Error: ${response.statusText}`);
    }

    return response.json();
}

// --- ERP Types (Matching Backend erp.py) ---

export interface ERPProduct {
    id: string;
    code: string;
    name: string;
    spec: string | null;
    unit: string;
    category_id: string | null;
    purchase_price: number;
    selling_price: number;
    safety_stock: number;
    memo: string | null;
    is_active: boolean;
    created_at: string;
    updated_at: string | null;
}

export interface ProductListResponse {
    items: ERPProduct[];
    total: number;
}

export interface ERPCustomer {
    id: string;
    code: string;
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
    credit_limit: number;
    current_receivable: number;
    payment_terms: string | null;
    memo: string | null;
    is_active: boolean;
    created_at: string;
    updated_at: string | null;
}

export interface CustomerListResponse {
    items: ERPCustomer[];
    total: number;
}

// --- Sale (매출전표) Types ---

export interface ERPSaleItem {
    product_id?: string | null;
    product_code?: string | null;
    product_name: string;
    spec?: string | null;
    unit: string;
    quantity: number;
    unit_price: number;
    supply_amount: number;
    tax_amount: number;
    total_amount: number;
    cost_price?: number;
    memo?: string | null;
}

export interface ERPSaleCreate {
    sale_date: string;
    customer_id: string;
    status?: string;
    memo?: string | null;
    items: ERPSaleItem[];
}

export interface ERPSale {
    id: string;
    sale_number: string;
    sale_date: string;
    customer_id: string;
    status: string;
    supply_amount: number;
    tax_amount: number;
    total_amount: number;
    cost_amount: number;
    profit_amount: number;
    memo?: string | null;
    items: ERPSaleItem[];
    customer?: ERPCustomer | null;
    created_at: string;
    updated_at?: string | null;
    warning?: {
        type: string;
        threshold: number;
        usage_percent: number;
        message: string;
    } | null;
    error?: {
        code: string;
        message: string;
        credit_limit?: number;
        attempted_receivable?: number;
    } | null;
}

export interface SaleListResponse {
    items: ERPSale[];
    total: number;
}

// --- Purchase (매입) Types ---

export interface ERPPurchaseItem {
    product_id?: string | null;
    product_code?: string | null;
    product_name: string;
    spec?: string | null;
    unit: string;
    quantity: number;
    unit_price: number;
    supply_amount: number;
    tax_amount: number;
    total_amount: number;
    memo?: string | null;
}

export interface ERPPurchaseCreate {
    purchase_date: string;
    supplier_id: string;
    status?: string;
    memo?: string | null;
    items: ERPPurchaseItem[];
}

export interface ERPPurchase {
    id: string;
    purchase_number: string | null;
    purchase_date: string;
    supplier_id: string;
    status: string;
    supply_amount: number;
    tax_amount: number;
    total_amount: number;
    memo?: string | null;
    items: ERPPurchaseItem[];
    supplier?: ERPCustomer | null;
    created_at: string;
    updated_at?: string | null;
}

export interface PurchaseListResponse {
    items: ERPPurchase[];
    total: number;
}

// --- Payment (수금/지급) Types ---

export interface ERPPaymentCreate {
    payment_type: string;
    payment_date: string;
    customer_id: string;
    amount: number;
    payment_method?: string;
    status?: string;
    completed_date?: string | null;
    reference_type?: string | null;
    reference_id?: string | null;
    memo?: string | null;
}

export interface ERPPayment {
    id: string;
    payment_number: string | null;
    payment_type: string;
    payment_date: string;
    customer_id: string;
    amount: number;
    payment_method: string;
    status: string;
    completed_date?: string | null;
    reference_type?: string | null;
    reference_id?: string | null;
    memo?: string | null;
    customer?: ERPCustomer | null;
    created_at: string;
    updated_at?: string | null;
}

export interface PaymentListResponse {
    items: ERPPayment[];
    total: number;
}

// --- TaxInvoice (세금계산서) Types ---

export interface ERPTaxInvoiceCreate {
    invoice_type?: string;
    issue_date: string;
    customer_id: string;
    supply_amount: number;
    tax_amount: number;
    total_amount: number;
    status?: string;
    reference_type?: string | null;
    reference_id?: string | null;
    memo?: string | null;
}

export interface ERPTaxInvoice {
    id: string;
    invoice_number: string | null;
    invoice_type: string;
    issue_date: string;
    customer_id: string;
    supply_amount: number;
    tax_amount: number;
    total_amount: number;
    status: string;
    reference_type?: string | null;
    reference_id?: string | null;
    memo?: string | null;
    customer?: ERPCustomer | null;
    created_at: string;
    updated_at?: string | null;
}

export interface TaxInvoiceListResponse {
    items: ERPTaxInvoice[];
    total: number;
}

export interface UnissuedCustomer {
    customer_id: string;
    customer_name: string;
    business_number: string | null;
    representative: string | null;
    total_sales_amount: number;
    total_supply_amount: number;
    total_tax_amount: number;
    sale_count: number;
}

export interface UnissuedCustomerListResponse {
    items: UnissuedCustomer[];
    total: number;
}

// --- Dashboard Types ---

export interface ERPDashboardStats {
    success: boolean;
    stats: {
        monthlySales: number;
        monthlyPurchases: number;
        receivables: number;
        activeCustomers: number;
        salesChange: number;
        purchasesChange: number;
        newCustomers: number;
        overdueCount: number;
    };
    monthlyBreakdown: {
        sales: number;
        purchases: number;
        collections: number;
        payments: number;
        netProfit: number;
    };
    receivablesBreakdown: {
        within30Days: number;
        days30To60: number;
        over60Days: number;
        total: number;
    };
    inventoryStats: {
        totalItems: number;
        lowStock: number;
        overStock: number;
        normal: number;
    };
    todaySchedules: any[];
    monthlyTrend: any[];
}

export const api = {
    estimate: {
        create: (data: EstimateRequest) => {
            return fetchAPI<EstimateResponse>("/v1/estimates", {
                method: "POST",
                body: JSON.stringify(data),
            });
        },
        get: (estimateId: string) => {
            return fetchAPI<EstimateResponse>(`/v1/estimates/${estimateId}`);
        },
    },

    // ERP API
    erp: {
        products: {
            list: (params?: { search?: string; category_id?: string; is_active?: boolean; skip?: number; limit?: number }) => {
                const queryParams = new URLSearchParams();
                if (params?.search) queryParams.append("search", params.search);
                if (params?.category_id) queryParams.append("category_id", params.category_id);
                if (params?.is_active !== undefined) queryParams.append("is_active", String(params.is_active));
                if (params?.skip !== undefined) queryParams.append("skip", String(params.skip));
                if (params?.limit !== undefined) queryParams.append("limit", String(params.limit));

                const query = queryParams.toString();
                return fetchAPI<ProductListResponse>(`/v1/erp/products${query ? `?${query}` : ""}`);
            },
            get: (productId: string) => {
                return fetchAPI<ERPProduct>(`/v1/erp/products/${productId}`);
            },
            create: (data: Partial<ERPProduct>) => {
                return fetchAPI<ERPProduct>("/v1/erp/products", {
                    method: "POST",
                    body: JSON.stringify(data),
                });
            },
            update: (productId: string, data: Partial<ERPProduct>) => {
                return fetchAPI<ERPProduct>(`/v1/erp/products/${productId}`, {
                    method: "PATCH",
                    body: JSON.stringify(data),
                });
            },
            delete: (productId: string) => {
                return fetchAPI<{ message: string }>(`/v1/erp/products/${productId}`, {
                    method: "DELETE",
                });
            },
        },
        customers: {
            list: (params?: { search?: string; customer_type?: string; is_active?: boolean; skip?: number; limit?: number }) => {
                const queryParams = new URLSearchParams();
                if (params?.search) queryParams.append("search", params.search);
                if (params?.customer_type) queryParams.append("customer_type", params.customer_type);
                if (params?.is_active !== undefined) queryParams.append("is_active", String(params.is_active));
                if (params?.skip !== undefined) queryParams.append("skip", String(params.skip));
                if (params?.limit !== undefined) queryParams.append("limit", String(params.limit));

                const query = queryParams.toString();
                return fetchAPI<CustomerListResponse>(`/v1/erp/customers${query ? `?${query}` : ""}`);
            },
            get: (customerId: string) => {
                return fetchAPI<ERPCustomer>(`/v1/erp/customers/${customerId}`);
            },
            create: (data: Partial<ERPCustomer>) => {
                return fetchAPI<ERPCustomer>("/v1/erp/customers", {
                    method: "POST",
                    body: JSON.stringify(data),
                });
            },
            update: (customerId: string, data: Partial<ERPCustomer>) => {
                return fetchAPI<ERPCustomer>(`/v1/erp/customers/${customerId}`, {
                    method: "PATCH",
                    body: JSON.stringify(data),
                });
            },
            delete: (customerId: string) => {
                return fetchAPI<{ message: string }>(`/v1/erp/customers/${customerId}`, {
                    method: "DELETE",
                });
            },
        },
        sales: {
            create: (data: ERPSaleCreate) => {
                return fetchAPI<ERPSale>("/v1/erp/sales", {
                    method: "POST",
                    body: JSON.stringify(data),
                });
            },
            list: (params?: { customer_id?: string; status?: string; start_date?: string; end_date?: string; skip?: number; limit?: number }) => {
                const queryParams = new URLSearchParams();
                if (params?.customer_id) queryParams.append("customer_id", params.customer_id);
                if (params?.status) queryParams.append("status", params.status);
                if (params?.start_date) queryParams.append("start_date", params.start_date);
                if (params?.end_date) queryParams.append("end_date", params.end_date);
                if (params?.skip !== undefined) queryParams.append("skip", String(params.skip));
                if (params?.limit !== undefined) queryParams.append("limit", String(params.limit));

                const query = queryParams.toString();
                return fetchAPI<SaleListResponse>(`/v1/erp/sales${query ? `?${query}` : ""}`);
            },
            get: (saleId: string) => {
                return fetchAPI<ERPSale>(`/v1/erp/sales/${saleId}`);
            },
        },
        purchases: {
            list: (params?: { supplier_id?: string; status?: string; start_date?: string; end_date?: string; skip?: number; limit?: number }) => {
                const queryParams = new URLSearchParams();
                if (params?.supplier_id) queryParams.append("supplier_id", params.supplier_id);
                if (params?.status) queryParams.append("status", params.status);
                if (params?.start_date) queryParams.append("start_date", params.start_date);
                if (params?.end_date) queryParams.append("end_date", params.end_date);
                if (params?.skip !== undefined) queryParams.append("skip", String(params.skip));
                if (params?.limit !== undefined) queryParams.append("limit", String(params.limit));

                const query = queryParams.toString();
                return fetchAPI<PurchaseListResponse>(`/v1/erp/purchases${query ? `?${query}` : ""}`);
            },
            create: (data: ERPPurchaseCreate) => {
                return fetchAPI<ERPPurchase>("/v1/erp/purchases", {
                    method: "POST",
                    body: JSON.stringify(data),
                });
            },
            get: (purchaseId: string) => {
                return fetchAPI<ERPPurchase>(`/v1/erp/purchases/${purchaseId}`);
            },
        },
        payments: {
            list: (params?: { customer_id?: string; payment_type?: string; status?: string; start_date?: string; end_date?: string; skip?: number; limit?: number }) => {
                const queryParams = new URLSearchParams();
                if (params?.customer_id) queryParams.append("customer_id", params.customer_id);
                if (params?.payment_type) queryParams.append("payment_type", params.payment_type);
                if (params?.status) queryParams.append("status", params.status);
                if (params?.start_date) queryParams.append("start_date", params.start_date);
                if (params?.end_date) queryParams.append("end_date", params.end_date);
                if (params?.skip !== undefined) queryParams.append("skip", String(params.skip));
                if (params?.limit !== undefined) queryParams.append("limit", String(params.limit));

                const query = queryParams.toString();
                return fetchAPI<PaymentListResponse>(`/v1/erp/payments${query ? `?${query}` : ""}`);
            },
            create: (data: ERPPaymentCreate) => {
                return fetchAPI<ERPPayment>("/v1/erp/payments", {
                    method: "POST",
                    body: JSON.stringify(data),
                });
            },
        },
        dashboard: {
            stats: () => {
                return fetchAPI<ERPDashboardStats>("/v1/erp/dashboard/stats");
            },
            summary: () => {
                return fetchAPI<ERPDashboardStats>("/v1/erp/dashboard");
            },
        },
        settings: {
            getPreferences: () => {
                return fetchAPI<{ column_preferences: Record<string, string[]> }>("/v1/erp/settings/preferences");
            },
            updatePreferences: (columnPreferences: Record<string, string[]>) => {
                return fetchAPI<{ column_preferences: Record<string, string[]> }>("/v1/erp/settings/preferences", {
                    method: "PUT",
                    body: JSON.stringify({ column_preferences: columnPreferences }),
                });
            },
            getGeneral: () => {
                return fetchAPI<Record<string, unknown>>("/v1/erp/settings/general");
            },
            updateGeneral: (data: Record<string, unknown>) => {
                return fetchAPI<Record<string, unknown>>("/v1/erp/settings/general", {
                    method: "PUT",
                    body: JSON.stringify(data),
                });
            },
        },
        payroll: {
            list: (params?: { year?: number; month?: number; status?: string; skip?: number; limit?: number }) => {
                const qp = new URLSearchParams();
                if (params?.year !== undefined) qp.append("year", String(params.year));
                if (params?.status) qp.append("status", params.status);
                if (params?.skip !== undefined) qp.append("skip", String(params.skip));
                if (params?.limit !== undefined) qp.append("limit", String(params.limit));
                const q = qp.toString();
                return fetchAPI<ERPPayroll[]>(`/v1/erp/payroll${q ? `?${q}` : ""}`);
            },
            create: (data: ERPPayrollCreate) => {
                return fetchAPI<ERPPayroll>("/v1/erp/payroll", {
                    method: "POST",
                    body: JSON.stringify(data),
                });
            },
            get: (id: string) => {
                return fetchAPI<ERPPayroll>(`/v1/erp/payroll/${id}`);
            },
            getByPeriod: (year: number, month: number) => {
                return fetchAPI<ERPPayroll>(`/v1/erp/payroll/period/${year}/${month}`);
            },
            update: (id: string, data: ERPPayrollCreate) => {
                return fetchAPI<ERPPayroll>(`/v1/erp/payroll/${id}`, {
                    method: "PUT",
                    body: JSON.stringify(data),
                });
            },
            confirm: (id: string) => {
                return fetchAPI<ERPPayroll>(`/v1/erp/payroll/${id}/confirm`, {
                    method: "POST",
                });
            },
            pay: (id: string) => {
                return fetchAPI<ERPPayroll>(`/v1/erp/payroll/${id}/pay`, {
                    method: "POST",
                });
            },
            delete: (id: string) => {
                return fetchAPI<void>(`/v1/erp/payroll/${id}`, {
                    method: "DELETE",
                });
            },
        },
        taxInvoices: {
            list: (params?: { customer_id?: string; invoice_type?: string; status?: string; start_date?: string; end_date?: string; skip?: number; limit?: number }) => {
                const queryParams = new URLSearchParams();
                if (params?.customer_id) queryParams.append("customer_id", params.customer_id);
                if (params?.invoice_type) queryParams.append("invoice_type", params.invoice_type);
                if (params?.status) queryParams.append("status", params.status);
                if (params?.start_date) queryParams.append("start_date", params.start_date);
                if (params?.end_date) queryParams.append("end_date", params.end_date);
                if (params?.skip !== undefined) queryParams.append("skip", String(params.skip));
                if (params?.limit !== undefined) queryParams.append("limit", String(params.limit));

                const query = queryParams.toString();
                return fetchAPI<TaxInvoiceListResponse>(`/v1/erp/tax-invoices${query ? `?${query}` : ""}`);
            },
            create: (data: ERPTaxInvoiceCreate) => {
                return fetchAPI<ERPTaxInvoice>("/v1/erp/tax-invoices", {
                    method: "POST",
                    body: JSON.stringify(data),
                });
            },
            delete: (invoiceId: string) => {
                return fetchAPI<{ message: string; id: string }>(`/v1/erp/tax-invoices/${invoiceId}`, {
                    method: "DELETE",
                });
            },
            unissuedCustomers: (params: { start_date: string; end_date: string }) => {
                const queryParams = new URLSearchParams();
                queryParams.append("start_date", params.start_date);
                queryParams.append("end_date", params.end_date);
                return fetchAPI<UnissuedCustomerListResponse>(`/v1/erp/tax-invoices/unissued-customers?${queryParams.toString()}`);
            },
        },
        company: {
            get: () => {
                return fetchAPI<ERPCompanyInfo>("/v1/erp/company");
            },
            create: (data: Partial<ERPCompanyInfo>) => {
                return fetchAPI<ERPCompanyInfo>("/v1/erp/company", {
                    method: "POST",
                    body: JSON.stringify(data),
                });
            },
            update: (data: Partial<ERPCompanyInfo>) => {
                return fetchAPI<ERPCompanyInfo>("/v1/erp/company", {
                    method: "PUT",
                    body: JSON.stringify(data),
                });
            },
        },
        bankAccounts: {
            list: (params?: { is_active?: boolean; search?: string; skip?: number; limit?: number }) => {
                const queryParams = new URLSearchParams();
                if (params?.is_active !== undefined) queryParams.append("is_active", String(params.is_active));
                if (params?.search) queryParams.append("search", params.search);
                if (params?.skip !== undefined) queryParams.append("skip", String(params.skip));
                if (params?.limit !== undefined) queryParams.append("limit", String(params.limit));
                const query = queryParams.toString();
                return fetchAPI<ERPBankAccount[]>(`/v1/erp/bank-accounts${query ? `?${query}` : ""}`);
            },
            get: (accountId: string) => {
                return fetchAPI<ERPBankAccount>(`/v1/erp/bank-accounts/${accountId}`);
            },
            create: (data: Partial<ERPBankAccount>) => {
                return fetchAPI<ERPBankAccount>("/v1/erp/bank-accounts", {
                    method: "POST",
                    body: JSON.stringify(data),
                });
            },
            update: (accountId: string, data: Partial<ERPBankAccount>) => {
                return fetchAPI<ERPBankAccount>(`/v1/erp/bank-accounts/${accountId}`, {
                    method: "PUT",
                    body: JSON.stringify(data),
                });
            },
            delete: (accountId: string) => {
                return fetchAPI<void>(`/v1/erp/bank-accounts/${accountId}`, {
                    method: "DELETE",
                });
            },
        },
        employees: {
            list: (params?: { department?: string; status?: string; search?: string; skip?: number; limit?: number }) => {
                const queryParams = new URLSearchParams();
                if (params?.department) queryParams.append("department", params.department);
                if (params?.status) queryParams.append("status", params.status);
                if (params?.search) queryParams.append("search", params.search);
                if (params?.skip !== undefined) queryParams.append("skip", String(params.skip));
                if (params?.limit !== undefined) queryParams.append("limit", String(params.limit));
                const query = queryParams.toString();
                return fetchAPI<ERPEmployee[]>(`/v1/erp/employees${query ? `?${query}` : ""}`);
            },
            get: (employeeId: string) => {
                return fetchAPI<ERPEmployee>(`/v1/erp/employees/${employeeId}`);
            },
            create: (data: Partial<ERPEmployee>) => {
                return fetchAPI<ERPEmployee>("/v1/erp/employees", {
                    method: "POST",
                    body: JSON.stringify(data),
                });
            },
            update: (employeeId: string, data: Partial<ERPEmployee>) => {
                return fetchAPI<ERPEmployee>(`/v1/erp/employees/${employeeId}`, {
                    method: "PUT",
                    body: JSON.stringify(data),
                });
            },
            delete: (employeeId: string) => {
                return fetchAPI<void>(`/v1/erp/employees/${employeeId}`, {
                    method: "DELETE",
                });
            },
        },
        estimateFiles: {
            upload: async (formData: FormData) => {
                const url = `${API_BASE_URL}/v1/erp/estimate-files`;
                const res = await fetch(url, {
                    method: "POST",
                    headers: getAuthHeaders(),
                    body: formData,
                });
                if (!res.ok) {
                    const err = await res.json().catch(() => ({}));
                    throw new Error(err.detail || `Upload failed: ${res.statusText}`);
                }
                return res.json() as Promise<ERPEstimateFile>;
            },
            list: (params?: { search?: string; skip?: number; limit?: number }) => {
                const qp = new URLSearchParams();
                if (params?.search) qp.append("search", params.search);
                if (params?.skip !== undefined) qp.append("skip", String(params.skip));
                if (params?.limit !== undefined) qp.append("limit", String(params.limit));
                const q = qp.toString();
                return fetchAPI<ERPEstimateFile[]>(`/v1/erp/estimate-files${q ? `?${q}` : ""}`);
            },
            download: (fileId: string) => {
                const url = `${API_BASE_URL}/v1/erp/estimate-files/${fileId}/download`;
                return fetch(url, { headers: getAuthHeaders() });
            },
            delete: (fileId: string) => {
                return fetchAPI<void>(`/v1/erp/estimate-files/${fileId}`, { method: "DELETE" });
            },
        },
        drawingFiles: {
            upload: async (formData: FormData) => {
                const url = `${API_BASE_URL}/v1/erp/drawing-files`;
                const res = await fetch(url, {
                    method: "POST",
                    headers: getAuthHeaders(),
                    body: formData,
                });
                if (!res.ok) {
                    const err = await res.json().catch(() => ({}));
                    throw new Error(err.detail || `Upload failed: ${res.statusText}`);
                }
                return res.json() as Promise<ERPDrawingFile>;
            },
            list: (params?: { search?: string; project_name?: string; status?: string; skip?: number; limit?: number }) => {
                const qp = new URLSearchParams();
                if (params?.search) qp.append("search", params.search);
                if (params?.project_name) qp.append("project_name", params.project_name);
                if (params?.status) qp.append("status", params.status);
                if (params?.skip !== undefined) qp.append("skip", String(params.skip));
                if (params?.limit !== undefined) qp.append("limit", String(params.limit));
                const q = qp.toString();
                return fetchAPI<ERPDrawingFile[]>(`/v1/erp/drawing-files${q ? `?${q}` : ""}`);
            },
            get: (fileId: string) => {
                return fetchAPI<ERPDrawingFile>(`/v1/erp/drawing-files/${fileId}`);
            },
            download: (fileId: string) => {
                const url = `${API_BASE_URL}/v1/erp/drawing-files/${fileId}/download`;
                return fetch(url, { headers: getAuthHeaders() });
            },
            update: (fileId: string, data: Partial<ERPDrawingFile>) => {
                return fetchAPI<ERPDrawingFile>(`/v1/erp/drawing-files/${fileId}`, {
                    method: "PUT",
                    body: JSON.stringify(data),
                });
            },
            delete: (fileId: string) => {
                return fetchAPI<void>(`/v1/erp/drawing-files/${fileId}`, { method: "DELETE" });
            },
        },
    },
};

// --- ERP File Types ---

export interface ERPEstimateFile {
    id: string;
    estimate_id: string;
    file_name: string;
    file_type: string;
    file_size: number;
    customer_name?: string;
    total_price?: number;
    created_at?: string;
}

export interface ERPDrawingFile {
    id: string;
    drawing_name: string;
    file_name: string;
    file_type: string;
    file_size: number;
    project_name?: string;
    customer_name?: string;
    description?: string;
    tags: string[];
    version: number;
    status: string;
    created_at?: string;
    updated_at?: string;
}

// --- ERP Additional Types ---

export interface ERPCompanyInfo {
    id?: string;
    business_number: string;
    name: string;
    ceo: string;
    address?: string;
    tel?: string;
    fax?: string;
    email?: string;
    bank_info?: Record<string, unknown>;
    business_type?: string;
    business_item?: string;
    logo_path?: string;
    stamp_path?: string;
    created_at?: string;
    updated_at?: string;
}

export interface ERPBankAccount {
    id?: string;
    account_no: string;
    bank_name: string;
    account_name?: string;
    holder_name?: string;
    balance: number;
    is_active: boolean;
    memo?: string;
    created_at?: string;
    updated_at?: string;
}

export interface ERPEmployee {
    id?: string;
    emp_no?: string;
    name: string;
    department?: string;
    position?: string;
    tel?: string;
    email?: string;
    status?: string;
    created_at?: string;
    updated_at?: string;
}

// --- Payroll Types ---

export interface ERPPayrollItem {
    id?: string;
    employee_id: string;
    employee_name: string;
    department?: string | null;
    position?: string | null;
    base_salary: number;
    overtime_pay: number;
    bonus: number;
    allowances: number;
    total_earnings: number;
    income_tax: number;
    local_income_tax: number;
    national_pension: number;
    health_insurance: number;
    employment_insurance: number;
    long_term_care: number;
    other_deductions: number;
    total_deductions: number;
    net_pay: number;
    notes?: string | null;
}

export interface ERPPayroll {
    id: string;
    year: number;
    month: number;
    pay_date: string;
    status: string;
    items: ERPPayrollItem[];
    total_earnings: number;
    total_deductions: number;
    total_net_pay: number;
    insurance_rates?: Record<string, number> | null;
    created_at?: string;
    updated_at?: string;
}

export interface ERPPayrollCreate {
    year: number;
    month: number;
    pay_date: string;
    status?: string;
    items: ERPPayrollItem[];
    total_earnings?: number;
    total_deductions?: number;
    total_net_pay?: number;
    insurance_rates?: Record<string, number> | null;
}

// --- Helper: Map QuoteData to EstimateRequest ---

/**
 * UI 외함 유형 매핑: location + type → API enclosure type
 */
function mapEnclosureType(location: string, _type: string): EnclosureInput["type"] {
    // 기본 매핑 (기성함/제작함 모두 노출형으로 매핑)
    const typeMap: Record<string, EnclosureInput["type"]> = {
        "옥내": "옥내노출",
        "옥외": "옥외노출",
        "계량기함": "옥외노출",  // 계량기함은 옥외노출로 매핑
    };
    return typeMap[location] || "옥내노출";
}

/**
 * UI 재질 → API 재질 매핑
 * UI: "STEEL 1.0T", "STEEL 1.6T", "SUS201 1.0T", "SUS201 1.2T", "SUS201 1.5T", "SUS304 1.2T", "SUS304 1.5T", "SUS304 2.0T"
 * API: "STEEL 1.0T", "STEEL 1.6T", "SUS201 1.2T", "SUS304 1.2T"
 */
function mapEnclosureMaterial(material: string): EnclosureInput["material"] {
    // 직접 매핑 가능한 경우
    const directMatch = ["STEEL 1.0T", "STEEL 1.6T", "SUS201 1.2T", "SUS304 1.2T"];
    if (directMatch.includes(material)) {
        return material as EnclosureInput["material"];
    }

    // SUS201 계열 → SUS201 1.2T로 매핑
    if (material.startsWith("SUS201")) {
        return "SUS201 1.2T";
    }

    // SUS304 계열 → SUS304 1.2T로 매핑
    if (material.startsWith("SUS304")) {
        return "SUS304 1.2T";
    }

    // 기본값
    return "STEEL 1.6T";
}

export function mapQuoteDataToEstimateRequest(data: QuoteData): EstimateRequest {
    /**
     * 차단기 매핑 (NEW: 백엔드 카탈로그 조회 방식)
     *
     * 이전 방식: Frontend에서 generateModel()로 모델명 생성 → 오류 발생
     * 새로운 방식: Frontend는 breaker_type/poles/ampere만 전송
     *             → 백엔드에서 카탈로그 조회하여 정확한 모델명 결정
     */
    const mapBreaker = (b: any, isMain: boolean): BreakerInput => {
        const ampere = parseInt(b.capacity) || 100;  // 기본값 100A
        // Parse "3P" -> 3, "4P" -> 4
        const polesStr = String(b.poles).replace("P", "");
        const poles = (parseInt(polesStr) || 4) as 2 | 3 | 4;  // 기본값 4P
        const breakerType = b.type === "ELB" ? "ELB" : "MCCB";  // 기본값 MCCB

        return {
            breaker_type: breakerType,  // MCCB 또는 ELB (백엔드에서 모델 조회)
            ampere: ampere,
            poles: poles,
            quantity: isMain ? 1 : (b.quantity || 1),  // Main is always 1
            // model 미전송: 백엔드에서 카탈로그 기반 자동 조회
        };
    };

    const firstMain = data.mainBreakers[0];
    const mainBreaker = mapBreaker(firstMain, true);

    const branchBreakers = data.branchBreakers.map(b => mapBreaker(b, false));

    // UI 데이터를 API 형식으로 매핑
    const enclosureType = mapEnclosureType(data.enclosure.location, data.enclosure.type);
    const enclosureMaterial = mapEnclosureMaterial(data.enclosure.material || "STEEL 1.6T");

    // 부속자재 매핑 (UI → API)
    const mapAccessories = (accessories: any[]): AccessoryInput[] | null => {
        if (!accessories || accessories.length === 0) return null;

        return accessories.map((acc): AccessoryInput => {
            // 마그네트 타입
            if (acc.type === "MAGNET") {
                // "마그네트 MC-22" → "MC-22"
                const model = acc.name.replace("마그네트 ", "");
                return {
                    type: "magnet",
                    model: model,
                    quantity: acc.quantity || 1,
                };
            }

            // 기타 부속자재 타입 매핑
            const typeMap: Record<string, AccessoryInput["type"]> = {
                "계량기": "meter",
                "타이머": "timer",
                "SPD": "spd",
                "스위치": "switch",
            };

            // 이름에서 타입 추출 ("계량기 단상" → "계량기")
            const nameParts = acc.name.split(" ");
            const categoryName = nameParts[0];
            const mappedType = typeMap[categoryName] || "switch";

            return {
                type: mappedType,
                model: acc.name,
                quantity: acc.quantity || 1,
            };
        });
    };

    const mappedAccessories = mapAccessories(data.accessories);

    const panel: PanelInput = {
        panel_name: "분전반1", // Default name
        main_breaker: mainBreaker,
        branch_breakers: branchBreakers,
        accessories: mappedAccessories,
        enclosure: {
            type: enclosureType,
            material: enclosureMaterial,
            custom_size: null
        }
    };

    return {
        customer_name: data.customer.companyName || "Unknown Customer",
        project_name: "New Project",
        panels: [panel],
        options: {
            breaker_brand_preference: "SANGDO",  // 기본값: 상도차단기
            use_economy_series: true,
            include_evidence_pack: true
        }
    };
}
