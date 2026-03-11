"use client";

import React, { useState, useEffect, useRef } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { ToastProvider } from "@/components/ui/Toast";
import { Sidebar } from "./Sidebar";
import { Menu, X, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

// 페이지 전환 애니메이션 래퍼 컴포넌트
function PageTransition({ children, pathname }: { children: React.ReactNode; pathname: string }) {
    const [isAnimating, setIsAnimating] = useState(false);
    const [displayChildren, setDisplayChildren] = useState(children);
    const prevPathRef = useRef(pathname);

    useEffect(() => {
        if (prevPathRef.current !== pathname) {
            setIsAnimating(true);
            // 짧은 딜레이 후 새 콘텐츠 표시
            const timer = setTimeout(() => {
                setDisplayChildren(children);
                setIsAnimating(false);
            }, 150);
            prevPathRef.current = pathname;
            return () => clearTimeout(timer);
        } else {
            setDisplayChildren(children);
        }
    }, [children, pathname]);

    return (
        <div
            className={cn(
                "h-full w-full transition-all duration-300 ease-out",
                isAnimating
                    ? "opacity-0 translate-y-2"
                    : "opacity-100 translate-y-0"
            )}
        >
            {displayChildren}
        </div>
    );
}

// 인증이 필요하지 않은 페이지들 (trailingSlash 호환)
const PUBLIC_PATHS = ["/login", "/login/"];

// 사이드바 없이 전체화면 표시할 페이지 (인증은 필요)
const FRAMELESS_PATHS = ["/erp/window", "/erp/window/"];

function AuthenticatedLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const router = useRouter();
    const { isAuthenticated, isLoading } = useAuth();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    // 경로 변경 시 모바일 메뉴 닫기
    useEffect(() => {
        setMobileMenuOpen(false);
    }, [pathname]);

    // 모바일 메뉴 열릴 때 body 스크롤 방지
    useEffect(() => {
        if (mobileMenuOpen) {
            document.body.style.overflow = "hidden";
        } else {
            document.body.style.overflow = "";
        }
        return () => {
            document.body.style.overflow = "";
        };
    }, [mobileMenuOpen]);


    // 알림 설정 변경 이벤트 리스너
    useEffect(() => {
        const handleNotif = (e: Event) => {
            const detail = (e as CustomEvent).detail;
            if (detail) localStorage.setItem('kis-notification-settings', JSON.stringify(detail));
        };
        window.addEventListener('kis-notification-settings-updated', handleNotif);
        return () => window.removeEventListener('kis-notification-settings-updated', handleNotif);
    }, []);
    // 공개 페이지인지 확인
    const isPublicPage = PUBLIC_PATHS.includes(pathname);

    // 로딩 중 - Claude.ai 스타일 로딩
    if (isLoading) {
        return (
            <div className="flex h-screen flex-col items-center justify-center bg-bg">
                <div className="flex flex-col items-center gap-4">
                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand to-brand-strong shadow-lg animate-pulse">
                        <Sparkles className="h-7 w-7 text-white" />
                    </div>
                    <div className="text-sm font-medium text-text-subtle">
                        불러오는 중...
                    </div>
                </div>
            </div>
        );
    }

    // 로그인 페이지는 사이드바 없이 표시
    if (isPublicPage) {
        return <>{children}</>;
    }

    // 인증되지 않은 경우 로그인 페이지로 리다이렉트
    if (!isAuthenticated) {
        if (typeof window !== "undefined") {
            router.push("/login");
        }
        return (
            <div className="flex h-screen flex-col items-center justify-center bg-bg">
                <div className="flex flex-col items-center gap-4">
                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand to-brand-strong shadow-lg">
                        <Sparkles className="h-7 w-7 text-white" />
                    </div>
                    <div className="text-sm font-medium text-text-subtle">
                        로그인 페이지로 이동 중...
                    </div>
                </div>
            </div>
        );
    }

    // ERP 독립 윈도우: 사이드바 없이 컨텐츠만 표시
    const isFrameless = FRAMELESS_PATHS.some(p => pathname.startsWith(p));
    if (isFrameless) {
        return <>{children}</>;
    }

    // 인증된 사용자: Claude.ai 스타일 레이아웃
    return (
        <div className="flex h-screen overflow-hidden bg-bg">
            {/* 모바일 메뉴 버튼 - Claude.ai 스타일 */}
            <button
                onClick={() => setMobileMenuOpen(true)}
                className={cn(
                    "fixed left-4 top-4 z-50 flex h-11 w-11 items-center justify-center rounded-xl",
                    "bg-surface shadow-md border border-border/50",
                    "hover:bg-surface-secondary transition-all duration-200",
                    "lg:hidden",
                    mobileMenuOpen && "hidden"
                )}
                aria-label="메뉴 열기"
            >
                <Menu className="h-5 w-5 text-text" />
            </button>

            {/* 모바일 오버레이 - 부드러운 블러 효과 */}
            <div
                className={cn(
                    "fixed inset-0 z-40 bg-black/30 backdrop-blur-sm transition-opacity duration-300 lg:hidden",
                    mobileMenuOpen ? "opacity-100" : "opacity-0 pointer-events-none"
                )}
                onClick={() => setMobileMenuOpen(false)}
            />

            {/* 사이드바 컨테이너 */}
            <div
                className={cn(
                    "fixed inset-y-0 left-0 z-50 transform transition-transform duration-300 ease-out",
                    "lg:relative lg:translate-x-0",
                    mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
                )}
            >
                {/* 모바일 닫기 버튼 */}
                <button
                    onClick={() => setMobileMenuOpen(false)}
                    className={cn(
                        "absolute right-3 top-5 z-50 flex h-8 w-8 items-center justify-center rounded-lg",
                        "hover:bg-surface-secondary transition-colors duration-200",
                        "lg:hidden"
                    )}
                    aria-label="메뉴 닫기"
                >
                    <X className="h-5 w-5 text-text-subtle" />
                </button>
                <Sidebar />
            </div>

            {/* 메인 컨텐츠 영역 - Claude.ai 스타일 */}
            <main
                className={cn(
                    "flex-1 overflow-hidden",
                    "w-full lg:w-auto",
                    "relative"
                )}
            >
                {/* 메인 콘텐츠 래퍼 - 페이지 전환 애니메이션 적용 */}
                <div className="h-full w-full overflow-auto">
                    <PageTransition pathname={pathname}>
                        {children}
                    </PageTransition>
                </div>
            </main>
        </div>
    );
}

export function ClientLayout({ children }: { children: React.ReactNode }) {
    return (
        <AuthProvider>
            <ToastProvider>
                <AuthenticatedLayout>{children}</AuthenticatedLayout>
            </ToastProvider>
        </AuthProvider>
    );
}
