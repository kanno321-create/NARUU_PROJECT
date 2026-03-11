"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { Customer, CustomerListResponse } from "@/lib/types";

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchCustomers = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("page_size", "20");
      if (search) params.set("search", search);
      if (tagFilter) params.set("tag", tagFilter);

      const data = await api.get<CustomerListResponse>(
        `/customers?${params.toString()}`
      );
      setCustomers(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to fetch customers:", err);
    } finally {
      setLoading(false);
    }
  }, [page, search, tagFilter]);

  useEffect(() => {
    fetchCustomers();
  }, [fetchCustomers]);

  // Debounced search
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

      {/* Search & Filter */}
      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder="이름, 이메일, LINE ID, 전화번호 검색..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-naruu-500 focus:border-naruu-500 outline-none text-sm"
        />
        <select
          value={tagFilter}
          onChange={(e) => {
            setTagFilter(e.target.value);
            setPage(1);
          }}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 outline-none"
        >
          <option value="">전체 태그</option>
          <option value="VIP">VIP</option>
          <option value="리피터">리피터</option>
          <option value="성형">성형</option>
          <option value="피부과">피부과</option>
          <option value="관광">관광</option>
          <option value="굿즈">굿즈</option>
        </select>
      </div>

      {/* Customer Table */}
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
                <td colSpan={6} className="text-center py-8 text-gray-400">
                  로딩 중...
                </td>
              </tr>
            ) : customers.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-8 text-gray-400">
                  {search || tagFilter
                    ? "검색 결과가 없습니다"
                    : "등록된 고객이 없습니다"}
                </td>
              </tr>
            ) : (
              customers.map((c) => (
                <tr
                  key={c.id}
                  className="border-b border-gray-100 hover:bg-gray-50 transition"
                >
                  <td className="px-4 py-3">
                    <Link
                      href={`/customers/${c.id}`}
                      className="text-naruu-600 hover:underline font-medium"
                    >
                      {c.name_ja}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {c.name_ko || "-"}
                  </td>
                  <td className="px-4 py-3 text-gray-500 font-mono text-xs">
                    {c.line_user_id || "-"}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {c.phone || c.email || "-"}
                  </td>
                  <td className="px-4 py-3">
                    {c.tags?.map((tag) => (
                      <span
                        key={tag}
                        className="inline-block px-2 py-0.5 bg-naruu-50 text-naruu-700 rounded text-xs mr-1"
                      >
                        {tag}
                      </span>
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

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
            <span className="text-xs text-gray-500">
              총 {total}명 중 {(page - 1) * 20 + 1}-
              {Math.min(page * 20, total)}명
            </span>
            <div className="flex gap-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
              >
                이전
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
              >
                다음
              </button>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
