"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { CustomerDetail, JourneyEvent } from "@/lib/types";

const EVENT_ICONS: Record<string, string> = {
  reservation: "📅",
  order: "💰",
  review: "⭐",
  line_message: "💬",
};

const EVENT_COLORS: Record<string, string> = {
  reservation: "border-blue-400",
  order: "border-green-400",
  review: "border-yellow-400",
  line_message: "border-purple-400",
};

export default function CustomerDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [customer, setCustomer] = useState<CustomerDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await api.get<CustomerDetail>(
          `/customers/${params.id}`
        );
        setCustomer(data);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "고객 정보를 불러올 수 없습니다"
        );
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [params.id]);

  const handleDelete = async () => {
    if (!confirm("정말 이 고객을 삭제하시겠습니까?")) return;
    try {
      await api.delete(`/customers/${params.id}`);
      router.push("/customers");
    } catch (err) {
      alert("삭제 실패");
    }
  };

  if (loading) {
    return (
      <AppShell>
        <div className="text-center py-12 text-gray-400">로딩 중...</div>
      </AppShell>
    );
  }

  if (error || !customer) {
    return (
      <AppShell>
        <div className="text-center py-12 text-red-500">{error}</div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <Link
            href="/customers"
            className="text-sm text-gray-500 hover:text-naruu-600"
          >
            &larr; 고객 목록
          </Link>
          <h2 className="text-2xl font-bold text-gray-800 mt-1">
            {customer.name_ja}
            {customer.name_ko && (
              <span className="text-lg text-gray-500 ml-2">
                ({customer.name_ko})
              </span>
            )}
          </h2>
        </div>
        <div className="flex gap-2">
          <Link
            href={`/customers/${customer.id}/edit`}
            className="px-4 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 transition text-sm"
          >
            수정
          </Link>
          <button
            onClick={handleDelete}
            className="px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition text-sm"
          >
            삭제
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Customer Info */}
        <div className="lg:col-span-1 space-y-4">
          {/* Profile Card */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-3">기본 정보</h3>
            <dl className="space-y-2 text-sm">
              <InfoRow label="국적" value={customer.nationality} />
              <InfoRow label="언어" value={customer.preferred_language} />
              <InfoRow label="이메일" value={customer.email} />
              <InfoRow label="전화번호" value={customer.phone} />
              <InfoRow label="LINE ID" value={customer.line_user_id} />
              <InfoRow label="비자" value={customer.visa_type} />
              <InfoRow
                label="첫 방문일"
                value={
                  customer.first_visit_date
                    ? new Date(customer.first_visit_date).toLocaleDateString("ko-KR")
                    : null
                }
              />
            </dl>

            {customer.tags && customer.tags.length > 0 && (
              <div className="mt-4 pt-3 border-t border-gray-100">
                <p className="text-xs text-gray-500 mb-2">태그</p>
                <div className="flex flex-wrap gap-1">
                  {customer.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 bg-naruu-50 text-naruu-700 rounded text-xs"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {customer.notes && (
              <div className="mt-4 pt-3 border-t border-gray-100">
                <p className="text-xs text-gray-500 mb-1">메모</p>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                  {customer.notes}
                </p>
              </div>
            )}
          </div>

          {/* Stats Card */}
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-3">통계</h3>
            <div className="grid grid-cols-2 gap-3">
              <StatBox label="총 주문" value={customer.stats.total_orders} />
              <StatBox
                label="총 매출"
                value={`¥${customer.stats.total_revenue.toLocaleString()}`}
              />
              <StatBox label="예약" value={customer.stats.total_reservations} />
              <StatBox label="리뷰" value={customer.stats.total_reviews} />
              <StatBox
                label="LINE 메시지"
                value={customer.stats.total_messages}
              />
            </div>
          </div>
        </div>

        {/* Journey Timeline */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl p-5 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-4">
              고객 여정 타임라인
            </h3>

            {customer.journey.length === 0 ? (
              <p className="text-gray-400 text-sm py-4">
                아직 기록된 이벤트가 없습니다
              </p>
            ) : (
              <div className="space-y-0">
                {customer.journey.map((event, idx) => (
                  <TimelineItem
                    key={`${event.event_type}-${event.id}`}
                    event={event}
                    isLast={idx === customer.journey.length - 1}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function InfoRow({
  label,
  value,
}: {
  label: string;
  value: string | null | undefined;
}) {
  return (
    <div className="flex justify-between">
      <dt className="text-gray-500">{label}</dt>
      <dd className="text-gray-800 font-medium">{value || "-"}</dd>
    </div>
  );
}

function StatBox({
  label,
  value,
}: {
  label: string;
  value: number | string;
}) {
  return (
    <div className="text-center p-2 bg-gray-50 rounded-lg">
      <p className="text-lg font-bold text-gray-800">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  );
}

function TimelineItem({
  event,
  isLast,
}: {
  event: JourneyEvent;
  isLast: boolean;
}) {
  const icon = EVENT_ICONS[event.event_type] || "📌";
  const borderColor = EVENT_COLORS[event.event_type] || "border-gray-300";

  return (
    <div className="flex gap-3">
      {/* Timeline line + dot */}
      <div className="flex flex-col items-center">
        <div
          className={`w-8 h-8 rounded-full border-2 ${borderColor} bg-white flex items-center justify-center text-sm`}
        >
          {icon}
        </div>
        {!isLast && <div className="w-0.5 flex-1 bg-gray-200 my-1" />}
      </div>

      {/* Content */}
      <div className={`pb-4 flex-1 ${isLast ? "" : ""}`}>
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium text-gray-800">{event.title}</p>
          {event.status && (
            <span
              className={`text-xs px-1.5 py-0.5 rounded ${
                event.status === "completed" || event.status === "paid"
                  ? "bg-green-50 text-green-700"
                  : event.status === "cancelled" || event.status === "refunded"
                  ? "bg-red-50 text-red-600"
                  : "bg-yellow-50 text-yellow-700"
              }`}
            >
              {event.status}
            </span>
          )}
        </div>
        {event.description && (
          <p className="text-xs text-gray-500 mt-1 line-clamp-2">
            {event.description}
          </p>
        )}
        <p className="text-xs text-gray-400 mt-1">
          {new Date(event.date).toLocaleString("ko-KR")}
        </p>
      </div>
    </div>
  );
}
