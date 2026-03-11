"use client";

import React, { useState } from "react";

interface PaymentStatusItem {
  id: string;
  vendorCode: string;
  vendorName: string;
  prevPayable: number;
  purchaseAmount: number;
  paymentAmount: number;
  currentPayable: number;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: PaymentStatusItem[] = [
  {
    id: "1",
    vendorCode: "v001",
    vendorName: "공급업체A",
    prevPayable: 50000,
    purchaseAmount: 371250,
    paymentAmount: 300000,
    currentPayable: 121250,
  },
  {
    id: "2",
    vendorCode: "v002",
    vendorName: "공급업체B",
    prevPayable: 0,
    purchaseAmount: 110000,
    paymentAmount: 50000,
    currentPayable: 60000,
  },
  {
    id: "3",
    vendorCode: "v003",
    vendorName: "공급업체C",
    prevPayable: 30000,
    purchaseAmount: 156750,
    paymentAmount: 80000,
    currentPayable: 106750,
  },
];

export function PaymentStatus() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [vendorSearch, setVendorSearch] = useState("");
  const [data] = useState<PaymentStatusItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      item.vendorCode.includes(vendorSearch) ||
      item.vendorName.includes(vendorSearch)
  );

  // 누계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      prevPayable: acc.prevPayable + item.prevPayable,
      purchaseAmount: acc.purchaseAmount + item.purchaseAmount,
      paymentAmount: acc.paymentAmount + item.paymentAmount,
      currentPayable: acc.currentPayable + item.currentPayable,
    }),
    { prevPayable: 0, purchaseAmount: 0, paymentAmount: 0, currentPayable: 0 }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">지급현황</span>
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
              <th className="border border-gray-400 px-2 py-1 w-20">거래처코드</th>
              <th className="border border-gray-400 px-2 py-1 w-28">거래처명</th>
              <th className="border border-gray-400 px-2 py-1 w-28">전기미지급금</th>
              <th className="border border-gray-400 px-2 py-1 w-28">매입액</th>
              <th className="border border-gray-400 px-2 py-1 w-28">지급액</th>
              <th className="border border-gray-400 px-2 py-1">현미지급금</th>
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
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.prevPayable.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.purchaseAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.paymentAmount.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right font-medium ${
                  item.currentPayable > 0 ? "text-red-600" : "text-blue-600"
                }`}>
                  {item.currentPayable.toLocaleString()}
                </td>
              </tr>
            ))}
            {/* 누계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={2}>
                (누계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.prevPayable.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.purchaseAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.paymentAmount.toLocaleString()}
              </td>
              <td className={`border border-gray-400 px-2 py-1 text-right ${
                totals.currentPayable > 0 ? "text-red-600" : "text-blue-600"
              }`}>
                {totals.currentPayable.toLocaleString()}
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
