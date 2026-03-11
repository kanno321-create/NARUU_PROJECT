"use client";

import React, { useState, useCallback, useEffect, useRef } from "react";
import { ERPSidebar } from "@/components/erp/ERPSidebar";
import { ERPToolbar } from "@/components/erp/ERPToolbar";
import { ERPDashboard } from "@/components/erp/ERPDashboard";
import { ERPWindowManager, ERPWindow } from "@/components/erp/ERPWindowManager";
import { ERPProvider } from "@/components/erp/ERPContext";
import { ERPDataProvider } from "@/contexts/ERPDataContext";
import { cn } from "@/lib/utils";
import { AISupporter } from "@/components/ai-supporter";

// 윈도우 타입 정의
export interface WindowConfig {
    id: string;
    title: string;
    type: string;
    x: number;
    y: number;
    width: number;
    height: number;
    minimized: boolean;
    zIndex: number;
}

// localStorage 키
const WINDOWS_STORAGE_KEY = "kis-erp-windows";
const SIDEBAR_STORAGE_KEY = "kis-erp-sidebar";

// localStorage에서 윈도우 상태 로드
function loadWindowsFromStorage(): WindowConfig[] {
    if (typeof window === "undefined") return [];
    try {
        const saved = localStorage.getItem(WINDOWS_STORAGE_KEY);
        if (saved) {
            const parsed = JSON.parse(saved);
            // ID 재생성 (중복 방지)
            return parsed.map((w: WindowConfig, index: number) => ({
                ...w,
                id: `window-restored-${Date.now()}-${index}`,
            }));
        }
    } catch (e) {
        console.error("Failed to load windows from localStorage:", e);
    }
    return [];
}

// localStorage에서 사이드바 상태 로드
function loadSidebarFromStorage(): boolean {
    if (typeof window === "undefined") return false;
    try {
        const saved = localStorage.getItem(SIDEBAR_STORAGE_KEY);
        if (saved) {
            return JSON.parse(saved);
        }
    } catch (e) {
        console.error("Failed to load sidebar state from localStorage:", e);
    }
    return false;
}

export default function ERPPage() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [windows, setWindows] = useState<WindowConfig[]>([]);
    const [maxZIndex, setMaxZIndex] = useState(100);
    const [isInitialized, setIsInitialized] = useState(false);
    const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    // 초기 로드: localStorage에서 상태 복원
    useEffect(() => {
        const savedWindows = loadWindowsFromStorage();
        const savedSidebar = loadSidebarFromStorage();

        if (savedWindows.length > 0) {
            // 최대 zIndex 계산
            const maxZ = Math.max(...savedWindows.map(w => w.zIndex), 100);
            setMaxZIndex(maxZ);
            setWindows(savedWindows);
        }
        setSidebarCollapsed(savedSidebar);
        setIsInitialized(true);
    }, []);

    // 윈도우 상태 변경 시 localStorage에 저장 (디바운스 적용)
    useEffect(() => {
        if (!isInitialized) return;

        // 이전 타이머 취소
        if (saveTimeoutRef.current) {
            clearTimeout(saveTimeoutRef.current);
        }

        // 300ms 디바운스로 저장 (드래그 중 과도한 저장 방지)
        saveTimeoutRef.current = setTimeout(() => {
            try {
                // 저장할 데이터 준비 (id 제외, 복원 시 재생성)
                const dataToSave = windows.map(w => ({
                    title: w.title,
                    type: w.type,
                    x: w.x,
                    y: w.y,
                    width: w.width,
                    height: w.height,
                    minimized: w.minimized,
                    zIndex: w.zIndex,
                }));
                localStorage.setItem(WINDOWS_STORAGE_KEY, JSON.stringify(dataToSave));
            } catch (e) {
                console.error("Failed to save windows to localStorage:", e);
            }
        }, 300);

        return () => {
            if (saveTimeoutRef.current) {
                clearTimeout(saveTimeoutRef.current);
            }
        };
    }, [windows, isInitialized]);

    // 사이드바 상태 변경 시 localStorage에 저장
    useEffect(() => {
        if (!isInitialized) return;
        try {
            localStorage.setItem(SIDEBAR_STORAGE_KEY, JSON.stringify(sidebarCollapsed));
        } catch (e) {
            console.error("Failed to save sidebar state to localStorage:", e);
        }
    }, [sidebarCollapsed, isInitialized]);

    // 윈도우 타입별 크기 설정 (컨텐츠가 다 보이도록 넉넉하게)
    const getWindowSize = (type: string): { width: number; height: number } => {
        // 전표작성 (큰 창 - 테이블 + 입력폼)
        const voucherTypes = [
            "sales-voucher", "purchase-voucher", "sales-slip", "purchase-slip",
            "collection-slip", "payment-slip", "income-expense-slip",
            "sales-return-slip", "purchase-return-slip", "deposit-slip", "withdrawal-slip"
        ];
        if (voucherTypes.includes(type)) {
            return { width: 1500, height: 920 };
        }

        // 거래처/상품 (컬럼이 많아 넓은 창 필요)
        if (type === "customer" || type === "product") {
            return { width: 1650, height: 900 };
        }

        // 기초자료 등록
        const basicDataTypes = [
            "employee", "bank-account", "credit-card",
            "income-expense-item", "warehouse", "department", "theme",
            "margin-group", "product-category-margin", "theme-category-margin",
            "allowance-item", "deduction-item"
        ];
        if (basicDataTypes.includes(type)) {
            return { width: 1350, height: 850 };
        }

        // 이월 윈도우
        const carryoverTypes = [
            "product-inventory-carryover", "bank-balance-carryover", "cash-balance-carryover",
            "receivable-payable-carryover", "bill-carryover", "debt-credit-carryover"
        ];
        if (carryoverTypes.includes(type)) {
            return { width: 1250, height: 800 };
        }

        // 설정/기타
        const settingsTypes = ["settings", "company-info"];
        if (settingsTypes.includes(type)) {
            return { width: 1050, height: 780 };
        }

        // 발행관리
        const issuanceTypes = [
            "quotation", "purchase-order", "transaction-statement",
            "business-daily-transaction", "tax-invoice"
        ];
        if (issuanceTypes.includes(type)) {
            return { width: 1450, height: 900 };
        }

        // SMS/FAX
        if (type === "sms" || type === "fax") {
            return { width: 850, height: 720 };
        }

        // 급여대장
        if (type === "payroll") {
            return { width: 1500, height: 920 };
        }

        // 수금/지급 전표
        if (type === "collection-voucher" || type === "payment-voucher") {
            return { width: 1350, height: 850 };
        }

        // 보고서/현황 (미수금, 매출현황 등)
        const reportTypes = [
            "receivable-list", "sales-statement", "purchase-statement",
            "daily-report", "monthly-chart", "inventory-status"
        ];
        if (reportTypes.includes(type)) {
            return { width: 1400, height: 880 };
        }

        // 기본값
        return { width: 1350, height: 850 };
    };

    // Electron 환경 감지
    const isElectron = typeof window !== "undefined" && !!(window as any).electronAPI;

    // 디버그: Electron 감지 상태
    useEffect(() => {
        console.log('[ERP] isElectron:', isElectron);
    }, [isElectron]);


    // 새 윈도우 열기
    const openWindow = useCallback((type: string, title: string) => {
        // Electron: 실제 OS 창으로 열기 (모니터 간 이동 가능)
        if (isElectron && (window as any).electronAPI?.openERPWindow) {
            const { width, height } = getWindowSize(type);
            (window as any).electronAPI.openERPWindow(type, title, width, height);
            return;
        }

        // 웹 브라우저: 기존 오버레이 윈도우 방식
        const existingWindow = windows.find(w => w.type === type && !w.minimized);
        if (existingWindow) {
            bringToFront(existingWindow.id);
            return;
        }

        const newZIndex = maxZIndex + 1;
        setMaxZIndex(newZIndex);

        const { width, height } = getWindowSize(type);

        const newWindow: WindowConfig = {
            id: `window-${Date.now()}`,
            title,
            type,
            x: 50 + (windows.length * 30) % 100,
            y: 20 + (windows.length * 20) % 60,
            width,
            height,
            minimized: false,
            zIndex: newZIndex,
        };

        setWindows(prev => [...prev, newWindow]);
    }, [windows, maxZIndex, isElectron]);

    // 윈도우 닫기
    const closeWindow = useCallback((id: string) => {
        setWindows(prev => prev.filter(w => w.id !== id));
    }, []);

    // 윈도우 최소화
    const minimizeWindow = useCallback((id: string) => {
        setWindows(prev => prev.map(w =>
            w.id === id ? { ...w, minimized: !w.minimized } : w
        ));
    }, []);

    // 윈도우 앞으로 가져오기
    const bringToFront = useCallback((id: string) => {
        const newZIndex = maxZIndex + 1;
        setMaxZIndex(newZIndex);
        setWindows(prev => prev.map(w =>
            w.id === id ? { ...w, zIndex: newZIndex, minimized: false } : w
        ));
    }, [maxZIndex]);

    // 윈도우 위치/크기 업데이트
    const updateWindow = useCallback((id: string, updates: Partial<WindowConfig>) => {
        setWindows(prev => prev.map(w =>
            w.id === id ? { ...w, ...updates } : w
        ));
    }, []);

    return (
        <ERPDataProvider>
            <ERPProvider openWindow={openWindow} closeWindow={closeWindow}>
                <div className="flex h-full w-full overflow-hidden bg-surface-secondary">
                    {/* ERP 전용 사이드바 */}
                    <ERPSidebar
                        collapsed={sidebarCollapsed}
                        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
                        onMenuClick={openWindow}
                    />

                    {/* 메인 컨텐츠 영역 */}
                    <div className="flex flex-1 flex-col overflow-hidden">
                        {/* 상단 툴바 */}
                        <ERPToolbar onToolClick={openWindow} />

                        {/* 대시보드 / 메인 컨텐츠 */}
                        <div className="relative flex-1 overflow-auto p-4">
                            <ERPDashboard onOpenWindow={openWindow} />

                            {/* 윈도우 매니저 */}
                            <ERPWindowManager
                                windows={windows}
                                onClose={closeWindow}
                                onMinimize={minimizeWindow}
                                onFocus={bringToFront}
                                onUpdate={updateWindow}
                            />
                        </div>

                        {/* 하단 태스크바 (최소화된 윈도우) */}
                        {windows.filter(w => w.minimized).length > 0 && (
                            <div className="flex items-center gap-2 border-t bg-surface px-4 py-2">
                                {windows.filter(w => w.minimized).map(window => (
                                    <button
                                        key={window.id}
                                        onClick={() => minimizeWindow(window.id)}
                                        className="flex items-center gap-2 rounded border border-surface-tertiary bg-surface px-3 py-1.5 text-xs text-text hover:bg-surface-secondary"
                                    >
                                        <span className="max-w-[120px] truncate">{window.title}</span>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* AI 서포터 */}
                <AISupporter
                    tabContext="erp"
                    onERPAction={(action, data) => {
                        // AI가 ERP 기능을 직접 제어할 때 사용
                        console.log("ERP AI Action:", action, data);
                        if (action === "openWindow" && data.type && data.title) {
                            openWindow(data.type as string, data.title as string);
                        }
                    }}
                />
            </ERPProvider>
        </ERPDataProvider>
    );
}
