"use client";

import React, { useRef, useEffect, useCallback, useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
    Send,
    Paperclip,
    X,
    Image,
    FileText,
    File,
    Loader2,
    Bot,
    AlertCircle,
    Plus,
    History,
    ChevronDown,
    MessageSquare,
    BookOpen,
    DollarSign,
    Lightbulb,
    Search,
    CheckCircle2,
    Cpu,
    Zap,
    Sparkles,
    Check,
    Download,
    Copy,
    MoreHorizontal,
} from "lucide-react";
import type { ChatMessage, FileAttachment, ActionResult } from "@/app/ai-manager/page";
import type { ChatSession } from "./hooks/useChatStorage";

// AI 모델 타입 정의
export type AIModelType = "claude-haiku" | "claude-sonnet" | "claude-opus";

export interface AIModelOption {
    id: AIModelType;
    name: string;
    description: string;
    icon: React.ElementType;
    color: string;
}

// 사용 가능한 AI 모델 목록
export const AI_MODELS: AIModelOption[] = [
    {
        id: "claude-haiku",
        name: "Claude Haiku 4.6",
        description: "빠른 응답, 간단한 작업",
        icon: Zap,
        color: "text-emerald-500",
    },
    {
        id: "claude-sonnet",
        name: "Claude Sonnet 4.6",
        description: "균형잡힌 성능 (기본)",
        icon: Cpu,
        color: "text-blue-500",
    },
    {
        id: "claude-opus",
        name: "Claude Opus 4.6",
        description: "최고 성능, 복잡한 작업",
        icon: Sparkles,
        color: "text-violet-500",
    },
];

/**
 * 프롬프트 인젝션 패턴을 제거하는 기본 살균 함수.
 * 프론트엔드 1차 방어 - 백엔드에서도 반드시 살균해야 합니다.
 */
function sanitizeInput(text: string): string {
    const injectionPatterns: RegExp[] = [
        /system\s*:/gi,
        /assistant\s*:/gi,
        /\[INST\]/gi,
        /\[\/INST\]/gi,
        /<\|im_start\|>/gi,
        /<\|im_end\|>/gi,
        /<<SYS>>/gi,
        /<<\/SYS>>/gi,
    ];

    let sanitized = text;
    for (const pattern of injectionPatterns) {
        sanitized = sanitized.replace(pattern, "");
    }
    return sanitized.trim();
}

interface ChatPanelProps {
    messages: ChatMessage[];
    inputValue: string;
    onInputChange: (value: string) => void;
    onSend: () => void;
    isLoading: boolean;
    attachments: FileAttachment[];
    onFileUpload: (files: FileList) => void;
    onRemoveAttachment: (id: string) => void;
    onDrop: (e: React.DragEvent) => void;
    onDragOver: (e: React.DragEvent) => void;
    // 세션 관리 props
    sessions: ChatSession[];
    onLoadSession: (sessionId: string) => void;
    onNewChat: () => void;
    // AI 모델 선택 props
    selectedModel: AIModelType;
    onModelChange: (model: AIModelType) => void;
    // 내보내기 props
    onExportMd?: () => void;
    onExportTxt?: () => void;
    onCopyLastResponse?: () => void;
}

/**
 * AI 매니저 채팅 패널
 *
 * ChatGPT 스타일 인터페이스:
 * - 메시지 리스트 (스크롤)
 * - 입력 영역 (하단 고정)
 * - 파일 첨부 기능
 * - 드래그앤드롭 지원
 */
export function ChatPanel({
    messages,
    inputValue,
    onInputChange,
    onSend,
    isLoading,
    attachments,
    onFileUpload,
    onRemoveAttachment,
    onDrop,
    onDragOver,
    sessions,
    onLoadSession,
    onNewChat,
    selectedModel,
    onModelChange,
    onExportMd,
    onExportTxt,
    onCopyLastResponse,
}: ChatPanelProps) {
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const pendingQuickActionRef = useRef(false);
    const [showInputModelSelector, setShowInputModelSelector] = useState(false); // 입력창 모델 선택기
    const [showExportMenu, setShowExportMenu] = useState(false); // 내보내기 메뉴
    const exportMenuRef = useRef<HTMLDivElement>(null);

    // 내보내기 메뉴 외부 클릭 시 닫기
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (exportMenuRef.current && !exportMenuRef.current.contains(e.target as Node)) {
                setShowExportMenu(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // 현재 선택된 모델 정보
    const currentModel = AI_MODELS.find(m => m.id === selectedModel) || AI_MODELS[1];

    // 메시지 추가 시 스크롤
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // 텍스트 영역 자동 높이 조절
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
        }
    }, [inputValue]);

    // 외부 클릭 시 모델 선택기 닫기
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (showInputModelSelector) {
                const target = e.target as HTMLElement;
                // 모델 선택기 버튼이나 팝업 내부가 아닌 경우 닫기
                if (!target.closest('[data-model-selector]')) {
                    setShowInputModelSelector(false);
                }
            }
        };

        document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    }, [showInputModelSelector]);

    // 살균 후 전송: 프롬프트 인젝션 패턴 제거 후 onSend 호출
    const sanitizedSend = useCallback(() => {
        const cleaned = sanitizeInput(inputValue);
        if (cleaned !== inputValue) {
            onInputChange(cleaned);
        }
        onSend();
    }, [inputValue, onInputChange, onSend]);

    // 빠른 액션: inputValue가 설정된 후 onSend 호출 (setTimeout 대체)
    useEffect(() => {
        if (pendingQuickActionRef.current && inputValue.trim()) {
            pendingQuickActionRef.current = false;
            sanitizedSend();
        }
    }, [inputValue, sanitizedSend]);

    // 빠른 액션 핸들러: inputValue를 설정하고 pendingQuickAction 플래그 켜기
    const handleQuickAction = useCallback((text: string) => {
        pendingQuickActionRef.current = true;
        onInputChange(sanitizeInput(text));
    }, [onInputChange]);

    // 키보드 이벤트 핸들러
    const handleKeyDown = useCallback(
        (e: React.KeyboardEvent) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sanitizedSend();
            }
        },
        [sanitizedSend]
    );

    // 파일 선택 핸들러
    const handleFileSelect = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            if (e.target.files && e.target.files.length > 0) {
                onFileUpload(e.target.files);
            }
            // 같은 파일 재업로드 허용을 위해 input value 리셋
            e.target.value = "";
        },
        [onFileUpload]
    );

    // 파일 아이콘 선택
    const getFileIcon = (type: string) => {
        if (type.startsWith("image/")) return Image;
        if (type.includes("pdf") || type.includes("document")) return FileText;
        return File;
    };

    // 파일 크기 포맷
    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    // 첫 화면 (메시지 없음) - Claude.ai 스타일 중앙 레이아웃
    if (messages.length === 0) {
        return (
            <div
                className="flex h-full flex-col bg-gradient-to-b from-bg via-bg to-surface-secondary/30"
                onDrop={onDrop}
                onDragOver={onDragOver}
            >
                {/* 중앙 컨텐츠 영역 */}
                <div className="flex-1 flex flex-col items-center justify-center px-6">
                    {/* 환영 메시지 */}
                    <div className="flex flex-col items-center mb-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
                        {/* 로고 with 글로우 효과 */}
                        <div className="relative mb-6">
                            <div className="absolute inset-0 rounded-3xl bg-brand/20 blur-2xl scale-150" />
                            <div className="relative flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-brand via-brand to-brand-strong shadow-xl shadow-brand/25">
                                <Bot className="h-10 w-10 text-white drop-shadow-sm" />
                            </div>
                        </div>
                        <h1 className="text-3xl font-bold text-text-strong mb-3 tracking-tight">
                            무엇을 도와드릴까요?
                        </h1>
                        <p className="text-text-subtle text-center max-w-md text-base leading-relaxed">
                            견적 생성, 자재 조회, 보고서 작성 등<br />
                            다양한 업무를 AI가 도와드립니다
                        </p>
                    </div>

                    {/* 제안 버튼들 - 호버 시 상승 효과 */}
                    <div className="grid grid-cols-2 gap-4 mb-10 w-full max-w-xl animate-in fade-in slide-in-from-bottom-6 duration-700 delay-150">
                        <button
                            onClick={() => handleQuickAction("상도 4P 100A 메인, 분기 ELB 3P 30A 5개로 견적해줘")}
                            className="group flex items-center gap-4 rounded-2xl border border-border bg-surface/80 backdrop-blur-sm p-5 text-left hover:bg-surface hover:shadow-lg hover:shadow-brand/5 hover:-translate-y-0.5 transition-all duration-200"
                        >
                            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-brand/10 to-brand/5 group-hover:from-brand/20 group-hover:to-brand/10 transition-colors">
                                <FileText className="h-6 w-6 text-brand" />
                            </div>
                            <div>
                                <div className="text-sm font-semibold text-text group-hover:text-text-strong transition-colors">견적서 작성</div>
                                <div className="text-xs text-text-subtle mt-0.5">분전반 견적 자동 생성</div>
                            </div>
                        </button>
                        <button
                            onClick={() => handleQuickAction("SBE-104 차단기 단가 알려줘")}
                            className="group flex items-center gap-4 rounded-2xl border border-border bg-surface/80 backdrop-blur-sm p-5 text-left hover:bg-surface hover:shadow-lg hover:shadow-emerald-500/5 hover:-translate-y-0.5 transition-all duration-200"
                        >
                            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 group-hover:from-emerald-500/20 group-hover:to-emerald-500/10 transition-colors">
                                <Search className="h-6 w-6 text-emerald-600" />
                            </div>
                            <div>
                                <div className="text-sm font-semibold text-text group-hover:text-text-strong transition-colors">자재 조회</div>
                                <div className="text-xs text-text-subtle mt-0.5">가격 및 재고 확인</div>
                            </div>
                        </button>
                        <button
                            onClick={() => handleQuickAction("이번 달 매출 현황 보여줘")}
                            className="group flex items-center gap-4 rounded-2xl border border-border bg-surface/80 backdrop-blur-sm p-5 text-left hover:bg-surface hover:shadow-lg hover:shadow-blue-500/5 hover:-translate-y-0.5 transition-all duration-200"
                        >
                            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500/10 to-blue-500/5 group-hover:from-blue-500/20 group-hover:to-blue-500/10 transition-colors">
                                <DollarSign className="h-6 w-6 text-blue-600" />
                            </div>
                            <div>
                                <div className="text-sm font-semibold text-text group-hover:text-text-strong transition-colors">매출 분석</div>
                                <div className="text-xs text-text-subtle mt-0.5">실적 및 통계 조회</div>
                            </div>
                        </button>
                        <button
                            onClick={() => handleQuickAction("도움말")}
                            className="group flex items-center gap-4 rounded-2xl border border-border bg-surface/80 backdrop-blur-sm p-5 text-left hover:bg-surface hover:shadow-lg hover:shadow-violet-500/5 hover:-translate-y-0.5 transition-all duration-200"
                        >
                            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500/10 to-violet-500/5 group-hover:from-violet-500/20 group-hover:to-violet-500/10 transition-colors">
                                <Lightbulb className="h-6 w-6 text-violet-600" />
                            </div>
                            <div>
                                <div className="text-sm font-semibold text-text group-hover:text-text-strong transition-colors">사용 가이드</div>
                                <div className="text-xs text-text-subtle mt-0.5">기능 안내 보기</div>
                            </div>
                        </button>
                    </div>

                    {/* 중앙 입력창 - 글로우 효과 */}
                    <div className="w-full max-w-2xl animate-in fade-in slide-in-from-bottom-8 duration-700 delay-300">
                        {/* 첨부 파일 미리보기 */}
                        {attachments.length > 0 && (
                            <div className="flex flex-wrap gap-2 mb-3">
                                {attachments.map((attachment) => {
                                    const FileIcon = getFileIcon(attachment.type);
                                    return (
                                        <div
                                            key={attachment.id}
                                            className={cn(
                                                "flex items-center gap-2 rounded-xl border px-3 py-2 bg-surface/80 backdrop-blur-sm",
                                                attachment.status === "uploading" && "bg-surface-secondary",
                                                attachment.status === "error" && "border-red-300 bg-red-50"
                                            )}
                                        >
                                            {attachment.status === "uploading" ? (
                                                <Loader2 className="h-4 w-4 animate-spin text-text-subtle" />
                                            ) : attachment.status === "error" ? (
                                                <AlertCircle className="h-4 w-4 text-red-500" />
                                            ) : (
                                                <FileIcon className="h-4 w-4 text-text-subtle" />
                                            )}
                                            <span className="max-w-[150px] truncate text-xs font-medium">
                                                {attachment.name}
                                            </span>
                                            <button
                                                onClick={() => onRemoveAttachment(attachment.id)}
                                                className="ml-1 rounded-full p-0.5 hover:bg-surface-secondary"
                                            >
                                                <X className="h-3 w-3 text-text-subtle" />
                                            </button>
                                        </div>
                                    );
                                })}
                            </div>
                        )}

                        {/* 입력 박스 with 글로우 */}
                        <div className="relative group">
                            {/* 글로우 효과 */}
                            <div className="absolute -inset-0.5 rounded-2xl bg-gradient-to-r from-brand/20 via-transparent to-brand/20 opacity-0 group-focus-within:opacity-100 blur transition-opacity duration-300" />

                            <div className="relative flex items-end gap-2 rounded-2xl border border-border bg-surface shadow-lg shadow-black/5 p-4 group-focus-within:border-brand transition-colors">
                                {/* 모델 선택 팝업 (입력창 위에 표시) */}
                                {showInputModelSelector && (
                                    <div
                                        data-model-selector
                                        className="absolute left-4 bottom-full z-50 mb-2 w-72 rounded-xl border border-border/30 bg-surface shadow-xl shadow-black/10"
                                        onClick={(e) => e.stopPropagation()}
                                    >
                                        <div className="p-2">
                                            {AI_MODELS.map((model) => {
                                                const ModelIcon = model.icon;
                                                const isSelected = model.id === selectedModel;
                                                return (
                                                    <button
                                                        key={model.id}
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            onModelChange(model.id);
                                                            setShowInputModelSelector(false);
                                                        }}
                                                        className={cn(
                                                            "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors",
                                                            isSelected
                                                                ? "bg-brand/10 border border-brand/20"
                                                                : "hover:bg-surface-secondary"
                                                        )}
                                                    >
                                                        <div className={cn(
                                                            "flex h-9 w-9 items-center justify-center rounded-lg",
                                                            isSelected ? "bg-brand/20" : "bg-surface-secondary"
                                                        )}>
                                                            <ModelIcon className={cn("h-5 w-5", model.color)} />
                                                        </div>
                                                        <div className="flex-1">
                                                            <div className="flex items-center gap-2">
                                                                <span className={cn(
                                                                    "text-sm font-medium",
                                                                    isSelected ? "text-brand" : "text-text"
                                                                )}>
                                                                    {model.name}
                                                                </span>
                                                                {isSelected && (
                                                                    <Check className="h-4 w-4 text-brand" />
                                                                )}
                                                            </div>
                                                            <span className="text-xs text-text-subtle">
                                                                {model.description}
                                                            </span>
                                                        </div>
                                                    </button>
                                                );
                                            })}
                                        </div>
                                        <div className="border-t border-border/20 px-3 py-2">
                                            <p className="text-[11px] text-text-subtle/70">
                                                💡 견적 작성 시 자동으로 Opus 사용
                                            </p>
                                        </div>
                                    </div>
                                )}

                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    multiple
                                    accept="image/*,.pdf,.xlsx,.xls,.csv,.doc,.docx,.txt,.dwg,.dxf"
                                    className="hidden"
                                    onChange={handleFileSelect}
                                />
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-10 w-10 shrink-0 text-text-subtle hover:text-text hover:bg-surface-secondary rounded-xl"
                                    onClick={() => fileInputRef.current?.click()}
                                    disabled={isLoading}
                                >
                                    <Paperclip className="h-5 w-5" />
                                </Button>

                                {/* 모델 선택 버튼 */}
                                <button
                                    data-model-selector
                                    onClick={() => setShowInputModelSelector(!showInputModelSelector)}
                                    className={cn(
                                        "flex items-center gap-1.5 shrink-0 rounded-lg border px-2.5 py-2 text-sm transition-all",
                                        "border-border/40 bg-surface-secondary/50 hover:bg-surface-secondary",
                                        showInputModelSelector && "border-brand/40 bg-surface-secondary"
                                    )}
                                    title="AI 모델 선택"
                                >
                                    <currentModel.icon className={cn("h-4 w-4", currentModel.color)} />
                                    <span className="text-xs font-medium text-text hidden sm:inline">{currentModel.name.split(' ').pop()}</span>
                                    <ChevronDown className={cn(
                                        "h-3 w-3 text-text-subtle transition-transform",
                                        showInputModelSelector && "rotate-180"
                                    )} />
                                </button>

                                <textarea
                                    ref={textareaRef}
                                    value={inputValue}
                                    onChange={(e) => onInputChange(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    placeholder="무엇이든 물어보세요..."
                                    className={cn(
                                        "w-full resize-none bg-transparent px-2 py-2",
                                        "focus:outline-none",
                                        "placeholder:text-text-subtle/70",
                                        "min-h-[40px] max-h-[200px]",
                                        "text-text text-base"
                                    )}
                                    rows={1}
                                    disabled={isLoading}
                                />

                                <Button
                                    size="icon"
                                    className="h-10 w-10 shrink-0 rounded-xl bg-brand hover:bg-brand-strong shadow-md shadow-brand/25 transition-all hover:shadow-lg hover:shadow-brand/30"
                                    onClick={sanitizedSend}
                                    disabled={isLoading || (!inputValue.trim() && attachments.length === 0)}
                                >
                                    {isLoading ? (
                                        <Loader2 className="h-5 w-5 animate-spin" />
                                    ) : (
                                        <Send className="h-5 w-5" />
                                    )}
                                </Button>
                            </div>
                        </div>

                        <p className="mt-4 text-center text-xs text-text-subtle/70">
                            Enter로 전송 · Shift+Enter로 줄바꿈 · 파일 드래그로 첨부
                        </p>
                    </div>
                </div>

                {/* 하단 최근 대화 - 더 세련된 스타일 */}
                {sessions.length > 0 && (
                    <div className="border-t border-border/50 bg-surface-secondary/30 backdrop-blur-sm px-6 py-4">
                        <div className="flex items-center gap-2 text-xs text-text-subtle mb-3">
                            <History className="h-3.5 w-3.5" />
                            <span className="font-medium">최근 대화</span>
                        </div>
                        <div className="flex gap-3 overflow-x-auto pb-1 scrollbar-hide">
                            {sessions.slice(0, 5).map((session) => (
                                <button
                                    key={session.id}
                                    onClick={() => onLoadSession(session.id)}
                                    className="flex items-center gap-2.5 shrink-0 rounded-xl border border-border bg-surface/80 backdrop-blur-sm px-4 py-2.5 hover:bg-surface hover:border-border hover:shadow-sm transition-all"
                                >
                                    <MessageSquare className="h-4 w-4 text-brand/70" />
                                    <span className="text-sm font-medium text-text max-w-[140px] truncate">
                                        {session.title}
                                    </span>
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        );
    }

    // 채팅 화면 (메시지 있음) - Claude.ai 스타일 + 사이드바
    return (
        <div
            className="flex h-full bg-bg"
            onDrop={onDrop}
            onDragOver={onDragOver}
        >
            {/* 메인 채팅 영역 */}
            <div className="flex-1 flex flex-col">
                {/* 헤더 */}
                <div className="flex items-center justify-between border-b border-border/50 px-4 py-3">
                    <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand to-brand-strong shadow-sm">
                            <Bot className="h-5 w-5 text-white" />
                        </div>
                        <span className="font-semibold text-lg text-text-strong">AI 매니저</span>
                    </div>
                    <div className="flex items-center gap-1">
                        {/* 내보내기 버튼 */}
                        {messages.length > 0 && (onExportMd || onExportTxt || onCopyLastResponse) && (
                            <div className="relative" ref={exportMenuRef}>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setShowExportMenu(!showExportMenu)}
                                    className="flex items-center gap-2 text-sm text-text-subtle hover:text-text hover:bg-surface-secondary/50 rounded-lg px-3"
                                >
                                    <Download className="h-4 w-4" />
                                    내보내기
                                </Button>
                                {showExportMenu && (
                                    <div className="absolute right-0 top-full z-50 mt-1 w-52 rounded-lg border border-border/40 bg-surface shadow-lg">
                                        <div className="py-1">
                                            {onExportMd && (
                                                <button
                                                    onClick={() => { onExportMd(); setShowExportMenu(false); }}
                                                    className="flex w-full items-center gap-2.5 px-3 py-2 text-sm text-text hover:bg-surface-secondary transition"
                                                >
                                                    <FileText className="h-4 w-4 text-blue-600" />
                                                    대화 내보내기 (MD)
                                                </button>
                                            )}
                                            {onExportTxt && (
                                                <button
                                                    onClick={() => { onExportTxt(); setShowExportMenu(false); }}
                                                    className="flex w-full items-center gap-2.5 px-3 py-2 text-sm text-text hover:bg-surface-secondary transition"
                                                >
                                                    <FileText className="h-4 w-4 text-text-subtle" />
                                                    대화 내보내기 (TXT)
                                                </button>
                                            )}
                                            {onCopyLastResponse && (
                                                <>
                                                    <div className="mx-2 my-1 border-t border-border/30" />
                                                    <button
                                                        onClick={() => { onCopyLastResponse(); setShowExportMenu(false); }}
                                                        className="flex w-full items-center gap-2.5 px-3 py-2 text-sm text-text hover:bg-surface-secondary transition"
                                                    >
                                                        <Copy className="h-4 w-4 text-brand" />
                                                        현재 응답 복사
                                                    </button>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                        {/* 새 채팅 버튼 */}
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={onNewChat}
                            className="flex items-center gap-2 text-sm text-text-subtle hover:text-text hover:bg-surface-secondary/50 rounded-lg px-3"
                        >
                            <Plus className="h-4 w-4" />
                            새 대화
                        </Button>
                    </div>
                </div>

            {/* 메시지 목록 - Claude.ai 스타일: 중앙 정렬 + 양쪽 여백 */}
            <div className="flex-1 overflow-y-auto">
                <div className="mx-auto max-w-3xl px-6 py-8 space-y-8">
                    {messages.map((message) => (
                        <MessageBubble key={message.id} message={message} />
                    ))}

                    {/* 로딩 인디케이터 */}
                    {isLoading && (
                        <div className="flex items-start gap-4">
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand to-brand-strong shadow-sm">
                                <Bot className="h-5 w-5 text-white" />
                            </div>
                            <div className="flex items-center gap-3 pt-2">
                                <div className="flex gap-1">
                                    <span className="w-2 h-2 rounded-full bg-brand/60 animate-bounce" style={{ animationDelay: "0ms" }} />
                                    <span className="w-2 h-2 rounded-full bg-brand/60 animate-bounce" style={{ animationDelay: "150ms" }} />
                                    <span className="w-2 h-2 rounded-full bg-brand/60 animate-bounce" style={{ animationDelay: "300ms" }} />
                                </div>
                                <span className="text-sm text-text-subtle">생각하는 중...</span>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* 하단 입력 영역 - Claude.ai 스타일 */}
            <div className="border-t border-border/50 bg-bg">
                <div className="mx-auto max-w-3xl px-6 py-4">
                    {/* 첨부 파일 미리보기 */}
                    {attachments.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-3">
                            {attachments.map((attachment) => {
                                const FileIcon = getFileIcon(attachment.type);
                                return (
                                    <div
                                        key={attachment.id}
                                        className={cn(
                                            "flex items-center gap-2 rounded-xl border border-border/40 bg-surface/80 px-3 py-2",
                                            attachment.status === "uploading" && "bg-surface-secondary",
                                            attachment.status === "error" && "border-red-300 bg-red-50"
                                        )}
                                    >
                                        {attachment.status === "uploading" ? (
                                            <Loader2 className="h-4 w-4 animate-spin text-text-subtle" />
                                        ) : attachment.status === "error" ? (
                                            <AlertCircle className="h-4 w-4 text-red-500" />
                                        ) : (
                                            <FileIcon className="h-4 w-4 text-text-subtle" />
                                        )}
                                        <div className="flex flex-col">
                                            <span className="max-w-[150px] truncate text-sm font-medium">
                                                {attachment.name}
                                            </span>
                                            <span className="text-xs text-text-subtle">
                                                {formatFileSize(attachment.size)}
                                            </span>
                                        </div>
                                        <button
                                            onClick={() => onRemoveAttachment(attachment.id)}
                                            className="ml-1 rounded-full p-1 hover:bg-surface-secondary transition-colors"
                                        >
                                            <X className="h-3.5 w-3.5 text-text-subtle" />
                                        </button>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {/* 입력 박스 */}
                    <div className="relative group">
                        {/* 포커스 시 글로우 효과 */}
                        <div className="absolute -inset-0.5 rounded-2xl bg-gradient-to-r from-brand/20 via-transparent to-brand/20 opacity-0 group-focus-within:opacity-100 blur transition-opacity duration-300" />

                        <div className="relative flex items-end gap-3 rounded-2xl border border-border bg-surface shadow-sm p-3">
                            {/* 모델 선택 팝업 (입력창 위에 표시) */}
                            {showInputModelSelector && (
                                <div
                                    data-model-selector
                                    className="absolute left-3 bottom-full z-50 mb-2 w-72 rounded-xl border border-border/30 bg-surface shadow-xl shadow-black/10"
                                    onClick={(e) => e.stopPropagation()}
                                >
                                    <div className="p-2">
                                        {AI_MODELS.map((model) => {
                                            const ModelIcon = model.icon;
                                            const isSelected = model.id === selectedModel;
                                            return (
                                                <button
                                                    key={model.id}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        onModelChange(model.id);
                                                        setShowInputModelSelector(false);
                                                    }}
                                                    className={cn(
                                                        "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors",
                                                        isSelected
                                                            ? "bg-brand/10 border border-brand/20"
                                                            : "hover:bg-surface-secondary"
                                                    )}
                                                >
                                                    <div className={cn(
                                                        "flex h-9 w-9 items-center justify-center rounded-lg",
                                                        isSelected ? "bg-brand/20" : "bg-surface-secondary"
                                                    )}>
                                                        <ModelIcon className={cn("h-5 w-5", model.color)} />
                                                    </div>
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-2">
                                                            <span className={cn(
                                                                "text-sm font-medium",
                                                                isSelected ? "text-brand" : "text-text"
                                                            )}>
                                                                {model.name}
                                                            </span>
                                                            {isSelected && (
                                                                <Check className="h-4 w-4 text-brand" />
                                                            )}
                                                        </div>
                                                        <span className="text-xs text-text-subtle">
                                                            {model.description}
                                                        </span>
                                                    </div>
                                                </button>
                                            );
                                        })}
                                    </div>
                                    <div className="border-t border-border/20 px-3 py-2">
                                        <p className="text-[11px] text-text-subtle/70">
                                            💡 견적 작성 시 자동으로 Opus 사용
                                        </p>
                                    </div>
                                </div>
                            )}

                            {/* 파일 첨부 버튼 */}
                            <input
                                ref={fileInputRef}
                                type="file"
                                multiple
                                accept="image/*,.pdf,.xlsx,.xls,.csv,.doc,.docx,.txt,.dwg,.dxf"
                                className="hidden"
                                onChange={handleFileSelect}
                            />
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-10 w-10 shrink-0 text-text-subtle hover:text-text hover:bg-surface-secondary/50 rounded-xl"
                                onClick={() => fileInputRef.current?.click()}
                                disabled={isLoading}
                            >
                                <Paperclip className="h-5 w-5" />
                            </Button>

                            {/* 모델 선택 버튼 */}
                            <button
                                data-model-selector
                                onClick={() => setShowInputModelSelector(!showInputModelSelector)}
                                className={cn(
                                    "flex items-center gap-1.5 shrink-0 rounded-lg border px-2.5 py-2 text-sm transition-all",
                                    "border-border/40 bg-surface-secondary/50 hover:bg-surface-secondary",
                                    showInputModelSelector && "border-brand/40 bg-surface-secondary"
                                )}
                                title="AI 모델 선택"
                            >
                                <currentModel.icon className={cn("h-4 w-4", currentModel.color)} />
                                <span className="text-xs font-medium text-text hidden sm:inline">{currentModel.name.split(' ').pop()}</span>
                                <ChevronDown className={cn(
                                    "h-3 w-3 text-text-subtle transition-transform",
                                    showInputModelSelector && "rotate-180"
                                )} />
                            </button>

                            {/* 텍스트 입력 - 글씨 키움 */}
                            <textarea
                                ref={textareaRef}
                                value={inputValue}
                                onChange={(e) => onInputChange(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="메시지를 입력하세요..."
                                className={cn(
                                    "w-full resize-none bg-transparent px-1 py-2",
                                    "focus:outline-none",
                                    "placeholder:text-text-subtle/70",
                                    "min-h-[44px] max-h-[200px]",
                                    "text-base text-text leading-relaxed"
                                )}
                                rows={1}
                                disabled={isLoading}
                            />

                            {/* 전송 버튼 */}
                            <Button
                                size="icon"
                                className="h-10 w-10 shrink-0 rounded-xl shadow-sm"
                                onClick={sanitizedSend}
                                disabled={isLoading || (!inputValue.trim() && attachments.length === 0)}
                            >
                                {isLoading ? (
                                    <Loader2 className="h-5 w-5 animate-spin" />
                                ) : (
                                    <Send className="h-5 w-5" />
                                )}
                            </Button>
                        </div>
                    </div>

                    {/* 힌트 텍스트 */}
                    <p className="mt-2 text-center text-xs text-text-subtle/60">
                        Enter로 전송 · Shift+Enter로 줄바꿈
                    </p>
                </div>
            </div>
            </div> {/* 메인 채팅 영역 닫기 */}
        </div>
    );
}

/**
 * 메시지 버블 컴포넌트 - Claude.ai 스타일
 * 유저: 말풍선 스타일 (우측 정렬, 배경색)
 * AI: 말풍선 없이 깔끔한 설명글 스타일 (좌측 정렬)
 */
function MessageBubble({ message }: { message: ChatMessage }) {
    const isUser = message.role === "user";

    // 유저 메시지 - 말풍선 스타일
    if (isUser) {
        return (
            <div className="flex justify-end">
                <div className="max-w-[85%]">
                    {/* 첨부 파일 표시 */}
                    {message.attachments && message.attachments.length > 0 && (
                        <div className="mb-2 flex flex-wrap justify-end gap-2">
                            {message.attachments.map((att) => (
                                <div
                                    key={att.id}
                                    className="flex items-center gap-1.5 rounded-lg bg-surface-secondary/70 px-3 py-1.5 text-sm"
                                >
                                    <Paperclip className="h-3.5 w-3.5 text-text-subtle" />
                                    <span className="max-w-[120px] truncate text-text-subtle">{att.name}</span>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* 유저 메시지 말풍선 */}
                    <div className="rounded-2xl rounded-tr-md bg-brand/10 border border-brand/20 px-5 py-3.5">
                        <div className="whitespace-pre-wrap text-base leading-relaxed text-text">
                            {message.content}
                        </div>
                    </div>

                    {/* 타임스탬프 */}
                    <div className="mt-1.5 text-right text-xs text-text-subtle/60">
                        {new Date(message.timestamp).toLocaleTimeString("ko-KR", {
                            hour: "2-digit",
                            minute: "2-digit",
                        })}
                    </div>
                </div>
            </div>
        );
    }

    // AI 메시지 - 말풍선 없이 깔끔한 설명글 스타일
    return (
        <div className="flex items-start gap-4">
            {/* AI 아바타 */}
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand to-brand-strong shadow-sm">
                <Bot className="h-5 w-5 text-white" />
            </div>

            {/* AI 메시지 내용 - 말풍선 없이 */}
            <div className="flex-1 pt-1">
                {/* 첨부 파일 표시 */}
                {message.attachments && message.attachments.length > 0 && (
                    <div className="mb-3 flex flex-wrap gap-2">
                        {message.attachments.map((att) => (
                            <div
                                key={att.id}
                                className="flex items-center gap-1.5 rounded-lg bg-surface-secondary px-3 py-1.5 text-sm"
                            >
                                <Paperclip className="h-3.5 w-3.5 text-text-subtle" />
                                <span className="max-w-[120px] truncate text-text-subtle">{att.name}</span>
                            </div>
                        ))}
                    </div>
                )}

                {/* AI 메시지 텍스트 - 큰 글씨, 가독성 좋게 */}
                <div className="text-base leading-[1.8] text-text">
                    {message.content.split('\n').map((line, i) => {
                        // 볼드 텍스트 처리 (**텍스트**)
                        const parts = line.split(/(\*\*[^*]+\*\*)/g);

                        // 빈 줄 처리
                        if (line.trim() === '') {
                            return <div key={i} className="h-3" />;
                        }

                        // 리스트 아이템 처리 (- 로 시작)
                        if (line.trim().startsWith('- ')) {
                            return (
                                <div key={i} className="flex items-start gap-2 mt-1.5">
                                    <span className="text-brand mt-1.5">•</span>
                                    <p className="flex-1">
                                        {parts.map((part, j) => {
                                            if (part.startsWith('**') && part.endsWith('**')) {
                                                return (
                                                    <strong key={j} className="font-semibold text-text-strong">
                                                        {part.slice(2, -2)}
                                                    </strong>
                                                );
                                            }
                                            return <span key={j}>{part.replace(/^- /, '')}</span>;
                                        })}
                                    </p>
                                </div>
                            );
                        }

                        return (
                            <p key={i} className={i > 0 && message.content.split('\n')[i - 1].trim() !== '' ? "mt-3" : ""}>
                                {parts.map((part, j) => {
                                    if (part.startsWith('**') && part.endsWith('**')) {
                                        return (
                                            <strong key={j} className="font-semibold text-text-strong">
                                                {part.slice(2, -2)}
                                            </strong>
                                        );
                                    }
                                    return <span key={j}>{part}</span>;
                                })}
                            </p>
                        );
                    })}
                </div>

                {/* 명령 실행 결과 표시 - 에러 시에만 표시 */}
                {message.command && message.command.status === "error" && (
                    <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3">
                        <div className="flex items-center gap-2 text-sm text-red-700">
                            <AlertCircle className="h-4 w-4" />
                            <span className="font-medium">
                                {message.command.errorMessage || "처리 중 오류가 발생했습니다."}
                            </span>
                        </div>
                    </div>
                )}

                {/* 학습/검색 결과 표시 */}
                {message.actionResult && (
                    <div className="mt-4">
                        <ActionResultBadge actionResult={message.actionResult} />
                    </div>
                )}

                {/* 타임스탬프 */}
                <div className="mt-3 text-xs text-text-subtle/60">
                    {new Date(message.timestamp).toLocaleTimeString("ko-KR", {
                        hour: "2-digit",
                        minute: "2-digit",
                    })}
                </div>
            </div>
        </div>
    );
}

/**
 * 학습/검색 결과 배지 컴포넌트
 */
function ActionResultBadge({ actionResult }: { actionResult: ActionResult }) {
    const getIcon = () => {
        switch (actionResult.type) {
            case "learning":
            case "price_update":
                return <DollarSign className="h-3.5 w-3.5" />;
            case "learned_search":
                return <Search className="h-3.5 w-3.5" />;
            case "knowledge_save":
                return <Lightbulb className="h-3.5 w-3.5" />;
            default:
                return <BookOpen className="h-3.5 w-3.5" />;
        }
    };

    const getLabel = () => {
        switch (actionResult.type) {
            case "learning":
                return "자동 학습";
            case "price_update":
                return "가격 업데이트";
            case "learned_search":
                return `검색 결과 ${actionResult.result_count || 0}건`;
            case "knowledge_save":
                return "지식 저장";
            default:
                return "학습";
        }
    };

    const getBgColor = () => {
        if (actionResult.status === "error") return "bg-red-100 border-red-300 text-red-700";
        switch (actionResult.type) {
            case "learning":
            case "price_update":
                return "bg-green-100 border-green-300 text-green-700";
            case "learned_search":
                return "bg-blue-100 border-blue-300 text-blue-700";
            case "knowledge_save":
                return "bg-purple-100 border-purple-300 text-purple-700";
            default:
                return "bg-surface-secondary border-surface-tertiary text-text-subtle";
        }
    };

    // 가격 포맷팅
    const formatPrice = (price: number | undefined) => {
        if (price === undefined) return "";
        return price.toLocaleString("ko-KR") + "원";
    };

    return (
        <div className={cn(
            "mt-2 rounded-md border px-2.5 py-1.5 text-xs",
            getBgColor()
        )}>
            <div className="flex items-center gap-1.5">
                {getIcon()}
                <span className="font-medium">{getLabel()}</span>
                {actionResult.status === "success" && (
                    <CheckCircle2 className="ml-auto h-3.5 w-3.5" />
                )}
            </div>

            {/* 가격 정보 표시 */}
            {(actionResult.type === "learning" || actionResult.type === "price_update") && actionResult.item_name && (
                <div className="mt-1 text-[11px] opacity-80">
                    <span className="font-medium">{actionResult.item_name}</span>
                    {actionResult.old_price !== null && actionResult.old_price !== undefined && (
                        <span className="line-through ml-1">{formatPrice(actionResult.old_price)}</span>
                    )}
                    {actionResult.new_price && (
                        <span className="ml-1 font-semibold">{formatPrice(actionResult.new_price)}</span>
                    )}
                </div>
            )}

            {/* 검색 결과 요약 */}
            {actionResult.type === "learned_search" && actionResult.results && actionResult.results.length > 0 && (
                <div className="mt-1 space-y-0.5 text-[11px] opacity-80">
                    {actionResult.results.slice(0, 3).map((result, idx) => (
                        <div key={result.id || idx} className="truncate">
                            {result.item_name && (
                                <>
                                    <span className="font-medium">{result.item_name}</span>
                                    {result.new_price && (
                                        <span className="ml-1">{formatPrice(result.new_price)}</span>
                                    )}
                                </>
                            )}
                            {result.content && (
                                <span>{result.content.substring(0, 50)}...</span>
                            )}
                        </div>
                    ))}
                    {actionResult.results.length > 3 && (
                        <div className="text-[10px] italic">
                            +{actionResult.results.length - 3}건 더 있음
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
