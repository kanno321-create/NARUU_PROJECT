"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { Partner, PartnerListResponse, PartnerStats } from "@/lib/types";
import { PARTNER_TYPE_LABELS, PARTNER_TYPE_COLORS } from "@/lib/constants";
import Pagination from "@/components/ui/pagination";
import LoadingSpinner from "@/components/ui/loading-spinner";
import ErrorBanner from "@/components/ui/error-banner";
import SearchFilter from "@/components/ui/search-filter";

export default function PartnersPage() {
  const [partners, setPartners] = useState<Partner[]>([]);
  const [stats, setStats] = useState<PartnerStats | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [activeFilter, setActiveFilter] = useState<string>("");
  const [search, setSearch] = useState("");

  const perPage = 20;

  useEffect(() => { loadStats(); }, []);
  useEffect(() => { loadPartners(); }, [page, typeFilter, activeFilter, search]);

  async function loadStats() {
    try {
      const data = await api.get<PartnerStats>("/partners/stats");
      setStats(data);
    } catch {
      setError("통계를 불러오는데 실패했습니다.");
    }
  }

  async function loadPartners() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("per_page", String(perPage));
      if (typeFilter) params.set("type", typeFilter);
      if (activeFilter === "active") params.set("is_active", "true");
      if (activeFilter === "inactive") params.set("is_active", "false");
      if (search) params.set("search", search);

      const data = await api.get<PartnerListResponse>(`/partners?${params}`);
      setPartners(data.items);
      setTotal(data.total);
      setError(null);
    } catch {
      setError("제휴처를 불러오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  const totalPages = Math.ceil(total / perPage);

  function contractStatus(p: Partner) {
    if (!p.contract_end) return null;
    const end = new Date(p.contract_end);
    const now = new Date();
    const daysLeft = Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    if (daysLeft < 0) return { text: "만료", color: "text-red-600 bg-red-50" };
    if (daysLeft <= 30) return { text: `${daysLeft}일 남음`, color: "text-yellow-600 bg-yellow-50" };
    return { text: `~${p.contract_end}`, color: "text-gray-500 bg-gray-50" };
  }

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">제휴 병원/업체</h2>
        <Link
          href="/partners/new"
          className="px-4 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 transition text-sm font-medium"
        >
          + 제휴처 등록
        </Link>
      </div>

      <ErrorBanner message={error} />

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <p className="text-xs text-gray-500 mb-1">전체</p>
            <p className="text-2xl font-bold text-gray-800">{stats.total}</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <p className="text-xs text-gray-500 mb-1">활성</p>
            <p className="text-2xl font-bold text-green-600">{stats.active}</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <p className="text-xs text-gray-500 mb-1">비활성</p>
            <p className="text-2xl font-bold text-gray-400">{stats.inactive}</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <p className="text-xs text-gray-500 mb-1">계약 만료 임박</p>
            <p className="text-2xl font-bold text-yellow-600">{stats.expiring_soon}</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <p className="text-xs text-gray-500 mb-1">병원/클리닉</p>
            <p className="text-2xl font-bold text-red-600">
              {(stats.by_type.hospital || 0) + (stats.by_type.clinic || 0)}
            </p>
          </div>
        </div>
      )}

      <SearchFilter
        searchValue={search}
        onSearch={(v) => { setSearch(v); setPage(1); }}
        placeholder="업체명 검색..."
        filters={[
          {
            value: typeFilter,
            onChange: (v) => { setTypeFilter(v); setPage(1); },
            options: [
              { value: "hospital", label: "병원" },
              { value: "clinic", label: "클리닉" },
              { value: "restaurant", label: "레스토랑" },
              { value: "hotel", label: "호텔" },
              { value: "shop", label: "샵" },
            ],
            placeholder: "전체 유형",
            ariaLabel: "유형 필터",
          },
          {
            value: activeFilter,
            onChange: (v) => { setActiveFilter(v); setPage(1); },
            options: [
              { value: "active", label: "활성" },
              { value: "inactive", label: "비활성" },
            ],
            placeholder: "전체 상태",
            ariaLabel: "상태 필터",
          },
        ]}
      />

      {/* Partners List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full"><LoadingSpinner /></div>
        ) : partners.length === 0 ? (
          <div className="col-span-full text-center py-8 text-gray-400">등록된 제휴처가 없습니다.</div>
        ) : (
          partners.map((p) => {
            const cs = contractStatus(p);
            return (
              <Link
                key={p.id}
                href={`/partners/${p.id}`}
                className="bg-white rounded-xl p-5 shadow-sm hover:shadow-md transition block"
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="font-semibold text-gray-800">{p.name_ko}</h3>
                    {p.name_ja && <p className="text-xs text-gray-400">{p.name_ja}</p>}
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${PARTNER_TYPE_COLORS[p.type]}`}>
                    {PARTNER_TYPE_LABELS[p.type]}
                  </span>
                </div>

                {p.address && <p className="text-xs text-gray-500 mb-2">{p.address}</p>}

                <div className="flex items-center gap-3 text-xs text-gray-500 mt-3">
                  {p.commission_rate !== null && (
                    <span className="font-medium text-naruu-600">커미션 {p.commission_rate}%</span>
                  )}
                  {p.contact_person && <span>{p.contact_person}</span>}
                  {!p.is_active && (
                    <span className="px-1.5 py-0.5 rounded bg-gray-100 text-gray-400">비활성</span>
                  )}
                </div>

                {cs && (
                  <div className="mt-2">
                    <span className={`text-xs px-2 py-0.5 rounded ${cs.color}`}>{cs.text}</span>
                  </div>
                )}
              </Link>
            );
          })
        )}
      </div>

      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} total={total} perPage={perPage} unit="개" />
    </AppShell>
  );
}
