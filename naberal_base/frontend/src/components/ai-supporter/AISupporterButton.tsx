"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Bot, X } from "lucide-react";

interface AISupporterButtonProps {
    isOpen: boolean;
    onClick: () => void;
    hasUnread?: boolean;
}

/**
 * AI 서포터 플로팅 버튼 컴포넌트
 *
 * - 우측 하단 고정 위치
 * - 펄스 애니메이션으로 눈에 잘 띄게
 * - 열림/닫힘 상태에 따라 아이콘 변경
 */
export function AISupporterButton({ isOpen, onClick, hasUnread }: AISupporterButtonProps) {
    return (
        <button
            onClick={onClick}
            className={cn(
                "fixed bottom-6 right-6 z-50",
                "flex h-14 w-14 items-center justify-center",
                "rounded-full shadow-lg",
                "transition-all duration-300 ease-out",
                "hover:scale-110 active:scale-95",
                isOpen
                    ? "bg-surface border-2 border-border/50 hover:bg-surface-secondary"
                    : "bg-gradient-to-br from-brand to-brand-strong hover:shadow-xl hover:shadow-brand/30"
            )}
            title={isOpen ? "AI 서포터 닫기" : "AI 서포터 열기"}
        >
            {/* 아이콘 */}
            <div className={cn(
                "transition-transform duration-300",
                isOpen ? "rotate-0" : "rotate-0"
            )}>
                {isOpen ? (
                    <X className="h-6 w-6 text-text" />
                ) : (
                    <Bot className="h-7 w-7 text-white" />
                )}
            </div>

            {/* 읽지 않은 메시지 표시 */}
            {!isOpen && hasUnread && (
                <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
                    <span className="relative inline-flex h-4 w-4 rounded-full bg-red-500" />
                </span>
            )}

            {/* 펄스 링 (닫힌 상태에서만) */}
            {!isOpen && (
                <span className="absolute inset-0 rounded-full animate-pulse-ring" />
            )}
        </button>
    );
}
