"use client";

import React, { useState, useCallback, useEffect, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import { AIManagerLayout } from "@/components/ai-manager/AIManagerLayout";
import { ChatPanel, AIModelType } from "@/components/ai-manager/ChatPanel";
import { VisualizationPanel } from "@/components/ai-manager/VisualizationPanel";
import { useTabController, useChatStorage } from "@/components/ai-manager/hooks";
import { API_BASE_URL, getFileUrl } from "@/config/api";

/**
 * AI 매니저 메인 페이지
 *
 * 구현 계획 참조: 절대코어파일/AI_매니저_구현계획_V1.0.md
 *
 * 주요 기능:
 * 1. ChatGPT 스타일 채팅 인터페이스 (좌측 40%)
 * 2. 시각화/결과 패널 (우측 60%)
 * 3. 탭 통합 컨트롤러 (견적/ERP/캘린더/도면/설정 제어)
 * 4. 드래그앤드롭 파일 업로드
 * 5. 실시간 스트리밍 응답
 * 6. 채팅 히스토리 저장 (localStorage)
 */

// 학습/검색 액션 결과 타입
export interface ActionResult {
    type: "learning" | "learned_search" | "price_update" | "knowledge_save";
    status: "success" | "error";
    category?: string;
    item_name?: string;
    new_price?: number;
    old_price?: number | null;
    query?: string;
    result_count?: number;
    results?: Array<{
        id: string;
        item_name?: string;
        new_price?: number;
        content?: string;
        source?: string;
    }>;
}

// 채팅 메시지 타입
export interface ChatMessage {
    id: string;
    role: "user" | "assistant" | "system";
    content: string;
    timestamp: Date;
    attachments?: FileAttachment[];
    visualizations?: VisualizationData[];
    command?: ExecutedCommand;
    actionResult?: ActionResult;
}

// 파일 첨부 타입
export interface FileAttachment {
    id: string;
    name: string;
    type: string;
    size: number;
    url?: string;
    thumbnail?: string;
    status: "uploading" | "processing" | "ready" | "error";
    extractedData?: unknown;
}

// 시각화 데이터 타입
export interface VisualizationData {
    id: string;
    type: "estimate_preview" | "erp_table" | "calendar_event" | "drawing_preview" | "chart" | "json";
    title: string;
    data: unknown;
    actions?: VisualizationAction[];
}

// 시각화 액션 타입
export interface VisualizationAction {
    id: string;
    label: string;
    icon?: string;
    action: () => void;
}

// 실행된 명령 타입
export interface ExecutedCommand {
    id: string;
    tab: "quote" | "erp" | "calendar" | "drawings" | "settings";
    operation: "create" | "read" | "update" | "delete" | "execute";
    entity: string;
    params?: Record<string, unknown>;
    result?: unknown;
    status: "pending" | "success" | "error";
    errorMessage?: string;
}

export default function AIManagerPage() {
    // URL searchParams에서 세션 ID 읽기 (사이드바/대시보드에서 전달)
    const searchParams = useSearchParams();
    const loadSessionId = searchParams.get('loadSession');

    // 채팅 저장소 훅 사용 (세션 ID 전달)
    const chatStorage = useChatStorage(loadSessionId);
    const { messages, addMessage, isLoaded, sessions, loadSession, createNewSession } = chatStorage;

    const [inputValue, setInputValue] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [attachments, setAttachments] = useState<FileAttachment[]>([]);

    // AI 모델 설정 (기본값: Claude Sonnet 4.6)
    const [aiModel, setAiModel] = useState<AIModelType>("claude-sonnet");

    // localStorage에서 AI 모델 설정 로드
    useEffect(() => {
        try {
            const savedModel = localStorage.getItem('kis-ai-model');
            if (savedModel && ['claude-haiku', 'claude-sonnet', 'claude-opus'].includes(savedModel)) {
                setAiModel(savedModel as AIModelType);
            }
        } catch (e) {
            console.error('AI 모델 설정 로드 실패:', e);
        }
    }, []);

    // AI 모델 변경 핸들러
    const handleModelChange = useCallback((model: AIModelType) => {
        setAiModel(model);
        localStorage.setItem('kis-ai-model', model);
    }, []);

    // 견적 관련 키워드 체크 함수
    const isEstimateRequest = useCallback((message: string): boolean => {
        const estimateKeywords = [
            '견적', '분전반', 'estimate', '차단기', 'ELB', 'MCCB',
            '외함', '메인', '분기', 'AF', '암페어', 'A메인',
            '상도', 'LS', '누전', '배선용', '부스바'
        ];
        const lowerMessage = message.toLowerCase();
        return estimateKeywords.some(keyword =>
            lowerMessage.includes(keyword.toLowerCase())
        );
    }, []);

    // 시각화 상태 - sessionStorage에서 복원
    const [currentVisualization, setCurrentVisualization] = useState<VisualizationData | null>(() => {
        if (typeof window !== "undefined") {
            try {
                const saved = sessionStorage.getItem("ai_manager_current_viz");
                return saved ? JSON.parse(saved) : null;
            } catch { return null; }
        }
        return null;
    });
    const [visualizationHistory, setVisualizationHistory] = useState<VisualizationData[]>(() => {
        if (typeof window !== "undefined") {
            try {
                const saved = sessionStorage.getItem("ai_manager_viz_history");
                return saved ? JSON.parse(saved) : [];
            } catch { return []; }
        }
        return [];
    });

    // 시각화 상태 변경 시 sessionStorage에 저장
    useEffect(() => {
        if (currentVisualization) {
            sessionStorage.setItem("ai_manager_current_viz", JSON.stringify(currentVisualization));
        }
    }, [currentVisualization]);

    useEffect(() => {
        if (visualizationHistory.length > 0) {
            // 최근 20건만 저장 (메모리 절약)
            const toSave = visualizationHistory.slice(-20);
            sessionStorage.setItem("ai_manager_viz_history", JSON.stringify(toSave));
        }
    }, [visualizationHistory]);

    // 패널 크기 상태
    const [chatPanelWidth, setChatPanelWidth] = useState(40); // 퍼센트

    // 시각화 패널 접힘 상태 (AIManagerLayout와 공유) - sessionStorage에서 복원
    const [visualizationCollapsed, setVisualizationCollapsed] = useState(() => {
        if (typeof window !== "undefined") {
            try {
                return sessionStorage.getItem("ai_manager_viz_collapsed") === "true";
            } catch { return false; }
        }
        return false;
    });

    // 시각화 패널 접힘 상태 저장
    useEffect(() => {
        sessionStorage.setItem("ai_manager_viz_collapsed", String(visualizationCollapsed));
    }, [visualizationCollapsed]);

    // 탭 컨트롤러
    const tabController = useTabController();

    // 메시지 전송
    const sendMessage = useCallback(async () => {
        if (!inputValue.trim() && attachments.length === 0) return;

        const userMessage: ChatMessage = {
            id: `msg-${Date.now()}`,
            role: "user",
            content: inputValue,
            timestamp: new Date(),
            attachments: attachments.length > 0 ? [...attachments] : undefined,
        };

        addMessage(userMessage);
        setInputValue("");
        setAttachments([]);
        setIsLoading(true);

        try {
            // 견적 요청인 경우 자동으로 Opus 모델 사용
            const effectiveModel = isEstimateRequest(inputValue) ? "claude-opus" : aiModel;

            // AI 응답 요청 - 선택된 모델 포함
            const response = await fetch(`${API_BASE_URL}/v1/ai-manager/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: inputValue,
                    model: effectiveModel, // 견적 요청 시 Opus, 그 외에는 선택된 모델
                    attachments: attachments.map(a => ({
                        id: a.id,
                        name: a.name,
                        type: a.type,
                        url: a.url,
                        extractedData: a.extractedData,
                    })),
                    context: {
                        recentMessages: messages.slice(-30),
                        currentVisualization: currentVisualization?.type,
                        savedEstimates: (() => {
                            try {
                                const saved = localStorage.getItem("savedEstimates");
                                if (saved) {
                                    const parsed = JSON.parse(saved);
                                    // 저장된 견적 요약 정보만 전송 (전체 데이터는 너무 큼)
                                    return parsed.map((e: { id: string; customer: string; panelName: string; totalPriceWithVat: number; savedAt: string }) => ({
                                        id: e.id,
                                        customer: e.customer,
                                        panelName: e.panelName,
                                        totalPriceWithVat: e.totalPriceWithVat,
                                        savedAt: e.savedAt,
                                    }));
                                }
                            } catch { /* ignore */ }
                            return [];
                        })(),
                    },
                }),
            });

            if (!response.ok) {
                throw new Error("AI 응답 요청 실패");
            }

            const data = await response.json();

            // AI 응답 메시지 추가
            const assistantMessage: ChatMessage = {
                id: `msg-${Date.now()}`,
                role: "assistant",
                content: data.message,
                timestamp: new Date(),
                visualizations: data.visualizations,
                command: data.command,
                actionResult: data.action_result,
            };

            addMessage(assistantMessage);

            // 시각화 데이터 업데이트
            if (data.visualizations && data.visualizations.length > 0) {
                setCurrentVisualization(data.visualizations[0]);
                setVisualizationHistory(prev => [...prev, ...data.visualizations]);
            }

            // 명령 실행 결과 처리
            if (data.command) {
                await handleCommandExecution(data.command);
            }
        } catch (error) {
            console.error("AI 요청 오류:", error);
            const errorMessage: ChatMessage = {
                id: `msg-${Date.now()}`,
                role: "assistant",
                content: `죄송합니다. 요청 처리 중 오류가 발생했습니다: ${error instanceof Error ? error.message : "알 수 없는 오류"}`,
                timestamp: new Date(),
            };
            addMessage(errorMessage);
        } finally {
            setIsLoading(false);
        }
    }, [inputValue, attachments, messages, currentVisualization, addMessage, aiModel, isEstimateRequest]);

    // 명령 실행 핸들러
    const handleCommandExecution = useCallback(async (command: ExecutedCommand) => {
        try {
            const result = await tabController.executeCommand(command);

            // 결과 시각화
            if (result.visualization) {
                setCurrentVisualization(result.visualization);
            }
        } catch (error) {
            console.error("명령 실행 오류:", error);
        }
    }, [tabController]);

    // 파일 업로드 핸들러
    const handleFileUpload = useCallback(async (files: FileList) => {
        const newAttachments: FileAttachment[] = [];

        for (const file of Array.from(files)) {
            const attachment: FileAttachment = {
                id: `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                name: file.name,
                type: file.type,
                size: file.size,
                status: "uploading",
            };
            newAttachments.push(attachment);
        }

        setAttachments(prev => [...prev, ...newAttachments]);

        // 파일 업로드 및 처리
        const fileArray = Array.from(files);
        for (let i = 0; i < newAttachments.length; i++) {
            const file = fileArray[i];
            const attachment = newAttachments[i];

            // 파일이 유효한지 확인 (undefined 방지)
            if (!file || !(file instanceof File)) {
                console.error("Invalid file at index", i, file);
                setAttachments(prev =>
                    prev.map(a =>
                        a.id === attachment.id ? { ...a, status: "error" } : a
                    )
                );
                continue;
            }

            try {
                const formData = new FormData();
                formData.append("file", file);

                const response = await fetch(`${API_BASE_URL}/v1/ai-manager/upload`, {
                    method: "POST",
                    body: formData,
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    console.error("Upload error:", errorText);
                    throw new Error("업로드 실패");
                }

                const data = await response.json();

                setAttachments(prev =>
                    prev.map(a =>
                        a.id === attachment.id
                            ? { ...a, status: "ready", url: data.url, extractedData: data.extractedData }
                            : a
                    )
                );
            } catch (error) {
                console.error("File upload error:", error);
                setAttachments(prev =>
                    prev.map(a =>
                        a.id === attachment.id ? { ...a, status: "error" } : a
                    )
                );
            }
        }
    }, []);

    // 첨부 파일 삭제
    const removeAttachment = useCallback((id: string) => {
        setAttachments(prev => prev.filter(a => a.id !== id));
    }, []);

    // 드래그앤드롭 핸들러
    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files);
        }
    }, [handleFileUpload]);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
    }, []);

    // 패널 리사이즈 핸들러
    const handlePanelResize = useCallback((newWidth: number) => {
        setChatPanelWidth(Math.min(Math.max(newWidth, 30), 70));
    }, []);

    // 시각화 액션 실행 (action.id 기반 처리)
    const executeVisualizationAction = useCallback((action: VisualizationAction) => {
        // 백엔드에서 오는 액션에는 action 함수가 없으므로 id 기반으로 처리
        if (action.action && typeof action.action === "function") {
            action.action();
            return;
        }

        // action.id 기반 핸들링
        const vizData = currentVisualization?.data as Record<string, unknown> | undefined;
        const documents = vizData?.documents as { excel_url?: string; pdf_url?: string } | undefined;

        switch (action.id) {
            case "download_excel":
                if (documents?.excel_url) {
                    window.open(getFileUrl(documents.excel_url), "_blank");
                } else {
                    alert("Excel 파일이 준비되지 않았습니다.");
                }
                break;
            case "download_pdf":
            case "download":
                if (documents?.pdf_url) {
                    window.open(getFileUrl(documents.pdf_url), "_blank");
                } else {
                    alert("PDF 파일이 준비되지 않았습니다.");
                }
                break;
            case "edit":
                tabController.navigateTo("quote", { id: vizData?.estimate_id || vizData?.id });
                break;
            case "confirm":
                // 견적서 확정 - 로컬 스토리지에 저장
                if (vizData) {
                    try {
                        const savedEstimates = JSON.parse(localStorage.getItem("savedEstimates") || "[]");
                        const confirmData = {
                            id: vizData.estimate_id || vizData.id || `EST-${Date.now()}`,
                            customer: (vizData as Record<string, unknown>).customer || "미지정",
                            panelName: (vizData as Record<string, unknown>).panel_name || "분전반",
                            totalPrice: (vizData as Record<string, unknown>).total_price || 0,
                            totalPriceWithVat: (vizData as Record<string, unknown>).total_price_with_vat || 0,
                            confirmedAt: new Date().toISOString(),
                            savedAt: new Date().toISOString(),
                            status: "confirmed",
                            data: vizData
                        };

                        // 중복 확인 후 저장
                        const existingIndex = savedEstimates.findIndex((e: { id: string }) => e.id === confirmData.id);
                        if (existingIndex >= 0) {
                            savedEstimates[existingIndex] = confirmData;
                        } else {
                            savedEstimates.push(confirmData);
                        }

                        localStorage.setItem("savedEstimates", JSON.stringify(savedEstimates));
                        alert(`견적서가 확정되었습니다.\n\n견적번호: ${confirmData.id}\n거래처: ${confirmData.customer}\n금액: ${Number(confirmData.totalPriceWithVat).toLocaleString()}원 (VAT포함)`);
                    } catch (error) {
                        console.error("견적서 확정 오류:", error);
                        alert("견적서 확정 중 오류가 발생했습니다.");
                    }
                } else {
                    alert("확정할 견적 데이터가 없습니다.");
                }
                break;
            case "copy":
                if (vizData) {
                    navigator.clipboard.writeText(JSON.stringify(vizData, null, 2));
                    alert("데이터가 클립보드에 복사되었습니다.");
                }
                break;
            case "print":
                window.print();
                break;
            case "export":
                // ERP 테이블 Excel 내보내기 (CSV 형식)
                if (vizData) {
                    try {
                        let csvContent = "";
                        const dataArray = Array.isArray(vizData) ? vizData : [vizData];

                        if (dataArray.length > 0) {
                            // 헤더 생성
                            const headers = Object.keys(dataArray[0] as object);
                            csvContent += "\uFEFF"; // UTF-8 BOM for Excel
                            csvContent += headers.join(",") + "\n";

                            // 데이터 행 생성
                            dataArray.forEach((row: unknown) => {
                                const rowData = row as Record<string, unknown>;
                                const values = headers.map(header => {
                                    const value = rowData[header];
                                    if (value === null || value === undefined) return "";
                                    const strValue = String(value);
                                    // 쉼표나 줄바꿈이 포함된 경우 따옴표로 감싸기
                                    if (strValue.includes(",") || strValue.includes("\n") || strValue.includes("\"")) {
                                        return `"${strValue.replace(/"/g, '""')}"`;
                                    }
                                    return strValue;
                                });
                                csvContent += values.join(",") + "\n";
                            });

                            // 다운로드
                            const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
                            const url = URL.createObjectURL(blob);
                            const link = document.createElement("a");
                            link.href = url;
                            link.download = `export_${new Date().toISOString().split("T")[0]}.csv`;
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                            URL.revokeObjectURL(url);

                            alert("Excel(CSV) 파일이 다운로드되었습니다.");
                        } else {
                            alert("내보낼 데이터가 없습니다.");
                        }
                    } catch (error) {
                        console.error("Excel 내보내기 오류:", error);
                        alert("Excel 내보내기 중 오류가 발생했습니다.");
                    }
                } else {
                    alert("내보낼 데이터가 없습니다.");
                }
                break;
            default:
                break;
        }
    }, [currentVisualization, tabController]);

    // 대화 내보내기 핸들러
    const handleExportChat = useCallback((format: 'md' | 'txt') => {
        if (messages.length === 0) {
            alert("내보낼 대화가 없습니다.");
            return;
        }

        const content = messages.map(m => {
            const role = m.role === 'user' ? '사용자' : m.role === 'assistant' ? 'AI' : '시스템';
            if (format === 'md') {
                return `### ${role}\n${m.content}\n`;
            }
            return `[${role}] ${m.content}\n`;
        }).join('\n');

        const blob = new Blob([content], {
            type: format === 'md' ? 'text/markdown;charset=utf-8' : 'text/plain;charset=utf-8'
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat_export_${new Date().toISOString().slice(0, 10)}.${format}`;
        a.click();
        URL.revokeObjectURL(url);
    }, [messages]);

    // 현재 응답 복사 핸들러
    const handleCopyLastResponse = useCallback(() => {
        const lastAssistant = [...messages].reverse().find(m => m.role === 'assistant');
        if (!lastAssistant) {
            alert("복사할 AI 응답이 없습니다.");
            return;
        }
        navigator.clipboard.writeText(lastAssistant.content).then(() => {
            alert("현재 AI 응답이 클립보드에 복사되었습니다.");
        }).catch(() => {
            alert("복사 중 오류가 발생했습니다.");
        });
    }, [messages]);

    // 내보내기 핸들러 메모이제이션
    const exportHandlers = useMemo(() => ({
        exportMd: () => handleExportChat('md'),
        exportTxt: () => handleExportChat('txt'),
        copyLastResponse: handleCopyLastResponse,
    }), [handleExportChat, handleCopyLastResponse]);

    // 로딩 중일 때 표시
    if (!isLoaded) {
        return (
            <div className="flex h-full items-center justify-center bg-surface-secondary">
                <div className="text-lg text-text-subtle">로딩 중...</div>
            </div>
        );
    }

    return (
        <AIManagerLayout
            chatPanelWidth={chatPanelWidth}
            onPanelResize={handlePanelResize}
            hasMessages={messages.length > 0}
            hasVisualization={currentVisualization !== null}
            isVisualizationCollapsed={visualizationCollapsed}
            onVisualizationCollapsedChange={setVisualizationCollapsed}
        >
            {/* 채팅 패널 */}
            <ChatPanel
                messages={messages}
                inputValue={inputValue}
                onInputChange={setInputValue}
                onSend={sendMessage}
                isLoading={isLoading}
                attachments={attachments}
                onFileUpload={handleFileUpload}
                onRemoveAttachment={removeAttachment}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                sessions={sessions}
                onLoadSession={loadSession}
                onNewChat={createNewSession}
                selectedModel={aiModel}
                onModelChange={handleModelChange}
                onExportMd={exportHandlers.exportMd}
                onExportTxt={exportHandlers.exportTxt}
                onCopyLastResponse={exportHandlers.copyLastResponse}
            />

            {/* 시각화 패널 */}
            <VisualizationPanel
                currentVisualization={currentVisualization}
                history={visualizationHistory}
                onSelectHistory={(viz) => setCurrentVisualization(viz)}
                onExecuteAction={executeVisualizationAction}
                tabController={tabController}
                onClose={() => setVisualizationCollapsed(true)}
            />
        </AIManagerLayout>
    );
}
