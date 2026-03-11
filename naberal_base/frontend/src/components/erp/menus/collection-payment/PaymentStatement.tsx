"use client";

import React, { useState } from "react";

interface PaymentItem {
  id: string;
  date: string;
  slipNo: string;
  vendorCode: string;
  vendorName: string;
  paymentMethod: string;
  amount: number;
  memo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: PaymentItem[] = [
  {
    id: "1",
    date: "2025-12-05",
    slipNo: "P20251205-001",
    vendorCode: "v001",
    vendorName: "공급업체A",
    paymentMethod: "계좌이체",
    amount: 200000,
    memo: "",
  },
  {
    id: "2",
    date: "2025-12-04",
    slipNo: "P20251204-001",
    vendorCode: "v002",
    vendorName: "공급업체B",
    paymentMethod: "현금",
    amount: 50000,
    memo: "",
  },
  {
    id: "3",
    date: "2025-12-03",
    slipNo: "P20251203-001",
    vendorCode: "v001",
    vendorName: "공급업체A",
    paymentMethod: "어음",
    amount: 100000,
    memo: "3개월 어음",
  },
  {
    id: "4",
    date: "2025-12-02",
    slipNo: "P20251202-001",
    vendorCode: "v003",
    vendorName: "공급업체C",
    paymentMethod: "계좌이체",
    amount: 80000,
    memo: "",
  },
];

export function PaymentStatement() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [vendorSearch, setVendorSearch] = useState("");
  const [data] = useState<PaymentItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      item.vendorCode.includes(vendorSearch) ||
      item.vendorName.includes(vendorSearch)
  );

  // 일계 계산 (오늘 날짜)
  const dailyTotal = filteredData
    .filter((item) => item.date === "2025-12-05")
    .reduce((sum, item) => sum + item.amount, 0);

  // 월계 계산 (이번 달)
  const monthlyTotal = filteredData
    .filter((item) => item.date.startsWith("2025-12"))
    .reduce((sum, item) => sum + item.amount, 0);

  // 누계 계산
  const total = filteredData.reduce((sum, item) => sum + item.amount, 0);

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">지급명세서</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>➕</span> 신규
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>✏️</span> 수정
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🗑️</span> 삭제
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
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
            value={vendorSearch}
            onChange={(e) => setVendorSearch(e.target.value)}
            placeholder="거래처명/코드"
            className="w-28 rounded border border-gray-400 px-2 py-1 text-xs"
          />
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색
        </button>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-24">일자</th>
              <th className="border border-gray-400 px-2 py-1 w-28">전표번호</th>
              <th className="border border-gray-400 px-2 py-1 w-20">거래처코드</th>
              <th className="border border-gray-400 px-2 py-1 w-28">거래처명</th>
              <th className="border border-gray-400 px-2 py-1 w-20">결제방법</th>
              <th className="border border-gray-400 px-2 py-1 w-28">지급액</th>
              <th className="border border-gray-400 px-2 py-1">비고</th>
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
                <td className="border border-gray-300 px-2 py-1">{item.date}</td>
                <td className="border border-gray-300 px-2 py-1">{item.slipNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.vendorCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.vendorName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.paymentMethod}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.amount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.memo}</td>
              </tr>
            ))}
            {/* 일계 행 */}
            <tr className="bg-yellow-50 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={5}>
                (일계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {dailyTotal.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
            </tr>
            {/* 월계 행 */}
            <tr className="bg-blue-50 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={5}>
                (월계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {monthlyTotal.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
            </tr>
            {/* 누계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={5}>
                (누계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {total.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
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
