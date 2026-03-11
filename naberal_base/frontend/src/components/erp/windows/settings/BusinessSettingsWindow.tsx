"use client";

import React, { useState, useEffect } from "react";
import {
    Save, RotateCcw, Building2, Calendar, RefreshCw, ChevronRight,
    Plus, Trash2, Edit2, CheckCircle, AlertTriangle, Lock, Unlock,
    FileText, DollarSign, Package, CreditCard, Receipt, Users,
    Clock, ArrowRight, ArrowLeftRight, Settings, Database, History,
    Archive, BarChart2, Download, Upload, Eye, EyeOff, Info, X,
    CalendarDays, TrendingUp, Wallet, Banknote, FileCheck
} from "lucide-react";

// ============================================
// 타입 정의
// ============================================

interface BusinessUnit {
    id: string;
    code: string;
    name: string;
    shortName: string;
    businessNumber: string;
    representative: string;
    address: string;
    phone: string;
    fax: string;
    email: string;
    establishedDate: string;
    fiscalYearStart: string;
    fiscalYearEnd: string;
    isHeadquarters: boolean;
    isActive: boolean;
    createdAt: string;
    closedAt?: string;
    bankAccounts: string[];
    defaultCurrency: string;
    taxRate: number;
}

interface FiscalPeriod {
    id: string;
    businessUnitId: string;
    year: number;
    startDate: string;
    endDate: string;
    status: "open" | "closed" | "pending";
    closedAt?: string;
    closedBy?: string;
    isCurrentPeriod: boolean;
    carryForwardStatus: "not_started" | "in_progress" | "completed";
    carryForwardDate?: string;
}

interface CarryForwardItem {
    id: string;
    type: "inventory" | "accounts_receivable" | "accounts_payable" | "bank_balance" | "notes" | "bonds";
    name: string;
    description: string;
    currentBalance: number;
    previousBalance: number;
    adjustment: number;
    verified: boolean;
    lastUpdated: string;
    status: "pending" | "completed" | "error";
    errorMessage?: string;
}

interface ClosingTask {
    id: string;
    name: string;
    description: string;
    order: number;
    required: boolean;
    status: "pending" | "in_progress" | "completed" | "skipped";
    completedAt?: string;
    completedBy?: string;
    dependencies: string[];
    autoExecute: boolean;
}

interface BusinessSettings {
    // 현재 사업장
    currentBusinessUnit: string;

    // 사업장 목록
    businessUnits: BusinessUnit[];

    // 회계기간 설정
    fiscalPeriods: FiscalPeriod[];

    // 기초이월 설정
    autoCarryForward: boolean;
    carryForwardReminder: boolean;
    reminderDays: number;
    requireVerification: boolean;

    // 마감 설정
    allowReopenClosed: boolean;
    reopenPassword: string;
    autoCloseMonthly: boolean;
    monthlyCloseDay: number;
    requireApprovalForClose: boolean;
    closeApprovers: string[];

    // 다중 사업장 설정
    allowInterCompanyTransactions: boolean;
    consolidationEnabled: boolean;
    consolidationCurrency: string;

    // 보안 설정
    restrictAccessByUnit: boolean;
    requirePasswordForSwitch: boolean;
    switchPassword: string;
}

// ============================================
// 기본값
// ============================================

const defaultSettings: BusinessSettings = {
    currentBusinessUnit: "1",

    businessUnits: [
        {
            id: "1",
            code: "HQ001",
            name: "(주)한국산업",
            shortName: "본사",
            businessNumber: "123-45-67890",
            representative: "홍길동",
            address: "서울시 강남구 테헤란로 123",
            phone: "02-1234-5678",
            fax: "02-1234-5679",
            email: "info@hankook.co.kr",
            establishedDate: "2010-01-01",
            fiscalYearStart: "01-01",
            fiscalYearEnd: "12-31",
            isHeadquarters: true,
            isActive: true,
            createdAt: "2010-01-01",
            bankAccounts: ["국민은행 123-456-789", "신한은행 987-654-321"],
            defaultCurrency: "KRW",
            taxRate: 10
        },
        {
            id: "2",
            code: "BR001",
            name: "(주)한국산업 부산지점",
            shortName: "부산지점",
            businessNumber: "123-45-67891",
            representative: "김철수",
            address: "부산시 해운대구 센텀로 456",
            phone: "051-1234-5678",
            fax: "051-1234-5679",
            email: "busan@hankook.co.kr",
            establishedDate: "2015-03-01",
            fiscalYearStart: "01-01",
            fiscalYearEnd: "12-31",
            isHeadquarters: false,
            isActive: true,
            createdAt: "2015-03-01",
            bankAccounts: ["부산은행 111-222-333"],
            defaultCurrency: "KRW",
            taxRate: 10
        }
    ],

    fiscalPeriods: [
        { id: "1", businessUnitId: "1", year: 2025, startDate: "2025-01-01", endDate: "2025-12-31", status: "open", isCurrentPeriod: true, carryForwardStatus: "completed", carryForwardDate: "2025-01-02" },
        { id: "2", businessUnitId: "1", year: 2024, startDate: "2024-01-01", endDate: "2024-12-31", status: "closed", closedAt: "2025-01-02", closedBy: "관리자", isCurrentPeriod: false, carryForwardStatus: "completed" },
        { id: "3", businessUnitId: "1", year: 2023, startDate: "2023-01-01", endDate: "2023-12-31", status: "closed", closedAt: "2024-01-02", closedBy: "관리자", isCurrentPeriod: false, carryForwardStatus: "completed" }
    ],

    autoCarryForward: false,
    carryForwardReminder: true,
    reminderDays: 7,
    requireVerification: true,

    allowReopenClosed: true,
    reopenPassword: "1234",
    autoCloseMonthly: false,
    monthlyCloseDay: 5,
    requireApprovalForClose: true,
    closeApprovers: ["관리자"],

    allowInterCompanyTransactions: true,
    consolidationEnabled: true,
    consolidationCurrency: "KRW",

    restrictAccessByUnit: false,
    requirePasswordForSwitch: false,
    switchPassword: ""
};

const mockCarryForwardItems: CarryForwardItem[] = [
    { id: "1", type: "inventory", name: "상품재고이월", description: "모든 상품의 기말재고를 기초재고로 이월", currentBalance: 125000000, previousBalance: 118500000, adjustment: 0, verified: false, lastUpdated: "2025-12-05", status: "pending" },
    { id: "2", type: "bank_balance", name: "은행잔고이월", description: "모든 은행계좌 잔고 이월", currentBalance: 45800000, previousBalance: 42300000, adjustment: 0, verified: true, lastUpdated: "2025-12-05", status: "completed" },
    { id: "3", type: "accounts_receivable", name: "미수금이월", description: "거래처별 미수금 잔액 이월", currentBalance: 32500000, previousBalance: 28900000, adjustment: 0, verified: false, lastUpdated: "2025-12-05", status: "pending" },
    { id: "4", type: "accounts_payable", name: "미지급금이월", description: "거래처별 미지급금 잔액 이월", currentBalance: 18200000, previousBalance: 15600000, adjustment: 0, verified: false, lastUpdated: "2025-12-05", status: "pending" },
    { id: "5", type: "notes", name: "어음이월", description: "받을어음/지급어음 이월", currentBalance: 8500000, previousBalance: 7200000, adjustment: 0, verified: false, lastUpdated: "2025-12-05", status: "pending" },
    { id: "6", type: "bonds", name: "채권채무이월", description: "채권/채무 잔액 이월", currentBalance: 5200000, previousBalance: 4800000, adjustment: 0, verified: false, lastUpdated: "2025-12-05", status: "pending" }
];

const mockClosingTasks: ClosingTask[] = [
    { id: "1", name: "매출전표 마감", description: "당월 매출전표 확정 처리", order: 1, required: true, status: "completed", completedAt: "2025-12-01 18:00", completedBy: "관리자", dependencies: [], autoExecute: false },
    { id: "2", name: "매입전표 마감", description: "당월 매입전표 확정 처리", order: 2, required: true, status: "completed", completedAt: "2025-12-01 18:05", completedBy: "관리자", dependencies: [], autoExecute: false },
    { id: "3", name: "수금/지급 확정", description: "당월 수금/지급 내역 확정", order: 3, required: true, status: "completed", completedAt: "2025-12-01 18:10", completedBy: "관리자", dependencies: ["1", "2"], autoExecute: false },
    { id: "4", name: "재고실사 반영", description: "재고실사 결과 반영 및 조정", order: 4, required: false, status: "pending", dependencies: [], autoExecute: false },
    { id: "5", name: "감가상각 처리", description: "당월 감가상각비 자동 계산", order: 5, required: false, status: "pending", dependencies: [], autoExecute: true },
    { id: "6", name: "월말 마감 확정", description: "모든 마감 작업 최종 확정", order: 6, required: true, status: "pending", dependencies: ["1", "2", "3"], autoExecute: false }
];

// ============================================
// 유틸리티 함수
// ============================================

const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat("ko-KR", { style: "currency", currency: "KRW" }).format(amount);
};

const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleDateString("ko-KR");
};

// ============================================
// 메인 컴포넌트
// ============================================

export function BusinessSettingsWindow() {
    const [activeTab, setActiveTab] = useState("units");
    const [settings, setSettings] = useState<BusinessSettings>(defaultSettings);
    const [carryForwardItems, setCarryForwardItems] = useState<CarryForwardItem[]>(mockCarryForwardItems);
    const [closingTasks, setClosingTasks] = useState<ClosingTask[]>(mockClosingTasks);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: "success" | "error" | "warning"; text: string } | null>(null);
    const [showUnitModal, setShowUnitModal] = useState(false);
    const [selectedUnit, setSelectedUnit] = useState<BusinessUnit | null>(null);
    const [showCloseConfirm, setShowCloseConfirm] = useState(false);
    const [showCarryForwardConfirm, setShowCarryForwardConfirm] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [reopenPassword, setReopenPassword] = useState("");

    // 설정 저장
    const handleSave = async () => {
        setSaving(true);
        try {
            localStorage.setItem("erp_business_settings", JSON.stringify(settings));
            window.dispatchEvent(new CustomEvent("kis-erp-settings-updated"));
            setMessage({ type: "success", text: "사업장 설정이 저장되었습니다." });
            setTimeout(() => setMessage(null), 3000);
        } catch (error) {
            setMessage({ type: "error", text: "설정 저장에 실패했습니다." });
        } finally {
            setSaving(false);
        }
    };

    // 설정 불러오기
    useEffect(() => {
        const saved = localStorage.getItem("erp_business_settings");
        if (saved) {
            try {
                setSettings(JSON.parse(saved));
            } catch (e) {
                console.error("설정 불러오기 실패:", e);
            }
        }
    }, []);

    // 사업장 전환
    const handleSwitchUnit = (unitId: string) => {
        setSettings({ ...settings, currentBusinessUnit: unitId });
        const unit = settings.businessUnits.find(u => u.id === unitId);
        setMessage({ type: "success", text: `${unit?.shortName || unit?.name} 사업장으로 전환되었습니다.` });
        setTimeout(() => setMessage(null), 3000);
    };

    // 기초이월 실행
    const handleCarryForward = () => {
        setCarryForwardItems(items =>
            items.map(item => ({ ...item, status: "completed" as const, verified: true }))
        );
        setShowCarryForwardConfirm(false);
        setMessage({ type: "success", text: "기초이월이 완료되었습니다." });
        setTimeout(() => setMessage(null), 3000);
    };

    // 마감 태스크 실행
    const handleExecuteTask = (taskId: string) => {
        setClosingTasks(tasks =>
            tasks.map(task =>
                task.id === taskId
                    ? { ...task, status: "completed" as const, completedAt: new Date().toISOString(), completedBy: "관리자" }
                    : task
            )
        );
    };

    // 회계기간 마감
    const handleClosePeriod = (periodId: string) => {
        setSettings({
            ...settings,
            fiscalPeriods: settings.fiscalPeriods.map(p =>
                p.id === periodId
                    ? { ...p, status: "closed" as const, closedAt: new Date().toISOString(), closedBy: "관리자" }
                    : p
            )
        });
        setShowCloseConfirm(false);
        setMessage({ type: "success", text: "회계기간이 마감되었습니다." });
        setTimeout(() => setMessage(null), 3000);
    };

    const currentUnit = settings.businessUnits.find(u => u.id === settings.currentBusinessUnit);
    const currentPeriod = settings.fiscalPeriods.find(p => p.isCurrentPeriod && p.businessUnitId === settings.currentBusinessUnit);

    const tabs = [
        { id: "units", label: "사업장 관리", icon: Building2 },
        { id: "periods", label: "회계기간", icon: Calendar },
        { id: "closing", label: "월/년 마감", icon: Lock },
        { id: "carryforward", label: "기초이월", icon: ArrowLeftRight },
        { id: "consolidation", label: "연결/통합", icon: Database },
        { id: "security", label: "보안 설정", icon: Lock }
    ];

    return (
        <div className="flex h-full flex-col">
            {/* 툴바 */}
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark disabled:opacity-50"
                >
                    <Save className="h-4 w-4" />
                    {saving ? "저장 중..." : "설정 저장"}
                </button>
                <button
                    onClick={() => setSettings(defaultSettings)}
                    className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"
                >
                    <RotateCcw className="h-4 w-4" />
                    초기화
                </button>

                <div className="ml-4 h-6 border-l" />

                {/* 현재 사업장 표시 */}
                <div className="ml-2 flex items-center gap-2 bg-blue-50 px-3 py-1 rounded-lg">
                    <Building2 className="h-4 w-4 text-blue-600" />
                    <span className="text-sm font-medium text-blue-700">
                        현재 사업장: {currentUnit?.shortName || currentUnit?.name}
                    </span>
                    {currentPeriod && (
                        <span className="text-xs text-blue-500">
                            ({currentPeriod.year}년 회계기간)
                        </span>
                    )}
                </div>

                {message && (
                    <span className={`ml-4 text-sm ${
                        message.type === "success" ? "text-green-600" :
                        message.type === "warning" ? "text-yellow-600" : "text-red-600"
                    }`}>
                        {message.text}
                    </span>
                )}
            </div>

            <div className="flex flex-1 overflow-hidden">
                {/* 탭 메뉴 */}
                <div className="w-48 border-r bg-surface-secondary p-2 overflow-y-auto">
                    {tabs.map((tab) => {
                        const Icon = tab.icon;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex w-full items-center gap-2 rounded px-3 py-2 text-left text-sm ${
                                    activeTab === tab.id
                                        ? "bg-brand text-white"
                                        : "hover:bg-surface"
                                }`}
                            >
                                <Icon className="h-4 w-4" />
                                {tab.label}
                            </button>
                        );
                    })}
                </div>

                {/* 설정 내용 */}
                <div className="flex-1 overflow-auto p-4">
                    {/* 사업장 관리 탭 */}
                    {activeTab === "units" && (
                        <div className="space-y-6">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-medium flex items-center gap-2">
                                    <Building2 className="h-5 w-5" />
                                    사업장 관리
                                </h3>
                                <button
                                    onClick={() => {
                                        setSelectedUnit(null);
                                        setShowUnitModal(true);
                                    }}
                                    className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"
                                >
                                    <Plus className="h-4 w-4" />
                                    사업장 추가
                                </button>
                            </div>

                            {/* 사업장 목록 */}
                            <div className="grid grid-cols-2 gap-4">
                                {settings.businessUnits.map((unit) => (
                                    <div
                                        key={unit.id}
                                        className={`rounded-lg border p-4 ${
                                            unit.id === settings.currentBusinessUnit
                                                ? "border-blue-500 bg-blue-50"
                                                : "hover:bg-surface-secondary"
                                        }`}
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-center gap-3">
                                                <div className={`p-2 rounded-lg ${
                                                    unit.isHeadquarters ? "bg-blue-100" : "bg-gray-100"
                                                }`}>
                                                    <Building2 className={`h-5 w-5 ${
                                                        unit.isHeadquarters ? "text-blue-600" : "text-gray-600"
                                                    }`} />
                                                </div>
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <h4 className="font-medium">{unit.name}</h4>
                                                        {unit.isHeadquarters && (
                                                            <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">
                                                                본사
                                                            </span>
                                                        )}
                                                        {!unit.isActive && (
                                                            <span className="px-1.5 py-0.5 bg-red-100 text-red-700 text-xs rounded">
                                                                비활성
                                                            </span>
                                                        )}
                                                    </div>
                                                    <p className="text-xs text-text-subtle">{unit.code}</p>
                                                </div>
                                            </div>
                                            {unit.id === settings.currentBusinessUnit && (
                                                <CheckCircle className="h-5 w-5 text-blue-500" />
                                            )}
                                        </div>

                                        <div className="mt-3 space-y-1 text-sm text-text-subtle">
                                            <p>사업자번호: {unit.businessNumber}</p>
                                            <p>대표자: {unit.representative}</p>
                                            <p>전화: {unit.phone}</p>
                                        </div>

                                        <div className="mt-3 flex items-center gap-2">
                                            {unit.id !== settings.currentBusinessUnit && (
                                                <button
                                                    onClick={() => handleSwitchUnit(unit.id)}
                                                    className="flex items-center gap-1 text-xs px-2 py-1 rounded bg-brand text-white hover:bg-brand-dark"
                                                >
                                                    <ArrowRight className="h-3 w-3" />
                                                    전환
                                                </button>
                                            )}
                                            <button
                                                onClick={() => {
                                                    setSelectedUnit(unit);
                                                    setShowUnitModal(true);
                                                }}
                                                className="flex items-center gap-1 text-xs px-2 py-1 rounded border hover:bg-gray-50"
                                            >
                                                <Edit2 className="h-3 w-3" />
                                                편집
                                            </button>
                                            {!unit.isHeadquarters && (
                                                <button
                                                    onClick={() => {
                                                        const updated = settings.businessUnits.filter(u => u.id !== unit.id);
                                                        setSettings({ ...settings, businessUnits: updated });
                                                    }}
                                                    className="flex items-center gap-1 text-xs px-2 py-1 rounded border hover:bg-red-50 text-red-500"
                                                >
                                                    <Trash2 className="h-3 w-3" />
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* 회계기간 탭 */}
                    {activeTab === "periods" && (
                        <div className="space-y-6">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-medium flex items-center gap-2">
                                    <Calendar className="h-5 w-5" />
                                    회계기간 관리
                                </h3>
                                <button className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark">
                                    <Plus className="h-4 w-4" />
                                    회계기간 추가
                                </button>
                            </div>

                            {/* 회계연도 설정 */}
                            <div className="rounded border p-4 space-y-4">
                                <h4 className="font-medium">회계연도 기본 설정</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">회계연도 시작</label>
                                        <input
                                            type="text"
                                            value={currentUnit?.fiscalYearStart || "01-01"}
                                            onChange={(e) => {
                                                const updated = settings.businessUnits.map(u =>
                                                    u.id === settings.currentBusinessUnit
                                                        ? { ...u, fiscalYearStart: e.target.value }
                                                        : u
                                                );
                                                setSettings({ ...settings, businessUnits: updated });
                                            }}
                                            className="w-full rounded border px-3 py-2 text-sm"
                                            placeholder="MM-DD"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">회계연도 종료</label>
                                        <input
                                            type="text"
                                            value={currentUnit?.fiscalYearEnd || "12-31"}
                                            onChange={(e) => {
                                                const updated = settings.businessUnits.map(u =>
                                                    u.id === settings.currentBusinessUnit
                                                        ? { ...u, fiscalYearEnd: e.target.value }
                                                        : u
                                                );
                                                setSettings({ ...settings, businessUnits: updated });
                                            }}
                                            className="w-full rounded border px-3 py-2 text-sm"
                                            placeholder="MM-DD"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* 회계기간 목록 */}
                            <div className="rounded border overflow-hidden">
                                <table className="w-full text-sm">
                                    <thead className="bg-surface-secondary">
                                        <tr>
                                            <th className="text-left px-4 py-2">회계연도</th>
                                            <th className="text-left px-4 py-2">기간</th>
                                            <th className="text-center px-4 py-2">상태</th>
                                            <th className="text-center px-4 py-2">이월 상태</th>
                                            <th className="text-left px-4 py-2">마감 정보</th>
                                            <th className="text-center px-4 py-2">작업</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {settings.fiscalPeriods
                                            .filter(p => p.businessUnitId === settings.currentBusinessUnit)
                                            .sort((a, b) => b.year - a.year)
                                            .map((period) => (
                                                <tr key={period.id} className="border-t hover:bg-surface-secondary">
                                                    <td className="px-4 py-2">
                                                        <div className="flex items-center gap-2">
                                                            <span className="font-medium">{period.year}년</span>
                                                            {period.isCurrentPeriod && (
                                                                <span className="px-1.5 py-0.5 bg-green-100 text-green-700 text-xs rounded">
                                                                    현재
                                                                </span>
                                                            )}
                                                        </div>
                                                    </td>
                                                    <td className="px-4 py-2">
                                                        {formatDate(period.startDate)} ~ {formatDate(period.endDate)}
                                                    </td>
                                                    <td className="px-4 py-2 text-center">
                                                        <span className={`px-2 py-0.5 rounded text-xs ${
                                                            period.status === "open" ? "bg-green-100 text-green-700" :
                                                            period.status === "closed" ? "bg-gray-100 text-gray-700" :
                                                            "bg-yellow-100 text-yellow-700"
                                                        }`}>
                                                            {period.status === "open" ? "진행중" :
                                                             period.status === "closed" ? "마감" : "대기"}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-2 text-center">
                                                        <span className={`px-2 py-0.5 rounded text-xs ${
                                                            period.carryForwardStatus === "completed" ? "bg-blue-100 text-blue-700" :
                                                            period.carryForwardStatus === "in_progress" ? "bg-yellow-100 text-yellow-700" :
                                                            "bg-gray-100 text-gray-700"
                                                        }`}>
                                                            {period.carryForwardStatus === "completed" ? "완료" :
                                                             period.carryForwardStatus === "in_progress" ? "진행중" : "미시작"}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-2">
                                                        {period.closedAt && (
                                                            <div className="text-xs text-text-subtle">
                                                                <p>{formatDate(period.closedAt)}</p>
                                                                <p>마감자: {period.closedBy}</p>
                                                            </div>
                                                        )}
                                                    </td>
                                                    <td className="px-4 py-2 text-center">
                                                        {period.status === "open" ? (
                                                            <button
                                                                onClick={() => setShowCloseConfirm(true)}
                                                                className="text-brand hover:underline text-sm"
                                                            >
                                                                마감
                                                            </button>
                                                        ) : settings.allowReopenClosed && (
                                                            <button
                                                                className="text-orange-600 hover:underline text-sm"
                                                            >
                                                                재개
                                                            </button>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* 마감 탭 */}
                    {activeTab === "closing" && (
                        <div className="space-y-6">
                            <h3 className="text-lg font-medium flex items-center gap-2">
                                <Lock className="h-5 w-5" />
                                월/년 마감 관리
                            </h3>

                            {/* 마감 현황 */}
                            <div className="grid grid-cols-3 gap-4">
                                <div className="rounded-lg border bg-green-50 p-4">
                                    <div className="flex items-center gap-2">
                                        <CheckCircle className="h-5 w-5 text-green-600" />
                                        <span className="font-medium text-green-700">완료된 작업</span>
                                    </div>
                                    <p className="mt-2 text-2xl font-bold text-green-600">
                                        {closingTasks.filter(t => t.status === "completed").length}
                                    </p>
                                </div>
                                <div className="rounded-lg border bg-yellow-50 p-4">
                                    <div className="flex items-center gap-2">
                                        <Clock className="h-5 w-5 text-yellow-600" />
                                        <span className="font-medium text-yellow-700">대기 중인 작업</span>
                                    </div>
                                    <p className="mt-2 text-2xl font-bold text-yellow-600">
                                        {closingTasks.filter(t => t.status === "pending").length}
                                    </p>
                                </div>
                                <div className="rounded-lg border bg-blue-50 p-4">
                                    <div className="flex items-center gap-2">
                                        <BarChart2 className="h-5 w-5 text-blue-600" />
                                        <span className="font-medium text-blue-700">진행률</span>
                                    </div>
                                    <p className="mt-2 text-2xl font-bold text-blue-600">
                                        {Math.round((closingTasks.filter(t => t.status === "completed").length / closingTasks.length) * 100)}%
                                    </p>
                                </div>
                            </div>

                            {/* 마감 작업 목록 */}
                            <div className="space-y-3">
                                <h4 className="font-medium">마감 체크리스트</h4>
                                {closingTasks.sort((a, b) => a.order - b.order).map((task) => (
                                    <div
                                        key={task.id}
                                        className={`rounded border p-4 ${
                                            task.status === "completed" ? "bg-green-50 border-green-200" :
                                            task.status === "in_progress" ? "bg-yellow-50 border-yellow-200" :
                                            "bg-white"
                                        }`}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                                                    task.status === "completed" ? "bg-green-500 text-white" :
                                                    task.status === "in_progress" ? "bg-yellow-500 text-white" :
                                                    "bg-gray-200 text-gray-600"
                                                }`}>
                                                    {task.status === "completed" ? <CheckCircle className="h-4 w-4" /> : task.order}
                                                </div>
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <span className="font-medium">{task.name}</span>
                                                        {task.required && (
                                                            <span className="px-1.5 py-0.5 bg-red-100 text-red-700 text-xs rounded">
                                                                필수
                                                            </span>
                                                        )}
                                                        {task.autoExecute && (
                                                            <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">
                                                                자동
                                                            </span>
                                                        )}
                                                    </div>
                                                    <p className="text-sm text-text-subtle">{task.description}</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                {task.completedAt && (
                                                    <div className="text-right text-xs text-text-subtle">
                                                        <p>{task.completedAt}</p>
                                                        <p>{task.completedBy}</p>
                                                    </div>
                                                )}
                                                {task.status !== "completed" && (
                                                    <button
                                                        onClick={() => handleExecuteTask(task.id)}
                                                        className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"
                                                    >
                                                        실행
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* 마감 설정 */}
                            <div className="rounded border p-4 space-y-4">
                                <h4 className="font-medium">마감 설정</h4>

                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.autoCloseMonthly}
                                        onChange={(e) => setSettings({ ...settings, autoCloseMonthly: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    <span className="text-sm">월 자동 마감 사용</span>
                                </label>

                                {settings.autoCloseMonthly && (
                                    <div>
                                        <label className="block text-sm font-medium mb-1">
                                            자동 마감일 (매월)
                                        </label>
                                        <input
                                            type="number"
                                            value={settings.monthlyCloseDay}
                                            onChange={(e) => setSettings({ ...settings, monthlyCloseDay: Number(e.target.value) })}
                                            className="w-32 rounded border px-3 py-2 text-sm"
                                            min="1"
                                            max="28"
                                        />
                                        <span className="ml-2 text-sm text-text-subtle">일</span>
                                    </div>
                                )}

                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.requireApprovalForClose}
                                        onChange={(e) => setSettings({ ...settings, requireApprovalForClose: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    <span className="text-sm">마감 시 승인 필요</span>
                                </label>
                            </div>
                        </div>
                    )}

                    {/* 기초이월 탭 */}
                    {activeTab === "carryforward" && (
                        <div className="space-y-6">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-medium flex items-center gap-2">
                                    <ArrowLeftRight className="h-5 w-5" />
                                    기초이월 관리
                                </h3>
                                <button
                                    onClick={() => setShowCarryForwardConfirm(true)}
                                    className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"
                                >
                                    <RefreshCw className="h-4 w-4" />
                                    전체 이월 실행
                                </button>
                            </div>

                            {/* 이월 현황 */}
                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                <div className="flex items-start gap-3">
                                    <Info className="h-5 w-5 text-blue-600 mt-0.5" />
                                    <div>
                                        <h4 className="font-medium text-blue-800">기초이월 안내</h4>
                                        <p className="mt-1 text-sm text-blue-700">
                                            기초이월은 전년도의 기말잔액을 신년도의 기초잔액으로 이월하는 작업입니다.
                                            회계연도 마감 후 수행하며, 한 번 이월된 데이터는 수정이 어려우니 신중하게 진행하세요.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* 이월 항목 목록 */}
                            <div className="space-y-3">
                                {carryForwardItems.map((item) => (
                                    <div
                                        key={item.id}
                                        className={`rounded-lg border p-4 ${
                                            item.status === "completed" ? "bg-green-50 border-green-200" :
                                            item.status === "error" ? "bg-red-50 border-red-200" :
                                            "bg-white"
                                        }`}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-4">
                                                <div className={`p-2 rounded-lg ${
                                                    item.type === "inventory" ? "bg-blue-100" :
                                                    item.type === "bank_balance" ? "bg-green-100" :
                                                    item.type === "accounts_receivable" ? "bg-yellow-100" :
                                                    item.type === "accounts_payable" ? "bg-orange-100" :
                                                    item.type === "notes" ? "bg-purple-100" :
                                                    "bg-pink-100"
                                                }`}>
                                                    {item.type === "inventory" ? <Package className="h-5 w-5 text-blue-600" /> :
                                                     item.type === "bank_balance" ? <Wallet className="h-5 w-5 text-green-600" /> :
                                                     item.type === "accounts_receivable" ? <TrendingUp className="h-5 w-5 text-yellow-600" /> :
                                                     item.type === "accounts_payable" ? <Receipt className="h-5 w-5 text-orange-600" /> :
                                                     item.type === "notes" ? <FileText className="h-5 w-5 text-purple-600" /> :
                                                     <CreditCard className="h-5 w-5 text-pink-600" />}
                                                </div>
                                                <div>
                                                    <h4 className="font-medium">{item.name}</h4>
                                                    <p className="text-sm text-text-subtle">{item.description}</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-4">
                                                <div className="text-right">
                                                    <p className="text-sm text-text-subtle">현재 잔액</p>
                                                    <p className="font-medium">{formatCurrency(item.currentBalance)}</p>
                                                </div>
                                                <div className="text-right">
                                                    <p className="text-sm text-text-subtle">전기 잔액</p>
                                                    <p className="text-text-subtle">{formatCurrency(item.previousBalance)}</p>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    {item.verified ? (
                                                        <CheckCircle className="h-5 w-5 text-green-500" />
                                                    ) : (
                                                        <AlertTriangle className="h-5 w-5 text-yellow-500" />
                                                    )}
                                                    <span className={`px-2 py-0.5 rounded text-xs ${
                                                        item.status === "completed" ? "bg-green-100 text-green-700" :
                                                        item.status === "error" ? "bg-red-100 text-red-700" :
                                                        "bg-yellow-100 text-yellow-700"
                                                    }`}>
                                                        {item.status === "completed" ? "완료" :
                                                         item.status === "error" ? "오류" : "대기"}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                        {item.errorMessage && (
                                            <p className="mt-2 text-sm text-red-600">{item.errorMessage}</p>
                                        )}
                                    </div>
                                ))}
                            </div>

                            {/* 이월 설정 */}
                            <div className="rounded border p-4 space-y-4">
                                <h4 className="font-medium">이월 설정</h4>

                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.autoCarryForward}
                                        onChange={(e) => setSettings({ ...settings, autoCarryForward: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    <span className="text-sm">회계연도 마감 시 자동 이월</span>
                                </label>

                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.carryForwardReminder}
                                        onChange={(e) => setSettings({ ...settings, carryForwardReminder: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    <span className="text-sm">이월 미완료 시 알림</span>
                                </label>

                                {settings.carryForwardReminder && (
                                    <div>
                                        <label className="block text-sm font-medium mb-1">
                                            알림 기간 (회계연도 시작 후)
                                        </label>
                                        <input
                                            type="number"
                                            value={settings.reminderDays}
                                            onChange={(e) => setSettings({ ...settings, reminderDays: Number(e.target.value) })}
                                            className="w-32 rounded border px-3 py-2 text-sm"
                                            min="1"
                                            max="30"
                                        />
                                        <span className="ml-2 text-sm text-text-subtle">일</span>
                                    </div>
                                )}

                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.requireVerification}
                                        onChange={(e) => setSettings({ ...settings, requireVerification: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    <span className="text-sm">이월 전 검증 필수</span>
                                </label>
                            </div>
                        </div>
                    )}

                    {/* 연결/통합 탭 */}
                    {activeTab === "consolidation" && (
                        <div className="space-y-6">
                            <h3 className="text-lg font-medium flex items-center gap-2">
                                <Database className="h-5 w-5" />
                                연결/통합 설정
                            </h3>

                            <div className="rounded border p-4 space-y-4">
                                <h4 className="font-medium">사업장 간 거래</h4>

                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.allowInterCompanyTransactions}
                                        onChange={(e) => setSettings({ ...settings, allowInterCompanyTransactions: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    <span className="text-sm">사업장 간 거래 허용</span>
                                </label>
                                <p className="text-xs text-text-subtle ml-6">
                                    활성화하면 서로 다른 사업장 간의 거래를 기록할 수 있습니다.
                                </p>
                            </div>

                            <div className="rounded border p-4 space-y-4">
                                <h4 className="font-medium">연결 재무제표</h4>

                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.consolidationEnabled}
                                        onChange={(e) => setSettings({ ...settings, consolidationEnabled: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    <span className="text-sm">연결 재무제표 작성</span>
                                </label>

                                {settings.consolidationEnabled && (
                                    <div>
                                        <label className="block text-sm font-medium mb-1">기준 통화</label>
                                        <select
                                            value={settings.consolidationCurrency}
                                            onChange={(e) => setSettings({ ...settings, consolidationCurrency: e.target.value })}
                                            className="w-full rounded border px-3 py-2 text-sm"
                                        >
                                            <option value="KRW">KRW (원)</option>
                                            <option value="USD">USD ($)</option>
                                            <option value="EUR">EUR (€)</option>
                                        </select>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* 보안 설정 탭 */}
                    {activeTab === "security" && (
                        <div className="space-y-6">
                            <h3 className="text-lg font-medium flex items-center gap-2">
                                <Lock className="h-5 w-5" />
                                보안 설정
                            </h3>

                            <div className="rounded border p-4 space-y-4">
                                <h4 className="font-medium">접근 제어</h4>

                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.restrictAccessByUnit}
                                        onChange={(e) => setSettings({ ...settings, restrictAccessByUnit: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    <span className="text-sm">사업장별 접근 제한</span>
                                </label>
                                <p className="text-xs text-text-subtle ml-6">
                                    사용자가 배정된 사업장의 데이터만 조회/수정할 수 있습니다.
                                </p>
                            </div>

                            <div className="rounded border p-4 space-y-4">
                                <h4 className="font-medium">사업장 전환 보안</h4>

                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.requirePasswordForSwitch}
                                        onChange={(e) => setSettings({ ...settings, requirePasswordForSwitch: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    <span className="text-sm">사업장 전환 시 비밀번호 필요</span>
                                </label>

                                {settings.requirePasswordForSwitch && (
                                    <div>
                                        <label className="block text-sm font-medium mb-1">전환 비밀번호</label>
                                        <div className="relative">
                                            <input
                                                type={showPassword ? "text" : "password"}
                                                value={settings.switchPassword}
                                                onChange={(e) => setSettings({ ...settings, switchPassword: e.target.value })}
                                                className="w-full rounded border px-3 py-2 pr-10 text-sm"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setShowPassword(!showPassword)}
                                                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400"
                                            >
                                                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="rounded border p-4 space-y-4">
                                <h4 className="font-medium">마감 재개 보안</h4>

                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.allowReopenClosed}
                                        onChange={(e) => setSettings({ ...settings, allowReopenClosed: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    <span className="text-sm">마감된 기간 재개 허용</span>
                                </label>

                                {settings.allowReopenClosed && (
                                    <div>
                                        <label className="block text-sm font-medium mb-1">재개 비밀번호</label>
                                        <input
                                            type="password"
                                            value={settings.reopenPassword}
                                            onChange={(e) => setSettings({ ...settings, reopenPassword: e.target.value })}
                                            className="w-full rounded border px-3 py-2 text-sm"
                                        />
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* 기초이월 확인 모달 */}
            {showCarryForwardConfirm && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg w-[500px] p-6">
                        <h3 className="text-lg font-medium mb-4">기초이월 실행 확인</h3>
                        <p className="text-sm text-text-subtle mb-4">
                            전년도 기말잔액을 신년도 기초잔액으로 이월합니다.
                            이월된 데이터는 수정이 어려우니 신중하게 진행하세요.
                        </p>
                        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">
                            <p className="text-sm text-yellow-700">
                                <strong>주의:</strong> 이월 전에 전년도 마감이 완료되었는지 확인하세요.
                            </p>
                        </div>
                        <div className="flex justify-end gap-2">
                            <button
                                onClick={() => setShowCarryForwardConfirm(false)}
                                className="px-4 py-2 text-sm rounded border hover:bg-surface-secondary"
                            >
                                취소
                            </button>
                            <button
                                onClick={handleCarryForward}
                                className="px-4 py-2 text-sm rounded bg-brand text-white hover:bg-brand-dark"
                            >
                                이월 실행
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
