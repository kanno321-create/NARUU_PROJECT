"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { ContentSeries, ContentPlatform, ContentCreate } from "@/lib/types";
import ErrorBanner from "@/components/ui/error-banner";

const SERIES_OPTIONS: { value: ContentSeries; label: string }[] = [
  { value: "DaeguTour", label: "대구투어" },
  { value: "JCouple", label: "J커플" },
  { value: "Medical", label: "의료" },
  { value: "Brochure", label: "브로슈어" },
];

const PLATFORM_OPTIONS: { value: ContentPlatform; label: string }[] = [
  { value: "youtube", label: "YouTube" },
  { value: "instagram", label: "Instagram" },
  { value: "tiktok", label: "TikTok" },
];

export default function NewContentPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<ContentCreate>({
    title: "",
    series: "DaeguTour",
    script_ja: "",
    script_ko: "",
    video_url: "",
    thumbnail_url: "",
    platform: undefined,
  });

  // AI Script Generation
  const [aiTopic, setAiTopic] = useState("");
  const [aiTone, setAiTone] = useState("friendly");
  const [aiLength, setAiLength] = useState("medium");
  const [aiLoading, setAiLoading] = useState(false);

  const handleChange = (field: keyof ContentCreate, value: unknown) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const generateScript = async () => {
    if (!aiTopic.trim()) return;
    setAiLoading(true);
    try {
      const data = await api.post<{
        script_ja: string;
        script_ko: string;
      }>("/content/generate-script", {
        series: form.series,
        topic: aiTopic,
        tone: aiTone,
        length: aiLength,
      });
      setForm((prev) => ({
        ...prev,
        script_ja: data.script_ja,
        script_ko: data.script_ko,
      }));
    } catch {
      setError("AI 스크립트 생성에 실패했습니다.");
    } finally {
      setAiLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title) return;
    setSaving(true);
    try {
      const body = { ...form };
      if (!body.platform) delete body.platform;
      await api.post("/content", body);
      router.push("/content");
    } catch {
      setError("콘텐츠 생성에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppShell>
      <Link href="/content" className="text-sm text-naruu-600 hover:underline">&larr; 목록</Link>
      <h2 className="text-2xl font-bold text-gray-800 mt-2 mb-6">새 콘텐츠 등록</h2>

      <ErrorBanner message={error} />

      <form onSubmit={handleSubmit} className="max-w-3xl space-y-6">
        {/* Basic Info */}
        <div className="bg-white rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="font-semibold text-gray-700">기본 정보</h3>
          <div>
            <label className="block text-sm text-gray-600 mb-1">제목 *</label>
            <input
              type="text"
              value={form.title}
              onChange={(e) => handleChange("title", e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-naruu-500"
              placeholder="콘텐츠 제목"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">시리즈</label>
              <select
                value={form.series}
                onChange={(e) => handleChange("series", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-naruu-500"
              >
                {SERIES_OPTIONS.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">플랫폼</label>
              <select
                value={form.platform || ""}
                onChange={(e) =>
                  handleChange("platform", e.target.value || undefined)
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-naruu-500"
              >
                <option value="">미지정</option>
                {PLATFORM_OPTIONS.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">영상 URL</label>
              <input
                type="url"
                value={form.video_url || ""}
                onChange={(e) => handleChange("video_url", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-naruu-500"
                placeholder="https://..."
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">썸네일 URL</label>
              <input
                type="url"
                value={form.thumbnail_url || ""}
                onChange={(e) => handleChange("thumbnail_url", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-naruu-500"
                placeholder="https://..."
              />
            </div>
          </div>
        </div>

        {/* AI Script Generator */}
        <div className="bg-gradient-to-r from-violet-50 to-blue-50 rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="font-semibold text-violet-700">AI 스크립트 생성</h3>
          <div>
            <label className="block text-sm text-violet-600 mb-1">주제</label>
            <input
              type="text"
              value={aiTopic}
              onChange={(e) => setAiTopic(e.target.value)}
              className="w-full px-3 py-2 border border-violet-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-violet-400"
              placeholder="예: 대구 동성로 야경 투어, 피부과 시술 후기"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-violet-600 mb-1">톤</label>
              <select
                value={aiTone}
                onChange={(e) => setAiTone(e.target.value)}
                className="w-full px-3 py-2 border border-violet-200 rounded-lg text-sm outline-none"
              >
                <option value="friendly">친근한</option>
                <option value="professional">전문적인</option>
                <option value="casual">캐주얼 (SNS풍)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-violet-600 mb-1">길이</label>
              <select
                value={aiLength}
                onChange={(e) => setAiLength(e.target.value)}
                className="w-full px-3 py-2 border border-violet-200 rounded-lg text-sm outline-none"
              >
                <option value="short">짧게 (~1분)</option>
                <option value="medium">보통 (~3분)</option>
                <option value="long">길게 (~5분)</option>
              </select>
            </div>
          </div>
          <button
            type="button"
            onClick={generateScript}
            disabled={aiLoading || !aiTopic.trim()}
            className="w-full py-2 bg-violet-600 text-white rounded-lg text-sm hover:bg-violet-700 disabled:opacity-50 transition"
          >
            {aiLoading ? "AI 생성 중..." : "스크립트 자동 생성"}
          </button>
        </div>

        {/* Scripts */}
        <div className="bg-white rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="font-semibold text-gray-700">스크립트</h3>
          <div>
            <label className="block text-sm text-gray-600 mb-1">일본어 스크립트</label>
            <textarea
              value={form.script_ja || ""}
              onChange={(e) => handleChange("script_ja", e.target.value)}
              rows={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-naruu-500 font-mono"
              placeholder="日本語スクリプト..."
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">한국어 스크립트</label>
            <textarea
              value={form.script_ko || ""}
              onChange={(e) => handleChange("script_ko", e.target.value)}
              rows={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-naruu-500 font-mono"
              placeholder="한국어 스크립트..."
            />
          </div>
        </div>

        {/* Submit */}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={saving || !form.title}
            className="px-6 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 text-sm font-medium disabled:opacity-50 transition"
          >
            {saving ? "저장 중..." : "콘텐츠 등록 (초안)"}
          </button>
          <Link
            href="/content"
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 text-sm transition"
          >
            취소
          </Link>
        </div>
      </form>
    </AppShell>
  );
}
