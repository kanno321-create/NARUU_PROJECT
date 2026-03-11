"use client";

import React, { useState, useEffect } from "react";
import {
    Save,
    RotateCcw,
    Printer,
    FileText,
    Settings,
    ChevronDown,
    ChevronRight,
    Plus,
    Trash2,
    Edit2,
    Copy,
    CheckCircle,
    AlertCircle,
    RefreshCw,
    Play,
    Pause,
    X,
    Layers,
    Layout,
    Maximize2,
    Grid,
    Image,
    Type,
    List,
    Clock,
    Monitor,
    Sliders,
    BookOpen,
    FileCheck,
    TestTube,
    Download,
    Upload,
} from "lucide-react";

// ============== 인터페이스 정의 ==============

interface PrinterDevice {
    id: string;
    name: string;
    displayName: string;
    isDefault: boolean;
    isOnline: boolean;
    status: "ready" | "printing" | "error" | "offline" | "paper_jam" | "low_ink";
    location?: string;
    model?: string;
    capabilities: {
        color: boolean;
        duplex: boolean;
        stapling: boolean;
        collating: boolean;
        maxPaperSize: string;
        supportedPaperSizes: string[];
        maxDpi: number;
    };
}

interface PaperSize {
    id: string;
    name: string;
    width: number;
    height: number;
    unit: "mm" | "inch";
    isCustom: boolean;
}

interface MarginPreset {
    id: string;
    name: string;
    top: number;
    bottom: number;
    left: number;
    right: number;
    gutter: number;
    headerMargin: number;
    footerMargin: number;
}

interface PrintQuality {
    id: string;
    name: string;
    dpi: number;
    description: string;
}

interface PrintProfile {
    id: string;
    name: string;
    documentType: "quote" | "taxInvoice" | "statement" | "report" | "label" | "envelope" | "custom";
    printerId: string;
    paperSize: string;
    orientation: "portrait" | "landscape";
    margins: MarginPreset;
    quality: PrintQuality;
    colorMode: "color" | "grayscale" | "blackWhite";
    duplex: "none" | "longEdge" | "shortEdge";
    copies: number;
    collate: boolean;
    pagesPerSheet: 1 | 2 | 4 | 6 | 9 | 16;
    scaling: "fit" | "actual" | "shrink" | "custom";
    customScale: number;
    pageRange: "all" | "current" | "custom";
    customPageRange: string;
    reverseOrder: boolean;
    header: {
        enabled: boolean;
        left: string;
        center: string;
        right: string;
    };
    footer: {
        enabled: boolean;
        left: string;
        center: string;
        right: string;
    };
    watermark: {
        enabled: boolean;
        text: string;
        opacity: number;
        angle: number;
        font: string;
        size: number;
        color: string;
    };
    isDefault: boolean;
    createdAt: string;
    updatedAt: string;
}

interface PrintJob {
    id: string;
    documentName: string;
    documentType: string;
    printerId: string;
    printerName: string;
    status: "queued" | "printing" | "paused" | "completed" | "failed" | "cancelled";
    pages: number;
    copies: number;
    submittedAt: string;
    startedAt?: string;
    completedAt?: string;
    errorMessage?: string;
    progress: number;
}

interface PrintSettings {
    printers: PrinterDevice[];
    defaultPrinterId: string;
    documentTypePrinters: Record<string, string>;
    paperSizes: PaperSize[];
    marginPresets: MarginPreset[];
    qualityPresets: PrintQuality[];
    profiles: PrintProfile[];
    defaultProfileId: string;
    printQueue: PrintJob[];
    printHistory: PrintJob[];
    options: {
        showPrintPreview: boolean;
        confirmBeforePrint: boolean;
        saveLastSettings: boolean;
        autoSelectTray: boolean;
        inkSaverMode: boolean;
        quietMode: boolean;
        bannerPage: boolean;
        printBackground: boolean;
        printImages: boolean;
    };
    statistics: {
        totalPrinted: number;
        monthlyPrinted: number;
        paperUsed: number;
        colorPages: number;
        bwPages: number;
    };
}

// ============== 기본값 정의 ==============

const defaultPaperSizes: PaperSize[] = [
    { id: "a4", name: "A4", width: 210, height: 297, unit: "mm", isCustom: false },
    { id: "a5", name: "A5", width: 148, height: 210, unit: "mm", isCustom: false },
    { id: "a3", name: "A3", width: 297, height: 420, unit: "mm", isCustom: false },
    { id: "b5", name: "B5", width: 176, height: 250, unit: "mm", isCustom: false },
    { id: "letter", name: "Letter", width: 8.5, height: 11, unit: "inch", isCustom: false },
    { id: "legal", name: "Legal", width: 8.5, height: 14, unit: "inch", isCustom: false },
    { id: "envelope_c5", name: "봉투 C5", width: 162, height: 229, unit: "mm", isCustom: false },
    { id: "envelope_dl", name: "봉투 DL", width: 110, height: 220, unit: "mm", isCustom: false },
    { id: "label_a4", name: "라벨 A4", width: 210, height: 297, unit: "mm", isCustom: false },
];

const defaultMarginPresets: MarginPreset[] = [
    { id: "normal", name: "보통", top: 25.4, bottom: 25.4, left: 25.4, right: 25.4, gutter: 0, headerMargin: 12.7, footerMargin: 12.7 },
    { id: "narrow", name: "좁게", top: 12.7, bottom: 12.7, left: 12.7, right: 12.7, gutter: 0, headerMargin: 12.7, footerMargin: 12.7 },
    { id: "wide", name: "넓게", top: 25.4, bottom: 25.4, left: 50.8, right: 50.8, gutter: 0, headerMargin: 12.7, footerMargin: 12.7 },
    { id: "moderate", name: "중간", top: 25.4, bottom: 25.4, left: 19.05, right: 19.05, gutter: 0, headerMargin: 12.7, footerMargin: 12.7 },
    { id: "mirrored", name: "미러 (제본용)", top: 25.4, bottom: 25.4, left: 31.75, right: 25.4, gutter: 12.7, headerMargin: 12.7, footerMargin: 12.7 },
];

const defaultQualityPresets: PrintQuality[] = [
    { id: "draft", name: "초안", dpi: 150, description: "빠른 인쇄, 낮은 품질" },
    { id: "normal", name: "일반", dpi: 300, description: "일상적인 문서용" },
    { id: "high", name: "고품질", dpi: 600, description: "프리젠테이션, 이미지용" },
    { id: "photo", name: "사진", dpi: 1200, description: "사진 인쇄용 최고 품질" },
];

const defaultPrinter: PrinterDevice = {
    id: "default_printer",
    name: "Microsoft Print to PDF",
    displayName: "PDF로 인쇄",
    isDefault: true,
    isOnline: true,
    status: "ready",
    location: "로컬",
    model: "PDF 프린터",
    capabilities: {
        color: true,
        duplex: false,
        stapling: false,
        collating: true,
        maxPaperSize: "A3",
        supportedPaperSizes: ["A4", "A5", "A3", "Letter", "Legal"],
        maxDpi: 1200,
    },
};

const createDefaultProfile = (type: PrintProfile["documentType"]): PrintProfile => ({
    id: `profile_${type}_${Date.now()}`,
    name: type === "quote" ? "견적서" : type === "taxInvoice" ? "세금계산서" : type === "statement" ? "거래명세서" : type === "report" ? "보고서" : type === "label" ? "라벨" : type === "envelope" ? "봉투" : "사용자 정의",
    documentType: type,
    printerId: "",
    paperSize: "a4",
    orientation: "portrait",
    margins: defaultMarginPresets[0],
    quality: defaultQualityPresets[1],
    colorMode: "blackWhite",
    duplex: "none",
    copies: 1,
    collate: true,
    pagesPerSheet: 1,
    scaling: "fit",
    customScale: 100,
    pageRange: "all",
    customPageRange: "",
    reverseOrder: false,
    header: { enabled: false, left: "", center: "", right: "" },
    footer: { enabled: true, left: "", center: "{page} / {pages}", right: "" },
    watermark: { enabled: false, text: "", opacity: 30, angle: -45, font: "맑은 고딕", size: 48, color: "#CCCCCC" },
    isDefault: false,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
});

const defaultSettings: PrintSettings = {
    printers: [defaultPrinter],
    defaultPrinterId: defaultPrinter.id,
    documentTypePrinters: {},
    paperSizes: defaultPaperSizes,
    marginPresets: defaultMarginPresets,
    qualityPresets: defaultQualityPresets,
    profiles: [
        { ...createDefaultProfile("quote"), isDefault: true },
        createDefaultProfile("taxInvoice"),
        createDefaultProfile("statement"),
        createDefaultProfile("report"),
    ],
    defaultProfileId: "",
    printQueue: [],
    printHistory: [],
    options: {
        showPrintPreview: true,
        confirmBeforePrint: true,
        saveLastSettings: true,
        autoSelectTray: true,
        inkSaverMode: false,
        quietMode: false,
        bannerPage: false,
        printBackground: true,
        printImages: true,
    },
    statistics: {
        totalPrinted: 0,
        monthlyPrinted: 0,
        paperUsed: 0,
        colorPages: 0,
        bwPages: 0,
    },
};

// ============== 메인 컴포넌트 ==============

export function PrintSettingsWindow() {
    const [activeTab, setActiveTab] = useState<"printers" | "paper" | "profiles" | "queue" | "options">("printers");
    const [settings, setSettings] = useState<PrintSettings>(defaultSettings);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
    const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
        printerList: true,
        printerSettings: true,
        paperSizes: true,
        margins: true,
        quality: true,
        profiles: true,
        queue: true,
        history: false,
        generalOptions: true,
        advancedOptions: false,
    });
    const [editingProfile, setEditingProfile] = useState<PrintProfile | null>(null);
    const [selectedPrinter, setSelectedPrinter] = useState<PrinterDevice | null>(null);
    const [testPrintStatus, setTestPrintStatus] = useState<"idle" | "printing" | "success" | "error">("idle");

    // 설정 불러오기
    useEffect(() => {
        const saved = localStorage.getItem("erp_print_settings");
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                setSettings({ ...defaultSettings, ...parsed });
            } catch (e) {
                console.error("프린트 설정 불러오기 실패:", e);
            }
        }
    }, []);

    // 설정 저장
    const handleSave = async () => {
        setSaving(true);
        try {
            localStorage.setItem("erp_print_settings", JSON.stringify(settings));
            window.dispatchEvent(new CustomEvent("kis-erp-settings-updated"));
            setMessage({ type: "success", text: "프린트 설정이 저장되었습니다." });
            setTimeout(() => setMessage(null), 3000);
        } catch (error) {
            setMessage({ type: "error", text: "저장에 실패했습니다." });
        } finally {
            setSaving(false);
        }
    };

    // 초기화
    const handleReset = () => {
        if (confirm("모든 프린트 설정을 초기화하시겠습니까?")) {
            setSettings(defaultSettings);
        }
    };

    // 섹션 토글
    const toggleSection = (section: string) => {
        setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
    };

    // 프린터 새로고침 시뮬레이션
    const refreshPrinters = () => {
        setMessage({ type: "success", text: "프린터 목록을 새로고침했습니다." });
    };

    // 테스트 인쇄
    const handleTestPrint = () => {
        setTestPrintStatus("printing");
        setTimeout(() => {
            setTestPrintStatus("success");
            setTimeout(() => setTestPrintStatus("idle"), 2000);
        }, 1500);
    };

    // 기본 프린터 설정
    const setDefaultPrinter = (printerId: string) => {
        setSettings(prev => ({
            ...prev,
            defaultPrinterId: printerId,
            printers: prev.printers.map(p => ({
                ...p,
                isDefault: p.id === printerId,
            })),
        }));
    };

    // 문서 유형별 프린터 설정
    const setDocumentTypePrinter = (docType: string, printerId: string) => {
        setSettings(prev => ({
            ...prev,
            documentTypePrinters: {
                ...prev.documentTypePrinters,
                [docType]: printerId,
            },
        }));
    };

    // 프로파일 저장
    const handleSaveProfile = (profile: PrintProfile) => {
        setSettings(prev => ({
            ...prev,
            profiles: editingProfile?.id && prev.profiles.find(p => p.id === editingProfile.id)
                ? prev.profiles.map(p => p.id === profile.id ? { ...profile, updatedAt: new Date().toISOString() } : p)
                : [...prev.profiles, { ...profile, id: `profile_${Date.now()}`, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() }],
        }));
        setEditingProfile(null);
    };

    // 프로파일 삭제
    const handleDeleteProfile = (profileId: string) => {
        if (confirm("프로파일을 삭제하시겠습니까?")) {
            setSettings(prev => ({
                ...prev,
                profiles: prev.profiles.filter(p => p.id !== profileId),
            }));
        }
    };

    // 인쇄 작업 관리
    const handleJobAction = (jobId: string, action: "pause" | "resume" | "cancel") => {
        setSettings(prev => ({
            ...prev,
            printQueue: prev.printQueue.map(job => {
                if (job.id !== jobId) return job;
                switch (action) {
                    case "pause": return { ...job, status: "paused" as const };
                    case "resume": return { ...job, status: "printing" as const };
                    case "cancel": return { ...job, status: "cancelled" as const };
                    default: return job;
                }
            }).filter(job => job.status !== "cancelled"),
        }));
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

    // 프린터 상태 아이콘
    const PrinterStatusIcon = ({ status }: { status: PrinterDevice["status"] }) => {
        switch (status) {
            case "ready": return <CheckCircle className="h-4 w-4 text-green-500" />;
            case "printing": return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />;
            case "error":
            case "paper_jam":
            case "low_ink": return <AlertCircle className="h-4 w-4 text-red-500" />;
            case "offline": return <Monitor className="h-4 w-4 text-gray-400" />;
            default: return <Monitor className="h-4 w-4 text-gray-400" />;
        }
    };

    const statusLabels: Record<string, string> = {
        ready: "준비됨",
        printing: "인쇄 중",
        error: "오류",
        offline: "오프라인",
        paper_jam: "용지 걸림",
        low_ink: "잉크 부족",
    };

    const documentTypeLabels: Record<string, string> = {
        quote: "견적서",
        taxInvoice: "세금계산서",
        statement: "거래명세서",
        report: "보고서",
        label: "라벨",
        envelope: "봉투",
        custom: "사용자 정의",
    };

    // ============== 탭 목록 ==============
    const tabs = [
        { id: "printers" as const, label: "프린터 관리", icon: Printer },
        { id: "paper" as const, label: "용지/여백", icon: Layout },
        { id: "profiles" as const, label: "인쇄 프로파일", icon: FileCheck },
        { id: "queue" as const, label: "인쇄 대기열", icon: List },
        { id: "options" as const, label: "인쇄 옵션", icon: Settings },
    ];

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
                    <div className="mx-2 h-6 w-px bg-border" />
                    <button
                        onClick={refreshPrinters}
                        className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"
                    >
                        <RefreshCw className="h-4 w-4" />
                        프린터 새로고침
                    </button>
                    <button
                        onClick={handleTestPrint}
                        disabled={testPrintStatus === "printing"}
                        className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"
                    >
                        <TestTube className="h-4 w-4" />
                        {testPrintStatus === "printing" ? "인쇄 중..." : testPrintStatus === "success" ? "성공!" : "테스트 인쇄"}
                    </button>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-4 text-sm">
                        <span className="text-text-subtle">
                            총 인쇄: <span className="font-medium text-text">{settings.statistics.totalPrinted.toLocaleString()}매</span>
                        </span>
                        <span className="text-text-subtle">
                            대기: <span className="font-medium text-brand">{settings.printQueue.length}건</span>
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
                                {tab.id === "queue" && settings.printQueue.length > 0 && (
                                    <span className={`ml-auto text-xs px-1.5 py-0.5 rounded-full ${activeTab === tab.id ? "bg-white/20" : "bg-brand text-white"}`}>
                                        {settings.printQueue.length}
                                    </span>
                                )}
                            </button>
                        );
                    })}
                </div>

                {/* 설정 내용 */}
                <div className="flex-1 overflow-auto p-4">
                    {/* 프린터 관리 */}
                    {activeTab === "printers" && (
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold">프린터 관리</h3>

                            {/* 프린터 목록 */}
                            <SectionHeader title="설치된 프린터" section="printerList" icon={Printer} />
                            {expandedSections.printerList && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    {settings.printers.map((printer) => (
                                        <div
                                            key={printer.id}
                                            className={`rounded-lg border p-4 cursor-pointer transition-colors ${
                                                selectedPrinter?.id === printer.id ? "border-brand bg-brand/5" : "hover:bg-surface-secondary"
                                            }`}
                                            onClick={() => setSelectedPrinter(printer)}
                                        >
                                            <div className="flex items-start justify-between">
                                                <div className="flex items-start gap-3">
                                                    <div className="p-2 rounded-lg bg-surface-secondary">
                                                        <Printer className="h-6 w-6 text-text-subtle" />
                                                    </div>
                                                    <div>
                                                        <div className="flex items-center gap-2">
                                                            <h4 className="font-medium">{printer.displayName}</h4>
                                                            {printer.isDefault && (
                                                                <span className="text-xs px-2 py-0.5 rounded bg-brand/10 text-brand">기본</span>
                                                            )}
                                                        </div>
                                                        <p className="text-sm text-text-subtle">{printer.name}</p>
                                                        <div className="flex items-center gap-4 mt-1 text-xs text-text-subtle">
                                                            {printer.location && <span>위치: {printer.location}</span>}
                                                            {printer.model && <span>모델: {printer.model}</span>}
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <PrinterStatusIcon status={printer.status} />
                                                    <span className={`text-sm ${printer.status === "ready" ? "text-green-600" : printer.status === "offline" ? "text-gray-500" : "text-red-600"}`}>
                                                        {statusLabels[printer.status]}
                                                    </span>
                                                </div>
                                            </div>
                                            {/* 프린터 기능 */}
                                            <div className="mt-3 flex items-center gap-2 flex-wrap">
                                                {printer.capabilities.color && (
                                                    <span className="text-xs px-2 py-0.5 rounded bg-surface-secondary">컬러</span>
                                                )}
                                                {printer.capabilities.duplex && (
                                                    <span className="text-xs px-2 py-0.5 rounded bg-surface-secondary">양면인쇄</span>
                                                )}
                                                {printer.capabilities.stapling && (
                                                    <span className="text-xs px-2 py-0.5 rounded bg-surface-secondary">스테이플</span>
                                                )}
                                                <span className="text-xs px-2 py-0.5 rounded bg-surface-secondary">
                                                    최대 {printer.capabilities.maxDpi} DPI
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* 프린터 설정 */}
                            <SectionHeader title="프린터 설정" section="printerSettings" icon={Settings} />
                            {expandedSections.printerSettings && (
                                <div className="ml-6 space-y-4 border-l-2 border-brand/20 pl-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-2">기본 프린터</label>
                                        <select
                                            value={settings.defaultPrinterId}
                                            onChange={(e) => setDefaultPrinter(e.target.value)}
                                            className="w-full rounded border px-3 py-2 text-sm"
                                        >
                                            {settings.printers.map((printer) => (
                                                <option key={printer.id} value={printer.id}>
                                                    {printer.displayName} {!printer.isOnline && "(오프라인)"}
                                                </option>
                                            ))}
                                        </select>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium mb-2">문서 유형별 프린터 지정</label>
                                        <div className="space-y-2">
                                            {["quote", "taxInvoice", "statement", "report"].map((docType) => (
                                                <div key={docType} className="flex items-center gap-4">
                                                    <span className="w-24 text-sm">{documentTypeLabels[docType]}</span>
                                                    <select
                                                        value={settings.documentTypePrinters[docType] || ""}
                                                        onChange={(e) => setDocumentTypePrinter(docType, e.target.value)}
                                                        className="flex-1 rounded border px-3 py-2 text-sm"
                                                    >
                                                        <option value="">기본 프린터 사용</option>
                                                        {settings.printers.map((printer) => (
                                                            <option key={printer.id} value={printer.id}>
                                                                {printer.displayName}
                                                            </option>
                                                        ))}
                                                    </select>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* 용지/여백 설정 */}
                    {activeTab === "paper" && (
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold">용지/여백 설정</h3>

                            {/* 용지 크기 */}
                            <SectionHeader title="용지 크기" section="paperSizes" icon={Layout} />
                            {expandedSections.paperSizes && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <div className="grid grid-cols-3 gap-3">
                                        {settings.paperSizes.map((paper) => (
                                            <div key={paper.id} className="rounded border p-3">
                                                <div className="flex items-center justify-between mb-1">
                                                    <span className="font-medium text-sm">{paper.name}</span>
                                                    {paper.isCustom && (
                                                        <button className="text-red-500 hover:text-red-700">
                                                            <Trash2 className="h-3 w-3" />
                                                        </button>
                                                    )}
                                                </div>
                                                <p className="text-xs text-text-subtle">
                                                    {paper.width} × {paper.height} {paper.unit}
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                    <button
                                        className="flex items-center gap-1 rounded border px-3 py-2 text-sm hover:bg-surface-secondary"
                                    >
                                        <Plus className="h-4 w-4" />
                                        사용자 정의 용지 추가
                                    </button>
                                </div>
                            )}

                            {/* 여백 설정 */}
                            <SectionHeader title="여백 프리셋" section="margins" icon={Maximize2} />
                            {expandedSections.margins && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        {settings.marginPresets.map((margin) => (
                                            <div key={margin.id} className="rounded border p-4">
                                                <div className="flex items-center justify-between mb-2">
                                                    <span className="font-medium">{margin.name}</span>
                                                    <button
                                                        className="text-text-subtle hover:text-text"
                                                    >
                                                        <Edit2 className="h-4 w-4" />
                                                    </button>
                                                </div>
                                                <div className="grid grid-cols-2 gap-2 text-xs text-text-subtle">
                                                    <span>상: {margin.top}mm</span>
                                                    <span>하: {margin.bottom}mm</span>
                                                    <span>좌: {margin.left}mm</span>
                                                    <span>우: {margin.right}mm</span>
                                                </div>
                                                {margin.gutter > 0 && (
                                                    <p className="text-xs text-text-subtle mt-1">제본 여백: {margin.gutter}mm</p>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                    <button
                                        className="flex items-center gap-1 rounded border px-3 py-2 text-sm hover:bg-surface-secondary"
                                    >
                                        <Plus className="h-4 w-4" />
                                        사용자 정의 여백 추가
                                    </button>
                                </div>
                            )}

                            {/* 인쇄 품질 */}
                            <SectionHeader title="인쇄 품질 프리셋" section="quality" icon={Sliders} />
                            {expandedSections.quality && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        {settings.qualityPresets.map((quality) => (
                                            <div key={quality.id} className="rounded border p-4">
                                                <div className="flex items-center justify-between mb-1">
                                                    <span className="font-medium">{quality.name}</span>
                                                    <span className="text-sm text-brand">{quality.dpi} DPI</span>
                                                </div>
                                                <p className="text-xs text-text-subtle">{quality.description}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* 인쇄 프로파일 */}
                    {activeTab === "profiles" && (
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-semibold">인쇄 프로파일</h3>
                                <div className="flex items-center gap-2">
                                    <button
                                        className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"
                                    >
                                        <Upload className="h-4 w-4" />
                                        가져오기
                                    </button>
                                    <button
                                        className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"
                                    >
                                        <Download className="h-4 w-4" />
                                        내보내기
                                    </button>
                                    <button
                                        onClick={() => setEditingProfile(createDefaultProfile("custom"))}
                                        className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"
                                    >
                                        <Plus className="h-4 w-4" />
                                        새 프로파일
                                    </button>
                                </div>
                            </div>

                            {/* 프로파일 편집 모달 */}
                            {editingProfile && (
                                <div className="rounded-lg border bg-surface-secondary p-4 space-y-4">
                                    <h4 className="font-medium">{editingProfile.id ? "프로파일 수정" : "새 프로파일"}</h4>
                                    <div className="grid grid-cols-3 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">프로파일 이름</label>
                                            <input
                                                type="text"
                                                value={editingProfile.name}
                                                onChange={(e) => setEditingProfile({ ...editingProfile, name: e.target.value })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">문서 유형</label>
                                            <select
                                                value={editingProfile.documentType}
                                                onChange={(e) => setEditingProfile({ ...editingProfile, documentType: e.target.value as PrintProfile["documentType"] })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                {Object.entries(documentTypeLabels).map(([key, label]) => (
                                                    <option key={key} value={key}>{label}</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">프린터</label>
                                            <select
                                                value={editingProfile.printerId}
                                                onChange={(e) => setEditingProfile({ ...editingProfile, printerId: e.target.value })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                <option value="">기본 프린터</option>
                                                {settings.printers.map((printer) => (
                                                    <option key={printer.id} value={printer.id}>{printer.displayName}</option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-4 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">용지 크기</label>
                                            <select
                                                value={editingProfile.paperSize}
                                                onChange={(e) => setEditingProfile({ ...editingProfile, paperSize: e.target.value })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                {settings.paperSizes.map((paper) => (
                                                    <option key={paper.id} value={paper.id}>{paper.name}</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">용지 방향</label>
                                            <select
                                                value={editingProfile.orientation}
                                                onChange={(e) => setEditingProfile({ ...editingProfile, orientation: e.target.value as "portrait" | "landscape" })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                <option value="portrait">세로</option>
                                                <option value="landscape">가로</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">색상 모드</label>
                                            <select
                                                value={editingProfile.colorMode}
                                                onChange={(e) => setEditingProfile({ ...editingProfile, colorMode: e.target.value as "color" | "grayscale" | "blackWhite" })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                <option value="color">컬러</option>
                                                <option value="grayscale">그레이스케일</option>
                                                <option value="blackWhite">흑백</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">양면 인쇄</label>
                                            <select
                                                value={editingProfile.duplex}
                                                onChange={(e) => setEditingProfile({ ...editingProfile, duplex: e.target.value as "none" | "longEdge" | "shortEdge" })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                <option value="none">단면</option>
                                                <option value="longEdge">양면 (긴 가장자리)</option>
                                                <option value="shortEdge">양면 (짧은 가장자리)</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-4 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">매수</label>
                                            <input
                                                type="number"
                                                min="1"
                                                max="999"
                                                value={editingProfile.copies}
                                                onChange={(e) => setEditingProfile({ ...editingProfile, copies: Number(e.target.value) })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">한 면에 페이지</label>
                                            <select
                                                value={editingProfile.pagesPerSheet}
                                                onChange={(e) => setEditingProfile({ ...editingProfile, pagesPerSheet: Number(e.target.value) as PrintProfile["pagesPerSheet"] })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                <option value="1">1</option>
                                                <option value="2">2</option>
                                                <option value="4">4</option>
                                                <option value="6">6</option>
                                                <option value="9">9</option>
                                                <option value="16">16</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">크기 조정</label>
                                            <select
                                                value={editingProfile.scaling}
                                                onChange={(e) => setEditingProfile({ ...editingProfile, scaling: e.target.value as PrintProfile["scaling"] })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                <option value="fit">용지에 맞춤</option>
                                                <option value="actual">실제 크기</option>
                                                <option value="shrink">축소 맞춤</option>
                                                <option value="custom">사용자 지정</option>
                                            </select>
                                        </div>
                                        {editingProfile.scaling === "custom" && (
                                            <div>
                                                <label className="block text-sm font-medium mb-1">배율 (%)</label>
                                                <input
                                                    type="number"
                                                    min="10"
                                                    max="400"
                                                    value={editingProfile.customScale}
                                                    onChange={(e) => setEditingProfile({ ...editingProfile, customScale: Number(e.target.value) })}
                                                    className="w-full rounded border px-3 py-2 text-sm"
                                                />
                                            </div>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-6">
                                        <label className="flex items-center gap-2">
                                            <input
                                                type="checkbox"
                                                checked={editingProfile.collate}
                                                onChange={(e) => setEditingProfile({ ...editingProfile, collate: e.target.checked })}
                                                className="h-4 w-4"
                                            />
                                            <span className="text-sm">한 부씩 인쇄</span>
                                        </label>
                                        <label className="flex items-center gap-2">
                                            <input
                                                type="checkbox"
                                                checked={editingProfile.reverseOrder}
                                                onChange={(e) => setEditingProfile({ ...editingProfile, reverseOrder: e.target.checked })}
                                                className="h-4 w-4"
                                            />
                                            <span className="text-sm">역순 인쇄</span>
                                        </label>
                                        <label className="flex items-center gap-2">
                                            <input
                                                type="checkbox"
                                                checked={editingProfile.isDefault}
                                                onChange={(e) => setEditingProfile({ ...editingProfile, isDefault: e.target.checked })}
                                                className="h-4 w-4"
                                            />
                                            <span className="text-sm">기본 프로파일로 설정</span>
                                        </label>
                                    </div>

                                    {/* 워터마크 설정 */}
                                    <div className="rounded border p-3">
                                        <label className="flex items-center gap-2 mb-3">
                                            <input
                                                type="checkbox"
                                                checked={editingProfile.watermark.enabled}
                                                onChange={(e) => setEditingProfile({
                                                    ...editingProfile,
                                                    watermark: { ...editingProfile.watermark, enabled: e.target.checked }
                                                })}
                                                className="h-4 w-4"
                                            />
                                            <span className="text-sm font-medium">워터마크 사용</span>
                                        </label>
                                        {editingProfile.watermark.enabled && (
                                            <div className="grid grid-cols-4 gap-4">
                                                <div className="col-span-2">
                                                    <label className="block text-xs mb-1">텍스트</label>
                                                    <input
                                                        type="text"
                                                        value={editingProfile.watermark.text}
                                                        onChange={(e) => setEditingProfile({
                                                            ...editingProfile,
                                                            watermark: { ...editingProfile.watermark, text: e.target.value }
                                                        })}
                                                        className="w-full rounded border px-2 py-1 text-sm"
                                                        placeholder="예: 대외비"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="block text-xs mb-1">투명도 (%)</label>
                                                    <input
                                                        type="number"
                                                        min="0"
                                                        max="100"
                                                        value={editingProfile.watermark.opacity}
                                                        onChange={(e) => setEditingProfile({
                                                            ...editingProfile,
                                                            watermark: { ...editingProfile.watermark, opacity: Number(e.target.value) }
                                                        })}
                                                        className="w-full rounded border px-2 py-1 text-sm"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="block text-xs mb-1">각도</label>
                                                    <input
                                                        type="number"
                                                        min="-90"
                                                        max="90"
                                                        value={editingProfile.watermark.angle}
                                                        onChange={(e) => setEditingProfile({
                                                            ...editingProfile,
                                                            watermark: { ...editingProfile.watermark, angle: Number(e.target.value) }
                                                        })}
                                                        className="w-full rounded border px-2 py-1 text-sm"
                                                    />
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    <div className="flex justify-end gap-2">
                                        <button
                                            onClick={() => setEditingProfile(null)}
                                            className="rounded border px-4 py-2 text-sm hover:bg-surface"
                                        >
                                            취소
                                        </button>
                                        <button
                                            onClick={() => handleSaveProfile(editingProfile)}
                                            className="rounded bg-brand px-4 py-2 text-sm text-white hover:bg-brand-dark"
                                        >
                                            저장
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* 프로파일 목록 */}
                            <div className="grid gap-3">
                                {settings.profiles.map((profile) => (
                                    <div key={profile.id} className="rounded-lg border p-4">
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <h4 className="font-medium">{profile.name}</h4>
                                                    <span className="text-xs px-2 py-0.5 rounded bg-surface-secondary">
                                                        {documentTypeLabels[profile.documentType]}
                                                    </span>
                                                    {profile.isDefault && (
                                                        <span className="text-xs px-2 py-0.5 rounded bg-brand/10 text-brand">기본</span>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-4 text-sm text-text-subtle">
                                                    <span>{settings.paperSizes.find(p => p.id === profile.paperSize)?.name || profile.paperSize}</span>
                                                    <span>{profile.orientation === "portrait" ? "세로" : "가로"}</span>
                                                    <span>{profile.colorMode === "color" ? "컬러" : profile.colorMode === "grayscale" ? "그레이스케일" : "흑백"}</span>
                                                    <span>{profile.duplex === "none" ? "단면" : "양면"}</span>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <button
                                                    onClick={() => setEditingProfile(profile)}
                                                    className="p-1.5 rounded hover:bg-surface-secondary"
                                                >
                                                    <Edit2 className="h-4 w-4" />
                                                </button>
                                                <button
                                                    onClick={() => handleSaveProfile({ ...profile, id: "", name: `${profile.name} (복사)`, isDefault: false })}
                                                    className="p-1.5 rounded hover:bg-surface-secondary"
                                                >
                                                    <Copy className="h-4 w-4" />
                                                </button>
                                                {!profile.isDefault && (
                                                    <button
                                                        onClick={() => handleDeleteProfile(profile.id)}
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

                    {/* 인쇄 대기열 */}
                    {activeTab === "queue" && (
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold">인쇄 대기열</h3>

                            {/* 대기열 */}
                            <SectionHeader title="대기 중인 작업" section="queue" icon={List} />
                            {expandedSections.queue && (
                                <div className="ml-6 border-l-2 border-brand/20 pl-4">
                                    {settings.printQueue.length === 0 ? (
                                        <div className="rounded-lg border border-dashed p-8 text-center">
                                            <Printer className="h-12 w-12 mx-auto text-text-subtle mb-2" />
                                            <p className="text-text-subtle">대기 중인 인쇄 작업이 없습니다.</p>
                                        </div>
                                    ) : (
                                        <div className="space-y-2">
                                            {settings.printQueue.map((job) => (
                                                <div key={job.id} className="rounded border p-3">
                                                    <div className="flex items-center justify-between mb-2">
                                                        <div>
                                                            <span className="font-medium">{job.documentName}</span>
                                                            <span className="text-sm text-text-subtle ml-2">({job.pages}페이지 × {job.copies}부)</span>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <span className={`text-xs px-2 py-0.5 rounded ${
                                                                job.status === "printing" ? "bg-blue-100 text-blue-700" :
                                                                job.status === "paused" ? "bg-yellow-100 text-yellow-700" :
                                                                job.status === "failed" ? "bg-red-100 text-red-700" :
                                                                "bg-gray-100 text-gray-700"
                                                            }`}>
                                                                {job.status === "printing" ? "인쇄 중" :
                                                                 job.status === "paused" ? "일시정지" :
                                                                 job.status === "queued" ? "대기" :
                                                                 job.status === "failed" ? "실패" : job.status}
                                                            </span>
                                                            <div className="flex items-center gap-1">
                                                                {job.status === "printing" && (
                                                                    <button
                                                                        onClick={() => handleJobAction(job.id, "pause")}
                                                                        className="p-1 rounded hover:bg-surface-secondary"
                                                                    >
                                                                        <Pause className="h-4 w-4" />
                                                                    </button>
                                                                )}
                                                                {job.status === "paused" && (
                                                                    <button
                                                                        onClick={() => handleJobAction(job.id, "resume")}
                                                                        className="p-1 rounded hover:bg-surface-secondary"
                                                                    >
                                                                        <Play className="h-4 w-4" />
                                                                    </button>
                                                                )}
                                                                <button
                                                                    onClick={() => handleJobAction(job.id, "cancel")}
                                                                    className="p-1 rounded hover:bg-surface-secondary text-red-500"
                                                                >
                                                                    <X className="h-4 w-4" />
                                                                </button>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    {job.status === "printing" && (
                                                        <div className="w-full bg-gray-200 rounded-full h-2">
                                                            <div
                                                                className="bg-brand h-2 rounded-full transition-all"
                                                                style={{ width: `${job.progress}%` }}
                                                            />
                                                        </div>
                                                    )}
                                                    <div className="flex items-center gap-4 mt-2 text-xs text-text-subtle">
                                                        <span>프린터: {job.printerName}</span>
                                                        <span>제출: {new Date(job.submittedAt).toLocaleString()}</span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* 인쇄 기록 */}
                            <SectionHeader title="인쇄 기록" section="history" icon={Clock} />
                            {expandedSections.history && (
                                <div className="ml-6 border-l-2 border-brand/20 pl-4">
                                    {settings.printHistory.length === 0 ? (
                                        <p className="text-sm text-text-subtle py-4">인쇄 기록이 없습니다.</p>
                                    ) : (
                                        <div className="rounded-lg border overflow-hidden">
                                            <table className="w-full text-sm">
                                                <thead className="bg-surface-secondary">
                                                    <tr>
                                                        <th className="px-4 py-2 text-left">문서명</th>
                                                        <th className="px-4 py-2 text-left">프린터</th>
                                                        <th className="px-4 py-2 text-right">페이지</th>
                                                        <th className="px-4 py-2 text-left">상태</th>
                                                        <th className="px-4 py-2 text-left">완료 시간</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {settings.printHistory.map((job) => (
                                                        <tr key={job.id} className="border-t">
                                                            <td className="px-4 py-2">{job.documentName}</td>
                                                            <td className="px-4 py-2">{job.printerName}</td>
                                                            <td className="px-4 py-2 text-right">{job.pages}</td>
                                                            <td className="px-4 py-2">
                                                                <span className={`text-xs px-2 py-0.5 rounded ${
                                                                    job.status === "completed" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                                                                }`}>
                                                                    {job.status === "completed" ? "완료" : "실패"}
                                                                </span>
                                                            </td>
                                                            <td className="px-4 py-2">{job.completedAt ? new Date(job.completedAt).toLocaleString() : "-"}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {/* 인쇄 옵션 */}
                    {activeTab === "options" && (
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold">인쇄 옵션</h3>

                            {/* 일반 옵션 */}
                            <SectionHeader title="일반 설정" section="generalOptions" icon={Settings} />
                            {expandedSections.generalOptions && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        {[
                                            { key: "showPrintPreview", label: "인쇄 전 미리보기 표시" },
                                            { key: "confirmBeforePrint", label: "인쇄 전 확인 대화상자 표시" },
                                            { key: "saveLastSettings", label: "마지막 인쇄 설정 기억" },
                                            { key: "autoSelectTray", label: "용지함 자동 선택" },
                                        ].map(({ key, label }) => (
                                            <label key={key} className="flex items-center gap-2">
                                                <input
                                                    type="checkbox"
                                                    checked={settings.options[key as keyof typeof settings.options] as boolean}
                                                    onChange={(e) => setSettings(prev => ({
                                                        ...prev,
                                                        options: { ...prev.options, [key]: e.target.checked }
                                                    }))}
                                                    className="h-4 w-4"
                                                />
                                                <span className="text-sm">{label}</span>
                                            </label>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* 고급 옵션 */}
                            <SectionHeader title="고급 설정" section="advancedOptions" icon={Sliders} />
                            {expandedSections.advancedOptions && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        {[
                                            { key: "inkSaverMode", label: "잉크/토너 절약 모드", description: "인쇄 농도를 낮춰 잉크 사용량 절감" },
                                            { key: "quietMode", label: "저소음 모드", description: "인쇄 속도를 낮춰 소음 감소" },
                                            { key: "bannerPage", label: "표지 페이지 인쇄", description: "각 인쇄 작업 앞에 분리 페이지 추가" },
                                            { key: "printBackground", label: "배경색 인쇄", description: "문서의 배경색도 함께 인쇄" },
                                            { key: "printImages", label: "이미지 인쇄", description: "문서에 포함된 이미지 인쇄" },
                                        ].map(({ key, label, description }) => (
                                            <div key={key} className="rounded border p-3">
                                                <label className="flex items-start gap-2">
                                                    <input
                                                        type="checkbox"
                                                        checked={settings.options[key as keyof typeof settings.options] as boolean}
                                                        onChange={(e) => setSettings(prev => ({
                                                            ...prev,
                                                            options: { ...prev.options, [key]: e.target.checked }
                                                        }))}
                                                        className="h-4 w-4 mt-0.5"
                                                    />
                                                    <div>
                                                        <span className="text-sm font-medium">{label}</span>
                                                        <p className="text-xs text-text-subtle">{description}</p>
                                                    </div>
                                                </label>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* 통계 */}
                            <div className="rounded-lg border p-4">
                                <h4 className="font-medium mb-3">인쇄 통계</h4>
                                <div className="grid grid-cols-5 gap-4 text-center">
                                    <div>
                                        <p className="text-2xl font-bold">{settings.statistics.totalPrinted.toLocaleString()}</p>
                                        <p className="text-xs text-text-subtle">총 인쇄</p>
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold">{settings.statistics.monthlyPrinted.toLocaleString()}</p>
                                        <p className="text-xs text-text-subtle">이번 달</p>
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold">{settings.statistics.paperUsed.toLocaleString()}</p>
                                        <p className="text-xs text-text-subtle">용지 사용(매)</p>
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold text-blue-600">{settings.statistics.colorPages.toLocaleString()}</p>
                                        <p className="text-xs text-text-subtle">컬러</p>
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold">{settings.statistics.bwPages.toLocaleString()}</p>
                                        <p className="text-xs text-text-subtle">흑백</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default PrintSettingsWindow;
