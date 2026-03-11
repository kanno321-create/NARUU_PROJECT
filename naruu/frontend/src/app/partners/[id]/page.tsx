"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { Partner, PartnerPerformance, SettlementReport, PartnerType } from "@/lib/types";

const TYPE_LABELS: Record<PartnerType, string> = {
  hospital: "병원",
  clinic: "클리닉",
  restaurant: "레스토랑",
  hotel: "호텔",
  shop: "샵",
};

export default function PartnerDetailPage() {
  const params = useParams();
  const router = useRouter();
  const partnerId = params.id as string;

  const [partner, setPartner] = useState<Partner | null>(null);
  const [performance, setPerformance] = useState<PartnerPerformance | null>(null);
  const [settlement, setSettlement] = useState<SettlementReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [settlementYear, setSettlementYear] = useState(new Date().getFullYear());
  const [settlementMonth, setSettlementMonth] = useState(new Date().getMonth() + 1);
  const [loadingSettlement, setLoadingSettlement] = useState(false);

  useEffect(() => {
    loadData();
  }, [partnerId]);

  async function loadData() {
    try {
      const [p, perf] = await Promise.all([
        api.get<Partner>(`/partners/${partnerId}`),
        api.get<PartnerPerformance>(`/partners/${partnerId}/performance`),
      ]);
      setPartner(p);
      setPerformance(perf);
    } catch {
      router.push("/partners");
    } finally {
      setLoading(false);
    }
  }

  async function loadSettlement() {
    setLoadingSettlement(true);
    try {
      const data = await api.get<SettlementReport>(
        `/partners/${partnerId}/settlement?year=${settlementYear}&month=${settlementMonth}`
      );
      setSettlement(data);
    } catch (e) {
      alert("정산 조회 실패: " + (e instanceof Error ? e.message : "알 수 없는 오류"));
    } finally {
      setLoadingSettlement(false);
    }
  }

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center py-20 text-gray-400">로딩 중...</div>
      </AppShell>
    );
  }

  if (!partner) return null;

  const contractDaysLeft = partner.contract_end
    ? Math.ceil((new Date(partner.contract_end).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
    : null;

  return (
    <AppShell>
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.push("/partners")} className="text-gray-400 hover:text-gray-600">
          ← 목록
        </button>
        <h2 className="text-2xl font-bold text-gray-800">{partner.name_ko}</h2>
        {partner.name_ja && <span className="text-gray-400 text-sm">({partner.name_ja})</span>}
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${partner.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
          {partner.is_active ? "활성" : "비활성"}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Info + Performance */}
        <div className="lg:col-span-2 space-y-4">
          {/* Partner Info */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-700">기본 정보</h3>
              <button
                onClick={() => router.push(`/partners/${partnerId}/edit`)}
                className="text-sm text-naruu-600 hover:text-naruu-800"
              >
                수정
              </button>
            </div>
            <dl className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt className="text-gray-500">유형</dt>
                <dd className="font-medium">{TYPE_LABELS[partner.type]}</dd>
              </div>
              <div>
                <dt className="text-gray-500">커미션율</dt>
                <dd className="font-medium text-naruu-600">
                  {partner.commission_rate !== null ? `${partner.commission_rate}%` : "-"}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500">담당자</dt>
                <dd>{partner.contact_person || "-"}</dd>
              </div>
              <div>
                <dt className="text-gray-500">연락처</dt>
                <dd>{partner.phone || "-"}</dd>
              </div>
              <div className="col-span-2">
                <dt className="text-gray-500">주소</dt>
                <dd>{partner.address || "-"}</dd>
              </div>
              <div>
                <dt className="text-gray-500">계약 시작</dt>
                <dd>{partner.contract_start || "-"}</dd>
              </div>
              <div>
                <dt className="text-gray-500">계약 종료</dt>
                <dd>
                  {partner.contract_end || "-"}
                  {contractDaysLeft !== null && (
                    <span className={`ml-2 text-xs ${contractDaysLeft < 0 ? "text-red-500" : contractDaysLeft <= 30 ? "text-yellow-500" : "text-gray-400"}`}>
                      {contractDaysLeft < 0 ? "(만료)" : `(${contractDaysLeft}일 남음)`}
                    </span>
                  )}
                </dd>
              </div>
            </dl>
          </div>

          {/* Performance */}
          {performance && (
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <h3 className="font-semibold text-gray-700 mb-4">실적 현황</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-gray-800">{performance.total_reservations}</p>
                  <p className="text-xs text-gray-500">총 예약</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-gray-800">{performance.total_reviews}</p>
                  <p className="text-xs text-gray-500">총 리뷰</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-blue-600">
                    {performance.avg_sentiment !== null ? (performance.avg_sentiment * 100).toFixed(0) + "%" : "-"}
                  </p>
                  <p className="text-xs text-gray-500">감성점수 평균</p>
                </div>
                <div className="text-center p-3 bg-naruu-50 rounded-lg">
                  <p className="text-2xl font-bold text-naruu-700">
                    {performance.total_revenue.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500">총 매출</p>
                </div>
                <div className="text-center p-3 bg-orange-50 rounded-lg">
                  <p className="text-2xl font-bold text-orange-700">
                    {performance.total_commission.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500">총 커미션</p>
                </div>
              </div>
            </div>
          )}

          {/* Settlement Report */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-4">월별 정산 리포트</h3>
            <div className="flex gap-2 items-center mb-4">
              <select
                value={settlementYear}
                onChange={(e) => setSettlementYear(Number(e.target.value))}
                className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
              >
                {[2024, 2025, 2026].map((y) => (
                  <option key={y} value={y}>{y}년</option>
                ))}
              </select>
              <select
                value={settlementMonth}
                onChange={(e) => setSettlementMonth(Number(e.target.value))}
                className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
              >
                {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                  <option key={m} value={m}>{m}월</option>
                ))}
              </select>
              <button
                onClick={loadSettlement}
                disabled={loadingSettlement}
                className="px-4 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 disabled:opacity-50 transition text-sm"
              >
                {loadingSettlement ? "조회 중..." : "정산 조회"}
              </button>
            </div>

            {settlement && (
              <div>
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-lg font-bold">{settlement.total_orders}건</p>
                    <p className="text-xs text-gray-500">주문</p>
                  </div>
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <p className="text-lg font-bold text-blue-700">{settlement.total_revenue.toLocaleString()}</p>
                    <p className="text-xs text-gray-500">매출</p>
                  </div>
                  <div className="text-center p-3 bg-orange-50 rounded-lg">
                    <p className="text-lg font-bold text-orange-700">{settlement.total_commission.toLocaleString()}</p>
                    <p className="text-xs text-gray-500">커미션</p>
                  </div>
                </div>

                {settlement.items.length > 0 ? (
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-3 py-2 text-left">주문 ID</th>
                        <th className="px-3 py-2 text-left">고객 ID</th>
                        <th className="px-3 py-2 text-right">금액</th>
                        <th className="px-3 py-2 text-right">커미션율</th>
                        <th className="px-3 py-2 text-right">커미션</th>
                        <th className="px-3 py-2 text-left">일시</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {settlement.items.map((item) => (
                        <tr key={item.order_id}>
                          <td className="px-3 py-2 font-mono">#{item.order_id}</td>
                          <td className="px-3 py-2 font-mono">#{item.customer_id}</td>
                          <td className="px-3 py-2 text-right">{item.total_amount.toLocaleString()} {item.currency}</td>
                          <td className="px-3 py-2 text-right">{item.commission_rate}%</td>
                          <td className="px-3 py-2 text-right font-medium text-orange-600">{item.commission_amount.toLocaleString()}</td>
                          <td className="px-3 py-2 text-xs text-gray-500">{new Date(item.created_at).toLocaleDateString("ko-KR")}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="text-gray-400 text-sm text-center py-4">해당 기간 정산 내역이 없습니다.</p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right: Quick Actions */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-3">등록 정보</h3>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">ID</dt>
                <dd className="font-mono">#{partner.id}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">등록일</dt>
                <dd>{new Date(partner.created_at).toLocaleDateString("ko-KR")}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">수정일</dt>
                <dd>{new Date(partner.updated_at).toLocaleDateString("ko-KR")}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
