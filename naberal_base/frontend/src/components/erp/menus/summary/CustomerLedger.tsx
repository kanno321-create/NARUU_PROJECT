"use client";

import React, { useState, useCallback } from "react";
import { fetchAPI } from "@/lib/api";

interface LedgerTransaction {
  id: string;
  transDate: string;
  transType: string;
  docNo: string;
  description: string;
  debitAmount: number;
  creditAmount: number;
  balance: number;
  memo: string;
}

interface CustomerLedgerItem {
  customerCode: string;
  customerName: string;
  businessNo: string;
  representative: string;
  phone: string;
  previousBalance: number;
  currentDebit: number;
  currentCredit: number;
  currentBalance: number;
  transactions: LedgerTransaction[];
}

export function CustomerLedger() {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [customerFilter, setCustomerFilter] = useState("");
  const [data, setData] = useState<CustomerLedgerItem[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<string | null>(null);
  const [selectedTransId, setSelectedTransId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (startDate) params.append("start_date", startDate);
      if (endDate) params.append("end_date", endDate);

      const endpoint = `/v1/erp/ledger/customer${params.toString() ? `?${params}` : ""}`;
      const json = await fetchAPI<any>(endpoint);

      const items: CustomerLedgerItem[] = (json.items || []).map(
        (item: CustomerLedgerItem) => ({
          customerCode: item.customerCode || "",
          customerName: item.customerName || "",
          businessNo: item.businessNo || "",
          representative: item.representative || "",
          phone: item.phone || "",
          previousBalance: item.previousBalance || 0,
          currentDebit: item.currentDebit || 0,
          currentCredit: item.currentCredit || 0,
          currentBalance: item.currentBalance || 0,
          transactions: (item.transactions || []).map(
            (t: LedgerTransaction) => ({
              id: t.id || "",
              transDate: t.transDate || "",
              transType: t.transType || "",
              docNo: t.docNo || "",
              description: t.description || "",
              debitAmount: t.debitAmount || 0,
              creditAmount: t.creditAmount || 0,
              balance: t.balance || 0,
              memo: t.memo || "",
            })
          ),
        })
      );

      setData(items);
      if (items.length > 0 && !selectedCustomer) {
        setSelectedCustomer(items[0].customerCode);
      }
      setLoaded(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : "데이터 로딩 실패";
      setError(message);
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, selectedCustomer]);

  const filteredCustomers = data.filter(
    (item) =>
      customerFilter === "" ||
      item.customerName.includes(customerFilter) ||
      item.customerCode.includes(customerFilter)
  );

  const selectedCustomerData = data.find(
    (c) => c.customerCode === selectedCustomer
  );

  // 전체 합계
  const totals = filteredCustomers.reduce(
    (acc, item) => ({
      previousBalance: acc.previousBalance + item.previousBalance,
      currentDebit: acc.currentDebit + item.currentDebit,
      currentCredit: acc.currentCredit + item.currentCredit,
      currentBalance: acc.currentBalance + item.currentBalance,
    }),
    { previousBalance: 0, currentDebit: 0, currentCredit: 0, currentBalance: 0 }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">거래처원장</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
          onClick={fetchData}
        >
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🖨️</span> 원장출력
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📊</span> 보고서
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 엑셀
        </button>
      </div>

      {/* 검색 조건 */}
      <div className="flex items-center gap-4 border-b bg-white px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="text-xs">기간:</span>
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
        <div className="flex items-center gap-2">
          <span className="text-xs">거래처:</span>
          <input
            type="text"
            value={customerFilter}
            onChange={(e) => setCustomerFilter(e.target.value)}
            placeholder="거래처명/코드"
            className="w-32 rounded border border-gray-400 px-2 py-1 text-xs"
          />
        </div>
        <button
          className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200"
          onClick={fetchData}
        >
          조 회(F)
        </button>
      </div>

      {/* 에러 표시 */}
      {error && (
        <div className="bg-red-50 px-3 py-1 text-xs text-red-700">
          {error}
        </div>
      )}

      {/* 상하 분할 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 좌측: 거래처 목록 */}
        <div className="flex w-1/3 flex-col border-r">
          <div className="bg-blue-50 px-2 py-1 text-xs font-medium">
            거래처 목록
          </div>
          <div className="flex-1 overflow-auto">
            <table className="w-full border-collapse text-xs">
              <thead className="sticky top-0 bg-[#E8E4D9]">
                <tr>
                  <th className="border border-gray-400 px-2 py-1">코드</th>
                  <th className="border border-gray-400 px-2 py-1">거래처명</th>
                  <th className="border border-gray-400 px-2 py-1 text-right">
                    잔액
                  </th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={3} className="border border-gray-300 px-2 py-4 text-center text-gray-500">
                      로딩 중...
                    </td>
                  </tr>
                ) : !loaded ? (
                  <tr>
                    <td colSpan={3} className="border border-gray-300 px-2 py-4 text-center text-gray-500">
                      조회 버튼을 클릭하세요.
                    </td>
                  </tr>
                ) : filteredCustomers.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="border border-gray-300 px-2 py-4 text-center text-gray-500">
                      결과 없음
                    </td>
                  </tr>
                ) : (
                  <>
                    {filteredCustomers.map((item) => (
                      <tr
                        key={item.customerCode}
                        className={`cursor-pointer ${
                          selectedCustomer === item.customerCode
                            ? "bg-[#316AC5] text-white"
                            : "hover:bg-gray-100"
                        }`}
                        onClick={() => setSelectedCustomer(item.customerCode)}
                      >
                        <td className="border border-gray-300 px-2 py-1">
                          {item.customerCode}
                        </td>
                        <td className="border border-gray-300 px-2 py-1">
                          {item.customerName}
                        </td>
                        <td
                          className={`border border-gray-300 px-2 py-1 text-right ${
                            selectedCustomer === item.customerCode
                              ? ""
                              : item.currentBalance > 0
                                ? "text-blue-600"
                                : "text-red-600"
                          }`}
                        >
                          {item.currentBalance.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                    <tr className="bg-gray-200 font-medium">
                      <td
                        className="border border-gray-400 px-2 py-1"
                        colSpan={2}
                      >
                        합 계 ({filteredCustomers.length}건)
                      </td>
                      <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                        {totals.currentBalance.toLocaleString()}
                      </td>
                    </tr>
                  </>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* 우측: 원장 상세 */}
        <div className="flex flex-1 flex-col">
          {/* 거래처 정보 */}
          {selectedCustomerData && (
            <div className="border-b bg-yellow-50 px-3 py-2">
              <div className="flex items-center gap-6 text-xs">
                <div>
                  <span className="font-medium">거래처명:</span>{" "}
                  {selectedCustomerData.customerName}
                </div>
                <div>
                  <span className="font-medium">사업자번호:</span>{" "}
                  {selectedCustomerData.businessNo}
                </div>
                <div>
                  <span className="font-medium">대표자:</span>{" "}
                  {selectedCustomerData.representative}
                </div>
                <div>
                  <span className="font-medium">전화:</span>{" "}
                  {selectedCustomerData.phone}
                </div>
              </div>
              <div className="mt-1 flex items-center gap-6 text-xs">
                <div>
                  <span className="font-medium">전기잔액:</span>{" "}
                  <span className="text-gray-600">
                    {selectedCustomerData.previousBalance.toLocaleString()}원
                  </span>
                </div>
                <div>
                  <span className="font-medium">당기차변:</span>{" "}
                  <span className="text-blue-600">
                    {selectedCustomerData.currentDebit.toLocaleString()}원
                  </span>
                </div>
                <div>
                  <span className="font-medium">당기대변:</span>{" "}
                  <span className="text-red-600">
                    {selectedCustomerData.currentCredit.toLocaleString()}원
                  </span>
                </div>
                <div>
                  <span className="font-medium">현재잔액:</span>{" "}
                  <span className="font-bold text-blue-700">
                    {selectedCustomerData.currentBalance.toLocaleString()}원
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* 거래 내역 */}
          <div className="bg-blue-50 px-2 py-1 text-xs font-medium">
            거래 내역
          </div>
          <div className="flex-1 overflow-auto">
            <table className="w-full border-collapse text-xs">
              <thead className="sticky top-0 bg-[#E8E4D9]">
                <tr>
                  <th className="border border-gray-400 px-2 py-1 w-24">
                    거래일자
                  </th>
                  <th className="border border-gray-400 px-2 py-1 w-20">
                    거래유형
                  </th>
                  <th className="border border-gray-400 px-2 py-1 w-28">
                    전표번호
                  </th>
                  <th className="border border-gray-400 px-2 py-1">적요</th>
                  <th className="border border-gray-400 px-2 py-1 w-24">
                    차변(매출)
                  </th>
                  <th className="border border-gray-400 px-2 py-1 w-24">
                    대변(수금)
                  </th>
                  <th className="border border-gray-400 px-2 py-1 w-24">
                    잔액
                  </th>
                  <th className="border border-gray-400 px-2 py-1 w-24">
                    비고
                  </th>
                </tr>
              </thead>
              <tbody>
                {!selectedCustomerData ? (
                  <tr>
                    <td colSpan={8} className="border border-gray-300 px-2 py-4 text-center text-gray-500">
                      {loaded ? "거래처를 선택하세요." : "조회 버튼을 클릭하세요."}
                    </td>
                  </tr>
                ) : selectedCustomerData.transactions.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="border border-gray-300 px-2 py-4 text-center text-gray-500">
                      거래 내역이 없습니다.
                    </td>
                  </tr>
                ) : (
                  selectedCustomerData.transactions.map((trans) => (
                    <tr
                      key={trans.id}
                      className={`cursor-pointer ${
                        selectedTransId === trans.id
                          ? "bg-[#316AC5] text-white"
                          : "hover:bg-gray-100"
                      }`}
                      onClick={() => setSelectedTransId(trans.id)}
                    >
                      <td className="border border-gray-300 px-2 py-1">
                        {trans.transDate}
                      </td>
                      <td
                        className={`border border-gray-300 px-2 py-1 ${
                          selectedTransId === trans.id
                            ? ""
                            : trans.transType === "매출"
                              ? "text-blue-600"
                              : trans.transType === "수금"
                                ? "text-red-600"
                                : ""
                        }`}
                      >
                        {trans.transType}
                      </td>
                      <td className="border border-gray-300 px-2 py-1">
                        {trans.docNo}
                      </td>
                      <td className="border border-gray-300 px-2 py-1">
                        {trans.description}
                      </td>
                      <td
                        className={`border border-gray-300 px-2 py-1 text-right ${
                          selectedTransId === trans.id
                            ? ""
                            : trans.debitAmount > 0
                              ? "text-blue-600"
                              : ""
                        }`}
                      >
                        {trans.debitAmount > 0
                          ? trans.debitAmount.toLocaleString()
                          : ""}
                      </td>
                      <td
                        className={`border border-gray-300 px-2 py-1 text-right ${
                          selectedTransId === trans.id
                            ? ""
                            : trans.creditAmount > 0
                              ? "text-red-600"
                              : ""
                        }`}
                      >
                        {trans.creditAmount > 0
                          ? trans.creditAmount.toLocaleString()
                          : ""}
                      </td>
                      <td className="border border-gray-300 px-2 py-1 text-right font-medium">
                        {trans.balance.toLocaleString()}
                      </td>
                      <td className="border border-gray-300 px-2 py-1">
                        {trans.memo}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredCustomers.length}개 거래처 | 전기잔액:{" "}
        {totals.previousBalance.toLocaleString()} | 당기차변:{" "}
        {totals.currentDebit.toLocaleString()} | 당기대변:{" "}
        {totals.currentCredit.toLocaleString()} | 현재잔액:{" "}
        {totals.currentBalance.toLocaleString()} | {loading ? "loading..." : loaded ? "loading ok" : "대기중"}
      </div>
    </div>
  );
}
