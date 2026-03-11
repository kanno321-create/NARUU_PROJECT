"use client";

import React, { useState, useCallback, useEffect } from "react";
import { API_BASE_URL } from "@/config/api";
import { AISupporterButton } from "./AISupporterButton";
import { AISupporterPopup, TabContextType, SupporterMessage } from "./AISupporterPopup";

// LocalStorage 키
const SUPPORTER_MESSAGES_KEY = "kis-ai-supporter-messages";
const SUPPORTER_SESSION_KEY = "kis-ai-supporter-session";

interface AISupporterProps {
    tabContext: TabContextType;
    // 탭별 콜백 함수들 (AI가 직접 제어할 때 사용)
    onQuoteAction?: (action: string, data: Record<string, unknown>) => void;
    onERPAction?: (action: string, data: Record<string, unknown>) => void;
    onCalendarAction?: (action: string, data: Record<string, unknown>) => void;
    onEmailAction?: (action: string, data: Record<string, unknown>) => void;
    onDrawingsAction?: (action: string, data: Record<string, unknown>) => void;
}

/**
 * AI 서포터 통합 컴포넌트
 *
 * - 플로팅 버튼 + 팝업 창 관리
 * - AI API 연동
 * - 탭별 컨텍스트 기반 대화
 * - LocalStorage에 대화 기록 저장
 */
export function AISupporter({
    tabContext,
    onQuoteAction,
    onERPAction,
    onCalendarAction,
    onEmailAction,
    onDrawingsAction,
}: AISupporterProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<SupporterMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [hasUnread, setHasUnread] = useState(false);
    const [sessionId, setSessionId] = useState<string>("");

    // 초기 로드: LocalStorage에서 메시지 복원
    useEffect(() => {
        if (typeof window === "undefined") return;

        // 세션 ID 로드 또는 생성
        let currentSessionId = localStorage.getItem(SUPPORTER_SESSION_KEY);
        if (!currentSessionId) {
            currentSessionId = `supporter-${Date.now()}`;
            localStorage.setItem(SUPPORTER_SESSION_KEY, currentSessionId);
        }
        setSessionId(currentSessionId);

        // 메시지 로드
        try {
            const saved = localStorage.getItem(`${SUPPORTER_MESSAGES_KEY}-${tabContext}`);
            if (saved) {
                const parsed = JSON.parse(saved);
                // Date 객체 복원
                const restored = parsed.map((msg: SupporterMessage) => ({
                    ...msg,
                    timestamp: new Date(msg.timestamp),
                }));
                setMessages(restored);
            }
        } catch (e) {
            console.error("Failed to load supporter messages:", e);
        }
    }, [tabContext]);

    // 메시지 변경 시 LocalStorage에 저장
    useEffect(() => {
        if (typeof window === "undefined" || messages.length === 0) return;

        try {
            localStorage.setItem(
                `${SUPPORTER_MESSAGES_KEY}-${tabContext}`,
                JSON.stringify(messages)
            );
        } catch (e) {
            console.error("Failed to save supporter messages:", e);
        }
    }, [messages, tabContext]);

    // 탭별 한글 이름
    const tabNames: Record<TabContextType, string> = {
        quote: "견적",
        erp: "ERP",
        calendar: "캘린더",
        email: "이메일",
        drawings: "도면",
    };

    // 탭별 시스템 프롬프트 - 더 명확하게 현재 위치 강조
    const getSystemPrompt = useCallback(() => {
        const currentTabName = tabNames[tabContext];

        const contextPrompts: Record<TabContextType, string> = {
            quote: `[시스템 정보]
- 당신의 역할: (주)한국산업 KIS 시스템의 AI 서포터
- 현재 위치: **${currentTabName} 탭** (견적서 작성 페이지)
- 당신은 AI 매니저가 아닙니다. 당신은 ${currentTabName} 탭 전용 AI 서포터입니다.

[당신의 임무]
사용자가 현재 ${currentTabName} 탭에서 작업 중입니다. 다음 업무만 지원하세요:
1. 분전반 견적서 생성 도움 (차단기 배치, 외함 계산)
2. 차단기 가격 조회 및 비교
3. 견적 조건 안내
4. 고객 정보 입력 지원

[중요]
- 항상 "${currentTabName} 탭에서 도와드리겠습니다"라고 인식하세요
- 견적과 무관한 질문은 해당 탭으로 이동을 안내하세요`,

            erp: `[시스템 정보]
- 당신의 역할: (주)한국산업 KIS 시스템의 AI 서포터
- 현재 위치: **${currentTabName} 탭** (ERP 관리 페이지)
- 당신은 AI 매니저가 아닙니다. 당신은 ${currentTabName} 탭 전용 AI 서포터입니다.

[당신의 임무]
사용자가 현재 ${currentTabName} 탭에서 작업 중입니다. 다음 업무만 지원하세요:
1. 매출/매입 현황 조회
2. 거래처 관리
3. 재고 확인
4. 전표 작성 안내

[중요]
- 항상 "${currentTabName} 탭에서 도와드리겠습니다"라고 인식하세요
- ERP와 무관한 질문은 해당 탭으로 이동을 안내하세요`,

            calendar: `[시스템 정보]
- 당신의 역할: (주)한국산업 KIS 시스템의 AI 서포터
- 현재 위치: **${currentTabName} 탭** (일정 관리 페이지)
- 당신은 AI 매니저가 아닙니다. 당신은 ${currentTabName} 탭 전용 AI 서포터입니다.

[당신의 임무]
사용자가 현재 ${currentTabName} 탭에서 작업 중입니다. 다음 업무만 지원하세요:
1. 일정 추가/수정/삭제
2. 일정 조회 및 확인
3. 알림 설정
4. 반복 일정 관리

[중요]
- 항상 "${currentTabName} 탭에서 도와드리겠습니다"라고 인식하세요
- 일정과 무관한 질문은 해당 탭으로 이동을 안내하세요`,

            email: `[시스템 정보]
- 당신의 역할: (주)한국산업 KIS 시스템의 AI 서포터
- 현재 위치: **${currentTabName} 탭** (이메일 관리 페이지)
- 당신은 AI 매니저가 아닙니다. 당신은 ${currentTabName} 탭 전용 AI 서포터입니다.

[당신의 임무]
사용자가 현재 ${currentTabName} 탭에서 작업 중입니다. 다음 업무만 지원하세요:
1. 이메일 작성 및 수정
2. 문장 톤 조정 (격식체/비격식체로 변환)
3. 이메일 요약
4. 답장 초안 작성

[중요]
- 항상 "${currentTabName} 탭에서 도와드리겠습니다"라고 인식하세요
- 회사 이미지에 맞는 격식 있고 전문적인 톤으로 글을 다듬어주세요
- 이메일과 무관한 질문은 해당 탭으로 이동을 안내하세요`,

            drawings: `[시스템 정보]
- 당신의 역할: (주)한국산업 KIS 시스템의 AI 서포터
- 현재 위치: **${currentTabName} 탭** (도면 관리 페이지)
- 당신은 AI 매니저가 아닙니다. 당신은 ${currentTabName} 탭 전용 AI 서포터입니다.

[당신의 임무]
사용자가 현재 ${currentTabName} 탭에서 작업 중입니다. 다음 업무만 지원하세요:
1. 도면 분석 및 정보 추출
2. 부품 목록 생성
3. 견적서 연동
4. 도면 파일 관리

[중요]
- 항상 "${currentTabName} 탭에서 도와드리겠습니다"라고 인식하세요
- 도면과 무관한 질문은 해당 탭으로 이동을 안내하세요`,
        };

        return contextPrompts[tabContext];
    }, [tabContext]);

    // AI에게 메시지 전송
    const sendMessage = useCallback(async (content: string) => {
        if (!content.trim() || isLoading) return;

        // 사용자 메시지 추가
        const userMessage: SupporterMessage = {
            id: `user-${Date.now()}`,
            role: "user",
            content,
            timestamp: new Date(),
            tabContext,
        };
        setMessages(prev => [...prev, userMessage]);
        setIsLoading(true);

        try {
            // 대화 히스토리 구성
            const conversationHistory = [...messages, userMessage].map(msg => ({
                role: msg.role,
                content: msg.content,
            }));

            // API 호출 - AI 서포터 모드 명시
            const response = await fetch(`${API_BASE_URL}/v1/ai-manager/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    message: content,
                    context: {
                        tabContext,
                        currentTab: tabNames[tabContext], // 현재 탭 이름 (한글)
                        supporterMode: true, // AI 서포터 모드 명시
                        systemPrompt: getSystemPrompt(),
                        conversationHistory: conversationHistory.slice(-10), // 최근 10개만
                    },
                    model: "claude-sonnet",
                    sessionId,
                    supporterMode: true, // 최상위에도 명시
                }),
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            const data = await response.json();

            // AI 응답 추가
            const assistantMessage: SupporterMessage = {
                id: `assistant-${Date.now()}`,
                role: "assistant",
                content: data.response || data.message || "죄송합니다. 응답을 처리하지 못했습니다.",
                timestamp: new Date(),
                tabContext,
            };
            setMessages(prev => [...prev, assistantMessage]);

            // 탭별 액션 처리 (AI가 반환한 액션이 있을 경우)
            if (data.action) {
                handleTabAction(data.action, data.actionData || {});
            }

            // 읽지 않은 메시지 표시 (창이 닫혀있을 때)
            if (!isOpen) {
                setHasUnread(true);
            }
        } catch (error) {
            console.error("AI Supporter error:", error);

            // 에러 메시지 추가
            const errorMessage: SupporterMessage = {
                id: `error-${Date.now()}`,
                role: "assistant",
                content: "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                timestamp: new Date(),
                tabContext,
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    }, [messages, isLoading, tabContext, sessionId, getSystemPrompt, isOpen]);

    // 탭별 액션 처리
    const handleTabAction = useCallback((action: string, data: Record<string, unknown>) => {
        switch (tabContext) {
            case "quote":
                onQuoteAction?.(action, data);
                break;
            case "erp":
                onERPAction?.(action, data);
                break;
            case "calendar":
                onCalendarAction?.(action, data);
                break;
            case "email":
                onEmailAction?.(action, data);
                break;
            case "drawings":
                onDrawingsAction?.(action, data);
                break;
        }
    }, [tabContext, onQuoteAction, onERPAction, onCalendarAction, onEmailAction, onDrawingsAction]);

    // 팝업 열기
    const handleOpen = useCallback(() => {
        setIsOpen(true);
        setHasUnread(false);
    }, []);

    // 팝업 닫기
    const handleClose = useCallback(() => {
        setIsOpen(false);
    }, []);

    // 토글
    const handleToggle = useCallback(() => {
        if (isOpen) {
            handleClose();
        } else {
            handleOpen();
        }
    }, [isOpen, handleOpen, handleClose]);

    return (
        <>
            <AISupporterButton
                isOpen={isOpen}
                onClick={handleToggle}
                hasUnread={hasUnread}
            />
            <AISupporterPopup
                isOpen={isOpen}
                onClose={handleClose}
                tabContext={tabContext}
                messages={messages}
                onSendMessage={sendMessage}
                isLoading={isLoading}
            />
        </>
    );
}

// Export 편의를 위한 re-export
export { type TabContextType, type SupporterMessage } from "./AISupporterPopup";
