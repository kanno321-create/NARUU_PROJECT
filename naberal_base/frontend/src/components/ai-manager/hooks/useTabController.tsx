"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import type { ExecutedCommand, VisualizationData } from "@/app/ai-manager/page";

/**
 * 탭 타입 정의
 */
export type TabType = "quote" | "erp" | "calendar" | "drawings" | "settings";

/**
 * 명령 실행 결과 타입
 */
export interface CommandResult {
    success: boolean;
    data?: unknown;
    visualization?: VisualizationData;
    error?: string;
}

/**
 * 탭 컨트롤러 인터페이스
 */
export interface TabController {
    // 현재 탭
    currentTab: TabType | null;

    // 탭 이동
    navigateTo: (tab: TabType, params?: Record<string, unknown>) => void;

    // 명령 실행
    executeCommand: (command: ExecutedCommand) => Promise<CommandResult>;

    // 견적 탭 컨트롤
    quote: {
        create: (params: QuoteCreateParams) => Promise<CommandResult>;
        read: (params: QuoteReadParams) => Promise<CommandResult>;
        update: (params: QuoteUpdateParams) => Promise<CommandResult>;
        delete: (id: string) => Promise<CommandResult>;
        list: (params?: QuoteListParams) => Promise<CommandResult>;
        generate: (params: QuoteGenerateParams) => Promise<CommandResult>;
    };

    // ERP 탭 컨트롤
    erp: {
        // 거래처 관리
        customer: {
            create: (params: CustomerParams) => Promise<CommandResult>;
            read: (id: string) => Promise<CommandResult>;
            update: (id: string, params: CustomerParams) => Promise<CommandResult>;
            delete: (id: string) => Promise<CommandResult>;
            list: (params?: ListParams) => Promise<CommandResult>;
        };
        // 상품 관리
        product: {
            create: (params: ProductParams) => Promise<CommandResult>;
            read: (id: string) => Promise<CommandResult>;
            update: (id: string, params: ProductParams) => Promise<CommandResult>;
            delete: (id: string) => Promise<CommandResult>;
            list: (params?: ListParams) => Promise<CommandResult>;
        };
        // 전표 관리
        voucher: {
            create: (type: VoucherType, params: VoucherParams) => Promise<CommandResult>;
            read: (id: string) => Promise<CommandResult>;
            list: (params?: VoucherListParams) => Promise<CommandResult>;
        };
        // 보고서
        report: {
            sales: (params: ReportParams) => Promise<CommandResult>;
            purchase: (params: ReportParams) => Promise<CommandResult>;
            receivable: (params: ReportParams) => Promise<CommandResult>;
            payable: (params: ReportParams) => Promise<CommandResult>;
            profitLoss: (params: ReportParams) => Promise<CommandResult>;
        };
    };

    // 캘린더 탭 컨트롤
    calendar: {
        create: (params: CalendarEventParams) => Promise<CommandResult>;
        read: (id: string) => Promise<CommandResult>;
        update: (id: string, params: CalendarEventParams) => Promise<CommandResult>;
        delete: (id: string) => Promise<CommandResult>;
        list: (params?: CalendarListParams) => Promise<CommandResult>;
    };

    // 도면 탭 컨트롤
    drawings: {
        read: (id: string) => Promise<CommandResult>;
        list: (params?: ListParams) => Promise<CommandResult>;
        analyze: (id: string) => Promise<CommandResult>;
    };

    // 설정 탭 컨트롤
    settings: {
        read: (category: string) => Promise<CommandResult>;
        update: (category: string, params: Record<string, unknown>) => Promise<CommandResult>;
    };
}

// 파라미터 타입 정의
interface QuoteCreateParams {
    customer?: string;
    panelName?: string;
    enclosure?: Record<string, unknown>;
    mainBreaker?: Record<string, unknown>;
    branchBreakers?: Array<Record<string, unknown>>;
}

interface QuoteReadParams {
    id: string;
}

interface QuoteUpdateParams {
    id: string;
    data: Partial<QuoteCreateParams>;
}

interface QuoteListParams {
    startDate?: string;
    endDate?: string;
    customer?: string;
    status?: string;
    page?: number;
    limit?: number;
}

interface QuoteGenerateParams {
    customer: string;
    panelName: string;
    mainBreaker: {
        type: "MCCB" | "ELB";
        poles: 2 | 3 | 4;
        frame: number;
        ampere: number;
    };
    branchBreakers: Array<{
        type: "MCCB" | "ELB";
        poles: 2 | 3 | 4;
        frame: number;
        ampere: number;
        quantity: number;
    }>;
    enclosure?: {
        type?: string;
        material?: string;
    };
}

interface CustomerParams {
    name: string;
    businessNumber?: string;
    representative?: string;
    contact?: string;
    address?: string;
    email?: string;
}

interface ProductParams {
    name: string;
    code?: string;
    category?: string;
    spec?: string;
    unit?: string;
    price?: number;
}

interface ListParams {
    search?: string;
    page?: number;
    limit?: number;
}

type VoucherType = "sales" | "purchase" | "collection" | "payment" | "income-expense";

interface VoucherParams {
    date: string;
    customerId?: string;
    items: Array<{
        productId: string;
        quantity: number;
        unitPrice: number;
    }>;
    memo?: string;
}

interface VoucherListParams extends ListParams {
    type?: VoucherType;
    startDate?: string;
    endDate?: string;
    customerId?: string;
}

interface ReportParams {
    startDate: string;
    endDate: string;
    groupBy?: "day" | "week" | "month";
    customerId?: string;
}

interface CalendarEventParams {
    title: string;
    start: string;
    end?: string;
    description?: string;
    type?: "meeting" | "task" | "reminder" | "other";
    reminders?: Array<{ time: string; type: "email" | "notification" }>;
}

interface CalendarListParams {
    startDate?: string;
    endDate?: string;
    type?: string;
}

/**
 * 탭 통합 컨트롤러 훅
 *
 * 모든 탭(견적/ERP/캘린더/도면/설정)의 CRUD 기능을 통합 관리
 *
 * 참조: 절대코어파일/AI_매니저_구현계획_V1.0.md
 */
export function useTabController(): TabController {
    const router = useRouter();
    const [currentTab, setCurrentTab] = useState<TabType | null>(null);

    // API 호출 헬퍼
    const apiCall = useCallback(
        async <T,>(
            endpoint: string,
            method: "GET" | "POST" | "PUT" | "DELETE" = "GET",
            body?: unknown
        ): Promise<{ success: boolean; data?: T; error?: string }> => {
            try {
                const response = await fetch(`/api/v1${endpoint}`, {
                    method,
                    headers: { "Content-Type": "application/json" },
                    body: body ? JSON.stringify(body) : undefined,
                });

                const data = await response.json();

                if (!response.ok) {
                    return { success: false, error: data.message || "요청 실패" };
                }

                return { success: true, data };
            } catch (error) {
                return { success: false, error: "네트워크 오류" };
            }
        },
        []
    );

    // 탭 이동
    const navigateTo = useCallback(
        (tab: TabType, params?: Record<string, unknown>) => {
            const routes: Record<TabType, string> = {
                quote: "/quote",
                erp: "/erp",
                calendar: "/calendar",
                drawings: "/drawings",
                settings: "/settings",
            };

            setCurrentTab(tab);

            let url = routes[tab];
            if (params) {
                const queryString = new URLSearchParams(
                    Object.entries(params).map(([k, v]) => [k, String(v)])
                ).toString();
                url += `?${queryString}`;
            }

            router.push(url);
        },
        [router]
    );

    // 명령 실행
    const executeCommand = useCallback(
        async (command: ExecutedCommand): Promise<CommandResult> => {
            const { tab, operation, entity, params } = command;

            try {
                // 탭별 명령 라우팅
                switch (tab) {
                    case "quote":
                        return await handleQuoteCommand(operation, entity, params);
                    case "erp":
                        return await handleERPCommand(operation, entity, params);
                    case "calendar":
                        return await handleCalendarCommand(operation, entity, params);
                    case "drawings":
                        return await handleDrawingsCommand(operation, entity, params);
                    case "settings":
                        return await handleSettingsCommand(operation, entity, params);
                    default:
                        return { success: false, error: "알 수 없는 탭" };
                }
            } catch (error) {
                return {
                    success: false,
                    error: error instanceof Error ? error.message : "명령 실행 실패",
                };
            }
        },
        []
    );

    // 견적 명령 핸들러
    const handleQuoteCommand = async (
        operation: string,
        entity: string,
        params?: Record<string, unknown>
    ): Promise<CommandResult> => {
        const endpoint = "/estimate";

        switch (operation) {
            case "create":
                return apiCall(endpoint, "POST", params);
            case "read":
                return apiCall(`${endpoint}/${params?.id}`);
            case "update":
                return apiCall(`${endpoint}/${params?.id}`, "PUT", params);
            case "delete":
                return apiCall(`${endpoint}/${params?.id}`, "DELETE");
            case "execute":
                // 견적 생성 파이프라인 실행
                return apiCall(`${endpoint}/generate`, "POST", params);
            default:
                return { success: false, error: "알 수 없는 명령" };
        }
    };

    // ERP 명령 핸들러
    const handleERPCommand = async (
        operation: string,
        entity: string,
        params?: Record<string, unknown>
    ): Promise<CommandResult> => {
        const entityEndpoints: Record<string, string> = {
            customer: "/v1/erp/customers",
            product: "/v1/erp/products",
            voucher: "/v1/erp/vouchers",
            report: "/v1/erp/reports",
        };

        const endpoint = entityEndpoints[entity];
        if (!endpoint) {
            return { success: false, error: "알 수 없는 엔티티" };
        }

        switch (operation) {
            case "create":
                return apiCall(endpoint, "POST", params);
            case "read":
                return apiCall(`${endpoint}/${params?.id}`);
            case "update":
                return apiCall(`${endpoint}/${params?.id}`, "PUT", params);
            case "delete":
                return apiCall(`${endpoint}/${params?.id}`, "DELETE");
            case "execute":
                // 보고서 생성 등
                return apiCall(`${endpoint}/generate`, "POST", params);
            default:
                return { success: false, error: "알 수 없는 명령" };
        }
    };

    // 캘린더 명령 핸들러
    const handleCalendarCommand = async (
        operation: string,
        entity: string,
        params?: Record<string, unknown>
    ): Promise<CommandResult> => {
        const endpoint = "/calendar/events";

        switch (operation) {
            case "create":
                return apiCall(endpoint, "POST", params);
            case "read":
                return apiCall(`${endpoint}/${params?.id}`);
            case "update":
                return apiCall(`${endpoint}/${params?.id}`, "PUT", params);
            case "delete":
                return apiCall(`${endpoint}/${params?.id}`, "DELETE");
            default:
                return { success: false, error: "알 수 없는 명령" };
        }
    };

    // 도면 명령 핸들러
    const handleDrawingsCommand = async (
        operation: string,
        entity: string,
        params?: Record<string, unknown>
    ): Promise<CommandResult> => {
        const endpoint = "/drawings";

        switch (operation) {
            case "read":
                return apiCall(`${endpoint}/${params?.id}`);
            case "execute":
                // 도면 분석
                return apiCall(`${endpoint}/${params?.id}/analyze`, "POST", params);
            default:
                return { success: false, error: "알 수 없는 명령" };
        }
    };

    // 설정 명령 핸들러
    const handleSettingsCommand = async (
        operation: string,
        entity: string,
        params?: Record<string, unknown>
    ): Promise<CommandResult> => {
        const endpoint = `/settings/${entity}`;

        switch (operation) {
            case "read":
                return apiCall(endpoint);
            case "update":
                return apiCall(endpoint, "PUT", params);
            default:
                return { success: false, error: "알 수 없는 명령" };
        }
    };

    // 견적 컨트롤러
    const quoteController = {
        create: async (params: QuoteCreateParams) =>
            apiCall<unknown>("/estimate", "POST", params),
        read: async (params: QuoteReadParams) =>
            apiCall<unknown>(`/estimate/${params.id}`),
        update: async (params: QuoteUpdateParams) =>
            apiCall<unknown>(`/estimate/${params.id}`, "PUT", params.data),
        delete: async (id: string) =>
            apiCall<unknown>(`/estimate/${id}`, "DELETE"),
        list: async (params?: QuoteListParams) => {
            const query = params
                ? `?${new URLSearchParams(
                    Object.entries(params)
                        .filter(([, v]) => v !== undefined)
                        .map(([k, v]) => [k, String(v)])
                ).toString()}`
                : "";
            return apiCall<unknown>(`/estimate${query}`);
        },
        generate: async (params: QuoteGenerateParams) =>
            apiCall<unknown>("/estimate/generate", "POST", params),
    };

    // ERP 컨트롤러
    const erpController = {
        customer: {
            create: async (params: CustomerParams) =>
                apiCall<unknown>("/v1/erp/customers", "POST", params),
            read: async (id: string) =>
                apiCall<unknown>(`/v1/erp/customers/${id}`),
            update: async (id: string, params: CustomerParams) =>
                apiCall<unknown>(`/v1/erp/customers/${id}`, "PUT", params),
            delete: async (id: string) =>
                apiCall<unknown>(`/v1/erp/customers/${id}`, "DELETE"),
            list: async (params?: ListParams) => {
                const query = params
                    ? `?${new URLSearchParams(
                        Object.entries(params)
                            .filter(([, v]) => v !== undefined)
                            .map(([k, v]) => [k, String(v)])
                    ).toString()}`
                    : "";
                return apiCall<unknown>(`/v1/erp/customers${query}`);
            },
        },
        product: {
            create: async (params: ProductParams) =>
                apiCall<unknown>("/v1/erp/products", "POST", params),
            read: async (id: string) =>
                apiCall<unknown>(`/v1/erp/products/${id}`),
            update: async (id: string, params: ProductParams) =>
                apiCall<unknown>(`/v1/erp/products/${id}`, "PUT", params),
            delete: async (id: string) =>
                apiCall<unknown>(`/v1/erp/products/${id}`, "DELETE"),
            list: async (params?: ListParams) => {
                const query = params
                    ? `?${new URLSearchParams(
                        Object.entries(params)
                            .filter(([, v]) => v !== undefined)
                            .map(([k, v]) => [k, String(v)])
                    ).toString()}`
                    : "";
                return apiCall<unknown>(`/v1/erp/products${query}`);
            },
        },
        voucher: {
            create: async (type: VoucherType, params: VoucherParams) =>
                apiCall<unknown>(`/v1/erp/vouchers/${type}`, "POST", params),
            read: async (id: string) =>
                apiCall<unknown>(`/v1/erp/vouchers/${id}`),
            list: async (params?: VoucherListParams) => {
                const query = params
                    ? `?${new URLSearchParams(
                        Object.entries(params)
                            .filter(([, v]) => v !== undefined)
                            .map(([k, v]) => [k, String(v)])
                    ).toString()}`
                    : "";
                return apiCall<unknown>(`/v1/erp/vouchers${query}`);
            },
        },
        report: {
            sales: async (params: ReportParams) =>
                apiCall<unknown>("/v1/erp/reports/sales", "POST", params),
            purchase: async (params: ReportParams) =>
                apiCall<unknown>("/v1/erp/reports/purchase", "POST", params),
            receivable: async (params: ReportParams) =>
                apiCall<unknown>("/v1/erp/reports/receivable", "POST", params),
            payable: async (params: ReportParams) =>
                apiCall<unknown>("/v1/erp/reports/payable", "POST", params),
            profitLoss: async (params: ReportParams) =>
                apiCall<unknown>("/v1/erp/reports/profit-loss", "POST", params),
        },
    };

    // 캘린더 컨트롤러
    const calendarController = {
        create: async (params: CalendarEventParams) =>
            apiCall<unknown>("/calendar/events", "POST", params),
        read: async (id: string) =>
            apiCall<unknown>(`/calendar/events/${id}`),
        update: async (id: string, params: CalendarEventParams) =>
            apiCall<unknown>(`/calendar/events/${id}`, "PUT", params),
        delete: async (id: string) =>
            apiCall<unknown>(`/calendar/events/${id}`, "DELETE"),
        list: async (params?: CalendarListParams) => {
            const query = params
                ? `?${new URLSearchParams(
                    Object.entries(params)
                        .filter(([, v]) => v !== undefined)
                        .map(([k, v]) => [k, String(v)])
                ).toString()}`
                : "";
            return apiCall<unknown>(`/calendar/events${query}`);
        },
    };

    // 도면 컨트롤러
    const drawingsController = {
        read: async (id: string) =>
            apiCall<unknown>(`/drawings/${id}`),
        list: async (params?: ListParams) => {
            const query = params
                ? `?${new URLSearchParams(
                    Object.entries(params)
                        .filter(([, v]) => v !== undefined)
                        .map(([k, v]) => [k, String(v)])
                ).toString()}`
                : "";
            return apiCall<unknown>(`/drawings${query}`);
        },
        analyze: async (id: string) =>
            apiCall<unknown>(`/drawings/${id}/analyze`, "POST"),
    };

    // 설정 컨트롤러
    const settingsController = {
        read: async (category: string) =>
            apiCall<unknown>(`/settings/${category}`),
        update: async (category: string, params: Record<string, unknown>) =>
            apiCall<unknown>(`/settings/${category}`, "PUT", params),
    };

    return {
        currentTab,
        navigateTo,
        executeCommand,
        quote: quoteController,
        erp: erpController,
        calendar: calendarController,
        drawings: drawingsController,
        settings: settingsController,
    };
}
