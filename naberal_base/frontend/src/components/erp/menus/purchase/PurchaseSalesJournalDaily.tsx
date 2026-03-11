"use client";

import React, { useState } from "react";

interface JournalDailyItem {
  id: string;
  date: string;
  salesSupply: number;
  salesTax: number;
  salesTotal: number;
  purchaseSupply: number;
  purchaseTax: number;
  purchaseTotal: number;
  difference: number;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: JournalDailyItem[] = [
  {
    id: "1",
    date: "2025-12-01",
    salesSupply: 150000,
    salesTax: 15000,
    salesTotal: 165000,
    purchaseSupply: 100000,
    purchaseTax: 10000,
    purchaseTotal: 110000,
    difference: 55000,
  },
  {
    id: "2",
    date: "2025-12-02",
    salesSupply: 200000,
    salesTax: 20000,
    salesTotal: 220000,
    purchaseSupply: 0,
    purchaseTax: 0,
    purchaseTotal: 0,
    difference: 220000,
  },
  {
    id: "3",
    date: "2025-12-03",
    salesSupply: 180000,
    salesTax: 18000,
    salesTotal: 198000,
    purchaseSupply: 142500,
    purchaseTax: 14250,
    purchaseTotal: 156750,
    difference: 41250,
  },
  {
    id: "4",
    date: "2025-12-04",
    salesSupply: 250000,
    salesTax: 25000,
    salesTotal: 275000,
    purchaseSupply: 100000,
    purchaseTax: 10000,
    purchaseTotal: 110000,
    difference: 165000,
  },
  {
    id: "5",
    date: "2025-12-05",
    salesSupply: 320000,
    salesTax: 32000,
    salesTotal: 352000,
    purchaseSupply: 200000,
    purchaseTax: 20000,
    purchaseTotal: 220000,
    difference: 132000,
  },
];

export function PurchaseSalesJournalDaily() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [data] = useState<JournalDailyItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // 누계 계산
  const totals = data.reduce(
    (acc, item) => ({
      salesSupply: acc.salesSupply + item.salesSupply,
      salesTax: acc.salesTax + item.salesTax,
      salesTotal: acc.salesTotal + item.salesTotal,
      purchaseSupply: acc.purchaseSupply + item.purchaseSupply,
      purchaseTax: acc.purchaseTax + item.purchaseTax,
      purchaseTotal: acc.purchaseTotal + item.purchaseTotal,
      difference: acc.difference + item.difference,
    }),
    {
      salesSupply: 0,
      salesTax: 0,
      salesTotal: 0,
      purchaseSupply: 0,
      purchaseTax: 0,
      purchaseTotal: 0,
      difference: 0,
    }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">매입매출장(일별)</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📊</span> 보고서출력
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 엑셀변환
        </button>
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
          최근1달검색(F2)
        </button>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색(F)
        </button>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>일자</th>
              <th className="border border-gray-400 px-2 py-1 bg-blue-100" colSpan={3}>매 출</th>
              <th className="border border-gray-400 px-2 py-1 bg-red-100" colSpan={3}>매 입</th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>차액</th>
            </tr>
            <tr>
              <th className="border border-gray-400 px-2 py-1 bg-blue-100 w-24">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 bg-blue-100 w-20">세액</th>
              <th className="border border-gray-400 px-2 py-1 bg-blue-100 w-24">합계</th>
              <th className="border border-gray-400 px-2 py-1 bg-red-100 w-24">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 bg-red-100 w-20">세액</th>
              <th className="border border-gray-400 px-2 py-1 bg-red-100 w-24">합계</th>
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
                <td className="border border-gray-300 px-2 py-1 text-right bg-blue-50">
                  {item.salesSupply.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right bg-blue-50">
                  {item.salesTax.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right bg-blue-50 font-medium">
                  {item.salesTotal.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right bg-red-50">
                  {item.purchaseSupply.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right bg-red-50">
                  {item.purchaseTax.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right bg-red-50 font-medium">
                  {item.purchaseTotal.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right font-medium ${
                  item.difference >= 0 ? "text-blue-600" : "text-red-600"
                }`}>
                  {item.difference.toLocaleString()}
                </td>
              </tr>
            ))}
            {/* 누계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1">(누계)</td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.salesSupply.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.salesTax.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.salesTotal.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.purchaseSupply.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.purchaseTax.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.purchaseTotal.toLocaleString()}
              </td>
              <td className={`border border-gray-400 px-2 py-1 text-right ${
                totals.difference >= 0 ? "text-blue-600" : "text-red-600"
              }`}>
                {totals.difference.toLocaleString()}
              </td>
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
