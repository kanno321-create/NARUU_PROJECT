"use client";

import React, { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
    TrendingUp,
    TrendingDown,
    ArrowUpRight,
    ArrowDownRight,
    Wallet,
    Receipt,
    CreditCard,
    Users,
    AlertCircle,
    Calendar,
    ChevronRight,
    FileText,
    Clock,
    MoreHorizontal,
    ArrowRight,
    Activity,
    PieChart,
    BarChart3,
} from "lucide-react";

// 메트릭 카드 (대기업 스타일 + 모던 애니메이션)
function MetricCard({
    title,
    value,
    subtitle,
    change,
    changeType,
    icon: Icon,
    accentColor = "blue",
    delay = 0,
    onClick,
}: {
    title: string;
    value: string;
    subtitle?: string;
    change?: string;
    changeType?: "positive" | "negative" | "neutral";
    icon: React.ElementType;
    accentColor?: "blue" | "emerald" | "amber" | "rose" | "violet";
    delay?: number;
    onClick?: () => void;
}) {
    const colorMap = {
        blue: {
            bg: "bg-blue-50 dark:bg-blue-950/30",
            icon: "text-blue-600 dark:text-blue-400",
            border: "border-blue-100 dark:border-blue-900/50",
            gradient: "from-blue-500/20 via-blue-400/10 to-transparent",
            glow: "group-hover:shadow-blue-500/20",
        },
        emerald: {
            bg: "bg-emerald-50 dark:bg-emerald-950/30",
            icon: "text-emerald-600 dark:text-emerald-400",
            border: "border-emerald-100 dark:border-emerald-900/50",
            gradient: "from-emerald-500/20 via-emerald-400/10 to-transparent",
            glow: "group-hover:shadow-emerald-500/20",
        },
        amber: {
            bg: "bg-amber-50 dark:bg-amber-950/30",
            icon: "text-amber-600 dark:text-amber-400",
            border: "border-amber-100 dark:border-amber-900/50",
            gradient: "from-amber-500/20 via-amber-400/10 to-transparent",
            glow: "group-hover:shadow-amber-500/20",
        },
        rose: {
            bg: "bg-rose-50 dark:bg-rose-950/30",
            icon: "text-rose-600 dark:text-rose-400",
            border: "border-rose-100 dark:border-rose-900/50",
            gradient: "from-rose-500/20 via-rose-400/10 to-transparent",
            glow: "group-hover:shadow-rose-500/20",
        },
        violet: {
            bg: "bg-violet-50 dark:bg-violet-950/30",
            icon: "text-violet-600 dark:text-violet-400",
            border: "border-violet-100 dark:border-violet-900/50",
            gradient: "from-violet-500/20 via-violet-400/10 to-transparent",
            glow: "group-hover:shadow-violet-500/20",
        },
    };

    const colors = colorMap[accentColor];

    return (
        <div
            className={cn(
                "group relative overflow-hidden rounded-2xl border border-border/40 bg-surface p-5 metric-card-depth metric-card-depth",
                "transition-all duration-300 ease-out",
                "hover:border-border/60 hover:-translate-y-1",
                colors.glow,
                "opacity-0 animate-fade-in",
                onClick && "cursor-pointer"
            )}
            style={{ animationDelay: `${delay}ms` }}
            onClick={onClick}
        >
            {/* 배경 그라데이션 데코레이션 - 애니메이션 */}
            <div className={cn(
                "absolute -right-8 -top-8 h-32 w-32 rounded-full bg-gradient-to-br opacity-0",
                "transition-all duration-500 ease-out",
                "group-hover:opacity-100 group-hover:scale-150",
                colors.gradient
            )} />

            {/* 하단 그라데이션 라인 */}
            <div className={cn(
                "absolute bottom-0 left-0 h-1 w-0 bg-gradient-to-r",
                "transition-all duration-500 ease-out group-hover:w-full",
                colors.gradient
            )} />

            <div className="relative flex items-start justify-between">
                <div className="flex-1">
                    <p className="text-[13px] font-medium text-text-subtle transition-colors group-hover:text-text">
                        {title}
                    </p>
                    <p className="mt-2 text-[28px] font-bold tracking-tight text-text-strong animate-number-count">
                        {value}
                    </p>
                    {(subtitle || change) && (
                        <div className="mt-2 flex items-center gap-2">
                            {change && (
                                <span className={cn(
                                    "inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-xs font-medium",
                                    "transition-transform duration-300 group-hover:scale-105",
                                    changeType === "positive" && "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400",
                                    changeType === "negative" && "bg-rose-100 text-rose-700 dark:bg-rose-950/50 dark:text-rose-400",
                                    changeType === "neutral" && "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                                )}>
                                    {changeType === "positive" && <ArrowUpRight className="h-3 w-3 animate-bounce-subtle" />}
                                    {changeType === "negative" && <ArrowDownRight className="h-3 w-3" />}
                                    {change}
                                </span>
                            )}
                            {subtitle && (
                                <span className="text-xs text-text-subtle">{subtitle}</span>
                            )}
                        </div>
                    )}
                </div>
                <div className={cn(
                    "flex h-12 w-12 items-center justify-center rounded-xl border",
                    "transition-all duration-300 ease-out",
                    "group-hover:scale-110 group-hover:rotate-3 group-hover:shadow-lg",
                    colors.bg,
                    colors.border
                )}>
                    <Icon className={cn(
                        "h-6 w-6 transition-transform duration-300 group-hover:scale-110",
                        colors.icon
                    )} />
                </div>
            </div>
        </div>
    );
}

// 미니 스파크라인 차트 (애니메이션 추가)
function MiniSparkline({ data, color = "blue" }: { data: number[]; color?: string }) {
    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;

    const points = data.map((val, i) => {
        const x = (i / (data.length - 1)) * 100;
        const y = 100 - ((val - min) / range) * 100;
        return `${x},${y}`;
    }).join(" ");

    const strokeColor = color === "emerald" ? "#10b981" : color === "rose" ? "#f43f5e" : "#3b82f6";

    return (
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="h-10 w-full">
            {/* 그라데이션 영역 */}
            <defs>
                <linearGradient id={`gradient-${color}`} x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor={strokeColor} stopOpacity="0.3" />
                    <stop offset="100%" stopColor={strokeColor} stopOpacity="0" />
                </linearGradient>
            </defs>
            {/* 영역 채우기 */}
            <polygon
                fill={`url(#gradient-${color})`}
                points={`0,100 ${points} 100,100`}
                className="opacity-0 animate-fade-in"
                style={{ animationDelay: "0.3s" }}
            />
            {/* 라인 */}
            <polyline
                fill="none"
                stroke={strokeColor}
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={points}
                strokeDasharray="1000"
                className="animate-sparkline-draw"
            />
            {/* 끝점 표시 */}
            <circle
                cx="100"
                cy={100 - ((data[data.length - 1] - min) / range) * 100}
                r="3"
                fill={strokeColor}
                className="opacity-0 animate-scale-in"
                style={{ animationDelay: "1s" }}
            />
        </svg>
    );
}

// 프로그레스 바 차트 (애니메이션 추가)
function ProgressChart({
    data
}: {
    data: { label: string; value: number; maxValue: number; color: string }[]
}) {
    return (
        <div className="space-y-4">
            {data.map((item, idx) => (
                <div
                    key={idx}
                    className="opacity-0 animate-fade-in group"
                    style={{ animationDelay: `${idx * 100}ms` }}
                >
                    <div className="mb-1.5 flex items-center justify-between">
                        <span className="text-sm font-medium text-text transition-colors group-hover:text-text-strong">
                            {item.label}
                        </span>
                        <span className="text-sm font-semibold text-text-strong animate-number-count">
                            {item.value.toLocaleString()}원
                        </span>
                    </div>
                    <div className="h-2.5 w-full overflow-hidden rounded-full bg-surface-secondary/70 transition-all group-hover:h-3">
                        <div
                            className={cn(
                                "h-full rounded-full transition-all duration-1000 ease-out",
                                "bg-gradient-to-r",
                                item.color,
                                "group-hover:brightness-110"
                            )}
                            style={{
                                width: `${(item.value / item.maxValue) * 100}%`,
                                animation: "progress-fill 1s ease-out forwards",
                                animationDelay: `${idx * 100 + 200}ms`
                            }}
                        />
                    </div>
                </div>
            ))}
        </div>
    );
}

// 최근 거래 테이블 (모던 스타일)
function RecentTransactionsTable({
    onViewAll,
    transactions: propTransactions
}: {
    onViewAll?: () => void;
    transactions?: Transaction[];
}) {
    // API 데이터가 있으면 사용, 없으면 기본 데이터
    const transactions = propTransactions && propTransactions.length > 0
        ? propTransactions.map(tx => ({
            id: tx.id,
            date: new Date(tx.date).toLocaleDateString('ko-KR', { month: '2-digit', day: '2-digit' }).replace(/\. /g, '.').replace('.', ''),
            customer: tx.customer,
            type: tx.typeLabel || tx.type,
            amount: tx.amount,
            status: tx.status,
        }))
        : [];

    const typeStyles = {
        "매출": "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400",
        "매입": "bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400",
        "수금": "bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-400",
    };

    const statusStyles: Record<string, { bg: string; text: string; label: string }> = {
        draft: { bg: "bg-amber-50 dark:bg-amber-950/50", text: "text-amber-700 dark:text-amber-400", label: "임시저장" },
        confirmed: { bg: "bg-slate-100 dark:bg-slate-800", text: "text-slate-600 dark:text-slate-400", label: "확정" },
        cancelled: { bg: "bg-rose-50 dark:bg-rose-950/50", text: "text-rose-700 dark:text-rose-400", label: "취소" },
        completed: { bg: "bg-slate-100 dark:bg-slate-800", text: "text-slate-600 dark:text-slate-400", label: "완료" },
        pending: { bg: "bg-amber-50 dark:bg-amber-950/50", text: "text-amber-700 dark:text-amber-400", label: "진행중" },
        overdue: { bg: "bg-rose-50 dark:bg-rose-950/50", text: "text-rose-700 dark:text-rose-400", label: "미수금" },
    };

    return (
        <div className="overflow-hidden rounded-xl border border-border/40">
            <table className="w-full">
                <thead>
                    <tr className="border-b border-border/40 bg-surface-secondary/50">
                        <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-subtle">전표번호</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-subtle">일자</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-subtle">거래처</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-subtle">유형</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-text-subtle">금액</th>
                        <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-text-subtle">상태</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                    {transactions.length === 0 && (
                        <tr>
                            <td colSpan={6} className="px-4 py-12 text-center text-sm text-text-subtle">
                                거래 내역이 없습니다. 매출/매입 전표를 등록해주세요.
                            </td>
                        </tr>
                    )}
                    {transactions.map((tx, idx) => {
                        const status = statusStyles[tx.status] || { bg: "bg-gray-100 dark:bg-gray-800", text: "text-gray-600 dark:text-gray-400", label: tx.status || "알 수 없음" };
                        return (
                            <tr
                                key={tx.id}
                                className={cn(
                                    "group transition-all duration-200",
                                    "hover:bg-surface-secondary/30 hover:shadow-sm",
                                    "opacity-0 animate-fade-in"
                                )}
                                style={{ animationDelay: `${idx * 80}ms` }}
                            >
                                <td className="px-4 py-3">
                                    <span className="font-mono text-sm font-medium text-brand transition-colors group-hover:text-brand-strong">
                                        {tx.id}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-sm text-text-subtle">{tx.date}</td>
                                <td className="px-4 py-3">
                                    <span className="text-sm font-medium text-text transition-transform group-hover:translate-x-1 inline-block">
                                        {tx.customer}
                                    </span>
                                </td>
                                <td className="px-4 py-3">
                                    <span className={cn(
                                        "inline-flex rounded-md px-2 py-1 text-xs font-medium",
                                        "transition-transform duration-200 group-hover:scale-105",
                                        typeStyles[tx.type as keyof typeof typeStyles]
                                    )}>
                                        {tx.type}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-right">
                                    <span className="font-mono text-sm font-semibold text-text-strong">
                                        ₩{tx.amount.toLocaleString()}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-center">
                                    <span className={cn(
                                        "inline-flex rounded-md px-2 py-1 text-xs font-medium",
                                        "transition-all duration-200 group-hover:shadow-sm",
                                        status.bg,
                                        status.text
                                    )}>
                                        {status.label}
                                    </span>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}

// 퀵 액션 버튼 (모던 애니메이션 추가)
function QuickActionButton({
    icon: Icon,
    label,
    onClick,
    variant = "default",
    delay = 0
}: {
    icon: React.ElementType;
    label: string;
    onClick?: () => void;
    variant?: "default" | "primary";
    delay?: number;
}) {
    return (
        <button
            onClick={onClick}
            className={cn(
                "group relative flex flex-col items-center gap-2 rounded-xl p-4",
                "transition-all duration-300 ease-out",
                "hover:scale-105 hover:-translate-y-0.5 hover:shadow-lg",
                "opacity-0 animate-scale-in",
                variant === "primary"
                    ? "bg-brand/10 hover:bg-brand/20 hover:shadow-brand/20"
                    : "bg-surface-secondary/50 hover:bg-surface-secondary hover:shadow-slate-500/10"
            )}
            style={{ animationDelay: `${delay}ms` }}
        >
            {/* 호버 시 배경 글로우 효과 */}
            <div className={cn(
                "absolute inset-0 rounded-xl opacity-0 transition-opacity duration-300",
                "group-hover:opacity-100",
                variant === "primary"
                    ? "bg-gradient-to-br from-brand/5 to-brand/10"
                    : "bg-gradient-to-br from-surface-tertiary/50 to-surface-secondary/50"
            )} />

            <div className={cn(
                "relative flex h-10 w-10 items-center justify-center rounded-lg",
                "transition-all duration-300 ease-out",
                "group-hover:scale-110 group-hover:rotate-6 group-hover:shadow-lg",
                variant === "primary"
                    ? "bg-brand text-white group-hover:shadow-brand/30"
                    : "bg-surface text-text-subtle group-hover:text-text group-hover:shadow-slate-500/20"
            )}>
                <Icon className="h-5 w-5 transition-transform duration-300 group-hover:scale-110" />
            </div>
            <span className={cn(
                "relative text-xs font-medium transition-all duration-300",
                "group-hover:font-semibold",
                variant === "primary" ? "text-brand" : "text-text-subtle group-hover:text-text"
            )}>
                {label}
            </span>
        </button>
    );
}

// 일정 아이템 (모던 애니메이션 추가)
function ScheduleItem({
    time,
    title,
    type,
    delay = 0,
    onClick,
}: {
    time: string;
    title: string;
    type: "delivery" | "meeting" | "task";
    delay?: number;
    onClick?: () => void;
}) {
    const typeColors = {
        delivery: { bg: "bg-blue-500", glow: "shadow-blue-500/50" },
        meeting: { bg: "bg-emerald-500", glow: "shadow-emerald-500/50" },
        task: { bg: "bg-amber-500", glow: "shadow-amber-500/50" },
    };

    const colors = typeColors[type];

    return (
        <div
            className={cn(
                "group flex items-center gap-3 rounded-lg p-3",
                "bg-surface-secondary/50 transition-all duration-300 ease-out",
                "hover:bg-surface-secondary hover:shadow-md hover:-translate-x-1",
                "cursor-pointer opacity-0 animate-slide-in-right"
            )}
            style={{ animationDelay: `${delay}ms` }}
            onClick={onClick}
        >
            {/* 상태 인디케이터 - 펄스 애니메이션 */}
            <div className="relative">
                <div className={cn(
                    "h-2.5 w-2.5 rounded-full transition-all duration-300",
                    "group-hover:scale-125",
                    colors.bg
                )} />
                <div className={cn(
                    "absolute inset-0 h-2.5 w-2.5 rounded-full opacity-0",
                    "group-hover:opacity-75 group-hover:animate-ping",
                    colors.bg
                )} />
            </div>
            <div className="flex-1 min-w-0">
                <p className="truncate text-sm font-medium text-text transition-colors group-hover:text-text-strong">
                    {title}
                </p>
                <p className="text-xs text-text-subtle transition-colors group-hover:text-text">
                    {time}
                </p>
            </div>
            <ChevronRight className={cn(
                "h-4 w-4 text-text-subtle transition-all duration-300",
                "group-hover:text-text group-hover:translate-x-1"
            )} />
        </div>
    );
}

// 미수금 아이템 (모던 애니메이션 추가)
function ReceivableItem({
    period,
    amount,
    status,
    delay = 0,
    onClick,
}: {
    period: string;
    amount: number;
    status: "normal" | "warning" | "danger";
    delay?: number;
    onClick?: () => void;
}) {
    const statusStyles = {
        normal: {
            text: "text-text group-hover:text-text-strong",
            bg: "group-hover:bg-slate-50 dark:group-hover:bg-slate-900/30"
        },
        warning: {
            text: "text-amber-600 dark:text-amber-400",
            bg: "group-hover:bg-amber-50/50 dark:group-hover:bg-amber-900/20"
        },
        danger: {
            text: "text-rose-600 dark:text-rose-400",
            bg: "group-hover:bg-rose-50/50 dark:group-hover:bg-rose-900/20"
        },
    };

    const styles = statusStyles[status];

    return (
        <div
            className={cn(
                "group flex items-center justify-between py-2.5 px-2 -mx-2 rounded-lg",
                "transition-all duration-300 ease-out cursor-pointer",
                "opacity-0 animate-fade-in",
                styles.bg
            )}
            style={{ animationDelay: `${delay}ms` }}
            onClick={onClick}
        >
            <span className="text-sm text-text-subtle transition-colors group-hover:text-text">
                {period}
            </span>
            <div className="flex items-center gap-2">
                {status === "danger" && (
                    <span className="flex h-2 w-2">
                        <span className="relative inline-flex h-2 w-2 rounded-full bg-rose-500">
                            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-rose-400 opacity-75" />
                        </span>
                    </span>
                )}
                <span className={cn(
                    "font-mono text-sm font-semibold transition-all duration-300",
                    "group-hover:scale-105 group-hover:font-bold",
                    styles.text
                )}>
                    ₩{amount.toLocaleString()}
                </span>
            </div>
        </div>
    );
}

// 거래 타입
interface Transaction {
    id: string;
    date: string;
    customer: string;
    type: string;
    typeLabel?: string; // API에서 선택적으로 반환될 수 있음
    amount: number;
    status: "completed" | "pending" | "overdue";
}

// 일정 타입
interface Schedule {
    id: string;
    time: string;
    title: string;
    type: "delivery" | "meeting" | "task";
}

// API 응답 타입
interface ERPStatsResponse {
    success: boolean;
    stats: {
        monthlySales: number;
        monthlyPurchases: number;
        receivables: number;
        activeCustomers: number;
        salesChange: number;
        purchasesChange: number;
        newCustomers: number;
        overdueCount: number;
    };
    monthlyBreakdown: {
        sales: number;
        purchases: number;
        collections: number;
        payments: number;
        netProfit: number;
    };
    receivablesBreakdown: {
        within30Days: number;
        days30To60: number;
        over60Days: number;
        total: number;
    };
    todaySchedules: Schedule[];
    monthlyTrend: number[];
}

interface ERPDashboardProps {
    onOpenWindow?: (type: string, title: string) => void;
}

// 스켈레톤 로딩 컴포넌트
function SkeletonCard({ className }: { className?: string }) {
    return (
        <div className={cn("animate-pulse rounded-2xl border border-border/40 bg-surface p-5 metric-card-depth", className)}>
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <div className="h-4 w-20 rounded bg-surface-secondary" />
                    <div className="mt-3 h-8 w-32 rounded bg-surface-secondary" />
                    <div className="mt-3 h-4 w-24 rounded bg-surface-secondary" />
                </div>
                <div className="h-12 w-12 rounded-xl bg-surface-secondary" />
            </div>
        </div>
    );
}

function SkeletonTable() {
    return (
        <div className="animate-pulse overflow-hidden rounded-xl border border-border/40">
            <div className="border-b border-border/40 bg-surface-secondary/50 px-4 py-3">
                <div className="flex gap-4">
                    {[80, 60, 100, 60, 80, 60].map((w, i) => (
                        <div key={i} className="h-3 rounded bg-surface-secondary" style={{ width: w }} />
                    ))}
                </div>
            </div>
            {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="border-b border-border/40 px-4 py-3 last:border-0">
                    <div className="flex gap-4">
                        {[80, 60, 100, 60, 80, 60].map((w, j) => (
                            <div key={j} className="h-4 rounded bg-surface-secondary" style={{ width: w }} />
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}

function SkeletonBlock({ className }: { className?: string }) {
    return (
        <div className={cn("animate-pulse rounded-2xl border border-border/40 bg-surface p-5 metric-card-depth", className)}>
            <div className="mb-4 flex items-center justify-between">
                <div className="h-5 w-24 rounded bg-surface-secondary" />
                <div className="h-4 w-12 rounded bg-surface-secondary" />
            </div>
            <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                    <div key={i} className="h-12 rounded-lg bg-surface-secondary" />
                ))}
            </div>
        </div>
    );
}

export function ERPDashboard({ onOpenWindow }: ERPDashboardProps) {
    const [stats, setStats] = useState<ERPStatsResponse["stats"] | null>(null);
    const [monthlyBreakdown, setMonthlyBreakdown] = useState<ERPStatsResponse["monthlyBreakdown"] | null>(null);
    const [receivablesBreakdown, setReceivablesBreakdown] = useState<ERPStatsResponse["receivablesBreakdown"] | null>(null);
    const [schedules, setSchedules] = useState<Schedule[]>([]);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [monthlyTrend, setMonthlyTrend] = useState<number[]>([]);
    const [loading, setLoading] = useState(true);

    const handleOpenWindow = (type: string, title: string) => {
        if (onOpenWindow) {
            onOpenWindow(type, title);
        }
    };

    // API 데이터 로드
    const fetchData = useCallback(async () => {
        try {
            // 대시보드 통계 API 호출 (어댑터 경로 사용)
            const statsData = await api.erp.dashboard.stats() as unknown as ERPStatsResponse;
            if (statsData.success) {
                setStats(statsData.stats);
                setMonthlyBreakdown(statsData.monthlyBreakdown);
                setReceivablesBreakdown(statsData.receivablesBreakdown);
                setSchedules(statsData.todaySchedules || []);
                setMonthlyTrend(statsData.monthlyTrend || []);
            }

            // 최근 거래 목록 (매출전표 최근 5건)
            try {
                const salesData = await api.erp.sales.list({ limit: 5 });
                const salesItems = salesData.items || [];
                const mapped = salesItems.map((s: any) => ({
                    id: s.id,
                    date: s.sale_date,
                    type: "매출",
                    customer: s.customer?.name || "",
                    amount: s.total_amount,
                    status: s.status,
                }));
                setTransactions(mapped);
            } catch {
                // 매출 조회 실패는 무시
            }
        } catch (error) {
            console.error("Failed to fetch ERP data:", error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // 월별 데이터 (API 데이터만 사용, 없으면 0)
    const mbSales = monthlyBreakdown?.sales ?? 0;
    const mbPurchases = monthlyBreakdown?.purchases ?? 0;
    const mbCollections = monthlyBreakdown?.collections ?? 0;
    const mbPayments = monthlyBreakdown?.payments ?? 0;
    const mbMax = Math.max(mbSales, mbPurchases, mbCollections, mbPayments, 1);
    const monthlyData = [
        { label: "매출", value: mbSales, maxValue: mbMax, color: "bg-emerald-500" },
        { label: "매입", value: mbPurchases, maxValue: mbMax, color: "bg-amber-500" },
        { label: "수금", value: mbCollections, maxValue: mbMax, color: "bg-blue-500" },
        { label: "지급", value: mbPayments, maxValue: mbMax, color: "bg-rose-500" },
    ];

    // 순이익 계산
    const netProfit = monthlyBreakdown?.netProfit ?? 0;

    // 현재 날짜
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1;

    // 로딩 상태 UI
    if (loading) {
        return (
            <div className="space-y-6">
                {/* 상단 메트릭 카드 스켈레톤 */}
                <div className="grid grid-cols-4 gap-4">
                    <SkeletonCard />
                    <SkeletonCard />
                    <SkeletonCard />
                    <SkeletonCard />
                </div>

                {/* 중앙 영역 스켈레톤 */}
                <div className="grid grid-cols-12 gap-4">
                    <SkeletonBlock className="col-span-4" />
                    <div className="col-span-8 rounded-2xl border border-border/40 bg-surface p-5 metric-card-depth">
                        <div className="mb-5 flex items-center justify-between">
                            <div className="h-5 w-24 animate-pulse rounded bg-surface-secondary" />
                            <div className="h-4 w-16 animate-pulse rounded bg-surface-secondary" />
                        </div>
                        <SkeletonTable />
                    </div>
                </div>

                {/* 하단 영역 스켈레톤 */}
                <div className="grid grid-cols-12 gap-4">
                    <SkeletonBlock className="col-span-3" />
                    <SkeletonBlock className="col-span-3" />
                    <SkeletonBlock className="col-span-3" />
                    <SkeletonBlock className="col-span-3" />
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* 상단 메트릭 카드 - Stagger 애니메이션 */}
            <div className="grid grid-cols-4 gap-4">
                <MetricCard
                    title="이번 달 매출"
                    value={`₩${(stats?.monthlySales ?? 0).toLocaleString()}`}
                    change={stats?.salesChange != null ? `${stats.salesChange > 0 ? '+' : ''}${stats.salesChange}%` : undefined}
                    changeType={stats?.salesChange != null ? (stats.salesChange >= 0 ? "positive" : "negative") : undefined}
                    subtitle={stats?.salesChange != null ? "전월 대비" : "데이터 없음"}
                    icon={Wallet}
                    accentColor="emerald"
                    delay={0}
                    onClick={() => handleOpenWindow("sales-statement", "매출현황")}
                />
                <MetricCard
                    title="이번 달 매입"
                    value={`₩${(stats?.monthlyPurchases ?? 0).toLocaleString()}`}
                    change={stats?.purchasesChange != null ? `${stats.purchasesChange > 0 ? '+' : ''}${stats.purchasesChange}%` : undefined}
                    changeType={stats?.purchasesChange != null ? (stats.purchasesChange >= 0 ? "positive" : "negative") : undefined}
                    subtitle={stats?.purchasesChange != null ? "전월 대비" : "데이터 없음"}
                    icon={Receipt}
                    accentColor="amber"
                    delay={100}
                    onClick={() => handleOpenWindow("purchase-statement", "매입현황")}
                />
                <MetricCard
                    title="미수금 잔액"
                    value={`₩${(stats?.receivables ?? 0).toLocaleString()}`}
                    subtitle={stats?.overdueCount ? `${stats.overdueCount}건 연체` : "연체 없음"}
                    icon={CreditCard}
                    accentColor="rose"
                    delay={200}
                    onClick={() => handleOpenWindow("receivable-list", "미수금현황")}
                />
                <MetricCard
                    title="활성 거래처"
                    value={(stats?.activeCustomers ?? 0).toString()}
                    change={stats?.newCustomers ? `+${stats.newCustomers}` : undefined}
                    changeType={stats?.newCustomers ? "positive" : undefined}
                    subtitle={stats?.newCustomers ? "이번 달 신규" : "등록된 거래처 없음"}
                    icon={Users}
                    accentColor="blue"
                    delay={300}
                    onClick={() => handleOpenWindow("customer", "거래처등록")}
                />
            </div>

            {/* 중앙 영역: 차트 + 테이블 */}
            <div className="grid grid-cols-12 gap-4">
                {/* 월별 현황 차트 */}
                <div
                    className="col-span-4 rounded-2xl border border-border/40 bg-surface p-5 metric-card-depth opacity-0 animate-fade-in-up cursor-pointer hover:shadow-lg hover:border-brand/20 transition-all duration-300"
                    style={{ animationDelay: "400ms" }}
                    onClick={() => handleOpenWindow("monthly-chart", "월별현황")}
                >
                    <div className="mb-5 flex items-center justify-between">
                        <div>
                            <h3 className="text-base font-semibold text-text-strong">월별 현황</h3>
                            <p className="text-xs text-text-subtle">{currentYear}년 {currentMonth}월</p>
                        </div>
                        <button className="rounded-lg p-1.5 text-text-subtle transition-all duration-200 hover:bg-surface-secondary hover:text-text hover:rotate-90">
                            <MoreHorizontal className="h-5 w-5" />
                        </button>
                    </div>
                    <ProgressChart data={monthlyData} />

                    {/* 순이익 표시 */}
                    <div className="mt-5 rounded-xl bg-surface-secondary/50 p-4">
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-text-subtle">순이익</span>
                            <span className={cn(
                                "text-lg font-bold",
                                netProfit >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
                            )}>
                                {netProfit >= 0 ? '+' : ''}₩{netProfit.toLocaleString()}
                            </span>
                        </div>
                        {monthlyTrend.length > 1 && (
                            <div className="mt-2">
                                <MiniSparkline
                                    data={monthlyTrend}
                                    color={netProfit >= 0 ? "emerald" : "rose"}
                                />
                            </div>
                        )}
                    </div>
                </div>

                {/* 최근 거래 */}
                <div
                    className="col-span-8 rounded-2xl border border-border/40 bg-surface p-5 metric-card-depth opacity-0 animate-fade-in-up"
                    style={{ animationDelay: "500ms" }}
                >
                    <div className="mb-5 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <h3 className="text-base font-semibold text-text-strong">최근 거래</h3>
                            {transactions.length > 0 && (
                                <span className="rounded-full bg-brand/10 px-2.5 py-0.5 text-xs font-medium text-brand">
                                    {transactions.length}건
                                </span>
                            )}
                        </div>
                        <button
                            onClick={() => handleOpenWindow("daily-report", "일일거래현황")}
                            className="group flex items-center gap-1 text-sm font-medium text-brand transition-all duration-200 hover:text-brand-dark hover:gap-2"
                        >
                            전체보기
                            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                        </button>
                    </div>
                    <RecentTransactionsTable
                        transactions={transactions}
                        onViewAll={() => handleOpenWindow("daily-report", "일일거래현황")}
                    />
                </div>
            </div>

            {/* 하단 영역 */}
            <div className="grid grid-cols-12 gap-4">
                {/* 오늘 일정 */}
                <div
                    className="col-span-3 rounded-2xl border border-border/40 bg-surface p-5 metric-card-depth opacity-0 animate-fade-in-up hover:shadow-lg hover:border-brand/20 transition-all duration-300"
                    style={{ animationDelay: "600ms" }}
                >
                    <div className="mb-4 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Calendar className="h-5 w-5 text-brand" />
                            <h3 className="text-base font-semibold text-text-strong">오늘 일정</h3>
                        </div>
                        {schedules.length > 0 && (
                            <span className="rounded-full bg-brand/10 px-2 py-0.5 text-xs font-medium text-brand">{schedules.length}건</span>
                        )}
                    </div>
                    <div className="space-y-2">
                        {schedules.length > 0 ? (
                            schedules.map((schedule, idx) => (
                                <ScheduleItem
                                    key={schedule.id}
                                    time={schedule.time}
                                    title={schedule.title}
                                    type={schedule.type}
                                    delay={idx * 100}
                                    onClick={() => handleOpenWindow("daily-report", "오늘일정")}
                                />
                            ))
                        ) : (
                            <div className="flex flex-col items-center justify-center py-6 text-center">
                                <Calendar className="h-8 w-8 text-text-subtle/40 mb-2" />
                                <p className="text-sm text-text-subtle">오늘 일정이 없습니다</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* 미수금 현황 */}
                <div
                    className="col-span-3 rounded-2xl border border-border/40 bg-surface p-5 metric-card-depth opacity-0 animate-fade-in-up hover:shadow-lg hover:border-rose-500/20 transition-all duration-300"
                    style={{ animationDelay: "700ms" }}
                >
                    <div className="mb-4 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <div className="relative">
                                <AlertCircle className="h-5 w-5 text-rose-500" />
                                <span className="absolute -right-1 -top-1 flex h-2 w-2">
                                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-rose-400 opacity-75" />
                                    <span className="relative inline-flex h-2 w-2 rounded-full bg-rose-500" />
                                </span>
                            </div>
                            <h3 className="text-base font-semibold text-text-strong">미수금 현황</h3>
                        </div>
                        <button
                            onClick={() => handleOpenWindow("receivable-list", "미수금상세")}
                            className="text-xs font-medium text-brand hover:underline transition-colors"
                        >
                            상세
                        </button>
                    </div>
                    <div className="divide-y divide-border/40">
                        <ReceivableItem
                            period="30일 이내"
                            amount={receivablesBreakdown?.within30Days ?? 0}
                            status="normal"
                            delay={0}
                            onClick={() => handleOpenWindow("receivable-list", "미수금현황")}
                        />
                        <ReceivableItem
                            period="30~60일"
                            amount={receivablesBreakdown?.days30To60 ?? 0}
                            status="warning"
                            delay={100}
                            onClick={() => handleOpenWindow("receivable-list", "미수금현황")}
                        />
                        <ReceivableItem
                            period="60일 초과"
                            amount={receivablesBreakdown?.over60Days ?? 0}
                            status="danger"
                            delay={200}
                            onClick={() => handleOpenWindow("receivable-list", "미수금현황")}
                        />
                    </div>
                    <div className="mt-4 flex items-center justify-between rounded-lg bg-gradient-to-r from-rose-50 to-rose-100/50 p-3 dark:from-rose-950/30 dark:to-rose-900/20">
                        <span className="text-sm font-medium text-rose-700 dark:text-rose-400">총 미수금</span>
                        <span className="font-mono text-sm font-bold text-rose-700 dark:text-rose-400">
                            ₩{(receivablesBreakdown?.total ?? 0).toLocaleString()}
                        </span>
                    </div>
                </div>

                {/* 빠른 실행 */}
                <div
                    className="col-span-3 rounded-2xl border border-border/40 bg-surface p-5 metric-card-depth opacity-0 animate-fade-in-up hover:shadow-lg hover:border-brand/20 transition-all duration-300"
                    style={{ animationDelay: "900ms" }}
                >
                    <div className="mb-4 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Activity className="h-5 w-5 text-brand animate-pulse" />
                            <h3 className="text-base font-semibold text-text-strong">빠른 실행</h3>
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                        <QuickActionButton
                            icon={FileText}
                            label="매출전표"
                            onClick={() => handleOpenWindow("sales-voucher", "매출전표")}
                            variant="primary"
                            delay={0}
                        />
                        <QuickActionButton
                            icon={Receipt}
                            label="매입전표"
                            onClick={() => handleOpenWindow("purchase-voucher", "매입전표")}
                            delay={100}
                        />
                        <QuickActionButton
                            icon={Users}
                            label="거래처"
                            onClick={() => handleOpenWindow("customer", "거래처등록")}
                            delay={200}
                        />
                        <QuickActionButton
                            icon={FileText}
                            label="세금계산서"
                            onClick={() => handleOpenWindow("tax-invoice", "전자세금계산서")}
                            delay={300}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}
