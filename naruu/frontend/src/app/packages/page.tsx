"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { Package, PackageListResponse, PackageCategory } from "@/lib/types";

const CATEGORY_LABELS: Record<PackageCategory, string> = {
  medical: "의료",
  tourism: "관광",
  combo: "콤보",
  goods: "굿즈",
};

const CATEGORY_COLORS: Record<PackageCategory, string> = {
  medical: "bg-rose-100 text-rose-700",
  tourism: "bg-sky-100 text-sky-700",
  combo: "bg-violet-100 text-violet-700",
  goods: "bg-amber-100 text-amber-700",
};

export default function PackagesPage() {
  const [packages, setPackages] = useState<Package[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const fetchPackages = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("per_page", "20");
      if (search) params.set("search", search);
      if (categoryFilter) params.set("category", categoryFilter);

      const data = await api.get<PackageListResponse>(
        `/packages?${params.toString()}`
      );
      setPackages(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to fetch packages:", err);
    } finally {
      setLoading(false);
    }
  }, [page, search, categoryFilter]);

  useEffect(() => {
    fetchPackages();
  }, [fetchPackages]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const totalPages = Math.ceil(total / 20);

  const formatPrice = (price: number | null, currency: string) => {
    if (price === null) return "-";
    if (currency === "JPY") return `¥${price.toLocaleString()}`;
    return `₩${price.toLocaleString()}`;
  };

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">패키지 관리</h2>
        <div className="flex gap-2">
          <Link
            href="/packages/quote"
            className="px-4 py-2 bg-white border border-naruu-600 text-naruu-600 rounded-lg hover:bg-naruu-50 transition text-sm font-medium"
          >
            견적 생성
          </Link>
          <Link
            href="/packages/new"
            className="px-4 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 transition text-sm font-medium"
          >
            + 신규 패키지
          </Link>
        </div>
      </div>

      {/* Search & Filter */}
      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder="패키지명 검색 (일본어/한국어)..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-naruu-500 focus:border-naruu-500 outline-none text-sm"
        />
        <select
          value={categoryFilter}
          onChange={(e) => {
            setCategoryFilter(e.target.value);
            setPage(1);
          }}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 outline-none"
        >
          <option value="">전체 카테고리</option>
          <option value="medical">의료</option>
          <option value="tourism">관광</option>
          <option value="combo">콤보</option>
          <option value="goods">굿즈</option>
        </select>
      </div>

      {/* Package Table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">패키지명 (JP)</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">패키지명 (KR)</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">카테고리</th>
              <th className="text-right px-4 py-3 font-medium text-gray-600">가격</th>
              <th className="text-center px-4 py-3 font-medium text-gray-600">기간</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">포함사항</th>
              <th className="text-center px-4 py-3 font-medium text-gray-600">상태</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="text-center py-8 text-gray-400">
                  로딩 중...
                </td>
              </tr>
            ) : packages.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-8 text-gray-400">
                  {search || categoryFilter
                    ? "검색 결과가 없습니다"
                    : "등록된 패키지가 없습니다"}
                </td>
              </tr>
            ) : (
              packages.map((pkg) => (
                <tr
                  key={pkg.id}
                  className="border-b border-gray-100 hover:bg-gray-50 transition"
                >
                  <td className="px-4 py-3">
                    <Link
                      href={`/packages/${pkg.id}`}
                      className="text-naruu-600 hover:underline font-medium"
                    >
                      {pkg.name_ja}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{pkg.name_ko}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                        CATEGORY_COLORS[pkg.category]
                      }`}
                    >
                      {CATEGORY_LABELS[pkg.category]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-gray-700">
                    {formatPrice(pkg.base_price, pkg.currency)}
                  </td>
                  <td className="px-4 py-3 text-center text-gray-500">
                    {pkg.duration_days ? `${pkg.duration_days}일` : "-"}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {pkg.includes?.slice(0, 3).map((item) => (
                        <span
                          key={item}
                          className="inline-block px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                        >
                          {item}
                        </span>
                      ))}
                      {(pkg.includes?.length || 0) > 3 && (
                        <span className="text-xs text-gray-400">
                          +{pkg.includes!.length - 3}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`inline-block w-2 h-2 rounded-full ${
                        pkg.is_active ? "bg-green-500" : "bg-gray-300"
                      }`}
                    />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
            <span className="text-xs text-gray-500">
              총 {total}개 중 {(page - 1) * 20 + 1}-
              {Math.min(page * 20, total)}개
            </span>
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
      </div>
    </AppShell>
  );
}
