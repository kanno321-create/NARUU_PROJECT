"use client";

import { useState, useEffect, useCallback } from "react";
import type { ChatMessage } from "@/app/ai-manager/page";

/**
 * 채팅 세션 타입
 */
export interface ChatSession {
    id: string;
    title: string;
    messages: ChatMessage[];
    createdAt: string;
    updatedAt: string;
}

/**
 * 채팅 스토리지 훅 반환 타입
 */
export interface ChatStorageController {
    // 현재 세션
    currentSession: ChatSession | null;
    messages: ChatMessage[];

    // 세션 관리
    sessions: ChatSession[];
    loadSession: (sessionId: string) => boolean;
    createNewSession: () => void;
    deleteSession: (sessionId: string) => void;

    // 메시지 관리
    addMessage: (message: ChatMessage) => void;
    updateMessages: (messages: ChatMessage[]) => void;

    // 유틸리티
    isLoaded: boolean;
}

const STORAGE_KEY = "ai_manager_chat_sessions";
const CURRENT_SESSION_KEY = "ai_manager_current_session";

/** Sidebar 등 다른 컴포넌트에 채팅 목록 변경을 알린다. */
function dispatchChatUpdated(): void {
    if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("kis-chat-updated"));
    }
}

/**
 * 채팅 저장소 훅
 *
 * - localStorage에 채팅 세션 저장
 * - 페이지 로드 시 항상 첫 화면(빈 메시지)으로 시작
 * - 이전 대화는 수동으로 불러오기 가능
 * - 최근 채팅 히스토리 관리
 */
export function useChatStorage(initialSessionId?: string | null): ChatStorageController {
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
    const [isLoaded, setIsLoaded] = useState(false);

    // 초기 로드 - 세션 목록 + URL searchParams 또는 localStorage에서 세션 로드
    useEffect(() => {
        if (typeof window === "undefined") return;

        try {
            // 저장된 세션 목록 로드 (최근 대화 목록용)
            const savedSessions = localStorage.getItem(STORAGE_KEY);
            const parsedSessions: ChatSession[] = savedSessions
                ? JSON.parse(savedSessions)
                : [];

            if (parsedSessions.length > 0) {
                setSessions(parsedSessions);
            }

            // 세션 로드 우선순위: URL searchParams > localStorage 폴백
            const loadId = initialSessionId || localStorage.getItem('kis-load-session-id');
            // localStorage 키는 사용 후 즉시 정리 (URL params 방식으로 전환됨)
            localStorage.removeItem('kis-load-session-id');

            if (loadId) {
                const targetSession = parsedSessions.find(s => s.id === loadId);
                if (targetSession) {
                    setCurrentSession({
                        ...targetSession,
                        messages: targetSession.messages.map(m => ({
                            ...m,
                            timestamp: new Date(m.timestamp),
                        })),
                    });
                } else {
                    setCurrentSession(createFreshSession());
                }
            } else {
                setCurrentSession(createFreshSession());
            }

        } catch (error) {
            console.error("Failed to load chat sessions:", error);
            setCurrentSession(createFreshSession());
        }

        setIsLoaded(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // 참고: 저장은 addMessage, updateMessages 등에서 직접 수행
    // useEffect에서의 중복 저장 제거로 무한 루프 방지

    // localStorage 저장 함수
    const saveToStorage = useCallback((sessionsToSave: ChatSession[], currentId: string) => {
        if (typeof window === "undefined") return;

        try {
            // 최근 10개 세션만 유지
            const limitedSessions = sessionsToSave.slice(0, 10);
            localStorage.setItem(STORAGE_KEY, JSON.stringify(limitedSessions));
            localStorage.setItem(CURRENT_SESSION_KEY, currentId);
            dispatchChatUpdated();
        } catch (error) {
            console.error("Failed to save chat sessions:", error);
        }
    }, []);

    // 완전히 빈 세션 생성 (첫 화면용 - 메시지 없음)
    const createFreshSession = (): ChatSession => {
        return {
            id: `session-${Date.now()}`,
            title: "새 대화",
            messages: [], // 빈 메시지 배열 → 첫 화면 표시
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
        };
    };

    // 빈 세션 생성 (저장용 - 첫 메시지 전송 시 사용)
    const createEmptySession = (): ChatSession => {
        return {
            id: `session-${Date.now()}`,
            title: "새 대화",
            messages: [],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
        };
    };

    // 메시지 추가 - 함수형 업데이트로 최신 상태 보장
    const addMessage = useCallback((message: ChatMessage) => {
        setCurrentSession(prevSession => {
            if (!prevSession) return null;

            const updatedSession: ChatSession = {
                ...prevSession,
                messages: [...prevSession.messages, message],
                updatedAt: new Date().toISOString(),
                // 첫 사용자 메시지를 제목으로 사용
                title: prevSession.title === "새 대화" && message.role === "user"
                    ? message.content.slice(0, 30) + (message.content.length > 30 ? "..." : "")
                    : prevSession.title,
            };

            // 세션 목록도 함수형 업데이트로 동기화
            setSessions(prevSessions => {
                // 세션이 이미 리스트에 있는지 확인
                const existingIndex = prevSessions.findIndex(s => s.id === updatedSession.id);

                let updated: ChatSession[];
                if (existingIndex >= 0) {
                    // 기존 세션 업데이트
                    updated = prevSessions.map(s => s.id === updatedSession.id ? updatedSession : s);
                } else {
                    // 새 세션이면 리스트 맨 앞에 추가
                    updated = [updatedSession, ...prevSessions];
                }

                // 즉시 localStorage에 저장 (최근 10개만)
                if (typeof window !== "undefined") {
                    try {
                        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated.slice(0, 10)));
                        localStorage.setItem(CURRENT_SESSION_KEY, updatedSession.id);
                        dispatchChatUpdated();
                    } catch (e) {
                        console.error("Failed to save message:", e);
                    }
                }
                return updated;
            });

            return updatedSession;
        });
    }, []);

    // 메시지 목록 업데이트 - 함수형 업데이트로 최신 상태 보장
    const updateMessages = useCallback((messages: ChatMessage[]) => {
        setCurrentSession(prevSession => {
            if (!prevSession) return null;

            const updatedSession: ChatSession = {
                ...prevSession,
                messages,
                updatedAt: new Date().toISOString(),
            };

            // 세션 목록도 함수형 업데이트로 동기화
            setSessions(prevSessions => {
                const updated = prevSessions.map(s => s.id === updatedSession.id ? updatedSession : s);
                // 즉시 localStorage에 저장
                if (typeof window !== "undefined") {
                    try {
                        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated.slice(0, 10)));
                        localStorage.setItem(CURRENT_SESSION_KEY, updatedSession.id);
                        dispatchChatUpdated();
                    } catch (e) {
                        console.error("Failed to save messages:", e);
                    }
                }
                return updated;
            });

            return updatedSession;
        });
    }, []);

    // 세션 로드 (성공 시 true 반환)
    const loadSession = useCallback((sessionId: string): boolean => {
        const session = sessions.find(s => s.id === sessionId);
        if (session) {
            // timestamp 복원
            const restoredSession = {
                ...session,
                messages: session.messages.map(m => ({
                    ...m,
                    timestamp: new Date(m.timestamp),
                })),
            };
            setCurrentSession(restoredSession);
            localStorage.setItem(CURRENT_SESSION_KEY, sessionId);
            return true;
        }
        return false;
    }, [sessions]);

    // 새 세션 생성
    const createNewSession = useCallback(() => {
        const newSession = createEmptySession();
        const updatedSessions = [newSession, ...sessions];
        setSessions(updatedSessions);
        setCurrentSession(newSession);
        saveToStorage(updatedSessions, newSession.id);
    }, [sessions, saveToStorage]);

    // 세션 삭제
    const deleteSession = useCallback((sessionId: string) => {
        const updatedSessions = sessions.filter(s => s.id !== sessionId);

        if (updatedSessions.length === 0) {
            // 마지막 세션 삭제 시 새 세션 생성
            const newSession = createEmptySession();
            setSessions([newSession]);
            setCurrentSession(newSession);
            saveToStorage([newSession], newSession.id);
        } else {
            setSessions(updatedSessions);

            // 현재 세션이 삭제된 경우 첫 번째 세션으로 전환
            if (currentSession?.id === sessionId) {
                setCurrentSession(updatedSessions[0]);
                saveToStorage(updatedSessions, updatedSessions[0].id);
            } else {
                saveToStorage(updatedSessions, currentSession?.id || updatedSessions[0].id);
            }
        }
    }, [sessions, currentSession, saveToStorage]);

    return {
        currentSession,
        messages: currentSession?.messages || [],
        sessions,
        loadSession,
        createNewSession,
        deleteSession,
        addMessage,
        updateMessages,
        isLoaded,
    };
}
