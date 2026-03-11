"use client";

import React, { useState, useEffect } from "react";
import {
    FileText,
    Server,
    Key,
    Shield,
    Clock,
    List,
    Settings,
    Plus,
    Trash2,
    Edit,
    Eye,
    RefreshCw,
    Download,
    Upload,
    Check,
    X,
    AlertTriangle,
    Info,
    Calendar,
    Search,
    Filter,
    Send,
    CheckCircle,
    XCircle,
    AlertCircle,
    Loader2,
    Building2,
    User,
    Phone,
    Mail,
    CreditCard,
    FileCheck,
    FilePlus,
    FileX,
    Lock,
    Unlock,
    ExternalLink,
    Copy,
    MoreVertical,
    ChevronDown,
    ChevronRight,
    RotateCcw,
    Zap,
    Bell,
    History,
} from "lucide-react";

// ===== 인터페이스 정의 =====
interface TaxInvoiceAPI {
    id: string;
    name: string;
    provider: "nts" | "popbill" | "barobill" | "ezform" | "custom";
    apiKey: string;
    secretKey: string;
    corpNum: string;
    testMode: boolean;
    isDefault: boolean;
    isActive: boolean;
    lastSyncAt?: string;
    testResult?: {
        success: boolean;
        message: string;
        testedAt: string;
    };
}

interface Certificate {
    id: string;
    name: string;
    type: "npki" | "gpki" | "signkorea" | "koscom";
    serialNumber: string;
    issuer: string;
    subject: string;
    validFrom: string;
    validTo: string;
    password: string;
    filePath: string;
    isDefault: boolean;
    isActive: boolean;
}

interface IssuanceSettings {
    autoIssue: boolean;
    issueTime: string;
    issueCondition: "immediate" | "daily" | "weekly" | "monthly";
    requireApproval: boolean;
    approvers: string[];
    defaultTaxType: "01" | "02" | "03" | "04";
    defaultPurposeType: "01" | "02" | "03" | "04";
    roundingMethod: "round" | "floor" | "ceil";
    autoSendEmail: boolean;
    autoSendSms: boolean;
    retryOnFail: boolean;
    maxRetries: number;
}

interface TaxInvoice {
    id: string;
    invoiceNo: string;
    issueDate: string;
    supplierName: string;
    supplierCorpNum: string;
    buyerName: string;
    buyerCorpNum: string;
    supplyAmount: number;
    taxAmount: number;
    totalAmount: number;
    status: "draft" | "issued" | "sent" | "received" | "rejected" | "cancelled";
    ntsConfirmNum?: string;
    issuedAt?: string;
    sentAt?: string;
    errorMessage?: string;
}

interface TaxInvoiceHistory {
    id: string;
    invoiceNo: string;
    action: "created" | "issued" | "sent" | "modified" | "cancelled" | "rejected";
    timestamp: string;
    userId: string;
    userName: string;
    description: string;
    details?: string;
}

interface NotificationSettings {
    onIssue: boolean;
    onReceive: boolean;
    onReject: boolean;
    onCancel: boolean;
    onExpiry: boolean;
    expiryDays: number;
    notifyEmail: string[];
    notifySms: string[];
}

interface TaxInvoiceSettingsData {
    apis: TaxInvoiceAPI[];
    certificates: Certificate[];
    issuanceSettings: IssuanceSettings;
    notifications: NotificationSettings;
    invoices: TaxInvoice[];
    history: TaxInvoiceHistory[];
    companyInfo: {
        corpNum: string;
        corpName: string;
        ceoName: string;
        address: string;
        bizType: string;
        bizClass: string;
        contactName: string;
        contactEmail: string;
        contactPhone: string;
    };
}

// ===== 기본 데이터 =====
const defaultSettings: TaxInvoiceSettingsData = {
    apis: [
        {
            id: "api_1",
            name: "팝빌 API",
            provider: "popbill",
            apiKey: "",
            secretKey: "",
            corpNum: "",
            testMode: true,
            isDefault: true,
            isActive: true,
        },
    ],
    certificates: [],
    issuanceSettings: {
        autoIssue: false,
        issueTime: "09:00",
        issueCondition: "daily",
        requireApproval: true,
        approvers: [],
        defaultTaxType: "01",
        defaultPurposeType: "01",
        roundingMethod: "round",
        autoSendEmail: true,
        autoSendSms: false,
        retryOnFail: true,
        maxRetries: 3,
    },
    notifications: {
        onIssue: true,
        onReceive: true,
        onReject: true,
        onCancel: true,
        onExpiry: true,
        expiryDays: 7,
        notifyEmail: [],
        notifySms: [],
    },
    invoices: [],
    history: [],
    companyInfo: {
        corpNum: "",
        corpName: "(주)한국산업",
        ceoName: "홍길동",
        address: "서울시 강남구 테헤란로 123",
        bizType: "제조업",
        bizClass: "전기설비",
        contactName: "김담당",
        contactEmail: "contact@company.com",
        contactPhone: "02-1234-5678",
    },
};

// ===== 메인 컴포넌트 =====
export function TaxInvoiceSettingsWindow() {
    const [activeTab, setActiveTab] = useState("api");
    const [settings, setSettings] = useState<TaxInvoiceSettingsData>(defaultSettings);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: "success" | "error" | "info"; text: string } | null>(null);

    // 설정 로드
    useEffect(() => {
        const saved = localStorage.getItem("erp_taxinvoice_settings");
        if (saved) {
            try {
                setSettings(JSON.parse(saved));
            } catch (e) {
                console.error("전자세금계산서 설정 로드 실패:", e);
            }
        }
    }, []);

    // 설정 저장
    const handleSave = async () => {
        setSaving(true);
        try {
            localStorage.setItem("erp_taxinvoice_settings", JSON.stringify(settings));
            window.dispatchEvent(new CustomEvent("kis-erp-settings-updated"));
            setMessage({ type: "success", text: "전자세금계산서 설정이 저장되었습니다." });
            setTimeout(() => setMessage(null), 3000);
        } catch (error) {
            setMessage({ type: "error", text: "설정 저장에 실패했습니다." });
        } finally {
            setSaving(false);
        }
    };

    const tabs = [
        { id: "api", label: "API 연동", icon: Server },
        { id: "certificate", label: "인증서 관리", icon: Key },
        { id: "issuance", label: "발행 설정", icon: FilePlus },
        { id: "auto", label: "자동 발행", icon: Zap },
        { id: "company", label: "사업자 정보", icon: Building2 },
        { id: "history", label: "발행 이력", icon: History },
        { id: "notifications", label: "알림 설정", icon: Bell },
        { id: "general", label: "일반 설정", icon: Settings },
    ];

    return (
        <div className="flex h-full flex-col bg-white">
            {/* 상단 툴바 */}
            <div className="flex items-center justify-between border-b bg-gray-50 px-4 py-2">
                <div className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-indigo-600" />
                    <span className="font-medium">전자세금계산서 설정</span>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center gap-1 rounded bg-indigo-600 px-4 py-1.5 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
                    >
                        {saving ? (
                            <RefreshCw className="h-4 w-4 animate-spin" />
                        ) : (
                            <Check className="h-4 w-4" />
                        )}
                        {saving ? "저장 중..." : "저장"}
                    </button>
                </div>
            </div>

            {/* 알림 메시지 */}
            {message && (
                <div
                    className={`mx-4 mt-2 flex items-center gap-2 rounded px-3 py-2 text-sm ${
                        message.type === "success"
                            ? "bg-green-50 text-green-700"
                            : message.type === "error"
                            ? "bg-red-50 text-red-700"
                            : "bg-blue-50 text-blue-700"
                    }`}
                >
                    {message.type === "success" && <Check className="h-4 w-4" />}
                    {message.type === "error" && <X className="h-4 w-4" />}
                    {message.type === "info" && <Info className="h-4 w-4" />}
                    {message.text}
                </div>
            )}

            <div className="flex flex-1 overflow-hidden">
                {/* 좌측 탭 메뉴 */}
                <div className="w-48 border-r bg-gray-50 p-2">
                    {tabs.map((tab) => {
                        const Icon = tab.icon;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex w-full items-center gap-2 rounded px-3 py-2 text-left text-sm ${
                                    activeTab === tab.id
                                        ? "bg-indigo-600 text-white"
                                        : "text-gray-700 hover:bg-gray-200"
                                }`}
                            >
                                <Icon className="h-4 w-4" />
                                {tab.label}
                            </button>
                        );
                    })}
                </div>

                {/* 우측 콘텐츠 */}
                <div className="flex-1 overflow-auto p-4">
                    {activeTab === "api" && (
                        <APITab settings={settings} setSettings={setSettings} setMessage={setMessage} />
                    )}
                    {activeTab === "certificate" && (
                        <CertificateTab settings={settings} setSettings={setSettings} />
                    )}
                    {activeTab === "issuance" && (
                        <IssuanceTab settings={settings} setSettings={setSettings} />
                    )}
                    {activeTab === "auto" && (
                        <AutoIssuanceTab settings={settings} setSettings={setSettings} />
                    )}
                    {activeTab === "company" && (
                        <CompanyInfoTab settings={settings} setSettings={setSettings} />
                    )}
                    {activeTab === "history" && (
                        <HistoryTab settings={settings} />
                    )}
                    {activeTab === "notifications" && (
                        <NotificationsTab settings={settings} setSettings={setSettings} />
                    )}
                    {activeTab === "general" && (
                        <GeneralTab settings={settings} setSettings={setSettings} />
                    )}
                </div>
            </div>
        </div>
    );
}

// ===== API 연동 탭 =====
function APITab({
    settings,
    setSettings,
    setMessage,
}: {
    settings: TaxInvoiceSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<TaxInvoiceSettingsData>>;
    setMessage: React.Dispatch<React.SetStateAction<{ type: "success" | "error" | "info"; text: string } | null>>;
}) {
    const [selectedAPI, setSelectedAPI] = useState<TaxInvoiceAPI | null>(
        settings.apis[0] || null
    );
    const [testing, setTesting] = useState(false);

    const providers = [
        { id: "nts", name: "국세청 홈택스" },
        { id: "popbill", name: "팝빌" },
        { id: "barobill", name: "바로빌" },
        { id: "ezform", name: "이지폼" },
        { id: "custom", name: "사용자 정의" },
    ];

    const handleAddAPI = () => {
        const newAPI: TaxInvoiceAPI = {
            id: `api_${Date.now()}`,
            name: "새 API 연동",
            provider: "popbill",
            apiKey: "",
            secretKey: "",
            corpNum: "",
            testMode: true,
            isDefault: settings.apis.length === 0,
            isActive: true,
        };
        setSettings({
            ...settings,
            apis: [...settings.apis, newAPI],
        });
        setSelectedAPI(newAPI);
    };

    const handleTestConnection = async () => {
        if (!selectedAPI) return;
        setTesting(true);
        setTimeout(() => {
            const success = Boolean(selectedAPI.apiKey && selectedAPI.corpNum);
            setSettings({
                ...settings,
                apis: settings.apis.map((a) =>
                    a.id === selectedAPI.id
                        ? {
                              ...a,
                              testResult: {
                                  success,
                                  message: success ? "API 연결 성공" : "연결 실패: API 키를 확인하세요",
                                  testedAt: new Date().toISOString(),
                              },
                          }
                        : a
                ),
            });
            setMessage({
                type: success ? "success" : "error",
                text: success ? "API 연결 테스트 성공" : "API 연결 테스트 실패",
            });
            setTesting(false);
        }, 2000);
    };

    const updateAPI = (updates: Partial<TaxInvoiceAPI>) => {
        if (!selectedAPI) return;
        const updated = { ...selectedAPI, ...updates };
        setSelectedAPI(updated);
        setSettings({
            ...settings,
            apis: settings.apis.map((a) =>
                a.id === selectedAPI.id ? updated : a
            ),
        });
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">API 연동 관리</h3>
                <button
                    onClick={handleAddAPI}
                    className="flex items-center gap-1 rounded bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-700"
                >
                    <Plus className="h-4 w-4" />
                    API 추가
                </button>
            </div>

            <div className="grid grid-cols-3 gap-4">
                {/* API 목록 */}
                <div className="col-span-1 rounded border">
                    <div className="border-b bg-gray-50 px-3 py-2 text-sm font-medium">
                        API 목록 ({settings.apis.length})
                    </div>
                    <div className="max-h-96 overflow-auto">
                        {settings.apis.map((api) => (
                            <div
                                key={api.id}
                                onClick={() => setSelectedAPI(api)}
                                className={`flex cursor-pointer items-center justify-between border-b px-3 py-2 hover:bg-gray-50 ${
                                    selectedAPI?.id === api.id ? "bg-indigo-50" : ""
                                }`}
                            >
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm font-medium">{api.name}</span>
                                        {api.isDefault && (
                                            <span className="rounded bg-indigo-100 px-1.5 py-0.5 text-xs text-indigo-700">
                                                기본
                                            </span>
                                        )}
                                        {api.testMode && (
                                            <span className="rounded bg-yellow-100 px-1.5 py-0.5 text-xs text-yellow-700">
                                                테스트
                                            </span>
                                        )}
                                    </div>
                                    <div className="text-xs text-gray-500">
                                        {providers.find((p) => p.id === api.provider)?.name}
                                    </div>
                                </div>
                                <div className="flex items-center gap-1">
                                    {api.isActive ? (
                                        <span className="h-2 w-2 rounded-full bg-green-500"></span>
                                    ) : (
                                        <span className="h-2 w-2 rounded-full bg-gray-300"></span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* API 상세 설정 */}
                <div className="col-span-2 rounded border">
                    {selectedAPI ? (
                        <div className="p-4">
                            <div className="mb-4 flex items-center justify-between">
                                <h4 className="font-medium">API 설정</h4>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={handleTestConnection}
                                        disabled={testing}
                                        className="flex items-center gap-1 rounded border px-3 py-1 text-sm hover:bg-gray-50"
                                    >
                                        {testing ? (
                                            <RefreshCw className="h-4 w-4 animate-spin" />
                                        ) : (
                                            <Server className="h-4 w-4" />
                                        )}
                                        연결 테스트
                                    </button>
                                </div>
                            </div>

                            {selectedAPI.testResult && (
                                <div
                                    className={`mb-4 flex items-center gap-2 rounded px-3 py-2 text-sm ${
                                        selectedAPI.testResult.success
                                            ? "bg-green-50 text-green-700"
                                            : "bg-red-50 text-red-700"
                                    }`}
                                >
                                    {selectedAPI.testResult.success ? (
                                        <Check className="h-4 w-4" />
                                    ) : (
                                        <X className="h-4 w-4" />
                                    )}
                                    {selectedAPI.testResult.message}
                                </div>
                            )}

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-3">
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">연동 이름</label>
                                        <input
                                            type="text"
                                            value={selectedAPI.name}
                                            onChange={(e) => updateAPI({ name: e.target.value })}
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">서비스 제공자</label>
                                        <select
                                            value={selectedAPI.provider}
                                            onChange={(e) =>
                                                updateAPI({ provider: e.target.value as TaxInvoiceAPI["provider"] })
                                            }
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        >
                                            {providers.map((p) => (
                                                <option key={p.id} value={p.id}>
                                                    {p.name}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">사업자등록번호</label>
                                        <input
                                            type="text"
                                            value={selectedAPI.corpNum}
                                            onChange={(e) => updateAPI({ corpNum: e.target.value })}
                                            placeholder="000-00-00000"
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-3">
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">API Key</label>
                                        <input
                                            type="password"
                                            value={selectedAPI.apiKey}
                                            onChange={(e) => updateAPI({ apiKey: e.target.value })}
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">Secret Key</label>
                                        <input
                                            type="password"
                                            value={selectedAPI.secretKey}
                                            onChange={(e) => updateAPI({ secretKey: e.target.value })}
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="mt-4 flex items-center gap-4">
                                <label className="flex items-center gap-2 text-sm">
                                    <input
                                        type="checkbox"
                                        checked={selectedAPI.testMode}
                                        onChange={(e) => updateAPI({ testMode: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    테스트 모드
                                </label>
                                <label className="flex items-center gap-2 text-sm">
                                    <input
                                        type="checkbox"
                                        checked={selectedAPI.isDefault}
                                        onChange={(e) => updateAPI({ isDefault: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    기본 API로 설정
                                </label>
                                <label className="flex items-center gap-2 text-sm">
                                    <input
                                        type="checkbox"
                                        checked={selectedAPI.isActive}
                                        onChange={(e) => updateAPI({ isActive: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    활성화
                                </label>
                            </div>
                        </div>
                    ) : (
                        <div className="flex h-full items-center justify-center p-8 text-gray-500">
                            API를 선택하거나 새로 추가하세요
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// ===== 인증서 관리 탭 =====
function CertificateTab({
    settings,
    setSettings,
}: {
    settings: TaxInvoiceSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<TaxInvoiceSettingsData>>;
}) {
    const [selectedCert, setSelectedCert] = useState<Certificate | null>(
        settings.certificates[0] || null
    );

    const certTypes = [
        { id: "npki", name: "공동인증서 (NPKI)" },
        { id: "gpki", name: "행정전자서명 (GPKI)" },
        { id: "signkorea", name: "SignKorea" },
        { id: "koscom", name: "코스콤" },
    ];

    const handleAddCert = () => {
        const newCert: Certificate = {
            id: `cert_${Date.now()}`,
            name: "새 인증서",
            type: "npki",
            serialNumber: "",
            issuer: "",
            subject: "",
            validFrom: "",
            validTo: "",
            password: "",
            filePath: "",
            isDefault: settings.certificates.length === 0,
            isActive: true,
        };
        setSettings({
            ...settings,
            certificates: [...settings.certificates, newCert],
        });
        setSelectedCert(newCert);
    };

    const updateCert = (updates: Partial<Certificate>) => {
        if (!selectedCert) return;
        const updated = { ...selectedCert, ...updates };
        setSelectedCert(updated);
        setSettings({
            ...settings,
            certificates: settings.certificates.map((c) =>
                c.id === selectedCert.id ? updated : c
            ),
        });
    };

    const isExpired = (validTo: string) => {
        return validTo && new Date(validTo) < new Date();
    };

    const isExpiringSoon = (validTo: string) => {
        if (!validTo) return false;
        const expiry = new Date(validTo);
        const now = new Date();
        const diffDays = Math.ceil((expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
        return diffDays > 0 && diffDays <= 30;
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">인증서 관리</h3>
                <div className="flex items-center gap-2">
                    <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-gray-50">
                        <Upload className="h-4 w-4" />
                        인증서 가져오기
                    </button>
                    <button
                        onClick={handleAddCert}
                        className="flex items-center gap-1 rounded bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-700"
                    >
                        <Plus className="h-4 w-4" />
                        인증서 등록
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
                {/* 인증서 목록 */}
                <div className="col-span-1 rounded border">
                    <div className="border-b bg-gray-50 px-3 py-2 text-sm font-medium">
                        인증서 목록 ({settings.certificates.length})
                    </div>
                    <div className="max-h-96 overflow-auto">
                        {settings.certificates.map((cert) => (
                            <div
                                key={cert.id}
                                onClick={() => setSelectedCert(cert)}
                                className={`cursor-pointer border-b px-3 py-2 hover:bg-gray-50 ${
                                    selectedCert?.id === cert.id ? "bg-indigo-50" : ""
                                }`}
                            >
                                <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium">{cert.name}</span>
                                    <div className="flex items-center gap-1">
                                        {isExpired(cert.validTo) && (
                                            <span className="rounded bg-red-100 px-1.5 py-0.5 text-xs text-red-700">
                                                만료됨
                                            </span>
                                        )}
                                        {isExpiringSoon(cert.validTo) && !isExpired(cert.validTo) && (
                                            <span className="rounded bg-yellow-100 px-1.5 py-0.5 text-xs text-yellow-700">
                                                만료임박
                                            </span>
                                        )}
                                        {cert.isDefault && (
                                            <span className="rounded bg-indigo-100 px-1.5 py-0.5 text-xs text-indigo-700">
                                                기본
                                            </span>
                                        )}
                                    </div>
                                </div>
                                <div className="text-xs text-gray-500">
                                    {certTypes.find((t) => t.id === cert.type)?.name}
                                </div>
                            </div>
                        ))}
                        {settings.certificates.length === 0 && (
                            <div className="p-4 text-center text-sm text-gray-500">
                                등록된 인증서가 없습니다
                            </div>
                        )}
                    </div>
                </div>

                {/* 인증서 상세 */}
                <div className="col-span-2 rounded border p-4">
                    {selectedCert ? (
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="mb-1 block text-sm font-medium">인증서 이름</label>
                                    <input
                                        type="text"
                                        value={selectedCert.name}
                                        onChange={(e) => updateCert({ name: e.target.value })}
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium">인증서 종류</label>
                                    <select
                                        value={selectedCert.type}
                                        onChange={(e) =>
                                            updateCert({ type: e.target.value as Certificate["type"] })
                                        }
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                    >
                                        {certTypes.map((t) => (
                                            <option key={t.id} value={t.id}>
                                                {t.name}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium">발급자</label>
                                    <input
                                        type="text"
                                        value={selectedCert.issuer}
                                        onChange={(e) => updateCert({ issuer: e.target.value })}
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium">시리얼 번호</label>
                                    <input
                                        type="text"
                                        value={selectedCert.serialNumber}
                                        onChange={(e) => updateCert({ serialNumber: e.target.value })}
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium">유효기간 시작</label>
                                    <input
                                        type="date"
                                        value={selectedCert.validFrom}
                                        onChange={(e) => updateCert({ validFrom: e.target.value })}
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium">유효기간 종료</label>
                                    <input
                                        type="date"
                                        value={selectedCert.validTo}
                                        onChange={(e) => updateCert({ validTo: e.target.value })}
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium">인증서 경로</label>
                                    <input
                                        type="text"
                                        value={selectedCert.filePath}
                                        onChange={(e) => updateCert({ filePath: e.target.value })}
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium">비밀번호</label>
                                    <input
                                        type="password"
                                        value={selectedCert.password}
                                        onChange={(e) => updateCert({ password: e.target.value })}
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                    />
                                </div>
                            </div>

                            <div className="flex items-center gap-4">
                                <label className="flex items-center gap-2 text-sm">
                                    <input
                                        type="checkbox"
                                        checked={selectedCert.isDefault}
                                        onChange={(e) => updateCert({ isDefault: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    기본 인증서로 설정
                                </label>
                                <label className="flex items-center gap-2 text-sm">
                                    <input
                                        type="checkbox"
                                        checked={selectedCert.isActive}
                                        onChange={(e) => updateCert({ isActive: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    활성화
                                </label>
                            </div>
                        </div>
                    ) : (
                        <div className="flex h-full items-center justify-center text-gray-500">
                            인증서를 선택하거나 새로 등록하세요
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// ===== 발행 설정 탭 =====
function IssuanceTab({
    settings,
    setSettings,
}: {
    settings: TaxInvoiceSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<TaxInvoiceSettingsData>>;
}) {
    const updateIssuance = (updates: Partial<IssuanceSettings>) => {
        setSettings({
            ...settings,
            issuanceSettings: { ...settings.issuanceSettings, ...updates },
        });
    };

    const taxTypes = [
        { id: "01", name: "과세" },
        { id: "02", name: "영세율" },
        { id: "03", name: "면세" },
        { id: "04", name: "비과세" },
    ];

    const purposeTypes = [
        { id: "01", name: "영수" },
        { id: "02", name: "청구" },
        { id: "03", name: "영수(수정)" },
        { id: "04", name: "청구(수정)" },
    ];

    return (
        <div className="space-y-6">
            <h3 className="text-lg font-medium">발행 설정</h3>

            <div className="grid grid-cols-2 gap-6">
                {/* 기본 설정 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">기본 설정</h4>
                    <div className="space-y-4">
                        <div>
                            <label className="mb-1 block text-sm font-medium">기본 세금 유형</label>
                            <select
                                value={settings.issuanceSettings.defaultTaxType}
                                onChange={(e) =>
                                    updateIssuance({
                                        defaultTaxType: e.target.value as IssuanceSettings["defaultTaxType"],
                                    })
                                }
                                className="w-full rounded border px-3 py-1.5 text-sm"
                            >
                                {taxTypes.map((t) => (
                                    <option key={t.id} value={t.id}>
                                        {t.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="mb-1 block text-sm font-medium">기본 발행 목적</label>
                            <select
                                value={settings.issuanceSettings.defaultPurposeType}
                                onChange={(e) =>
                                    updateIssuance({
                                        defaultPurposeType: e.target.value as IssuanceSettings["defaultPurposeType"],
                                    })
                                }
                                className="w-full rounded border px-3 py-1.5 text-sm"
                            >
                                {purposeTypes.map((t) => (
                                    <option key={t.id} value={t.id}>
                                        {t.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="mb-1 block text-sm font-medium">금액 계산 방식</label>
                            <select
                                value={settings.issuanceSettings.roundingMethod}
                                onChange={(e) =>
                                    updateIssuance({
                                        roundingMethod: e.target.value as IssuanceSettings["roundingMethod"],
                                    })
                                }
                                className="w-full rounded border px-3 py-1.5 text-sm"
                            >
                                <option value="round">반올림</option>
                                <option value="floor">내림</option>
                                <option value="ceil">올림</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* 승인 설정 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">승인 설정</h4>
                    <div className="space-y-4">
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.issuanceSettings.requireApproval}
                                onChange={(e) => updateIssuance({ requireApproval: e.target.checked })}
                                className="h-4 w-4"
                            />
                            발행 전 승인 필요
                        </label>
                        <div>
                            <label className="mb-1 block text-sm font-medium">승인자 목록</label>
                            <textarea
                                value={settings.issuanceSettings.approvers.join("\n")}
                                onChange={(e) =>
                                    updateIssuance({
                                        approvers: e.target.value.split("\n").filter((a) => a.trim()),
                                    })
                                }
                                rows={3}
                                placeholder="이메일 주소를 한 줄에 하나씩 입력"
                                className="w-full rounded border px-3 py-1.5 text-sm"
                                disabled={!settings.issuanceSettings.requireApproval}
                            />
                        </div>
                    </div>
                </div>

                {/* 발송 설정 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">발송 설정</h4>
                    <div className="space-y-3">
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.issuanceSettings.autoSendEmail}
                                onChange={(e) => updateIssuance({ autoSendEmail: e.target.checked })}
                                className="h-4 w-4"
                            />
                            발행 시 이메일 자동 전송
                        </label>
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.issuanceSettings.autoSendSms}
                                onChange={(e) => updateIssuance({ autoSendSms: e.target.checked })}
                                className="h-4 w-4"
                            />
                            발행 시 SMS 자동 전송
                        </label>
                    </div>
                </div>

                {/* 재시도 설정 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">재시도 설정</h4>
                    <div className="space-y-4">
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.issuanceSettings.retryOnFail}
                                onChange={(e) => updateIssuance({ retryOnFail: e.target.checked })}
                                className="h-4 w-4"
                            />
                            발행 실패 시 자동 재시도
                        </label>
                        <div>
                            <label className="mb-1 block text-sm font-medium">최대 재시도 횟수</label>
                            <input
                                type="number"
                                value={settings.issuanceSettings.maxRetries}
                                onChange={(e) => updateIssuance({ maxRetries: Number(e.target.value) })}
                                className="w-32 rounded border px-3 py-1.5 text-sm"
                                disabled={!settings.issuanceSettings.retryOnFail}
                            />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// ===== 자동 발행 탭 =====
function AutoIssuanceTab({
    settings,
    setSettings,
}: {
    settings: TaxInvoiceSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<TaxInvoiceSettingsData>>;
}) {
    const updateIssuance = (updates: Partial<IssuanceSettings>) => {
        setSettings({
            ...settings,
            issuanceSettings: { ...settings.issuanceSettings, ...updates },
        });
    };

    return (
        <div className="space-y-6">
            <h3 className="text-lg font-medium">자동 발행 설정</h3>

            <div className="rounded border p-4">
                <div className="space-y-4">
                    <label className="flex items-center gap-2 text-sm">
                        <input
                            type="checkbox"
                            checked={settings.issuanceSettings.autoIssue}
                            onChange={(e) => updateIssuance({ autoIssue: e.target.checked })}
                            className="h-4 w-4"
                        />
                        자동 발행 사용
                    </label>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="mb-1 block text-sm font-medium">발행 조건</label>
                            <select
                                value={settings.issuanceSettings.issueCondition}
                                onChange={(e) =>
                                    updateIssuance({
                                        issueCondition: e.target.value as IssuanceSettings["issueCondition"],
                                    })
                                }
                                className="w-full rounded border px-3 py-1.5 text-sm"
                                disabled={!settings.issuanceSettings.autoIssue}
                            >
                                <option value="immediate">즉시 발행</option>
                                <option value="daily">일별 발행</option>
                                <option value="weekly">주별 발행</option>
                                <option value="monthly">월별 발행</option>
                            </select>
                        </div>
                        <div>
                            <label className="mb-1 block text-sm font-medium">발행 시간</label>
                            <input
                                type="time"
                                value={settings.issuanceSettings.issueTime}
                                onChange={(e) => updateIssuance({ issueTime: e.target.value })}
                                className="w-full rounded border px-3 py-1.5 text-sm"
                                disabled={!settings.issuanceSettings.autoIssue || settings.issuanceSettings.issueCondition === "immediate"}
                            />
                        </div>
                    </div>

                    <div className="rounded bg-gray-50 p-3 text-sm text-gray-600">
                        <Info className="mb-1 inline h-4 w-4" />
                        <span className="ml-1">
                            {settings.issuanceSettings.issueCondition === "immediate" && "거래 완료 즉시 세금계산서가 발행됩니다."}
                            {settings.issuanceSettings.issueCondition === "daily" && `매일 ${settings.issuanceSettings.issueTime}에 전일 거래분이 일괄 발행됩니다.`}
                            {settings.issuanceSettings.issueCondition === "weekly" && `매주 월요일 ${settings.issuanceSettings.issueTime}에 전주 거래분이 일괄 발행됩니다.`}
                            {settings.issuanceSettings.issueCondition === "monthly" && `매월 1일 ${settings.issuanceSettings.issueTime}에 전월 거래분이 일괄 발행됩니다.`}
                        </span>
                    </div>
                </div>
            </div>

            {/* 자동 발행 대상 */}
            <div className="rounded border p-4">
                <h4 className="mb-4 font-medium">자동 발행 대상</h4>
                <div className="space-y-3">
                    <label className="flex items-center gap-2 text-sm">
                        <input type="checkbox" defaultChecked className="h-4 w-4" />
                        매출 거래
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                        <input type="checkbox" className="h-4 w-4" />
                        매입 거래 (역발행)
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                        <input type="checkbox" className="h-4 w-4" />
                        수정 세금계산서
                    </label>
                </div>
            </div>
        </div>
    );
}

// ===== 사업자 정보 탭 =====
function CompanyInfoTab({
    settings,
    setSettings,
}: {
    settings: TaxInvoiceSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<TaxInvoiceSettingsData>>;
}) {
    const updateCompanyInfo = (updates: Partial<typeof settings.companyInfo>) => {
        setSettings({
            ...settings,
            companyInfo: { ...settings.companyInfo, ...updates },
        });
    };

    return (
        <div className="space-y-6">
            <h3 className="text-lg font-medium">사업자 정보</h3>

            <div className="rounded border p-4">
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="mb-1 block text-sm font-medium">사업자등록번호</label>
                        <input
                            type="text"
                            value={settings.companyInfo.corpNum}
                            onChange={(e) => updateCompanyInfo({ corpNum: e.target.value })}
                            placeholder="000-00-00000"
                            className="w-full rounded border px-3 py-1.5 text-sm"
                        />
                    </div>
                    <div>
                        <label className="mb-1 block text-sm font-medium">상호 (법인명)</label>
                        <input
                            type="text"
                            value={settings.companyInfo.corpName}
                            onChange={(e) => updateCompanyInfo({ corpName: e.target.value })}
                            className="w-full rounded border px-3 py-1.5 text-sm"
                        />
                    </div>
                    <div>
                        <label className="mb-1 block text-sm font-medium">대표자명</label>
                        <input
                            type="text"
                            value={settings.companyInfo.ceoName}
                            onChange={(e) => updateCompanyInfo({ ceoName: e.target.value })}
                            className="w-full rounded border px-3 py-1.5 text-sm"
                        />
                    </div>
                    <div>
                        <label className="mb-1 block text-sm font-medium">업태</label>
                        <input
                            type="text"
                            value={settings.companyInfo.bizType}
                            onChange={(e) => updateCompanyInfo({ bizType: e.target.value })}
                            className="w-full rounded border px-3 py-1.5 text-sm"
                        />
                    </div>
                    <div>
                        <label className="mb-1 block text-sm font-medium">종목</label>
                        <input
                            type="text"
                            value={settings.companyInfo.bizClass}
                            onChange={(e) => updateCompanyInfo({ bizClass: e.target.value })}
                            className="w-full rounded border px-3 py-1.5 text-sm"
                        />
                    </div>
                    <div className="col-span-2">
                        <label className="mb-1 block text-sm font-medium">사업장 주소</label>
                        <input
                            type="text"
                            value={settings.companyInfo.address}
                            onChange={(e) => updateCompanyInfo({ address: e.target.value })}
                            className="w-full rounded border px-3 py-1.5 text-sm"
                        />
                    </div>
                </div>
            </div>

            <div className="rounded border p-4">
                <h4 className="mb-4 font-medium">담당자 정보</h4>
                <div className="grid grid-cols-3 gap-4">
                    <div>
                        <label className="mb-1 block text-sm font-medium">담당자명</label>
                        <input
                            type="text"
                            value={settings.companyInfo.contactName}
                            onChange={(e) => updateCompanyInfo({ contactName: e.target.value })}
                            className="w-full rounded border px-3 py-1.5 text-sm"
                        />
                    </div>
                    <div>
                        <label className="mb-1 block text-sm font-medium">이메일</label>
                        <input
                            type="email"
                            value={settings.companyInfo.contactEmail}
                            onChange={(e) => updateCompanyInfo({ contactEmail: e.target.value })}
                            className="w-full rounded border px-3 py-1.5 text-sm"
                        />
                    </div>
                    <div>
                        <label className="mb-1 block text-sm font-medium">전화번호</label>
                        <input
                            type="text"
                            value={settings.companyInfo.contactPhone}
                            onChange={(e) => updateCompanyInfo({ contactPhone: e.target.value })}
                            className="w-full rounded border px-3 py-1.5 text-sm"
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}

// ===== 발행 이력 탭 =====
function HistoryTab({ settings }: { settings: TaxInvoiceSettingsData }) {
    const [filterStatus, setFilterStatus] = useState<string>("all");
    const [searchTerm, setSearchTerm] = useState("");
    const [dateRange, setDateRange] = useState({ from: "", to: "" });

    const statusLabels: Record<string, { label: string; color: string; icon: React.ElementType }> = {
        draft: { label: "임시저장", color: "bg-gray-100 text-gray-700", icon: FileText },
        issued: { label: "발행완료", color: "bg-blue-100 text-blue-700", icon: FileCheck },
        sent: { label: "전송완료", color: "bg-green-100 text-green-700", icon: CheckCircle },
        received: { label: "수신완료", color: "bg-purple-100 text-purple-700", icon: CheckCircle },
        rejected: { label: "거부됨", color: "bg-red-100 text-red-700", icon: XCircle },
        cancelled: { label: "취소됨", color: "bg-orange-100 text-orange-700", icon: FileX },
    };

    // 샘플 데이터
    const sampleInvoices: TaxInvoice[] = [
        {
            id: "1",
            invoiceNo: "20240115-001",
            issueDate: "2024-01-15",
            supplierName: "(주)한국산업",
            supplierCorpNum: "123-45-67890",
            buyerName: "(주)협력사",
            buyerCorpNum: "987-65-43210",
            supplyAmount: 1000000,
            taxAmount: 100000,
            totalAmount: 1100000,
            status: "sent",
            ntsConfirmNum: "20240115123456",
            issuedAt: "2024-01-15T10:30:00",
            sentAt: "2024-01-15T10:31:00",
        },
        {
            id: "2",
            invoiceNo: "20240114-003",
            issueDate: "2024-01-14",
            supplierName: "(주)한국산업",
            supplierCorpNum: "123-45-67890",
            buyerName: "(주)거래처",
            buyerCorpNum: "555-55-55555",
            supplyAmount: 500000,
            taxAmount: 50000,
            totalAmount: 550000,
            status: "issued",
            issuedAt: "2024-01-14T14:00:00",
        },
    ];

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">발행 이력</h3>
                <div className="flex items-center gap-2">
                    <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-gray-50">
                        <Download className="h-4 w-4" />
                        내보내기
                    </button>
                    <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-gray-50">
                        <RefreshCw className="h-4 w-4" />
                        동기화
                    </button>
                </div>
            </div>

            {/* 필터 */}
            <div className="flex items-center gap-4 rounded bg-gray-50 p-3">
                <div className="flex items-center gap-2">
                    <Search className="h-4 w-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="번호, 거래처 검색..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="rounded border px-3 py-1.5 text-sm"
                    />
                </div>
                <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="rounded border px-3 py-1.5 text-sm"
                >
                    <option value="all">전체 상태</option>
                    <option value="draft">임시저장</option>
                    <option value="issued">발행완료</option>
                    <option value="sent">전송완료</option>
                    <option value="rejected">거부됨</option>
                    <option value="cancelled">취소됨</option>
                </select>
                <input
                    type="date"
                    value={dateRange.from}
                    onChange={(e) => setDateRange({ ...dateRange, from: e.target.value })}
                    className="rounded border px-3 py-1.5 text-sm"
                />
                <span className="text-gray-500">~</span>
                <input
                    type="date"
                    value={dateRange.to}
                    onChange={(e) => setDateRange({ ...dateRange, to: e.target.value })}
                    className="rounded border px-3 py-1.5 text-sm"
                />
            </div>

            {/* 이력 테이블 */}
            <div className="rounded border">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="border-b px-4 py-2 text-left">승인번호</th>
                            <th className="border-b px-4 py-2 text-left">발행일</th>
                            <th className="border-b px-4 py-2 text-left">공급받는자</th>
                            <th className="border-b px-4 py-2 text-right">공급가액</th>
                            <th className="border-b px-4 py-2 text-right">세액</th>
                            <th className="border-b px-4 py-2 text-right">합계</th>
                            <th className="border-b px-4 py-2 text-center">상태</th>
                            <th className="border-b px-4 py-2 text-center">관리</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sampleInvoices.map((invoice) => {
                            const status = statusLabels[invoice.status];
                            const StatusIcon = status.icon;
                            return (
                                <tr key={invoice.id} className="hover:bg-gray-50">
                                    <td className="border-b px-4 py-2">
                                        <div className="font-mono text-sm">{invoice.invoiceNo}</div>
                                        {invoice.ntsConfirmNum && (
                                            <div className="text-xs text-gray-500">
                                                국세청: {invoice.ntsConfirmNum}
                                            </div>
                                        )}
                                    </td>
                                    <td className="border-b px-4 py-2">{invoice.issueDate}</td>
                                    <td className="border-b px-4 py-2">
                                        <div>{invoice.buyerName}</div>
                                        <div className="text-xs text-gray-500">{invoice.buyerCorpNum}</div>
                                    </td>
                                    <td className="border-b px-4 py-2 text-right">
                                        {invoice.supplyAmount.toLocaleString()}
                                    </td>
                                    <td className="border-b px-4 py-2 text-right">
                                        {invoice.taxAmount.toLocaleString()}
                                    </td>
                                    <td className="border-b px-4 py-2 text-right font-medium">
                                        {invoice.totalAmount.toLocaleString()}
                                    </td>
                                    <td className="border-b px-4 py-2 text-center">
                                        <span className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs ${status.color}`}>
                                            <StatusIcon className="h-3 w-3" />
                                            {status.label}
                                        </span>
                                    </td>
                                    <td className="border-b px-4 py-2 text-center">
                                        <div className="flex justify-center gap-1">
                                            <button className="rounded p-1 hover:bg-gray-100">
                                                <Eye className="h-4 w-4" />
                                            </button>
                                            <button className="rounded p-1 hover:bg-gray-100">
                                                <Download className="h-4 w-4" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {/* 통계 */}
            <div className="grid grid-cols-6 gap-4">
                {Object.entries(statusLabels).map(([key, value]) => (
                    <div key={key} className="rounded border p-3 text-center">
                        <div className={`mb-1 text-2xl font-bold ${value.color.split(" ")[1]}`}>
                            {sampleInvoices.filter((i) => i.status === key).length}
                        </div>
                        <div className="text-xs text-gray-500">{value.label}</div>
                    </div>
                ))}
            </div>
        </div>
    );
}

// ===== 알림 설정 탭 =====
function NotificationsTab({
    settings,
    setSettings,
}: {
    settings: TaxInvoiceSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<TaxInvoiceSettingsData>>;
}) {
    const updateNotifications = (updates: Partial<NotificationSettings>) => {
        setSettings({
            ...settings,
            notifications: { ...settings.notifications, ...updates },
        });
    };

    return (
        <div className="space-y-6">
            <h3 className="text-lg font-medium">알림 설정</h3>

            <div className="grid grid-cols-2 gap-6">
                {/* 알림 이벤트 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">알림 이벤트</h4>
                    <div className="space-y-3">
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.notifications.onIssue}
                                onChange={(e) => updateNotifications({ onIssue: e.target.checked })}
                                className="h-4 w-4"
                            />
                            세금계산서 발행 시
                        </label>
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.notifications.onReceive}
                                onChange={(e) => updateNotifications({ onReceive: e.target.checked })}
                                className="h-4 w-4"
                            />
                            세금계산서 수신 시
                        </label>
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.notifications.onReject}
                                onChange={(e) => updateNotifications({ onReject: e.target.checked })}
                                className="h-4 w-4"
                            />
                            세금계산서 거부 시
                        </label>
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.notifications.onCancel}
                                onChange={(e) => updateNotifications({ onCancel: e.target.checked })}
                                className="h-4 w-4"
                            />
                            세금계산서 취소 시
                        </label>
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.notifications.onExpiry}
                                onChange={(e) => updateNotifications({ onExpiry: e.target.checked })}
                                className="h-4 w-4"
                            />
                            인증서 만료 임박 시
                        </label>
                        <div className="ml-6">
                            <label className="mb-1 block text-xs text-gray-500">만료 알림 기준 (일)</label>
                            <input
                                type="number"
                                value={settings.notifications.expiryDays}
                                onChange={(e) => updateNotifications({ expiryDays: Number(e.target.value) })}
                                className="w-20 rounded border px-2 py-1 text-sm"
                                disabled={!settings.notifications.onExpiry}
                            />
                        </div>
                    </div>
                </div>

                {/* 알림 수신자 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">알림 수신자</h4>
                    <div className="space-y-4">
                        <div>
                            <label className="mb-1 block text-sm font-medium">이메일 수신자</label>
                            <textarea
                                value={settings.notifications.notifyEmail.join("\n")}
                                onChange={(e) =>
                                    updateNotifications({
                                        notifyEmail: e.target.value.split("\n").filter((a) => a.trim()),
                                    })
                                }
                                rows={3}
                                placeholder="이메일 주소를 한 줄에 하나씩 입력"
                                className="w-full rounded border px-3 py-1.5 text-sm"
                            />
                        </div>
                        <div>
                            <label className="mb-1 block text-sm font-medium">SMS 수신자</label>
                            <textarea
                                value={settings.notifications.notifySms.join("\n")}
                                onChange={(e) =>
                                    updateNotifications({
                                        notifySms: e.target.value.split("\n").filter((a) => a.trim()),
                                    })
                                }
                                rows={3}
                                placeholder="전화번호를 한 줄에 하나씩 입력"
                                className="w-full rounded border px-3 py-1.5 text-sm"
                            />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// ===== 일반 설정 탭 =====
function GeneralTab({
    settings,
    setSettings,
}: {
    settings: TaxInvoiceSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<TaxInvoiceSettingsData>>;
}) {
    return (
        <div className="space-y-6">
            <h3 className="text-lg font-medium">일반 설정</h3>

            <div className="grid grid-cols-2 gap-6">
                {/* 현재 상태 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">현재 상태</h4>
                    <div className="space-y-2 text-sm">
                        <div className="flex items-center justify-between">
                            <span>등록된 API</span>
                            <span>{settings.apis.length}개</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>활성 API</span>
                            <span>{settings.apis.filter((a) => a.isActive).length}개</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>등록된 인증서</span>
                            <span>{settings.certificates.length}개</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>자동 발행</span>
                            <span className={settings.issuanceSettings.autoIssue ? "text-green-600" : "text-gray-400"}>
                                {settings.issuanceSettings.autoIssue ? "활성" : "비활성"}
                            </span>
                        </div>
                    </div>
                </div>

                {/* 발행 설정 요약 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">발행 설정 요약</h4>
                    <div className="space-y-2 text-sm">
                        <div className="flex items-center justify-between">
                            <span>승인 필요</span>
                            <span className={settings.issuanceSettings.requireApproval ? "text-yellow-600" : "text-green-600"}>
                                {settings.issuanceSettings.requireApproval ? "예" : "아니오"}
                            </span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>이메일 자동 전송</span>
                            <span className={settings.issuanceSettings.autoSendEmail ? "text-green-600" : "text-gray-400"}>
                                {settings.issuanceSettings.autoSendEmail ? "활성" : "비활성"}
                            </span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>SMS 자동 전송</span>
                            <span className={settings.issuanceSettings.autoSendSms ? "text-green-600" : "text-gray-400"}>
                                {settings.issuanceSettings.autoSendSms ? "활성" : "비활성"}
                            </span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>실패 시 재시도</span>
                            <span>
                                {settings.issuanceSettings.retryOnFail
                                    ? `최대 ${settings.issuanceSettings.maxRetries}회`
                                    : "비활성"}
                            </span>
                        </div>
                    </div>
                </div>

                {/* 데이터 관리 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">데이터 관리</h4>
                    <div className="space-y-3">
                        <button className="flex w-full items-center gap-2 rounded border px-3 py-2 text-sm hover:bg-gray-50">
                            <RefreshCw className="h-4 w-4" />
                            국세청 데이터 동기화
                        </button>
                        <button className="flex w-full items-center gap-2 rounded border px-3 py-2 text-sm hover:bg-gray-50">
                            <Download className="h-4 w-4" />
                            발행 이력 백업
                        </button>
                        <button className="flex w-full items-center gap-2 rounded border px-3 py-2 text-sm hover:bg-gray-50">
                            <RotateCcw className="h-4 w-4" />
                            설정 초기화
                        </button>
                    </div>
                </div>

                {/* 도움말 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">도움말</h4>
                    <div className="space-y-2 text-sm text-gray-600">
                        <p>
                            <ExternalLink className="mr-1 inline h-4 w-4" />
                            <a href="#" className="text-indigo-600 hover:underline">
                                전자세금계산서 가이드
                            </a>
                        </p>
                        <p>
                            <ExternalLink className="mr-1 inline h-4 w-4" />
                            <a href="#" className="text-indigo-600 hover:underline">
                                API 연동 매뉴얼
                            </a>
                        </p>
                        <p>
                            <ExternalLink className="mr-1 inline h-4 w-4" />
                            <a href="#" className="text-indigo-600 hover:underline">
                                인증서 등록 방법
                            </a>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default TaxInvoiceSettingsWindow;
