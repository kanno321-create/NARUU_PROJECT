"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { GoodsItem, GoodsListResponse, GoodsStats } from "@/lib/types";
import { CAT_LABELS, CAT_COLORS } from "@/lib/constants";
import Pagination from "@/components/ui/pagination";
import LoadingSpinner from "@/components/ui/loading-spinner";
import ErrorBanner from "@/components/ui/error-banner";
import SearchFilter from "@/components/ui/search-filter";

export default function GoodsPage() {
  const [goods, setGoods] = useState<GoodsItem[]>([]);
  const [stats, setStats] = useState<GoodsStats | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [catFilter, setCatFilter] = useState<string>("");
  const [search, setSearch] = useState("");
  const [lowStock, setLowStock] = useState(false);

  const perPage = 20;

  useEffect(() => { loadStats(); }, []);
  useEffect(() => { loadGoods(); }, [page, catFilter, search, lowStock]);

  async function loadStats() {
    try {
      const data = await api.get<GoodsStats>("/goods/stats");
      setStats(data);
    } catch {
      setError("통계를 불러오는데 실패했습니다.");
    }
  }

  async function loadGoods() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("per_page", String(perPage));
      if (catFilter) params.set("category", catFilter);
      if (search) params.set("search", search);
      if (lowStock) params.set("low_stock", "true");

      const data = await api.get<GoodsListResponse>(`/goods?${params}`);
      setGoods(data.items);
      setTotal(data.total);
      setError(null);
    } catch {
      setError("상품을 불러오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  const totalPages = Math.ceil(total / perPage);

  function stockBadge(qty: number) {
    if (qty === 0) return { text: "품절", color: "bg-red-100 text-red-700" };
    if (qty <= 5) return { text: `잔여 ${qty}`, color: "bg-yellow-100 text-yellow-700" };
    return { text: `${qty}개`, color: "bg-green-100 text-green-700" };
  }

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">굿즈 샵</h2>
        <Link
          href="/goods/new"
          className="px-4 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 transition text-sm font-medium"
        >
          + 상품 등록
        </Link>
      </div>

      <ErrorBanner message={error} />

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <p className="text-xs text-gray-500 mb-1">전체 상품</p>
            <p className="text-2xl font-bold text-gray-800">{stats.total}</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <p className="text-xs text-gray-500 mb-1">판매 중</p>
            <p className="text-2xl font-bold text-green-600">{stats.active}</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <p className="text-xs text-gray-500 mb-1">재고 부족</p>
            <p className="text-2xl font-bold text-yellow-600">{stats.low_stock}</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <p className="text-xs text-gray-500 mb-1">품절</p>
            <p className="text-2xl font-bold text-red-600">{stats.out_of_stock}</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <p className="text-xs text-gray-500 mb-1">재고 총액</p>
            <p className="text-lg font-bold text-naruu-700">{stats.total_inventory_value.toLocaleString()}원</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-xl p-4 shadow-sm mb-4">
        <div className="flex flex-wrap gap-3 items-center">
          <SearchFilter
            searchValue={search}
            onSearch={(v) => { setSearch(v); setPage(1); }}
            placeholder="상품명 검색..."
            filters={[{
              value: catFilter,
              onChange: (v) => { setCatFilter(v); setPage(1); },
              options: [
                { value: "bag", label: "가방" },
                { value: "accessory", label: "액세서리" },
                { value: "souvenir", label: "기념품" },
              ],
              placeholder: "전체 카테고리",
              ariaLabel: "카테고리 필터",
            }]}
          />
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={lowStock}
              onChange={(e) => { setLowStock(e.target.checked); setPage(1); }}
              className="rounded"
              aria-label="재고 부족 상품만 보기"
            />
            재고 부족만
          </label>
        </div>
      </div>

      {/* Products Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {loading ? (
          <div className="col-span-full"><LoadingSpinner /></div>
        ) : goods.length === 0 ? (
          <div className="col-span-full text-center py-8 text-gray-400">등록된 상품이 없습니다.</div>
        ) : (
          goods.map((g) => {
            const stock = stockBadge(g.stock_quantity);
            return (
              <Link
                key={g.id}
                href={`/goods/${g.id}`}
                className="bg-white rounded-xl shadow-sm hover:shadow-md transition block overflow-hidden"
              >
                {/* Image placeholder */}
                <div className="h-40 bg-gray-100 flex items-center justify-center">
                  {g.image_urls && g.image_urls.length > 0 ? (
                    <img src={g.image_urls[0]} alt={g.name_ko} className="h-full w-full object-cover" />
                  ) : (
                    <span className="text-4xl" aria-hidden="true">🛍️</span>
                  )}
                </div>
                <div className="p-4">
                  <div className="flex items-start justify-between mb-1">
                    <h3 className="font-semibold text-gray-800 text-sm">{g.name_ko}</h3>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${CAT_COLORS[g.category]}`}>
                      {CAT_LABELS[g.category]}
                    </span>
                  </div>
                  {g.name_ja && <p className="text-xs text-gray-400 mb-2">{g.name_ja}</p>}
                  <div className="flex items-center justify-between mt-2">
                    <span className="font-bold text-naruu-700">{g.price.toLocaleString()}원</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${stock.color}`}>{stock.text}</span>
                  </div>
                  {!g.is_active && (
                    <span className="text-xs text-gray-400 mt-1 block">판매 중지</span>
                  )}
                </div>
              </Link>
            );
          })
        )}
      </div>

      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} total={total} perPage={perPage} unit="개" />
    </AppShell>
  );
}
