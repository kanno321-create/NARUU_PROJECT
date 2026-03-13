"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { Review, ReviewPlatform } from "@/lib/types";
import { PLATFORM_LABELS, PLATFORM_COLORS } from "@/lib/constants";
import LoadingSpinner from "@/components/ui/loading-spinner";
import ErrorBanner from "@/components/ui/error-banner";

function sentimentDisplay(score: number | null) {
  if (score === null) return { label: "미분석", emoji: "❓", color: "text-gray-400", bg: "bg-gray-100" };
  if (score >= 0.7) return { label: "긍정적", emoji: "😊", color: "text-green-700", bg: "bg-green-50" };
  if (score >= 0.4) return { label: "중립적", emoji: "😐", color: "text-yellow-700", bg: "bg-yellow-50" };
  return { label: "부정적", emoji: "😞", color: "text-red-700", bg: "bg-red-50" };
}

export default function ReviewDetailPage() {
  const params = useParams();
  const router = useRouter();
  const reviewId = params.id as string;

  const [review, setReview] = useState<Review | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generatedResponse, setGeneratedResponse] = useState<string | null>(null);
  const [responseText, setResponseText] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadReview();
  }, [reviewId]);

  async function loadReview() {
    try {
      const data = await api.get<Review>(`/reviews/${reviewId}`);
      setReview(data);
      if (data.response_text) setResponseText(data.response_text);
    } catch {
      router.push("/reviews");
    } finally {
      setLoading(false);
    }
  }

  async function handleAnalyze() {
    setAnalyzing(true);
    try {
      const updated = await api.post<Review>(`/reviews/${reviewId}/analyze`);
      setReview(updated);
    } catch (e) {
      setError("감성 분석 실패: " + (e instanceof Error ? e.message : "알 수 없는 오류"));
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleGenerateResponse() {
    setGenerating(true);
    try {
      const data = await api.post<{ response: string }>(`/reviews/${reviewId}/generate-response`);
      setGeneratedResponse(data.response);
      setResponseText(data.response);
    } catch (e) {
      setError("응답 생성 실패: " + (e instanceof Error ? e.message : "알 수 없는 오류"));
    } finally {
      setGenerating(false);
    }
  }

  async function handleSaveResponse() {
    if (!responseText.trim()) return;
    setSaving(true);
    try {
      const updated = await api.put<Review>(`/reviews/${reviewId}`, {
        response_text: responseText,
      });
      setReview(updated);
      setGeneratedResponse(null);
    } catch (e) {
      setError("저장 실패: " + (e instanceof Error ? e.message : "알 수 없는 오류"));
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <AppShell>
        <LoadingSpinner text="리뷰 로딩 중..." />
      </AppShell>
    );
  }

  if (!review) return null;

  const sentiment = sentimentDisplay(review.sentiment_score);

  return (
    <AppShell>
      <div className="flex items-center gap-3 mb-6">
        <Link href="/reviews" className="text-gray-400 hover:text-gray-600">
          &larr; 목록
        </Link>
        <h2 className="text-2xl font-bold text-gray-800">리뷰 상세</h2>
        <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${PLATFORM_COLORS[review.platform]}`}>
          {PLATFORM_LABELS[review.platform]}
        </span>
      </div>

      <ErrorBanner message={error} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Review Content */}
        <div className="lg:col-span-2 space-y-4">
          {/* Review Content Card */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-700">리뷰 내용</h3>
              {review.rating && (
                <span className="text-yellow-500 font-bold text-lg">{review.rating.toFixed(1)} <span aria-hidden="true">★</span></span>
              )}
            </div>

            {review.content_ja && (
              <div className="mb-4">
                <p className="text-xs text-gray-400 mb-1">일본어</p>
                <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{review.content_ja}</p>
              </div>
            )}
            {review.content_ko && (
              <div>
                <p className="text-xs text-gray-400 mb-1">한국어</p>
                <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{review.content_ko}</p>
              </div>
            )}
            {!review.content_ja && !review.content_ko && (
              <p className="text-gray-400">리뷰 내용이 없습니다.</p>
            )}
          </div>

          {/* Response Section */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-700">응답</h3>
              {review.responded_at && (
                <span className="text-xs text-gray-400">
                  응답일: {new Date(review.responded_at).toLocaleDateString("ko-KR")}
                </span>
              )}
            </div>

            {/* AI Generate Button */}
            <div className="mb-4">
              <button
                onClick={handleGenerateResponse}
                disabled={generating || (!review.content_ja && !review.content_ko)}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition text-sm font-medium"
              >
                {generating ? "AI 생성 중..." : "AI 응답 생성"}
              </button>
              {generatedResponse && (
                <p className="text-xs text-purple-500 mt-1">AI가 생성한 응답입니다. 수정 후 저장하세요.</p>
              )}
            </div>

            {/* Response Text */}
            <textarea
              value={responseText}
              onChange={(e) => setResponseText(e.target.value)}
              rows={6}
              aria-label="리뷰 응답 내용"
              placeholder="리뷰에 대한 응답을 입력하세요..."
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 focus:border-transparent resize-y"
            />

            <div className="flex justify-end mt-3">
              <button
                onClick={handleSaveResponse}
                disabled={saving || !responseText.trim()}
                className="px-4 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 disabled:opacity-50 transition text-sm font-medium"
              >
                {saving ? "저장 중..." : "응답 저장"}
              </button>
            </div>
          </div>
        </div>

        {/* Right: Sidebar Info */}
        <div className="space-y-4">
          {/* Sentiment Card */}
          <div className={`rounded-xl p-6 shadow-sm ${sentiment.bg}`}>
            <h3 className="font-semibold text-gray-700 mb-3">AI 감성 분석</h3>
            <div className="text-center py-4">
              <span className="text-5xl" aria-hidden="true">{sentiment.emoji}</span>
              <p className={`text-lg font-bold mt-2 ${sentiment.color}`}>{sentiment.label}</p>
              {review.sentiment_score !== null && (
                <>
                  <p className="text-3xl font-bold text-gray-800 mt-1">
                    {(review.sentiment_score * 100).toFixed(0)}%
                  </p>
                  <div className="w-full h-3 bg-white/50 rounded-full mt-3 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        review.sentiment_score >= 0.7
                          ? "bg-green-500"
                          : review.sentiment_score >= 0.4
                          ? "bg-yellow-500"
                          : "bg-red-500"
                      }`}
                      style={{ width: `${review.sentiment_score * 100}%` }}
                    />
                  </div>
                </>
              )}
            </div>

            <button
              onClick={handleAnalyze}
              disabled={analyzing || (!review.content_ja && !review.content_ko)}
              className="w-full mt-3 px-4 py-2 bg-white text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition text-sm font-medium border border-gray-200"
            >
              {analyzing ? "분석 중..." : review.sentiment_score !== null ? "재분석" : "감성 분석 실행"}
            </button>
          </div>

          {/* Meta Info Card */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-3">정보</h3>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">ID</dt>
                <dd className="font-mono text-gray-700">#{review.id}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">플랫폼</dt>
                <dd>{PLATFORM_LABELS[review.platform]}</dd>
              </div>
              {review.customer_id && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">고객 ID</dt>
                  <dd className="font-mono">#{review.customer_id}</dd>
                </div>
              )}
              {review.partner_id && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">제휴처 ID</dt>
                  <dd className="font-mono">#{review.partner_id}</dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-gray-500">공개 여부</dt>
                <dd>{review.is_published ? "공개" : "비공개"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">등록일</dt>
                <dd>{new Date(review.created_at).toLocaleDateString("ko-KR")}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">수정일</dt>
                <dd>{new Date(review.updated_at).toLocaleDateString("ko-KR")}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
