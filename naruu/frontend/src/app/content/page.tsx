"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type {
  Content,
  ContentListResponse,
  ContentSeries,
  ContentStatus,
  ContentStats,
} from "@/lib/types";

const SERIES_LABELS: Record<ContentSeries, string> = {
  DaeguTour: "대구투어",
  JCouple: "J커플",
  Medical: "의료",
  Brochure: "브로슈어",
};

const STATUS_LABELS: Record<ContentStatus, string> = {
  draft: "초안",
  review: "검토 중",
  approved: "승인됨",
  published: "게시됨",
  rejected: "반려",
};

const STATUS_COLORS: Record<ContentStatus, string> = {
  draft: "bg-gray-100 text-gray-600",
  review: "bg-amber-100 text-amber-700",
  approved: "bg-green-100 text-green-700",
  published: "bg-blue-100 text-blue-700",
  rejected: "bg-red-100 text-red-600",
};

const PLATFORM_LABELS: Record<string, string> = {
  youtube: "YouTube",
  instagram: "Instagram",
  tiktok: "TikTok",
};

export default function ContentPage() {
  const [contents, setContents] = useState<Content[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [seriesFilter, setSeriesFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [stats, setStats] = useState<ContentStats | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchContents = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("per_page", "20");
      if (search) params.set("search", search);
      if (seriesFilter) params.set("series", seriesFilter);
      if (statusFilter) params.set("status", statusFilter);

      const data = await api.get<ContentListResponse>(
        `/content?${params.toString()}`
      );
      setContents(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to fetch content:", err);
    } finally {
      setLoading(false);
    }
  }, [page, search, seriesFilter, statusFilter]);

  useEffect(() => {
    fetchContents();
  }, [fetchContents]);

  useEffect(() => {
    api
      .get<ContentStats>("/content/stats/overview")
      .then(setStats)
      .catch(() => {});
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const totalPages = Math.ceil(total / 20);

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">콘텐츠 관리</h2>
        <Link
          href="/content/new"
          className="px-4 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 transition text-sm font-medium"
        >
          + 새 콘텐츠
        </Link>
      </div>

      {/* Pipeline Stats */}
      {stats && (
        <div className="grid grid-cols-5 gap-3 mb-6">
          {(["draft", "review", "approved", "published", "rejected"] as ContentStatus[]).map(
            (s) => (
              <button
                key={s}
                onClick={() => {
                  setStatusFilter(statusFilter === s ? "" : s);
                  setPage(1);
                }}
                className={`rounded-xl p-3 text-center transition border ${
                  statusFilter === s
                    ? "border-naruu-400 ring-2 ring-naruu-200"
                    : "border-gray-100"
                } ${STATUS_COLORS[s]} bg-opacity-50`}
              >
                <p className="text-xl font-bold">{stats.by_status[s] || 0}</p>
                <p className="text-xs">{STATUS_LABELS[s]}</p>
              </button>
            )
          )}
        </div>
      )}

      {/* Search & Filters */}
      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder="콘텐츠 검색..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-naruu-500 outline-none text-sm"
        />
        <select
          value={seriesFilter}
          onChange={(e) => {
            setSeriesFilter(e.target.value);
            setPage(1);
          }}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none"
        >
          <option value="">전체 시리즈</option>
          <option value="DaeguTour">대구투어</option>
          <option value="JCouple">J커플</option>
          <option value="Medical">의료</option>
          <option value="Brochure">브로슈어</option>
        </select>
      </div>

      {/* Content Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-3 text-center py-12 text-gray-400">로딩 중...</div>
        ) : contents.length === 0 ? (
          <div className="col-span-3 text-center py-12 text-gray-400">
            {search || seriesFilter || statusFilter
              ? "검색 결과가 없습니다"
              : "등록된 콘텐츠가 없습니다"}
          </div>
        ) : (
          contents.map((c) => (
            <Link
              key={c.id}
              href={`/content/${c.id}`}
              className="bg-white rounded-xl shadow-sm hover:shadow-md transition border border-gray-100 overflow-hidden"
            >
              {/* Thumbnail */}
              {c.thumbnail_url ? (
                <div className="h-40 bg-gray-100">
                  <img
                    src={c.thumbnail_url}
                    alt={c.title}
                    className="w-full h-full object-cover"
                  />
                </div>
              ) : (
                <div className="h-40 bg-gradient-to-br from-naruu-100 to-violet-100 flex items-center justify-center">
                  <span className="text-4xl">
                    {c.series === "DaeguTour"
                      ? "🏙️"
                      : c.series === "JCouple"
                      ? "💑"
                      : c.series === "Medical"
                      ? "🏥"
                      : "📄"}
                  </span>
                </div>
              )}

              <div className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-gray-800 text-sm line-clamp-2">
                    {c.title}
                  </h3>
                </div>

                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 bg-naruu-50 text-naruu-700 rounded text-xs">
                    {SERIES_LABELS[c.series]}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[c.status]}`}
                  >
                    {STATUS_LABELS[c.status]}
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>{c.platform ? PLATFORM_LABELS[c.platform] : "미지정"}</span>
                  <span>{new Date(c.created_at).toLocaleDateString("ko-KR")}</span>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-6">
          <span className="text-xs text-gray-500">총 {total}개</span>
          <div className="flex gap-1">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
            >
              이전
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
            >
              다음
            </button>
          </div>
        </div>
      )}
    </AppShell>
  );
}
