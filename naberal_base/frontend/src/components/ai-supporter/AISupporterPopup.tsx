"use client";

import React, { useRef, useEffect, useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
    Bot,
    Send,
    Loader2,
    Minimize2,
    Maximize2,
    X,
    Sparkles,
    FileText,
    Settings,
    Calendar,
    Mail,
    Image as ImageIcon,
} from "lucide-react";

// 탭 컨텍스트 타입
export type TabContextType = "quote" | "erp" | "calendar" | "email" | "drawings";

// 메시지 타입
export interface SupporterMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: Date;
    tabContext?: TabContextType;
}

interface AISupporterPopupProps {
    isOpen: boolean;
    onClose: () => void;
    tabContext: TabContextType;
    messages: SupporterMessage[];
    onSendMessage: (message: string) => void;
    isLoading: boolean;
}

// 탭별 제안 메시지
const tabSuggestions: Record<TabContextType, { label: string; message: string }[]> = {
    quote: [
        { label: "견적 생성", message: "상도 4P 100A 메인, 분기 ELB 3P 30A 5개로 견적해줘" },
        { label: "차단기 조회", message: "SBE-104 차단기 단가 알려줘" },
        { label: "외함 계산", message: "600*800*150 외함 가격 계산해줘" },
    ],
    erp: [
        { label: "매출 현황", message: "이번 달 매출 현황 보여줘" },
        { label: "거래처 조회", message: "최근 거래처 목록 보여줘" },
        { label: "재고 확인", message: "부족한 재고 목록 알려줘" },
    ],
    calendar: [
        { label: "일정 추가", message: "내일 오후 2시에 거래처 미팅 일정 추가해줘" },
        { label: "일정 확인", message: "이번 주 일정 알려줘" },
        { label: "알림 설정", message: "중요 일정 알림 설정해줘" },
    ],
    email: [
        { label: "이메일 작성", message: "거래처에 보낼 견적서 안내 이메일 작성해줘" },
        { label: "톤 조정", message: "이 이메일을 더 격식있게 다듬어줘" },
        { label: "요약", message: "받은 이메일들 요약해줘" },
    ],
    drawings: [
        { label: "도면 분석", message: "첨부된 도면을 분석해줘" },
        { label: "부품 추출", message: "도면에서 차단기 정보 추출해줘" },
        { label: "견적 연동", message: "이 도면으로 견적서 만들어줘" },
    ],
};

// 탭별 아이콘
const tabIcons: Record<TabContextType, React.ElementType> = {
    quote: FileText,
    erp: Settings,
    calendar: Calendar,
    email: Mail,
    drawings: ImageIcon,
};

// 탭별 레이블
const tabLabels: Record<TabContextType, string> = {
    quote: "견적",
    erp: "ERP",
    calendar: "캘린더",
    email: "이메일",
    drawings: "도면",
};

/**
 * AI 서포터 팝업 채팅 창 컴포넌트
 *
 * - 메인 창의 약 1/4 크기 (400x500px)
 * - 우측 하단 위치
 * - 탭 컨텍스트에 따른 맞춤형 제안
 * - AI 매니저와 동일한 채팅 기능
 */
export function AISupporterPopup({
    isOpen,
    onClose,
    tabContext,
    messages,
    onSendMessage,
    isLoading,
}: AISupporterPopupProps) {
    const [inputValue, setInputValue] = useState("");
    const [isExpanded, setIsExpanded] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // 메시지 추가 시 스크롤
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // 텍스트 영역 자동 높이 조절
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 100)}px`;
        }
    }, [inputValue]);

    // 전송 핸들러
    const handleSend = useCallback(() => {
        if (inputValue.trim() && !isLoading) {
            onSendMessage(inputValue.trim());
            setInputValue("");
        }
    }, [inputValue, isLoading, onSendMessage]);

    // 키보드 이벤트 핸들러
    const handleKeyDown = useCallback(
        (e: React.KeyboardEvent) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        },
        [handleSend]
    );

    // 제안 클릭 핸들러
    const handleSuggestionClick = (message: string) => {
        setInputValue(message);
        textareaRef.current?.focus();
    };

    const TabIcon = tabIcons[tabContext];
    const suggestions = tabSuggestions[tabContext];

    if (!isOpen) return null;

    return (
        <div
            className={cn(
                "fixed z-50 flex flex-col overflow-hidden",
                "rounded-2xl border border-border/50",
                "bg-surface shadow-2xl shadow-black/20",
                "transition-all duration-300 ease-out",
                // 크기 및 위치
                isExpanded
                    ? "bottom-6 right-6 w-[600px] h-[700px]"
                    : "bottom-24 right-6 w-[400px] h-[500px]"
            )}
        >
            {/* 헤더 */}
            <div className="flex items-center justify-between border-b border-border/30 bg-gradient-to-r from-brand/5 to-transparent px-4 py-3">
                <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand to-brand-strong shadow-sm">
                        <Bot className="h-5 w-5 text-white" />
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <span className="font-semibold text-text-strong">AI 서포터</span>
                            <span className="flex items-center gap-1 rounded-full bg-brand/10 px-2 py-0.5 text-xs font-medium text-brand">
                                <TabIcon className="h-3 w-3" />
                                {tabLabels[tabContext]}
                            </span>
                        </div>
                        <p className="text-xs text-text-subtle">
                            {tabLabels[tabContext]} 작업을 도와드립니다
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-1">
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="flex h-8 w-8 items-center justify-center rounded-lg text-text-subtle hover:bg-surface-secondary hover:text-text transition-colors"
                        title={isExpanded ? "축소" : "확대"}
                    >
                        {isExpanded ? (
                            <Minimize2 className="h-4 w-4" />
                        ) : (
                            <Maximize2 className="h-4 w-4" />
                        )}
                    </button>
                    <button
                        onClick={onClose}
                        className="flex h-8 w-8 items-center justify-center rounded-lg text-text-subtle hover:bg-surface-secondary hover:text-text transition-colors"
                        title="닫기"
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>
            </div>

            {/* 메시지 영역 */}
            <div className="flex-1 overflow-y-auto">
                {messages.length === 0 ? (
                    // 빈 상태 - 제안 표시
                    <div className="flex h-full flex-col items-center justify-center p-6">
                        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand/10 to-brand/5">
                            <Sparkles className="h-7 w-7 text-brand" />
                        </div>
                        <h3 className="mb-2 text-lg font-semibold text-text-strong">
                            {tabLabels[tabContext]} 도우미
                        </h3>
                        <p className="mb-6 text-center text-sm text-text-subtle">
                            무엇을 도와드릴까요?
                        </p>

                        {/* 제안 버튼들 */}
                        <div className="w-full space-y-2">
                            {suggestions.map((suggestion, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => handleSuggestionClick(suggestion.message)}
                                    className="flex w-full items-center gap-3 rounded-xl border border-border/30 bg-surface-secondary/50 px-4 py-3 text-left hover:bg-surface-secondary hover:border-brand/30 transition-all"
                                >
                                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand/10">
                                        <TabIcon className="h-4 w-4 text-brand" />
                                    </div>
                                    <span className="text-sm font-medium text-text">
                                        {suggestion.label}
                                    </span>
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    // 메시지 리스트
                    <div className="p-4 space-y-4">
                        {messages.map((message) => (
                            <MessageBubble key={message.id} message={message} />
                        ))}

                        {/* 로딩 인디케이터 */}
                        {isLoading && (
                            <div className="flex items-start gap-3">
                                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-brand to-brand-strong">
                                    <Bot className="h-4 w-4 text-white" />
                                </div>
                                <div className="flex items-center gap-2 pt-2">
                                    <div className="flex gap-1">
                                        <span className="w-1.5 h-1.5 rounded-full bg-brand/60 animate-bounce" style={{ animationDelay: "0ms" }} />
                                        <span className="w-1.5 h-1.5 rounded-full bg-brand/60 animate-bounce" style={{ animationDelay: "150ms" }} />
                                        <span className="w-1.5 h-1.5 rounded-full bg-brand/60 animate-bounce" style={{ animationDelay: "300ms" }} />
                                    </div>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>
                )}
            </div>

            {/* 입력 영역 */}
            <div className="border-t border-border/30 bg-surface-secondary/30 p-3">
                <div className="flex items-end gap-2 rounded-xl border border-border/40 bg-surface px-3 py-2">
                    <textarea
                        ref={textareaRef}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="메시지를 입력하세요..."
                        className={cn(
                            "flex-1 resize-none bg-transparent",
                            "focus:outline-none",
                            "placeholder:text-text-subtle/60",
                            "min-h-[36px] max-h-[100px]",
                            "text-sm text-text leading-relaxed py-1"
                        )}
                        rows={1}
                        disabled={isLoading}
                    />
                    <Button
                        size="icon"
                        className="h-8 w-8 shrink-0 rounded-lg"
                        onClick={handleSend}
                        disabled={isLoading || !inputValue.trim()}
                    >
                        {isLoading ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <Send className="h-4 w-4" />
                        )}
                    </Button>
                </div>
                <p className="mt-2 text-center text-[10px] text-text-subtle/50">
                    Enter로 전송 · Shift+Enter로 줄바꿈
                </p>
            </div>
        </div>
    );
}

/**
 * 메시지 버블 컴포넌트
 */
function MessageBubble({ message }: { message: SupporterMessage }) {
    const isUser = message.role === "user";

    if (isUser) {
        return (
            <div className="flex justify-end">
                <div className="max-w-[85%] rounded-2xl rounded-tr-md bg-brand/10 border border-brand/20 px-4 py-2.5">
                    <div className="whitespace-pre-wrap text-sm leading-relaxed text-text">
                        {message.content}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-brand to-brand-strong">
                <Bot className="h-4 w-4 text-white" />
            </div>
            <div className="flex-1 pt-0.5">
                <div className="text-sm leading-relaxed text-text">
                    {message.content.split('\n').map((line, i) => {
                        if (line.trim() === '') {
                            return <div key={i} className="h-2" />;
                        }
                        if (line.trim().startsWith('- ')) {
                            return (
                                <div key={i} className="flex items-start gap-1.5 mt-1">
                                    <span className="text-brand text-xs mt-1">•</span>
                                    <p className="flex-1">{line.replace(/^- /, '')}</p>
                                </div>
                            );
                        }
                        return <p key={i} className={i > 0 ? "mt-2" : ""}>{line}</p>;
                    })}
                </div>
            </div>
        </div>
    );
}
