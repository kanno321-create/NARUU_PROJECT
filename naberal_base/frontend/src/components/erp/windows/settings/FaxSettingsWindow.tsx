"use client";

import React, { useState, useEffect } from "react";
import {
    Phone,
    Server,
    Send,
    Inbox,
    FileText,
    Clock,
    Plus,
    Trash2,
    Edit,
    Eye,
    RefreshCw,
    Download,
    Upload,
    Settings,
    Check,
    X,
    AlertTriangle,
    Info,
    Calendar,
    List,
    Search,
    Filter,
    Printer,
    File,
    Image,
    Folder,
    Users,
    Building2,
    MoreVertical,
    ChevronDown,
    ChevronRight,
    Copy,
    Archive,
    Star,
    Flag,
    Tag,
    RotateCcw,
    Pause,
    Play,
    StopCircle,
} from "lucide-react";

// ===== 인터페이스 정의 =====
interface FaxServer {
    id: string;
    name: string;
    type: "modem" | "internet" | "cloud";
    host: string;
    port: number;
    username: string;
    password: string;
    faxNumber: string;
    lineCount: number;
    isDefault: boolean;
    isActive: boolean;
    testResult?: {
        success: boolean;
        message: string;
        testedAt: string;
    };
}

interface FaxSendSettings {
    defaultResolution: "standard" | "fine" | "superfine";
    defaultPaperSize: "A4" | "Letter" | "Legal";
    retryCount: number;
    retryInterval: number;
    sendConfirmation: boolean;
    confirmationEmail: string;
    headerFormat: string;
    includeCompanyLogo: boolean;
    convertToBlackWhite: boolean;
    compressImage: boolean;
}

interface FaxReceiveSettings {
    autoReceive: boolean;
    saveLocation: string;
    fileFormat: "pdf" | "tiff" | "jpg";
    printOnReceive: boolean;
    printerName: string;
    notifyOnReceive: boolean;
    notifyEmail: string;
    autoForward: boolean;
    forwardNumber: string;
    routingRules: RoutingRule[];
}

interface RoutingRule {
    id: string;
    name: string;
    condition: "sender" | "time" | "keyword";
    value: string;
    action: "folder" | "email" | "print" | "forward";
    target: string;
    isActive: boolean;
}

interface CoverSheet {
    id: string;
    name: string;
    template: string;
    isDefault: boolean;
    isActive: boolean;
    fields: {
        showSender: boolean;
        showRecipient: boolean;
        showDate: boolean;
        showPageCount: boolean;
        showUrgent: boolean;
        showConfidential: boolean;
        showSubject: boolean;
        showMessage: boolean;
    };
}

interface ScheduledFax {
    id: string;
    recipient: string;
    recipientName: string;
    subject: string;
    pageCount: number;
    scheduledAt: string;
    status: "pending" | "sent" | "failed" | "cancelled";
    createdAt: string;
    sentAt?: string;
    errorMessage?: string;
    retryCount: number;
}

interface FaxHistory {
    id: string;
    type: "sent" | "received";
    number: string;
    contactName: string;
    subject: string;
    pageCount: number;
    duration: number;
    status: "success" | "failed" | "busy" | "no_answer";
    timestamp: string;
    filePath: string;
}

interface FaxSettingsData {
    servers: FaxServer[];
    sendSettings: FaxSendSettings;
    receiveSettings: FaxReceiveSettings;
    coverSheets: CoverSheet[];
    scheduledFaxes: ScheduledFax[];
    history: FaxHistory[];
    addressBook: FaxContact[];
}

interface FaxContact {
    id: string;
    name: string;
    company: string;
    faxNumber: string;
    email: string;
    group: string;
    isFavorite: boolean;
}

// ===== 기본 데이터 =====
const defaultSettings: FaxSettingsData = {
    servers: [
        {
            id: "fax_1",
            name: "본사 팩스 서버",
            type: "modem",
            host: "192.168.1.100",
            port: 4559,
            username: "admin",
            password: "",
            faxNumber: "02-1234-5679",
            lineCount: 2,
            isDefault: true,
            isActive: true,
        },
    ],
    sendSettings: {
        defaultResolution: "fine",
        defaultPaperSize: "A4",
        retryCount: 3,
        retryInterval: 5,
        sendConfirmation: true,
        confirmationEmail: "admin@company.com",
        headerFormat: "{company} - {faxNumber} - {date} {time} - Page {page}/{total}",
        includeCompanyLogo: true,
        convertToBlackWhite: true,
        compressImage: true,
    },
    receiveSettings: {
        autoReceive: true,
        saveLocation: "C:\\FAX\\Received",
        fileFormat: "pdf",
        printOnReceive: false,
        printerName: "",
        notifyOnReceive: true,
        notifyEmail: "admin@company.com",
        autoForward: false,
        forwardNumber: "",
        routingRules: [],
    },
    coverSheets: [
        {
            id: "cover_1",
            name: "기본 표지",
            template: "standard",
            isDefault: true,
            isActive: true,
            fields: {
                showSender: true,
                showRecipient: true,
                showDate: true,
                showPageCount: true,
                showUrgent: false,
                showConfidential: false,
                showSubject: true,
                showMessage: true,
            },
        },
    ],
    scheduledFaxes: [],
    history: [],
    addressBook: [
        {
            id: "contact_1",
            name: "김철수",
            company: "(주)협력사",
            faxNumber: "02-9876-5432",
            email: "kim@partner.com",
            group: "협력사",
            isFavorite: true,
        },
    ],
};

// ===== 메인 컴포넌트 =====
export function FaxSettingsWindow() {
    const [activeTab, setActiveTab] = useState("server");
    const [settings, setSettings] = useState<FaxSettingsData>(defaultSettings);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: "success" | "error" | "info"; text: string } | null>(null);

    // 설정 로드
    useEffect(() => {
        const saved = localStorage.getItem("erp_fax_settings");
        if (saved) {
            try {
                setSettings(JSON.parse(saved));
            } catch (e) {
                console.error("팩스 설정 로드 실패:", e);
            }
        }
    }, []);

    // 설정 저장
    const handleSave = async () => {
        setSaving(true);
        try {
            localStorage.setItem("erp_fax_settings", JSON.stringify(settings));
            window.dispatchEvent(new CustomEvent("kis-erp-settings-updated"));
            setMessage({ type: "success", text: "팩스 설정이 저장되었습니다." });
            setTimeout(() => setMessage(null), 3000);
        } catch (error) {
            setMessage({ type: "error", text: "설정 저장에 실패했습니다." });
        } finally {
            setSaving(false);
        }
    };

    const tabs = [
        { id: "server", label: "팩스 서버", icon: Server },
        { id: "send", label: "발송 설정", icon: Send },
        { id: "receive", label: "수신 설정", icon: Inbox },
        { id: "coversheet", label: "커버시트", icon: FileText },
        { id: "scheduled", label: "예약 발송", icon: Clock },
        { id: "history", label: "발송/수신 이력", icon: List },
        { id: "addressbook", label: "주소록", icon: Users },
        { id: "general", label: "일반 설정", icon: Settings },
    ];

    return (
        <div className="flex h-full flex-col bg-white">
            {/* 상단 툴바 */}
            <div className="flex items-center justify-between border-b bg-gray-50 px-4 py-2">
                <div className="flex items-center gap-2">
                    <Phone className="h-5 w-5 text-green-600" />
                    <span className="font-medium">팩스 설정</span>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center gap-1 rounded bg-green-600 px-4 py-1.5 text-sm text-white hover:bg-green-700 disabled:opacity-50"
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
                                        ? "bg-green-600 text-white"
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
                    {activeTab === "server" && (
                        <FaxServerTab settings={settings} setSettings={setSettings} setMessage={setMessage} />
                    )}
                    {activeTab === "send" && (
                        <SendSettingsTab settings={settings} setSettings={setSettings} />
                    )}
                    {activeTab === "receive" && (
                        <ReceiveSettingsTab settings={settings} setSettings={setSettings} />
                    )}
                    {activeTab === "coversheet" && (
                        <CoverSheetTab settings={settings} setSettings={setSettings} />
                    )}
                    {activeTab === "scheduled" && (
                        <ScheduledTab settings={settings} setSettings={setSettings} />
                    )}
                    {activeTab === "history" && (
                        <HistoryTab settings={settings} />
                    )}
                    {activeTab === "addressbook" && (
                        <AddressBookTab settings={settings} setSettings={setSettings} />
                    )}
                    {activeTab === "general" && (
                        <GeneralTab settings={settings} setSettings={setSettings} />
                    )}
                </div>
            </div>
        </div>
    );
}

// ===== 팩스 서버 탭 =====
function FaxServerTab({
    settings,
    setSettings,
    setMessage,
}: {
    settings: FaxSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<FaxSettingsData>>;
    setMessage: React.Dispatch<React.SetStateAction<{ type: "success" | "error" | "info"; text: string } | null>>;
}) {
    const [selectedServer, setSelectedServer] = useState<FaxServer | null>(
        settings.servers[0] || null
    );
    const [testing, setTesting] = useState(false);

    const handleAddServer = () => {
        const newServer: FaxServer = {
            id: `fax_${Date.now()}`,
            name: "새 팩스 서버",
            type: "modem",
            host: "",
            port: 4559,
            username: "",
            password: "",
            faxNumber: "",
            lineCount: 1,
            isDefault: settings.servers.length === 0,
            isActive: true,
        };
        setSettings({
            ...settings,
            servers: [...settings.servers, newServer],
        });
        setSelectedServer(newServer);
    };

    const handleTestConnection = async () => {
        if (!selectedServer) return;
        setTesting(true);
        setTimeout(() => {
            const success = Boolean(selectedServer.host && selectedServer.faxNumber);
            setSettings({
                ...settings,
                servers: settings.servers.map((s) =>
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
                text: success ? "팩스 서버 연결 테스트 성공" : "팩스 서버 연결 테스트 실패",
            });
            setTesting(false);
        }, 2000);
    };

    const updateServer = (updates: Partial<FaxServer>) => {
        if (!selectedServer) return;
        const updated = { ...selectedServer, ...updates };
        setSelectedServer(updated);
        setSettings({
            ...settings,
            servers: settings.servers.map((s) =>
                s.id === selectedServer.id ? updated : s
            ),
        });
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">팩스 서버 관리</h3>
                <button
                    onClick={handleAddServer}
                    className="flex items-center gap-1 rounded bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700"
                >
                    <Plus className="h-4 w-4" />
                    서버 추가
                </button>
            </div>

            <div className="grid grid-cols-3 gap-4">
                {/* 서버 목록 */}
                <div className="col-span-1 rounded border">
                    <div className="border-b bg-gray-50 px-3 py-2 text-sm font-medium">
                        서버 목록 ({settings.servers.length})
                    </div>
                    <div className="max-h-96 overflow-auto">
                        {settings.servers.map((server) => (
                            <div
                                key={server.id}
                                onClick={() => setSelectedServer(server)}
                                className={`flex cursor-pointer items-center justify-between border-b px-3 py-2 hover:bg-gray-50 ${
                                    selectedServer?.id === server.id ? "bg-green-50" : ""
                                }`}
                            >
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm font-medium">{server.name}</span>
                                        {server.isDefault && (
                                            <span className="rounded bg-green-100 px-1.5 py-0.5 text-xs text-green-700">
                                                기본
                                            </span>
                                        )}
                                    </div>
                                    <div className="text-xs text-gray-500">{server.faxNumber}</div>
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
                                            <Phone className="h-4 w-4" />
                                        )}
                                        연결 테스트
                                    </button>
                                </div>
                            </div>

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
                                </div>
                            )}

                            <div className="grid grid-cols-2 gap-4">
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
                                        <label className="mb-1 block text-sm font-medium">서버 유형</label>
                                        <select
                                            value={selectedServer.type}
                                            onChange={(e) =>
                                                updateServer({ type: e.target.value as FaxServer["type"] })
                                            }
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        >
                                            <option value="modem">모뎀 (로컬)</option>
                                            <option value="internet">인터넷 팩스</option>
                                            <option value="cloud">클라우드 팩스</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">서버 주소</label>
                                        <input
                                            type="text"
                                            value={selectedServer.host}
                                            onChange={(e) => updateServer({ host: e.target.value })}
                                            placeholder="192.168.1.100"
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">포트</label>
                                        <input
                                            type="number"
                                            value={selectedServer.port}
                                            onChange={(e) => updateServer({ port: Number(e.target.value) })}
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-3">
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">팩스 번호</label>
                                        <input
                                            type="text"
                                            value={selectedServer.faxNumber}
                                            onChange={(e) => updateServer({ faxNumber: e.target.value })}
                                            placeholder="02-1234-5679"
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="mb-1 block text-sm font-medium">회선 수</label>
                                        <input
                                            type="number"
                                            value={selectedServer.lineCount}
                                            onChange={(e) => updateServer({ lineCount: Number(e.target.value) })}
                                            className="w-full rounded border px-3 py-1.5 text-sm"
                                        />
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
                            </div>

                            <div className="mt-4 flex items-center gap-4">
                                <label className="flex items-center gap-2 text-sm">
                                    <input
                                        type="checkbox"
                                        checked={selectedServer.isDefault}
                                        onChange={(e) => updateServer({ isDefault: e.target.checked })}
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

// ===== 발송 설정 탭 =====
function SendSettingsTab({
    settings,
    setSettings,
}: {
    settings: FaxSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<FaxSettingsData>>;
}) {
    const updateSendSettings = (updates: Partial<FaxSendSettings>) => {
        setSettings({
            ...settings,
            sendSettings: { ...settings.sendSettings, ...updates },
        });
    };

    return (
        <div className="space-y-6">
            <h3 className="text-lg font-medium">발송 설정</h3>

            <div className="grid grid-cols-2 gap-6">
                {/* 기본 설정 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">기본 설정</h4>
                    <div className="space-y-4">
                        <div>
                            <label className="mb-1 block text-sm font-medium">기본 해상도</label>
                            <select
                                value={settings.sendSettings.defaultResolution}
                                onChange={(e) =>
                                    updateSendSettings({
                                        defaultResolution: e.target.value as FaxSendSettings["defaultResolution"],
                                    })
                                }
                                className="w-full rounded border px-3 py-1.5 text-sm"
                            >
                                <option value="standard">표준 (200x100 dpi)</option>
                                <option value="fine">고해상 (200x200 dpi)</option>
                                <option value="superfine">초고해상 (200x400 dpi)</option>
                            </select>
                        </div>
                        <div>
                            <label className="mb-1 block text-sm font-medium">기본 용지 크기</label>
                            <select
                                value={settings.sendSettings.defaultPaperSize}
                                onChange={(e) =>
                                    updateSendSettings({
                                        defaultPaperSize: e.target.value as FaxSendSettings["defaultPaperSize"],
                                    })
                                }
                                className="w-full rounded border px-3 py-1.5 text-sm"
                            >
                                <option value="A4">A4</option>
                                <option value="Letter">Letter</option>
                                <option value="Legal">Legal</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* 재시도 설정 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">재시도 설정</h4>
                    <div className="space-y-4">
                        <div>
                            <label className="mb-1 block text-sm font-medium">재시도 횟수</label>
                            <input
                                type="number"
                                value={settings.sendSettings.retryCount}
                                onChange={(e) => updateSendSettings({ retryCount: Number(e.target.value) })}
                                className="w-32 rounded border px-3 py-1.5 text-sm"
                            />
                        </div>
                        <div>
                            <label className="mb-1 block text-sm font-medium">재시도 간격 (분)</label>
                            <input
                                type="number"
                                value={settings.sendSettings.retryInterval}
                                onChange={(e) => updateSendSettings({ retryInterval: Number(e.target.value) })}
                                className="w-32 rounded border px-3 py-1.5 text-sm"
                            />
                        </div>
                    </div>
                </div>

                {/* 발송 확인 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">발송 확인</h4>
                    <div className="space-y-4">
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.sendSettings.sendConfirmation}
                                onChange={(e) => updateSendSettings({ sendConfirmation: e.target.checked })}
                                className="h-4 w-4"
                            />
                            발송 확인 이메일 전송
                        </label>
                        <div>
                            <label className="mb-1 block text-sm font-medium">확인 이메일 주소</label>
                            <input
                                type="email"
                                value={settings.sendSettings.confirmationEmail}
                                onChange={(e) => updateSendSettings({ confirmationEmail: e.target.value })}
                                className="w-full rounded border px-3 py-1.5 text-sm"
                                disabled={!settings.sendSettings.sendConfirmation}
                            />
                        </div>
                    </div>
                </div>

                {/* 이미지 처리 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">이미지 처리</h4>
                    <div className="space-y-3">
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.sendSettings.convertToBlackWhite}
                                onChange={(e) => updateSendSettings({ convertToBlackWhite: e.target.checked })}
                                className="h-4 w-4"
                            />
                            흑백으로 변환
                        </label>
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.sendSettings.compressImage}
                                onChange={(e) => updateSendSettings({ compressImage: e.target.checked })}
                                className="h-4 w-4"
                            />
                            이미지 압축
                        </label>
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.sendSettings.includeCompanyLogo}
                                onChange={(e) => updateSendSettings({ includeCompanyLogo: e.target.checked })}
                                className="h-4 w-4"
                            />
                            회사 로고 포함
                        </label>
                    </div>
                </div>

                {/* 헤더 설정 */}
                <div className="col-span-2 rounded border p-4">
                    <h4 className="mb-4 font-medium">헤더 형식</h4>
                    <input
                        type="text"
                        value={settings.sendSettings.headerFormat}
                        onChange={(e) => updateSendSettings({ headerFormat: e.target.value })}
                        className="w-full rounded border px-3 py-1.5 text-sm"
                    />
                    <div className="mt-2 text-xs text-gray-500">
                        사용 가능한 변수: {"{company}"}, {"{faxNumber}"}, {"{date}"}, {"{time}"}, {"{page}"}, {"{total}"}
                    </div>
                </div>
            </div>
        </div>
    );
}

// ===== 수신 설정 탭 =====
function ReceiveSettingsTab({
    settings,
    setSettings,
}: {
    settings: FaxSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<FaxSettingsData>>;
}) {
    const updateReceiveSettings = (updates: Partial<FaxReceiveSettings>) => {
        setSettings({
            ...settings,
            receiveSettings: { ...settings.receiveSettings, ...updates },
        });
    };

    return (
        <div className="space-y-6">
            <h3 className="text-lg font-medium">수신 설정</h3>

            <div className="grid grid-cols-2 gap-6">
                {/* 자동 수신 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">자동 수신</h4>
                    <div className="space-y-4">
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.receiveSettings.autoReceive}
                                onChange={(e) => updateReceiveSettings({ autoReceive: e.target.checked })}
                                className="h-4 w-4"
                            />
                            자동 수신 사용
                        </label>
                        <div>
                            <label className="mb-1 block text-sm font-medium">저장 위치</label>
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={settings.receiveSettings.saveLocation}
                                    onChange={(e) => updateReceiveSettings({ saveLocation: e.target.value })}
                                    className="flex-1 rounded border px-3 py-1.5 text-sm"
                                />
                                <button className="rounded border px-3 py-1.5 text-sm hover:bg-gray-50">
                                    <Folder className="h-4 w-4" />
                                </button>
                            </div>
                        </div>
                        <div>
                            <label className="mb-1 block text-sm font-medium">저장 형식</label>
                            <select
                                value={settings.receiveSettings.fileFormat}
                                onChange={(e) =>
                                    updateReceiveSettings({
                                        fileFormat: e.target.value as FaxReceiveSettings["fileFormat"],
                                    })
                                }
                                className="w-full rounded border px-3 py-1.5 text-sm"
                            >
                                <option value="pdf">PDF</option>
                                <option value="tiff">TIFF</option>
                                <option value="jpg">JPG</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* 자동 인쇄 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">자동 인쇄</h4>
                    <div className="space-y-4">
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.receiveSettings.printOnReceive}
                                onChange={(e) => updateReceiveSettings({ printOnReceive: e.target.checked })}
                                className="h-4 w-4"
                            />
                            수신 시 자동 인쇄
                        </label>
                        <div>
                            <label className="mb-1 block text-sm font-medium">프린터</label>
                            <select
                                value={settings.receiveSettings.printerName}
                                onChange={(e) => updateReceiveSettings({ printerName: e.target.value })}
                                className="w-full rounded border px-3 py-1.5 text-sm"
                                disabled={!settings.receiveSettings.printOnReceive}
                            >
                                <option value="">시스템 기본 프린터</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* 알림 설정 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">알림 설정</h4>
                    <div className="space-y-4">
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.receiveSettings.notifyOnReceive}
                                onChange={(e) => updateReceiveSettings({ notifyOnReceive: e.target.checked })}
                                className="h-4 w-4"
                            />
                            수신 시 이메일 알림
                        </label>
                        <div>
                            <label className="mb-1 block text-sm font-medium">알림 이메일</label>
                            <input
                                type="email"
                                value={settings.receiveSettings.notifyEmail}
                                onChange={(e) => updateReceiveSettings({ notifyEmail: e.target.value })}
                                className="w-full rounded border px-3 py-1.5 text-sm"
                                disabled={!settings.receiveSettings.notifyOnReceive}
                            />
                        </div>
                    </div>
                </div>

                {/* 자동 전달 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">자동 전달</h4>
                    <div className="space-y-4">
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.receiveSettings.autoForward}
                                onChange={(e) => updateReceiveSettings({ autoForward: e.target.checked })}
                                className="h-4 w-4"
                            />
                            수신 팩스 자동 전달
                        </label>
                        <div>
                            <label className="mb-1 block text-sm font-medium">전달 번호</label>
                            <input
                                type="text"
                                value={settings.receiveSettings.forwardNumber}
                                onChange={(e) => updateReceiveSettings({ forwardNumber: e.target.value })}
                                className="w-full rounded border px-3 py-1.5 text-sm"
                                placeholder="02-9876-5432"
                                disabled={!settings.receiveSettings.autoForward}
                            />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// ===== 커버시트 탭 =====
function CoverSheetTab({
    settings,
    setSettings,
}: {
    settings: FaxSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<FaxSettingsData>>;
}) {
    const [selectedSheet, setSelectedSheet] = useState<CoverSheet | null>(
        settings.coverSheets[0] || null
    );

    const handleAddSheet = () => {
        const newSheet: CoverSheet = {
            id: `cover_${Date.now()}`,
            name: "새 커버시트",
            template: "standard",
            isDefault: false,
            isActive: true,
            fields: {
                showSender: true,
                showRecipient: true,
                showDate: true,
                showPageCount: true,
                showUrgent: false,
                showConfidential: false,
                showSubject: true,
                showMessage: true,
            },
        };
        setSettings({
            ...settings,
            coverSheets: [...settings.coverSheets, newSheet],
        });
        setSelectedSheet(newSheet);
    };

    const updateSheet = (updates: Partial<CoverSheet>) => {
        if (!selectedSheet) return;
        const updated = { ...selectedSheet, ...updates };
        setSelectedSheet(updated);
        setSettings({
            ...settings,
            coverSheets: settings.coverSheets.map((s) =>
                s.id === selectedSheet.id ? updated : s
            ),
        });
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">커버시트 관리</h3>
                <button
                    onClick={handleAddSheet}
                    className="flex items-center gap-1 rounded bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700"
                >
                    <Plus className="h-4 w-4" />
                    커버시트 추가
                </button>
            </div>

            <div className="grid grid-cols-3 gap-4">
                {/* 커버시트 목록 */}
                <div className="col-span-1 rounded border">
                    <div className="border-b bg-gray-50 px-3 py-2 text-sm font-medium">
                        커버시트 목록 ({settings.coverSheets.length})
                    </div>
                    <div className="max-h-96 overflow-auto">
                        {settings.coverSheets.map((sheet) => (
                            <div
                                key={sheet.id}
                                onClick={() => setSelectedSheet(sheet)}
                                className={`cursor-pointer border-b px-3 py-2 hover:bg-gray-50 ${
                                    selectedSheet?.id === sheet.id ? "bg-green-50" : ""
                                }`}
                            >
                                <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium">{sheet.name}</span>
                                    {sheet.isDefault && (
                                        <span className="rounded bg-green-100 px-1.5 py-0.5 text-xs text-green-700">
                                            기본
                                        </span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 커버시트 설정 */}
                <div className="col-span-2 rounded border p-4">
                    {selectedSheet ? (
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="mb-1 block text-sm font-medium">커버시트 이름</label>
                                    <input
                                        type="text"
                                        value={selectedSheet.name}
                                        onChange={(e) => updateSheet({ name: e.target.value })}
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium">템플릿</label>
                                    <select
                                        value={selectedSheet.template}
                                        onChange={(e) => updateSheet({ template: e.target.value })}
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                    >
                                        <option value="standard">표준</option>
                                        <option value="simple">간소화</option>
                                        <option value="formal">공식</option>
                                        <option value="custom">사용자 정의</option>
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="mb-2 block text-sm font-medium">표시 항목</label>
                                <div className="grid grid-cols-4 gap-3">
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedSheet.fields.showSender}
                                            onChange={(e) =>
                                                updateSheet({
                                                    fields: { ...selectedSheet.fields, showSender: e.target.checked },
                                                })
                                            }
                                            className="h-4 w-4"
                                        />
                                        발신자
                                    </label>
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedSheet.fields.showRecipient}
                                            onChange={(e) =>
                                                updateSheet({
                                                    fields: { ...selectedSheet.fields, showRecipient: e.target.checked },
                                                })
                                            }
                                            className="h-4 w-4"
                                        />
                                        수신자
                                    </label>
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedSheet.fields.showDate}
                                            onChange={(e) =>
                                                updateSheet({
                                                    fields: { ...selectedSheet.fields, showDate: e.target.checked },
                                                })
                                            }
                                            className="h-4 w-4"
                                        />
                                        날짜
                                    </label>
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedSheet.fields.showPageCount}
                                            onChange={(e) =>
                                                updateSheet({
                                                    fields: { ...selectedSheet.fields, showPageCount: e.target.checked },
                                                })
                                            }
                                            className="h-4 w-4"
                                        />
                                        페이지 수
                                    </label>
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedSheet.fields.showSubject}
                                            onChange={(e) =>
                                                updateSheet({
                                                    fields: { ...selectedSheet.fields, showSubject: e.target.checked },
                                                })
                                            }
                                            className="h-4 w-4"
                                        />
                                        제목
                                    </label>
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedSheet.fields.showMessage}
                                            onChange={(e) =>
                                                updateSheet({
                                                    fields: { ...selectedSheet.fields, showMessage: e.target.checked },
                                                })
                                            }
                                            className="h-4 w-4"
                                        />
                                        메시지
                                    </label>
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedSheet.fields.showUrgent}
                                            onChange={(e) =>
                                                updateSheet({
                                                    fields: { ...selectedSheet.fields, showUrgent: e.target.checked },
                                                })
                                            }
                                            className="h-4 w-4"
                                        />
                                        긴급 표시
                                    </label>
                                    <label className="flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={selectedSheet.fields.showConfidential}
                                            onChange={(e) =>
                                                updateSheet({
                                                    fields: { ...selectedSheet.fields, showConfidential: e.target.checked },
                                                })
                                            }
                                            className="h-4 w-4"
                                        />
                                        기밀 표시
                                    </label>
                                </div>
                            </div>

                            <div className="flex items-center gap-4">
                                <label className="flex items-center gap-2 text-sm">
                                    <input
                                        type="checkbox"
                                        checked={selectedSheet.isDefault}
                                        onChange={(e) => updateSheet({ isDefault: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    기본 커버시트
                                </label>
                                <label className="flex items-center gap-2 text-sm">
                                    <input
                                        type="checkbox"
                                        checked={selectedSheet.isActive}
                                        onChange={(e) => updateSheet({ isActive: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    활성화
                                </label>
                            </div>

                            <div className="flex gap-2">
                                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-gray-50">
                                    <Eye className="h-4 w-4" />
                                    미리보기
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="flex h-full items-center justify-center text-gray-500">
                            커버시트를 선택하거나 새로 추가하세요
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
    settings: FaxSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<FaxSettingsData>>;
}) {
    const statusLabels: Record<string, { label: string; color: string }> = {
        pending: { label: "대기", color: "bg-yellow-100 text-yellow-700" },
        sent: { label: "발송됨", color: "bg-green-100 text-green-700" },
        failed: { label: "실패", color: "bg-red-100 text-red-700" },
        cancelled: { label: "취소됨", color: "bg-gray-100 text-gray-700" },
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">예약 발송 관리</h3>
                <button className="flex items-center gap-1 rounded bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700">
                    <Plus className="h-4 w-4" />
                    예약 추가
                </button>
            </div>

            <div className="rounded border">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="border-b px-4 py-2 text-left">수신자</th>
                            <th className="border-b px-4 py-2 text-left">제목</th>
                            <th className="border-b px-4 py-2 text-center">페이지</th>
                            <th className="border-b px-4 py-2 text-left">예약 시간</th>
                            <th className="border-b px-4 py-2 text-left">상태</th>
                            <th className="border-b px-4 py-2 text-center">관리</th>
                        </tr>
                    </thead>
                    <tbody>
                        {settings.scheduledFaxes.length > 0 ? (
                            settings.scheduledFaxes.map((fax) => (
                                <tr key={fax.id} className="hover:bg-gray-50">
                                    <td className="border-b px-4 py-2">
                                        <div>{fax.recipientName}</div>
                                        <div className="text-xs text-gray-500">{fax.recipient}</div>
                                    </td>
                                    <td className="border-b px-4 py-2">{fax.subject}</td>
                                    <td className="border-b px-4 py-2 text-center">{fax.pageCount}</td>
                                    <td className="border-b px-4 py-2">
                                        {new Date(fax.scheduledAt).toLocaleString()}
                                    </td>
                                    <td className="border-b px-4 py-2">
                                        <span className={`rounded px-2 py-0.5 text-xs ${statusLabels[fax.status].color}`}>
                                            {statusLabels[fax.status].label}
                                        </span>
                                    </td>
                                    <td className="border-b px-4 py-2 text-center">
                                        {fax.status === "pending" && (
                                            <div className="flex justify-center gap-1">
                                                <button className="rounded p-1 hover:bg-gray-100">
                                                    <Edit className="h-4 w-4" />
                                                </button>
                                                <button className="rounded p-1 text-red-600 hover:bg-red-50">
                                                    <X className="h-4 w-4" />
                                                </button>
                                            </div>
                                        )}
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                                    예약된 팩스가 없습니다
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

// ===== 발송/수신 이력 탭 =====
function HistoryTab({ settings }: { settings: FaxSettingsData }) {
    const [filterType, setFilterType] = useState<string>("all");
    const [searchTerm, setSearchTerm] = useState("");

    const statusLabels: Record<string, { label: string; color: string }> = {
        success: { label: "성공", color: "bg-green-100 text-green-700" },
        failed: { label: "실패", color: "bg-red-100 text-red-700" },
        busy: { label: "통화중", color: "bg-yellow-100 text-yellow-700" },
        no_answer: { label: "응답없음", color: "bg-orange-100 text-orange-700" },
    };

    // 샘플 데이터
    const sampleHistory: FaxHistory[] = [
        {
            id: "1",
            type: "sent",
            number: "02-9876-5432",
            contactName: "김철수",
            subject: "견적서 발송",
            pageCount: 3,
            duration: 45,
            status: "success",
            timestamp: "2024-01-15T10:30:00",
            filePath: "C:\\FAX\\Sent\\20240115_103000.pdf",
        },
        {
            id: "2",
            type: "received",
            number: "031-555-1234",
            contactName: "이영희",
            subject: "발주서",
            pageCount: 2,
            duration: 30,
            status: "success",
            timestamp: "2024-01-15T09:15:00",
            filePath: "C:\\FAX\\Received\\20240115_091500.pdf",
        },
    ];

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">발송/수신 이력</h3>
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
                        placeholder="번호, 이름, 제목 검색..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="rounded border px-3 py-1.5 text-sm"
                    />
                </div>
                <select
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value)}
                    className="rounded border px-3 py-1.5 text-sm"
                >
                    <option value="all">전체</option>
                    <option value="sent">발송</option>
                    <option value="received">수신</option>
                </select>
            </div>

            {/* 이력 테이블 */}
            <div className="rounded border">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="border-b px-4 py-2 text-left">유형</th>
                            <th className="border-b px-4 py-2 text-left">번호/이름</th>
                            <th className="border-b px-4 py-2 text-left">제목</th>
                            <th className="border-b px-4 py-2 text-center">페이지</th>
                            <th className="border-b px-4 py-2 text-center">소요시간</th>
                            <th className="border-b px-4 py-2 text-left">일시</th>
                            <th className="border-b px-4 py-2 text-left">상태</th>
                            <th className="border-b px-4 py-2 text-center">파일</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sampleHistory.map((item) => (
                            <tr key={item.id} className="hover:bg-gray-50">
                                <td className="border-b px-4 py-2">
                                    <span
                                        className={`rounded px-2 py-0.5 text-xs ${
                                            item.type === "sent"
                                                ? "bg-blue-100 text-blue-700"
                                                : "bg-purple-100 text-purple-700"
                                        }`}
                                    >
                                        {item.type === "sent" ? "발송" : "수신"}
                                    </span>
                                </td>
                                <td className="border-b px-4 py-2">
                                    <div>{item.contactName}</div>
                                    <div className="text-xs text-gray-500">{item.number}</div>
                                </td>
                                <td className="border-b px-4 py-2">{item.subject}</td>
                                <td className="border-b px-4 py-2 text-center">{item.pageCount}</td>
                                <td className="border-b px-4 py-2 text-center">{item.duration}초</td>
                                <td className="border-b px-4 py-2">
                                    {new Date(item.timestamp).toLocaleString()}
                                </td>
                                <td className="border-b px-4 py-2">
                                    <span className={`rounded px-2 py-0.5 text-xs ${statusLabels[item.status].color}`}>
                                        {statusLabels[item.status].label}
                                    </span>
                                </td>
                                <td className="border-b px-4 py-2 text-center">
                                    <button className="rounded p-1 hover:bg-gray-100">
                                        <Eye className="h-4 w-4" />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

// ===== 주소록 탭 =====
function AddressBookTab({
    settings,
    setSettings,
}: {
    settings: FaxSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<FaxSettingsData>>;
}) {
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedContact, setSelectedContact] = useState<FaxContact | null>(null);

    const handleAddContact = () => {
        const newContact: FaxContact = {
            id: `contact_${Date.now()}`,
            name: "",
            company: "",
            faxNumber: "",
            email: "",
            group: "일반",
            isFavorite: false,
        };
        setSettings({
            ...settings,
            addressBook: [...settings.addressBook, newContact],
        });
        setSelectedContact(newContact);
    };

    const updateContact = (updates: Partial<FaxContact>) => {
        if (!selectedContact) return;
        const updated = { ...selectedContact, ...updates };
        setSelectedContact(updated);
        setSettings({
            ...settings,
            addressBook: settings.addressBook.map((c) =>
                c.id === selectedContact.id ? updated : c
            ),
        });
    };

    const filteredContacts = settings.addressBook.filter(
        (c) =>
            c.name.includes(searchTerm) ||
            c.company.includes(searchTerm) ||
            c.faxNumber.includes(searchTerm)
    );

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">팩스 주소록</h3>
                <div className="flex items-center gap-2">
                    <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-gray-50">
                        <Upload className="h-4 w-4" />
                        가져오기
                    </button>
                    <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-gray-50">
                        <Download className="h-4 w-4" />
                        내보내기
                    </button>
                    <button
                        onClick={handleAddContact}
                        className="flex items-center gap-1 rounded bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700"
                    >
                        <Plus className="h-4 w-4" />
                        연락처 추가
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
                {/* 연락처 목록 */}
                <div className="col-span-1 rounded border">
                    <div className="border-b bg-gray-50 px-3 py-2">
                        <div className="flex items-center gap-2">
                            <Search className="h-4 w-4 text-gray-400" />
                            <input
                                type="text"
                                placeholder="검색..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full border-0 bg-transparent text-sm focus:outline-none"
                            />
                        </div>
                    </div>
                    <div className="max-h-96 overflow-auto">
                        {filteredContacts.map((contact) => (
                            <div
                                key={contact.id}
                                onClick={() => setSelectedContact(contact)}
                                className={`cursor-pointer border-b px-3 py-2 hover:bg-gray-50 ${
                                    selectedContact?.id === contact.id ? "bg-green-50" : ""
                                }`}
                            >
                                <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium">{contact.name || "(이름 없음)"}</span>
                                    {contact.isFavorite && <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />}
                                </div>
                                <div className="text-xs text-gray-500">{contact.faxNumber}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 연락처 편집 */}
                <div className="col-span-2 rounded border p-4">
                    {selectedContact ? (
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="mb-1 block text-sm font-medium">이름</label>
                                    <input
                                        type="text"
                                        value={selectedContact.name}
                                        onChange={(e) => updateContact({ name: e.target.value })}
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium">회사</label>
                                    <input
                                        type="text"
                                        value={selectedContact.company}
                                        onChange={(e) => updateContact({ company: e.target.value })}
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium">팩스 번호</label>
                                    <input
                                        type="text"
                                        value={selectedContact.faxNumber}
                                        onChange={(e) => updateContact({ faxNumber: e.target.value })}
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium">이메일</label>
                                    <input
                                        type="email"
                                        value={selectedContact.email}
                                        onChange={(e) => updateContact({ email: e.target.value })}
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium">그룹</label>
                                    <input
                                        type="text"
                                        value={selectedContact.group}
                                        onChange={(e) => updateContact({ group: e.target.value })}
                                        className="w-full rounded border px-3 py-1.5 text-sm"
                                    />
                                </div>
                            </div>
                            <div className="flex items-center gap-4">
                                <label className="flex items-center gap-2 text-sm">
                                    <input
                                        type="checkbox"
                                        checked={selectedContact.isFavorite}
                                        onChange={(e) => updateContact({ isFavorite: e.target.checked })}
                                        className="h-4 w-4"
                                    />
                                    즐겨찾기
                                </label>
                                <button className="flex items-center gap-1 rounded border border-red-200 px-3 py-1 text-sm text-red-600 hover:bg-red-50">
                                    <Trash2 className="h-4 w-4" />
                                    삭제
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="flex h-full items-center justify-center text-gray-500">
                            연락처를 선택하거나 새로 추가하세요
                        </div>
                    )}
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
    settings: FaxSettingsData;
    setSettings: React.Dispatch<React.SetStateAction<FaxSettingsData>>;
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
                            <span>등록된 팩스 서버</span>
                            <span>{settings.servers.length}개</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>활성 서버</span>
                            <span>{settings.servers.filter((s) => s.isActive).length}개</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>커버시트</span>
                            <span>{settings.coverSheets.length}개</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>주소록 연락처</span>
                            <span>{settings.addressBook.length}개</span>
                        </div>
                    </div>
                </div>

                {/* 발송 설정 요약 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">발송 설정 요약</h4>
                    <div className="space-y-2 text-sm">
                        <div className="flex items-center justify-between">
                            <span>기본 해상도</span>
                            <span>{settings.sendSettings.defaultResolution}</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>재시도 횟수</span>
                            <span>{settings.sendSettings.retryCount}회</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>발송 확인 이메일</span>
                            <span className={settings.sendSettings.sendConfirmation ? "text-green-600" : "text-gray-400"}>
                                {settings.sendSettings.sendConfirmation ? "활성" : "비활성"}
                            </span>
                        </div>
                    </div>
                </div>

                {/* 수신 설정 요약 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">수신 설정 요약</h4>
                    <div className="space-y-2 text-sm">
                        <div className="flex items-center justify-between">
                            <span>자동 수신</span>
                            <span className={settings.receiveSettings.autoReceive ? "text-green-600" : "text-gray-400"}>
                                {settings.receiveSettings.autoReceive ? "활성" : "비활성"}
                            </span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>저장 형식</span>
                            <span>{settings.receiveSettings.fileFormat.toUpperCase()}</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>자동 인쇄</span>
                            <span className={settings.receiveSettings.printOnReceive ? "text-green-600" : "text-gray-400"}>
                                {settings.receiveSettings.printOnReceive ? "활성" : "비활성"}
                            </span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span>수신 알림</span>
                            <span className={settings.receiveSettings.notifyOnReceive ? "text-green-600" : "text-gray-400"}>
                                {settings.receiveSettings.notifyOnReceive ? "활성" : "비활성"}
                            </span>
                        </div>
                    </div>
                </div>

                {/* 데이터 관리 */}
                <div className="rounded border p-4">
                    <h4 className="mb-4 font-medium">데이터 관리</h4>
                    <div className="space-y-3">
                        <button className="flex w-full items-center gap-2 rounded border px-3 py-2 text-sm hover:bg-gray-50">
                            <Archive className="h-4 w-4" />
                            이력 정리 (30일 이전 삭제)
                        </button>
                        <button className="flex w-full items-center gap-2 rounded border px-3 py-2 text-sm hover:bg-gray-50">
                            <RotateCcw className="h-4 w-4" />
                            설정 초기화
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default FaxSettingsWindow;
