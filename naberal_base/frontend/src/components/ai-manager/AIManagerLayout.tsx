"use client";

import React, { useState, useCallback, useRef, ReactNode } from "react";
import { cn } from "@/lib/utils";
import { GripVertical, PanelRightClose, PanelRightOpen } from "lucide-react";

interface AIManagerLayoutProps {
    children: ReactNode;
    chatPanelWidth: number;
    onPanelResize: (newWidth: number) => void;
    hasMessages: boolean;
    hasVisualization: boolean;
    isVisualizationCollapsed?: boolean;
    onVisualizationCollapsedChange?: (collapsed: boolean) => void;
}

/**
 * AI 매니저 레이아웃 컴포넌트 - Claude.ai 3단계 레이아웃
 *
 * 1단계: 첫 화면 - 중앙 입력창 (메시지 없음)
 * 2단계: 채팅 화면 - 전체 너비 채팅 (메시지 있음, 시각화 없음)
 * 3단계: 시각화 활성화 - 채팅 + 우측 시각화 패널
 */
export function AIManagerLayout({
    children,
    chatPanelWidth,
    onPanelResize,
    hasMessages,
    hasVisualization,
    isVisualizationCollapsed: controlledCollapsed,
    onVisualizationCollapsedChange,
}: AIManagerLayoutProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [isResizing, setIsResizing] = useState(false);
    const [internalCollapsed, setInternalCollapsed] = useState(!hasVisualization);

    // controlled 또는 uncontrolled 상태 결정
    const isVisualizationCollapsed = controlledCollapsed !== undefined ? controlledCollapsed : internalCollapsed;
    const setIsVisualizationCollapsed = onVisualizationCollapsedChange || setInternalCollapsed;

    // 시각화 데이터가 있으면 자동으로 패널 열기
    React.useEffect(() => {
        if (hasVisualization && isVisualizationCollapsed) {
            setIsVisualizationCollapsed(false);
        }
    }, [hasVisualization]);

    // 리사이즈 시작
    const handleMouseDown = useCallback((e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizing(true);
    }, []);

    // 리사이즈 중
    const handleMouseMove = useCallback(
        (e: MouseEvent) => {
            if (!isResizing || !containerRef.current) return;

            const containerRect = containerRef.current.getBoundingClientRect();
            const newWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;
            onPanelResize(newWidth);
        },
        [isResizing, onPanelResize]
    );

    // 리사이즈 종료
    const handleMouseUp = useCallback(() => {
        setIsResizing(false);
    }, []);

    // 이벤트 리스너 등록
    React.useEffect(() => {
        if (isResizing) {
            window.addEventListener("mousemove", handleMouseMove);
            window.addEventListener("mouseup", handleMouseUp);
        }

        return () => {
            window.removeEventListener("mousemove", handleMouseMove);
            window.removeEventListener("mouseup", handleMouseUp);
        };
    }, [isResizing, handleMouseMove, handleMouseUp]);

    // children을 배열로 변환
    const childrenArray = React.Children.toArray(children);
    const chatPanel = childrenArray[0];
    const visualizationPanel = childrenArray[1];

    // 시각화 패널 표시 여부
    const showVisualizationPanel = hasVisualization && !isVisualizationCollapsed;

    return (
        <div
            ref={containerRef}
            className={cn(
                "flex h-full w-full overflow-hidden bg-bg",
                isResizing && "cursor-col-resize select-none"
            )}
        >
            {/* 채팅 패널 */}
            <div
                className={cn(
                    "relative flex h-full flex-col overflow-hidden transition-all duration-300 ease-out",
                    "bg-bg"
                )}
                style={{
                    width: showVisualizationPanel ? `${chatPanelWidth}%` : "100%",
                    minWidth: showVisualizationPanel ? "400px" : "100%"
                }}
            >
                {chatPanel}

                {/* 시각화 패널 토글 버튼 - 시각화 데이터가 있을 때만 표시 */}
                {hasVisualization && hasMessages && (
                    <button
                        onClick={() => setIsVisualizationCollapsed(!isVisualizationCollapsed)}
                        className={cn(
                            "absolute right-4 top-4 z-20 flex h-9 w-9 items-center justify-center rounded-lg",
                            "bg-surface border border-border/50 shadow-sm",
                            "hover:bg-surface-secondary transition-all duration-200",
                            "text-text-subtle hover:text-text"
                        )}
                        title={isVisualizationCollapsed ? "결과 패널 열기" : "결과 패널 닫기"}
                    >
                        {isVisualizationCollapsed ? (
                            <PanelRightOpen className="h-4 w-4" />
                        ) : (
                            <PanelRightClose className="h-4 w-4" />
                        )}
                    </button>
                )}
            </div>

            {/* 리사이즈 핸들 - 시각화 패널이 열려있을 때만 표시 */}
            {showVisualizationPanel && (
                <div
                    className={cn(
                        "group relative flex w-1 cursor-col-resize items-center justify-center",
                        "hover:w-1.5 transition-all duration-200",
                        isResizing && "w-1.5"
                    )}
                    onMouseDown={handleMouseDown}
                >
                    <div
                        className={cn(
                            "absolute inset-y-0 w-full",
                            "bg-border/30 hover:bg-brand/30 transition-colors duration-200",
                            isResizing && "bg-brand/40"
                        )}
                    />
                    <GripVertical
                        className={cn(
                            "relative z-10 h-8 w-4 text-text-subtle/50",
                            "opacity-0 group-hover:opacity-100 transition-opacity duration-200",
                            isResizing && "opacity-100 text-brand"
                        )}
                    />
                </div>
            )}

            {/* 시각화 패널 */}
            <div
                className={cn(
                    "flex h-full flex-col overflow-hidden transition-all duration-300 ease-out",
                    "bg-surface border-l border-border/50",
                    showVisualizationPanel ? "flex-1 opacity-100" : "w-0 opacity-0"
                )}
            >
                {showVisualizationPanel && visualizationPanel}
            </div>
        </div>
    );
}
