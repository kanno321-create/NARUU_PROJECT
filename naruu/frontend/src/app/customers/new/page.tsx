"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { Customer, CustomerCreate } from "@/lib/types";
import ErrorBanner from "@/components/ui/error-banner";

const AVAILABLE_TAGS = ["VIP", "리피터", "성형", "피부과", "관광", "굿즈", "대구투어"];

export default function NewCustomerPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState<CustomerCreate>({
    name_ja: "",
    name_ko: "",
    email: "",
    phone: "",
    line_user_id: "",
    nationality: "JP",
    visa_type: "",
    first_visit_date: "",
    preferred_language: "ja",
    notes: "",
    tags: [],
  });

  const updateField = (field: keyof CustomerCreate, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const toggleTag = (tag: string) => {
    setForm((prev) => {
      const tags = prev.tags || [];
      return {
        ...prev,
        tags: tags.includes(tag)
          ? tags.filter((t) => t !== tag)
          : [...tags, tag],
      };
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // Clean empty strings to undefined
      const payload: Record<string, unknown> = { ...form };
      for (const key of Object.keys(payload)) {
        if (payload[key] === "") {
          delete payload[key];
        }
      }

      const created = await api.post<Customer>("/customers", payload);
      router.push(`/customers/${created.id}`);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "고객 등록에 실패했습니다"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <Link
        href="/customers"
        className="text-sm text-gray-500 hover:text-naruu-600"
      >
        &larr; 고객 목록
      </Link>
      <h2 className="text-2xl font-bold text-gray-800 mt-2 mb-6">
        신규 고객 등록
      </h2>

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-xl p-6 shadow-sm max-w-2xl space-y-5"
      >
        <ErrorBanner message={error} />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField
            label="이름 (일본어) *"
            value={form.name_ja}
            onChange={(v) => updateField("name_ja", v)}
            placeholder="山田太郎"
            required
          />
          <FormField
            label="이름 (한국어)"
            value={form.name_ko || ""}
            onChange={(v) => updateField("name_ko", v)}
            placeholder="야마다 타로"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField
            label="이메일"
            type="email"
            value={form.email || ""}
            onChange={(v) => updateField("email", v)}
            placeholder="yamada@email.com"
          />
          <FormField
            label="전화번호"
            value={form.phone || ""}
            onChange={(v) => updateField("phone", v)}
            placeholder="+81-90-1234-5678"
          />
        </div>

        <FormField
          label="LINE User ID"
          value={form.line_user_id || ""}
          onChange={(v) => updateField("line_user_id", v)}
          placeholder="U1234567890abcdef"
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="new-nationality" className="block text-sm font-medium text-gray-700 mb-1">
              국적
            </label>
            <select
              id="new-nationality"
              value={form.nationality}
              onChange={(e) => updateField("nationality", e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 outline-none"
            >
              <option value="JP">일본</option>
              <option value="CN">중국</option>
              <option value="TW">대만</option>
              <option value="KR">한국</option>
              <option value="US">미국</option>
              <option value="OTHER">기타</option>
            </select>
          </div>
          <FormField
            label="비자 유형"
            value={form.visa_type || ""}
            onChange={(v) => updateField("visa_type", v)}
            placeholder="관광비자"
          />
          <FormField
            label="첫 방문일"
            type="date"
            value={form.first_visit_date || ""}
            onChange={(v) => updateField("first_visit_date", v)}
          />
        </div>

        {/* Tags */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            태그
          </label>
          <div className="flex flex-wrap gap-2">
            {AVAILABLE_TAGS.map((tag) => {
              const selected = form.tags?.includes(tag);
              return (
                <button
                  key={tag}
                  type="button"
                  onClick={() => toggleTag(tag)}
                  aria-pressed={selected}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition ${
                    selected
                      ? "bg-naruu-600 text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {tag}
                </button>
              );
            })}
          </div>
        </div>

        <FormField
          label="메모"
          value={form.notes || ""}
          onChange={(v) => updateField("notes", v)}
          placeholder="특이사항이나 선호사항을 입력하세요..."
          multiline
        />

        <div className="flex justify-end gap-3 pt-2">
          <Link
            href="/customers"
            className="px-4 py-2 text-gray-600 hover:text-gray-800 text-sm"
          >
            취소
          </Link>
          <button
            type="submit"
            disabled={loading || !form.name_ja}
            className="px-6 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 transition text-sm font-medium disabled:opacity-50"
          >
            {loading ? "등록 중..." : "고객 등록"}
          </button>
        </div>
      </form>
    </AppShell>
  );
}

function FormField({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
  required = false,
  multiline = false,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
  required?: boolean;
  multiline?: boolean;
}) {
  const fieldId = `new-${label.replace(/[^a-zA-Z가-힣]/g, "-").toLowerCase()}`;
  const cls =
    "w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 outline-none";

  return (
    <div>
      <label htmlFor={fieldId} className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      {multiline ? (
        <textarea
          id={fieldId}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          rows={3}
          className={cls}
        />
      ) : (
        <input
          id={fieldId}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          required={required}
          className={cls}
        />
      )}
    </div>
  );
}
