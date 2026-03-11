"use client";

import React, { useState, useEffect, useRef } from "react";
import {
    Save,
    RotateCcw,
    FileText,
    FileSpreadsheet,
    Receipt,
    Image,
    Stamp,
    Eye,
    Upload,
    Trash2,
    Copy,
    ChevronDown,
    ChevronRight,
    Move,
    ZoomIn,
    ZoomOut,
    AlignLeft,
    AlignCenter,
    AlignRight,
    Bold,
    Italic,
    Type,
    Palette,
    Grid,
    Layers,
} from "lucide-react";

// ============== 인터페이스 정의 ==============

interface Position {
    x: number;
    y: number;
}

interface Size {
    width: number;
    height: number;
}

interface FontSettings {
    family: string;
    size: number;
    weight: "normal" | "bold";
    style: "normal" | "italic";
    color: string;
    align: "left" | "center" | "right";
}

interface ImageElement {
    id: string;
    type: "logo" | "stamp" | "signature";
    name: string;
    dataUrl: string;
    position: Position;
    size: Size;
    opacity: number;
    rotation: number;
    visible: boolean;
}

interface FieldElement {
    id: string;
    name: string;
    label: string;
    position: Position;
    size: Size;
    font: FontSettings;
    visible: boolean;
    required: boolean;
    format?: string;
}

interface TableSettings {
    headerFont: FontSettings;
    bodyFont: FontSettings;
    borderColor: string;
    borderWidth: number;
    headerBgColor: string;
    alternateRowColor: string;
    showGridLines: boolean;
    cellPadding: number;
}

interface FormTemplate {
    id: string;
    name: string;
    type: "quote" | "taxInvoice" | "statement" | "custom";
    paperSize: "A4" | "Letter" | "A5" | "B5";
    orientation: "portrait" | "landscape";
    margins: {
        top: number;
        bottom: number;
        left: number;
        right: number;
    };
    header: {
        height: number;
        showLogo: boolean;
        showCompanyInfo: boolean;
        titleText: string;
        titleFont: FontSettings;
    };
    body: {
        tableSettings: TableSettings;
        fields: FieldElement[];
    };
    footer: {
        height: number;
        showStamp: boolean;
        showSignature: boolean;
        showPageNumber: boolean;
        pageNumberFormat: string;
        noteText: string;
        noteFont: FontSettings;
    };
    images: ImageElement[];
    customCss?: string;
}

interface QuoteFormSettings {
    template: FormTemplate;
    showUnitPrice: boolean;
    showTotalPrice: boolean;
    showVat: boolean;
    showDiscount: boolean;
    showItemCode: boolean;
    showItemDescription: boolean;
    showDeliveryDate: boolean;
    showPaymentTerms: boolean;
    showValidityPeriod: boolean;
    validityDays: number;
    termsAndConditions: string;
    bankInfo: string;
}

interface TaxInvoiceFormSettings {
    template: FormTemplate;
    issuerPosition: "left" | "right";
    receiverPosition: "left" | "right";
    showSupplyPrice: boolean;
    showTaxAmount: boolean;
    showTotalAmount: boolean;
    showRemark: boolean;
    electronicInvoice: boolean;
    electronicInvoiceType: "정발행" | "역발행";
    autoIssue: boolean;
    autoIssueDay: number;
}

interface StatementFormSettings {
    template: FormTemplate;
    showPreviousBalance: boolean;
    showCurrentSales: boolean;
    showCurrentPayment: boolean;
    showCurrentBalance: boolean;
    showItemDetails: boolean;
    showPaymentDetails: boolean;
    periodType: "monthly" | "custom";
    customPeriodDays: number;
}

interface FormSettings {
    quote: QuoteFormSettings;
    taxInvoice: TaxInvoiceFormSettings;
    statement: StatementFormSettings;
    globalImages: ImageElement[];
}

// ============== 기본값 정의 ==============

const defaultFontSettings: FontSettings = {
    family: "맑은 고딕",
    size: 10,
    weight: "normal",
    style: "normal",
    color: "#000000",
    align: "left",
};

const defaultTableSettings: TableSettings = {
    headerFont: { ...defaultFontSettings, weight: "bold", align: "center" },
    bodyFont: defaultFontSettings,
    borderColor: "#000000",
    borderWidth: 1,
    headerBgColor: "#E5E7EB",
    alternateRowColor: "#F9FAFB",
    showGridLines: true,
    cellPadding: 4,
};

const createDefaultTemplate = (type: FormTemplate["type"]): FormTemplate => ({
    id: `template_${type}_${Date.now()}`,
    name: type === "quote" ? "견적서" : type === "taxInvoice" ? "세금계산서" : type === "statement" ? "거래명세서" : "사용자 정의",
    type,
    paperSize: "A4",
    orientation: "portrait",
    margins: { top: 20, bottom: 20, left: 15, right: 15 },
    header: {
        height: 80,
        showLogo: true,
        showCompanyInfo: true,
        titleText: type === "quote" ? "견 적 서" : type === "taxInvoice" ? "세 금 계 산 서" : "거 래 명 세 서",
        titleFont: { ...defaultFontSettings, size: 20, weight: "bold", align: "center" },
    },
    body: {
        tableSettings: defaultTableSettings,
        fields: [],
    },
    footer: {
        height: 60,
        showStamp: true,
        showSignature: false,
        showPageNumber: true,
        pageNumberFormat: "- {page} / {total} -",
        noteText: "",
        noteFont: { ...defaultFontSettings, size: 8 },
    },
    images: [],
});

const defaultFormSettings: FormSettings = {
    quote: {
        template: createDefaultTemplate("quote"),
        showUnitPrice: true,
        showTotalPrice: true,
        showVat: true,
        showDiscount: true,
        showItemCode: true,
        showItemDescription: true,
        showDeliveryDate: true,
        showPaymentTerms: true,
        showValidityPeriod: true,
        validityDays: 30,
        termsAndConditions: "1. 본 견적서의 유효기간은 발행일로부터 30일입니다.\n2. 납기일은 발주 후 협의에 의해 결정됩니다.\n3. 대금 결제는 현금 또는 세금계산서 발행 후 30일 이내입니다.",
        bankInfo: "",
    },
    taxInvoice: {
        template: createDefaultTemplate("taxInvoice"),
        issuerPosition: "left",
        receiverPosition: "right",
        showSupplyPrice: true,
        showTaxAmount: true,
        showTotalAmount: true,
        showRemark: true,
        electronicInvoice: true,
        electronicInvoiceType: "정발행",
        autoIssue: false,
        autoIssueDay: 5,
    },
    statement: {
        template: createDefaultTemplate("statement"),
        showPreviousBalance: true,
        showCurrentSales: true,
        showCurrentPayment: true,
        showCurrentBalance: true,
        showItemDetails: true,
        showPaymentDetails: true,
        periodType: "monthly",
        customPeriodDays: 30,
    },
    globalImages: [],
};

// ============== 메인 컴포넌트 ==============

export function FormSettingsWindow() {
    const [activeTab, setActiveTab] = useState<"quote" | "taxInvoice" | "statement" | "images">("quote");
    const [settings, setSettings] = useState<FormSettings>(defaultFormSettings);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
    const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
        template: true,
        header: true,
        body: true,
        footer: true,
        options: true,
    });
    const [previewMode, setPreviewMode] = useState(false);
    const [previewZoom, setPreviewZoom] = useState(100);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [uploadTarget, setUploadTarget] = useState<"logo" | "stamp" | "signature">("logo");

    // 설정 불러오기
    useEffect(() => {
        const saved = localStorage.getItem("erp_form_settings");
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                setSettings({ ...defaultFormSettings, ...parsed });
            } catch (e) {
                console.error("양식 설정 불러오기 실패:", e);
            }
        }
    }, []);

    // 설정 저장
    const handleSave = async () => {
        setSaving(true);
        try {
            localStorage.setItem("erp_form_settings", JSON.stringify(settings));
            window.dispatchEvent(new CustomEvent("kis-erp-settings-updated"));
            setMessage({ type: "success", text: "양식 설정이 저장되었습니다." });
            setTimeout(() => setMessage(null), 3000);
        } catch (error) {
            setMessage({ type: "error", text: "저장에 실패했습니다." });
        } finally {
            setSaving(false);
        }
    };

    // 초기화
    const handleReset = () => {
        if (confirm("모든 양식 설정을 초기화하시겠습니까?")) {
            setSettings(defaultFormSettings);
        }
    };

    // 섹션 토글
    const toggleSection = (section: string) => {
        setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
    };

    // 이미지 업로드
    const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            const dataUrl = e.target?.result as string;
            const newImage: ImageElement = {
                id: `img_${Date.now()}`,
                type: uploadTarget,
                name: file.name,
                dataUrl,
                position: { x: 10, y: 10 },
                size: { width: 100, height: uploadTarget === "stamp" ? 100 : 50 },
                opacity: 1,
                rotation: 0,
                visible: true,
            };
            setSettings(prev => ({
                ...prev,
                globalImages: [...prev.globalImages, newImage],
            }));
        };
        reader.readAsDataURL(file);
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    // 이미지 삭제
    const handleImageDelete = (imageId: string) => {
        if (confirm("이미지를 삭제하시겠습니까?")) {
            setSettings(prev => ({
                ...prev,
                globalImages: prev.globalImages.filter(img => img.id !== imageId),
            }));
        }
    };

    // 견적서 설정 업데이트
    const updateQuoteSettings = (updates: Partial<QuoteFormSettings>) => {
        setSettings(prev => ({
            ...prev,
            quote: { ...prev.quote, ...updates },
        }));
    };

    // 세금계산서 설정 업데이트
    const updateTaxInvoiceSettings = (updates: Partial<TaxInvoiceFormSettings>) => {
        setSettings(prev => ({
            ...prev,
            taxInvoice: { ...prev.taxInvoice, ...updates },
        }));
    };

    // 거래명세서 설정 업데이트
    const updateStatementSettings = (updates: Partial<StatementFormSettings>) => {
        setSettings(prev => ({
            ...prev,
            statement: { ...prev.statement, ...updates },
        }));
    };

    // 템플릿 설정 업데이트
    const updateTemplate = (formType: "quote" | "taxInvoice" | "statement", updates: Partial<FormTemplate>) => {
        setSettings(prev => ({
            ...prev,
            [formType]: {
                ...prev[formType],
                template: { ...prev[formType].template, ...updates },
            },
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

    // ============== 탭 목록 ==============
    const tabs = [
        { id: "quote" as const, label: "견적서", icon: FileText },
        { id: "taxInvoice" as const, label: "세금계산서", icon: Receipt },
        { id: "statement" as const, label: "거래명세서", icon: FileSpreadsheet },
        { id: "images" as const, label: "로고/인감", icon: Image },
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
                        onClick={() => setPreviewMode(!previewMode)}
                        className={`flex items-center gap-1 rounded px-3 py-1.5 text-sm ${previewMode ? "bg-brand text-white" : "border hover:bg-surface-secondary"}`}
                    >
                        <Eye className="h-4 w-4" />
                        미리보기
                    </button>
                    {previewMode && (
                        <div className="flex items-center gap-1">
                            <button
                                onClick={() => setPreviewZoom(Math.max(50, previewZoom - 10))}
                                className="rounded p-1 hover:bg-surface-secondary"
                            >
                                <ZoomOut className="h-4 w-4" />
                            </button>
                            <span className="text-sm">{previewZoom}%</span>
                            <button
                                onClick={() => setPreviewZoom(Math.min(200, previewZoom + 10))}
                                className="rounded p-1 hover:bg-surface-secondary"
                            >
                                <ZoomIn className="h-4 w-4" />
                            </button>
                        </div>
                    )}
                </div>
                {message && (
                    <span className={`text-sm ${message.type === "success" ? "text-green-600" : "text-red-600"}`}>
                        {message.text}
                    </span>
                )}
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
                    {/* 견적서 설정 */}
                    {activeTab === "quote" && (
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold">견적서 양식 설정</h3>

                            {/* 템플릿 기본 설정 */}
                            <SectionHeader title="템플릿 기본 설정" section="template" icon={FileText} />
                            {expandedSections.template && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <div className="grid grid-cols-3 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">용지 크기</label>
                                            <select
                                                value={settings.quote.template.paperSize}
                                                onChange={(e) => updateTemplate("quote", { paperSize: e.target.value as FormTemplate["paperSize"] })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                <option value="A4">A4 (210×297mm)</option>
                                                <option value="Letter">Letter (216×279mm)</option>
                                                <option value="A5">A5 (148×210mm)</option>
                                                <option value="B5">B5 (176×250mm)</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">용지 방향</label>
                                            <select
                                                value={settings.quote.template.orientation}
                                                onChange={(e) => updateTemplate("quote", { orientation: e.target.value as "portrait" | "landscape" })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                <option value="portrait">세로</option>
                                                <option value="landscape">가로</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">제목</label>
                                            <input
                                                type="text"
                                                value={settings.quote.template.header.titleText}
                                                onChange={(e) => updateTemplate("quote", {
                                                    header: { ...settings.quote.template.header, titleText: e.target.value }
                                                })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            />
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-4 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">상단 여백 (mm)</label>
                                            <input
                                                type="number"
                                                value={settings.quote.template.margins.top}
                                                onChange={(e) => updateTemplate("quote", {
                                                    margins: { ...settings.quote.template.margins, top: Number(e.target.value) }
                                                })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">하단 여백 (mm)</label>
                                            <input
                                                type="number"
                                                value={settings.quote.template.margins.bottom}
                                                onChange={(e) => updateTemplate("quote", {
                                                    margins: { ...settings.quote.template.margins, bottom: Number(e.target.value) }
                                                })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">좌측 여백 (mm)</label>
                                            <input
                                                type="number"
                                                value={settings.quote.template.margins.left}
                                                onChange={(e) => updateTemplate("quote", {
                                                    margins: { ...settings.quote.template.margins, left: Number(e.target.value) }
                                                })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">우측 여백 (mm)</label>
                                            <input
                                                type="number"
                                                value={settings.quote.template.margins.right}
                                                onChange={(e) => updateTemplate("quote", {
                                                    margins: { ...settings.quote.template.margins, right: Number(e.target.value) }
                                                })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            />
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* 머리글 설정 */}
                            <SectionHeader title="머리글 설정" section="header" icon={Type} />
                            {expandedSections.header && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">머리글 높이 (mm)</label>
                                            <input
                                                type="number"
                                                value={settings.quote.template.header.height}
                                                onChange={(e) => updateTemplate("quote", {
                                                    header: { ...settings.quote.template.header, height: Number(e.target.value) }
                                                })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">제목 글꼴 크기</label>
                                            <input
                                                type="number"
                                                value={settings.quote.template.header.titleFont.size}
                                                onChange={(e) => updateTemplate("quote", {
                                                    header: {
                                                        ...settings.quote.template.header,
                                                        titleFont: { ...settings.quote.template.header.titleFont, size: Number(e.target.value) }
                                                    }
                                                })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            />
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-6">
                                        <label className="flex items-center gap-2">
                                            <input
                                                type="checkbox"
                                                checked={settings.quote.template.header.showLogo}
                                                onChange={(e) => updateTemplate("quote", {
                                                    header: { ...settings.quote.template.header, showLogo: e.target.checked }
                                                })}
                                                className="h-4 w-4"
                                            />
                                            <span className="text-sm">로고 표시</span>
                                        </label>
                                        <label className="flex items-center gap-2">
                                            <input
                                                type="checkbox"
                                                checked={settings.quote.template.header.showCompanyInfo}
                                                onChange={(e) => updateTemplate("quote", {
                                                    header: { ...settings.quote.template.header, showCompanyInfo: e.target.checked }
                                                })}
                                                className="h-4 w-4"
                                            />
                                            <span className="text-sm">회사정보 표시</span>
                                        </label>
                                    </div>
                                </div>
                            )}

                            {/* 본문 설정 */}
                            <SectionHeader title="본문/표 설정" section="body" icon={Grid} />
                            {expandedSections.body && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <div className="grid grid-cols-3 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">테이블 테두리 색상</label>
                                            <input
                                                type="color"
                                                value={settings.quote.template.body.tableSettings.borderColor}
                                                onChange={(e) => updateTemplate("quote", {
                                                    body: {
                                                        ...settings.quote.template.body,
                                                        tableSettings: { ...settings.quote.template.body.tableSettings, borderColor: e.target.value }
                                                    }
                                                })}
                                                className="w-full h-9 rounded border cursor-pointer"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">헤더 배경색</label>
                                            <input
                                                type="color"
                                                value={settings.quote.template.body.tableSettings.headerBgColor}
                                                onChange={(e) => updateTemplate("quote", {
                                                    body: {
                                                        ...settings.quote.template.body,
                                                        tableSettings: { ...settings.quote.template.body.tableSettings, headerBgColor: e.target.value }
                                                    }
                                                })}
                                                className="w-full h-9 rounded border cursor-pointer"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">줄무늬 색상</label>
                                            <input
                                                type="color"
                                                value={settings.quote.template.body.tableSettings.alternateRowColor}
                                                onChange={(e) => updateTemplate("quote", {
                                                    body: {
                                                        ...settings.quote.template.body,
                                                        tableSettings: { ...settings.quote.template.body.tableSettings, alternateRowColor: e.target.value }
                                                    }
                                                })}
                                                className="w-full h-9 rounded border cursor-pointer"
                                            />
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">테두리 두께 (px)</label>
                                            <input
                                                type="number"
                                                min="0"
                                                max="5"
                                                value={settings.quote.template.body.tableSettings.borderWidth}
                                                onChange={(e) => updateTemplate("quote", {
                                                    body: {
                                                        ...settings.quote.template.body,
                                                        tableSettings: { ...settings.quote.template.body.tableSettings, borderWidth: Number(e.target.value) }
                                                    }
                                                })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">셀 패딩 (px)</label>
                                            <input
                                                type="number"
                                                min="0"
                                                max="20"
                                                value={settings.quote.template.body.tableSettings.cellPadding}
                                                onChange={(e) => updateTemplate("quote", {
                                                    body: {
                                                        ...settings.quote.template.body,
                                                        tableSettings: { ...settings.quote.template.body.tableSettings, cellPadding: Number(e.target.value) }
                                                    }
                                                })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            />
                                        </div>
                                    </div>
                                    <label className="flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            checked={settings.quote.template.body.tableSettings.showGridLines}
                                            onChange={(e) => updateTemplate("quote", {
                                                body: {
                                                    ...settings.quote.template.body,
                                                    tableSettings: { ...settings.quote.template.body.tableSettings, showGridLines: e.target.checked }
                                                }
                                            })}
                                            className="h-4 w-4"
                                        />
                                        <span className="text-sm">격자선 표시</span>
                                    </label>
                                </div>
                            )}

                            {/* 표시 항목 설정 */}
                            <SectionHeader title="표시 항목" section="options" icon={Layers} />
                            {expandedSections.options && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <div className="grid grid-cols-3 gap-3">
                                        {[
                                            { key: "showUnitPrice", label: "단가" },
                                            { key: "showTotalPrice", label: "금액" },
                                            { key: "showVat", label: "부가세" },
                                            { key: "showDiscount", label: "할인" },
                                            { key: "showItemCode", label: "품목코드" },
                                            { key: "showItemDescription", label: "품목설명" },
                                            { key: "showDeliveryDate", label: "납기일" },
                                            { key: "showPaymentTerms", label: "결제조건" },
                                            { key: "showValidityPeriod", label: "유효기간" },
                                        ].map(({ key, label }) => (
                                            <label key={key} className="flex items-center gap-2">
                                                <input
                                                    type="checkbox"
                                                    checked={settings.quote[key as keyof QuoteFormSettings] as boolean}
                                                    onChange={(e) => updateQuoteSettings({ [key]: e.target.checked })}
                                                    className="h-4 w-4"
                                                />
                                                <span className="text-sm">{label}</span>
                                            </label>
                                        ))}
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">견적 유효기간 (일)</label>
                                        <input
                                            type="number"
                                            min="1"
                                            max="365"
                                            value={settings.quote.validityDays}
                                            onChange={(e) => updateQuoteSettings({ validityDays: Number(e.target.value) })}
                                            className="w-32 rounded border px-3 py-2 text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">이용약관/조건</label>
                                        <textarea
                                            value={settings.quote.termsAndConditions}
                                            onChange={(e) => updateQuoteSettings({ termsAndConditions: e.target.value })}
                                            rows={4}
                                            className="w-full rounded border px-3 py-2 text-sm"
                                            placeholder="견적서 하단에 표시될 약관/조건을 입력하세요"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">입금 계좌정보</label>
                                        <textarea
                                            value={settings.quote.bankInfo}
                                            onChange={(e) => updateQuoteSettings({ bankInfo: e.target.value })}
                                            rows={2}
                                            className="w-full rounded border px-3 py-2 text-sm"
                                            placeholder="예: 국민은행 123-456-789012 (주)한국산업"
                                        />
                                    </div>
                                </div>
                            )}

                            {/* 바닥글 설정 */}
                            <SectionHeader title="바닥글 설정" section="footer" icon={Type} />
                            {expandedSections.footer && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">바닥글 높이 (mm)</label>
                                            <input
                                                type="number"
                                                value={settings.quote.template.footer.height}
                                                onChange={(e) => updateTemplate("quote", {
                                                    footer: { ...settings.quote.template.footer, height: Number(e.target.value) }
                                                })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">페이지 번호 형식</label>
                                            <input
                                                type="text"
                                                value={settings.quote.template.footer.pageNumberFormat}
                                                onChange={(e) => updateTemplate("quote", {
                                                    footer: { ...settings.quote.template.footer, pageNumberFormat: e.target.value }
                                                })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                                placeholder="{page}/{total}"
                                            />
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-6">
                                        <label className="flex items-center gap-2">
                                            <input
                                                type="checkbox"
                                                checked={settings.quote.template.footer.showStamp}
                                                onChange={(e) => updateTemplate("quote", {
                                                    footer: { ...settings.quote.template.footer, showStamp: e.target.checked }
                                                })}
                                                className="h-4 w-4"
                                            />
                                            <span className="text-sm">직인 표시</span>
                                        </label>
                                        <label className="flex items-center gap-2">
                                            <input
                                                type="checkbox"
                                                checked={settings.quote.template.footer.showSignature}
                                                onChange={(e) => updateTemplate("quote", {
                                                    footer: { ...settings.quote.template.footer, showSignature: e.target.checked }
                                                })}
                                                className="h-4 w-4"
                                            />
                                            <span className="text-sm">서명 표시</span>
                                        </label>
                                        <label className="flex items-center gap-2">
                                            <input
                                                type="checkbox"
                                                checked={settings.quote.template.footer.showPageNumber}
                                                onChange={(e) => updateTemplate("quote", {
                                                    footer: { ...settings.quote.template.footer, showPageNumber: e.target.checked }
                                                })}
                                                className="h-4 w-4"
                                            />
                                            <span className="text-sm">페이지 번호</span>
                                        </label>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* 세금계산서 설정 */}
                    {activeTab === "taxInvoice" && (
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold">세금계산서 양식 설정</h3>

                            {/* 템플릿 기본 설정 */}
                            <SectionHeader title="템플릿 기본 설정" section="template" icon={Receipt} />
                            {expandedSections.template && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <div className="grid grid-cols-3 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">용지 크기</label>
                                            <select
                                                value={settings.taxInvoice.template.paperSize}
                                                onChange={(e) => updateTemplate("taxInvoice", { paperSize: e.target.value as FormTemplate["paperSize"] })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                <option value="A4">A4 (210×297mm)</option>
                                                <option value="Letter">Letter (216×279mm)</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">공급자 위치</label>
                                            <select
                                                value={settings.taxInvoice.issuerPosition}
                                                onChange={(e) => updateTaxInvoiceSettings({ issuerPosition: e.target.value as "left" | "right" })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                <option value="left">왼쪽</option>
                                                <option value="right">오른쪽</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">공급받는자 위치</label>
                                            <select
                                                value={settings.taxInvoice.receiverPosition}
                                                onChange={(e) => updateTaxInvoiceSettings({ receiverPosition: e.target.value as "left" | "right" })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                <option value="left">왼쪽</option>
                                                <option value="right">오른쪽</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* 전자세금계산서 설정 */}
                            <SectionHeader title="전자세금계산서 설정" section="options" icon={FileText} />
                            {expandedSections.options && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <label className="flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            checked={settings.taxInvoice.electronicInvoice}
                                            onChange={(e) => updateTaxInvoiceSettings({ electronicInvoice: e.target.checked })}
                                            className="h-4 w-4"
                                        />
                                        <span className="text-sm font-medium">전자세금계산서 사용</span>
                                    </label>
                                    {settings.taxInvoice.electronicInvoice && (
                                        <div className="grid grid-cols-2 gap-4 ml-6">
                                            <div>
                                                <label className="block text-sm font-medium mb-1">발행 유형</label>
                                                <select
                                                    value={settings.taxInvoice.electronicInvoiceType}
                                                    onChange={(e) => updateTaxInvoiceSettings({ electronicInvoiceType: e.target.value as "정발행" | "역발행" })}
                                                    className="w-full rounded border px-3 py-2 text-sm"
                                                >
                                                    <option value="정발행">정발행 (공급자 발행)</option>
                                                    <option value="역발행">역발행 (공급받는자 발행)</option>
                                                </select>
                                            </div>
                                            <div>
                                                <label className="flex items-center gap-2 mt-6">
                                                    <input
                                                        type="checkbox"
                                                        checked={settings.taxInvoice.autoIssue}
                                                        onChange={(e) => updateTaxInvoiceSettings({ autoIssue: e.target.checked })}
                                                        className="h-4 w-4"
                                                    />
                                                    <span className="text-sm">자동 발행</span>
                                                </label>
                                            </div>
                                        </div>
                                    )}
                                    {settings.taxInvoice.autoIssue && (
                                        <div className="ml-6">
                                            <label className="block text-sm font-medium mb-1">자동 발행일 (익월)</label>
                                            <div className="flex items-center gap-2">
                                                <span className="text-sm">매월</span>
                                                <input
                                                    type="number"
                                                    min="1"
                                                    max="28"
                                                    value={settings.taxInvoice.autoIssueDay}
                                                    onChange={(e) => updateTaxInvoiceSettings({ autoIssueDay: Number(e.target.value) })}
                                                    className="w-20 rounded border px-3 py-2 text-sm"
                                                />
                                                <span className="text-sm">일</span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* 표시 항목 설정 */}
                            <SectionHeader title="표시 항목" section="body" icon={Layers} />
                            {expandedSections.body && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <div className="grid grid-cols-2 gap-3">
                                        {[
                                            { key: "showSupplyPrice", label: "공급가액 표시" },
                                            { key: "showTaxAmount", label: "세액 표시" },
                                            { key: "showTotalAmount", label: "합계금액 표시" },
                                            { key: "showRemark", label: "비고란 표시" },
                                        ].map(({ key, label }) => (
                                            <label key={key} className="flex items-center gap-2">
                                                <input
                                                    type="checkbox"
                                                    checked={settings.taxInvoice[key as keyof TaxInvoiceFormSettings] as boolean}
                                                    onChange={(e) => updateTaxInvoiceSettings({ [key]: e.target.checked })}
                                                    className="h-4 w-4"
                                                />
                                                <span className="text-sm">{label}</span>
                                            </label>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* 거래명세서 설정 */}
                    {activeTab === "statement" && (
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold">거래명세서 양식 설정</h3>

                            {/* 템플릿 기본 설정 */}
                            <SectionHeader title="템플릿 기본 설정" section="template" icon={FileSpreadsheet} />
                            {expandedSections.template && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <div className="grid grid-cols-3 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">용지 크기</label>
                                            <select
                                                value={settings.statement.template.paperSize}
                                                onChange={(e) => updateTemplate("statement", { paperSize: e.target.value as FormTemplate["paperSize"] })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                <option value="A4">A4 (210×297mm)</option>
                                                <option value="Letter">Letter (216×279mm)</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">용지 방향</label>
                                            <select
                                                value={settings.statement.template.orientation}
                                                onChange={(e) => updateTemplate("statement", { orientation: e.target.value as "portrait" | "landscape" })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                <option value="portrait">세로</option>
                                                <option value="landscape">가로</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">기간 유형</label>
                                            <select
                                                value={settings.statement.periodType}
                                                onChange={(e) => updateStatementSettings({ periodType: e.target.value as "monthly" | "custom" })}
                                                className="w-full rounded border px-3 py-2 text-sm"
                                            >
                                                <option value="monthly">월별</option>
                                                <option value="custom">사용자 지정</option>
                                            </select>
                                        </div>
                                    </div>
                                    {settings.statement.periodType === "custom" && (
                                        <div>
                                            <label className="block text-sm font-medium mb-1">기간 (일)</label>
                                            <input
                                                type="number"
                                                min="1"
                                                max="365"
                                                value={settings.statement.customPeriodDays}
                                                onChange={(e) => updateStatementSettings({ customPeriodDays: Number(e.target.value) })}
                                                className="w-32 rounded border px-3 py-2 text-sm"
                                            />
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* 표시 항목 설정 */}
                            <SectionHeader title="표시 항목" section="options" icon={Layers} />
                            {expandedSections.options && (
                                <div className="ml-6 space-y-3 border-l-2 border-brand/20 pl-4">
                                    <div className="grid grid-cols-2 gap-3">
                                        {[
                                            { key: "showPreviousBalance", label: "전월 이월금액" },
                                            { key: "showCurrentSales", label: "당월 매출금액" },
                                            { key: "showCurrentPayment", label: "당월 입금금액" },
                                            { key: "showCurrentBalance", label: "당월 잔액" },
                                            { key: "showItemDetails", label: "품목 상세내역" },
                                            { key: "showPaymentDetails", label: "입금 상세내역" },
                                        ].map(({ key, label }) => (
                                            <label key={key} className="flex items-center gap-2">
                                                <input
                                                    type="checkbox"
                                                    checked={settings.statement[key as keyof StatementFormSettings] as boolean}
                                                    onChange={(e) => updateStatementSettings({ [key]: e.target.checked })}
                                                    className="h-4 w-4"
                                                />
                                                <span className="text-sm">{label}</span>
                                            </label>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* 로고/인감 관리 */}
                    {activeTab === "images" && (
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold">로고/인감 관리</h3>

                            {/* 이미지 업로드 */}
                            <div className="rounded-lg border p-4">
                                <h4 className="font-medium mb-3">이미지 업로드</h4>
                                <div className="flex items-center gap-4">
                                    <select
                                        value={uploadTarget}
                                        onChange={(e) => setUploadTarget(e.target.value as "logo" | "stamp" | "signature")}
                                        className="rounded border px-3 py-2 text-sm"
                                    >
                                        <option value="logo">회사 로고</option>
                                        <option value="stamp">직인 (도장)</option>
                                        <option value="signature">서명</option>
                                    </select>
                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        className="flex items-center gap-2 rounded bg-brand px-4 py-2 text-sm text-white hover:bg-brand-dark"
                                    >
                                        <Upload className="h-4 w-4" />
                                        파일 선택
                                    </button>
                                    <input
                                        ref={fileInputRef}
                                        type="file"
                                        accept="image/*"
                                        onChange={handleImageUpload}
                                        className="hidden"
                                    />
                                </div>
                                <p className="mt-2 text-xs text-text-subtle">
                                    권장: PNG 또는 투명 배경 이미지. 로고 권장 크기: 200x50px, 직인 권장 크기: 150x150px
                                </p>
                            </div>

                            {/* 등록된 이미지 목록 */}
                            <div className="rounded-lg border p-4">
                                <h4 className="font-medium mb-3">등록된 이미지</h4>
                                {settings.globalImages.length === 0 ? (
                                    <p className="text-sm text-text-subtle">등록된 이미지가 없습니다.</p>
                                ) : (
                                    <div className="grid grid-cols-3 gap-4">
                                        {settings.globalImages.map((image) => (
                                            <div key={image.id} className="rounded-lg border p-3">
                                                <div className="relative aspect-square mb-2 rounded bg-gray-100 flex items-center justify-center overflow-hidden">
                                                    <img
                                                        src={image.dataUrl}
                                                        alt={image.name}
                                                        className="max-w-full max-h-full object-contain"
                                                        style={{ opacity: image.opacity }}
                                                    />
                                                </div>
                                                <div className="space-y-2">
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-xs font-medium px-2 py-0.5 rounded bg-surface-secondary">
                                                            {image.type === "logo" ? "로고" : image.type === "stamp" ? "직인" : "서명"}
                                                        </span>
                                                        <button
                                                            onClick={() => handleImageDelete(image.id)}
                                                            className="text-red-500 hover:text-red-700"
                                                        >
                                                            <Trash2 className="h-4 w-4" />
                                                        </button>
                                                    </div>
                                                    <p className="text-xs text-text-subtle truncate">{image.name}</p>
                                                    <div>
                                                        <label className="block text-xs mb-1">투명도</label>
                                                        <input
                                                            type="range"
                                                            min="0"
                                                            max="1"
                                                            step="0.1"
                                                            value={image.opacity}
                                                            onChange={(e) => {
                                                                const opacity = Number(e.target.value);
                                                                setSettings(prev => ({
                                                                    ...prev,
                                                                    globalImages: prev.globalImages.map(img =>
                                                                        img.id === image.id ? { ...img, opacity } : img
                                                                    ),
                                                                }));
                                                            }}
                                                            className="w-full"
                                                        />
                                                    </div>
                                                    <div className="grid grid-cols-2 gap-2">
                                                        <div>
                                                            <label className="block text-xs mb-1">너비 (px)</label>
                                                            <input
                                                                type="number"
                                                                min="10"
                                                                max="500"
                                                                value={image.size.width}
                                                                onChange={(e) => {
                                                                    const width = Number(e.target.value);
                                                                    setSettings(prev => ({
                                                                        ...prev,
                                                                        globalImages: prev.globalImages.map(img =>
                                                                            img.id === image.id ? { ...img, size: { ...img.size, width } } : img
                                                                        ),
                                                                    }));
                                                                }}
                                                                className="w-full rounded border px-2 py-1 text-xs"
                                                            />
                                                        </div>
                                                        <div>
                                                            <label className="block text-xs mb-1">높이 (px)</label>
                                                            <input
                                                                type="number"
                                                                min="10"
                                                                max="500"
                                                                value={image.size.height}
                                                                onChange={(e) => {
                                                                    const height = Number(e.target.value);
                                                                    setSettings(prev => ({
                                                                        ...prev,
                                                                        globalImages: prev.globalImages.map(img =>
                                                                            img.id === image.id ? { ...img, size: { ...img.size, height } } : img
                                                                        ),
                                                                    }));
                                                                }}
                                                                className="w-full rounded border px-2 py-1 text-xs"
                                                            />
                                                        </div>
                                                    </div>
                                                    <label className="flex items-center gap-2">
                                                        <input
                                                            type="checkbox"
                                                            checked={image.visible}
                                                            onChange={(e) => {
                                                                setSettings(prev => ({
                                                                    ...prev,
                                                                    globalImages: prev.globalImages.map(img =>
                                                                        img.id === image.id ? { ...img, visible: e.target.checked } : img
                                                                    ),
                                                                }));
                                                            }}
                                                            className="h-3 w-3"
                                                        />
                                                        <span className="text-xs">양식에 표시</span>
                                                    </label>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* 이미지 사용 안내 */}
                            <div className="rounded-lg bg-blue-50 p-4">
                                <h4 className="font-medium text-blue-800 mb-2">이미지 사용 안내</h4>
                                <ul className="text-sm text-blue-700 space-y-1">
                                    <li>• 로고: 견적서, 세금계산서, 거래명세서 상단에 표시됩니다.</li>
                                    <li>• 직인: 양식 우측 하단 공급자 정보 영역에 표시됩니다.</li>
                                    <li>• 서명: 담당자 서명란에 표시됩니다.</li>
                                    <li>• 각 양식 설정에서 개별적으로 표시 여부를 설정할 수 있습니다.</li>
                                </ul>
                            </div>
                        </div>
                    )}
                </div>

                {/* 미리보기 패널 */}
                {previewMode && (
                    <div className="w-96 border-l bg-gray-100 p-4 overflow-auto">
                        <h4 className="font-medium mb-3">미리보기</h4>
                        <div
                            className="bg-white shadow-lg mx-auto"
                            style={{
                                width: `${210 * (previewZoom / 100)}px`,
                                height: `${297 * (previewZoom / 100)}px`,
                                padding: "10px",
                            }}
                        >
                            <div className="border h-full flex flex-col text-[6px]">
                                {/* 미리보기 헤더 */}
                                <div className="border-b p-2 text-center">
                                    <p className="font-bold" style={{ fontSize: `${8 * (previewZoom / 100)}px` }}>
                                        {activeTab === "quote" ? settings.quote.template.header.titleText :
                                         activeTab === "taxInvoice" ? settings.taxInvoice.template.header.titleText :
                                         settings.statement.template.header.titleText}
                                    </p>
                                </div>
                                {/* 미리보기 본문 */}
                                <div className="flex-1 p-2">
                                    <div className="h-full border flex items-center justify-center text-text-subtle">
                                        <span>본문 영역</span>
                                    </div>
                                </div>
                                {/* 미리보기 푸터 */}
                                <div className="border-t p-2 text-center text-text-subtle">
                                    <span>- 1 / 1 -</span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default FormSettingsWindow;
