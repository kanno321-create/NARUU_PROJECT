"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { Review, ReviewListResponse, ReviewStats, ReviewPlatform } from "@/lib/types";

const PLATFORM_LABELS: Record<ReviewPlatform, string> = {
  google: "Google",
  instagram: "Instagram",
  line: "LINE",
  naver: "Naver",
  tabelog: "食べログ",
};

const PLATFORM_COLORS: Record<ReviewPlatform, string> = {
  google: "bg-blue-100 text-blue-700",
  instagram: "bg-pink-100 text-pink-700",
  line: "bg-green-100 text-green-700",
  naver: "bg-emerald-100 text-emerald-700",
  tabelog: "bg-orange-100 text-orange-700",
};

const SENTIMENT_COLORS = ["#22c55e", "#f59e0b", "#ef4444"];

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
      <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
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
    } catch (e) {
      console.error("Failed to load review stats", e);
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
    } catch (e) {
      console.error("Failed to load reviews", e);
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
                    label={({ name, value }) => `${name} ${value}`}
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

      {/* Filters */}
      <div className="bg-white rounded-xl p-4 shadow-sm mb-4">
        <div className="flex flex-wrap gap-3 items-center">
          <input
            type="text"
            placeholder="리뷰 내용 검색..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 focus:border-transparent w-64"
          />
          <select
            value={platform}
            onChange={(e) => { setPlatform(e.target.value); setPage(1); }}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
          >
            <option value="">전체 플랫폼</option>
            <option value="google">Google</option>
            <option value="instagram">Instagram</option>
            <option value="line">LINE</option>
            <option value="naver">Naver</option>
            <option value="tabelog">食べログ</option>
          </select>
          <select
            value={hasResponse}
            onChange={(e) => { setHasResponse(e.target.value); setPage(1); }}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
          >
            <option value="">응답 상태 전체</option>
            <option value="yes">응답 완료</option>
            <option value="no">미응답</option>
          </select>
        </div>
      </div>

      {/* Reviews List */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-400">로딩 중...</div>
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
                  <tr key={r.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => window.location.href = `/reviews/${r.id}`}>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-1 rounded-full font-medium ${PLATFORM_COLORS[r.platform]}`}>
                        {PLATFORM_LABELS[r.platform]}
                      </span>
                    </td>
                    <td className="px-4 py-3 max-w-xs truncate text-gray-700">
                      {content.length > 60 ? content.slice(0, 60) + "..." : content}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {r.rating ? (
                        <span className="text-yellow-500 font-medium">{r.rating.toFixed(1)} ★</span>
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

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
            <p className="text-xs text-gray-500">
              전체 {total}건 중 {(page - 1) * perPage + 1}-{Math.min(page * perPage, total)}
            </p>
            <div className="flex gap-1">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page <= 1}
                className="px-3 py-1 text-sm border rounded disabled:opacity-30"
              >
                이전
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page >= totalPages}
                className="px-3 py-1 text-sm border rounded disabled:opacity-30"
              >
                다음
              </button>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
