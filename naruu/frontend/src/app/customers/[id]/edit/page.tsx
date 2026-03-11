"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { Customer } from "@/lib/types";

const AVAILABLE_TAGS = ["VIP", "리피터", "성형", "피부과", "관광", "굿즈", "대구투어"];

export default function EditCustomerPage() {
  const params = useParams();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
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
    tags: [] as string[],
  });

  useEffect(() => {
    async function load() {
      try {
        const data = await api.get<Customer>(`/customers/${params.id}`);
        setForm({
          name_ja: data.name_ja,
          name_ko: data.name_ko || "",
          email: data.email || "",
          phone: data.phone || "",
          line_user_id: data.line_user_id || "",
          nationality: data.nationality,
          visa_type: data.visa_type || "",
          first_visit_date: data.first_visit_date || "",
          preferred_language: data.preferred_language,
          notes: data.notes || "",
          tags: data.tags || [],
        });
      } catch (err) {
        setError("고객 정보를 불러올 수 없습니다");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [params.id]);

  const updateField = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const toggleTag = (tag: string) => {
    setForm((prev) => ({
      ...prev,
      tags: prev.tags.includes(tag)
        ? prev.tags.filter((t) => t !== tag)
        : [...prev.tags, tag],
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSaving(true);

    try {
      const payload: Record<string, unknown> = { ...form };
      for (const key of Object.keys(payload)) {
        if (payload[key] === "") {
          payload[key] = null;
        }
      }
      // Keep name_ja as string even if empty
      if (!form.name_ja) {
        setError("일본어 이름은 필수입니다");
        setSaving(false);
        return;
      }
      payload.name_ja = form.name_ja;

      await api.put<Customer>(`/customers/${params.id}`, payload);
      router.push(`/customers/${params.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "수정에 실패했습니다");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <AppShell>
        <div className="text-center py-12 text-gray-400">로딩 중...</div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <Link
        href={`/customers/${params.id}`}
        className="text-sm text-gray-500 hover:text-naruu-600"
      >
        &larr; 고객 상세
      </Link>
      <h2 className="text-2xl font-bold text-gray-800 mt-2 mb-6">
        고객 정보 수정
      </h2>

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-xl p-6 shadow-sm max-w-2xl space-y-5"
      >
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field
            label="이름 (일본어) *"
            value={form.name_ja}
            onChange={(v) => updateField("name_ja", v)}
          />
          <Field
            label="이름 (한국어)"
            value={form.name_ko}
            onChange={(v) => updateField("name_ko", v)}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field
            label="이메일"
            type="email"
            value={form.email}
            onChange={(v) => updateField("email", v)}
          />
          <Field
            label="전화번호"
            value={form.phone}
            onChange={(v) => updateField("phone", v)}
          />
        </div>

        <Field
          label="LINE User ID"
          value={form.line_user_id}
          onChange={(v) => updateField("line_user_id", v)}
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              국적
            </label>
            <select
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
          <Field
            label="비자 유형"
            value={form.visa_type}
            onChange={(v) => updateField("visa_type", v)}
          />
          <Field
            label="첫 방문일"
            type="date"
            value={form.first_visit_date}
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
              const selected = form.tags.includes(tag);
              return (
                <button
                  key={tag}
                  type="button"
                  onClick={() => toggleTag(tag)}
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

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            메모
          </label>
          <textarea
            value={form.notes}
            onChange={(e) => updateField("notes", e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 outline-none"
          />
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <Link
            href={`/customers/${params.id}`}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 text-sm"
          >
            취소
          </Link>
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 transition text-sm font-medium disabled:opacity-50"
          >
            {saving ? "저장 중..." : "저장"}
          </button>
        </div>
      </form>
    </AppShell>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 outline-none"
      />
    </div>
  );
}
