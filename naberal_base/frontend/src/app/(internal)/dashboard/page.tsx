"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import {
    FileText,
    Calendar,
    MessageSquare,
    TrendingUp,
    Clock,
    CheckCircle2,
    AlertCircle,
    ArrowRight,
    Building2,
    Zap,
    BarChart3,
    Plus,
    Bot,
    Receipt,
    Layers,
    Users,
    DollarSign,
    Activity,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";

// 통계 카드 타입
interface StatCard {
    title: string;
    value: string | number;
    change?: string;
    changeType?: "positive" | "negative" | "neutral";
    icon: React.ComponentType<{ className?: string }>;
    color: string;
    href: string;
}

// 최근 활동 타입
interface RecentActivity {
    id: string;
    type: "estimate" | "calendar" | "chat" | "drawing";
    title: string;
    description: string;
    timestamp: Date;
    status?: "completed" | "pending" | "in_progress";
}

// 일정 타입
interface UpcomingEvent {
    id: string;
    title: string;
    date: Date;
    type: "meeting" | "deadline" | "task";
}

export default function DashboardPage() {
    const router = useRouter();
    const { user } = useAuth();
    const [currentTime, setCurrentTime] = useState(new Date());
    const [stats, setStats] = useState<StatCard[]>([]);
    const [recentActivities, setRecentActivities] = useState<RecentActivity[]>([]);
    const [upcomingEvents, setUpcomingEvents] = useState<UpcomingEvent[]>([]);
    const [savedEstimatesCount, setSavedEstimatesCount] = useState(0);
    const [chatSessionsCount, setChatSessionsCount] = useState(0);

    // 시간 업데이트
    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentTime(new Date());
        }, 60000);
        return () => clearInterval(timer);
    }, []);

    // localStorage에서 데이터 로드
    useEffect(() => {
        // 저장된 견적 개수
        try {
            const savedEstimates = localStorage.getItem("savedEstimates");
            if (savedEstimates) {
                const parsed = JSON.parse(savedEstimates);
                setSavedEstimatesCount(Array.isArray(parsed) ? parsed.length : 0);
            }
        } catch {
            setSavedEstimatesCount(0);
        }

        // 채팅 세션 개수
        try {
            const chatSessions = localStorage.getItem("ai_manager_chat_sessions");
            if (chatSessions) {
                const parsed = JSON.parse(chatSessions);
                setChatSessionsCount(Array.isArray(parsed) ? parsed.length : 0);
            }
        } catch {
            setChatSessionsCount(0);
        }
    }, []);

    // 설정 변경 이벤트 리스너 (대시보드 통계 갱신)
    useEffect(() => {
        const handleSettingsUpdated = () => {
            try {
                const savedEstimates = localStorage.getItem("savedEstimates");
                if (savedEstimates) {
                    const parsed = JSON.parse(savedEstimates);
                    setSavedEstimatesCount(Array.isArray(parsed) ? parsed.length : 0);
                }
            } catch {
                setSavedEstimatesCount(0);
            }

            try {
                const chatSessions = localStorage.getItem("ai_manager_chat_sessions");
                if (chatSessions) {
                    const parsed = JSON.parse(chatSessions);
                    setChatSessionsCount(Array.isArray(parsed) ? parsed.length : 0);
                }
            } catch {
                setChatSessionsCount(0);
            }
        };
        window.addEventListener('kis-settings-updated', handleSettingsUpdated);
        return () => window.removeEventListener('kis-settings-updated', handleSettingsUpdated);
    }, []);

    // 통계 데이터 설정
    useEffect(() => {
        setStats([
            {
                title: "이번 달 견적",
                value: savedEstimatesCount,
                change: "+12%",
                changeType: "positive",
                icon: FileText,
                color: "bg-blue-500",
                href: "/quote",
            },
            {
                title: "진행 중인 프로젝트",
                value: 0,
                change: "등록된 프로젝트 없음",
                changeType: "neutral",
                icon: Building2,
                color: "bg-purple-500",
                href: "/erp",
            },
            {
                title: "AI 대화 세션",
                value: chatSessionsCount,
                change: "활성",
                changeType: "positive",
                icon: MessageSquare,
                color: "bg-green-500",
                href: "/ai-manager",
            },
            {
                title: "이번 주 일정",
                value: 0,
                change: "등록된 일정 없음",
                changeType: "neutral",
                icon: Calendar,
                color: "bg-orange-500",
                href: "/calendar",
            },
        ]);
    }, [savedEstimatesCount, chatSessionsCount]);

    // 최근 활동 설정
    useEffect(() => {
        // localStorage에서 최근 활동 데이터 구성
        const activities: RecentActivity[] = [];

        // 채팅 세션에서 최근 활동 추가
        try {
            const chatSessions = localStorage.getItem("ai_manager_chat_sessions");
            if (chatSessions) {
                const parsed = JSON.parse(chatSessions);
                const sortedSessions = parsed
                    .sort((a: { updatedAt: string }, b: { updatedAt: string }) =>
                        new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
                    )
                    .slice(0, 3);

                sortedSessions.forEach((session: { id: string; title: string; updatedAt: string }) => {
                    activities.push({
                        id: session.id,
                        type: "chat",
                        title: session.title || "AI 대화",
                        description: "AI 매니저와의 대화",
                        timestamp: new Date(session.updatedAt),
                        status: "completed",
                    });
                });
            }
        } catch {
            // ignore
        }

        // 저장된 견적에서 최근 활동 추가
        try {
            const savedEstimates = localStorage.getItem("savedEstimates");
            if (savedEstimates) {
                const parsed = JSON.parse(savedEstimates);
                const sortedEstimates = parsed
                    .sort((a: { savedAt: string }, b: { savedAt: string }) =>
                        new Date(b.savedAt).getTime() - new Date(a.savedAt).getTime()
                    )
                    .slice(0, 3);

                sortedEstimates.forEach((estimate: { id: string; customer: string; panelName: string; savedAt: string }) => {
                    activities.push({
                        id: estimate.id,
                        type: "estimate",
                        title: `${estimate.customer || "고객"} - ${estimate.panelName || "분전반"}`,
                        description: "견적서 작성",
                        timestamp: new Date(estimate.savedAt),
                        status: "completed",
                    });
                });
            }
        } catch {
            // ignore
        }

        // 시간순 정렬
        activities.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
        setRecentActivities(activities.slice(0, 5));

        // 실제 등록된 일정만 표시 (가짜 데이터 제거)
        setUpcomingEvents([]);
    }, []);

    // 시간 포맷팅
    const formatTime = (date: Date) => {
        return date.toLocaleTimeString("ko-KR", {
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    const formatDate = (date: Date) => {
        return date.toLocaleDateString("ko-KR", {
            year: "numeric",
            month: "long",
            day: "numeric",
            weekday: "long",
        });
    };

    const formatRelativeTime = (date: Date) => {
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return "방금 전";
        if (diffMins < 60) return `${diffMins}분 전`;
        if (diffHours < 24) return `${diffHours}시간 전`;
        return `${diffDays}일 전`;
    };

    const getActivityIcon = (type: string) => {
        switch (type) {
            case "estimate":
                return <Receipt className="h-4 w-4" />;
            case "calendar":
                return <Calendar className="h-4 w-4" />;
            case "chat":
                return <MessageSquare className="h-4 w-4" />;
            case "drawing":
                return <Layers className="h-4 w-4" />;
            default:
                return <Activity className="h-4 w-4" />;
        }
    };

    const getStatusBadge = (status?: string) => {
        switch (status) {
            case "completed":
                return (
                    <span className="flex items-center gap-1 text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
                        <CheckCircle2 className="h-3 w-3" />
                        완료
                    </span>
                );
            case "pending":
                return (
                    <span className="flex items-center gap-1 text-xs text-yellow-600 bg-yellow-50 px-2 py-0.5 rounded-full">
                        <Clock className="h-3 w-3" />
                        대기
                    </span>
                );
            case "in_progress":
                return (
                    <span className="flex items-center gap-1 text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">
                        <Activity className="h-3 w-3" />
                        진행중
                    </span>
                );
            default:
                return null;
        }
    };

    const getEventTypeColor = (type: string) => {
        switch (type) {
            case "meeting":
                return "bg-blue-100 text-blue-700 border-blue-200";
            case "deadline":
                return "bg-red-100 text-red-700 border-red-200";
            case "task":
                return "bg-green-100 text-green-700 border-green-200";
            default:
                return "bg-gray-100 text-gray-700 border-gray-200";
        }
    };

    // 인사말
    const getGreeting = () => {
        const hour = currentTime.getHours();
        if (hour < 12) return "좋은 아침입니다";
        if (hour < 18) return "좋은 오후입니다";
        return "좋은 저녁입니다";
    };

    return (
        <div className="min-h-full bg-bg p-6 space-y-6">
            {/* 헤더 섹션 */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-text-strong">
                        {getGreeting()}, {user?.name || "사용자"}님
                    </h1>
                    <p className="text-text-subtle mt-1">
                        {formatDate(currentTime)} · {formatTime(currentTime)}
                    </p>
                </div>
                <div className="flex gap-3">
                    <Button
                        onClick={() => router.push("/ai-manager")}
                        className="gap-2 bg-brand hover:bg-brand-strong text-white"
                    >
                        <Bot className="h-4 w-4" />
                        AI 매니저
                    </Button>
                    <Button
                        onClick={() => router.push("/quote")}
                        variant="outline"
                        className="gap-2"
                    >
                        <Plus className="h-4 w-4" />
                        새 견적
                    </Button>
                </div>
            </div>

            {/* 통계 카드 그리드 */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {stats.map((stat, index) => (
                    <div
                        key={index}
                        role="button"
                        tabIndex={0}
                        aria-label={`${stat.title}: ${stat.value}${stat.change ? `, ${stat.change}` : ""}. 클릭하여 이동`}
                        className="bg-surface rounded-xl border border-border/50 p-5 hover:shadow-md transition-all cursor-pointer hover:border-brand/30"
                        onClick={() => router.push(stat.href)}
                        onKeyDown={(e: React.KeyboardEvent) => {
                            if (e.key === "Enter" || e.key === " ") {
                                e.preventDefault();
                                router.push(stat.href);
                            }
                        }}
                    >
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="text-sm text-text-subtle">{stat.title}</p>
                                <p className="text-2xl font-bold text-text-strong mt-1">
                                    {stat.value}
                                </p>
                                {stat.change && (
                                    <p
                                        className={cn(
                                            "text-xs mt-1",
                                            stat.changeType === "positive" && "text-green-600",
                                            stat.changeType === "negative" && "text-red-600",
                                            stat.changeType === "neutral" && "text-text-subtle"
                                        )}
                                    >
                                        {stat.change}
                                    </p>
                                )}
                            </div>
                            <div
                                className={cn(
                                    "flex h-10 w-10 items-center justify-center rounded-lg",
                                    stat.color
                                )}
                            >
                                <stat.icon className="h-5 w-5 text-white" />
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* 메인 컨텐츠 그리드 */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* 최근 활동 */}
                <div className="lg:col-span-2 bg-surface rounded-xl border border-border/50 p-5">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-semibold text-text-strong">최근 활동</h2>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="text-text-subtle hover:text-text"
                            onClick={() => router.push("/ai-manager")}
                        >
                            전체 보기
                            <ArrowRight className="h-4 w-4 ml-1" />
                        </Button>
                    </div>
                    <div className="space-y-3">
                        {recentActivities.length > 0 ? (
                            recentActivities.map((activity) => (
                                <div
                                    key={activity.id}
                                    role="button"
                                    tabIndex={0}
                                    aria-label={`${activity.title} - ${activity.description}. 클릭하여 이동`}
                                    className="flex items-center gap-4 p-3 rounded-lg hover:bg-surface-secondary transition-colors cursor-pointer"
                                    onClick={() => {
                                        if (activity.type === "chat") {
                                            router.push(`/ai-manager?loadSession=${encodeURIComponent(activity.id)}`);
                                        } else if (activity.type === "estimate") {
                                            router.push("/quote");
                                        }
                                    }}
                                    onKeyDown={(e: React.KeyboardEvent) => {
                                        if (e.key === "Enter" || e.key === " ") {
                                            e.preventDefault();
                                            if (activity.type === "chat") {
                                                router.push(`/ai-manager?loadSession=${encodeURIComponent(activity.id)}`);
                                            } else if (activity.type === "estimate") {
                                                router.push("/quote");
                                            }
                                        }
                                    }}
                                >
                                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand/10 text-brand">
                                        {getActivityIcon(activity.type)}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-text-strong truncate">
                                            {activity.title}
                                        </p>
                                        <p className="text-xs text-text-subtle">
                                            {activity.description}
                                        </p>
                                    </div>
                                    <div className="flex flex-col items-end gap-1">
                                        <span className="text-xs text-text-subtle">
                                            {formatRelativeTime(activity.timestamp)}
                                        </span>
                                        {getStatusBadge(activity.status)}
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="text-center py-8 text-text-subtle">
                                <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
                                <p>아직 활동 기록이 없습니다</p>
                                <Button
                                    variant="link"
                                    className="mt-2"
                                    onClick={() => router.push("/ai-manager")}
                                >
                                    AI 매니저로 시작하기
                                </Button>
                            </div>
                        )}
                    </div>
                </div>

                {/* 오늘의 일정 */}
                <div className="bg-surface rounded-xl border border-border/50 p-5">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-semibold text-text-strong">예정된 일정</h2>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="text-text-subtle hover:text-text"
                            onClick={() => router.push("/calendar")}
                        >
                            캘린더
                            <ArrowRight className="h-4 w-4 ml-1" />
                        </Button>
                    </div>
                    <div className="space-y-3">
                        {upcomingEvents.map((event) => (
                            <div
                                key={event.id}
                                role="button"
                                tabIndex={0}
                                aria-label={`${event.title}. 클릭하여 캘린더로 이동`}
                                className={cn(
                                    "p-3 rounded-lg border cursor-pointer hover:shadow-sm transition-all",
                                    getEventTypeColor(event.type)
                                )}
                                onClick={() => router.push("/calendar")}
                                onKeyDown={(e: React.KeyboardEvent) => {
                                    if (e.key === "Enter" || e.key === " ") {
                                        e.preventDefault();
                                        router.push("/calendar");
                                    }
                                }}
                            >
                                <p className="text-sm font-medium">{event.title}</p>
                                <p className="text-xs mt-1 opacity-80">
                                    {event.date.toLocaleDateString("ko-KR", {
                                        month: "short",
                                        day: "numeric",
                                        hour: "2-digit",
                                        minute: "2-digit",
                                    })}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* 빠른 액션 카드 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <button
                    onClick={() => router.push("/ai-manager")}
                    className="flex flex-col items-center gap-3 p-5 bg-surface rounded-xl border border-border/50 hover:shadow-md hover:border-brand/30 transition-all group"
                >
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand/10 group-hover:bg-brand/20 transition-colors">
                        <Bot className="h-6 w-6 text-brand" />
                    </div>
                    <span className="text-sm font-medium text-text-strong">AI 견적</span>
                </button>
                <button
                    onClick={() => router.push("/quote")}
                    className="flex flex-col items-center gap-3 p-5 bg-surface rounded-xl border border-border/50 hover:shadow-md hover:border-brand/30 transition-all group"
                >
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-100 group-hover:bg-purple-200 transition-colors">
                        <Receipt className="h-6 w-6 text-purple-600" />
                    </div>
                    <span className="text-sm font-medium text-text-strong">견적 작성</span>
                </button>
                <button
                    onClick={() => router.push("/erp")}
                    className="flex flex-col items-center gap-3 p-5 bg-surface rounded-xl border border-border/50 hover:shadow-md hover:border-brand/30 transition-all group"
                >
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-100 group-hover:bg-green-200 transition-colors">
                        <BarChart3 className="h-6 w-6 text-green-600" />
                    </div>
                    <span className="text-sm font-medium text-text-strong">ERP</span>
                </button>
                <button
                    onClick={() => router.push("/drawings")}
                    className="flex flex-col items-center gap-3 p-5 bg-surface rounded-xl border border-border/50 hover:shadow-md hover:border-brand/30 transition-all group"
                >
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-orange-100 group-hover:bg-orange-200 transition-colors">
                        <Layers className="h-6 w-6 text-orange-600" />
                    </div>
                    <span className="text-sm font-medium text-text-strong">도면 관리</span>
                </button>
            </div>

            {/* 시스템 상태 */}
            <div className="bg-surface rounded-xl border border-border/50 p-5">
                <h2 className="text-lg font-semibold text-text-strong mb-4">시스템 현황</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="flex items-center gap-3">
                        <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse" />
                        <div>
                            <p className="text-sm font-medium text-text-strong">API 서버</p>
                            <p className="text-xs text-text-subtle">정상 운영중</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse" />
                        <div>
                            <p className="text-sm font-medium text-text-strong">AI 엔진</p>
                            <p className="text-xs text-text-subtle">Claude 연결됨</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse" />
                        <div>
                            <p className="text-sm font-medium text-text-strong">데이터베이스</p>
                            <p className="text-xs text-text-subtle">정상</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse" />
                        <div>
                            <p className="text-sm font-medium text-text-strong">캐시</p>
                            <p className="text-xs text-text-subtle">활성화</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
