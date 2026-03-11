"use client";

import React, { useState, useEffect } from "react";
import { Save, RotateCcw, Building2, Calculator, Globe, Palette, Clock, Shield, Info, ChevronDown, ChevronRight, X } from "lucide-react";
import { useWindowContextOptional } from "../../ERPContext";
import { api } from "@/lib/api";

interface CompanyInfo {
    companyName: string;
    businessNumber: string;
    corporateNumber: string;
    representative: string;
    businessType: string;
    businessCategory: string;
    address: string;
    detailAddress: string;
    zipCode: string;
    phone: string;
    fax: string;
    email: string;
    website: string;
    establishedDate: string;
}

interface TaxSettings {
    vatRate: number;
    vatRoundingMethod: "round" | "floor" | "ceil";
    priceIncludeVat: boolean;
    autoCalculateVat: boolean;
    vatDecimalPlaces: number;
    withholdingTaxRate: number;
    localTaxRate: number;
}

interface CurrencySettings {
    baseCurrency: string;
    currencySymbol: string;
    currencyPosition: "before" | "after";
    decimalPlaces: number;
    thousandSeparator: string;
    decimalSeparator: string;
    supportedCurrencies: string[];
    exchangeRates: Record<string, number>;
}

interface UISettings {
    theme: "light" | "dark" | "system";
    language: string;
    fontSize: "small" | "medium" | "large";
    sidebarCollapsed: boolean;
    showTooltips: boolean;
    animationsEnabled: boolean;
    compactMode: boolean;
    primaryColor: string;
    dateFormat: string;
    timeFormat: "12h" | "24h";
    firstDayOfWeek: number;
    timezone: string;
}

interface SecuritySettings {
    autoLogout: boolean;
    autoLogoutMinutes: number;
    requirePasswordChange: boolean;
    passwordChangeDays: number;
    twoFactorEnabled: boolean;
    ipWhitelist: string[];
    loginNotification: boolean;
}

interface BasicSettings {
    company: CompanyInfo;
    tax: TaxSettings;
    currency: CurrencySettings;
    ui: UISettings;
    security: SecuritySettings;
}

const defaultSettings: BasicSettings = {
    company: {
        companyName: "",
        businessNumber: "",
        corporateNumber: "",
        representative: "",
        businessType: "",
        businessCategory: "",
        address: "",
        detailAddress: "",
        zipCode: "",
        phone: "",
        fax: "",
        email: "",
        website: "",
        establishedDate: "",
    },
    tax: {
        vatRate: 10,
        vatRoundingMethod: "round",
        priceIncludeVat: false,
        autoCalculateVat: true,
        vatDecimalPlaces: 0,
        withholdingTaxRate: 3.3,
        localTaxRate: 0.33,
    },
    currency: {
        baseCurrency: "KRW",
        currencySymbol: "₩",
        currencyPosition: "before",
        decimalPlaces: 0,
        thousandSeparator: ",",
        decimalSeparator: ".",
        supportedCurrencies: ["KRW", "USD", "EUR", "JPY", "CNY"],
        exchangeRates: { USD: 1300, EUR: 1400, JPY: 9, CNY: 180 },
    },
    ui: {
        theme: "light",
        language: "ko",
        fontSize: "medium",
        sidebarCollapsed: false,
        showTooltips: true,
        animationsEnabled: true,
        compactMode: false,
        primaryColor: "#1a56db",
        dateFormat: "YYYY-MM-DD",
        timeFormat: "24h",
        firstDayOfWeek: 0,
        timezone: "Asia/Seoul",
    },
    security: {
        autoLogout: true,
        autoLogoutMinutes: 30,
        requirePasswordChange: false,
        passwordChangeDays: 90,
        twoFactorEnabled: false,
        ipWhitelist: [],
        loginNotification: true,
    },
};

export function BasicSettingsWindow() {
    const windowContext = useWindowContextOptional();
    const [settings, setSettings] = useState<BasicSettings>(defaultSettings);
    const [activeSection, setActiveSection] = useState<string>("company");
    const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(["company"]));
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
    const [hasChanges, setHasChanges] = useState(false);
    const [showBusinessSearchModal, setShowBusinessSearchModal] = useState(false);
    const [businessList, setBusinessList] = useState<Array<{ name: string; businessNumber: string; representative: string }>>([]);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const apiData = await api.erp.settings.getGeneral();
                if (!cancelled && apiData && typeof apiData === "object" && Object.keys(apiData).length > 0) {
                    const merged = { ...defaultSettings, ...apiData };
                    setSettings(merged);
                    localStorage.setItem("kis-erp-settings", JSON.stringify(merged));
                    return;
                }
            } catch {
                // API 실패 시 localStorage 폴백
            }
            if (cancelled) return;
            const saved = localStorage.getItem("kis-erp-settings");
            if (saved) {
                try {
                    const parsed = JSON.parse(saved);
                    setSettings({ ...defaultSettings, ...parsed });
                } catch (e) {
                    console.error("설정 불러오기 실패:", e);
                }
            }
        })();
        return () => { cancelled = true; };
    }, []);

    const handleSave = async () => {
        setSaving(true);
        try {
            localStorage.setItem("kis-erp-settings", JSON.stringify(settings));
            window.dispatchEvent(new CustomEvent("kis-erp-settings-updated"));
            try {
                await api.erp.settings.updateGeneral(settings as Record<string, unknown>);
            } catch {
                console.warn("API 설정 저장 실패 - localStorage에만 저장됨");
            }
            setMessage({ type: "success", text: "기본설정이 저장되었습니다." });
            setHasChanges(false);
            setTimeout(() => setMessage(null), 3000);
        } catch (error) {
            setMessage({ type: "error", text: "저장에 실패했습니다." });
        } finally {
            setSaving(false);
        }
    };

    const handleReset = () => {
        if (confirm("모든 기본설정을 초기화하시겠습니까?")) {
            setSettings(defaultSettings);
            setHasChanges(true);
        }
    };

    const handleCancel = () => {
        windowContext?.closeThisWindow();
    };

    const handleBusinessSearch = () => {
        // localStorage의 companyInfo 로드하여 사업장 목록 표시
        const list: Array<{ name: string; businessNumber: string; representative: string }> = [];
        try {
            const companyInfo = localStorage.getItem("erp-company-info");
            if (companyInfo) {
                const parsed = JSON.parse(companyInfo);
                if (Array.isArray(parsed)) {
                    list.push(...parsed);
                } else if (parsed.companyName) {
                    list.push({
                        name: parsed.companyName,
                        businessNumber: parsed.businessNumber || "",
                        representative: parsed.representative || "",
                    });
                }
            }
        } catch { /* ignore */ }

        // 현재 설정에서도 추가
        if (settings.company.companyName) {
            const exists = list.some((b) => b.name === settings.company.companyName);
            if (!exists) {
                list.push({
                    name: settings.company.companyName,
                    businessNumber: settings.company.businessNumber,
                    representative: settings.company.representative,
                });
            }
        }

        // 기본 사업장 데이터 (최소 1개 보장)
        if (list.length === 0) {
            list.push(
                { name: "이지판매상회", businessNumber: "123-45-67890", representative: "김대표" },
                { name: "한국산업(주)", businessNumber: "234-56-78901", representative: "박사장" },
            );
        }

        setBusinessList(list);
        setShowBusinessSearchModal(true);
    };

    const handleSelectBusiness = (biz: { name: string; businessNumber: string; representative: string }) => {
        setSettings((prev) => ({
            ...prev,
            company: {
                ...prev.company,
                companyName: biz.name,
                businessNumber: biz.businessNumber,
                representative: biz.representative,
            },
        }));
        setHasChanges(true);
        setShowBusinessSearchModal(false);
    };

    const updateCompany = (field: keyof CompanyInfo, value: string) => {
        setSettings(prev => ({ ...prev, company: { ...prev.company, [field]: value } }));
        setHasChanges(true);
    };

    const updateTax = (field: keyof TaxSettings, value: any) => {
        setSettings(prev => ({ ...prev, tax: { ...prev.tax, [field]: value } }));
        setHasChanges(true);
    };

    const updateCurrency = (field: keyof CurrencySettings, value: any) => {
        setSettings(prev => ({ ...prev, currency: { ...prev.currency, [field]: value } }));
        setHasChanges(true);
    };

    const updateUI = (field: keyof UISettings, value: any) => {
        setSettings(prev => ({ ...prev, ui: { ...prev.ui, [field]: value } }));
        setHasChanges(true);
    };

    const updateSecurity = (field: keyof SecuritySettings, value: any) => {
        setSettings(prev => ({ ...prev, security: { ...prev.security, [field]: value } }));
        setHasChanges(true);
    };

    const toggleSection = (section: string) => {
        setExpandedSections(prev => {
            const newSet = new Set(prev);
            if (newSet.has(section)) {
                newSet.delete(section);
            } else {
                newSet.add(section);
            }
            return newSet;
        });
    };

    const sections = [
        { id: "company", label: "회사 정보", icon: Building2 },
        { id: "tax", label: "세금 설정", icon: Calculator },
        { id: "currency", label: "통화 설정", icon: Globe },
        { id: "ui", label: "화면 설정", icon: Palette },
        { id: "security", label: "보안 설정", icon: Shield },
    ];

    return (
        <div className="relative flex h-full min-h-[600px] flex-col">
            {/* 툴바 */}
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button
                    onClick={handleSave}
                    disabled={saving || !hasChanges}
                    className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark disabled:opacity-50"
                >
                    <Save className="h-4 w-4" />
                    {saving ? "저장 중..." : "저장"}
                </button>
                <button
                    onClick={handleReset}
                    className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"
                >
                    <RotateCcw className="h-4 w-4" />
                    초기화
                </button>
                <button
                    onClick={handleCancel}
                    className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"
                >
                    <X className="h-4 w-4" />
                    취소
                </button>
                {hasChanges && (
                    <span className="ml-2 text-sm text-amber-600">* 저장되지 않은 변경사항이 있습니다</span>
                )}
                {message && (
                    <span className={`ml-auto text-sm ${message.type === "success" ? "text-green-600" : "text-red-600"}`}>
                        {message.text}
                    </span>
                )}
            </div>

            <div className="flex flex-1 overflow-hidden">
                {/* 좌측 네비게이션 */}
                <div className="w-52 border-r bg-surface-secondary overflow-auto">
                    {sections.map((section) => {
                        const Icon = section.icon;
                        const isActive = activeSection === section.id;
                        return (
                            <button
                                key={section.id}
                                onClick={() => {
                                    setActiveSection(section.id);
                                    toggleSection(section.id);
                                }}
                                className={`flex w-full items-center gap-2 px-4 py-3 text-left text-sm border-b ${
                                    isActive ? "bg-brand text-white" : "hover:bg-surface"
                                }`}
                            >
                                <Icon className="h-4 w-4" />
                                <span className="flex-1">{section.label}</span>
                                {expandedSections.has(section.id) ? (
                                    <ChevronDown className="h-4 w-4" />
                                ) : (
                                    <ChevronRight className="h-4 w-4" />
                                )}
                            </button>
                        );
                    })}
                </div>

                {/* 우측 설정 내용 */}
                <div className="flex-1 overflow-auto p-6">
                    {/* 회사 정보 */}
                    {activeSection === "company" && (
                        <div className="space-y-6">
                            <div className="flex items-center gap-2 mb-4">
                                <Building2 className="h-5 w-5 text-brand" />
                                <h3 className="text-lg font-medium">회사 정보</h3>
                            </div>

                            {/* 기본 정보 */}
                            <div className="rounded-lg border p-4">
                                <h4 className="font-medium mb-4 text-sm text-text-subtle">기본 정보</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">
                                            회사명 <span className="text-red-500">*</span>
                                        </label>
                                        <input
                                            type="text"
                                            value={settings.company.companyName}
                                            onChange={(e) => updateCompany("companyName", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                            placeholder="(주)한국산업"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">
                                            사업자등록번호 <span className="text-red-500">*</span>
                                        </label>
                                        <input
                                            type="text"
                                            value={settings.company.businessNumber}
                                            onChange={(e) => updateCompany("businessNumber", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                            placeholder="000-00-00000"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">법인등록번호</label>
                                        <input
                                            type="text"
                                            value={settings.company.corporateNumber}
                                            onChange={(e) => updateCompany("corporateNumber", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                            placeholder="000000-0000000"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">
                                            대표자 <span className="text-red-500">*</span>
                                        </label>
                                        <input
                                            type="text"
                                            value={settings.company.representative}
                                            onChange={(e) => updateCompany("representative", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">업태</label>
                                        <input
                                            type="text"
                                            value={settings.company.businessType}
                                            onChange={(e) => updateCompany("businessType", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                            placeholder="제조업"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">업종</label>
                                        <input
                                            type="text"
                                            value={settings.company.businessCategory}
                                            onChange={(e) => updateCompany("businessCategory", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                            placeholder="전기기기"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">설립일</label>
                                        <input
                                            type="date"
                                            value={settings.company.establishedDate}
                                            onChange={(e) => updateCompany("establishedDate", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">사업장 선택</label>
                                        <button
                                            onClick={handleBusinessSearch}
                                            className="w-full rounded border px-3 py-2 text-sm text-left hover:bg-surface-secondary focus:border-brand focus:ring-1 focus:ring-brand"
                                        >
                                            검색
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* 주소 정보 */}
                            <div className="rounded-lg border p-4">
                                <h4 className="font-medium mb-4 text-sm text-text-subtle">주소 정보</h4>
                                <div className="grid grid-cols-3 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">우편번호</label>
                                        <div className="flex gap-2">
                                            <input
                                                type="text"
                                                value={settings.company.zipCode}
                                                onChange={(e) => updateCompany("zipCode", e.target.value)}
                                                className="flex-1 rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                                placeholder="00000"
                                            />
                                            <button className="rounded border px-3 py-2 text-sm hover:bg-surface-secondary">
                                                검색
                                            </button>
                                        </div>
                                    </div>
                                    <div className="col-span-2">
                                        <label className="block text-sm font-medium mb-1">기본주소</label>
                                        <input
                                            type="text"
                                            value={settings.company.address}
                                            onChange={(e) => updateCompany("address", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        />
                                    </div>
                                    <div className="col-span-3">
                                        <label className="block text-sm font-medium mb-1">상세주소</label>
                                        <input
                                            type="text"
                                            value={settings.company.detailAddress}
                                            onChange={(e) => updateCompany("detailAddress", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* 연락처 정보 */}
                            <div className="rounded-lg border p-4">
                                <h4 className="font-medium mb-4 text-sm text-text-subtle">연락처 정보</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">전화번호</label>
                                        <input
                                            type="text"
                                            value={settings.company.phone}
                                            onChange={(e) => updateCompany("phone", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                            placeholder="02-0000-0000"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">팩스번호</label>
                                        <input
                                            type="text"
                                            value={settings.company.fax}
                                            onChange={(e) => updateCompany("fax", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                            placeholder="02-0000-0000"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">이메일</label>
                                        <input
                                            type="email"
                                            value={settings.company.email}
                                            onChange={(e) => updateCompany("email", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                            placeholder="info@company.co.kr"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">홈페이지</label>
                                        <input
                                            type="url"
                                            value={settings.company.website}
                                            onChange={(e) => updateCompany("website", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                            placeholder="https://www.company.co.kr"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 세금 설정 */}
                    {activeSection === "tax" && (
                        <div className="space-y-6">
                            <div className="flex items-center gap-2 mb-4">
                                <Calculator className="h-5 w-5 text-brand" />
                                <h3 className="text-lg font-medium">세금 설정</h3>
                            </div>

                            {/* 부가가치세 */}
                            <div className="rounded-lg border p-4">
                                <h4 className="font-medium mb-4 text-sm text-text-subtle">부가가치세 (VAT)</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">부가세율 (%)</label>
                                        <input
                                            type="number"
                                            value={settings.tax.vatRate}
                                            onChange={(e) => updateTax("vatRate", Number(e.target.value))}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                            min="0"
                                            max="100"
                                            step="0.1"
                                        />
                                        <p className="mt-1 text-xs text-text-subtle">일반적으로 10%</p>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">부가세 반올림 방식</label>
                                        <select
                                            value={settings.tax.vatRoundingMethod}
                                            onChange={(e) => updateTax("vatRoundingMethod", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        >
                                            <option value="round">반올림</option>
                                            <option value="floor">내림 (버림)</option>
                                            <option value="ceil">올림</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">부가세 소수점 자릿수</label>
                                        <select
                                            value={settings.tax.vatDecimalPlaces}
                                            onChange={(e) => updateTax("vatDecimalPlaces", Number(e.target.value))}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        >
                                            <option value={0}>정수 (소수점 없음)</option>
                                            <option value={1}>소수점 1자리</option>
                                            <option value={2}>소수점 2자리</option>
                                        </select>
                                    </div>
                                    <div className="flex flex-col justify-end">
                                        <label className="flex items-center gap-2 cursor-pointer">
                                            <input
                                                type="checkbox"
                                                checked={settings.tax.priceIncludeVat}
                                                onChange={(e) => updateTax("priceIncludeVat", e.target.checked)}
                                                className="h-4 w-4 rounded border-gray-300"
                                            />
                                            <span className="text-sm">가격에 부가세 포함 (세금 포함가)</span>
                                        </label>
                                        <label className="flex items-center gap-2 cursor-pointer mt-2">
                                            <input
                                                type="checkbox"
                                                checked={settings.tax.autoCalculateVat}
                                                onChange={(e) => updateTax("autoCalculateVat", e.target.checked)}
                                                className="h-4 w-4 rounded border-gray-300"
                                            />
                                            <span className="text-sm">부가세 자동 계산</span>
                                        </label>
                                    </div>
                                </div>
                            </div>

                            {/* 원천징수 */}
                            <div className="rounded-lg border p-4">
                                <h4 className="font-medium mb-4 text-sm text-text-subtle">원천징수</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">원천징수세율 (%)</label>
                                        <input
                                            type="number"
                                            value={settings.tax.withholdingTaxRate}
                                            onChange={(e) => updateTax("withholdingTaxRate", Number(e.target.value))}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                            min="0"
                                            max="100"
                                            step="0.1"
                                        />
                                        <p className="mt-1 text-xs text-text-subtle">사업소득: 3.3%, 기타소득: 22%</p>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">지방소득세율 (%)</label>
                                        <input
                                            type="number"
                                            value={settings.tax.localTaxRate}
                                            onChange={(e) => updateTax("localTaxRate", Number(e.target.value))}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                            min="0"
                                            max="100"
                                            step="0.01"
                                        />
                                        <p className="mt-1 text-xs text-text-subtle">소득세의 10%</p>
                                    </div>
                                </div>
                            </div>

                            {/* 세금 계산 미리보기 */}
                            <div className="rounded-lg border p-4 bg-surface-secondary">
                                <h4 className="font-medium mb-4 text-sm">세금 계산 미리보기</h4>
                                <div className="grid grid-cols-3 gap-4 text-sm">
                                    <div className="p-3 bg-white rounded border">
                                        <p className="text-text-subtle">공급가액</p>
                                        <p className="text-xl font-bold">100,000원</p>
                                    </div>
                                    <div className="p-3 bg-white rounded border">
                                        <p className="text-text-subtle">부가세 ({settings.tax.vatRate}%)</p>
                                        <p className="text-xl font-bold">{(100000 * settings.tax.vatRate / 100).toLocaleString()}원</p>
                                    </div>
                                    <div className="p-3 bg-white rounded border">
                                        <p className="text-text-subtle">합계금액</p>
                                        <p className="text-xl font-bold text-brand">{(100000 * (1 + settings.tax.vatRate / 100)).toLocaleString()}원</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 통화 설정 */}
                    {activeSection === "currency" && (
                        <div className="space-y-6">
                            <div className="flex items-center gap-2 mb-4">
                                <Globe className="h-5 w-5 text-brand" />
                                <h3 className="text-lg font-medium">통화 설정</h3>
                            </div>

                            {/* 기본 통화 */}
                            <div className="rounded-lg border p-4">
                                <h4 className="font-medium mb-4 text-sm text-text-subtle">기본 통화</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">기준 통화</label>
                                        <select
                                            value={settings.currency.baseCurrency}
                                            onChange={(e) => updateCurrency("baseCurrency", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        >
                                            <option value="KRW">대한민국 원 (KRW)</option>
                                            <option value="USD">미국 달러 (USD)</option>
                                            <option value="EUR">유로 (EUR)</option>
                                            <option value="JPY">일본 엔 (JPY)</option>
                                            <option value="CNY">중국 위안 (CNY)</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">통화 기호</label>
                                        <input
                                            type="text"
                                            value={settings.currency.currencySymbol}
                                            onChange={(e) => updateCurrency("currencySymbol", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                            placeholder="₩"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">기호 위치</label>
                                        <select
                                            value={settings.currency.currencyPosition}
                                            onChange={(e) => updateCurrency("currencyPosition", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        >
                                            <option value="before">앞 (₩1,000)</option>
                                            <option value="after">뒤 (1,000₩)</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">소수점 자릿수</label>
                                        <select
                                            value={settings.currency.decimalPlaces}
                                            onChange={(e) => updateCurrency("decimalPlaces", Number(e.target.value))}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        >
                                            <option value={0}>없음</option>
                                            <option value={1}>1자리</option>
                                            <option value={2}>2자리</option>
                                            <option value={3}>3자리</option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            {/* 숫자 형식 */}
                            <div className="rounded-lg border p-4">
                                <h4 className="font-medium mb-4 text-sm text-text-subtle">숫자 형식</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">천단위 구분자</label>
                                        <select
                                            value={settings.currency.thousandSeparator}
                                            onChange={(e) => updateCurrency("thousandSeparator", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        >
                                            <option value=",">쉼표 (,)</option>
                                            <option value=".">마침표 (.)</option>
                                            <option value=" ">공백 ( )</option>
                                            <option value="">없음</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">소수점 구분자</label>
                                        <select
                                            value={settings.currency.decimalSeparator}
                                            onChange={(e) => updateCurrency("decimalSeparator", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        >
                                            <option value=".">마침표 (.)</option>
                                            <option value=",">쉼표 (,)</option>
                                        </select>
                                    </div>
                                </div>
                                <div className="mt-4 p-3 bg-surface-secondary rounded">
                                    <p className="text-sm text-text-subtle">미리보기:</p>
                                    <p className="text-lg font-mono">
                                        {settings.currency.currencyPosition === "before" && settings.currency.currencySymbol}
                                        1{settings.currency.thousandSeparator}234{settings.currency.thousandSeparator}567
                                        {settings.currency.decimalPlaces > 0 && settings.currency.decimalSeparator + "0".repeat(settings.currency.decimalPlaces)}
                                        {settings.currency.currencyPosition === "after" && settings.currency.currencySymbol}
                                    </p>
                                </div>
                            </div>

                            {/* 환율 설정 */}
                            <div className="rounded-lg border p-4">
                                <h4 className="font-medium mb-4 text-sm text-text-subtle">환율 설정 (KRW 기준)</h4>
                                <div className="space-y-3">
                                    {Object.entries(settings.currency.exchangeRates).map(([currency, rate]) => (
                                        <div key={currency} className="flex items-center gap-4">
                                            <span className="w-16 font-medium">{currency}</span>
                                            <input
                                                type="number"
                                                value={rate}
                                                onChange={(e) => {
                                                    const newRates = { ...settings.currency.exchangeRates, [currency]: Number(e.target.value) };
                                                    updateCurrency("exchangeRates", newRates);
                                                }}
                                                className="w-32 rounded border px-3 py-2 text-sm text-right focus:border-brand focus:ring-1 focus:ring-brand"
                                            />
                                            <span className="text-sm text-text-subtle">원</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 화면 설정 */}
                    {activeSection === "ui" && (
                        <div className="space-y-6">
                            <div className="flex items-center gap-2 mb-4">
                                <Palette className="h-5 w-5 text-brand" />
                                <h3 className="text-lg font-medium">화면 설정</h3>
                            </div>

                            {/* 테마 */}
                            <div className="rounded-lg border p-4">
                                <h4 className="font-medium mb-4 text-sm text-text-subtle">테마 및 외관</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">테마</label>
                                        <select
                                            value={settings.ui.theme}
                                            onChange={(e) => updateUI("theme", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        >
                                            <option value="light">라이트 모드</option>
                                            <option value="dark">다크 모드</option>
                                            <option value="system">시스템 설정 따름</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">기본 색상</label>
                                        <div className="flex gap-2">
                                            <input
                                                type="color"
                                                value={settings.ui.primaryColor}
                                                onChange={(e) => updateUI("primaryColor", e.target.value)}
                                                className="h-10 w-20 rounded border cursor-pointer"
                                            />
                                            <input
                                                type="text"
                                                value={settings.ui.primaryColor}
                                                onChange={(e) => updateUI("primaryColor", e.target.value)}
                                                className="flex-1 rounded border px-3 py-2 text-sm font-mono focus:border-brand focus:ring-1 focus:ring-brand"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">글꼴 크기</label>
                                        <select
                                            value={settings.ui.fontSize}
                                            onChange={(e) => updateUI("fontSize", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        >
                                            <option value="small">작게</option>
                                            <option value="medium">보통</option>
                                            <option value="large">크게</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">언어</label>
                                        <select
                                            value={settings.ui.language}
                                            onChange={(e) => updateUI("language", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        >
                                            <option value="ko">한국어</option>
                                            <option value="en">English</option>
                                            <option value="ja">日本語</option>
                                            <option value="zh">中文</option>
                                        </select>
                                    </div>
                                </div>
                                <div className="mt-4 space-y-2">
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={settings.ui.compactMode}
                                            onChange={(e) => updateUI("compactMode", e.target.checked)}
                                            className="h-4 w-4 rounded border-gray-300"
                                        />
                                        <span className="text-sm">컴팩트 모드 (화면 요소 간격 줄임)</span>
                                    </label>
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={settings.ui.showTooltips}
                                            onChange={(e) => updateUI("showTooltips", e.target.checked)}
                                            className="h-4 w-4 rounded border-gray-300"
                                        />
                                        <span className="text-sm">툴팁 표시</span>
                                    </label>
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={settings.ui.animationsEnabled}
                                            onChange={(e) => updateUI("animationsEnabled", e.target.checked)}
                                            className="h-4 w-4 rounded border-gray-300"
                                        />
                                        <span className="text-sm">애니메이션 효과</span>
                                    </label>
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={settings.ui.sidebarCollapsed}
                                            onChange={(e) => updateUI("sidebarCollapsed", e.target.checked)}
                                            className="h-4 w-4 rounded border-gray-300"
                                        />
                                        <span className="text-sm">사이드바 기본 접힘</span>
                                    </label>
                                </div>
                            </div>

                            {/* 날짜/시간 형식 */}
                            <div className="rounded-lg border p-4">
                                <h4 className="font-medium mb-4 text-sm text-text-subtle">날짜 및 시간</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">날짜 형식</label>
                                        <select
                                            value={settings.ui.dateFormat}
                                            onChange={(e) => updateUI("dateFormat", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        >
                                            <option value="YYYY-MM-DD">2025-12-05</option>
                                            <option value="YYYY/MM/DD">2025/12/05</option>
                                            <option value="YYYY년 MM월 DD일">2025년 12월 05일</option>
                                            <option value="DD-MM-YYYY">05-12-2025</option>
                                            <option value="MM/DD/YYYY">12/05/2025</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">시간 형식</label>
                                        <select
                                            value={settings.ui.timeFormat}
                                            onChange={(e) => updateUI("timeFormat", e.target.value as "12h" | "24h")}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        >
                                            <option value="24h">24시간 (14:30)</option>
                                            <option value="12h">12시간 (오후 2:30)</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">주 시작일</label>
                                        <select
                                            value={settings.ui.firstDayOfWeek}
                                            onChange={(e) => updateUI("firstDayOfWeek", Number(e.target.value))}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        >
                                            <option value={0}>일요일</option>
                                            <option value={1}>월요일</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">시간대</label>
                                        <select
                                            value={settings.ui.timezone}
                                            onChange={(e) => updateUI("timezone", e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        >
                                            <option value="Asia/Seoul">서울 (UTC+9)</option>
                                            <option value="Asia/Tokyo">도쿄 (UTC+9)</option>
                                            <option value="America/New_York">뉴욕 (UTC-5)</option>
                                            <option value="Europe/London">런던 (UTC+0)</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 보안 설정 */}
                    {activeSection === "security" && (
                        <div className="space-y-6">
                            <div className="flex items-center gap-2 mb-4">
                                <Shield className="h-5 w-5 text-brand" />
                                <h3 className="text-lg font-medium">보안 설정</h3>
                            </div>

                            {/* 자동 로그아웃 */}
                            <div className="rounded-lg border p-4">
                                <h4 className="font-medium mb-4 text-sm text-text-subtle">세션 관리</h4>
                                <div className="space-y-4">
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={settings.security.autoLogout}
                                            onChange={(e) => updateSecurity("autoLogout", e.target.checked)}
                                            className="h-4 w-4 rounded border-gray-300"
                                        />
                                        <span className="text-sm">비활성 시 자동 로그아웃</span>
                                    </label>
                                    {settings.security.autoLogout && (
                                        <div className="ml-6">
                                            <label className="block text-sm font-medium mb-1">자동 로그아웃 시간 (분)</label>
                                            <input
                                                type="number"
                                                value={settings.security.autoLogoutMinutes}
                                                onChange={(e) => updateSecurity("autoLogoutMinutes", Number(e.target.value))}
                                                className="w-32 rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                                min="5"
                                                max="480"
                                            />
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* 비밀번호 정책 */}
                            <div className="rounded-lg border p-4">
                                <h4 className="font-medium mb-4 text-sm text-text-subtle">비밀번호 정책</h4>
                                <div className="space-y-4">
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={settings.security.requirePasswordChange}
                                            onChange={(e) => updateSecurity("requirePasswordChange", e.target.checked)}
                                            className="h-4 w-4 rounded border-gray-300"
                                        />
                                        <span className="text-sm">정기 비밀번호 변경 요구</span>
                                    </label>
                                    {settings.security.requirePasswordChange && (
                                        <div className="ml-6">
                                            <label className="block text-sm font-medium mb-1">변경 주기 (일)</label>
                                            <input
                                                type="number"
                                                value={settings.security.passwordChangeDays}
                                                onChange={(e) => updateSecurity("passwordChangeDays", Number(e.target.value))}
                                                className="w-32 rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                                min="30"
                                                max="365"
                                            />
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* 2단계 인증 */}
                            <div className="rounded-lg border p-4">
                                <h4 className="font-medium mb-4 text-sm text-text-subtle">추가 보안</h4>
                                <div className="space-y-4">
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={settings.security.twoFactorEnabled}
                                            onChange={(e) => updateSecurity("twoFactorEnabled", e.target.checked)}
                                            className="h-4 w-4 rounded border-gray-300"
                                        />
                                        <span className="text-sm">2단계 인증 (OTP)</span>
                                    </label>
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={settings.security.loginNotification}
                                            onChange={(e) => updateSecurity("loginNotification", e.target.checked)}
                                            className="h-4 w-4 rounded border-gray-300"
                                        />
                                        <span className="text-sm">로그인 알림 (이메일)</span>
                                    </label>
                                </div>
                            </div>

                            {/* IP 화이트리스트 */}
                            <div className="rounded-lg border p-4">
                                <h4 className="font-medium mb-4 text-sm text-text-subtle">IP 접근 제한</h4>
                                <div className="space-y-2">
                                    <p className="text-sm text-text-subtle">허용된 IP 주소만 접근 가능하도록 설정합니다. 비워두면 모든 IP에서 접근 가능합니다.</p>
                                    <div className="flex gap-2">
                                        <input
                                            type="text"
                                            placeholder="IP 주소 (예: 192.168.1.1)"
                                            className="flex-1 rounded border px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand"
                                        />
                                        <button className="rounded border px-4 py-2 text-sm hover:bg-surface-secondary">
                                            추가
                                        </button>
                                    </div>
                                    {settings.security.ipWhitelist.length > 0 && (
                                        <div className="mt-2 space-y-1">
                                            {settings.security.ipWhitelist.map((ip, idx) => (
                                                <div key={idx} className="flex items-center justify-between rounded bg-surface-secondary px-3 py-2">
                                                    <span className="font-mono text-sm">{ip}</span>
                                                    <button className="text-red-500 hover:text-red-700">삭제</button>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* 사업장 검색 모달 */}
            {showBusinessSearchModal && (
                <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/40">
                    <div className="w-[450px] rounded-lg border bg-white shadow-xl">
                        <div className="flex items-center justify-between border-b bg-brand px-4 py-2">
                            <span className="text-sm font-medium text-white">사업장 선택</span>
                            <button onClick={() => setShowBusinessSearchModal(false)} className="text-white hover:text-gray-200">
                                <X className="h-4 w-4" />
                            </button>
                        </div>
                        <div className="max-h-[300px] overflow-auto p-4">
                            {businessList.length === 0 ? (
                                <p className="text-center text-sm text-gray-500">등록된 사업장이 없습니다.</p>
                            ) : (
                                <table className="w-full border-collapse text-sm">
                                    <thead className="sticky top-0 bg-gray-100">
                                        <tr>
                                            <th className="border px-3 py-2 text-left">사업장명</th>
                                            <th className="border px-3 py-2 text-left">사업자번호</th>
                                            <th className="border px-3 py-2 text-left">대표자</th>
                                            <th className="border px-3 py-2 w-16"></th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {businessList.map((biz, idx) => (
                                            <tr key={idx} className="hover:bg-gray-50">
                                                <td className="border px-3 py-2">{biz.name}</td>
                                                <td className="border px-3 py-2">{biz.businessNumber}</td>
                                                <td className="border px-3 py-2">{biz.representative}</td>
                                                <td className="border px-3 py-2 text-center">
                                                    <button
                                                        onClick={() => handleSelectBusiness(biz)}
                                                        className="rounded bg-brand px-2 py-1 text-xs text-white hover:bg-brand-dark"
                                                    >
                                                        선택
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                        <div className="flex justify-end border-t px-4 py-2">
                            <button
                                onClick={() => setShowBusinessSearchModal(false)}
                                className="rounded border px-4 py-1.5 text-sm hover:bg-surface-secondary"
                            >
                                닫기
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
