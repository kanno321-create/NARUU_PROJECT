"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { Customer, CustomerListResponse } from "@/lib/types";
import Pagination from "@/components/ui/pagination";
import LoadingSpinner from "@/components/ui/loading-spinner";
import ErrorBanner from "@/components/ui/error-banner";
import SearchFilter from "@/components/ui/search-filter";

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCustomers = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("per_page", "20");
      if (search) params.set("search", search);
      if (tagFilter) params.set("tag", tagFilter);

      const data = await api.get<CustomerListResponse>(
        `/customers?${params.toString()}`
      );
      setCustomers(data.items);
      setTotal(data.total);
      setError(null);
    } catch {
      setError("데이터를 불러오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }, [page, search, tagFilter]);

  useEffect(() => {
    fetchCustomers();
  }, [fetchCustomers]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const totalPages = Math.ceil(total / 20);

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">고객 관리</h2>
        <Link
          href="/customers/new"
          className="px-4 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 transition text-sm font-medium"
        >
          + 신규 고객
        </Link>
      </div>

      <ErrorBanner message={error} />

      <SearchFilter
        searchValue={searchInput}
        onSearch={setSearchInput}
        placeholder="이름, 이메일, LINE ID, 전화번호 검색..."
        filters={[
          {
            value: tagFilter,
            onChange: (v) => { setTagFilter(v); setPage(1); },
            options: [
              { value: "VIP", label: "VIP" },
              { value: "리피터", label: "리피터" },
              { value: "성형", label: "성형" },
              { value: "피부과", label: "피부과" },
              { value: "관광", label: "관광" },
              { value: "굿즈", label: "굿즈" },
            ],
            placeholder: "전체 태그",
            ariaLabel: "태그 필터",
          },
        ]}
      />

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">이름 (JP)</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">이름 (KR)</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">LINE ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">연락처</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">태그</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">등록일</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6}><LoadingSpinner /></td>
              </tr>
            ) : customers.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-8 text-gray-400">
                  {search || tagFilter ? "검색 결과가 없습니다" : "등록된 고객이 없습니다"}
                </td>
              </tr>
            ) : (
              customers.map((c) => (
                <tr key={c.id} className="border-b border-gray-100 hover:bg-gray-50 transition">
                  <td className="px-4 py-3">
                    <Link href={`/customers/${c.id}`} className="text-naruu-600 hover:underline font-medium">
                      {c.name_ja}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{c.name_ko || "-"}</td>
                  <td className="px-4 py-3 text-gray-500 font-mono text-xs">{c.line_user_id || "-"}</td>
                  <td className="px-4 py-3 text-gray-600">{c.phone || c.email || "-"}</td>
                  <td className="px-4 py-3">
                    {c.tags?.map((tag) => (
                      <span key={tag} className="inline-block px-2 py-0.5 bg-naruu-50 text-naruu-700 rounded text-xs mr-1">{tag}</span>
                    ))}
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">
                    {new Date(c.created_at).toLocaleDateString("ko-KR")}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        <Pagination page={page} totalPages={totalPages} onPageChange={setPage} total={total} unit="명" />
      </div>
    </AppShell>
  );
}
