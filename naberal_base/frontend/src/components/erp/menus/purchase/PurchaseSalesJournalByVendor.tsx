"use client";

import React, { useState } from "react";

interface JournalByVendorItem {
  id: string;
  vendorCode: string;
  vendorName: string;
  salesSupply: number;
  salesTax: number;
  salesTotal: number;
  purchaseSupply: number;
  purchaseTax: number;
  purchaseTotal: number;
  difference: number;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: JournalByVendorItem[] = [
  {
    id: "1",
    vendorCode: "c001",
    vendorName: "테스트사업장",
    salesSupply: 500000,
    salesTax: 50000,
    salesTotal: 550000,
    purchaseSupply: 0,
    purchaseTax: 0,
    purchaseTotal: 0,
    difference: 550000,
  },
  {
    id: "2",
    vendorCode: "c002",
    vendorName: "제고사업장",
    salesSupply: 300000,
    salesTax: 30000,
    salesTotal: 330000,
    purchaseSupply: 0,
    purchaseTax: 0,
    purchaseTotal: 0,
    difference: 330000,
  },
  {
    id: "3",
    vendorCode: "v001",
    vendorName: "공급업체A",
    salesSupply: 0,
    salesTax: 0,
    salesTotal: 0,
    purchaseSupply: 337500,
    purchaseTax: 33750,
    purchaseTotal: 371250,
    difference: -371250,
  },
  {
    id: "4",
    vendorCode: "v002",
    vendorName: "공급업체B",
    salesSupply: 0,
    salesTax: 0,
    salesTotal: 0,
    purchaseSupply: 100000,
    purchaseTax: 10000,
    purchaseTotal: 110000,
    difference: -110000,
  },
  {
    id: "5",
    vendorCode: "v003",
    vendorName: "공급업체C",
    salesSupply: 0,
    salesTax: 0,
    salesTotal: 0,
    purchaseSupply: 142500,
    purchaseTax: 14250,
    purchaseTotal: 156750,
    difference: -156750,
  },
];

export function PurchaseSalesJournalByVendor() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [vendorSearch, setVendorSearch] = useState("");
  const [data] = useState<JournalByVendorItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      item.vendorCode.includes(vendorSearch) ||
      item.vendorName.includes(vendorSearch)
  );

  // 누계 계산
  const totals = filteredData.reduce(
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
        <span className="text-sm font-medium text-white">매입매출장(거래처별)</span>
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
        <div className="flex items-center gap-2">
          <span className="text-xs">거래처검색:</span>
          <input
            type="text"
            value={vendorSearch}
            onChange={(e) => setVendorSearch(e.target.value)}
            className="w-32 rounded border border-gray-400 px-2 py-1 text-xs"
          />
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
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>거래처코드</th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>거래처명</th>
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
            {filteredData.map((item) => (
              <tr
                key={item.id}
                className={`cursor-pointer ${
                  selectedId === item.id
                    ? "bg-[#316AC5] text-white"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1">{item.vendorCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.vendorName}</td>
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
              <td className="border border-gray-400 px-2 py-1" colSpan={2}>(누계)</td>
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
        총 {filteredData.length}건 | loading ok
      </div>
    </div>
  );
}
