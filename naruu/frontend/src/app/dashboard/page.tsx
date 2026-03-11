"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from "recharts";

interface KPI {
  monthly_revenue: number;
  prev_monthly_revenue: number;
  revenue_change_pct: number;
  new_customers_this_month: number;
  prev_new_customers: number;
  customer_change: number;
  reservations_this_month: number;
  prev_reservations: number;
  reservation_change: number;
  content_published_this_month: number;
  prev_content_published: number;
  content_change: number;
  total_customers: number;
  active_packages: number;
  active_routes: number;
  pending_reservations: number;
  unread_messages: number;
  avg_review_score: number | null;
}

interface ChartData {
  revenue_trend: { month: string; revenue: number }[];
  reservation_by_type: { type: string; count: number }[];
  customer_sources: { source: string; count: number }[];
  recent_reservations: {
    id: number;
    customer_id: number;
    type: string;
    status: string;
    date: string;
  }[];
  recent_reviews: {
    id: number;
    platform: string;
    sentiment_score: number;
    created_at: string;
  }[];
}

const PIE_COLORS = ["#3b82f6", "#ef4444", "#f59e0b", "#10b981", "#8b5cf6"];

const TYPE_LABELS: Record<string, string> = {
  medical: "의료",
  tourism: "관광",
  restaurant: "식당",
  goods: "굿즈",
};

const STATUS_LABELS: Record<string, string> = {
  pending: "대기",
  confirmed: "확정",
  completed: "완료",
  cancelled: "취소",
};

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const [kpi, setKpi] = useState<KPI | null>(null);
  const [charts, setCharts] = useState<ChartData | null>(null);
  const [aiInsights, setAiInsights] = useState("");
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [kpiData, chartData] = await Promise.all([
          api.get<KPI>("/dashboard/kpi"),
          api.get<ChartData>("/dashboard/charts"),
        ]);
        setKpi(kpiData);
        setCharts(chartData);
      } catch (err) {
        console.error("Dashboard load failed:", err);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const loadInsights = async () => {
    setInsightsLoading(true);
    try {
      const data = await api.get<{ insights: string }>("/dashboard/ai-insights");
      setAiInsights(data.insights);
    } catch {
      setAiInsights("AI 인사이트를 불러올 수 없습니다.");
    } finally {
      setInsightsLoading(false);
    }
  };

  const formatChange = (val: number, suffix = "") => {
    if (val > 0) return `+${val}${suffix}`;
    if (val < 0) return `${val}${suffix}`;
    return `0${suffix}`;
  };

  if (loading) {
    return (
      <AppShell>
        <p className="text-gray-400">대시보드 로딩 중...</p>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">대시보드</h2>
          <p className="text-sm text-gray-500 mt-1">
            환영합니다, {user?.name_ko || "관리자"}님
          </p>
        </div>
        <button
          onClick={loadInsights}
          disabled={insightsLoading}
          className="px-4 py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700 text-sm font-medium disabled:opacity-50 transition"
        >
          {insightsLoading ? "AI 분석 중..." : "AI 인사이트"}
        </button>
      </div>

      {/* AI Insights */}
      {aiInsights && (
        <div className="mb-6 bg-gradient-to-r from-violet-50 to-blue-50 rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-violet-700 text-sm mb-2">AI 비즈니스 인사이트</h3>
          <p className="text-sm text-gray-700 whitespace-pre-wrap">{aiInsights}</p>
        </div>
      )}

      {/* KPI Cards — Row 1 */}
      {kpi && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <KPICard
            title="이번 달 매출"
            value={`¥${kpi.monthly_revenue.toLocaleString()}`}
            change={formatChange(kpi.revenue_change_pct, "%")}
            positive={kpi.revenue_change_pct >= 0}
            icon="💰"
          />
          <KPICard
            title="신규 고객"
            value={`${kpi.new_customers_this_month}명`}
            change={formatChange(kpi.customer_change)}
            positive={kpi.customer_change >= 0}
            icon="👥"
          />
          <KPICard
            title="예약 건수"
            value={`${kpi.reservations_this_month}건`}
            change={formatChange(kpi.reservation_change)}
            positive={kpi.reservation_change >= 0}
            icon="📅"
          />
          <KPICard
            title="콘텐츠 게시"
            value={`${kpi.content_published_this_month}건`}
            change={formatChange(kpi.content_change)}
            positive={kpi.content_change >= 0}
            icon="🎬"
          />
        </div>
      )}

      {/* KPI Cards — Row 2 */}
      {kpi && (
        <div className="grid grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
          <MiniKPI label="총 고객" value={kpi.total_customers} />
          <MiniKPI label="활성 패키지" value={kpi.active_packages} />
          <MiniKPI label="관광 루트" value={kpi.active_routes} />
          <MiniKPI label="대기 예약" value={kpi.pending_reservations} highlight />
          <MiniKPI label="새 메시지" value={kpi.unread_messages} highlight />
          <MiniKPI
            label="리뷰 평균"
            value={kpi.avg_review_score ? `${kpi.avg_review_score}점` : "-"}
          />
        </div>
      )}

      {/* Charts Row */}
      {charts && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Revenue Trend */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-4">월별 매출 추이</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={charts.revenue_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(v) => {
                    const parts = v.split("-");
                    return `${parseInt(parts[1])}월`;
                  }}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickFormatter={(v) => `¥${(v / 10000).toFixed(0)}万`}
                />
                <Tooltip
                  formatter={(value: number) => [`¥${value.toLocaleString()}`, "매출"]}
                  labelFormatter={(label) => {
                    const [y, m] = label.split("-");
                    return `${y}년 ${parseInt(m)}월`;
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="revenue"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Reservation by Type */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-4">예약 유형 분포</h3>
            {charts.reservation_by_type.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={charts.reservation_by_type}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={5}
                    dataKey="count"
                    nameKey="type"
                    label={({ type, count }: { type: string; count: number }) =>
                      `${TYPE_LABELS[type] || type} ${count}`
                    }
                  >
                    {charts.reservation_by_type.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number, name: string) => [
                      `${value}건`,
                      TYPE_LABELS[name] || name,
                    ]}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[250px] text-gray-400 text-sm">
                예약 데이터가 없습니다
              </div>
            )}
          </div>
        </div>
      )}

      {/* Bottom Row */}
      {charts && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Customer Sources */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-4">고객 국적 분포</h3>
            {charts.customer_sources.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={charts.customer_sources} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis type="number" tick={{ fontSize: 12 }} />
                  <YAxis
                    type="category"
                    dataKey="source"
                    tick={{ fontSize: 12 }}
                    width={60}
                  />
                  <Tooltip formatter={(value: number) => [`${value}명`, "고객"]} />
                  <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-gray-400 text-center py-8">데이터 없음</p>
            )}
          </div>

          {/* Recent Reservations */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-4">최근 예약</h3>
            {charts.recent_reservations.length > 0 ? (
              <div className="space-y-3">
                {charts.recent_reservations.map((r) => (
                  <div
                    key={r.id}
                    className="flex items-center justify-between text-sm"
                  >
                    <div>
                      <span className="font-medium text-gray-800">
                        {TYPE_LABELS[r.type] || r.type}
                      </span>
                      <span className="text-gray-400 ml-2">#{r.customer_id}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-xs ${
                          r.status === "confirmed"
                            ? "bg-green-100 text-green-700"
                            : r.status === "pending"
                            ? "bg-amber-100 text-amber-700"
                            : r.status === "completed"
                            ? "bg-blue-100 text-blue-700"
                            : "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {STATUS_LABELS[r.status] || r.status}
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(r.date).toLocaleDateString("ko-KR")}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400 text-center py-8">예약 없음</p>
            )}
          </div>

          {/* Recent Reviews */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-4">최근 리뷰</h3>
            {charts.recent_reviews.length > 0 ? (
              <div className="space-y-3">
                {charts.recent_reviews.map((r) => (
                  <div
                    key={r.id}
                    className="flex items-center justify-between text-sm"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-800">{r.platform}</span>
                      {r.sentiment_score != null && (
                        <span
                          className={`text-xs ${
                            r.sentiment_score >= 0.7
                              ? "text-green-600"
                              : r.sentiment_score >= 0.4
                              ? "text-amber-600"
                              : "text-red-600"
                          }`}
                        >
                          {(r.sentiment_score * 100).toFixed(0)}점
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-gray-400">
                      {new Date(r.created_at).toLocaleDateString("ko-KR")}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400 text-center py-8">리뷰 없음</p>
            )}
          </div>
        </div>
      )}
    </AppShell>
  );
}

function KPICard({
  title,
  value,
  change,
  positive,
  icon,
}: {
  title: string;
  value: string;
  change: string;
  positive: boolean;
  icon: string;
}) {
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm text-gray-500">{title}</p>
        <span className="text-xl">{icon}</span>
      </div>
      <p className="text-2xl font-bold text-gray-800">{value}</p>
      <p
        className={`text-xs mt-1 font-medium ${
          positive ? "text-green-600" : "text-red-500"
        }`}
      >
        {change} vs 전월
      </p>
    </div>
  );
}

function MiniKPI({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: number | string;
  highlight?: boolean;
}) {
  return (
    <div
      className={`rounded-xl p-3 shadow-sm text-center ${
        highlight
          ? "bg-amber-50 border border-amber-200"
          : "bg-white border border-gray-100"
      }`}
    >
      <p
        className={`text-lg font-bold ${
          highlight ? "text-amber-700" : "text-gray-800"
        }`}
      >
        {value}
      </p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  );
}
