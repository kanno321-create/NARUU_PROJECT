"use client";

import React, { useState, useEffect, useCallback } from "react";
import { api, ERPTaxInvoice, ERPTaxInvoiceCreate, UnissuedCustomer } from "@/lib/api";

type ViewMode = "list" | "bulk-register";

export function SalesTaxInvoice() {
  // 기간 필터 (현재 월 기본값)
  const now = new Date();
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
  const [startDate, setStartDate] = useState(firstDay.toISOString().slice(0, 10));
  const [endDate, setEndDate] = useState(now.toISOString().slice(0, 10));

  // 데이터
  const [invoices, setInvoices] = useState<ERPTaxInvoice[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // 일괄등록 모드
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [unissuedCustomers, setUnissuedCustomers] = useState<UnissuedCustomer[]>([]);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [bulkSelectedIds, setBulkSelectedIds] = useState<Set<string>>(new Set());
  const [bulkIssueDate, setBulkIssueDate] = useState(now.toISOString().slice(0, 10));
  const [bulkProcessing, setBulkProcessing] = useState(false);

  // 필터
  const [customerFilter, setCustomerFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("전체");

  // 상태 메시지
  const [statusMsg, setStatusMsg] = useState("조회 대기 중");

  // 세금계산서 목록 조회
  const fetchInvoices = useCallback(async () => {
    setLoading(true);
    setStatusMsg("조회 중...");
    try {
      const res = await api.erp.taxInvoices.list({
        start_date: startDate,
        end_date: endDate,
        limit: 100,
      });
      const items = res.items ?? [];
      setInvoices(items);
      setSelectedIds(new Set());
      setStatusMsg(`총 ${items.length}건 조회 완료`);
    } catch (err) {
      console.error("세금계산서 조회 실패:", err);
      setInvoices([]);
      setStatusMsg("조회 실패");
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  // 첫 로드 시 조회
  useEffect(() => {
    fetchInvoices();
  }, [fetchInvoices]);

  // 필터링
  const filteredInvoices = invoices.filter((inv) => {
    const nameMatch =
      customerFilter === "" ||
      (inv.customer?.name ?? "").includes(customerFilter);
    const statusMatch =
      statusFilter === "전체" || inv.status === statusFilter;
    return nameMatch && statusMatch;
  });

  // 합계
  const totals = filteredInvoices.reduce(
    (acc, inv) => ({
      supply: acc.supply + inv.supply_amount,
      tax: acc.tax + inv.tax_amount,
      total: acc.total + inv.total_amount,
    }),
    { supply: 0, tax: 0, total: 0 }
  );

  // 행 선택 토글
  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // 전체 선택/해제
  const toggleSelectAll = () => {
    if (selectedIds.size === filteredInvoices.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredInvoices.map((inv) => inv.id)));
    }
  };

  // 삭제
  const handleDelete = async () => {
    if (selectedIds.size === 0) return;
    if (!confirm(`선택한 ${selectedIds.size}건의 세금계산서를 삭제하시겠습니까?`)) return;

    setStatusMsg(`삭제 중... (0/${selectedIds.size})`);
    let deleted = 0;
    let failed = 0;

    for (const id of selectedIds) {
      try {
        await api.erp.taxInvoices.delete(id);
        deleted++;
      } catch {
        failed++;
      }
      setStatusMsg(`삭제 중... (${deleted + failed}/${selectedIds.size})`);
    }

    setStatusMsg(`삭제 완료: ${deleted}건 성공${failed > 0 ? `, ${failed}건 실패` : ""}`);
    fetchInvoices();
  };

  // --- 일괄등록 모드 ---

  // 미발행 거래처 조회
  const fetchUnissuedCustomers = useCallback(async () => {
    setBulkLoading(true);
    try {
      const res = await api.erp.taxInvoices.unissuedCustomers({
        start_date: startDate,
        end_date: endDate,
      });
      const items = res.items ?? [];
      setUnissuedCustomers(items);
      setBulkSelectedIds(new Set(items.map((c) => c.customer_id))); // 기본 전체 선택
    } catch (err) {
      console.error("미발행 거래처 조회 실패:", err);
      setUnissuedCustomers([]);
    } finally {
      setBulkLoading(false);
    }
  }, [startDate, endDate]);

  // 일괄등록 모드 진입 시 조회
  useEffect(() => {
    if (viewMode === "bulk-register") {
      fetchUnissuedCustomers();
    }
  }, [viewMode, fetchUnissuedCustomers]);

  // 일괄등록 전체 선택
  const toggleBulkSelectAll = () => {
    if (bulkSelectedIds.size === unissuedCustomers.length) {
      setBulkSelectedIds(new Set());
    } else {
      setBulkSelectedIds(new Set(unissuedCustomers.map((c) => c.customer_id)));
    }
  };

  // 일괄등록 행 토글
  const toggleBulkSelect = (customerId: string) => {
    setBulkSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(customerId)) next.delete(customerId);
      else next.add(customerId);
      return next;
    });
  };

  // 일괄 세금계산서 발행
  const handleBulkRegister = async () => {
    if (bulkSelectedIds.size === 0) return;
    if (
      !confirm(
        `선택한 ${bulkSelectedIds.size}개 거래처에 대해 세금계산서를 일괄 발행하시겠습니까?`
      )
    )
      return;

    setBulkProcessing(true);
    setStatusMsg(`일괄 발행 중... (0/${bulkSelectedIds.size})`);
    let success = 0;
    let failed = 0;

    for (const customerId of bulkSelectedIds) {
      const customer = unissuedCustomers.find((c) => c.customer_id === customerId);
      if (!customer) continue;

      const data: ERPTaxInvoiceCreate = {
        invoice_type: "sales",
        issue_date: bulkIssueDate,
        customer_id: customerId,
        supply_amount: customer.total_supply_amount,
        tax_amount: customer.total_tax_amount,
        total_amount: customer.total_sales_amount,
        status: "issued",
        memo: `${startDate}~${endDate} 매출 일괄발행`,
      };

      try {
        await api.erp.taxInvoices.create(data);
        success++;
      } catch {
        failed++;
      }
      setStatusMsg(`일괄 발행 중... (${success + failed}/${bulkSelectedIds.size})`);
    }

    setStatusMsg(`일괄 발행 완료: ${success}건 성공${failed > 0 ? `, ${failed}건 실패` : ""}`);
    setBulkProcessing(false);
    setViewMode("list");
    fetchInvoices();
  };

  // 일괄등록 미발행 거래처 합계
  const bulkTotals = unissuedCustomers
    .filter((c) => bulkSelectedIds.has(c.customer_id))
    .reduce(
      (acc, c) => ({
        supply: acc.supply + c.total_supply_amount,
        tax: acc.tax + c.total_tax_amount,
        total: acc.total + c.total_sales_amount,
        count: acc.count + 1,
      }),
      { supply: 0, tax: 0, total: 0, count: 0 }
    );

  // ===== 렌더링 =====

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">
          {viewMode === "list" ? "매출세금계산서" : "세금계산서 일괄등록"}
        </span>
        {viewMode === "bulk-register" && (
          <button
            onClick={() => setViewMode("list")}
            className="text-xs text-white/80 hover:text-white underline"
          >
            목록으로 돌아가기
          </button>
        )}
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        {viewMode === "list" ? (
          <>
            <button
              onClick={() => setViewMode("bulk-register")}
              className="flex items-center gap-1 rounded border border-blue-400 bg-blue-100 px-2 py-0.5 text-xs font-medium hover:bg-blue-200"
            >
              <span>📋</span> 일괄등록
            </button>
            <div className="mx-2 h-4 w-px bg-gray-400" />
            <button
              onClick={handleDelete}
              disabled={selectedIds.size === 0}
              className={`flex items-center gap-1 rounded border px-2 py-0.5 text-xs ${
                selectedIds.size > 0
                  ? "border-red-400 bg-red-50 text-red-700 hover:bg-red-100"
                  : "border-gray-300 bg-gray-100 text-gray-400 cursor-not-allowed"
              }`}
            >
              <span>🗑️</span> 삭제 {selectedIds.size > 0 && `(${selectedIds.size})`}
            </button>
            <div className="mx-2 h-4 w-px bg-gray-400" />
            <button
              onClick={fetchInvoices}
              className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
            >
              <span>🔄</span> 새로고침
            </button>
          </>
        ) : (
          <>
            <button
              onClick={handleBulkRegister}
              disabled={bulkSelectedIds.size === 0 || bulkProcessing}
              className={`flex items-center gap-1 rounded border px-3 py-0.5 text-xs font-medium ${
                bulkSelectedIds.size > 0 && !bulkProcessing
                  ? "border-blue-400 bg-blue-500 text-white hover:bg-blue-600"
                  : "border-gray-300 bg-gray-100 text-gray-400 cursor-not-allowed"
              }`}
            >
              <span>✅</span> 선택 거래처 일괄발행 ({bulkSelectedIds.size}건)
            </button>
            <div className="mx-2 h-4 w-px bg-gray-400" />
            <div className="flex items-center gap-1 text-xs">
              <span>발행일:</span>
              <input
                type="date"
                value={bulkIssueDate}
                onChange={(e) => setBulkIssueDate(e.target.value)}
                className="rounded border border-gray-400 px-2 py-0.5 text-xs"
              />
            </div>
          </>
        )}
      </div>

      {/* 검색 조건 */}
      <div className="flex items-center gap-4 border-b bg-white px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium">기간:</span>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          />
          <span className="text-xs">~</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          />
        </div>
        {viewMode === "list" && (
          <>
            <div className="flex items-center gap-2">
              <span className="text-xs">거래처:</span>
              <input
                type="text"
                value={customerFilter}
                onChange={(e) => setCustomerFilter(e.target.value)}
                placeholder="거래처명"
                className="rounded border border-gray-400 px-2 py-1 text-xs w-32"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs">상태:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="rounded border border-gray-400 px-2 py-1 text-xs"
              >
                <option value="전체">전체</option>
                <option value="draft">작성</option>
                <option value="issued">발행</option>
                <option value="cancelled">취소</option>
              </select>
            </div>
            <button
              onClick={fetchInvoices}
              className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200"
            >
              검 색(F)
            </button>
          </>
        )}
        {viewMode === "bulk-register" && (
          <button
            onClick={fetchUnissuedCustomers}
            className="rounded border border-blue-400 bg-blue-50 px-4 py-1 text-xs text-blue-700 hover:bg-blue-100"
          >
            미발행 거래처 조회
          </button>
        )}
      </div>

      {/* === 목록 모드 === */}
      {viewMode === "list" && (
        <>
          {/* 그리드 */}
          <div className="flex-1 overflow-auto">
            <table className="w-full border-collapse text-xs">
              <thead className="sticky top-0 bg-[#E8E4D9]">
                <tr>
                  <th className="border border-gray-400 px-1 py-1 w-8">
                    <input
                      type="checkbox"
                      checked={selectedIds.size === filteredInvoices.length && filteredInvoices.length > 0}
                      onChange={toggleSelectAll}
                    />
                  </th>
                  <th className="border border-gray-400 px-2 py-1 w-28">계산서번호</th>
                  <th className="border border-gray-400 px-2 py-1 w-24">발급일자</th>
                  <th className="border border-gray-400 px-2 py-1">거래처명</th>
                  <th className="border border-gray-400 px-2 py-1 w-28">공급가액</th>
                  <th className="border border-gray-400 px-2 py-1 w-24">세액</th>
                  <th className="border border-gray-400 px-2 py-1 w-28">합계금액</th>
                  <th className="border border-gray-400 px-2 py-1 w-20">상태</th>
                  <th className="border border-gray-400 px-2 py-1">비고</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={9} className="border border-gray-300 px-4 py-8 text-center text-gray-500">
                      조회 중...
                    </td>
                  </tr>
                ) : filteredInvoices.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="border border-gray-300 px-4 py-8 text-center text-gray-500">
                      조회된 세금계산서가 없습니다.
                    </td>
                  </tr>
                ) : (
                  filteredInvoices.map((inv) => (
                    <tr
                      key={inv.id}
                      className={`cursor-pointer ${
                        selectedIds.has(inv.id)
                          ? "bg-[#316AC5] text-white"
                          : inv.status === "cancelled"
                          ? "bg-red-50 hover:bg-red-100"
                          : "hover:bg-gray-100"
                      }`}
                      onClick={() => toggleSelect(inv.id)}
                    >
                      <td className="border border-gray-300 px-1 py-1 text-center">
                        <input
                          type="checkbox"
                          checked={selectedIds.has(inv.id)}
                          onChange={() => toggleSelect(inv.id)}
                          onClick={(e) => e.stopPropagation()}
                        />
                      </td>
                      <td className="border border-gray-300 px-2 py-1 font-medium">
                        {inv.invoice_number ?? "-"}
                      </td>
                      <td className="border border-gray-300 px-2 py-1">{inv.issue_date}</td>
                      <td className="border border-gray-300 px-2 py-1">
                        {inv.customer?.name ?? "-"}
                      </td>
                      <td
                        className={`border border-gray-300 px-2 py-1 text-right ${
                          selectedIds.has(inv.id) ? "" : "text-blue-600"
                        }`}
                      >
                        {inv.supply_amount.toLocaleString()}
                      </td>
                      <td
                        className={`border border-gray-300 px-2 py-1 text-right ${
                          selectedIds.has(inv.id) ? "" : "text-red-600"
                        }`}
                      >
                        {inv.tax_amount.toLocaleString()}
                      </td>
                      <td className="border border-gray-300 px-2 py-1 text-right font-medium">
                        {inv.total_amount.toLocaleString()}
                      </td>
                      <td
                        className={`border border-gray-300 px-2 py-1 text-center ${
                          selectedIds.has(inv.id)
                            ? ""
                            : inv.status === "issued"
                            ? "text-green-600"
                            : inv.status === "cancelled"
                            ? "text-red-600"
                            : "text-gray-600"
                        }`}
                      >
                        {inv.status === "issued"
                          ? "발행"
                          : inv.status === "cancelled"
                          ? "취소"
                          : "작성"}
                      </td>
                      <td className="border border-gray-300 px-2 py-1">{inv.memo ?? ""}</td>
                    </tr>
                  ))
                )}
                {/* 합계 행 */}
                {filteredInvoices.length > 0 && (
                  <tr className="bg-gray-200 font-medium">
                    <td className="border border-gray-400 px-2 py-1" colSpan={4}>
                      (합계: {filteredInvoices.length}건)
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                      {totals.supply.toLocaleString()}
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                      {totals.tax.toLocaleString()}
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-right">
                      {totals.total.toLocaleString()}
                    </td>
                    <td className="border border-gray-400 px-2 py-1" colSpan={2}></td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* === 일괄등록 모드 === */}
      {viewMode === "bulk-register" && (
        <>
          {/* 안내 */}
          <div className="border-b bg-blue-50 px-3 py-2">
            <p className="text-xs text-blue-800">
              <strong>일괄등록 안내:</strong> 지정한 기간에 매출이력이 있으면서 세금계산서를 아직 발행하지 않은 거래처가 자동으로 표시됩니다.
              이미 세금계산서가 발행된 거래처는 표시되지 않습니다.
            </p>
          </div>

          {/* 미발행 거래처 그리드 */}
          <div className="flex-1 overflow-auto">
            <table className="w-full border-collapse text-xs">
              <thead className="sticky top-0 bg-[#E8E4D9]">
                <tr>
                  <th className="border border-gray-400 px-1 py-1 w-8">
                    <input
                      type="checkbox"
                      checked={bulkSelectedIds.size === unissuedCustomers.length && unissuedCustomers.length > 0}
                      onChange={toggleBulkSelectAll}
                    />
                  </th>
                  <th className="border border-gray-400 px-2 py-1">거래처명</th>
                  <th className="border border-gray-400 px-2 py-1 w-28">사업자번호</th>
                  <th className="border border-gray-400 px-2 py-1 w-20">대표자</th>
                  <th className="border border-gray-400 px-2 py-1 w-16">매출건수</th>
                  <th className="border border-gray-400 px-2 py-1 w-28">공급가액</th>
                  <th className="border border-gray-400 px-2 py-1 w-24">세액</th>
                  <th className="border border-gray-400 px-2 py-1 w-28">합계금액</th>
                </tr>
              </thead>
              <tbody>
                {bulkLoading ? (
                  <tr>
                    <td colSpan={8} className="border border-gray-300 px-4 py-8 text-center text-gray-500">
                      미발행 거래처 조회 중...
                    </td>
                  </tr>
                ) : unissuedCustomers.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="border border-gray-300 px-4 py-8 text-center text-gray-500">
                      해당 기간에 미발행 거래처가 없습니다. (모든 거래처에 세금계산서가 발행되었거나 매출이 없습니다)
                    </td>
                  </tr>
                ) : (
                  unissuedCustomers.map((cust) => (
                    <tr
                      key={cust.customer_id}
                      className={`cursor-pointer ${
                        bulkSelectedIds.has(cust.customer_id)
                          ? "bg-blue-100"
                          : "hover:bg-gray-100"
                      }`}
                      onClick={() => toggleBulkSelect(cust.customer_id)}
                    >
                      <td className="border border-gray-300 px-1 py-1 text-center">
                        <input
                          type="checkbox"
                          checked={bulkSelectedIds.has(cust.customer_id)}
                          onChange={() => toggleBulkSelect(cust.customer_id)}
                          onClick={(e) => e.stopPropagation()}
                        />
                      </td>
                      <td className="border border-gray-300 px-2 py-1 font-medium">
                        {cust.customer_name}
                      </td>
                      <td className="border border-gray-300 px-2 py-1">
                        {cust.business_number ?? "-"}
                      </td>
                      <td className="border border-gray-300 px-2 py-1">
                        {cust.representative ?? "-"}
                      </td>
                      <td className="border border-gray-300 px-2 py-1 text-center">
                        {cust.sale_count}건
                      </td>
                      <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">
                        {cust.total_supply_amount.toLocaleString()}
                      </td>
                      <td className="border border-gray-300 px-2 py-1 text-right text-red-600">
                        {cust.total_tax_amount.toLocaleString()}
                      </td>
                      <td className="border border-gray-300 px-2 py-1 text-right font-medium">
                        {cust.total_sales_amount.toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
                {/* 합계 행 */}
                {unissuedCustomers.length > 0 && (
                  <tr className="bg-gray-200 font-medium">
                    <td className="border border-gray-400 px-2 py-1" colSpan={4}>
                      선택: {bulkTotals.count}건 / 전체: {unissuedCustomers.length}건
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-center">-</td>
                    <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                      {bulkTotals.supply.toLocaleString()}
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                      {bulkTotals.tax.toLocaleString()}
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-right">
                      {bulkTotals.total.toLocaleString()}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        {statusMsg}
      </div>
    </div>
  );
}
