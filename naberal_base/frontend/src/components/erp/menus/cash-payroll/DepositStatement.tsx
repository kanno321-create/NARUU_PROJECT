"use client";

import React, { useState } from "react";

interface DepositItem {
  id: string;
  date: string;
  docNo: string;
  accountName: string;
  depositType: string;
  customerCode: string;
  customerName: string;
  amount: number;
  memo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: DepositItem[] = [
  {
    id: "1",
    date: "2025-12-05",
    docNo: "D2025120501",
    accountName: "기업은행",
    depositType: "현금",
    customerCode: "c001",
    customerName: "테스트사업장",
    amount: 100000,
    memo: "매출대금",
  },
  {
    id: "2",
    date: "2025-12-05",
    docNo: "D2025120502",
    accountName: "국민은행",
    depositType: "계좌이체",
    customerCode: "c002",
    customerName: "제고사업장",
    amount: 150000,
    memo: "매출대금",
  },
  {
    id: "3",
    date: "2025-12-04",
    docNo: "D2025120401",
    accountName: "기업은행",
    depositType: "현금",
    customerCode: "",
    customerName: "",
    amount: 50000,
    memo: "기타수입",
  },
  {
    id: "4",
    date: "2025-12-03",
    docNo: "D2025120301",
    accountName: "신한은행",
    depositType: "계좌이체",
    customerCode: "c001",
    customerName: "테스트사업장",
    amount: 80000,
    memo: "선수금",
  },
];

export function DepositStatement() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [accountFilter, setAccountFilter] = useState("전체");
  const [depositTypeFilter, setDepositTypeFilter] = useState("전체");
  const [data] = useState<DepositItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const accounts = ["전체", ...new Set(data.map((d) => d.accountName))];
  const depositTypes = ["전체", "현금", "계좌이체", "카드", "어음", "기타"];

  const filteredData = data.filter(
    (item) =>
      item.date >= startDate &&
      item.date <= endDate &&
      (accountFilter === "전체" || item.accountName === accountFilter) &&
      (depositTypeFilter === "전체" || item.depositType === depositTypeFilter)
  );

  // 일계
  const dailyData = filteredData.filter((item) => item.date === "2025-12-05");
  const dailyTotal = dailyData.reduce((acc, item) => acc + item.amount, 0);

  // 월계
  const monthlyData = filteredData.filter((item) => item.date.startsWith("2025-12"));
  const monthlyTotal = monthlyData.reduce((acc, item) => acc + item.amount, 0);

  // 누계
  const total = filteredData.reduce((acc, item) => acc + item.amount, 0);

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">입금명세서</span>
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
          <span className="text-xs">계좌:</span>
          <select
            value={accountFilter}
            onChange={(e) => setAccountFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            {accounts.map((acc) => (
              <option key={acc} value={acc}>{acc}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">유형:</span>
          <select
            value={depositTypeFilter}
            onChange={(e) => setDepositTypeFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            {depositTypes.map((type) => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
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
              <th className="border border-gray-400 px-2 py-1 w-24">계좌</th>
              <th className="border border-gray-400 px-2 py-1 w-16">유형</th>
              <th className="border border-gray-400 px-2 py-1 w-20">거래처코드</th>
              <th className="border border-gray-400 px-2 py-1 w-28">거래처명</th>
              <th className="border border-gray-400 px-2 py-1 w-28">입금액</th>
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
                <td className="border border-gray-300 px-2 py-1">{item.docNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.accountName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.depositType}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerName}</td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600 font-medium">
                  {item.amount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.memo}</td>
              </tr>
            ))}
            {/* 일계 행 */}
            <tr className="bg-yellow-50 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={6}>
                (일계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {dailyTotal.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
            </tr>
            {/* 월계 행 */}
            <tr className="bg-blue-50 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={6}>
                (월계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {monthlyTotal.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
            </tr>
            {/* 누계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={6}>
                (누계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
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
