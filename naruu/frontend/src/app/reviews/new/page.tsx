"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { Review, ReviewPlatform } from "@/lib/types";

export default function NewReviewPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    platform: "google" as ReviewPlatform,
    rating: "",
    content_ja: "",
    content_ko: "",
    customer_id: "",
    partner_id: "",
  });

  function update(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.content_ja && !form.content_ko) {
      alert("리뷰 내용을 입력하세요 (일본어 또는 한국어).");
      return;
    }

    setSaving(true);
    try {
      const body: Record<string, unknown> = {
        platform: form.platform,
      };
      if (form.rating) body.rating = parseFloat(form.rating);
      if (form.content_ja) body.content_ja = form.content_ja;
      if (form.content_ko) body.content_ko = form.content_ko;
      if (form.customer_id) body.customer_id = parseInt(form.customer_id);
      if (form.partner_id) body.partner_id = parseInt(form.partner_id);

      const created = await api.post<Review>("/reviews", body);
      router.push(`/reviews/${created.id}`);
    } catch (e) {
      alert("등록 실패: " + (e instanceof Error ? e.message : "알 수 없는 오류"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell>
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.push("/reviews")} className="text-gray-400 hover:text-gray-600">
          ← 목록
        </button>
        <h2 className="text-2xl font-bold text-gray-800">리뷰 등록</h2>
      </div>

      <form onSubmit={handleSubmit} className="max-w-2xl space-y-6">
        <div className="bg-white rounded-xl p-6 shadow-sm space-y-4">
          {/* Platform */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">플랫폼 *</label>
            <select
              value={form.platform}
              onChange={(e) => update("platform", e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
            >
              <option value="google">Google</option>
              <option value="instagram">Instagram</option>
              <option value="line">LINE</option>
              <option value="naver">Naver</option>
              <option value="tabelog">食べログ</option>
            </select>
          </div>

          {/* Rating */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">평점 (1.0~5.0)</label>
            <input
              type="number"
              step="0.1"
              min="1"
              max="5"
              value={form.rating}
              onChange={(e) => update("rating", e.target.value)}
              placeholder="예: 4.5"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
            />
          </div>

          {/* Content JA */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">리뷰 내용 (일본어)</label>
            <textarea
              value={form.content_ja}
              onChange={(e) => update("content_ja", e.target.value)}
              rows={4}
              placeholder="日本語のレビュー内容..."
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-y"
            />
          </div>

          {/* Content KO */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">리뷰 내용 (한국어)</label>
            <textarea
              value={form.content_ko}
              onChange={(e) => update("content_ko", e.target.value)}
              rows={4}
              placeholder="한국어 리뷰 내용..."
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-y"
            />
          </div>

          {/* Optional IDs */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">고객 ID (선택)</label>
              <input
                type="number"
                value={form.customer_id}
                onChange={(e) => update("customer_id", e.target.value)}
                placeholder="고객 ID"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">제휴처 ID (선택)</label>
              <input
                type="number"
                value={form.partner_id}
                onChange={(e) => update("partner_id", e.target.value)}
                placeholder="제휴처 ID"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
              />
            </div>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 disabled:opacity-50 transition font-medium text-sm"
          >
            {saving ? "등록 중..." : "리뷰 등록"}
          </button>
          <button
            type="button"
            onClick={() => router.push("/reviews")}
            className="px-6 py-2.5 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition text-sm"
          >
            취소
          </button>
        </div>
      </form>
    </AppShell>
  );
}
