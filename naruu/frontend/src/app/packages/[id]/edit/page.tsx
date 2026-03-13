"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { Package, PackageCategory, CurrencyType } from "@/lib/types";
import LoadingSpinner from "@/components/ui/loading-spinner";
import ErrorBanner from "@/components/ui/error-banner";

const CATEGORIES: { value: PackageCategory; label: string }[] = [
  { value: "medical", label: "의료" },
  { value: "tourism", label: "관광" },
  { value: "combo", label: "콤보 (의료+관광)" },
  { value: "goods", label: "굿즈" },
];

export default function EditPackagePage() {
  const params = useParams();
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [includeInput, setIncludeInput] = useState("");

  const [form, setForm] = useState({
    name_ja: "",
    name_ko: "",
    description_ja: "",
    description_ko: "",
    category: "tourism" as PackageCategory,
    base_price: undefined as number | undefined,
    currency: "JPY" as CurrencyType,
    duration_days: undefined as number | undefined,
    includes: [] as string[],
    is_active: true,
  });

  useEffect(() => {
    (async () => {
      try {
        const data = await api.get<Package>(`/packages/${params.id}`);
        setForm({
          name_ja: data.name_ja,
          name_ko: data.name_ko,
          description_ja: data.description_ja || "",
          description_ko: data.description_ko || "",
          category: data.category,
          base_price: data.base_price ?? undefined,
          currency: data.currency,
          duration_days: data.duration_days ?? undefined,
          includes: data.includes || [],
          is_active: data.is_active,
        });
      } catch {
        router.push("/packages");
      } finally {
        setLoading(false);
      }
    })();
  }, [params.id, router]);

  const handleChange = (field: string, value: unknown) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const addInclude = () => {
    const item = includeInput.trim();
    if (item && !form.includes.includes(item)) {
      handleChange("includes", [...form.includes, item]);
      setIncludeInput("");
    }
  };

  const removeInclude = (item: string) => {
    handleChange("includes", form.includes.filter((i) => i !== item));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.put(`/packages/${params.id}`, form);
      router.push(`/packages/${params.id}`);
    } catch {
      setError("패키지 수정에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <AppShell>
        <LoadingSpinner text="패키지 로딩 중..." />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <Link href={`/packages/${params.id}`} className="text-sm text-naruu-600 hover:underline">
        &larr; 패키지 상세
      </Link>
      <h2 className="text-2xl font-bold text-gray-800 mt-2 mb-6">패키지 수정</h2>

      <ErrorBanner message={error} />

      <form onSubmit={handleSubmit} className="max-w-2xl space-y-6">
        <div className="bg-white rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="font-semibold text-gray-700">기본 정보</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">패키지명 (일본어) *</label>
              <input
                type="text"
                value={form.name_ja}
                onChange={(e) => handleChange("name_ja", e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">패키지명 (한국어) *</label>
              <input
                type="text"
                value={form.name_ko}
                onChange={(e) => handleChange("name_ko", e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 outline-none"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">설명 (일본어)</label>
            <textarea
              value={form.description_ja}
              onChange={(e) => handleChange("description_ja", e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">설명 (한국어)</label>
            <textarea
              value={form.description_ko}
              onChange={(e) => handleChange("description_ko", e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 outline-none"
            />
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="font-semibold text-gray-700">카테고리 & 가격</h3>
          <div>
            <label className="block text-sm text-gray-600 mb-1">카테고리</label>
            <select
              value={form.category}
              onChange={(e) => handleChange("category", e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 outline-none"
            >
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">기준 가격</label>
              <input
                type="number"
                value={form.base_price ?? ""}
                onChange={(e) => handleChange("base_price", e.target.value ? Number(e.target.value) : undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">통화</label>
              <select
                value={form.currency}
                onChange={(e) => handleChange("currency", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 outline-none"
              >
                <option value="JPY">¥ JPY</option>
                <option value="KRW">₩ KRW</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">기간 (일)</label>
              <input
                type="number"
                value={form.duration_days ?? ""}
                onChange={(e) => handleChange("duration_days", e.target.value ? Number(e.target.value) : undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 outline-none"
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => handleChange("is_active", e.target.checked)}
              className="w-4 h-4 text-naruu-600 rounded"
            />
            <label className="text-sm text-gray-600">활성 상태</label>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="font-semibold text-gray-700">포함사항</h3>
          <div className="flex gap-2">
            <input
              type="text"
              value={includeInput}
              onChange={(e) => setIncludeInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addInclude(); } }}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 outline-none"
              placeholder="포함사항 입력 후 Enter"
            />
            <button type="button" onClick={addInclude} className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">추가</button>
          </div>
          <div className="flex flex-wrap gap-2">
            {form.includes.map((item) => (
              <span key={item} className="inline-flex items-center gap-1 px-3 py-1 bg-naruu-50 text-naruu-700 rounded-lg text-sm">
                {item}
                <button type="button" onClick={() => removeInclude(item)} className="text-naruu-400 hover:text-naruu-600">x</button>
              </span>
            ))}
          </div>
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 transition text-sm font-medium disabled:opacity-50"
          >
            {saving ? "저장 중..." : "수정 저장"}
          </button>
          <Link
            href={`/packages/${params.id}`}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition text-sm"
          >
            취소
          </Link>
        </div>
      </form>
    </AppShell>
  );
}
