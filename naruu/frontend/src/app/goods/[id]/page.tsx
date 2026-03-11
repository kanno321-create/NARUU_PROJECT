"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { GoodsItem, GoodsCategory } from "@/lib/types";

const CAT_LABELS: Record<GoodsCategory, string> = {
  bag: "가방",
  accessory: "액세서리",
  souvenir: "기념품",
};

export default function GoodsDetailPage() {
  const params = useParams();
  const router = useRouter();
  const goodsId = params.id as string;

  const [goods, setGoods] = useState<GoodsItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [adjustQty, setAdjustQty] = useState("");
  const [adjustReason, setAdjustReason] = useState("");
  const [adjusting, setAdjusting] = useState(false);

  useEffect(() => { loadGoods(); }, [goodsId]);

  async function loadGoods() {
    try {
      const data = await api.get<GoodsItem>(`/goods/${goodsId}`);
      setGoods(data);
    } catch {
      router.push("/goods");
    } finally {
      setLoading(false);
    }
  }

  async function handleStockAdjust() {
    const qty = parseInt(adjustQty);
    if (isNaN(qty) || qty === 0) return;

    setAdjusting(true);
    try {
      const updated = await api.post<GoodsItem>(`/goods/${goodsId}/stock`, {
        adjustment: qty,
        reason: adjustReason || undefined,
      });
      setGoods(updated);
      setAdjustQty("");
      setAdjustReason("");
    } catch (e) {
      alert("재고 조정 실패: " + (e instanceof Error ? e.message : "알 수 없는 오류"));
    } finally {
      setAdjusting(false);
    }
  }

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center py-20 text-gray-400">로딩 중...</div>
      </AppShell>
    );
  }

  if (!goods) return null;

  return (
    <AppShell>
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.push("/goods")} className="text-gray-400 hover:text-gray-600">
          ← 목록
        </button>
        <h2 className="text-2xl font-bold text-gray-800">{goods.name_ko}</h2>
        {!goods.is_active && (
          <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-500">판매 중지</span>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left */}
        <div className="lg:col-span-2 space-y-4">
          {/* Product Image */}
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="h-64 bg-gray-100 flex items-center justify-center">
              {goods.image_urls && goods.image_urls.length > 0 ? (
                <img src={goods.image_urls[0]} alt={goods.name_ko} className="h-full w-full object-contain" />
              ) : (
                <span className="text-6xl">🛍️</span>
              )}
            </div>
          </div>

          {/* Product Info */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-700">상품 정보</h3>
              <button
                onClick={() => router.push(`/goods/${goodsId}/edit`)}
                className="text-sm text-naruu-600 hover:text-naruu-800"
              >
                수정
              </button>
            </div>

            <dl className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt className="text-gray-500">상품명 (한국어)</dt>
                <dd className="font-medium">{goods.name_ko}</dd>
              </div>
              <div>
                <dt className="text-gray-500">상품명 (일본어)</dt>
                <dd className="font-medium">{goods.name_ja}</dd>
              </div>
              <div>
                <dt className="text-gray-500">카테고리</dt>
                <dd>{CAT_LABELS[goods.category]}</dd>
              </div>
              <div>
                <dt className="text-gray-500">가격</dt>
                <dd className="font-bold text-naruu-700">{goods.price.toLocaleString()}원</dd>
              </div>
            </dl>

            {goods.description_ko && (
              <div className="mt-4">
                <p className="text-xs text-gray-500 mb-1">설명 (한국어)</p>
                <p className="text-gray-700 text-sm whitespace-pre-wrap">{goods.description_ko}</p>
              </div>
            )}
            {goods.description_ja && (
              <div className="mt-3">
                <p className="text-xs text-gray-500 mb-1">説明 (日本語)</p>
                <p className="text-gray-700 text-sm whitespace-pre-wrap">{goods.description_ja}</p>
              </div>
            )}
          </div>
        </div>

        {/* Right sidebar */}
        <div className="space-y-4">
          {/* Stock Card */}
          <div className={`rounded-xl p-6 shadow-sm ${goods.stock_quantity === 0 ? "bg-red-50" : goods.stock_quantity <= 5 ? "bg-yellow-50" : "bg-green-50"}`}>
            <h3 className="font-semibold text-gray-700 mb-3">재고 현황</h3>
            <p className="text-4xl font-bold text-center py-4">
              {goods.stock_quantity}
              <span className="text-sm font-normal text-gray-500 ml-1">개</span>
            </p>
            {goods.stock_quantity === 0 && (
              <p className="text-center text-red-600 text-sm font-medium">품절 상태</p>
            )}
            {goods.stock_quantity > 0 && goods.stock_quantity <= 5 && (
              <p className="text-center text-yellow-600 text-sm font-medium">재고 부족 경고</p>
            )}

            {/* Stock Adjustment */}
            <div className="mt-4 pt-4 border-t border-white/50">
              <p className="text-xs text-gray-600 mb-2">재고 조정</p>
              <div className="flex gap-2 mb-2">
                <input
                  type="number"
                  value={adjustQty}
                  onChange={(e) => setAdjustQty(e.target.value)}
                  placeholder="+10 또는 -5"
                  className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white"
                />
                <button
                  onClick={handleStockAdjust}
                  disabled={adjusting || !adjustQty}
                  className="px-4 py-2 bg-naruu-600 text-white rounded-lg text-sm hover:bg-naruu-700 disabled:opacity-50"
                >
                  {adjusting ? "..." : "조정"}
                </button>
              </div>
              <input
                type="text"
                value={adjustReason}
                onChange={(e) => setAdjustReason(e.target.value)}
                placeholder="사유 (선택)"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white"
              />
            </div>
          </div>

          {/* Meta */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-3">정보</h3>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">ID</dt>
                <dd className="font-mono">#{goods.id}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">상태</dt>
                <dd>{goods.is_active ? "판매 중" : "판매 중지"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">등록일</dt>
                <dd>{new Date(goods.created_at).toLocaleDateString("ko-KR")}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
