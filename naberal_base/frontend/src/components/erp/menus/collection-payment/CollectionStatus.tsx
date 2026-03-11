"use client";

import React, { useState } from "react";

interface CollectionStatusItem {
  id: string;
  customerCode: string;
  customerName: string;
  prevReceivable: number;
  salesAmount: number;
  collectionAmount: number;
  currentReceivable: number;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: CollectionStatusItem[] = [
  {
    id: "1",
    customerCode: "c001",
    customerName: "테스트사업장",
    prevReceivable: 100000,
    salesAmount: 233200,
    collectionAmount: 180000,
    currentReceivable: 153200,
  },
  {
    id: "2",
    customerCode: "c002",
    customerName: "제고사업장",
    prevReceivable: 50000,
    salesAmount: 133100,
    collectionAmount: 150000,
    currentReceivable: 33100,
  },
  {
    id: "3",
    customerCode: "c003",
    customerName: "신규사업장",
    prevReceivable: 0,
    salesAmount: 250000,
    collectionAmount: 200000,
    currentReceivable: 50000,
  },
];

export function CollectionStatus() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [customerSearch, setCustomerSearch] = useState("");
  const [data] = useState<CollectionStatusItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      item.customerCode.includes(customerSearch) ||
      item.customerName.includes(customerSearch)
  );

  // 누계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      prevReceivable: acc.prevReceivable + item.prevReceivable,
      salesAmount: acc.salesAmount + item.salesAmount,
      collectionAmount: acc.collectionAmount + item.collectionAmount,
      currentReceivable: acc.currentReceivable + item.currentReceivable,
    }),
    { prevReceivable: 0, salesAmount: 0, collectionAmount: 0, currentReceivable: 0 }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">수금현황</span>
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
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색(F)
        </button>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-20">거래처코드</th>
              <th className="border border-gray-400 px-2 py-1 w-28">거래처명</th>
              <th className="border border-gray-400 px-2 py-1 w-28">전기미수금</th>
              <th className="border border-gray-400 px-2 py-1 w-28">매출액</th>
              <th className="border border-gray-400 px-2 py-1 w-28">수금액</th>
              <th className="border border-gray-400 px-2 py-1">현미수금</th>
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
                <td className="border border-gray-300 px-2 py-1">{item.customerCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerName}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.prevReceivable.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.salesAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.collectionAmount.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right font-medium ${
                  item.currentReceivable > 0 ? "text-red-600" : "text-blue-600"
                }`}>
                  {item.currentReceivable.toLocaleString()}
                </td>
              </tr>
            ))}
            {/* 누계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={2}>
                (누계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.prevReceivable.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.salesAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.collectionAmount.toLocaleString()}
              </td>
              <td className={`border border-gray-400 px-2 py-1 text-right ${
                totals.currentReceivable > 0 ? "text-red-600" : "text-blue-600"
              }`}>
                {totals.currentReceivable.toLocaleString()}
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
