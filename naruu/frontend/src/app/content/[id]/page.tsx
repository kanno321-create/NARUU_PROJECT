"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { Content, ContentStatus } from "@/lib/types";
import { CONTENT_STATUS_LABELS, CONTENT_STATUS_COLORS, SERIES_LABELS } from "@/lib/constants";
import LoadingSpinner from "@/components/ui/loading-spinner";
import ErrorBanner from "@/components/ui/error-banner";

const WORKFLOW_STEPS: ContentStatus[] = [
  "draft",
  "review",
  "approved",
  "published",
];

// Actions available for each status
const ACTIONS: Record<ContentStatus, { action: string; label: string; color: string }[]> = {
  draft: [{ action: "request_review", label: "검토 요청", color: "bg-amber-500 hover:bg-amber-600" }],
  review: [
    { action: "approve", label: "승인", color: "bg-green-600 hover:bg-green-700" },
    { action: "reject", label: "반려", color: "bg-red-500 hover:bg-red-600" },
  ],
  approved: [{ action: "publish", label: "게시하기", color: "bg-blue-600 hover:bg-blue-700" }],
  published: [],
  rejected: [{ action: "revert_draft", label: "초안으로 되돌리기", color: "bg-gray-500 hover:bg-gray-600" }],
};

export default function ContentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [content, setContent] = useState<Content | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [makeLoading, setMakeLoading] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const data = await api.get<Content>(`/content/${params.id}`);
        setContent(data);
      } catch {
        router.push("/content");
      } finally {
        setLoading(false);
      }
    })();
  }, [params.id, router]);

  const handleWorkflowAction = async (action: string) => {
    if (!content) return;
    const comment =
      action === "reject"
        ? prompt("반려 사유를 입력하세요:")
        : undefined;

    if (action === "reject" && !comment) return;

    setActionLoading(true);
    try {
      const updated = await api.post<Content>(
        `/content/${content.id}/workflow`,
        { action, comment }
      );
      setContent(updated);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "워크플로우 처리에 실패했습니다.";
      setError(message);
    } finally {
      setActionLoading(false);
    }
  };

  const triggerMake = async (blueprint: string) => {
    if (!content) return;
    setMakeLoading(true);
    try {
      await api.post("/content/trigger-make", {
        content_id: content.id,
        blueprint,
      });
      setError(null);
      // Success notification could use a toast, but for now show nothing on success
    } catch {
      setError("Make.com 웹훅 트리거에 실패했습니다.");
    } finally {
      setMakeLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("이 콘텐츠를 삭제하시겠습니까?")) return;
    try {
      await api.delete(`/content/${params.id}`);
      router.push("/content");
    } catch {
      setError("삭제에 실패했습니다.");
    }
  };

  if (loading) {
    return (
      <AppShell>
        <LoadingSpinner text="콘텐츠 로딩 중..." />
      </AppShell>
    );
  }

  if (!content) return null;

  const currentStepIndex = WORKFLOW_STEPS.indexOf(content.status);
  const actions = ACTIONS[content.status] || [];

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <div>
          <Link href="/content" className="text-sm text-naruu-600 hover:underline">
            &larr; 콘텐츠 목록
          </Link>
          <h2 className="text-2xl font-bold text-gray-800 mt-1">{content.title}</h2>
          <div className="flex items-center gap-2 mt-1">
            <span className="px-2 py-0.5 bg-naruu-50 text-naruu-700 rounded text-xs">
              {SERIES_LABELS[content.series] || content.series}
            </span>
            <span
              className={`px-2 py-0.5 rounded text-xs font-medium ${CONTENT_STATUS_COLORS[content.status]}`}
            >
              {CONTENT_STATUS_LABELS[content.status]}
            </span>
          </div>
        </div>
        <button
          onClick={handleDelete}
          className="px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition text-sm"
        >
          삭제
        </button>
      </div>

      <ErrorBanner message={error} />

      {/* Workflow Progress */}
      <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
        <h3 className="font-semibold text-gray-700 text-sm mb-4">승인 워크플로우</h3>

        {/* Progress Bar */}
        <div className="flex items-center gap-2 mb-6">
          {WORKFLOW_STEPS.map((step, i) => {
            const isActive = i === currentStepIndex;
            const isComplete = i < currentStepIndex;
            const isRejected = content.status === "rejected";

            return (
              <div key={step} className="flex items-center flex-1">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                    isRejected && step === "review"
                      ? "bg-red-500 text-white"
                      : isComplete
                      ? "bg-green-500 text-white"
                      : isActive
                      ? "bg-naruu-600 text-white"
                      : "bg-gray-200 text-gray-500"
                  }`}
                >
                  {isComplete ? "✓" : i + 1}
                </div>
                <span
                  className={`ml-2 text-xs ${
                    isActive ? "text-naruu-700 font-semibold" : "text-gray-500"
                  }`}
                >
                  {CONTENT_STATUS_LABELS[step]}
                </span>
                {i < WORKFLOW_STEPS.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 mx-3 ${
                      isComplete ? "bg-green-500" : "bg-gray-200"
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* Action Buttons */}
        {actions.length > 0 && (
          <div className="flex gap-3">
            {actions.map((a) => (
              <button
                key={a.action}
                onClick={() => handleWorkflowAction(a.action)}
                disabled={actionLoading}
                className={`px-5 py-2 text-white rounded-lg text-sm font-medium transition disabled:opacity-50 ${a.color}`}
              >
                {actionLoading ? "처리 중..." : a.label}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Scripts */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-3">일본어 스크립트</h3>
            <div className="text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto font-mono">
              {content.script_ja || "스크립트가 없습니다"}
            </div>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-3">한국어 스크립트</h3>
            <div className="text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto font-mono">
              {content.script_ko || "스크립트가 없습니다"}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Info */}
          <div className="bg-white rounded-xl p-5 shadow-sm space-y-3 text-sm">
            <h3 className="font-semibold text-gray-700">정보</h3>
            <div className="flex justify-between">
              <span className="text-gray-500">플랫폼</span>
              <span className="font-medium">
                {content.platform
                  ? content.platform === "youtube"
                    ? "YouTube"
                    : content.platform === "instagram"
                    ? "Instagram"
                    : "TikTok"
                  : "미지정"}
              </span>
            </div>
            {content.video_url && (
              <div className="flex justify-between">
                <span className="text-gray-500">영상</span>
                <a
                  href={content.video_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-naruu-600 hover:underline truncate ml-2"
                >
                  링크
                </a>
              </div>
            )}
            {content.published_at && (
              <div className="flex justify-between">
                <span className="text-gray-500">게시일</span>
                <span>
                  {new Date(content.published_at).toLocaleDateString("ko-KR")}
                </span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-gray-500">등록일</span>
              <span>
                {new Date(content.created_at).toLocaleDateString("ko-KR")}
              </span>
            </div>
          </div>

          {/* Make.com Trigger */}
          <div className="bg-white rounded-xl p-5 shadow-sm space-y-3">
            <h3 className="font-semibold text-gray-700 text-sm">Make.com 자동화</h3>
            <p className="text-xs text-gray-400">
              스크립트를 Make.com 블루프린트로 전송하여 영상/브로슈어를 자동 생성합니다
            </p>
            <button
              onClick={() => triggerMake("story_video")}
              disabled={makeLoading || !content.script_ja}
              className="w-full py-2 bg-orange-500 text-white rounded-lg text-sm hover:bg-orange-600 disabled:opacity-50 transition"
            >
              {makeLoading ? "전송 중..." : "영상 생성 트리거"}
            </button>
            <button
              onClick={() => triggerMake("brochure")}
              disabled={makeLoading || !content.script_ja}
              className="w-full py-2 bg-teal-500 text-white rounded-lg text-sm hover:bg-teal-600 disabled:opacity-50 transition"
            >
              {makeLoading ? "전송 중..." : "브로슈어 생성 트리거"}
            </button>
          </div>

          {/* Performance */}
          {content.performance_metrics && (
            <div className="bg-white rounded-xl p-5 shadow-sm space-y-3">
              <h3 className="font-semibold text-gray-700 text-sm">성과 지표</h3>
              {Object.entries(content.performance_metrics).map(([k, v]) => (
                <div key={k} className="flex justify-between text-sm">
                  <span className="text-gray-500">{k}</span>
                  <span className="font-medium">{String(v)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
