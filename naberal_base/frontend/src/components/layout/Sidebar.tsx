"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import {
    Bot,
    Receipt,
    Grid3X3,
    Calendar,
    Mail,
    Layers,
    ChevronLeft,
    ChevronRight,
    Plus,
    MessageSquare,
    Settings,
    LogOut,
    User,
    Sparkles,
    LayoutDashboard,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";

interface SidebarProps {
    className?: string;
}

export function Sidebar({ className }: SidebarProps) {
    const pathname = usePathname();
    const router = useRouter();
    const { user, logout } = useAuth();
    const [collapsed, setCollapsed] = useState(false);
    const [profileAvatar, setProfileAvatar] = useState<string | null>(null);
    const [recentChats, setRecentChats] = useState<Array<{ id: string; title: string }>>([]);

    // ERP 탭에서 사이드바 자동 접기 (이전 상태 저장)
    const wasInErpRef = useRef(false);
    const prevCollapsedRef = useRef(false);

    useEffect(() => {
        const isErp = pathname === "/erp" || pathname === "/erp/";

        if (isErp && !wasInErpRef.current) {
            // ERP 탭 진입 시: 현재 상태 저장 후 접기
            prevCollapsedRef.current = collapsed;
            setCollapsed(true);
        } else if (!isErp && wasInErpRef.current) {
            // ERP 탭 이탈 시: 이전 상태로 복원
            setCollapsed(prevCollapsedRef.current);
        }

        wasInErpRef.current = isErp;
    }, [pathname]); // collapsed는 의존성에서 제외

    // 최근 대화 로드 (localStorage에서)
    useEffect(() => {
        const loadRecentChats = () => {
            try {
                const saved = localStorage.getItem('ai_manager_chat_sessions');
                if (saved) {
                    const sessions = JSON.parse(saved);
                    // 최근 5개만 표시, 최신순 정렬
                    const recent = sessions
                        .sort((a: { updatedAt: string }, b: { updatedAt: string }) =>
                            new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
                        )
                        .slice(0, 5)
                        .map((s: { id: string; title: string }) => ({ id: s.id, title: s.title }));
                    setRecentChats(recent);
                }
            } catch (e) {
                console.error('최근 대화 로드 실패:', e);
            }
        };

        loadRecentChats();

        // storage 이벤트 리스닝 (다른 탭/컴포넌트에서 변경 시)
        const handleStorageChange = (e: StorageEvent) => {
            if (e.key === 'ai_manager_chat_sessions') {
                loadRecentChats();
            }
        };

        // 같은 탭에서의 변경 감지를 위한 커스텀 이벤트
        const handleCustomUpdate = () => loadRecentChats();

        window.addEventListener('storage', handleStorageChange);
        window.addEventListener('kis-chat-updated', handleCustomUpdate);

        return () => {
            window.removeEventListener('storage', handleStorageChange);
            window.removeEventListener('kis-chat-updated', handleCustomUpdate);
        };
    }, []);

    // 채팅 세션 로드 핸들러
    const handleLoadChat = (sessionId: string) => {
        // URL searchParams로 세션 ID 전달 (localStorage 타이밍 이슈 방지)
        router.push(`/ai-manager?loadSession=${encodeURIComponent(sessionId)}`);
    };

    // 로그아웃 핸들러
    const handleLogout = () => {
        logout();
        router.push("/login");
    };

    // 역할 표시 이름
    const getRoleName = (role: string) => {
        switch (role) {
            case "ceo": return "대표이사";
            case "manager": return "관리자";
            case "staff": return "직원";
            default: return role;
        }
    };

    // Load profile avatar from localStorage
    useEffect(() => {
        const savedAvatar = localStorage.getItem('kis-profile-avatar');
        if (savedAvatar) {
            setProfileAvatar(savedAvatar);
        }

        const handleStorageChange = (e: StorageEvent) => {
            if (e.key === 'kis-profile-avatar') {
                setProfileAvatar(e.newValue);
            }
        };
        window.addEventListener('storage', handleStorageChange);
        return () => window.removeEventListener('storage', handleStorageChange);
    }, []);


    // 설정 변경 이벤트 리스너 (프로필 아바타 등 갱신)
    useEffect(() => {
        const handleSettingsUpdated = () => {
            const savedAvatar = localStorage.getItem('kis-profile-avatar');
            setProfileAvatar(savedAvatar);
        };
        window.addEventListener('kis-settings-updated', handleSettingsUpdated);
        return () => window.removeEventListener('kis-settings-updated', handleSettingsUpdated);
    }, []);
    const navItems = [
        { icon: LayoutDashboard, label: "대시보드", href: "/dashboard", description: "홈 대시보드" },
        { icon: Bot, label: "AI매니저", href: "/ai-manager", description: "AI 견적 어시스턴트" },
        { icon: Receipt, label: "견적", href: "/quote", description: "견적서 작성" },
        { icon: Grid3X3, label: "ERP", href: "/erp", description: "업무 관리" },
        { icon: Calendar, label: "캘린더", href: "/calendar", description: "일정 관리" },
        { icon: Mail, label: "이메일", href: "/email", description: "이메일 발송" },
        { icon: Layers, label: "도면", href: "/drawings", description: "도면 관리" },
    ];

    return (
        <aside
            className={cn(
                "group/sidebar relative flex h-full flex-col bg-sidebar-bg border-r border-border transition-all duration-300 ease-in-out sidebar-depth",
                collapsed ? "w-[68px]" : "w-[280px]",
                className
            )}
        >
            {/* Toggle Button - Claude.ai style edge button */}
            <button
                onClick={() => setCollapsed(!collapsed)}
                className={cn(
                    "absolute -right-3 top-6 z-50 flex h-6 w-6 items-center justify-center rounded-full",
                    "bg-surface border border-border shadow-sm",
                    "hover:bg-surface-secondary transition-colors duration-200",
                    "opacity-0 group-hover/sidebar:opacity-100"
                )}
                title={collapsed ? "사이드바 펼치기" : "사이드바 접기"}
            >
                {collapsed ? (
                    <ChevronRight className="h-3.5 w-3.5 text-text-subtle" />
                ) : (
                    <ChevronLeft className="h-3.5 w-3.5 text-text-subtle" />
                )}
            </button>

            {/* Header - Logo & Brand */}
            <div className={cn(
                "flex items-center gap-3 px-4 py-5 border-b border-border/50",
                collapsed && "justify-center px-2"
            )}>
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand to-brand-strong shadow-sm">
                    <Sparkles className="h-5 w-5 text-white" />
                </div>
                {!collapsed && (
                    <div className="flex flex-col">
                        <span className="text-base font-semibold text-text-strong tracking-tight">
                            한국산업
                        </span>
                        <span className="text-xs text-text-subtle">
                            KIS Estimator
                        </span>
                    </div>
                )}
            </div>

            {/* New Chat Button - Claude.ai style */}
            <div className={cn("px-3 pt-4 pb-2", collapsed && "px-2")}>
                <Button
                    onClick={() => router.push('/ai-manager')}
                    className={cn(
                        "w-full gap-2 rounded-xl font-medium shadow-sm",
                        "bg-brand hover:bg-brand-strong text-white",
                        "transition-all duration-200",
                        collapsed ? "justify-center px-0 h-10 w-10 mx-auto" : "justify-start px-4 h-11"
                    )}
                >
                    <Plus className={cn("shrink-0", collapsed ? "h-5 w-5" : "h-4 w-4")} />
                    {!collapsed && <span>새 대화</span>}
                </Button>
            </div>

            {/* Navigation - Main Menu */}
            <div className="flex-1 overflow-y-auto px-3 py-2">
                {!collapsed && (
                    <div className="mb-2 px-2 text-xs font-semibold text-text-subtle uppercase tracking-wider">
                        메뉴
                    </div>
                )}
                <nav className="space-y-1">
                    {navItems.map((item, index) => {
                        const isActive = pathname === item.href;
                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={cn(
                                    "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium",
                                    "transition-all duration-300 ease-out",
                                    "hover:translate-x-1",
                                    isActive
                                        ? "bg-brand/10 text-brand shadow-sm"
                                        : "text-text hover:bg-surface-secondary",
                                    collapsed && "justify-center px-0 mx-auto w-10 h-10 hover:translate-x-0 hover:scale-105"
                                )}
                                title={collapsed ? item.label : undefined}
                                style={{
                                    animationDelay: `${index * 50}ms`,
                                }}
                            >
                                <item.icon className={cn(
                                    "shrink-0 transition-all duration-300",
                                    isActive ? "text-brand" : "text-text-subtle group-hover:text-text",
                                    collapsed ? "h-5 w-5" : "h-4.5 w-4.5",
                                    "group-hover:scale-110"
                                )} />
                                {!collapsed && (
                                    <span className="truncate transition-all duration-200">{item.label}</span>
                                )}
                            </Link>
                        );
                    })}
                </nav>

                {/* Recent Chats - Only when expanded */}
                {!collapsed && (
                    <div className="mt-6">
                        <div className="mb-2 px-2 text-xs font-semibold text-text-subtle uppercase tracking-wider">
                            최근 대화
                        </div>
                        <div className="space-y-0.5">
                            {recentChats.length > 0 ? (
                                recentChats.map((chat, index) => (
                                    <button
                                        key={chat.id}
                                        onClick={() => handleLoadChat(chat.id)}
                                        className="group flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-text-subtle hover:bg-surface-secondary hover:text-text transition-all duration-300 ease-out hover:translate-x-1"
                                        style={{
                                            animationDelay: `${index * 30}ms`,
                                        }}
                                    >
                                        <MessageSquare className="h-4 w-4 shrink-0 opacity-60 group-hover:opacity-100 transition-all duration-300 group-hover:scale-110" />
                                        <span className="truncate text-left">{chat.title}</span>
                                    </button>
                                ))
                            ) : (
                                <div className="px-3 py-2 text-sm text-text-subtle/60">
                                    아직 대화 기록이 없습니다
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Footer - User Profile & Actions */}
            <div className="border-t border-border/50 p-3">
                {/* Settings Link */}
                <Link
                    href="/settings"
                    className={cn(
                        "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium mb-2",
                        "transition-all duration-300 ease-out",
                        "hover:translate-x-1",
                        pathname === "/settings"
                            ? "bg-brand/10 text-brand shadow-sm"
                            : "text-text-subtle hover:bg-surface-secondary hover:text-text",
                        collapsed && "justify-center px-0 mx-auto w-10 h-10 hover:translate-x-0 hover:scale-105"
                    )}
                    title={collapsed ? "설정" : undefined}
                >
                    <Settings className={cn(
                        "shrink-0 transition-all duration-300 group-hover:scale-110",
                        collapsed ? "h-5 w-5" : "h-4 w-4"
                    )} />
                    {!collapsed && <span>설정</span>}
                </Link>

                {/* User Profile */}
                <div
                    className={cn(
                        "flex items-center gap-3 rounded-xl p-2 hover:bg-surface-secondary transition-all duration-200 cursor-pointer",
                        collapsed && "justify-center"
                    )}
                >
                    <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-strong text-white overflow-hidden ring-2 ring-brand/20">
                        {profileAvatar ? (
                            <img src={profileAvatar} alt="프로필" className="w-full h-full object-cover" />
                        ) : (
                            <span className="text-sm font-semibold">
                                {user?.name?.charAt(0) || <User className="h-4 w-4" />}
                            </span>
                        )}
                    </div>
                    {!collapsed && user && (
                        <div className="flex flex-1 flex-col min-w-0">
                            <span className="text-sm font-medium text-text truncate">
                                {user.name}
                            </span>
                            <span className="text-xs text-text-subtle">
                                {getRoleName(user.role)}
                            </span>
                        </div>
                    )}
                    {!collapsed && (
                        <button
                            onClick={handleLogout}
                            className="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-red-50 transition-colors"
                            title="로그아웃"
                        >
                            <LogOut className="h-4 w-4 text-red-500" />
                        </button>
                    )}
                </div>

                {/* Logout when collapsed */}
                {collapsed && (
                    <button
                        onClick={handleLogout}
                        className="mt-2 flex w-full items-center justify-center rounded-xl p-2.5 hover:bg-red-50 transition-colors"
                        title="로그아웃"
                    >
                        <LogOut className="h-5 w-5 text-red-500" />
                    </button>
                )}
            </div>
        </aside>
    );
}
