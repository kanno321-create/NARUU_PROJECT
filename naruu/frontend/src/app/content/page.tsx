"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type {
  Content,
  ContentListResponse,
  ContentStatus,
  ContentStats,
} from "@/lib/types";
import { SERIES_LABELS, CONTENT_STATUS_LABELS, CONTENT_STATUS_COLORS, CONTENT_PLATFORM_LABELS } from "@/lib/constants";
import Pagination from "@/components/ui/pagination";
import LoadingSpinner from "@/components/ui/loading-spinner";
import ErrorBanner from "@/components/ui/error-banner";
import SearchFilter from "@/components/ui/search-filter";

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
  const [error, setError] = useState<string | null>(null);

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
      setError(null);
    } catch {
      setError("데이터를 불러오는데 실패했습니다.");
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

      <ErrorBanner message={error} />

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
                aria-pressed={statusFilter === s}
                className={`rounded-xl p-3 text-center transition border ${
                  statusFilter === s
                    ? "border-naruu-400 ring-2 ring-naruu-200"
                    : "border-gray-100"
                } ${CONTENT_STATUS_COLORS[s]} bg-opacity-50`}
              >
                <p className="text-xl font-bold">{stats.by_status[s] || 0}</p>
                <p className="text-xs">{CONTENT_STATUS_LABELS[s]}</p>
              </button>
            )
          )}
        </div>
      )}

      <SearchFilter
        searchValue={searchInput}
        onSearch={setSearchInput}
        placeholder="콘텐츠 검색..."
        filters={[{
          value: seriesFilter,
          onChange: (v) => { setSeriesFilter(v); setPage(1); },
          options: [
            { value: "DaeguTour", label: "대구투어" },
            { value: "JCouple", label: "J커플" },
            { value: "Medical", label: "의료" },
            { value: "Brochure", label: "브로슈어" },
          ],
          placeholder: "전체 시리즈",
          ariaLabel: "시리즈 필터",
        }]}
      />

      {/* Content Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-3"><LoadingSpinner /></div>
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
                  <span className="text-4xl" aria-hidden="true">
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
                    className={`px-2 py-0.5 rounded text-xs font-medium ${CONTENT_STATUS_COLORS[c.status]}`}
                  >
                    {CONTENT_STATUS_LABELS[c.status]}
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>{c.platform ? CONTENT_PLATFORM_LABELS[c.platform] : "미지정"}</span>
                  <span>{new Date(c.created_at).toLocaleDateString("ko-KR")}</span>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>

      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} total={total} unit="개" />
    </AppShell>
  );
}
