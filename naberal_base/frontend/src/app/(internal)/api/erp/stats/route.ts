import { NextRequest, NextResponse } from "next/server";

// ERP 통계 데이터 타입
interface ERPStats {
    monthlySales: number;
    monthlyPurchases: number;
    receivables: number;
    activeCustomers: number;
    salesChange: number;
    purchasesChange: number;
    newCustomers: number;
    overdueCount: number;
}

// ERP 통계 API
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const year = searchParams.get("year") || new Date().getFullYear().toString();
        const month = searchParams.get("month") || (new Date().getMonth() + 1).toString();

        // 실제 환경에서는 DB에서 조회
        // 시뮬레이션 데이터 생성 (월별로 다르게)
        const monthNum = parseInt(month);
        const baseMultiplier = 1 + (monthNum * 0.05);

        const stats: ERPStats = {
            monthlySales: Math.round(40000000 * baseMultiplier),
            monthlyPurchases: Math.round(25000000 * baseMultiplier),
            receivables: 12500000 + (monthNum * 500000),
            activeCustomers: 150 + monthNum,
            salesChange: 12.5 - (monthNum % 5),
            purchasesChange: -5.2 + (monthNum % 3),
            newCustomers: 3 + (monthNum % 5),
            overdueCount: 3,
        };

        // 월별 세부 현황
        const monthlyBreakdown = {
            sales: stats.monthlySales,
            purchases: stats.monthlyPurchases,
            collections: Math.round(stats.monthlySales * 0.85),
            payments: Math.round(stats.monthlyPurchases * 0.8),
            netProfit: stats.monthlySales - stats.monthlyPurchases,
        };

        // 미수금 세부 현황
        const receivablesBreakdown = {
            within30Days: Math.round(stats.receivables * 0.42),
            days30To60: Math.round(stats.receivables * 0.38),
            over60Days: Math.round(stats.receivables * 0.20),
            total: stats.receivables,
        };

        // 재고 현황
        const inventoryStats = {
            totalItems: 1247,
            lowStock: 23,
            overStock: 8,
            normal: 1216,
        };

        // 오늘 일정 (실제 환경에서는 DB에서)
        const todaySchedules = [
            { id: "s1", time: "09:00", title: "동양기전 출고", type: "delivery" },
            { id: "s2", time: "14:00", title: "삼성전자 미팅", type: "meeting" },
            { id: "s3", time: "17:00", title: "월말 정산 마감", type: "task" },
        ];

        // 월간 추이 데이터 (스파크라인용)
        const monthlyTrend = Array.from({ length: 12 }, (_, i) =>
            Math.round(35 + Math.random() * 30)
        );

        return NextResponse.json({
            success: true,
            stats,
            monthlyBreakdown,
            receivablesBreakdown,
            inventoryStats,
            todaySchedules,
            monthlyTrend,
            period: { year, month },
        });
    } catch (error) {
        console.error("ERP Stats GET error:", error);
        return NextResponse.json(
            { success: false, error: "Failed to fetch ERP stats" },
            { status: 500 }
        );
    }
}
