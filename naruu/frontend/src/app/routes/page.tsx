"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { TourRoute, TourRouteListResponse, RouteStatus } from "@/lib/types";

const STATUS_LABELS: Record<RouteStatus, string> = {
  draft: "초안",
  published: "공개",
  archived: "보관",
};

const STATUS_COLORS: Record<RouteStatus, string> = {
  draft: "bg-gray-100 text-gray-600",
  published: "bg-green-100 text-green-700",
  archived: "bg-red-100 text-red-600",
};

export default function RoutesPage() {
  const [routes, setRoutes] = useState<TourRoute[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [templateOnly, setTemplateOnly] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchRoutes = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("per_page", "20");
      if (search) params.set("search", search);
      if (templateOnly) params.set("template_only", "true");

      const data = await api.get<TourRouteListResponse>(
        `/tour-routes?${params.toString()}`
      );
      setRoutes(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to fetch routes:", err);
    } finally {
      setLoading(false);
    }
  }, [page, search, templateOnly]);

  useEffect(() => {
    fetchRoutes();
  }, [fetchRoutes]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const totalPages = Math.ceil(total / 20);

  const formatDuration = (minutes: number | null) => {
    if (!minutes) return "-";
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return h > 0 ? `${h}시간 ${m}분` : `${m}분`;
  };

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">관광 루트</h2>
        <Link
          href="/routes/new"
          className="px-4 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 transition text-sm font-medium"
        >
          + 새 루트 만들기
        </Link>
      </div>

      {/* Search & Filter */}
      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder="루트 검색 (일본어/한국어)..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-naruu-500 focus:border-naruu-500 outline-none text-sm"
        />
        <button
          onClick={() => {
            setTemplateOnly(!templateOnly);
            setPage(1);
          }}
          className={`px-4 py-2 border rounded-lg text-sm transition ${
            templateOnly
              ? "border-naruu-600 bg-naruu-50 text-naruu-700"
              : "border-gray-300 text-gray-600 hover:bg-gray-50"
          }`}
        >
          템플릿만
        </button>
      </div>

      {/* Route Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-3 text-center py-12 text-gray-400">로딩 중...</div>
        ) : routes.length === 0 ? (
          <div className="col-span-3 text-center py-12 text-gray-400">
            {search ? "검색 결과가 없습니다" : "등록된 루트가 없습니다"}
          </div>
        ) : (
          routes.map((route) => (
            <Link
              key={route.id}
              href={`/routes/${route.id}`}
              className="bg-white rounded-xl p-5 shadow-sm hover:shadow-md transition border border-gray-100"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-gray-800">{route.name_ja}</h3>
                  <p className="text-sm text-gray-500">{route.name_ko}</p>
                </div>
                <span
                  className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[route.status]}`}
                >
                  {STATUS_LABELS[route.status]}
                </span>
              </div>

              <div className="flex gap-4 text-sm text-gray-600 mb-3">
                <span>{route.waypoints?.length || 0}곳</span>
                {route.total_distance_km && (
                  <span>{route.total_distance_km} km</span>
                )}
                <span>{formatDuration(route.total_duration_minutes)}</span>
              </div>

              <div className="flex flex-wrap gap-1">
                {route.tags?.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 bg-naruu-50 text-naruu-700 rounded text-xs"
                  >
                    {tag}
                  </span>
                ))}
                {route.is_template && (
                  <span className="px-2 py-0.5 bg-violet-50 text-violet-700 rounded text-xs">
                    템플릿
                  </span>
                )}
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
