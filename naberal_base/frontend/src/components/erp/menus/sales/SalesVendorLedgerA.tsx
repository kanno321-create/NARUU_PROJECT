"use client";

import React, { useState } from "react";

interface VendorLedgerItem {
  id: string;
  date: string;
  summary: string;
  sales: number;
  collection: number;
  purchase: number;
  payment: number;
  receivable: number;
  payable: number;
  slipNo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: VendorLedgerItem[] = [
  {
    id: "1",
    date: "2025-12-05",
    summary: "(전월이월)",
    sales: 0,
    collection: 0,
    purchase: 0,
    payment: 0,
    receivable: 0,
    payable: 0,
    slipNo: "",
  },
  {
    id: "2",
    date: "2025-12-05",
    summary: "상품판매",
    sales: 233200,
    collection: 0,
    purchase: 0,
    payment: 0,
    receivable: 233200,
    payable: 0,
    slipNo: "1",
  },
  {
    id: "3",
    date: "2025-12-05",
    summary: "외상수금",
    sales: 0,
    collection: 100000,
    purchase: 0,
    payment: 0,
    receivable: 133200,
    payable: 0,
    slipNo: "",
  },
];

export function SalesVendorLedgerA() {
  const [startDate, setStartDate] = useState("2025-12-05");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [vendorSearch, setVendorSearch] = useState("테스트사업장");
  const [data] = useState<VendorLedgerItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

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
        <span className="text-sm font-medium text-white">매출처원장(A형)</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
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
          <span className="text-xs">매출처검색:</span>
          <input
            type="text"
            value={vendorSearch}
            onChange={(e) => setVendorSearch(e.target.value)}
            className="w-32 rounded border border-gray-400 px-2 py-1 text-xs"
          />
          <button className="rounded border border-gray-400 bg-gray-100 px-2 py-1 text-xs hover:bg-gray-200">
            ...
          </button>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색(F)
        </button>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-24">날짜</th>
              <th className="border border-gray-400 px-2 py-1 w-32">적요</th>
              <th className="border border-gray-400 px-2 py-1 w-24">매출</th>
              <th className="border border-gray-400 px-2 py-1 w-24">수금</th>
              <th className="border border-gray-400 px-2 py-1 w-24">매입</th>
              <th className="border border-gray-400 px-2 py-1 w-24">지급</th>
              <th className="border border-gray-400 px-2 py-1 w-24">미수금</th>
              <th className="border border-gray-400 px-2 py-1 w-24">미지급금</th>
              <th className="border border-gray-400 px-2 py-1">전표번호</th>
            </tr>
          </thead>
          <tbody>
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
                  {item.payable > 0 ? item.payable.toLocaleString() : ""}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.slipNo}</td>
              </tr>
            ))}
            {/* 일계 행 */}
            <tr className="bg-yellow-50">
              <td className="border border-gray-400 px-2 py-1" colSpan={2}>
                (일계:2025-12-05)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {totals.sales.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {totals.collection.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {totals.purchase.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {totals.payment.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={3}></td>
            </tr>
            {/* 월계 행 */}
            <tr className="bg-blue-50">
              <td className="border border-gray-400 px-2 py-1" colSpan={2}>
                (월계:2025-12)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {totals.sales.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {totals.collection.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {totals.purchase.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {totals.payment.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={3}></td>
            </tr>
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
              <td className="border border-gray-400 px-2 py-1" colSpan={3}></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {data.length}건 | loading ok
      </div>
    </div>
  );
}
