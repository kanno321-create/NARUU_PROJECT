"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";

// API 기본 URL
// 브라우저: Next.js rewrite 프록시 사용 (/api/v1/* → Railway)
// Electron/직접 호출: Railway API 직접 호출
const IS_ELECTRON = typeof window !== "undefined" && !!(window as any).electronAPI;
const IS_BROWSER = typeof window !== "undefined" && !IS_ELECTRON;
const API_BASE_URL = IS_BROWSER ? "/api" : (process.env.NEXT_PUBLIC_API_URL || "https://naberalproject-production.up.railway.app");

// 사용자 타입
export interface User {
    id: string;
    username: string;
    name: string;
    role: "ceo" | "manager" | "staff" | "customer";
    status: "active" | "inactive" | "suspended";
    createdAt: string;
    lastLogin?: string;
}

// 토큰 응답 타입
interface TokenResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
}

// 인증 컨텍스트 타입
interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
    logout: () => void;
    // CEO 전용: 사용자 관리
    users: User[];
    loadUsers: () => Promise<void>;
    createUser: (username: string, password: string, name: string, role: User["role"]) => Promise<{ success: boolean; error?: string }>;
    deleteUser: (userId: string) => Promise<{ success: boolean; error?: string }>;
    updateUserPassword: (userId: string, newPassword: string) => Promise<{ success: boolean; error?: string }>;
    // 토큰 관련
    getAccessToken: () => string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// 토큰 저장 키
const ACCESS_TOKEN_KEY = "kis-access-token";
const REFRESH_TOKEN_KEY = "kis-refresh-token";
const TOKEN_EXPIRY_KEY = "kis-token-expiry";

// API 호출 헬퍼
async function apiCall<T>(
    endpoint: string,
    options: RequestInit = {},
    token?: string
): Promise<{ data?: T; error?: string; status: number }> {
    try {
        const headers: Record<string, string> = {
            "Content-Type": "application/json",
            ...(options.headers as Record<string, string>),
        };

        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers,
        });

        if (response.status === 204) {
            return { status: response.status };
        }

        const data = await response.json();

        if (!response.ok) {
            let errorMsg = "요청 처리 중 오류가 발생했습니다.";
            if (typeof data.detail === "string") {
                errorMsg = data.detail;
            } else if (Array.isArray(data.detail) && data.detail.length > 0) {
                errorMsg = data.detail.map((e: { msg?: string }) => e.msg || JSON.stringify(e)).join(", ");
            } else if (data.message) {
                errorMsg = data.message;
            }
            return {
                error: errorMsg,
                status: response.status,
            };
        }

        return { data, status: response.status };
    } catch (error) {
        console.error("API call error:", error);
        return {
            error: "서버에 연결할 수 없습니다.",
            status: 0,
        };
    }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [users, setUsers] = useState<User[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const refreshTimerRef = useRef<NodeJS.Timeout | null>(null);

    // 토큰 저장
    const saveTokens = useCallback((tokens: TokenResponse) => {
        localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
        localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
        // 만료 시간 저장 (현재 시간 + expires_in 초)
        const expiryTime = Date.now() + tokens.expires_in * 1000;
        localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
    }, []);

    // 토큰 로드
    const loadTokens = useCallback((): { accessToken: string; refreshToken: string; expiry: number } | null => {
        const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
        const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
        const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);

        if (!accessToken || !refreshToken || !expiry) {
            return null;
        }

        return {
            accessToken,
            refreshToken,
            expiry: parseInt(expiry, 10),
        };
    }, []);

    // 토큰 삭제
    const clearTokens = useCallback(() => {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        localStorage.removeItem(TOKEN_EXPIRY_KEY);
        if (refreshTimerRef.current) {
            clearTimeout(refreshTimerRef.current);
            refreshTimerRef.current = null;
        }
    }, []);

    // 액세스 토큰 가져오기
    const getAccessToken = useCallback((): string | null => {
        return localStorage.getItem(ACCESS_TOKEN_KEY);
    }, []);

    // 토큰 갱신
    const refreshAccessToken = useCallback(async (): Promise<string | null> => {
        const tokens = loadTokens();
        if (!tokens) {
            return null;
        }

        const { data, error } = await apiCall<TokenResponse>("/v1/auth/refresh", {
            method: "POST",
            body: JSON.stringify({ refresh_token: tokens.refreshToken }),
        });

        if (error || !data) {
            console.error("Token refresh failed:", error);
            clearTokens();
            setUser(null);
            return null;
        }

        saveTokens(data);
        return data.access_token;
    }, [loadTokens, saveTokens, clearTokens]);

    // 토큰 갱신 타이머 설정
    const scheduleTokenRefresh = useCallback((expiryTime: number) => {
        if (refreshTimerRef.current) {
            clearTimeout(refreshTimerRef.current);
        }

        // 만료 1분 전에 갱신 (최소 10초)
        const refreshTime = Math.max(expiryTime - Date.now() - 60000, 10000);

        refreshTimerRef.current = setTimeout(async () => {
            const newToken = await refreshAccessToken();
            if (newToken) {
                const tokens = loadTokens();
                if (tokens) {
                    scheduleTokenRefresh(tokens.expiry);
                }
            }
        }, refreshTime);
    }, [refreshAccessToken, loadTokens]);

    // 현재 사용자 정보 로드
    const loadCurrentUser = useCallback(async (token: string): Promise<User | null> => {
        const { data, error } = await apiCall<{
            id: string;
            username: string;
            name: string;
            role: string;
            status: string;
            created_at: string;
            last_login?: string;
        }>("/v1/auth/me", { method: "GET" }, token);

        if (error || !data) {
            return null;
        }

        return {
            id: data.id,
            username: data.username,
            name: data.name,
            role: data.role as User["role"],
            status: data.status as User["status"],
            createdAt: data.created_at,
            lastLogin: data.last_login,
        };
    }, []);

    // 초기화: 저장된 토큰으로 세션 복구
    useEffect(() => {
        const initAuth = async () => {
            try {
                const tokens = loadTokens();
                if (!tokens) {
                    setIsLoading(false);
                    return;
                }

                // 토큰이 만료되었는지 확인
                if (tokens.expiry < Date.now()) {
                    // 리프레시 토큰으로 갱신 시도
                    const newToken = await refreshAccessToken();
                    if (!newToken) {
                        setIsLoading(false);
                        return;
                    }
                }

                // 사용자 정보 로드
                const currentUser = await loadCurrentUser(tokens.accessToken);
                if (currentUser) {
                    setUser(currentUser);
                    scheduleTokenRefresh(tokens.expiry);
                } else {
                    clearTokens();
                }
            } catch (e) {
                console.error("Auth initialization error:", e);
                clearTokens();
            } finally {
                setIsLoading(false);
            }
        };

        initAuth();

        // 클린업
        return () => {
            if (refreshTimerRef.current) {
                clearTimeout(refreshTimerRef.current);
            }
        };
    }, [loadTokens, refreshAccessToken, loadCurrentUser, scheduleTokenRefresh, clearTokens]);

    // 로그인
    const login = useCallback(async (username: string, password: string): Promise<{ success: boolean; error?: string }> => {
        const { data, error } = await apiCall<TokenResponse>("/v1/auth/login", {
            method: "POST",
            body: JSON.stringify({ username, password }),
        });

        if (error || !data) {
            return { success: false, error: error || "로그인에 실패했습니다." };
        }

        // 토큰 저장
        saveTokens(data);

        // 사용자 정보 로드
        const currentUser = await loadCurrentUser(data.access_token);
        if (!currentUser) {
            clearTokens();
            return { success: false, error: "사용자 정보를 가져올 수 없습니다." };
        }

        setUser(currentUser);

        // 토큰 갱신 타이머 설정
        const tokens = loadTokens();
        if (tokens) {
            scheduleTokenRefresh(tokens.expiry);
        }

        return { success: true };
    }, [saveTokens, loadCurrentUser, clearTokens, loadTokens, scheduleTokenRefresh]);

    // 로그아웃
    const logout = useCallback(async () => {
        const token = getAccessToken();
        if (token) {
            // 서버에 로그아웃 알림 (실패해도 로컬 정리)
            await apiCall("/v1/auth/logout", { method: "POST" }, token);
        }

        clearTokens();
        setUser(null);
        setUsers([]);
    }, [getAccessToken, clearTokens]);

    // 사용자 목록 로드 (CEO 전용)
    const loadUsers = useCallback(async () => {
        if (!user || user.role !== "ceo") {
            return;
        }

        const token = getAccessToken();
        if (!token) {
            return;
        }

        const { data, error } = await apiCall<{ users: Array<{
            id: string;
            username: string;
            name: string;
            role: string;
            status: string;
            created_at: string;
            last_login?: string;
        }>; total: number }>("/v1/users", { method: "GET" }, token);

        if (error || !data) {
            console.error("Failed to load users:", error);
            return;
        }

        setUsers(data.users.map(u => ({
            id: u.id,
            username: u.username,
            name: u.name,
            role: u.role as User["role"],
            status: u.status as User["status"],
            createdAt: u.created_at,
            lastLogin: u.last_login,
        })));
    }, [user, getAccessToken]);

    // 사용자 생성 (CEO 전용)
    const createUser = useCallback(async (
        username: string,
        password: string,
        name: string,
        role: User["role"]
    ): Promise<{ success: boolean; error?: string }> => {
        if (!user || user.role !== "ceo") {
            return { success: false, error: "권한이 없습니다." };
        }

        const token = getAccessToken();
        if (!token) {
            return { success: false, error: "인증이 필요합니다." };
        }

        const { data, error } = await apiCall<{
            id: string;
            username: string;
            name: string;
            role: string;
            status: string;
            created_at: string;
        }>("/v1/users", {
            method: "POST",
            body: JSON.stringify({ username, password, name, role }),
        }, token);

        if (error || !data) {
            return { success: false, error: error || "사용자 생성에 실패했습니다." };
        }

        // 사용자 목록 갱신
        await loadUsers();

        return { success: true };
    }, [user, getAccessToken, loadUsers]);

    // 사용자 삭제 (CEO 전용)
    const deleteUser = useCallback(async (userId: string): Promise<{ success: boolean; error?: string }> => {
        if (!user || user.role !== "ceo") {
            return { success: false, error: "권한이 없습니다." };
        }

        const token = getAccessToken();
        if (!token) {
            return { success: false, error: "인증이 필요합니다." };
        }

        const { error, status } = await apiCall(`/v1/users/${userId}`, {
            method: "DELETE",
        }, token);

        if (status !== 204 && error) {
            return { success: false, error: error || "사용자 삭제에 실패했습니다." };
        }

        // 사용자 목록 갱신
        await loadUsers();

        return { success: true };
    }, [user, getAccessToken, loadUsers]);

    // 비밀번호 변경 (CEO 전용)
    const updateUserPassword = useCallback(async (
        userId: string,
        newPassword: string
    ): Promise<{ success: boolean; error?: string }> => {
        if (!user || user.role !== "ceo") {
            return { success: false, error: "권한이 없습니다." };
        }

        const token = getAccessToken();
        if (!token) {
            return { success: false, error: "인증이 필요합니다." };
        }

        const { error } = await apiCall(`/v1/users/${userId}/password`, {
            method: "PUT",
            body: JSON.stringify({ new_password: newPassword }),
        }, token);

        if (error) {
            return { success: false, error: error || "비밀번호 변경에 실패했습니다." };
        }

        return { success: true };
    }, [user, getAccessToken]);

    return (
        <AuthContext.Provider
            value={{
                user,
                isAuthenticated: !!user,
                isLoading,
                login,
                logout,
                users,
                loadUsers,
                createUser,
                deleteUser,
                updateUserPassword,
                getAccessToken,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
