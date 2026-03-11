"use client";

import React, { useState, useEffect } from "react";
import {
    Save,
    RotateCcw,
    MessageCircle,
    Phone,
    Send,
    Clock,
    Users,
    FileText,
    Settings,
    Plus,
    Trash2,
    Edit2,
    Copy,
    CheckCircle,
    AlertCircle,
    ChevronDown,
    ChevronRight,
    TestTube,
    History,
    BarChart3,
    Bell,
    Zap,
} from "lucide-react";

// ============== 인터페이스 정의 ==============

interface SMSProvider {
    id: string;
    name: string;
    apiUrl: string;
    apiKey: string;
    apiSecret: string;
    senderId: string;
    enabled: boolean;
    testMode: boolean;
}

interface MessageTemplate {
    id: string;
    name: string;
    category: "quote" | "invoice" | "payment" | "reminder" | "greeting" | "custom";
    content: string;
    variables: string[];
    isDefault: boolean;
    createdAt: string;
    updatedAt: string;
}

interface AutoSendRule {
    id: string;
    name: string;
    event: "quote_created" | "quote_sent" | "invoice_issued" | "payment_received" | "payment_overdue" | "birthday" | "custom";
    enabled: boolean;
    templateId: string;
    delay: number;
    delayUnit: "minutes" | "hours" | "days";
    conditions: {
        field: string;
        operator: "equals" | "contains" | "greater" | "less";
        value: string;
    }[];
    recipientType: "customer" | "manager" | "custom";
    customRecipients: string[];
    schedule?: {
        type: "immediate" | "scheduled" | "recurring";
        time?: string;
        days?: number[];
    };
}

interface SendingLimit {
    dailyLimit: number;
    hourlyLimit: number;
    perCustomerDaily: number;
    blockDuplicates: boolean;
    duplicateCheckPeriod: number;
}

interface NotificationSettings {
    sendFailureAlert: boolean;
    failureAlertEmail: string;
    dailyReport: boolean;
    dailyReportTime: string;
    lowBalanceAlert: boolean;
    lowBalanceThreshold: number;
}

interface SMSLog {
    id: string;
    timestamp: string;
    recipient: string;
    content: string;
    status: "sent" | "delivered" | "failed" | "pending";
    templateUsed?: string;
    errorMessage?: string;
}

interface SMSSettings {
    provider: SMSProvider;
    senderNumbers: string[];
    defaultSenderNumber: string;
    templates: MessageTemplate[];
    autoSendRules: AutoSendRule[];
    sendingLimits: SendingLimit;
    notifications: NotificationSettings;
    recentLogs: SMSLog[];
    statistics: {
        totalSent: number;
        totalDelivered: number;
        totalFailed: number;
        monthlyUsage: number;
        remainingCredits: number;
    };
}

// ============== 기본값 정의 ==============

const defaultProvider: SMSProvider = {
    id: "default",
    name: "",
    apiUrl: "",
    apiKey: "",
    apiSecret: "",
    senderId: "",
    enabled: false,
    testMode: true,
};

const defaultSendingLimits: SendingLimit = {
    dailyLimit: 1000,
    hourlyLimit: 100,
    perCustomerDaily: 5,
    blockDuplicates: true,
    duplicateCheckPeriod: 60,
};

const defaultNotifications: NotificationSettings = {
    sendFailureAlert: true,
    failureAlertEmail: "",
    dailyReport: false,
    dailyReportTime: "09:00",
    lowBalanceAlert: true,
    lowBalanceThreshold: 100,
};

const defaultTemplates: MessageTemplate[] = [
    {
        id: "tpl_1",
        name: "견적서 발송 안내",
        category: "quote",
        content: "[{회사명}] {고객명}님, 요청하신 견적서를 발송해드렸습니다. 확인 부탁드립니다. 문의: {전화번호}",
        variables: ["회사명", "고객명", "전화번호"],
        isDefault: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
    },
    {
        id: "tpl_2",
        name: "세금계산서 발행 안내",
        category: "invoice",
        content: "[{회사명}] {고객명}님, {금액}원의 세금계산서가 발행되었습니다. 국세청 홈택스에서 확인하세요.",
        variables: ["회사명", "고객명", "금액"],
        isDefault: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
    },
    {
        id: "tpl_3",
        name: "입금 확인 안내",
        category: "payment",
        content: "[{회사명}] {고객명}님, {금액}원 입금 확인되었습니다. 감사합니다.",
        variables: ["회사명", "고객명", "금액"],
        isDefault: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
    },
    {
        id: "tpl_4",
        name: "결제 기한 알림",
        category: "reminder",
        content: "[{회사명}] {고객명}님, {마감일}까지 {금액}원 결제 부탁드립니다. 문의: {전화번호}",
        variables: ["회사명", "고객명", "마감일", "금액", "전화번호"],
        isDefault: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
    },
];

const defaultSettings: SMSSettings = {
    provider: defaultProvider,
    senderNumbers: [],
    defaultSenderNumber: "",
    templates: defaultTemplates,
    autoSendRules: [],
    sendingLimits: defaultSendingLimits,
    notifications: defaultNotifications,
    recentLogs: [],
    statistics: {
        totalSent: 0,
        totalDelivered: 0,
        totalFailed: 0,
        monthlyUsage: 0,
        remainingCredits: 0,
    },
};

// ============== 메인 컴포넌트 ==============

export function SMSSettingsWindow() {
    const [activeTab, setActiveTab] = useState<"provider" | "templates" | "autoSend" | "limits" | "logs">("provider");
    const [settings, setSettings] = useState<SMSSettings>(defaultSettings);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
    const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
        connection: true,
        sender: true,
        test: false,
        templates: true,
        rules: true,
        limits: true,
        notifications: true,
    });
    const [editingTemplate, setEditingTemplate] = useState<MessageTemplate | null>(null);
    const [editingRule, setEditingRule] = useState<AutoSendRule | null>(null);
    const [testPhone, setTestPhone] = useState("");
    const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

    // 설정 불러오기
    useEffect(() => {
        const saved = localStorage.getItem("erp_sms_settings");
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                setSettings({ ...defaultSettings, ...parsed });
            } catch (e) {
                console.error("SMS 설정 불러오기 실패:", e);
            }
        }
    }, []);

    // 설정 저장
    const handleSave = async () => {
        setSaving(true);
        try {
            localStorage.setItem("erp_sms_settings", JSON.stringify(settings));
            window.dispatchEvent(new CustomEvent("kis-erp-settings-updated"));
            setMessage({ type: "success", text: "SMS 설정이 저장되었습니다." });
            setTimeout(() => setMessage(null), 3000);
        } catch (error) {
            setMessage({ type: "error", text: "저장에 실패했습니다." });
        } finally {
            setSaving(false);
        }
    };

    // 초기화
    const handleReset = () => {
        if (confirm("모든 SMS 설정을 초기화하시겠습니까?")) {
            setSettings(defaultSettings);
        }
    };

    // 섹션 토글
    const toggleSection = (section: string) => {
        setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
    };

    // Provider 업데이트
    const updateProvider = (updates: Partial<SMSProvider>) => {
        setSettings(prev => ({
            ...prev,
            provider: { ...prev.provider, ...updates },
        }));
    };

    // 테스트 발송
    const handleTestSend = async () => {
        if (!testPhone) {
            setTestResult({ success: false, message: "전화번호를 입력하세요." });
            return;
        }
        if (!settings.provider.apiKey) {
            setTestResult({ success: false, message: "API 키를 설정하세요." });
            return;
        }

        // 시뮬레이션 (실제로는 API 호출)
        setTestResult(null);
        setTimeout(() => {
            if (settings.provider.testMode) {
                setTestResult({ success: true, message: "테스트 모드: 발송 시뮬레이션 성공" });
            } else {
                setTestResult({ success: true, message: `${testPhone}로 테스트 메시지 발송 완료` });
            }
        }, 1000);
    };

    // 템플릿 저장
    const handleSaveTemplate = (template: MessageTemplate) => {
        setSettings(prev => ({
            ...prev,
            templates: editingTemplate?.id
                ? prev.templates.map(t => t.id === template.id ? template : t)
                : [...prev.templates, { ...template, id: `tpl_${Date.now()}` }],
        }));
        setEditingTemplate(null);
    };

    // 템플릿 삭제
    const handleDeleteTemplate = (templateId: string) => {
        if (confirm("템플릿을 삭제하시겠습니까?")) {
            setSettings(prev => ({
                ...prev,
                templates: prev.templates.filter(t => t.id !== templateId),
            }));
        }
    };

    // 자동발송 규칙 저장
    const handleSaveRule = (rule: AutoSendRule) => {
        setSettings(prev => ({
            ...prev,
            autoSendRules: editingRule?.id
                ? prev.autoSendRules.map(r => r.id === rule.id ? rule : r)
                : [...prev.autoSendRules, { ...rule, id: `rule_${Date.now()}` }],
        }));
        setEditingRule(null);
    };

    // 자동발송 규칙 삭제
    const handleDeleteRule = (ruleId: string) => {
        if (confirm("자동발송 규칙을 삭제하시겠습니까?")) {
            setSettings(prev => ({
                ...prev,
                autoSendRules: prev.autoSendRules.filter(r => r.id !== ruleId),
            }));
        }
    };

    // ============== 섹션 헤더 컴포넌트 ==============
    const SectionHeader = ({ title, section, icon: Icon }: { title: string; section: string; icon: React.ElementType }) => (
        <button
            onClick={() => toggleSection(section)}
            className="flex w-full items-center gap-2 rounded bg-surface-secondary px-3 py-2 text-left font-medium hover:bg-surface"
        >
            {expandedSections[section] ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            <Icon className="h-4 w-4 text-brand" />
            {title}
        </button>
    );

    // ============== 탭 목록 ==============
    const tabs = [
        { id: "provider" as const, label: "API 연동", icon: Settings },
        { id: "templates" as const, label: "메시지 템플릿", icon: FileText },
        { id: "autoSend" as const, label: "자동발송", icon: Zap },
        { id: "limits" as const, label: "발송 제한", icon: Clock },
        { id: "logs" as const, label: "발송 이력", icon: History },
    ];

    const eventLabels: Record<string, string> = {
        quote_created: "견적서 생성",
        quote_sent: "견적서 발송",
        invoice_issued: "세금계산서 발행",
        payment_received: "입금 확인",
        payment_overdue: "결제 기한 초과",
        birthday: "생일 축하",
        custom: "사용자 정의",
    };

    const categoryLabels: Record<string, string> = {
        quote: "견적",
        invoice: "세금계산서",
        payment: "결제",
        reminder: "알림",
        greeting: "인사",
        custom: "기타",
    };

    return (
        <div className="flex h-full flex-col">
            {/* 툴바 */}
            <div className="flex items-center justify-between border-b bg-surface px-4 py-2">
                <div className="flex items-center gap-2">
                    <button
                        onClick={handleSave}
                        disabled={saving}
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
                </div>
                <div className="flex items-center gap-4">
                    {/* 통계 요약 */}
                    <div className="flex items-center gap-4 text-sm">
                        <span className="text-text-subtle">
                            발송: <span className="font-medium text-text">{settings.statistics.totalSent.toLocaleString()}</span>
                        </span>
                        <span className="text-text-subtle">
                            성공: <span className="font-medium text-green-600">{settings.statistics.totalDelivered.toLocaleString()}</span>
                        </span>
                        <span className="text-text-subtle">
                            잔여: <span className="font-medium text-brand">{settings.statistics.remainingCredits.toLocaleString()}건</span>
                        </span>
                    </div>
                    {message && (
                        <span className={`text-sm ${message.type === "success" ? "text-green-600" : "text-red-600"}`}>
                            {message.text}
                        </span>
                    )}
                </div>
            </div>

            <div className="flex flex-1 overflow-hidden">
                {/* 탭 메뉴 */}
                <div className="w-44 border-r bg-surface-secondary p-2">
                    {tabs.map((tab) => {
                        const Icon = tab.icon;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex w-full items-center gap-2 rounded px-3 py-2.5 text-left text-sm ${
                                    activeTab === tab.id ? "bg-brand text-white" : "hover:bg-surface"
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
                    {/* API 연동 설정 */}
                    {activeTab === "provider" && (
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold">SMS API 연동 설정</h3>

                            {/* 연결 설정 */}
                            <SectionHeader title="API 연결 설정" section="connection" icon={Settings} />
                            {expandedSections.connection && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">서비스 제공업체</label>
                                            <select
                                                value={settings.provider.name}
                                                onChange={(e) => updateProvider({ name: e.target.value })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                <option value="">선택하세요</option>
                                                <option value="coolsms">CoolSMS</option>
                                                <option value="aligo">알리고</option>
                                                <option value="ppurio">뿌리오</option>
                                                <option value="ncloud">네이버 클라우드</option>
                                                <option value="kakao">카카오 알림톡</option>
                                                <option value="custom">직접 입력</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">API URL</label>
                                            <input
                                                type="url"
                                                value={settings.provider.apiUrl}
                                                onChange={(e) => updateProvider({ apiUrl: e.target.value })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                                placeholder="https://api.example.com/sms"
                                            />
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">API Key</label>
                                            <input
                                                type="password"
                                                value={settings.provider.apiKey}
                                                onChange={(e) => updateProvider({ apiKey: e.target.value })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                                placeholder="API 키 입력"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">API Secret</label>
                                            <input
                                                type="password"
                                                value={settings.provider.apiSecret}
                                                onChange={(e) => updateProvider({ apiSecret: e.target.value })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                                placeholder="API Secret 입력"
                                            />
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-6">
                                        <label className="flex items-center gap-2">
                                            <input
                                                type="checkbox"
                                                checked={settings.provider.enabled}
                                                onChange={(e) => updateProvider({ enabled: e.target.checked })}
                                                className="h-4 w-4"
                                            />
                                            <span className="text-sm">SMS 발송 활성화</span>
                                        </label>
                                        <label className="flex items-center gap-2">
                                            <input
                                                type="checkbox"
                                                checked={settings.provider.testMode}
                                                onChange={(e) => updateProvider({ testMode: e.target.checked })}
                                                className="h-4 w-4"
                                            />
                                            <span className="text-sm">테스트 모드 (실제 발송 안함)</span>
                                        </label>
                                    </div>
                                </div>
                            )}

                            {/* 발신번호 설정 */}
                            <SectionHeader title="발신번호 설정" section="sender" icon={Phone} />
                            {expandedSections.sender && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">발신번호 ID</label>
                                        <input
                                            type="text"
                                            value={settings.provider.senderId}
                                            onChange={(e) => updateProvider({ senderId: e.target.value })}
                                            className="w-full rounded border px-3 py-2 text-sm"
                                            placeholder="사전 등록된 발신번호 ID"
                                        />
                                        <p className="mt-1 text-xs text-text-subtle">
                                            발신번호는 통신사에 사전 등록이 필요합니다.
                                        </p>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">등록된 발신번호</label>
                                        <div className="space-y-2">
                                            {settings.senderNumbers.length === 0 ? (
                                                <p className="text-sm text-text-subtle">등록된 발신번호가 없습니다.</p>
                                            ) : (
                                                settings.senderNumbers.map((num, idx) => (
                                                    <div key={idx} className="flex items-center gap-2">
                                                        <input
                                                            type="radio"
                                                            name="defaultSender"
                                                            checked={settings.defaultSenderNumber === num}
                                                            onChange={() => setSettings(prev => ({ ...prev, defaultSenderNumber: num }))}
                                                            className="h-4 w-4"
                                                        />
                                                        <span className="text-sm">{num}</span>
                                                        <button
                                                            onClick={() => {
                                                                setSettings(prev => ({
                                                                    ...prev,
                                                                    senderNumbers: prev.senderNumbers.filter((_, i) => i !== idx),
                                                                }));
                                                            }}
                                                            className="text-red-500 hover:text-red-700"
                                                        >
                                                            <Trash2 className="h-4 w-4" />
                                                        </button>
                                                    </div>
                                                ))
                                            )}
                                        </div>
                                        <div className="mt-2 flex items-center gap-2">
                                            <input
                                                type="tel"
                                                placeholder="02-1234-5678"
                                                className="flex-1 rounded border px-3 py-2 text-sm"
                                                onKeyDown={(e) => {
                                                    if (e.key === "Enter") {
                                                        const input = e.currentTarget;
                                                        if (input.value) {
                                                            setSettings(prev => ({
                                                                ...prev,
                                                                senderNumbers: [...prev.senderNumbers, input.value],
                                                            }));
                                                            input.value = "";
                                                        }
                                                    }
                                                }}
                                            />
                                            <button className="rounded bg-surface-secondary px-3 py-2 text-sm hover:bg-surface">
                                                <Plus className="h-4 w-4" />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* 테스트 발송 */}
                            <SectionHeader title="테스트 발송" section="test" icon={TestTube} />
                            {expandedSections.test && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <div className="flex items-center gap-2">
                                        <input
                                            type="tel"
                                            value={testPhone}
                                            onChange={(e) => setTestPhone(e.target.value)}
                                            className="flex-1 rounded border px-3 py-2 text-sm"
                                            placeholder="테스트 수신 번호 (010-1234-5678)"
                                        />
                                        <button
                                            onClick={handleTestSend}
                                            className="flex items-center gap-1 rounded bg-brand px-4 py-2 text-sm text-white hover:bg-brand-dark"
                                        >
                                            <Send className="h-4 w-4" />
                                            테스트 발송
                                        </button>
                                    </div>
                                    {testResult && (
                                        <div className={`flex items-center gap-2 rounded p-3 ${testResult.success ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
                                            {testResult.success ? <CheckCircle className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                                            {testResult.message}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* 알림 설정 */}
                            <SectionHeader title="알림 설정" section="notifications" icon={Bell} />
                            {expandedSections.notifications && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <label className="flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            checked={settings.notifications.sendFailureAlert}
                                            onChange={(e) => setSettings(prev => ({
                                                ...prev,
                                                notifications: { ...prev.notifications, sendFailureAlert: e.target.checked }
                                            }))}
                                            className="h-4 w-4"
                                        />
                                        <span className="text-sm">발송 실패 시 알림</span>
                                    </label>
                                    {settings.notifications.sendFailureAlert && (
                                        <div className="ml-6">
                                            <input
                                                type="email"
                                                value={settings.notifications.failureAlertEmail}
                                                onChange={(e) => setSettings(prev => ({
                                                    ...prev,
                                                    notifications: { ...prev.notifications, failureAlertEmail: e.target.value }
                                                }))}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                                placeholder="알림 받을 이메일"
                                            />
                                        </div>
                                    )}
                                    <label className="flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            checked={settings.notifications.lowBalanceAlert}
                                            onChange={(e) => setSettings(prev => ({
                                                ...prev,
                                                notifications: { ...prev.notifications, lowBalanceAlert: e.target.checked }
                                            }))}
                                            className="h-4 w-4"
                                        />
                                        <span className="text-sm">잔여 건수 부족 알림</span>
                                    </label>
                                    {settings.notifications.lowBalanceAlert && (
                                        <div className="ml-6 flex items-center gap-2">
                                            <input
                                                type="number"
                                                min="0"
                                                value={settings.notifications.lowBalanceThreshold}
                                                onChange={(e) => setSettings(prev => ({
                                                    ...prev,
                                                    notifications: { ...prev.notifications, lowBalanceThreshold: Number(e.target.value) }
                                                }))}
                                                className="w-24 rounded border px-3 py-2 text-sm"
                                            />
                                            <span className="text-sm">건 이하일 때 알림</span>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {/* 메시지 템플릿 */}
                    {activeTab === "templates" && (
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-semibold">메시지 템플릿</h3>
                                <button
                                    onClick={() => setEditingTemplate({
                                        id: "",
                                        name: "",
                                        category: "custom",
                                        content: "",
                                        variables: [],
                                        isDefault: false,
                                        createdAt: new Date().toISOString(),
                                        updatedAt: new Date().toISOString(),
                                    })}
                                    className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"
                                >
                                    <Plus className="h-4 w-4" />
                                    새 템플릿
                                </button>
                            </div>

                            {/* 템플릿 편집 모달 */}
                            {editingTemplate && (
                                <div className="rounded-lg border bg-surface-secondary p-4 space-y-3">
                                    <h4 className="font-medium">{editingTemplate.id ? "템플릿 수정" : "새 템플릿"}</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">템플릿 이름</label>
                                            <input
                                                type="text"
                                                value={editingTemplate.name}
                                                onChange={(e) => setEditingTemplate({ ...editingTemplate, name: e.target.value })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">분류</label>
                                            <select
                                                value={editingTemplate.category}
                                                onChange={(e) => setEditingTemplate({ ...editingTemplate, category: e.target.value as MessageTemplate["category"] })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                <option value="quote">견적</option>
                                                <option value="invoice">세금계산서</option>
                                                <option value="payment">결제</option>
                                                <option value="reminder">알림</option>
                                                <option value="greeting">인사</option>
                                                <option value="custom">기타</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">메시지 내용</label>
                                        <textarea
                                            value={editingTemplate.content}
                                            onChange={(e) => setEditingTemplate({ ...editingTemplate, content: e.target.value })}
                                            rows={4}
                                            className="w-full rounded border px-3 py-2 text-sm"
                                            placeholder="변수는 {변수명} 형식으로 사용하세요"
                                        />
                                        <p className="mt-1 text-xs text-text-subtle">
                                            사용 가능한 변수: {"{회사명}"}, {"{고객명}"}, {"{금액}"}, {"{마감일}"}, {"{전화번호}"}
                                        </p>
                                    </div>
                                    <div className="flex justify-end gap-2">
                                        <button
                                            onClick={() => setEditingTemplate(null)}
                                            className="rounded border px-4 py-2 text-sm hover:bg-surface"
                                        >
                                            취소
                                        </button>
                                        <button
                                            onClick={() => handleSaveTemplate(editingTemplate)}
                                            className="rounded bg-brand px-4 py-2 text-sm text-white hover:bg-brand-dark"
                                        >
                                            저장
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* 템플릿 목록 */}
                            <div className="grid gap-3">
                                {settings.templates.map((template) => (
                                    <div key={template.id} className="rounded-lg border p-4">
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <h4 className="font-medium">{template.name}</h4>
                                                    <span className="text-xs px-2 py-0.5 rounded bg-surface-secondary">
                                                        {categoryLabels[template.category]}
                                                    </span>
                                                    {template.isDefault && (
                                                        <span className="text-xs px-2 py-0.5 rounded bg-brand/10 text-brand">기본</span>
                                                    )}
                                                </div>
                                                <p className="text-sm text-text-subtle line-clamp-2">{template.content}</p>
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <button
                                                    onClick={() => setEditingTemplate(template)}
                                                    className="p-1.5 rounded hover:bg-surface-secondary"
                                                >
                                                    <Edit2 className="h-4 w-4" />
                                                </button>
                                                <button
                                                    onClick={() => handleSaveTemplate({ ...template, id: "", name: `${template.name} (복사)` })}
                                                    className="p-1.5 rounded hover:bg-surface-secondary"
                                                >
                                                    <Copy className="h-4 w-4" />
                                                </button>
                                                {!template.isDefault && (
                                                    <button
                                                        onClick={() => handleDeleteTemplate(template.id)}
                                                        className="p-1.5 rounded hover:bg-surface-secondary text-red-500"
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* 자동발송 설정 */}
                    {activeTab === "autoSend" && (
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-semibold">자동발송 규칙</h3>
                                <button
                                    onClick={() => setEditingRule({
                                        id: "",
                                        name: "",
                                        event: "quote_created",
                                        enabled: true,
                                        templateId: settings.templates[0]?.id || "",
                                        delay: 0,
                                        delayUnit: "minutes",
                                        conditions: [],
                                        recipientType: "customer",
                                        customRecipients: [],
                                    })}
                                    className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"
                                >
                                    <Plus className="h-4 w-4" />
                                    새 규칙
                                </button>
                            </div>

                            {/* 규칙 편집 모달 */}
                            {editingRule && (
                                <div className="rounded-lg border bg-surface-secondary p-4 space-y-3">
                                    <h4 className="font-medium">{editingRule.id ? "규칙 수정" : "새 규칙"}</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">규칙 이름</label>
                                            <input
                                                type="text"
                                                value={editingRule.name}
                                                onChange={(e) => setEditingRule({ ...editingRule, name: e.target.value })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">트리거 이벤트</label>
                                            <select
                                                value={editingRule.event}
                                                onChange={(e) => setEditingRule({ ...editingRule, event: e.target.value as AutoSendRule["event"] })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                {Object.entries(eventLabels).map(([key, label]) => (
                                                    <option key={key} value={key}>{label}</option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">메시지 템플릿</label>
                                            <select
                                                value={editingRule.templateId}
                                                onChange={(e) => setEditingRule({ ...editingRule, templateId: e.target.value })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                {settings.templates.map((tpl) => (
                                                    <option key={tpl.id} value={tpl.id}>{tpl.name}</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">수신자</label>
                                            <select
                                                value={editingRule.recipientType}
                                                onChange={(e) => setEditingRule({ ...editingRule, recipientType: e.target.value as AutoSendRule["recipientType"] })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                <option value="customer">고객</option>
                                                <option value="manager">담당자</option>
                                                <option value="custom">직접 입력</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm">이벤트 발생 후</span>
                                        <input
                                            type="number"
                                            min="0"
                                            value={editingRule.delay}
                                            onChange={(e) => setEditingRule({ ...editingRule, delay: Number(e.target.value) })}
                                            className="w-20 rounded border px-3 py-2 text-sm"
                                        />
                                        <select
                                            value={editingRule.delayUnit}
                                            onChange={(e) => setEditingRule({ ...editingRule, delayUnit: e.target.value as AutoSendRule["delayUnit"] })}
                                            className="rounded border px-3 py-2 text-sm"
                                        >
                                            <option value="minutes">분</option>
                                            <option value="hours">시간</option>
                                            <option value="days">일</option>
                                        </select>
                                        <span className="text-sm">후 발송</span>
                                    </div>
                                    <label className="flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            checked={editingRule.enabled}
                                            onChange={(e) => setEditingRule({ ...editingRule, enabled: e.target.checked })}
                                            className="h-4 w-4"
                                        />
                                        <span className="text-sm">규칙 활성화</span>
                                    </label>
                                    <div className="flex justify-end gap-2">
                                        <button
                                            onClick={() => setEditingRule(null)}
                                            className="rounded border px-4 py-2 text-sm hover:bg-surface"
                                        >
                                            취소
                                        </button>
                                        <button
                                            onClick={() => handleSaveRule(editingRule)}
                                            className="rounded bg-brand px-4 py-2 text-sm text-white hover:bg-brand-dark"
                                        >
                                            저장
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* 규칙 목록 */}
                            {settings.autoSendRules.length === 0 ? (
                                <div className="rounded-lg border border-dashed p-8 text-center">
                                    <Zap className="h-12 w-12 mx-auto text-text-subtle mb-2" />
                                    <p className="text-text-subtle">자동발송 규칙이 없습니다.</p>
                                    <p className="text-sm text-text-subtle">새 규칙을 추가하여 자동 문자 발송을 설정하세요.</p>
                                </div>
                            ) : (
                                <div className="grid gap-3">
                                    {settings.autoSendRules.map((rule) => (
                                        <div key={rule.id} className="rounded-lg border p-4">
                                            <div className="flex items-start justify-between">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <h4 className="font-medium">{rule.name}</h4>
                                                        <span className={`text-xs px-2 py-0.5 rounded ${rule.enabled ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                                                            {rule.enabled ? "활성" : "비활성"}
                                                        </span>
                                                    </div>
                                                    <p className="text-sm text-text-subtle">
                                                        {eventLabels[rule.event]} → {settings.templates.find(t => t.id === rule.templateId)?.name || "템플릿 없음"}
                                                        {rule.delay > 0 && ` (${rule.delay}${rule.delayUnit === "minutes" ? "분" : rule.delayUnit === "hours" ? "시간" : "일"} 후)`}
                                                    </p>
                                                </div>
                                                <div className="flex items-center gap-1">
                                                    <button
                                                        onClick={() => setSettings(prev => ({
                                                            ...prev,
                                                            autoSendRules: prev.autoSendRules.map(r =>
                                                                r.id === rule.id ? { ...r, enabled: !r.enabled } : r
                                                            ),
                                                        }))}
                                                        className={`p-1.5 rounded ${rule.enabled ? "hover:bg-red-50 text-red-500" : "hover:bg-green-50 text-green-500"}`}
                                                    >
                                                        {rule.enabled ? "비활성화" : "활성화"}
                                                    </button>
                                                    <button
                                                        onClick={() => setEditingRule(rule)}
                                                        className="p-1.5 rounded hover:bg-surface-secondary"
                                                    >
                                                        <Edit2 className="h-4 w-4" />
                                                    </button>
                                                    <button
                                                        onClick={() => handleDeleteRule(rule.id)}
                                                        className="p-1.5 rounded hover:bg-surface-secondary text-red-500"
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* 발송 제한 설정 */}
                    {activeTab === "limits" && (
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold">발송 제한 설정</h3>

                            <SectionHeader title="발송 한도" section="limits" icon={Clock} />
                            {expandedSections.limits && (
                                <div className="ml-6 space-y-4 border-l-2 border-brand/20 pl-4">
                                    <div className="grid grid-cols-3 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">일일 발송 한도</label>
                                            <input
                                                type="number"
                                                min="0"
                                                value={settings.sendingLimits.dailyLimit}
                                                onChange={(e) => setSettings(prev => ({
                                                    ...prev,
                                                    sendingLimits: { ...prev.sendingLimits, dailyLimit: Number(e.target.value) }
                                                }))}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">시간당 발송 한도</label>
                                            <input
                                                type="number"
                                                min="0"
                                                value={settings.sendingLimits.hourlyLimit}
                                                onChange={(e) => setSettings(prev => ({
                                                    ...prev,
                                                    sendingLimits: { ...prev.sendingLimits, hourlyLimit: Number(e.target.value) }
                                                }))}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">고객당 일일 한도</label>
                                            <input
                                                type="number"
                                                min="0"
                                                value={settings.sendingLimits.perCustomerDaily}
                                                onChange={(e) => setSettings(prev => ({
                                                    ...prev,
                                                    sendingLimits: { ...prev.sendingLimits, perCustomerDaily: Number(e.target.value) }
                                                }))}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            />
                                        </div>
                                    </div>
                                    <label className="flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            checked={settings.sendingLimits.blockDuplicates}
                                            onChange={(e) => setSettings(prev => ({
                                                ...prev,
                                                sendingLimits: { ...prev.sendingLimits, blockDuplicates: e.target.checked }
                                            }))}
                                            className="h-4 w-4"
                                        />
                                        <span className="text-sm">중복 메시지 발송 차단</span>
                                    </label>
                                    {settings.sendingLimits.blockDuplicates && (
                                        <div className="ml-6 flex items-center gap-2">
                                            <span className="text-sm">같은 내용 메시지</span>
                                            <input
                                                type="number"
                                                min="1"
                                                value={settings.sendingLimits.duplicateCheckPeriod}
                                                onChange={(e) => setSettings(prev => ({
                                                    ...prev,
                                                    sendingLimits: { ...prev.sendingLimits, duplicateCheckPeriod: Number(e.target.value) }
                                                }))}
                                                className="w-20 rounded border px-3 py-2 text-sm"
                                            />
                                            <span className="text-sm">분 이내 재발송 차단</span>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* 발송 금지 시간대 */}
                            <div className="rounded-lg bg-yellow-50 p-4">
                                <h4 className="font-medium text-yellow-800 mb-2">발송 금지 시간대 안내</h4>
                                <p className="text-sm text-yellow-700">
                                    관련 법규에 따라 야간 시간대(21:00 ~ 08:00) 광고성 문자 발송이 제한됩니다.
                                    단, 업무 관련 메시지(견적서 안내, 입금 확인 등)는 예외입니다.
                                </p>
                            </div>
                        </div>
                    )}

                    {/* 발송 이력 */}
                    {activeTab === "logs" && (
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-semibold">발송 이력</h3>
                                <div className="flex items-center gap-2">
                                    <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary">
                                        <BarChart3 className="h-4 w-4" />
                                        통계 보기
                                    </button>
                                </div>
                            </div>

                            {/* 통계 카드 */}
                            <div className="grid grid-cols-4 gap-4">
                                <div className="rounded-lg border p-4">
                                    <p className="text-sm text-text-subtle">총 발송</p>
                                    <p className="text-2xl font-bold">{settings.statistics.totalSent.toLocaleString()}</p>
                                </div>
                                <div className="rounded-lg border p-4">
                                    <p className="text-sm text-text-subtle">성공</p>
                                    <p className="text-2xl font-bold text-green-600">{settings.statistics.totalDelivered.toLocaleString()}</p>
                                </div>
                                <div className="rounded-lg border p-4">
                                    <p className="text-sm text-text-subtle">실패</p>
                                    <p className="text-2xl font-bold text-red-600">{settings.statistics.totalFailed.toLocaleString()}</p>
                                </div>
                                <div className="rounded-lg border p-4">
                                    <p className="text-sm text-text-subtle">이번 달</p>
                                    <p className="text-2xl font-bold">{settings.statistics.monthlyUsage.toLocaleString()}</p>
                                </div>
                            </div>

                            {/* 로그 테이블 */}
                            {settings.recentLogs.length === 0 ? (
                                <div className="rounded-lg border border-dashed p-8 text-center">
                                    <History className="h-12 w-12 mx-auto text-text-subtle mb-2" />
                                    <p className="text-text-subtle">발송 이력이 없습니다.</p>
                                </div>
                            ) : (
                                <div className="rounded-lg border overflow-hidden">
                                    <table className="w-full text-sm">
                                        <thead className="bg-surface-secondary">
                                            <tr>
                                                <th className="px-4 py-2 text-left">발송 시간</th>
                                                <th className="px-4 py-2 text-left">수신번호</th>
                                                <th className="px-4 py-2 text-left">내용</th>
                                                <th className="px-4 py-2 text-left">상태</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {settings.recentLogs.map((log) => (
                                                <tr key={log.id} className="border-t">
                                                    <td className="px-4 py-2">{new Date(log.timestamp).toLocaleString()}</td>
                                                    <td className="px-4 py-2">{log.recipient}</td>
                                                    <td className="px-4 py-2 max-w-xs truncate">{log.content}</td>
                                                    <td className="px-4 py-2">
                                                        <span className={`px-2 py-0.5 rounded text-xs ${
                                                            log.status === "delivered" ? "bg-green-100 text-green-700" :
                                                            log.status === "sent" ? "bg-blue-100 text-blue-700" :
                                                            log.status === "failed" ? "bg-red-100 text-red-700" :
                                                            "bg-gray-100 text-gray-700"
                                                        }`}>
                                                            {log.status === "delivered" ? "전송완료" :
                                                             log.status === "sent" ? "발송" :
                                                             log.status === "failed" ? "실패" : "대기"}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default SMSSettingsWindow;
