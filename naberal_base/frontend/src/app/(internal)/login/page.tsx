"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import Link from "next/link";
import { Bot, Lock, User } from "lucide-react";

export default function LoginPage() {
    const router = useRouter();
    const { login, user, isAuthenticated, isLoading } = useAuth();

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    // 이미 로그인된 경우 역할별 리다이렉트
    useEffect(() => {
        if (!isLoading && isAuthenticated && user) {
            if (user.role === "customer") {
                router.push("/portal/estimates");
            } else {
                router.push("/ai-manager");
            }
        }
    }, [isAuthenticated, isLoading, user, router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setIsSubmitting(true);

        try {
            const result = await login(username, password);
            if (result.success) {
                // 역할별 리다이렉트는 useEffect에서 처리
                // (user state 업데이트 후 자동 리다이렉트)
            } else {
                setError(result.error || "로그인에 실패했습니다.");
            }
        } catch (err) {
            setError("시스템 오류가 발생했습니다.");
        } finally {
            setIsSubmitting(false);
        }
    };

    // 로딩 중일 때
    if (isLoading) {
        return (
            <div className="flex h-screen items-center justify-center" style={{ backgroundColor: "var(--color-surface-secondary)" }}>
                <div className="text-lg" style={{ color: "var(--color-text-subtle)" }}>로딩 중...</div>
            </div>
        );
    }

    // 이미 로그인된 경우
    if (isAuthenticated) {
        return null;
    }

    return (
        <div className="flex min-h-screen items-center justify-center p-4" style={{ backgroundColor: "var(--color-surface-secondary)" }}>
            <div className="w-full max-w-md">
                {/* 로고 및 타이틀 */}
                <div className="mb-8 text-center">
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-xl" style={{ backgroundColor: "var(--color-brand)" }}>
                        <Bot className="h-10 w-10 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold" style={{ color: "var(--color-text-strong)" }}>KIS Estimator</h1>
                    <p className="mt-2 text-sm" style={{ color: "var(--color-text-subtle)" }}>(주)한국산업 견적 시스템</p>
                </div>

                {/* 로그인 폼 */}
                <div className="rounded-xl p-8 shadow-lg" style={{ backgroundColor: "var(--color-surface)" }}>
                    <h2 className="mb-6 text-center text-xl font-semibold" style={{ color: "var(--color-text-strong)" }}>로그인</h2>

                    <form onSubmit={handleSubmit} className="space-y-5">
                        {/* 아이디 입력 */}
                        <div>
                            <label className="mb-2 block text-sm font-medium" style={{ color: "var(--color-text)" }}>
                                아이디
                            </label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2" style={{ color: "var(--color-text-subtle)" }} />
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="w-full rounded-lg border py-3 pl-10 pr-4 text-base focus:outline-none focus:ring-2"
                                    style={{
                                        backgroundColor: "var(--color-surface)",
                                        borderColor: "var(--color-border)",
                                        color: "var(--color-text)",
                                    }}
                                    placeholder="아이디를 입력하세요"
                                    required
                                    autoComplete="username"
                                />
                            </div>
                        </div>

                        {/* 비밀번호 입력 */}
                        <div>
                            <label className="mb-2 block text-sm font-medium" style={{ color: "var(--color-text)" }}>
                                비밀번호
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2" style={{ color: "var(--color-text-subtle)" }} />
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full rounded-lg border py-3 pl-10 pr-4 text-base focus:outline-none focus:ring-2"
                                    style={{
                                        backgroundColor: "var(--color-surface)",
                                        borderColor: "var(--color-border)",
                                        color: "var(--color-text)",
                                    }}
                                    placeholder="비밀번호를 입력하세요"
                                    required
                                    autoComplete="current-password"
                                />
                            </div>
                        </div>

                        {/* 에러 메시지 */}
                        {error && (
                            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
                                {error}
                            </div>
                        )}

                        {/* 로그인 버튼 */}
                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="w-full rounded-lg py-3 text-base font-medium text-white transition-colors disabled:opacity-50"
                            style={{ backgroundColor: "var(--color-brand)" }}
                        >
                            {isSubmitting ? "로그인 중..." : "로그인"}
                        </button>
                    </form>

                </div>

                {/* 하단 안내 */}
                <div className="mt-6 text-center space-y-2">
                    <p className="text-sm" style={{ color: "var(--color-text-subtle)" }}>
                        고객이신가요?{" "}
                        <Link href="/signup" className="text-blue-600 hover:text-blue-800 font-medium">
                            회원가입
                        </Link>
                    </p>
                    <p className="text-xs" style={{ color: "var(--color-text-subtle)" }}>
                        직원 계정 문의는 대표이사에게 연락하세요
                    </p>
                </div>
            </div>
        </div>
    );
}
