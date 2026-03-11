"use client";

import React, { useCallback, useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
    Eye,
    Download,
    ExternalLink,
    Maximize2,
    ChevronLeft,
    ChevronRight,
    FileText,
    Table,
    Calendar,
    Image,
    BarChart3,
    Code,
    Receipt,
    Grid3X3,
    Layers,
    Clock,
    Edit,
    Check,
    Copy,
    Printer,
    Mail,
    Send,
    FileOutput,
    X,
    Phone,
    Save,
} from "lucide-react";
import type { VisualizationData, VisualizationAction } from "@/app/ai-manager/page";
import type { TabController } from "./hooks/useTabController";
import { getFileUrl } from "@/config/api";

interface VisualizationPanelProps {
    currentVisualization: VisualizationData | null;
    history: VisualizationData[];
    onSelectHistory: (viz: VisualizationData) => void;
    onExecuteAction: (action: VisualizationAction) => void;
    tabController: TabController;
    onClose?: () => void;
}

/**
 * AI 매니저 시각화 패널
 *
 * 기능:
 * 1. 견적서 미리보기
 * 2. ERP 테이블 표시
 * 3. 캘린더 이벤트
 * 4. 도면 미리보기
 * 5. 차트/그래프
 * 6. JSON 데이터 뷰어
 */
export function VisualizationPanel({
    currentVisualization,
    history,
    onSelectHistory,
    onExecuteAction,
    tabController,
    onClose,
}: VisualizationPanelProps) {
    // 시각화 타입별로 히스토리에서 마지막 항목 찾기
    const findLastVisualizationByType = useCallback((targetType: string) => {
        // 타입 매핑: 탭 이름 -> 시각화 타입
        const typeMapping: Record<string, string[]> = {
            quote: ["estimate_preview"],
            erp: ["erp_table", "chart"],
            calendar: ["calendar_event"],
            drawings: ["drawing_preview"],
        };

        const visualizationTypes = typeMapping[targetType] || [targetType];

        // 히스토리에서 역순으로 해당 타입의 시각화 찾기
        for (let i = history.length - 1; i >= 0; i--) {
            if (visualizationTypes.includes(history[i].type)) {
                return history[i];
            }
        }
        return null;
    }, [history]);

    // 탭 바로가기 핸들러 - 페이지 이동 대신 히스토리에서 선택
    const handleTabShortcut = useCallback((tab: string) => {
        const visualization = findLastVisualizationByType(tab);
        if (visualization) {
            onSelectHistory(visualization);
        }
        // 해당 타입의 시각화가 없으면 아무 것도 하지 않음 (현재 시각화 유지)
    }, [findLastVisualizationByType, onSelectHistory]);

    // 시각화 타입별 아이콘
    const getTypeIcon = (type: string) => {
        switch (type) {
            case "estimate_preview":
                return Receipt;
            case "erp_table":
                return Table;
            case "calendar_event":
                return Calendar;
            case "drawing_preview":
                return Image;
            case "chart":
                return BarChart3;
            case "json":
                return Code;
            default:
                return FileText;
        }
    };

    // 시각화 타입별 라벨
    const getTypeLabel = (type: string) => {
        switch (type) {
            case "estimate_preview":
                return "견적서 미리보기";
            case "erp_table":
                return "ERP 데이터";
            case "calendar_event":
                return "일정";
            case "drawing_preview":
                return "도면 미리보기";
            case "chart":
                return "차트";
            case "json":
                return "JSON 데이터";
            default:
                return "데이터";
        }
    };

    // 현재 인덱스
    const currentIndex = currentVisualization
        ? history.findIndex((v) => v.id === currentVisualization.id)
        : -1;

    // 이전/다음 네비게이션
    const goToPrevious = useCallback(() => {
        if (currentIndex > 0) {
            onSelectHistory(history[currentIndex - 1]);
        }
    }, [currentIndex, history, onSelectHistory]);

    const goToNext = useCallback(() => {
        if (currentIndex < history.length - 1) {
            onSelectHistory(history[currentIndex + 1]);
        }
    }, [currentIndex, history, onSelectHistory]);

    return (
        <div className="flex h-full flex-col">
            {/* 헤더 */}
            <div className="flex items-center justify-between border-b bg-surface px-4 py-3">
                <div className="flex items-center gap-2">
                    <Eye className="h-5 w-5 text-text-subtle" />
                    <span className="font-semibold text-text-strong">시각화</span>
                </div>

                {/* 탭 바로가기 - 페이지 이동 대신 히스토리에서 해당 타입 시각화 선택 */}
                <div className="flex items-center gap-1">
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 px-2"
                        onClick={() => handleTabShortcut("quote")}
                        title="히스토리에서 마지막 견적 시각화로 이동"
                    >
                        <Receipt className="mr-1 h-4 w-4" />
                        <span className="text-xs">견적</span>
                    </Button>
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 px-2"
                        onClick={() => handleTabShortcut("erp")}
                        title="히스토리에서 마지막 ERP 시각화로 이동"
                    >
                        <Grid3X3 className="mr-1 h-4 w-4" />
                        <span className="text-xs">ERP</span>
                    </Button>
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 px-2"
                        onClick={() => handleTabShortcut("calendar")}
                        title="히스토리에서 마지막 캘린더 시각화로 이동"
                    >
                        <Calendar className="mr-1 h-4 w-4" />
                        <span className="text-xs">캘린더</span>
                    </Button>
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 px-2"
                        onClick={() => handleTabShortcut("drawings")}
                        title="히스토리에서 마지막 도면 시각화로 이동"
                    >
                        <Layers className="mr-1 h-4 w-4" />
                        <span className="text-xs">도면</span>
                    </Button>

                    {/* 닫기 버튼 */}
                    {onClose && (
                        <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0 ml-2 hover:bg-red-100 hover:text-red-600"
                            onClick={onClose}
                            title="시각화 패널 닫기"
                        >
                            <X className="h-4 w-4" />
                        </Button>
                    )}
                </div>
            </div>

            {/* 콘텐츠 영역 */}
            <div className="flex-1 overflow-auto p-4">
                {currentVisualization ? (
                    <VisualizationRenderer
                        visualization={currentVisualization}
                        onExecuteAction={onExecuteAction}
                    />
                ) : (
                    <EmptyState />
                )}
            </div>

            {/* 히스토리 네비게이션 */}
            {history.length > 0 && (
                <div className="flex items-center justify-between border-t bg-surface px-4 py-2">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={goToPrevious}
                        disabled={currentIndex <= 0}
                    >
                        <ChevronLeft className="h-4 w-4" />
                        이전
                    </Button>

                    <div className="flex items-center gap-2">
                        {history.slice(-5).map((viz, index) => {
                            const TypeIcon = getTypeIcon(viz.type);
                            const isActive = viz.id === currentVisualization?.id;
                            return (
                                <button
                                    key={viz.id}
                                    onClick={() => onSelectHistory(viz)}
                                    className={cn(
                                        "flex h-8 w-8 items-center justify-center rounded-full transition-colors",
                                        isActive
                                            ? "bg-brand text-white"
                                            : "bg-surface-secondary hover:bg-surface"
                                    )}
                                    title={viz.title}
                                >
                                    <TypeIcon className="h-4 w-4" />
                                </button>
                            );
                        })}
                    </div>

                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={goToNext}
                        disabled={currentIndex >= history.length - 1}
                    >
                        다음
                        <ChevronRight className="h-4 w-4" />
                    </Button>
                </div>
            )}
        </div>
    );
}

/**
 * 시각화 렌더러
 */
function VisualizationRenderer({
    visualization,
    onExecuteAction,
}: {
    visualization: VisualizationData;
    onExecuteAction: (action: VisualizationAction) => void;
}) {
    const TypeIcon = getVisualizationIcon(visualization.type);
    const [showPreviewModal, setShowPreviewModal] = useState(false);

    const isEstimate = visualization.type === "estimate_preview";

    return (
        <div className="flex h-full flex-col rounded-lg border bg-surface">
            {/* 헤더 */}
            <div className="flex items-center justify-between border-b px-4 py-3">
                <div className="flex items-center gap-2">
                    <TypeIcon className="h-5 w-5 text-brand" />
                    <span className="font-medium text-text-strong">
                        {visualization.title}
                    </span>
                </div>

                {/* 액션 버튼들 */}
                <div className="flex items-center gap-1">
                    {/* 견적서일 경우 미리보기 버튼 추가 */}
                    {isEstimate && (
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setShowPreviewModal(true)}
                            className="bg-brand text-white hover:bg-brand/90"
                        >
                            <Eye className="mr-1 h-4 w-4" />
                            미리보기
                        </Button>
                    )}
                    {visualization.actions?.map((action) => (
                        <Button
                            key={action.id}
                            variant="ghost"
                            size="sm"
                            onClick={() => onExecuteAction(action)}
                        >
                            {action.icon === "download" && <Download className="mr-1 h-4 w-4" />}
                            {action.icon === "external" && <ExternalLink className="mr-1 h-4 w-4" />}
                            {action.icon === "maximize" && <Maximize2 className="mr-1 h-4 w-4" />}
                            {action.icon === "edit" && <Edit className="mr-1 h-4 w-4" />}
                            {action.icon === "check" && <Check className="mr-1 h-4 w-4" />}
                            {action.icon === "copy" && <Copy className="mr-1 h-4 w-4" />}
                            {action.icon === "print" && <Printer className="mr-1 h-4 w-4" />}
                            {action.label}
                        </Button>
                    ))}
                </div>
            </div>

            {/* 콘텐츠 */}
            <div className="flex-1 overflow-auto p-4">
                {renderVisualizationContent(visualization)}
            </div>

            {/* 미리보기 모달 */}
            {showPreviewModal && isEstimate && (
                <PreviewModal
                    visualization={visualization}
                    onClose={() => setShowPreviewModal(false)}
                />
            )}
        </div>
    );
}

/**
 * 빈 상태 컴포넌트
 */
function EmptyState() {
    return (
        <div className="flex h-full flex-col items-center justify-center text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-surface-secondary">
                <Eye className="h-8 w-8 text-text-subtle" />
            </div>
            <h3 className="mb-2 text-lg font-medium text-text-strong">
                시각화 결과가 여기에 표시됩니다
            </h3>
            <p className="max-w-sm text-sm text-text-subtle">
                AI에게 견적서 조회, 매출 현황, 일정 확인 등을 요청하면
                결과가 이곳에 시각화됩니다.
            </p>

            <div className="mt-8 grid grid-cols-2 gap-4">
                <ExampleCard
                    icon={Receipt}
                    title="견적서 조회"
                    example="이번 달 견적서 목록 보여줘"
                />
                <ExampleCard
                    icon={BarChart3}
                    title="매출 현황"
                    example="이번 달 매출 현황 보여줘"
                />
                <ExampleCard
                    icon={Table}
                    title="거래처 조회"
                    example="거래처 목록 확인해줘"
                />
                <ExampleCard
                    icon={Calendar}
                    title="일정 확인"
                    example="이번 주 일정 알려줘"
                />
            </div>
        </div>
    );
}

/**
 * 예시 카드 컴포넌트
 */
function ExampleCard({
    icon: Icon,
    title,
    example,
}: {
    icon: typeof Receipt;
    title: string;
    example: string;
}) {
    return (
        <div className="rounded-lg border bg-surface-secondary/50 p-4 text-left">
            <div className="mb-2 flex items-center gap-2">
                <Icon className="h-4 w-4 text-brand" />
                <span className="text-sm font-medium text-text-strong">{title}</span>
            </div>
            <p className="text-xs text-text-subtle">"{example}"</p>
        </div>
    );
}

/**
 * 시각화 아이콘 헬퍼
 */
function getVisualizationIcon(type: string) {
    switch (type) {
        case "estimate_preview":
            return Receipt;
        case "erp_table":
            return Table;
        case "calendar_event":
            return Calendar;
        case "drawing_preview":
            return Image;
        case "chart":
            return BarChart3;
        case "json":
            return Code;
        default:
            return FileText;
    }
}

/**
 * 시각화 콘텐츠 렌더러
 */
function renderVisualizationContent(visualization: VisualizationData) {
    const data = visualization.data as Record<string, unknown>;

    switch (visualization.type) {
        case "estimate_preview":
            return <EstimatePreview data={data} />;
        case "erp_table":
            return <ERPTable data={data} />;
        case "calendar_event":
            return <CalendarEvents data={data} />;
        case "drawing_preview":
            return <DrawingPreview data={data} />;
        case "chart":
            return <ChartView data={data} />;
        case "json":
            return <JSONViewer data={data} />;
        default:
            return <JSONViewer data={data} />;
    }
}

/**
 * 견적서 미리보기 컴포넌트 (탭 구조: 표지 + 내역서)
 */
function EstimatePreview({ data }: { data: Record<string, unknown> }) {
    const [activeTab, setActiveTab] = React.useState<"cover" | "details">("cover");
    const [isSaving, setIsSaving] = React.useState(false);
    const [saveResult, setSaveResult] = React.useState<{ success: boolean; message: string } | null>(null);
    const [loadedData, setLoadedData] = React.useState<Record<string, unknown> | null>(null);

    // 저장된 견적 불러오기 처리
    React.useEffect(() => {
        const loadSavedEstimateId = data?.load_saved_estimate_id as string | undefined;
        if (loadSavedEstimateId) {
            try {
                const saved = localStorage.getItem("savedEstimates");
                if (saved) {
                    const estimates = JSON.parse(saved);
                    const found = estimates.find((e: { id: string }) => e.id === loadSavedEstimateId);
                    if (found && found.data) {
                        setLoadedData(found.data);
                    }
                }
            } catch {
                // ignore
            }
        }
    }, [data?.load_saved_estimate_id]);

    // 저장된 견적이 로드되면 해당 데이터 사용
    const effectiveData = loadedData || data;

    // API 응답 구조에 맞게 데이터 파싱
    const estimate = effectiveData as {
        estimate_id?: string;
        id?: string;
        customer?: string;
        panelName?: string;
        totalAmount?: number;
        total_price?: number;
        total_price_with_vat?: number;
        panels?: Array<{
            panel_id: string;
            total_price: number;
            items: Array<{
                name: string;
                spec: string;
                unit: string;
                quantity: number;
                unit_price?: number;
                unitPrice?: number;
                supply_price?: number;
                amount?: number;
            }>;
        }>;
        items?: Array<{
            name: string;
            spec: string;
            unit: string;
            quantity: number;
            unit_price?: number;
            unitPrice?: number;
            supply_price?: number;
            amount?: number;
        }>;
        createdAt?: string;
        created_at?: string;
        pipeline_results?: {
            stage_1_enclosure?: {
                enclosure_size?: number[];
            };
        };
        documents?: {
            excel_url?: string;
            pdf_url?: string;
        };
        ai_verification?: {
            passed: boolean;
            summary: string;
        };
        // NOTE 섹션용 추가 정보
        brand?: string;
        enclosure_type?: string;
        enclosure_material?: string;
    };

    // 첫 번째 패널 데이터 추출
    const panel = estimate.panels?.[0];
    const items = panel?.items || estimate.items || [];
    const estimateId = estimate.estimate_id || estimate.id || "-";
    const createdAt = estimate.created_at || estimate.createdAt;
    const totalPrice = panel?.total_price || estimate.total_price || estimate.totalAmount || 0;
    const totalPriceWithVat = estimate.total_price_with_vat || Math.round(totalPrice * 1.1);
    const enclosureSize = estimate.pipeline_results?.stage_1_enclosure?.enclosure_size;

    // 외함 정보 추출
    const enclosureItem = items.find(item => item.name?.includes("HDS"));
    const mainBreaker = items.find(item =>
        item.name?.includes("SBE") || item.name?.includes("SBS") ||
        item.name?.includes("ABN") || item.name?.includes("ABS")
    );

    // 견적 저장 핸들러
    const handleSaveEstimate = async () => {
        setIsSaving(true);
        setSaveResult(null);
        try {
            // 저장할 견적 데이터 구성
            const savedEstimate = {
                id: estimateId,
                customer: estimate.customer || "",
                panelName: panel?.panel_id || estimate.panelName || "",
                totalPrice: totalPrice,
                totalPriceWithVat: totalPriceWithVat,
                items: items,
                enclosureSize: enclosureSize,
                brand: estimate.brand,
                enclosureType: estimate.enclosure_type,
                enclosureMaterial: estimate.enclosure_material,
                documents: estimate.documents,
                createdAt: createdAt || new Date().toISOString(),
                savedAt: new Date().toISOString(),
                data: data, // 전체 원본 데이터 저장
            };

            // localStorage에서 기존 저장된 견적 불러오기
            const existingEstimates = JSON.parse(localStorage.getItem("savedEstimates") || "[]");

            // 같은 ID의 견적이 있으면 업데이트, 없으면 추가
            const existingIndex = existingEstimates.findIndex((e: { id: string }) => e.id === estimateId);
            if (existingIndex >= 0) {
                existingEstimates[existingIndex] = savedEstimate;
            } else {
                existingEstimates.push(savedEstimate);
            }

            // localStorage에 저장
            localStorage.setItem("savedEstimates", JSON.stringify(existingEstimates));

            setSaveResult({ success: true, message: `견적 "${estimateId}"가 저장되었습니다.` });
        } catch {
            setSaveResult({ success: false, message: "견적 저장에 실패했습니다." });
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className="space-y-4">
            {/* 저장 버튼 및 결과 메시지 */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Button
                        onClick={handleSaveEstimate}
                        disabled={isSaving}
                        className="bg-blue-600 hover:bg-blue-700 text-white"
                        size="sm"
                    >
                        {isSaving ? (
                            <>저장 중...</>
                        ) : (
                            <>
                                <Save className="mr-1 h-4 w-4" />
                                견적 저장
                            </>
                        )}
                    </Button>
                    {saveResult && (
                        <span className={cn(
                            "text-sm",
                            saveResult.success ? "text-green-600" : "text-red-600"
                        )}>
                            {saveResult.message}
                        </span>
                    )}
                </div>
                <span className="text-xs text-text-subtle">견적번호: {estimateId}</span>
            </div>

            {/* 탭 네비게이션 */}
            <div className="flex border-b">
                <button
                    onClick={() => setActiveTab("cover")}
                    className={cn(
                        "flex-1 py-3 text-sm font-medium transition-colors border-b-2",
                        activeTab === "cover"
                            ? "border-brand text-brand"
                            : "border-transparent text-text-subtle hover:text-text-strong"
                    )}
                >
                    📋 표지
                </button>
                <button
                    onClick={() => setActiveTab("details")}
                    className={cn(
                        "flex-1 py-3 text-sm font-medium transition-colors border-b-2",
                        activeTab === "details"
                            ? "border-brand text-brand"
                            : "border-transparent text-text-subtle hover:text-text-strong"
                    )}
                >
                    📝 내역서
                </button>
            </div>

            {/* 탭 콘텐츠 */}
            {activeTab === "cover" ? (
                /* 표지 탭 */
                <div className="space-y-6">
                    {/* 견적서 타이틀 */}
                    <div className="text-center py-4 border-b">
                        <h2 className="text-2xl font-bold text-text-strong">견 적 서</h2>
                        <p className="text-sm text-text-subtle mt-1">QUOTATION</p>
                    </div>

                    {/* 기본 정보 */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-3">
                            <div className="flex justify-between border-b pb-2">
                                <span className="text-sm text-text-subtle">견적번호</span>
                                <span className="text-sm font-mono font-medium">{estimateId}</span>
                            </div>
                            <div className="flex justify-between border-b pb-2">
                                <span className="text-sm text-text-subtle">작성일</span>
                                <span className="text-sm font-medium">
                                    {createdAt
                                        ? new Date(createdAt).toLocaleDateString("ko-KR", {
                                            year: "numeric",
                                            month: "long",
                                            day: "numeric"
                                        })
                                        : "-"}
                                </span>
                            </div>
                            <div className="flex justify-between border-b pb-2">
                                <span className="text-sm text-text-subtle">거래처</span>
                                <span className="text-sm font-medium">{estimate.customer || "-"}</span>
                            </div>
                        </div>
                        <div className="space-y-3">
                            <div className="flex justify-between border-b pb-2">
                                <span className="text-sm text-text-subtle">분전반명</span>
                                <span className="text-sm font-medium">{panel?.panel_id || estimate.panelName || "-"}</span>
                            </div>
                            <div className="flex justify-between border-b pb-2">
                                <span className="text-sm text-text-subtle">외함 사이즈</span>
                                <span className="text-sm font-medium">
                                    {enclosureSize
                                        ? `${enclosureSize[0]}×${enclosureSize[1]}×${enclosureSize[2]}`
                                        : enclosureItem?.name?.replace("HDS-", "") || "-"}
                                </span>
                            </div>
                            <div className="flex justify-between border-b pb-2">
                                <span className="text-sm text-text-subtle">메인차단기</span>
                                <span className="text-sm font-medium">
                                    {mainBreaker ? `${mainBreaker.name} ${mainBreaker.spec}` : "-"}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* 금액 요약 */}
                    <div className="rounded-lg border bg-surface-secondary p-4 space-y-3">
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-text-subtle">공급가액</span>
                            <span className="text-lg font-medium">{totalPrice.toLocaleString()}원</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-text-subtle">부가세 (10%)</span>
                            <span className="text-lg font-medium">{Math.round(totalPrice * 0.1).toLocaleString()}원</span>
                        </div>
                        <div className="flex justify-between items-center border-t pt-3">
                            <span className="text-base font-bold text-text-strong">합계 (VAT 포함)</span>
                            <span className="text-2xl font-bold text-brand">{totalPriceWithVat.toLocaleString()}원</span>
                        </div>
                    </div>

                    {/* NOTE 섹션 - API에서 전달받은 브랜드/외함 정보 사용 */}
                    <div className="rounded-lg border p-4 bg-amber-50/50">
                        <p className="text-sm text-text-subtle">
                            {"< NOTE > 1. 차단기: "}{estimate.brand || "상도차단기"}
                            {", 외함: "}{estimate.enclosure_type || "옥내노출"} {estimate.enclosure_material || "STEEL 1.6T"}
                        </p>
                    </div>

                    {/* AI 검증 결과 */}
                    {estimate.ai_verification && (
                        <div className={cn(
                            "rounded-lg border p-3 text-sm",
                            estimate.ai_verification.passed
                                ? "bg-green-50 border-green-200 text-green-700"
                                : "bg-red-50 border-red-200 text-red-700"
                        )}>
                            {estimate.ai_verification.summary}
                        </div>
                    )}
                </div>
            ) : (
                /* 내역서 탭 */
                <div className="space-y-4">
                    {/* 분전반 정보 헤더 */}
                    <div className="grid grid-cols-3 gap-4 rounded-lg bg-surface-secondary p-3">
                        <div>
                            <span className="text-xs text-text-subtle">분전반명</span>
                            <p className="text-sm font-medium">{panel?.panel_id || "-"}</p>
                        </div>
                        <div>
                            <span className="text-xs text-text-subtle">외함</span>
                            <p className="text-sm font-medium">{enclosureItem?.spec || "-"}</p>
                        </div>
                        <div>
                            <span className="text-xs text-text-subtle">품목 수</span>
                            <p className="text-sm font-medium">{items.length}개</p>
                        </div>
                    </div>

                    {/* 품목 테이블 */}
                    {items.length > 0 && (
                        <div className="overflow-hidden rounded-lg border">
                            <table className="w-full text-sm">
                                <thead className="bg-surface-secondary">
                                    <tr>
                                        <th className="px-3 py-2 text-left font-medium w-8">No</th>
                                        <th className="px-3 py-2 text-left font-medium">품명</th>
                                        <th className="px-3 py-2 text-left font-medium">규격</th>
                                        <th className="px-3 py-2 text-center font-medium">단위</th>
                                        <th className="px-3 py-2 text-right font-medium">수량</th>
                                        <th className="px-3 py-2 text-right font-medium">단가</th>
                                        <th className="px-3 py-2 text-right font-medium">금액</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y">
                                    {items.map((item, index) => {
                                        const unitPrice = item.unit_price || item.unitPrice || 0;
                                        const supplyPrice = item.supply_price || item.amount || unitPrice * item.quantity;
                                        return (
                                            <tr key={index} className="hover:bg-surface-secondary/50">
                                                <td className="px-3 py-2 text-text-subtle">{index + 1}</td>
                                                <td className="px-3 py-2 font-medium">{item.name}</td>
                                                <td className="px-3 py-2 text-text-subtle">{item.spec || "-"}</td>
                                                <td className="px-3 py-2 text-center">{item.unit}</td>
                                                <td className="px-3 py-2 text-right">{item.quantity}</td>
                                                <td className="px-3 py-2 text-right">
                                                    {unitPrice.toLocaleString()}
                                                </td>
                                                <td className="px-3 py-2 text-right font-medium">
                                                    {supplyPrice.toLocaleString()}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                                <tfoot className="bg-surface-secondary font-medium">
                                    <tr>
                                        <td colSpan={6} className="px-3 py-2 text-right">소계</td>
                                        <td className="px-3 py-2 text-right">{totalPrice.toLocaleString()}원</td>
                                    </tr>
                                    <tr className="border-t">
                                        <td colSpan={6} className="px-3 py-2 text-right font-bold">합계</td>
                                        <td className="px-3 py-2 text-right font-bold text-brand">{totalPrice.toLocaleString()}원</td>
                                    </tr>
                                </tfoot>
                            </table>
                        </div>
                    )}

                    {/* 다운로드 버튼 */}
                    {estimate.documents && (
                        <div className="flex gap-2 justify-end">
                            {estimate.documents.excel_url && (
                                <a
                                    href={getFileUrl(estimate.documents.excel_url)}
                                    className="inline-flex items-center gap-1 px-3 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700"
                                    download
                                >
                                    <Download className="h-4 w-4" />
                                    Excel 다운로드
                                </a>
                            )}
                            {estimate.documents.pdf_url && (
                                <a
                                    href={getFileUrl(estimate.documents.pdf_url)}
                                    className="inline-flex items-center gap-1 px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700"
                                    download
                                >
                                    <Download className="h-4 w-4" />
                                    PDF 다운로드
                                </a>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

/**
 * ERP 테이블 컴포넌트
 */
function ERPTable({ data }: { data: Record<string, unknown> }) {
    const tableData = data as {
        headers?: string[];
        rows?: Array<Record<string, unknown>>;
        total?: number;
    };

    if (!tableData.rows || tableData.rows.length === 0) {
        return (
            <div className="flex h-40 items-center justify-center text-text-subtle">
                데이터가 없습니다
            </div>
        );
    }

    const headers = tableData.headers || Object.keys(tableData.rows[0]);

    return (
        <div className="space-y-2">
            <div className="overflow-hidden rounded-lg border">
                <table className="w-full text-sm">
                    <thead className="bg-surface-secondary">
                        <tr>
                            {headers.map((header, index) => (
                                <th key={index} className="px-3 py-2 text-left font-medium">
                                    {header}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="divide-y">
                        {tableData.rows.map((row, rowIndex) => (
                            <tr key={rowIndex} className="hover:bg-surface-secondary/50">
                                {headers.map((header, colIndex) => (
                                    <td key={colIndex} className="px-3 py-2">
                                        {String(row[header] ?? "-")}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            {tableData.total !== undefined && (
                <p className="text-right text-sm text-text-subtle">
                    총 {tableData.total}건
                </p>
            )}
        </div>
    );
}

/**
 * 캘린더 이벤트 컴포넌트
 */
function CalendarEvents({ data }: { data: Record<string, unknown> }) {
    // 단일 이벤트 또는 이벤트 배열 처리
    let events: Array<{
        id: string;
        title: string;
        start: string;
        end?: string;
        description?: string;
        type?: string;
        customer?: string;
        completed?: boolean;
    }> = [];

    if (data.events && Array.isArray(data.events)) {
        events = data.events;
    } else if (data.id && data.title) {
        // 단일 이벤트
        events = [data as typeof events[0]];
    }

    // 일정 유형별 색상
    const getTypeColor = (type?: string) => {
        switch (type) {
            case "delivery":
                return { bg: "bg-orange-100", text: "text-orange-600", label: "납품" };
            case "meeting":
                return { bg: "bg-blue-100", text: "text-blue-600", label: "미팅" };
            case "reminder":
                return { bg: "bg-purple-100", text: "text-purple-600", label: "알림" };
            case "task":
            default:
                return { bg: "bg-green-100", text: "text-green-600", label: "작업" };
        }
    };

    if (events.length === 0) {
        return (
            <div className="flex h-40 flex-col items-center justify-center text-text-subtle">
                <Calendar className="h-12 w-12 mb-3 opacity-50" />
                <p>일정이 없습니다</p>
                <p className="text-xs mt-1">AI에게 "일정 추가해줘"라고 말해보세요</p>
            </div>
        );
    }

    // 날짜별 그룹화
    const groupedEvents = events.reduce((acc, event) => {
        const dateKey = event.start?.slice(0, 10) || "unknown";
        if (!acc[dateKey]) {
            acc[dateKey] = [];
        }
        acc[dateKey].push(event);
        return acc;
    }, {} as Record<string, typeof events>);

    const sortedDates = Object.keys(groupedEvents).sort();

    return (
        <div className="space-y-6">
            {/* 요약 정보 */}
            {events.length > 1 && (
                <div className="rounded-lg bg-surface-secondary p-4 flex items-center justify-between">
                    <div>
                        <span className="text-sm text-text-subtle">총 일정</span>
                        <p className="text-2xl font-bold text-brand">{events.length}건</p>
                    </div>
                    <div className="flex gap-4">
                        {["delivery", "meeting", "task"].map((type) => {
                            const count = events.filter(e => e.type === type).length;
                            const color = getTypeColor(type);
                            return count > 0 ? (
                                <div key={type} className="text-center">
                                    <span className={cn("text-xs px-2 py-0.5 rounded-full", color.bg, color.text)}>
                                        {color.label}
                                    </span>
                                    <p className="text-sm font-medium mt-1">{count}</p>
                                </div>
                            ) : null;
                        })}
                    </div>
                </div>
            )}

            {/* 날짜별 일정 목록 */}
            {sortedDates.map((dateKey) => {
                const dateEvents = groupedEvents[dateKey];
                const dateObj = new Date(dateKey);
                const isToday = dateKey === new Date().toISOString().slice(0, 10);

                return (
                    <div key={dateKey}>
                        {/* 날짜 헤더 */}
                        <div className="flex items-center gap-2 mb-3">
                            <div className={cn(
                                "px-3 py-1 rounded-full text-sm font-medium",
                                isToday ? "bg-brand text-white" : "bg-surface-secondary text-text-strong"
                            )}>
                                {isToday ? "오늘" : dateObj.toLocaleDateString("ko-KR", {
                                    month: "short",
                                    day: "numeric",
                                    weekday: "short",
                                })}
                            </div>
                            <span className="text-xs text-text-subtle">{dateEvents.length}건</span>
                        </div>

                        {/* 해당 날짜 일정 목록 */}
                        <div className="space-y-2 ml-2">
                            {dateEvents.map((event) => {
                                const typeColor = getTypeColor(event.type);
                                const time = event.start?.includes("T")
                                    ? event.start.slice(11, 16)
                                    : "";

                                return (
                                    <div
                                        key={event.id}
                                        className={cn(
                                            "flex items-start gap-3 rounded-lg border p-3 transition-colors",
                                            event.completed ? "bg-surface-secondary opacity-60" : "hover:bg-surface-secondary/50"
                                        )}
                                    >
                                        {/* 시간 표시 */}
                                        <div className="w-12 text-center shrink-0">
                                            {time ? (
                                                <span className="text-sm font-medium text-text-strong">{time}</span>
                                            ) : (
                                                <span className="text-xs text-text-subtle">종일</span>
                                            )}
                                        </div>

                                        {/* 유형 표시 막대 */}
                                        <div className={cn("w-1 rounded-full self-stretch", typeColor.bg.replace("100", "500"))} />

                                        {/* 일정 내용 */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2">
                                                <h4 className={cn(
                                                    "font-medium text-text-strong truncate",
                                                    event.completed && "line-through"
                                                )}>
                                                    {event.title}
                                                </h4>
                                                <span className={cn(
                                                    "text-xs px-1.5 py-0.5 rounded shrink-0",
                                                    typeColor.bg, typeColor.text
                                                )}>
                                                    {typeColor.label}
                                                </span>
                                            </div>

                                            {event.customer && (
                                                <p className="text-xs text-text-subtle mt-1">
                                                    거래처: {event.customer}
                                                </p>
                                            )}

                                            {event.description && (
                                                <p className="text-sm text-text mt-1 line-clamp-2">
                                                    {event.description}
                                                </p>
                                            )}

                                            {event.end && (
                                                <div className="mt-1 flex items-center gap-1 text-xs text-text-subtle">
                                                    <Clock className="h-3 w-3" />
                                                    <span>
                                                        ~ {new Date(event.end).toLocaleTimeString("ko-KR", {
                                                            hour: "2-digit",
                                                            minute: "2-digit",
                                                        })}
                                                    </span>
                                                </div>
                                            )}
                                        </div>

                                        {/* 완료 체크 */}
                                        {event.completed && (
                                            <div className="shrink-0">
                                                <Check className="h-5 w-5 text-green-500" />
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

/**
 * 차트 뷰 컴포넌트 (간단한 바 차트)
 */
function ChartView({ data }: { data: Record<string, unknown> }) {
    const chartData = data as {
        type?: "bar" | "line" | "pie";
        labels?: string[];
        values?: number[];
        title?: string;
    };

    if (!chartData.values || chartData.values.length === 0) {
        return (
            <div className="flex h-40 items-center justify-center text-text-subtle">
                차트 데이터가 없습니다
            </div>
        );
    }

    const maxValue = Math.max(...chartData.values);

    return (
        <div className="space-y-4">
            {chartData.title && (
                <h4 className="text-center font-medium text-text-strong">{chartData.title}</h4>
            )}
            <div className="space-y-2">
                {chartData.values.map((value, index) => {
                    const percentage = (value / maxValue) * 100;
                    const label = chartData.labels?.[index] || `항목 ${index + 1}`;
                    return (
                        <div key={index} className="flex items-center gap-3">
                            <span className="w-24 shrink-0 truncate text-sm text-text-subtle">
                                {label}
                            </span>
                            <div className="flex-1">
                                <div className="h-6 w-full overflow-hidden rounded-full bg-surface-secondary">
                                    <div
                                        className="h-full rounded-full bg-brand transition-all"
                                        style={{ width: `${percentage}%` }}
                                    />
                                </div>
                            </div>
                            <span className="w-20 shrink-0 text-right text-sm font-medium">
                                {value.toLocaleString()}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

/**
 * 도면 미리보기 컴포넌트
 */
function DrawingPreview({ data }: { data: Record<string, unknown> }) {
    const drawingData = data as {
        estimate_id?: string;
        drawings?: {
            panel_layout?: string;
            wiring_diagram?: string;
            single_line?: string;
        };
        generated_count?: number;
    };

    const drawings = [
        { key: "panel_layout", label: "패널 레이아웃", icon: Layers },
        { key: "wiring_diagram", label: "배선도", icon: Grid3X3 },
        { key: "single_line", label: "단선도", icon: FileText },
    ];

    const availableDrawings = drawings.filter(
        (d) => drawingData.drawings?.[d.key as keyof typeof drawingData.drawings]
    );

    if (availableDrawings.length === 0) {
        return (
            <div className="flex h-40 items-center justify-center text-text-subtle">
                생성된 도면이 없습니다
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* 헤더 정보 */}
            <div className="rounded-lg bg-surface-secondary p-4">
                <div className="flex items-center justify-between">
                    <div>
                        <span className="text-xs text-text-subtle">견적번호</span>
                        <p className="font-mono text-sm font-medium">
                            {drawingData.estimate_id || "-"}
                        </p>
                    </div>
                    <div>
                        <span className="text-xs text-text-subtle">생성된 도면</span>
                        <p className="text-sm font-medium">
                            {drawingData.generated_count || 0}개
                        </p>
                    </div>
                </div>
            </div>

            {/* 도면 목록 */}
            <div className="grid gap-4">
                {availableDrawings.map((drawing) => {
                    const DrawingIcon = drawing.icon;
                    const url =
                        drawingData.drawings?.[
                            drawing.key as keyof typeof drawingData.drawings
                        ];
                    return (
                        <div
                            key={drawing.key}
                            className="flex items-center justify-between rounded-lg border p-4"
                        >
                            <div className="flex items-center gap-3">
                                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand/10">
                                    <DrawingIcon className="h-5 w-5 text-brand" />
                                </div>
                                <div>
                                    <h4 className="font-medium text-text-strong">
                                        {drawing.label}
                                    </h4>
                                    <p className="text-xs text-text-subtle">
                                        {url ? "생성 완료" : "생성 중..."}
                                    </p>
                                </div>
                            </div>
                            {url && (
                                <div className="flex gap-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => window.open(getFileUrl(url), "_blank")}
                                    >
                                        <Eye className="mr-1 h-4 w-4" />
                                        보기
                                    </Button>
                                    <a
                                        href={getFileUrl(url)}
                                        download
                                        className="inline-flex items-center gap-1 px-3 py-1.5 text-sm border rounded-md hover:bg-surface-secondary"
                                    >
                                        <Download className="h-4 w-4" />
                                        다운로드
                                    </a>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

/**
 * JSON 뷰어 컴포넌트
 */
function JSONViewer({ data }: { data: Record<string, unknown> }) {
    return (
        <pre className="overflow-auto rounded-lg bg-surface-secondary p-4 text-xs">
            <code>{JSON.stringify(data, null, 2)}</code>
        </pre>
    );
}

/**
 * 미리보기 모달 컴포넌트 (이메일/팩스/프린트 기능)
 */
function PreviewModal({
    visualization,
    onClose,
}: {
    visualization: VisualizationData;
    onClose: () => void;
}) {
    const [activeAction, setActiveAction] = useState<"email" | "fax" | "print" | null>(null);
    const [email, setEmail] = useState("");
    const [faxNumber, setFaxNumber] = useState("");
    const [isSending, setIsSending] = useState(false);
    const [sendResult, setSendResult] = useState<{ success: boolean; message: string } | null>(null);

    const data = visualization.data as Record<string, unknown>;
    const estimate = data as {
        estimate_id?: string;
        id?: string;
        customer?: string;
        total_price?: number;
        total_price_with_vat?: number;
        documents?: {
            excel_url?: string;
            pdf_url?: string;
        };
    };

    const estimateId = estimate.estimate_id || estimate.id || "-";
    const totalPrice = estimate.total_price || 0;
    const totalPriceWithVat = estimate.total_price_with_vat || Math.round(totalPrice * 1.1);

    // 이메일 전송
    const handleSendEmail = async () => {
        if (!email) {
            setSendResult({ success: false, message: "이메일 주소를 입력해주세요." });
            return;
        }
        setIsSending(true);
        try {
            // API 호출 (추후 실제 구현)
            await new Promise(resolve => setTimeout(resolve, 1500));
            setSendResult({ success: true, message: `${email}로 견적서가 전송되었습니다.` });
            setEmail("");
        } catch {
            setSendResult({ success: false, message: "이메일 전송에 실패했습니다." });
        } finally {
            setIsSending(false);
        }
    };

    // 팩스 전송
    const handleSendFax = async () => {
        if (!faxNumber) {
            setSendResult({ success: false, message: "팩스 번호를 입력해주세요." });
            return;
        }
        setIsSending(true);
        try {
            // API 호출 (추후 실제 구현)
            await new Promise(resolve => setTimeout(resolve, 1500));
            setSendResult({ success: true, message: `${faxNumber}로 팩스가 전송되었습니다.` });
            setFaxNumber("");
        } catch {
            setSendResult({ success: false, message: "팩스 전송에 실패했습니다." });
        } finally {
            setIsSending(false);
        }
    };

    // 프린트
    const handlePrint = () => {
        window.print();
        setSendResult({ success: true, message: "인쇄 대화상자가 열렸습니다." });
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* 오버레이 */}
            <div
                className="absolute inset-0 bg-black/50"
                onClick={onClose}
            />

            {/* 모달 */}
            <div className="relative z-10 w-full max-w-4xl max-h-[90vh] bg-surface rounded-xl shadow-2xl overflow-hidden">
                {/* 모달 헤더 */}
                <div className="flex items-center justify-between border-b px-6 py-4 bg-surface-secondary">
                    <div className="flex items-center gap-3">
                        <Receipt className="h-6 w-6 text-brand" />
                        <div>
                            <h2 className="text-lg font-bold text-text-strong">견적서 미리보기</h2>
                            <p className="text-sm text-text-subtle">견적번호: {estimateId}</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-surface rounded-full transition-colors"
                    >
                        <X className="h-5 w-5 text-text-subtle" />
                    </button>
                </div>

                {/* 모달 바디 */}
                <div className="flex h-[calc(90vh-140px)]">
                    {/* 왼쪽: 미리보기 */}
                    <div className="flex-1 overflow-auto p-6 border-r bg-surface-secondary">
                        <div className="bg-surface rounded-lg shadow-sm p-8 min-h-full">
                            {/* 견적서 표지 미리보기 */}
                            <div className="text-center border-b-2 border-text-strong pb-6 mb-6">
                                <h1 className="text-3xl font-bold tracking-widest text-text-strong">견 적 서</h1>
                                <p className="text-sm text-text-subtle mt-1">QUOTATION</p>
                            </div>

                            <div className="grid grid-cols-2 gap-8 mb-8">
                                <div className="space-y-4">
                                    <div className="flex border-b border-surface-tertiary pb-2">
                                        <span className="w-24 text-sm text-text-subtle">견적번호</span>
                                        <span className="font-mono font-medium text-text-strong">{estimateId}</span>
                                    </div>
                                    <div className="flex border-b border-surface-tertiary pb-2">
                                        <span className="w-24 text-sm text-text-subtle">거래처</span>
                                        <span className="font-medium text-text-strong">{estimate.customer || "-"}</span>
                                    </div>
                                </div>
                                <div className="space-y-4">
                                    <div className="flex border-b border-surface-tertiary pb-2">
                                        <span className="w-24 text-sm text-text-subtle">작성일</span>
                                        <span className="font-medium text-text-strong">
                                            {new Date().toLocaleDateString("ko-KR", {
                                                year: "numeric",
                                                month: "long",
                                                day: "numeric"
                                            })}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* 금액 */}
                            <div className="bg-surface-secondary rounded-lg p-6 mb-6">
                                <div className="flex justify-between items-center mb-3">
                                    <span className="text-text-subtle">공급가액</span>
                                    <span className="text-xl text-text-strong">{totalPrice.toLocaleString()}원</span>
                                </div>
                                <div className="flex justify-between items-center mb-3">
                                    <span className="text-text-subtle">부가세 (10%)</span>
                                    <span className="text-xl text-text-strong">{Math.round(totalPrice * 0.1).toLocaleString()}원</span>
                                </div>
                                <div className="flex justify-between items-center pt-3 border-t-2 border-surface-tertiary">
                                    <span className="text-lg font-bold text-text-strong">합계 (VAT 포함)</span>
                                    <span className="text-2xl font-bold text-brand">{totalPriceWithVat.toLocaleString()}원</span>
                                </div>
                            </div>

                            {/* 회사 정보 */}
                            <div className="text-center text-sm text-text-subtle mt-8 pt-6 border-t border-surface-tertiary">
                                <p className="font-medium text-text">한국산업전기 KIS</p>
                                <p>전화: 000-0000-0000 | 팩스: 000-0000-0000</p>
                            </div>
                        </div>
                    </div>

                    {/* 오른쪽: 액션 패널 */}
                    <div className="w-80 p-6 space-y-4">
                        <h3 className="font-semibold text-text-strong mb-4">전송 옵션</h3>

                        {/* 이메일 전송 */}
                        <div
                            className={cn(
                                "rounded-lg border p-4 cursor-pointer transition-all",
                                activeAction === "email"
                                    ? "border-blue-500 bg-blue-50"
                                    : "hover:border-surface-tertiary hover:bg-surface-secondary"
                            )}
                            onClick={() => setActiveAction("email")}
                        >
                            <div className="flex items-center gap-3 mb-3">
                                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100">
                                    <Mail className="h-5 w-5 text-blue-600" />
                                </div>
                                <div>
                                    <h4 className="font-medium text-text-strong">이메일 전송</h4>
                                    <p className="text-xs text-text-subtle">PDF로 이메일 발송</p>
                                </div>
                            </div>
                            {activeAction === "email" && (
                                <div className="space-y-3 pt-3 border-t border-surface-tertiary">
                                    <input
                                        type="email"
                                        placeholder="이메일 주소 입력"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="w-full px-3 py-2 text-sm border border-surface-tertiary rounded-lg bg-surface text-text focus:outline-none focus:ring-2 focus:ring-brand"
                                    />
                                    <Button
                                        size="sm"
                                        className="w-full"
                                        onClick={handleSendEmail}
                                        disabled={isSending}
                                    >
                                        {isSending ? "전송 중..." : "이메일 전송"}
                                        <Send className="ml-1 h-4 w-4" />
                                    </Button>
                                </div>
                            )}
                        </div>

                        {/* 팩스 전송 */}
                        <div
                            className={cn(
                                "rounded-lg border p-4 cursor-pointer transition-all",
                                activeAction === "fax"
                                    ? "border-green-500 bg-green-50"
                                    : "hover:border-surface-tertiary hover:bg-surface-secondary"
                            )}
                            onClick={() => setActiveAction("fax")}
                        >
                            <div className="flex items-center gap-3 mb-3">
                                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100">
                                    <Phone className="h-5 w-5 text-green-600" />
                                </div>
                                <div>
                                    <h4 className="font-medium text-text-strong">팩스 전송</h4>
                                    <p className="text-xs text-text-subtle">인터넷 팩스로 발송</p>
                                </div>
                            </div>
                            {activeAction === "fax" && (
                                <div className="space-y-3 pt-3 border-t border-surface-tertiary">
                                    <input
                                        type="tel"
                                        placeholder="팩스 번호 입력 (예: 02-1234-5678)"
                                        value={faxNumber}
                                        onChange={(e) => setFaxNumber(e.target.value)}
                                        className="w-full px-3 py-2 text-sm border border-surface-tertiary rounded-lg bg-surface text-text focus:outline-none focus:ring-2 focus:ring-green-500"
                                    />
                                    <Button
                                        size="sm"
                                        className="w-full bg-green-600 hover:bg-green-700"
                                        onClick={handleSendFax}
                                        disabled={isSending}
                                    >
                                        {isSending ? "전송 중..." : "팩스 전송"}
                                        <FileOutput className="ml-1 h-4 w-4" />
                                    </Button>
                                </div>
                            )}
                        </div>

                        {/* 프린트 */}
                        <div
                            className={cn(
                                "rounded-lg border p-4 cursor-pointer transition-all",
                                activeAction === "print"
                                    ? "border-purple-500 bg-purple-50"
                                    : "hover:border-surface-tertiary hover:bg-surface-secondary"
                            )}
                            onClick={() => setActiveAction("print")}
                        >
                            <div className="flex items-center gap-3 mb-3">
                                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100">
                                    <Printer className="h-5 w-5 text-purple-600" />
                                </div>
                                <div>
                                    <h4 className="font-medium text-text-strong">프린트</h4>
                                    <p className="text-xs text-text-subtle">직접 인쇄하기</p>
                                </div>
                            </div>
                            {activeAction === "print" && (
                                <div className="pt-3 border-t border-surface-tertiary">
                                    <Button
                                        size="sm"
                                        className="w-full bg-purple-600 hover:bg-purple-700"
                                        onClick={handlePrint}
                                    >
                                        인쇄 대화상자 열기
                                        <Printer className="ml-1 h-4 w-4" />
                                    </Button>
                                </div>
                            )}
                        </div>

                        {/* 결과 메시지 */}
                        {sendResult && (
                            <div className={cn(
                                "rounded-lg p-3 text-sm",
                                sendResult.success
                                    ? "bg-green-50 text-green-700 border border-green-200"
                                    : "bg-red-50 text-red-700 border border-red-200"
                            )}>
                                {sendResult.message}
                            </div>
                        )}

                        {/* 다운로드 링크 */}
                        {estimate.documents && (
                            <div className="pt-4 border-t border-surface-tertiary space-y-2">
                                <h4 className="text-sm font-medium text-text-subtle">파일 다운로드</h4>
                                {estimate.documents.pdf_url && (
                                    <a
                                        href={getFileUrl(estimate.documents.pdf_url)}
                                        download
                                        className="flex items-center gap-2 px-3 py-2 text-sm bg-red-50 text-red-700 rounded-lg hover:bg-red-100"
                                    >
                                        <Download className="h-4 w-4" />
                                        PDF 다운로드
                                    </a>
                                )}
                                {estimate.documents.excel_url && (
                                    <a
                                        href={getFileUrl(estimate.documents.excel_url)}
                                        download
                                        className="flex items-center gap-2 px-3 py-2 text-sm bg-green-50 text-green-700 rounded-lg hover:bg-green-100"
                                    >
                                        <Download className="h-4 w-4" />
                                        Excel 다운로드
                                    </a>
                                )}
                            </div>
                        )}
                    </div>
                </div>

                {/* 모달 푸터 */}
                <div className="flex justify-end gap-3 px-6 py-4 border-t bg-surface-secondary">
                    <Button variant="outline" onClick={onClose}>
                        닫기
                    </Button>
                </div>
            </div>
        </div>
    );
}
