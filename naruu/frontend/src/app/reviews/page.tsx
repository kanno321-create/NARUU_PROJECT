"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { Review, ReviewListResponse, ReviewStats, ReviewPlatform } from "@/lib/types";
import { PLATFORM_LABELS, PLATFORM_COLORS, SENTIMENT_COLORS } from "@/lib/constants";
import Pagination from "@/components/ui/pagination";
import LoadingSpinner from "@/components/ui/loading-spinner";
import ErrorBanner from "@/components/ui/error-banner";
import SearchFilter from "@/components/ui/search-filter";

function sentimentLabel(score: number | null): { text: string; color: string } {
  if (score === null) return { text: "미분석", color: "text-gray-400" };
  if (score >= 0.7) return { text: "긍정", color: "text-green-600" };
  if (score >= 0.4) return { text: "중립", color: "text-yellow-600" };
  return { text: "부정", color: "text-red-600" };
}

function sentimentBar(score: number | null) {
  if (score === null) return null;
  const pct = Math.round(score * 100);
  const color = score >= 0.7 ? "bg-green-500" : score >= 0.4 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={`감성점수 ${pct}%`}>
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-500">{score.toFixed(2)}</span>
    </div>
  );
}

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [platform, setPlatform] = useState<string>("");
  const [hasResponse, setHasResponse] = useState<string>("");
  const [search, setSearch] = useState("");

  const perPage = 20;

  useEffect(() => {
    loadStats();
  }, []);

  useEffect(() => {
    loadReviews();
  }, [page, platform, hasResponse, search]);

  async function loadStats() {
    try {
      const data = await api.get<ReviewStats>("/reviews/stats");
      setStats(data);
    } catch {
      setError("리뷰 통계를 불러오는데 실패했습니다.");
    }
  }

  async function loadReviews() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("per_page", String(perPage));
      if (platform) params.set("platform", platform);
      if (hasResponse === "yes") params.set("has_response", "true");
      if (hasResponse === "no") params.set("has_response", "false");
      if (search) params.set("search", search);

      const data = await api.get<ReviewListResponse>(`/reviews?${params}`);
      setReviews(data.items);
      setTotal(data.total);
      setError(null);
    } catch {
      setError("리뷰를 불러오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  const totalPages = Math.ceil(total / perPage);

  const sentimentChartData = stats
    ? [
        { name: "긍정", value: stats.sentiment_distribution.positive },
        { name: "중립", value: stats.sentiment_distribution.neutral },
        { name: "부정", value: stats.sentiment_distribution.negative },
      ]
    : [];

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">리뷰 관리</h2>
        <Link
          href="/reviews/new"
          className="px-4 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 transition text-sm font-medium"
        >
          + 리뷰 등록
        </Link>
      </div>

      <ErrorBanner message={error} />

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <p className="text-xs text-gray-500 mb-1">전체 리뷰</p>
            <p className="text-2xl font-bold text-gray-800">{stats.total}</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <p className="text-xs text-gray-500 mb-1">평균 평점</p>
            <p className="text-2xl font-bold text-yellow-600">
              {stats.avg_rating ? `${stats.avg_rating.toFixed(1)} ★` : "-"}
            </p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <p className="text-xs text-gray-500 mb-1">평균 감성점수</p>
            <p className="text-2xl font-bold text-blue-600">
              {stats.avg_sentiment ? stats.avg_sentiment.toFixed(3) : "-"}
            </p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <p className="text-xs text-gray-500 mb-1">미응답 리뷰</p>
            <p className="text-2xl font-bold text-red-600">{stats.awaiting_response}</p>
          </div>
        </div>
      )}

      {/* Charts Row */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {/* Sentiment Distribution Pie */}
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">감성 분포</h3>
            {sentimentChartData.some((d) => d.value > 0) ? (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={sentimentChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    dataKey="value"
                    label={(props: any) => `${props.name} ${props.value}`}
                  >
                    {sentimentChartData.map((_, i) => (
                      <Cell key={i} fill={SENTIMENT_COLORS[i]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-400 text-sm py-8 text-center">데이터 없음</p>
            )}
          </div>

          {/* Platform Breakdown */}
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">플랫폼별 현황</h3>
            {stats.by_platform.length > 0 ? (
              <div className="space-y-3">
                {stats.by_platform.map((p) => (
                  <div key={p.platform} className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">{PLATFORM_LABELS[p.platform as ReviewPlatform] || p.platform}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium">{p.count}건</span>
                      <span className="text-xs text-gray-400">
                        감성 {p.avg_sentiment !== null ? p.avg_sentiment.toFixed(3) : "-"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-sm py-8 text-center">데이터 없음</p>
            )}
          </div>
        </div>
      )}

      <SearchFilter
        searchValue={search}
        onSearch={(v) => { setSearch(v); setPage(1); }}
        placeholder="리뷰 내용 검색..."
        filters={[
          {
            value: platform,
            onChange: (v) => { setPlatform(v); setPage(1); },
            options: [
              { value: "google", label: "Google" },
              { value: "instagram", label: "Instagram" },
              { value: "line", label: "LINE" },
              { value: "naver", label: "Naver" },
              { value: "tabelog", label: "食べログ" },
            ],
            placeholder: "전체 플랫폼",
            ariaLabel: "플랫폼 필터",
          },
          {
            value: hasResponse,
            onChange: (v) => { setHasResponse(v); setPage(1); },
            options: [
              { value: "yes", label: "응답 완료" },
              { value: "no", label: "미응답" },
            ],
            placeholder: "응답 상태 전체",
            ariaLabel: "응답 상태 필터",
          },
        ]}
      />

      {/* Reviews List */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <LoadingSpinner />
        ) : reviews.length === 0 ? (
          <div className="p-8 text-center text-gray-400">리뷰가 없습니다.</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-3 text-left font-medium">플랫폼</th>
                <th className="px-4 py-3 text-left font-medium">내용</th>
                <th className="px-4 py-3 text-center font-medium">평점</th>
                <th className="px-4 py-3 text-center font-medium">감성</th>
                <th className="px-4 py-3 text-center font-medium">응답</th>
                <th className="px-4 py-3 text-left font-medium">등록일</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {reviews.map((r) => {
                const sentiment = sentimentLabel(r.sentiment_score);
                const content = r.content_ja || r.content_ko || "-";
                return (
                  <tr key={r.id} className="hover:bg-gray-50 transition">
                    <td className="px-4 py-3">
                      <Link href={`/reviews/${r.id}`} className="text-xs px-2 py-1 rounded-full font-medium hover:underline" aria-label={`${PLATFORM_LABELS[r.platform]} 리뷰 상세`}>
                        <span className={`px-2 py-1 rounded-full ${PLATFORM_COLORS[r.platform]}`}>
                          {PLATFORM_LABELS[r.platform]}
                        </span>
                      </Link>
                    </td>
                    <td className="px-4 py-3 max-w-xs truncate text-gray-700">
                      <Link href={`/reviews/${r.id}`} className="hover:underline">
                        {content.length > 60 ? content.slice(0, 60) + "..." : content}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {r.rating ? (
                        <span className="text-yellow-500 font-medium">{r.rating.toFixed(1)} <span aria-hidden="true">★</span></span>
                      ) : (
                        <span className="text-gray-300">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {sentimentBar(r.sentiment_score)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {r.response_text ? (
                        <span className="text-xs px-2 py-1 rounded-full bg-green-100 text-green-700">완료</span>
                      ) : (
                        <span className="text-xs px-2 py-1 rounded-full bg-red-100 text-red-700">미응답</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {new Date(r.created_at).toLocaleDateString("ko-KR")}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}

        <Pagination page={page} totalPages={totalPages} onPageChange={setPage} total={total} perPage={perPage} unit="건" />
      </div>
    </AppShell>
  );
}
