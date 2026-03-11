"use client";

import React, { useState, useEffect } from "react";
import DOMPurify from "dompurify";
import {
    Mail,
    Server,
    FileText,
    Paperclip,
    PenTool,
    Clock,
    CheckCircle,
    Plus,
    Trash2,
    Edit,
    Copy,
    Send,
    Eye,
    RefreshCw,
    Download,
    Upload,
    Settings,
    Shield,
    Bell,
    Users,
    Folder,
    Search,
    Filter,
    MoreVertical,
    Check,
    X,
    AlertTriangle,
    Info,
    Lock,
    Unlock,
    Calendar,
    List,
    Grid,
    ChevronDown,
    ChevronRight,
    ExternalLink,
    Link,
    Image,
    Type,
    Bold,
    Italic,
    Underline,
    AlignLeft,
    AlignCenter,
    AlignRight,
    Table,
} from "lucide-react";

// ===== 인터페이스 정의 =====
interface SMTPSettings {
    id: string;
    name: string;
    host: string;
    port: number;
    encryption: "none" | "ssl" | "tls" | "starttls";
    username: string;
    password: string;
    fromEmail: string;
    fromName: string;
    replyTo: string;
    isDefault: boolean;
    isActive: boolean;
    timeout: number;
    maxRetries: number;
    dailyLimit: number;
    testResult?: {
        success: boolean;
        message: string;
        testedAt: string;
    };
}

interface EmailTemplate {
    id: string;
    name: string;
    category: "quotation" | "invoice" | "payment" | "reminder" | "notice" | "marketing" | "custom";
    subject: string;
    body: string;
    isHtml: boolean;
    variables: string[];
    attachments: string[];
    isDefault: boolean;
    isActive: boolean;
    createdAt: string;
    updatedAt: string;
}

interface AttachmentRule {
    id: string;
    name: string;
    documentType: string;
    autoAttach: boolean;
    maxSize: number;
    allowedFormats: string[];
    compressPdf: boolean;
    watermark: boolean;
    passwordProtect: boolean;
}

interface EmailSignature {
    id: string;
    name: string;
    content: string;
    isHtml: boolean;
    includeLogo: boolean;
    logoUrl: string;
    includeContact: boolean;
    isDefault: boolean;
    isActive: boolean;
}

interface ScheduledEmail {
    id: string;
    templateId: string;
    recipients: string[];
    subject: string;
    scheduledAt: string;
    status: "pending" | "sent" | "failed" | "cancelled";
    createdAt: string;
    sentAt?: string;
    errorMessage?: string;
}

interface EmailHistory {
    id: string;
    recipient: string;
    subject: string;
    templateName: string;
    status: "sent" | "delivered" | "opened" | "clicked" | "bounced" | "failed";
    sentAt: string;
    openedAt?: string;
    clickedAt?: string;
    attachments: string[];
}

interface EmailSettingsData {
    smtpServers: SMTPSettings[];
    templates: EmailTemplate[];
    attachmentRules: AttachmentRule[];
    signatures: EmailSignature[];
    scheduledEmails: ScheduledEmail[];
    history: EmailHistory[];
    general: {
        trackOpens: boolean;
        trackClicks: boolean;
        unsubscribeLink: boolean;
        bccAdmin: boolean;
        adminEmail: string;
        defaultReplyDays: number;
        autoResend: boolean;
        resendAfterDays: number;
    };
}

// ===== 기본 데이터 =====
const defaultSettings: EmailSettingsData = {
    smtpServers: [
        {
            id: "smtp_1",
            name: "기본 메일서버",
            host: "smtp.example.com",
            port: 587,
            encryption: "tls",
            username: "user@example.com",
            password: "",
            fromEmail: "noreply@company.com",
            fromName: "(주)한국산업",
            replyTo: "support@company.com",
            isDefault: true,
            isActive: true,
            timeout: 30,
            maxRetries: 3,
            dailyLimit: 500,
        },
    ],
    templates: [
        {
            id: "tpl_1",
            name: "견적서 발송",
            category: "quotation",
            subject: "[{company}] 견적서를 보내드립니다 - {quotationNo}",
            body: "<p>안녕하세요, {customerName}님</p><p>요청하신 견적서를 첨부파일로 보내드립니다.</p><p>문의사항이 있으시면 언제든 연락주세요.</p><p>감사합니다.</p>",
            isHtml: true,
            variables: ["company", "quotationNo", "customerName", "amount", "validDate"],
            attachments: ["견적서.pdf"],
            isDefault: true,
            isActive: true,
            createdAt: "2024-01-01",
            updatedAt: "2024-01-01",
        },
        {
            id: "tpl_2",
            name: "세금계산서 발송",
            category: "invoice",
            subject: "[{company}] 세금계산서 발행 안내 - {invoiceNo}",
            body: "<p>안녕하세요, {customerName}님</p><p>세금계산서가 발행되었습니다.</p><p>첨부파일을 확인해주세요.</p>",
            isHtml: true,
            variables: ["company", "invoiceNo", "customerName", "amount", "issueDate"],
            attachments: ["세금계산서.pdf"],
            isDefault: false,
            isActive: true,
            createdAt: "2024-01-01",
            updatedAt: "2024-01-01",
        },
        {
            id: "tpl_3",
            name: "결제 요청",
            category: "payment",
            subject: "[{company}] 결제 요청 안내",
            body: "<p>안녕하세요, {customerName}님</p><p>미수금 결제를 요청드립니다.</p><p>금액: {amount}원</p><p>입금계좌: {bankAccount}</p>",
            isHtml: true,
            variables: ["company", "customerName", "amount", "bankAccount", "dueDate"],
            attachments: [],
            isDefault: false,
            isActive: true,
            createdAt: "2024-01-01",
            updatedAt: "2024-01-01",
        },
    ],
    attachmentRules: [
        {
            id: "att_1",
            name: "견적서 첨부 규칙",
            documentType: "quotation",
            autoAttach: true,
            maxSize: 10,
            allowedFormats: ["pdf", "xlsx"],
            compressPdf: true,
            watermark: false,
            passwordProtect: false,
        },
        {
            id: "att_2",
            name: "세금계산서 첨부 규칙",
            documentType: "invoice",
            autoAttach: true,
            maxSize: 5,
            allowedFormats: ["pdf"],
            compressPdf: false,
            watermark: true,
            passwordProtect: true,
        },
    ],
    signatures: [
        {
            id: "sig_1",
            name: "기본 서명",
            content: "<p><strong>{userName}</strong></p><p>{position} | {department}</p><p>Tel: {phone} | Email: {email}</p><p>{company}</p>",
            isHtml: true,
            includeLogo: true,
            logoUrl: "/logo.png",
            includeContact: true,
            isDefault: true,
            isActive: true,
        },
    ],
    scheduledEmails: [],
    history: [],
    general: {
        trackOpens: true,
        trackClicks: true,
        unsubscribeLink: true,
        bccAdmin: false,
        adminEmail: "admin@company.com",
        defaultReplyDays: 7,
        autoResend: false,
        resendAfterDays: 3,
    },
};

// ===== 메인 컴포넌트 =====
export function EmailSettingsWindow() {
    const [activeTab, setActiveTab] = useState("smtp");
    const [settings, setSettings] = useState<EmailSettingsData>(defaultSettings);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: "success" | "error" | "info"; text: string } | null>(null);

    // 설정 로드
    useEffect(() => {
        const saved = localStorage.getItem("erp_email_settings");
        if (saved) {
            try {
                setSettings(JSON.parse(saved));
            } catch (e) {
                console.error("이메일 설정 로드 실패:", e);
            }
        }
    }, []);

    // 설정 저장
    const handleSave = async () => {
        setSaving(true);
        try {
            localStorage.setItem("erp_email_settings", JSON.stringify(settings));
            window.dispatchEvent(new CustomEvent("kis-erp-settings-updated"));
            setMessage({ type: "success", text: "이메일 설정이 저장되었습니다." });
            setTimeout(() => setMessage(null), 3000);
        } catch (error) {
            setMessage({ type: "error", text: "설정 저장에 실패했습니다." });
        } finally {
            setSaving(false);
        }
    };

    const tabs = [
        { id: "smtp", label: "SMTP 서버", icon: Server },
        { id: "templates", label: "메일 템플릿", icon: FileText },
        { id: "attachments", label: "첨부파일 설정", icon: Paperclip },
        { id: "signatures", label: "서명 관리", icon: PenTool },
        { id: "scheduled", label: "예약 발송", icon: Clock },
        { id: "tracking", label: "수신 확인", icon: CheckCircle },
        { id: "history", label: "발송 이력", icon: List },
        { id: "general", label: "일반 설정", icon: Settings },
    ];

    return (
        <div className="flex h-full flex-col bg-white">
            {/* 상단 툴바 */}
            <div className="flex items-center justify-between border-b bg-gray-50 px-4 py-2">
                <div className="flex items-center gap-2">
                    <Mail className="h-5 w-5 text-blue-600" />
                    <span className="font-medium">이메일 설정</span>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center gap-1 rounded bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
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
                                        ? "bg-blue-600 text-white"
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
                    {activeTab === "smtp" && (
                        <SMTPServerTab settings={settings} setSettings={setSettings} setMessage={setMessage} />
                    )}
                    {activeTab === "templates" && (
                        <TemplatesTab settings={settings} setSettings={setSettings} />
                    )}
                    {activeTab === "attachments" && (
                        <AttachmentsTab settings={settings} setSettings={setSettings} />
                    )}
                    {activeTab === "signatures" && (
                        <SignaturesTab settings={settings} setSettings={setSettings} />
                    )}
                    {activeTab === "scheduled" && (
                        <ScheduledTab settings={settings} setSettings={setSettings} />
                    )}
                    {activeTab === "tracking" && (
                        <TrackingTab settings={settings} setSettings={setSettings} />
                    )}
                    {activeTab === "history" && (
                        <HistoryTab settings={settings} />
                    )}
                    {activeTab === "general" && (
                        <GeneralTab settings={settings} setSettings={setSettings} />
                    )}
                </div>
            </div>
        </div>
    );
}

// ===== SMTP 서버 탭 =====
function SMTPServerTab({
    settings,
    setSettings,
    setMessage,
}: {
    settings: EmailSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<EmailSettingsData>>;
    setMessage: React.Dispatch<React.SetStateAction<{ type: "success" | "error" | "info"; text: string } | null>>;
}) {
    const [selectedServer, setSelectedServer] = useState<SMTPSettings | null>(
        settings.smtpServers[0] || null
    );
    const [testing, setTesting] = useState(false);

    const handleAddServer = () => {
        const newServer: SMTPSettings = {
            id: `smtp_${Date.now()}`,
            name: "새 메일서버",
            host: "",
            port: 587,
            encryption: "tls",
            username: "",
            password: "",
            fromEmail: "",
            fromName: "",
            replyTo: "",
            isDefault: settings.smtpServers.length === 0,
            isActive: true,
            timeout: 30,
            maxRetries: 3,
            dailyLimit: 500,
        };
        setSettings({
            ...settings,
            smtpServers: [...settings.smtpServers, newServer],
        });
        setSelectedServer(newServer);
    };

    const handleDeleteServer = (id: string) => {
        if (confirm("이 SMTP 서버를 삭제하시겠습니까?")) {
            setSettings({
                ...settings,
                smtpServers: settings.smtpServers.filter((s) => s.id !== id),
            });
            setSelectedServer(settings.smtpServers[0] || null);
        }
    };

    const handleTestConnection = async () => {
        if (!selectedServer) return;
        setTesting(true);
        // 실제로는 백엔드 API를 호출해야 함
        setTimeout(() => {
            const success = Boolean(selectedServer.host && selectedServer.username);
            setSettings({
                ...settings,
                smtpServers: settings.smtpServers.map((s) =>
                    s.id === selectedServer.id
                        ? {
                              ...s,
                              testResult: {
                                  success,
                                  message: success ? "연결 성공" : "연결 실패: 서버 정보를 확인하세요",
                                  testedAt: new Date().toISOString(),
                              },
                          }
                        : s
                ),
            });
            setMessage({
                type: success ? "success" : "error",
                text: success ? "SMTP 연결 테스트 성공" : "SMTP 연결 테스트 실패",
            });
            setTesting(false);
        }, 2000);
    };

    const updateServer = (updates: Partial<SMTPSettings>) => {
        if (!selectedServer) return;
        const updated = { ...selectedServer, ...updates };
        setSelectedServer(updated);
        setSettings({
            ...settings,
            smtpServers: settings.smtpServers.map((s) =>
                s.id === selectedServer.id ? updated : s
            ),
        });
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">SMTP 서버 관리</h3>
                <button
                    onClick={handleAddServer}
                    className="flex items-center gap-1 rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700"
                >
                    <Plus className="h-4 w-4" />
                    서버 추가
                </button>
            </div>

            <div className="grid grid-cols-3 gap-4">
                {/* 서버 목록 */}
                <div className="col-span-1 rounded border">
                    <div className="border-b bg-gray-50 px-3 py-2 text-sm font-medium">
                        서버 목록 ({settings.smtpServers.length})
                    </div>
                    <div className="max-h-96 overflow-auto">
                        {settings.smtpServers.map((server) => (
                            <div
                                key={server.id}
                                onClick={() => setSelectedServer(server)}
                                className={`flex cursor-pointer items-center justify-between border-b px-3 py-2 hover:bg-gray-50 ${
                                    selectedServer?.id === server.id ? "bg-blue-50" : ""
                                }`}
                            >
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm font-medium">{server.name}</span>
                                        {server.isDefault && (
                                            <span className="rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700">
                                                기본
                                            </span>
                                        )}
                                    </div>
                                    <div className="text-xs text-gray-500">{server.host}</div>
                                </div>
                                <div className="flex items-center gap-1">
                                    {server.isActive ? (
                                        <span className="h-2 w-2 rounded-full bg-green-500"></span>
                                    ) : (
                                        <span className="h-2 w-2 rounded-full bg-gray-300"></span>
                                    )}
                                </div>
                            </div>
                        ))}
                        {settings.smtpServers.length === 0 && (
                            <div className="p-4 text-center text-sm text-gray-500">
                                등록된 서버가 없습니다
                            </div>
                        )}
                    </div>
                </div>

                {/* 서버 상세 설정 */}
                <div className="col-span-2 rounded border">
                    {selectedServer ? (
                        <div className="p-4">
                            <div className="mb-4 flex items-center justify-between">
                                <h4 className="font-medium">서버 설정</h4>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={handleTestConnection}
                                        disabled={testing}
                                        className="flex items-center gap-1 rounded border px-3 py-1 text-sm hover:bg-gray-50"
                                    >
                                        {testing ? (
                                            <RefreshCw className="h-4 w-4 animate-spin" />
                                        ) : (
                                            <Send className="h-4 w-4" />
                                        )}
                                        연결 테스트
                                    </button>
                                    <button
                                        onClick={() => handleDeleteServer(selectedServer.id)}
                                        className="flex items-center gap-1 rounded border border-red-200 px-3 py-1 text-sm text-red-600 hover:bg-red-50"
                                    >
                                        <Trash2 className="h-4 w-4" />
                                        삭제
                                    </button>
                                </div>
                            </div>

                            {/* 테스트 결과 */}
                            {selectedServer.testResult && (
                                <div
                                    className={`mb-4 flex items-center gap-2 rounded px-3 py-2 text-sm ${
                                        selectedServer.testResult.success
                                            ? "bg-green-50 text-green-700"
                                            : "bg-red-50 text-red-700"
                                    }`}
                                >
                                    {selectedServer.testResult.success ? (
                                        <Check className="h-4 w-4" />
                                    ) : (
                                        <X className="h-4 w-4" />
                                    )}
                                    {selectedServer.testResult.message}
                                    <span className="text-xs opacity-70">
                                        ({new Date(selectedServer.testResult.testedAt).toLocaleString()})
                                    </span>
                                </div>
                            )}

                            <div className="grid grid-cols-2 gap-4">
                                {/* 기본 정보 */}
                                <div className="space-y-3">
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">서버 이름</label>
                                        <input
                                            type="text"
                                            value={selectedServer.name}
                                            onChange={(e) => updateServer({ name: e.target.value })}
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">SMTP 호스트</label>
                                        <input
                                            type="text"
                                            value={selectedServer.host}
                                            onChange={(e) => updateServer({ host: e.target.value })}
                                            placeholder="smtp.example.com"
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        />
                                    </div>
                                    <div className="grid grid-cols-2 gap-2">
                                        <div>
                                            <label className="mb-1 block text-sm font-medium">포트</label>
                                            <input
                                                type="number"
                                                value={selectedServer.port}
                                                onChange={(e) => updateServer({ port: Number(e.target.value) })}
                                                className="w-full rounded border px-3 py-1.5 text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="mb-1 block text-sm font-medium">암호화</label>
                                            <select
                                                value={selectedServer.encryption}
                                                onChange={(e) =>
                                                    updateServer({
                                                        encryption: e.target.value as SMTPSettings["encryption"],
                                                    })
                                                }
                                                className="w-full rounded border px-3 py-1.5 text-sm"
                                            >
                                                <option value="none">없음</option>
                                                <option value="ssl">SSL</option>
                                                <option value="tls">TLS</option>
                                                <option value="starttls">STARTTLS</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">사용자명</label>
                                        <input
                                            type="text"
                                            value={selectedServer.username}
                                            onChange={(e) => updateServer({ username: e.target.value })}
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">비밀번호</label>
                                        <input
                                            type="password"
                                            value={selectedServer.password}
                                            onChange={(e) => updateServer({ password: e.target.value })}
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        />
                                    </div>
                                </div>

                                {/* 발신 정보 */}
                                <div className="space-y-3">
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">발신 이메일</label>
                                        <input
                                            type="email"
                                            value={selectedServer.fromEmail}
                                            onChange={(e) => updateServer({ fromEmail: e.target.value })}
                                            placeholder="noreply@company.com"
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">발신자 이름</label>
                                        <input
                                            type="text"
                                            value={selectedServer.fromName}
                                            onChange={(e) => updateServer({ fromName: e.target.value })}
                                            placeholder="(주)한국산업"
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">회신 주소</label>
                                        <input
                                            type="email"
                                            value={selectedServer.replyTo}
                                            onChange={(e) => updateServer({ replyTo: e.target.value })}
                                            placeholder="support@company.com"
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        />
                                    </div>
                                    <div className="grid grid-cols-2 gap-2">
                                        <div>
                                            <label className="mb-1 block text-sm font-medium">타임아웃 (초)</label>
                                            <input
                                                type="number"
                                                value={selectedServer.timeout}
                                                onChange={(e) => updateServer({ timeout: Number(e.target.value) })}
                                                className="w-full rounded border px-3 py-1.5 text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="mb-1 block text-sm font-medium">재시도 횟수</label>
                                            <input
                                                type="number"
                                                value={selectedServer.maxRetries}
                                                onChange={(e) => updateServer({ maxRetries: Number(e.target.value) })}
                                                className="w-full rounded border px-3 py-1.5 text-sm"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">일일 발송 제한</label>
                                        <input
                                            type="number"
                                            value={selectedServer.dailyLimit}
                                            onChange={(e) => updateServer({ dailyLimit: Number(e.target.value) })}
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        />
                                    </div>
                                    <div className="flex items-center gap-4 pt-2">
                                        <label className="flex items-center gap-2 text-sm">
                                            <input
                                                type="checkbox"
                                                checked={selectedServer.isDefault}
                                                onChange={(e) => {
                                                    if (e.target.checked) {
                                                        setSettings({
                                                            ...settings,
                                                            smtpServers: settings.smtpServers.map((s) => ({
                                                                ...s,
                                                                isDefault: s.id === selectedServer.id,
                                                            })),
                                                        });
                                                    }
                                                    updateServer({ isDefault: e.target.checked });
                                                }}
                                                className="h-4 w-4"
                                            />
                                            기본 서버로 설정
                                        </label>
                                        <label className="flex items-center gap-2 text-sm">
                                            <input
                                                type="checkbox"
                                                checked={selectedServer.isActive}
                                                onChange={(e) => updateServer({ isActive: e.target.checked })}
                                                className="h-4 w-4"
                                            />
                                            활성화
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex h-full items-center justify-center p-8 text-gray-500">
                            서버를 선택하거나 새로 추가하세요
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// ===== 템플릿 탭 =====
function TemplatesTab({
    settings,
    setSettings,
}: {
    settings: EmailSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<EmailSettingsData>>;
}) {
    const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(
        settings.templates[0] || null
    );
    const [filterCategory, setFilterCategory] = useState<string>("all");
    const [showPreview, setShowPreview] = useState(false);

    const categories = [
        { id: "all", name: "전체" },
        { id: "quotation", name: "견적서" },
        { id: "invoice", name: "세금계산서" },
        { id: "payment", name: "결제" },
        { id: "reminder", name: "알림" },
        { id: "notice", name: "공지" },
        { id: "marketing", name: "마케팅" },
        { id: "custom", name: "사용자 정의" },
    ];

    const filteredTemplates =
        filterCategory === "all"
            ? settings.templates
            : settings.templates.filter((t) => t.category === filterCategory);

    const handleAddTemplate = () => {
        const newTemplate: EmailTemplate = {
            id: `tpl_${Date.now()}`,
            name: "새 템플릿",
            category: "custom",
            subject: "",
            body: "",
            isHtml: true,
            variables: [],
            attachments: [],
            isDefault: false,
            isActive: true,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
        };
        setSettings({
            ...settings,
            templates: [...settings.templates, newTemplate],
        });
        setSelectedTemplate(newTemplate);
    };

    const handleDeleteTemplate = (id: string) => {
        if (confirm("이 템플릿을 삭제하시겠습니까?")) {
            setSettings({
                ...settings,
                templates: settings.templates.filter((t) => t.id !== id),
            });
            setSelectedTemplate(null);
        }
    };

    const updateTemplate = (updates: Partial<EmailTemplate>) => {
        if (!selectedTemplate) return;
        const updated = { ...selectedTemplate, ...updates, updatedAt: new Date().toISOString() };
        setSelectedTemplate(updated);
        setSettings({
            ...settings,
            templates: settings.templates.map((t) =>
                t.id === selectedTemplate.id ? updated : t
            ),
        });
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">메일 템플릿 관리</h3>
                <div className="flex items-center gap-2">
                    <select
                        value={filterCategory}
                        onChange={(e) => setFilterCategory(e.target.value)}
                        className="rounded border px-3 py-1.5 text-sm"
                    >
                        {categories.map((cat) => (
                            <option key={cat.id} value={cat.id}>
                                {cat.name}
                            </option>
                        ))}
                    </select>
                    <button
                        onClick={handleAddTemplate}
                        className="flex items-center gap-1 rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700"
                    >
                        <Plus className="h-4 w-4" />
                        템플릿 추가
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
                {/* 템플릿 목록 */}
                <div className="col-span-1 rounded border">
                    <div className="border-b bg-gray-50 px-3 py-2 text-sm font-medium">
                        템플릿 목록 ({filteredTemplates.length})
                    </div>
                    <div className="max-h-[500px] overflow-auto">
                        {filteredTemplates.map((template) => (
                            <div
                                key={template.id}
                                onClick={() => setSelectedTemplate(template)}
                                className={`cursor-pointer border-b px-3 py-2 hover:bg-gray-50 ${
                                    selectedTemplate?.id === template.id ? "bg-blue-50" : ""
                                }`}
                            >
                                <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium">{template.name}</span>
                                    {template.isDefault && (
                                        <span className="rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700">
                                            기본
                                        </span>
                                    )}
                                </div>
                                <div className="flex items-center gap-2 text-xs text-gray-500">
                                    <span>
                                        {categories.find((c) => c.id === template.category)?.name}
                                    </span>
                                    {!template.isActive && (
                                        <span className="text-red-500">비활성</span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 템플릿 편집 */}
                <div className="col-span-2 rounded border">
                    {selectedTemplate ? (
                        <div className="p-4">
                            <div className="mb-4 flex items-center justify-between">
                                <h4 className="font-medium">템플릿 편집</h4>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={() => setShowPreview(true)}
                                        className="flex items-center gap-1 rounded border px-3 py-1 text-sm hover:bg-gray-50"
                                    >
                                        <Eye className="h-4 w-4" />
                                        미리보기
                                    </button>
                                    <button
                                        onClick={() => {
                                            const copied = {
                                                ...selectedTemplate,
                                                id: `tpl_${Date.now()}`,
                                                name: `${selectedTemplate.name} (복사본)`,
                                                isDefault: false,
                                            };
                                            setSettings({
                                                ...settings,
                                                templates: [...settings.templates, copied],
                                            });
                                        }}
                                        className="flex items-center gap-1 rounded border px-3 py-1 text-sm hover:bg-gray-50"
                                    >
                                        <Copy className="h-4 w-4" />
                                        복제
                                    </button>
                                    <button
                                        onClick={() => handleDeleteTemplate(selectedTemplate.id)}
                                        className="flex items-center gap-1 rounded border border-red-200 px-3 py-1 text-sm text-red-600 hover:bg-red-50"
                                    >
                                        <Trash2 className="h-4 w-4" />
                                        삭제
                                    </button>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">템플릿 이름</label>
                                        <input
                                            type="text"
                                            value={selectedTemplate.name}
                                            onChange={(e) => updateTemplate({ name: e.target.value })}
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">카테고리</label>
                                        <select
                                            value={selectedTemplate.category}
                                            onChange={(e) =>
                                                updateTemplate({
                                                    category: e.target.value as EmailTemplate["category"],
                                                })
                                            }
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        >
                                            {categories.slice(1).map((cat) => (
                                                <option key={cat.id} value={cat.id}>
                                                    {cat.name}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                <div>
                                    <label className="mb-1 block text-sm font-medium">제목</label>
                                    <input
                                        type="text"
                                        value={selectedTemplate.subject}
                                        onChange={(e) => updateTemplate({ subject: e.target.value })}
                                        placeholder="[{company}] 제목을 입력하세요"
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                    />
                                </div>

                                <div>
                                    <div className="mb-1 flex items-center justify-between">
                                        <label className="text-sm font-medium">본문</label>
                                        <div className="flex items-center gap-2">
                                            <button className="rounded border p-1 hover:bg-gray-100">
                                                <Bold className="h-4 w-4" />
                                            </button>
                                            <button className="rounded border p-1 hover:bg-gray-100">
                                                <Italic className="h-4 w-4" />
                                            </button>
                                            <button className="rounded border p-1 hover:bg-gray-100">
                                                <Underline className="h-4 w-4" />
                                            </button>
                                            <span className="mx-1 text-gray-300">|</span>
                                            <button className="rounded border p-1 hover:bg-gray-100">
                                                <AlignLeft className="h-4 w-4" />
                                            </button>
                                            <button className="rounded border p-1 hover:bg-gray-100">
                                                <AlignCenter className="h-4 w-4" />
                                            </button>
                                            <button className="rounded border p-1 hover:bg-gray-100">
                                                <AlignRight className="h-4 w-4" />
                                            </button>
                                            <span className="mx-1 text-gray-300">|</span>
                                            <button className="rounded border p-1 hover:bg-gray-100">
                                                <Link className="h-4 w-4" />
                                            </button>
                                            <button className="rounded border p-1 hover:bg-gray-100">
                                                <Image className="h-4 w-4" />
                                            </button>
                                            <button className="rounded border p-1 hover:bg-gray-100">
                                                <Table className="h-4 w-4" />
                                            </button>
                                        </div>
                                    </div>
                                    <textarea
                                        value={selectedTemplate.body}
                                        onChange={(e) => updateTemplate({ body: e.target.value })}
                                        rows={10}
                                        className="w-full rounded border px-3 py-2 font-mono text-sm"
                                        placeholder="HTML 또는 텍스트 본문을 입력하세요..."
                                    />
                                </div>

                                <div>
                                    <label className="mb-1 block text-sm font-medium">
                                        사용 가능한 변수
                                    </label>
                                    <div className="flex flex-wrap gap-2">
                                        {selectedTemplate.variables.map((v) => (
                                            <span
                                                key={v}
                                                className="cursor-pointer rounded bg-gray-100 px-2 py-1 text-xs hover:bg-gray-200"
                                                onClick={() => {
                                                    navigator.clipboard.writeText(`{${v}}`);
                                                }}
                                            >
                                                {`{${v}}`}
                                            </span>
                                        ))}
                                        <button
                                            className="flex items-center gap-1 rounded bg-blue-50 px-2 py-1 text-xs text-blue-600 hover:bg-blue-100"
                                            onClick={() => {
                                                const varName = prompt("변수명을 입력하세요:");
                                                if (varName) {
                                                    updateTemplate({
                                                        variables: [...selectedTemplate.variables, varName],
                                                    });
                                                }
                                            }}
                                        >
                                            <Plus className="h-3 w-3" />
                                            변수 추가
                                        </button>
                                    </div>
                                </div>

                                <div className="flex items-center gap-4">
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedTemplate.isHtml}
                                            onChange={(e) => updateTemplate({ isHtml: e.target.checked })}
                                            className="h-4 w-4"
                                        />
                                        HTML 형식
                                    </label>
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedTemplate.isDefault}
                                            onChange={(e) => updateTemplate({ isDefault: e.target.checked })}
                                            className="h-4 w-4"
                                        />
                                        기본 템플릿
                                    </label>
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedTemplate.isActive}
                                            onChange={(e) => updateTemplate({ isActive: e.target.checked })}
                                            className="h-4 w-4"
                                        />
                                        활성화
                                    </label>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex h-full items-center justify-center p-8 text-gray-500">
                            템플릿을 선택하거나 새로 추가하세요
                        </div>
                    )}
                </div>
            </div>

            {/* 미리보기 모달 */}
            {showPreview && selectedTemplate && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                    <div className="max-h-[80vh] w-[600px] overflow-auto rounded-lg bg-white shadow-xl">
                        <div className="flex items-center justify-between border-b bg-gray-50 px-4 py-3">
                            <h3 className="font-medium">이메일 미리보기</h3>
                            <button
                                onClick={() => setShowPreview(false)}
                                className="text-gray-500 hover:text-gray-700"
                            >
                                <X className="h-5 w-5" />
                            </button>
                        </div>
                        <div className="p-4">
                            <div className="mb-4 rounded bg-gray-50 p-3">
                                <div className="mb-2">
                                    <span className="text-xs text-gray-500">제목:</span>
                                    <div className="font-medium">{selectedTemplate.subject}</div>
                                </div>
                                <div className="text-xs text-gray-500">
                                    카테고리: {categories.find((c) => c.id === selectedTemplate.category)?.name}
                                </div>
                            </div>
                            <div className="border rounded p-4">
                                <div className="mb-2 text-xs text-gray-500">본문 미리보기:</div>
                                {selectedTemplate.isHtml ? (
                                    <div
                                        className="prose prose-sm max-w-none"
                                        dangerouslySetInnerHTML={{
                                            __html: DOMPurify.sanitize(selectedTemplate.body, {
                                                ALLOWED_TAGS: ['p', 'br', 'b', 'i', 'u', 'strong', 'em', 'a', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'span', 'div', 'table', 'tr', 'td', 'th', 'thead', 'tbody'],
                                                ALLOWED_ATTR: ['href', 'class', 'style', 'target'],
                                                ALLOW_DATA_ATTR: false
                                            })
                                        }}
                                    />
                                ) : (
                                    <pre className="whitespace-pre-wrap text-sm">{selectedTemplate.body}</pre>
                                )}
                            </div>
                            {selectedTemplate.variables.length > 0 && (
                                <div className="mt-4 rounded bg-yellow-50 p-3">
                                    <div className="mb-1 text-xs font-medium text-yellow-700">사용된 변수:</div>
                                    <div className="flex flex-wrap gap-1">
                                        {selectedTemplate.variables.map((v) => (
                                            <span key={v} className="rounded bg-yellow-200 px-2 py-0.5 text-xs">
                                                {`{${v}}`}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                        <div className="flex justify-end border-t bg-gray-50 px-4 py-3">
                            <button
                                onClick={() => setShowPreview(false)}
                                className="rounded bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700"
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

// ===== 첨부파일 설정 탭 =====
function AttachmentsTab({
    settings,
    setSettings,
}: {
    settings: EmailSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<EmailSettingsData>>;
}) {
    const [selectedRule, setSelectedRule] = useState<AttachmentRule | null>(
        settings.attachmentRules[0] || null
    );

    const documentTypes = [
        { id: "quotation", name: "견적서" },
        { id: "invoice", name: "세금계산서" },
        { id: "order", name: "발주서" },
        { id: "delivery", name: "거래명세서" },
        { id: "receipt", name: "영수증" },
        { id: "report", name: "리포트" },
        { id: "other", name: "기타" },
    ];

    const handleAddRule = () => {
        const newRule: AttachmentRule = {
            id: `att_${Date.now()}`,
            name: "새 첨부 규칙",
            documentType: "other",
            autoAttach: true,
            maxSize: 10,
            allowedFormats: ["pdf"],
            compressPdf: false,
            watermark: false,
            passwordProtect: false,
        };
        setSettings({
            ...settings,
            attachmentRules: [...settings.attachmentRules, newRule],
        });
        setSelectedRule(newRule);
    };

    const updateRule = (updates: Partial<AttachmentRule>) => {
        if (!selectedRule) return;
        const updated = { ...selectedRule, ...updates };
        setSelectedRule(updated);
        setSettings({
            ...settings,
            attachmentRules: settings.attachmentRules.map((r) =>
                r.id === selectedRule.id ? updated : r
            ),
        });
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">첨부파일 설정</h3>
                <button
                    onClick={handleAddRule}
                    className="flex items-center gap-1 rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700"
                >
                    <Plus className="h-4 w-4" />
                    규칙 추가
                </button>
            </div>

            <div className="grid grid-cols-3 gap-4">
                {/* 규칙 목록 */}
                <div className="col-span-1 rounded border">
                    <div className="border-b bg-gray-50 px-3 py-2 text-sm font-medium">
                        첨부 규칙 ({settings.attachmentRules.length})
                    </div>
                    <div className="max-h-96 overflow-auto">
                        {settings.attachmentRules.map((rule) => (
                            <div
                                key={rule.id}
                                onClick={() => setSelectedRule(rule)}
                                className={`cursor-pointer border-b px-3 py-2 hover:bg-gray-50 ${
                                    selectedRule?.id === rule.id ? "bg-blue-50" : ""
                                }`}
                            >
                                <div className="text-sm font-medium">{rule.name}</div>
                                <div className="text-xs text-gray-500">
                                    {documentTypes.find((d) => d.id === rule.documentType)?.name}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 규칙 설정 */}
                <div className="col-span-2 rounded border p-4">
                    {selectedRule ? (
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="mb-1 block text-sm font-medium">규칙 이름</label>
                                    <input
                                        type="text"
                                        value={selectedRule.name}
                                        onChange={(e) => updateRule({ name: e.target.value })}
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium">문서 유형</label>
                                    <select
                                        value={selectedRule.documentType}
                                        onChange={(e) => updateRule({ documentType: e.target.value })}
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                    >
                                        {documentTypes.map((type) => (
                                            <option key={type.id} value={type.id}>
                                                {type.name}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="mb-1 block text-sm font-medium">최대 파일 크기 (MB)</label>
                                <input
                                    type="number"
                                    value={selectedRule.maxSize}
                                    onChange={(e) => updateRule({ maxSize: Number(e.target.value) })}
                                    className="w-32 rounded border px-3 py-1.5 text-sm"
                                />
                            </div>

                            <div>
                                <label className="mb-1 block text-sm font-medium">허용 파일 형식</label>
                                <div className="flex flex-wrap gap-2">
                                    {["pdf", "xlsx", "docx", "jpg", "png", "zip"].map((format) => (
                                        <label key={format} className="flex items-center gap-1 text-sm">
                                            <input
                                                type="checkbox"
                                                checked={selectedRule.allowedFormats.includes(format)}
                                                onChange={(e) => {
                                                    if (e.target.checked) {
                                                        updateRule({
                                                            allowedFormats: [...selectedRule.allowedFormats, format],
                                                        });
                                                    } else {
                                                        updateRule({
                                                            allowedFormats: selectedRule.allowedFormats.filter(
                                                                (f) => f !== format
                                                            ),
                                                        });
                                                    }
                                                }}
                                                className="h-4 w-4"
                                            />
                                            {format.toUpperCase()}
                                        </label>
                                    ))}
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedRule.autoAttach}
                                            onChange={(e) => updateRule({ autoAttach: e.target.checked })}
                                            className="h-4 w-4"
                                        />
                                        자동 첨부
                                    </label>
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedRule.compressPdf}
                                            onChange={(e) => updateRule({ compressPdf: e.target.checked })}
                                            className="h-4 w-4"
                                        />
                                        PDF 압축
                                    </label>
                                </div>
                                <div className="space-y-2">
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedRule.watermark}
                                            onChange={(e) => updateRule({ watermark: e.target.checked })}
                                            className="h-4 w-4"
                                        />
                                        워터마크 추가
                                    </label>
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedRule.passwordProtect}
                                            onChange={(e) => updateRule({ passwordProtect: e.target.checked })}
                                            className="h-4 w-4"
                                        />
                                        암호 보호
                                    </label>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex h-full items-center justify-center text-gray-500">
                            규칙을 선택하거나 새로 추가하세요
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// ===== 서명 관리 탭 =====
function SignaturesTab({
    settings,
    setSettings,
}: {
    settings: EmailSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<EmailSettingsData>>;
}) {
    const [selectedSignature, setSelectedSignature] = useState<EmailSignature | null>(
        settings.signatures[0] || null
    );

    const handleAddSignature = () => {
        const newSignature: EmailSignature = {
            id: `sig_${Date.now()}`,
            name: "새 서명",
            content: "",
            isHtml: true,
            includeLogo: false,
            logoUrl: "",
            includeContact: true,
            isDefault: false,
            isActive: true,
        };
        setSettings({
            ...settings,
            signatures: [...settings.signatures, newSignature],
        });
        setSelectedSignature(newSignature);
    };

    const updateSignature = (updates: Partial<EmailSignature>) => {
        if (!selectedSignature) return;
        const updated = { ...selectedSignature, ...updates };
        setSelectedSignature(updated);
        setSettings({
            ...settings,
            signatures: settings.signatures.map((s) =>
                s.id === selectedSignature.id ? updated : s
            ),
        });
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">서명 관리</h3>
                <button
                    onClick={handleAddSignature}
                    className="flex items-center gap-1 rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700"
                >
                    <Plus className="h-4 w-4" />
                    서명 추가
                </button>
            </div>

            <div className="grid grid-cols-3 gap-4">
                {/* 서명 목록 */}
                <div className="col-span-1 rounded border">
                    <div className="border-b bg-gray-50 px-3 py-2 text-sm font-medium">
                        서명 목록 ({settings.signatures.length})
                    </div>
                    <div className="max-h-96 overflow-auto">
                        {settings.signatures.map((sig) => (
                            <div
                                key={sig.id}
                                onClick={() => setSelectedSignature(sig)}
                                className={`cursor-pointer border-b px-3 py-2 hover:bg-gray-50 ${
                                    selectedSignature?.id === sig.id ? "bg-blue-50" : ""
                                }`}
                            >
                                <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium">{sig.name}</span>
                                    {sig.isDefault && (
                                        <span className="rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700">
                                            기본
                                        </span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 서명 편집 */}
                <div className="col-span-2 rounded border p-4">
                    {selectedSignature ? (
                        <div className="space-y-4">
                            <div>
                                <label className="mb-1 block text-sm font-medium">서명 이름</label>
                                <input
                                    type="text"
                                    value={selectedSignature.name}
                                    onChange={(e) => updateSignature({ name: e.target.value })}
                                    className="w-full rounded border px-3 py-1.5 text-sm"
                                />
                            </div>

                            <div>
                                <label className="mb-1 block text-sm font-medium">서명 내용</label>
                                <textarea
                                    value={selectedSignature.content}
                                    onChange={(e) => updateSignature({ content: e.target.value })}
                                    rows={8}
                                    className="w-full rounded border px-3 py-2 font-mono text-sm"
                                    placeholder="HTML 또는 텍스트 서명을 입력하세요..."
                                />
                            </div>

                            <div className="rounded bg-gray-50 p-3">
                                <div className="mb-2 text-sm font-medium">사용 가능한 변수</div>
                                <div className="flex flex-wrap gap-2 text-xs">
                                    <span className="rounded bg-gray-200 px-2 py-1">{"{userName}"}</span>
                                    <span className="rounded bg-gray-200 px-2 py-1">{"{position}"}</span>
                                    <span className="rounded bg-gray-200 px-2 py-1">{"{department}"}</span>
                                    <span className="rounded bg-gray-200 px-2 py-1">{"{phone}"}</span>
                                    <span className="rounded bg-gray-200 px-2 py-1">{"{email}"}</span>
                                    <span className="rounded bg-gray-200 px-2 py-1">{"{company}"}</span>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedSignature.isHtml}
                                            onChange={(e) => updateSignature({ isHtml: e.target.checked })}
                                            className="h-4 w-4"
                                        />
                                        HTML 형식
                                    </label>
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedSignature.includeLogo}
                                            onChange={(e) => updateSignature({ includeLogo: e.target.checked })}
                                            className="h-4 w-4"
                                        />
                                        로고 포함
                                    </label>
                                </div>
                                <div className="space-y-2">
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedSignature.includeContact}
                                            onChange={(e) => updateSignature({ includeContact: e.target.checked })}
                                            className="h-4 w-4"
                                        />
                                        연락처 포함
                                    </label>
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedSignature.isDefault}
                                            onChange={(e) => updateSignature({ isDefault: e.target.checked })}
                                            className="h-4 w-4"
                                        />
                                        기본 서명
                                    </label>
                                </div>
                            </div>

                            {selectedSignature.includeLogo && (
                                <div>
                                    <label className="mb-1 block text-sm font-medium">로고 URL</label>
                                    <input
                                        type="text"
                                        value={selectedSignature.logoUrl}
                                        onChange={(e) => updateSignature({ logoUrl: e.target.value })}
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                        placeholder="/logo.png"
                                    />
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="flex h-full items-center justify-center text-gray-500">
                            서명을 선택하거나 새로 추가하세요
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// ===== 예약 발송 탭 =====
function ScheduledTab({
    settings,
    setSettings,
}: {
    settings: EmailSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<EmailSettingsData>>;
}) {
    const [filterStatus, setFilterStatus] = useState<string>("all");

    const statusLabels: Record<string, { label: string; color: string }> = {
        pending: { label: "대기", color: "bg-yellow-100 text-yellow-700" },
        sent: { label: "발송됨", color: "bg-green-100 text-green-700" },
        failed: { label: "실패", color: "bg-red-100 text-red-700" },
        cancelled: { label: "취소됨", color: "bg-gray-100 text-gray-700" },
    };

    const filteredEmails =
        filterStatus === "all"
            ? settings.scheduledEmails
            : settings.scheduledEmails.filter((e) => e.status === filterStatus);

    const handleCancelScheduled = (id: string) => {
        if (confirm("이 예약을 취소하시겠습니까?")) {
            setSettings({
                ...settings,
                scheduledEmails: settings.scheduledEmails.map((e) =>
                    e.id === id ? { ...e, status: "cancelled" as const } : e
                ),
            });
        }
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">예약 발송 관리</h3>
                <div className="flex items-center gap-2">
                    <select
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                        className="rounded border px-3 py-1.5 text-sm"
                    >
                        <option value="all">전체</option>
                        <option value="pending">대기</option>
                        <option value="sent">발송됨</option>
                        <option value="failed">실패</option>
                        <option value="cancelled">취소됨</option>
                    </select>
                    <button className="flex items-center gap-1 rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700">
                        <Plus className="h-4 w-4" />
                        예약 추가
                    </button>
                </div>
            </div>

            <div className="rounded border">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="border-b px-4 py-2 text-left">제목</th>
                            <th className="border-b px-4 py-2 text-left">수신자</th>
                            <th className="border-b px-4 py-2 text-left">예약 시간</th>
                            <th className="border-b px-4 py-2 text-left">상태</th>
                            <th className="border-b px-4 py-2 text-center">관리</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredEmails.length > 0 ? (
                            filteredEmails.map((email) => (
                                <tr key={email.id} className="hover:bg-gray-50">
                                    <td className="border-b px-4 py-2">{email.subject}</td>
                                    <td className="border-b px-4 py-2">
                                        {email.recipients.length}명
                                    </td>
                                    <td className="border-b px-4 py-2">
                                        {new Date(email.scheduledAt).toLocaleString()}
                                    </td>
                                    <td className="border-b px-4 py-2">
                                        <span
                                            className={`rounded px-2 py-0.5 text-xs ${
                                                statusLabels[email.status].color
                                            }`}
                                        >
                                            {statusLabels[email.status].label}
                                        </span>
                                    </td>
                                    <td className="border-b px-4 py-2 text-center">
                                        {email.status === "pending" && (
                                            <button
                                                onClick={() => handleCancelScheduled(email.id)}
                                                className="text-red-600 hover:text-red-800"
                                            >
                                                취소
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                                    예약된 이메일이 없습니다
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

// ===== 수신 확인 탭 =====
function TrackingTab({
    settings,
    setSettings,
}: {
    settings: EmailSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<EmailSettingsData>>;
}) {
    return (
        <div className="space-y-4">
            <h3 className="text-lg font-medium">수신 확인 설정</h3>

            <div className="grid grid-cols-2 gap-6">
                {/* 추적 설정 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">추적 옵션</h4>
                    <div className="space-y-3">
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.general.trackOpens}
                                onChange={(e) =>
                                    setSettings({
                                        ...settings,
                                        general: { ...settings.general, trackOpens: e.target.checked },
                                    })
                                }
                                className="h-4 w-4"
                            />
                            이메일 열람 추적
                            <span className="text-xs text-gray-500">(수신자가 이메일을 열면 기록)</span>
                        </label>
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.general.trackClicks}
                                onChange={(e) =>
                                    setSettings({
                                        ...settings,
                                        general: { ...settings.general, trackClicks: e.target.checked },
                                    })
                                }
                                className="h-4 w-4"
                            />
                            링크 클릭 추적
                            <span className="text-xs text-gray-500">(본문 내 링크 클릭 시 기록)</span>
                        </label>
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.general.unsubscribeLink}
                                onChange={(e) =>
                                    setSettings({
                                        ...settings,
                                        general: { ...settings.general, unsubscribeLink: e.target.checked },
                                    })
                                }
                                className="h-4 w-4"
                            />
                            수신거부 링크 포함
                            <span className="text-xs text-gray-500">(마케팅 이메일에 권장)</span>
                        </label>
                    </div>
                </div>

                {/* 관리자 알림 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">관리자 알림</h4>
                    <div className="space-y-3">
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.general.bccAdmin}
                                onChange={(e) =>
                                    setSettings({
                                        ...settings,
                                        general: { ...settings.general, bccAdmin: e.target.checked },
                                    })
                                }
                                className="h-4 w-4"
                            />
                            관리자에게 숨은참조(BCC) 발송
                        </label>
                        <div>
                            <label className="mb-1 block text-sm font-medium">관리자 이메일</label>
                            <input
                                type="email"
                                value={settings.general.adminEmail}
                                onChange={(e) =>
                                    setSettings({
                                        ...settings,
                                        general: { ...settings.general, adminEmail: e.target.value },
                                    })
                                }
                                className="w-full rounded border px-3 py-1.5 text-sm"
                            />
                        </div>
                    </div>
                </div>

                {/* 자동 재발송 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">자동 재발송</h4>
                    <div className="space-y-3">
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.general.autoResend}
                                onChange={(e) =>
                                    setSettings({
                                        ...settings,
                                        general: { ...settings.general, autoResend: e.target.checked },
                                    })
                                }
                                className="h-4 w-4"
                            />
                            미열람 시 자동 재발송
                        </label>
                        <div>
                            <label className="mb-1 block text-sm font-medium">재발송 간격 (일)</label>
                            <input
                                type="number"
                                value={settings.general.resendAfterDays}
                                onChange={(e) =>
                                    setSettings({
                                        ...settings,
                                        general: {
                                            ...settings.general,
                                            resendAfterDays: Number(e.target.value),
                                        },
                                    })
                                }
                                className="w-32 rounded border px-3 py-1.5 text-sm"
                                disabled={!settings.general.autoResend}
                            />
                        </div>
                    </div>
                </div>

                {/* 회신 기한 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">회신 관리</h4>
                    <div>
                        <label className="mb-1 block text-sm font-medium">기본 회신 기한 (일)</label>
                        <input
                            type="number"
                            value={settings.general.defaultReplyDays}
                            onChange={(e) =>
                                setSettings({
                                    ...settings,
                                    general: {
                                        ...settings.general,
                                        defaultReplyDays: Number(e.target.value),
                                    },
                                })
                            }
                            className="w-32 rounded border px-3 py-1.5 text-sm"
                        />
                        <p className="mt-1 text-xs text-gray-500">
                            견적서 등 회신이 필요한 이메일의 기본 기한
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

// ===== 발송 이력 탭 =====
function HistoryTab({ settings }: { settings: EmailSettingsData }) {
    const [searchTerm, setSearchTerm] = useState("");
    const [filterStatus, setFilterStatus] = useState<string>("all");
    const [dateRange, setDateRange] = useState({ from: "", to: "" });

    const statusLabels: Record<string, { label: string; color: string }> = {
        sent: { label: "발송", color: "bg-blue-100 text-blue-700" },
        delivered: { label: "전달", color: "bg-green-100 text-green-700" },
        opened: { label: "열람", color: "bg-purple-100 text-purple-700" },
        clicked: { label: "클릭", color: "bg-indigo-100 text-indigo-700" },
        bounced: { label: "반송", color: "bg-orange-100 text-orange-700" },
        failed: { label: "실패", color: "bg-red-100 text-red-700" },
    };

    // 샘플 데이터
    const sampleHistory: EmailHistory[] = [
        {
            id: "1",
            recipient: "customer1@example.com",
            subject: "견적서를 보내드립니다",
            templateName: "견적서 발송",
            status: "opened",
            sentAt: "2024-01-15T10:30:00",
            openedAt: "2024-01-15T11:45:00",
            attachments: ["견적서.pdf"],
        },
        {
            id: "2",
            recipient: "customer2@example.com",
            subject: "세금계산서 발행 안내",
            templateName: "세금계산서 발송",
            status: "delivered",
            sentAt: "2024-01-14T09:00:00",
            attachments: ["세금계산서.pdf"],
        },
    ];

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">발송 이력</h3>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-gray-50">
                    <Download className="h-4 w-4" />
                    내보내기
                </button>
            </div>

            {/* 필터 */}
            <div className="flex items-center gap-4 rounded bg-gray-50 p-3">
                <div className="flex items-center gap-2">
                    <Search className="h-4 w-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="수신자, 제목 검색..."
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
                    <option value="sent">발송</option>
                    <option value="delivered">전달</option>
                    <option value="opened">열람</option>
                    <option value="clicked">클릭</option>
                    <option value="bounced">반송</option>
                    <option value="failed">실패</option>
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
                            <th className="border-b px-4 py-2 text-left">수신자</th>
                            <th className="border-b px-4 py-2 text-left">제목</th>
                            <th className="border-b px-4 py-2 text-left">템플릿</th>
                            <th className="border-b px-4 py-2 text-left">발송일시</th>
                            <th className="border-b px-4 py-2 text-left">상태</th>
                            <th className="border-b px-4 py-2 text-center">첨부</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sampleHistory.map((item) => (
                            <tr key={item.id} className="hover:bg-gray-50">
                                <td className="border-b px-4 py-2">{item.recipient}</td>
                                <td className="border-b px-4 py-2">{item.subject}</td>
                                <td className="border-b px-4 py-2">{item.templateName}</td>
                                <td className="border-b px-4 py-2">
                                    {new Date(item.sentAt).toLocaleString()}
                                </td>
                                <td className="border-b px-4 py-2">
                                    <span
                                        className={`rounded px-2 py-0.5 text-xs ${
                                            statusLabels[item.status].color
                                        }`}
                                    >
                                        {statusLabels[item.status].label}
                                    </span>
                                </td>
                                <td className="border-b px-4 py-2 text-center">
                                    {item.attachments.length > 0 && (
                                        <Paperclip className="mx-auto h-4 w-4 text-gray-400" />
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* 통계 */}
            <div className="grid grid-cols-6 gap-4">
                {Object.entries(statusLabels).map(([key, value]) => (
                    <div key={key} className="rounded border p-3 text-center">
                        <div className={`mb-1 text-2xl font-bold ${value.color.split(" ")[1]}`}>
                            {sampleHistory.filter((h) => h.status === key).length}
                        </div>
                        <div className="text-xs text-gray-500">{value.label}</div>
                    </div>
                ))}
            </div>
        </div>
    );
}

// ===== 일반 설정 탭 =====
function GeneralTab({
    settings,
    setSettings,
}: {
    settings: EmailSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<EmailSettingsData>>;
}) {
    return (
        <div className="space-y-6">
            <h3 className="text-lg font-medium">일반 설정</h3>

            <div className="grid grid-cols-2 gap-6">
                {/* 기본 설정 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">기본 설정</h4>
                    <div className="space-y-4">
                        <div>
                            <label className="mb-1 block text-sm font-medium">기본 회신 기한 (일)</label>
                            <input
                                type="number"
                                value={settings.general.defaultReplyDays}
                                onChange={(e) =>
                                    setSettings({
                                        ...settings,
                                        general: {
                                            ...settings.general,
                                            defaultReplyDays: Number(e.target.value),
                                        },
                                    })
                                }
                                className="w-32 rounded border px-3 py-1.5 text-sm"
                            />
                        </div>
                        <div>
                            <label className="mb-1 block text-sm font-medium">관리자 이메일</label>
                            <input
                                type="email"
                                value={settings.general.adminEmail}
                                onChange={(e) =>
                                    setSettings({
                                        ...settings,
                                        general: { ...settings.general, adminEmail: e.target.value },
                                    })
                                }
                                className="w-full rounded border px-3 py-1.5 text-sm"
                            />
                        </div>
                    </div>
                </div>

                {/* 추적 설정 요약 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">추적 설정</h4>
                    <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                            <span>이메일 열람 추적</span>
                            <span className={settings.general.trackOpens ? "text-green-600" : "text-gray-400"}>
                                {settings.general.trackOpens ? "활성" : "비활성"}
                            </span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                            <span>링크 클릭 추적</span>
                            <span className={settings.general.trackClicks ? "text-green-600" : "text-gray-400"}>
                                {settings.general.trackClicks ? "활성" : "비활성"}
                            </span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                            <span>수신거부 링크</span>
                            <span className={settings.general.unsubscribeLink ? "text-green-600" : "text-gray-400"}>
                                {settings.general.unsubscribeLink ? "포함" : "미포함"}
                            </span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                            <span>관리자 BCC</span>
                            <span className={settings.general.bccAdmin ? "text-green-600" : "text-gray-400"}>
                                {settings.general.bccAdmin ? "활성" : "비활성"}
                            </span>
                        </div>
                    </div>
                </div>

                {/* 자동 재발송 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">자동 재발송</h4>
                    <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                            <span>미열람 시 자동 재발송</span>
                            <span className={settings.general.autoResend ? "text-green-600" : "text-gray-400"}>
                                {settings.general.autoResend ? "활성" : "비활성"}
                            </span>
                        </div>
                        {settings.general.autoResend && (
                            <div className="flex items-center justify-between text-sm">
                                <span>재발송 간격</span>
                                <span>{settings.general.resendAfterDays}일</span>
                            </div>
                        )}
                    </div>
                </div>

                {/* 현재 상태 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">현재 상태</h4>
                    <div className="space-y-2 text-sm">
                        <div className="flex items-center justify-between">
                            <span>등록된 SMTP 서버</span>
                            <span>{settings.smtpServers.length}개</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>이메일 템플릿</span>
                            <span>{settings.templates.length}개</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>첨부파일 규칙</span>
                            <span>{settings.attachmentRules.length}개</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>서명</span>
                            <span>{settings.signatures.length}개</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default EmailSettingsWindow;
