"use client";

import React, { useState, useCallback } from "react";
import { fetchAPI } from "@/lib/api";

interface LedgerItem {
  id: string;
  date: string;
  summary: string;
  sales: number;
  collection: number;
  purchase: number;
  payment: number;
  receivable: number;
  balance: number;
  slipNo: string;
}

export function CustomerLedger() {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [customerSearch, setCustomerSearch] = useState("");
  const [data, setData] = useState<LedgerItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
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

      // API 응답을 LedgerItem 형태로 변환
      // 모든 거래처의 거래내역을 합쳐서 거래처원장 형태로 표시
      const flatItems: LedgerItem[] = [];
      for (const customer of json.items || []) {
        // 거래처 검색 필터
        if (
          customerSearch &&
          !customer.customerName.includes(customerSearch) &&
          !customer.customerCode.includes(customerSearch)
        ) {
          continue;
        }

        // 전기이월 행
        if (customer.previousBalance !== 0) {
          flatItems.push({
            id: `prev-${customer.customerCode}`,
            date: startDate || "",
            summary: `(전월이월) ${customer.customerName}`,
            sales: 0,
            collection: 0,
            purchase: 0,
            payment: 0,
            receivable: customer.previousBalance,
            balance: 0,
            slipNo: "",
          });
        }

        // 각 거래 내역
        for (const trans of customer.transactions || []) {
          flatItems.push({
            id: trans.id,
            date: trans.transDate,
            summary: `${customer.customerName} - ${trans.description}`,
            sales: trans.transType === "매출" ? trans.debitAmount : 0,
            collection: trans.transType === "수금" ? trans.creditAmount : 0,
            purchase: 0,
            payment: 0,
            receivable: trans.balance,
            balance: 0,
            slipNo: trans.docNo,
          });
        }
      }

      setData(flatItems);
      setLoaded(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : "데이터 로딩 실패";
      setError(message);
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, customerSearch]);

  // 합계 계산
  const totals = data.reduce(
    (acc, item) => ({
      sales: acc.sales + item.sales,
      collection: acc.collection + item.collection,
      purchase: acc.purchase + item.purchase,
      payment: acc.payment + item.payment,
    }),
    { sales: 0, collection: 0, purchase: 0, payment: 0 }
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
          <span>📊</span> 보고서추력
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🖨️</span> 표시항목 ▼
        </button>
      </div>

      {/* 안내 메시지 */}
      <div className="bg-blue-50 px-3 py-1 text-xs text-blue-700">
        • 환경설정에서 '매출건조작성시 원가재산' 항목이 체크를 해제하신 경우 원가관리(원가,재고금액,이익등) 보고서를 표시하기전에 원가재계산을 실행하셔야 정확한 데이터가 표시됩니다.
      </div>

      {/* 검색 조건 */}
      <div className="flex items-center gap-4 border-b bg-white px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="text-xs">기간선택:</span>
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
        <button className="rounded border border-gray-400 bg-yellow-100 px-3 py-1 text-xs hover:bg-yellow-200">
          회근판달금색(F2)
        </button>
        <div className="flex items-center gap-2">
          <span className="text-xs">거래처검색:</span>
          <input
            type="text"
            value={customerSearch}
            onChange={(e) => setCustomerSearch(e.target.value)}
            className="w-32 rounded border border-gray-400 px-2 py-1 text-xs"
          />
          <button className="rounded border border-gray-400 bg-gray-100 px-2 py-1 text-xs hover:bg-gray-200">
            ...
          </button>
        </div>
        <button
          className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200"
          onClick={fetchData}
        >
          검 색(F)
        </button>
      </div>

      {/* 에러 표시 */}
      {error && (
        <div className="bg-red-50 px-3 py-1 text-xs text-red-700">
          {error}
        </div>
      )}

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-24">날짜</th>
              <th className="border border-gray-400 px-2 py-1 w-32">거래내용</th>
              <th className="border border-gray-400 px-2 py-1 w-24">매출</th>
              <th className="border border-gray-400 px-2 py-1 w-24">수금</th>
              <th className="border border-gray-400 px-2 py-1 w-24">매입</th>
              <th className="border border-gray-400 px-2 py-1 w-24">지급</th>
              <th className="border border-gray-400 px-2 py-1 w-24">미수금</th>
              <th className="border border-gray-400 px-2 py-1 w-24">미지급금</th>
              <th className="border border-gray-400 px-2 py-1 w-20">잔액</th>
              <th className="border border-gray-400 px-2 py-1">전표번호</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={10} className="border border-gray-300 px-2 py-4 text-center text-gray-500">
                  데이터 로딩 중...
                </td>
              </tr>
            ) : !loaded ? (
              <tr>
                <td colSpan={10} className="border border-gray-300 px-2 py-4 text-center text-gray-500">
                  기간을 선택하고 검색 버튼을 클릭하세요.
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={10} className="border border-gray-300 px-2 py-4 text-center text-gray-500">
                  조회 결과가 없습니다.
                </td>
              </tr>
            ) : (
              <>
                {data.map((item) => (
                  <tr
                    key={item.id}
                    className={`cursor-pointer ${
                      selectedId === item.id
                        ? "bg-[#316AC5] text-white"
                        : "hover:bg-gray-100"
                    }`}
                    onClick={() => setSelectedId(item.id)}
                  >
                    <td className="border border-gray-300 px-2 py-1">{item.date}</td>
                    <td className="border border-gray-300 px-2 py-1">{item.summary}</td>
                    <td className="border border-gray-300 px-2 py-1 text-right">
                      {item.sales > 0 ? item.sales.toLocaleString() : ""}
                    </td>
                    <td className="border border-gray-300 px-2 py-1 text-right">
                      {item.collection > 0 ? item.collection.toLocaleString() : ""}
                    </td>
                    <td className="border border-gray-300 px-2 py-1 text-right">
                      {item.purchase > 0 ? item.purchase.toLocaleString() : ""}
                    </td>
                    <td className="border border-gray-300 px-2 py-1 text-right">
                      {item.payment > 0 ? item.payment.toLocaleString() : ""}
                    </td>
                    <td className="border border-gray-300 px-2 py-1 text-right">
                      {item.receivable > 0 ? item.receivable.toLocaleString() : ""}
                    </td>
                    <td className="border border-gray-300 px-2 py-1 text-right">
                      {item.balance > 0 ? item.balance.toLocaleString() : ""}
                    </td>
                    <td className="border border-gray-300 px-2 py-1 text-right">
                      {item.slipNo}
                    </td>
                    <td className="border border-gray-300 px-2 py-1"></td>
                  </tr>
                ))}
                {/* 누계 행 */}
                <tr className="bg-gray-200 font-medium">
                  <td className="border border-gray-400 px-2 py-1" colSpan={2}>
                    (누계)
                  </td>
                  <td className="border border-gray-400 px-2 py-1 text-right">
                    {totals.sales.toLocaleString()}
                  </td>
                  <td className="border border-gray-400 px-2 py-1 text-right">
                    {totals.collection.toLocaleString()}
                  </td>
                  <td className="border border-gray-400 px-2 py-1 text-right">
                    {totals.purchase.toLocaleString()}
                  </td>
                  <td className="border border-gray-400 px-2 py-1 text-right">
                    {totals.payment.toLocaleString()}
                  </td>
                  <td className="border border-gray-400 px-2 py-1" colSpan={4}></td>
                </tr>
              </>
            )}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {data.length}건 | {loading ? "loading..." : loaded ? "loading ok" : "대기중"}
      </div>
    </div>
  );
}
