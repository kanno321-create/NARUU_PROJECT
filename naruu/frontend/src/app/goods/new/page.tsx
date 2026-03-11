"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { GoodsItem, GoodsCategory } from "@/lib/types";

export default function NewGoodsPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    name_ko: "",
    name_ja: "",
    description_ko: "",
    description_ja: "",
    category: "souvenir" as GoodsCategory,
    price: "",
    stock_quantity: "0",
  });

  function update(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name_ko.trim() || !form.name_ja.trim()) {
      alert("상품명(한/일)을 모두 입력하세요.");
      return;
    }
    if (!form.price || parseFloat(form.price) <= 0) {
      alert("올바른 가격을 입력하세요.");
      return;
    }

    setSaving(true);
    try {
      const body: Record<string, unknown> = {
        name_ko: form.name_ko,
        name_ja: form.name_ja,
        category: form.category,
        price: parseFloat(form.price),
        stock_quantity: parseInt(form.stock_quantity) || 0,
      };
      if (form.description_ko) body.description_ko = form.description_ko;
      if (form.description_ja) body.description_ja = form.description_ja;

      const created = await api.post<GoodsItem>("/goods", body);
      router.push(`/goods/${created.id}`);
    } catch (e) {
      alert("등록 실패: " + (e instanceof Error ? e.message : "알 수 없는 오류"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell>
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.push("/goods")} className="text-gray-400 hover:text-gray-600">
          ← 목록
        </button>
        <h2 className="text-2xl font-bold text-gray-800">상품 등록</h2>
      </div>

      <form onSubmit={handleSubmit} className="max-w-2xl space-y-6">
        <div className="bg-white rounded-xl p-6 shadow-sm space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">상품명 (한국어) *</label>
              <input type="text" value={form.name_ko} onChange={(e) => update("name_ko", e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">商品名 (日本語) *</label>
              <input type="text" value={form.name_ja} onChange={(e) => update("name_ja", e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" required />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">카테고리 *</label>
              <select value={form.category} onChange={(e) => update("category", e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
                <option value="bag">가방</option>
                <option value="accessory">액세서리</option>
                <option value="souvenir">기념품</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">가격 (원) *</label>
              <input type="number" min="0" step="100" value={form.price} onChange={(e) => update("price", e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">초기 재고</label>
              <input type="number" min="0" value={form.stock_quantity} onChange={(e) => update("stock_quantity", e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">설명 (한국어)</label>
            <textarea value={form.description_ko} onChange={(e) => update("description_ko", e.target.value)} rows={3} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-y" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">説明 (日本語)</label>
            <textarea value={form.description_ja} onChange={(e) => update("description_ja", e.target.value)} rows={3} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-y" />
          </div>
        </div>

        <div className="flex gap-3">
          <button type="submit" disabled={saving} className="px-6 py-2.5 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 disabled:opacity-50 transition font-medium text-sm">
            {saving ? "등록 중..." : "상품 등록"}
          </button>
          <button type="button" onClick={() => router.push("/goods")} className="px-6 py-2.5 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition text-sm">
            취소
          </button>
        </div>
      </form>
    </AppShell>
  );
}
