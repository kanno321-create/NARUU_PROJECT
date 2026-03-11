"use client";

import React, { useState } from "react";

interface CashFlowItem {
  id: string;
  category: string;
  categoryType: string;
  prevBalance: number;
  depositAmount: number;
  withdrawAmount: number;
  currentBalance: number;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: CashFlowItem[] = [
  {
    id: "1",
    category: "현금",
    categoryType: "현금",
    prevBalance: 500000,
    depositAmount: 330000,
    withdrawAmount: 180000,
    currentBalance: 650000,
  },
  {
    id: "2",
    category: "기업은행",
    categoryType: "보통예금",
    prevBalance: 5000000,
    depositAmount: 330000,
    withdrawAmount: 350000,
    currentBalance: 4980000,
  },
  {
    id: "3",
    category: "국민은행",
    categoryType: "보통예금",
    prevBalance: 2000000,
    depositAmount: 0,
    withdrawAmount: 3500000,
    currentBalance: 1500000,
  },
  {
    id: "4",
    category: "신한은행",
    categoryType: "정기적금",
    prevBalance: 10000000,
    depositAmount: 1000000,
    withdrawAmount: 0,
    currentBalance: 11000000,
  },
  {
    id: "5",
    category: "우리은행",
    categoryType: "보통예금",
    prevBalance: 500000,
    depositAmount: 0,
    withdrawAmount: 0,
    currentBalance: 500000,
  },
  {
    id: "6",
    category: "카드매출",
    categoryType: "카드",
    prevBalance: 0,
    depositAmount: 1500000,
    withdrawAmount: 45000,
    currentBalance: 1455000,
  },
];

export function CashFlowSummary() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [data] = useState<CashFlowItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // 유형별 집계
  const typeSummary = data.reduce((acc, item) => {
    if (!acc[item.categoryType]) {
      acc[item.categoryType] = {
        prevBalance: 0,
        depositAmount: 0,
        withdrawAmount: 0,
        currentBalance: 0,
      };
    }
    acc[item.categoryType].prevBalance += item.prevBalance;
    acc[item.categoryType].depositAmount += item.depositAmount;
    acc[item.categoryType].withdrawAmount += item.withdrawAmount;
    acc[item.categoryType].currentBalance += item.currentBalance;
    return acc;
  }, {} as Record<string, { prevBalance: number; depositAmount: number; withdrawAmount: number; currentBalance: number }>);

  // 총계 계산
  const totals = data.reduce(
    (acc, item) => ({
      prevBalance: acc.prevBalance + item.prevBalance,
      depositAmount: acc.depositAmount + item.depositAmount,
      withdrawAmount: acc.withdrawAmount + item.withdrawAmount,
      currentBalance: acc.currentBalance + item.currentBalance,
    }),
    { prevBalance: 0, depositAmount: 0, withdrawAmount: 0, currentBalance: 0 }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">입출금집계표</span>
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
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색(F)
        </button>
      </div>

      {/* 요약 정보 */}
      <div className="grid grid-cols-4 gap-2 border-b bg-yellow-50 px-3 py-2">
        <div className="bg-white px-3 py-2 rounded border text-center">
          <div className="text-xs text-gray-600">전기이월</div>
          <div className="text-sm font-bold">{totals.prevBalance.toLocaleString()}원</div>
        </div>
        <div className="bg-white px-3 py-2 rounded border text-center">
          <div className="text-xs text-gray-600">입금합계</div>
          <div className="text-sm font-bold text-blue-600">{totals.depositAmount.toLocaleString()}원</div>
        </div>
        <div className="bg-white px-3 py-2 rounded border text-center">
          <div className="text-xs text-gray-600">출금합계</div>
          <div className="text-sm font-bold text-red-600">{totals.withdrawAmount.toLocaleString()}원</div>
        </div>
        <div className="bg-white px-3 py-2 rounded border text-center">
          <div className="text-xs text-gray-600">현잔액</div>
          <div className="text-sm font-bold text-green-600">{totals.currentBalance.toLocaleString()}원</div>
        </div>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-32">계정과목</th>
              <th className="border border-gray-400 px-2 py-1 w-24">유형</th>
              <th className="border border-gray-400 px-2 py-1 w-32">전기이월</th>
              <th className="border border-gray-400 px-2 py-1 w-32">입금액</th>
              <th className="border border-gray-400 px-2 py-1 w-32">출금액</th>
              <th className="border border-gray-400 px-2 py-1 w-32">현잔액</th>
              <th className="border border-gray-400 px-2 py-1">증감</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item) => {
              const change = item.depositAmount - item.withdrawAmount;
              return (
                <tr
                  key={item.id}
                  className={`cursor-pointer ${
                    selectedId === item.id
                      ? "bg-[#316AC5] text-white"
                      : "hover:bg-gray-100"
                  }`}
                  onClick={() => setSelectedId(item.id)}
                >
                  <td className="border border-gray-300 px-2 py-1 font-medium">{item.category}</td>
                  <td className="border border-gray-300 px-2 py-1">{item.categoryType}</td>
                  <td className="border border-gray-300 px-2 py-1 text-right">
                    {item.prevBalance.toLocaleString()}
                  </td>
                  <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">
                    {item.depositAmount.toLocaleString()}
                  </td>
                  <td className="border border-gray-300 px-2 py-1 text-right text-red-600">
                    {item.withdrawAmount.toLocaleString()}
                  </td>
                  <td className="border border-gray-300 px-2 py-1 text-right font-medium">
                    {item.currentBalance.toLocaleString()}
                  </td>
                  <td className={`border border-gray-300 px-2 py-1 text-right font-medium ${
                    change > 0 ? "text-blue-600" : change < 0 ? "text-red-600" : ""
                  }`}>
                    {change > 0 ? "+" : ""}{change.toLocaleString()}
                  </td>
                </tr>
              );
            })}
            {/* 유형별 소계 */}
            {Object.entries(typeSummary).map(([type, summary]) => (
              <tr key={type} className="bg-blue-50 font-medium">
                <td className="border border-gray-400 px-2 py-1" colSpan={2}>
                  ({type} 소계)
                </td>
                <td className="border border-gray-400 px-2 py-1 text-right">
                  {summary.prevBalance.toLocaleString()}
                </td>
                <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                  {summary.depositAmount.toLocaleString()}
                </td>
                <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                  {summary.withdrawAmount.toLocaleString()}
                </td>
                <td className="border border-gray-400 px-2 py-1 text-right">
                  {summary.currentBalance.toLocaleString()}
                </td>
                <td className="border border-gray-400 px-2 py-1 text-right">
                  {(summary.depositAmount - summary.withdrawAmount).toLocaleString()}
                </td>
              </tr>
            ))}
            {/* 총계 행 */}
            <tr className="bg-gray-200 font-bold">
              <td className="border border-gray-400 px-2 py-1" colSpan={2}>
                (총   계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.prevBalance.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.depositAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.withdrawAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.currentBalance.toLocaleString()}
              </td>
              <td className={`border border-gray-400 px-2 py-1 text-right ${
                totals.depositAmount - totals.withdrawAmount > 0 ? "text-blue-600" : "text-red-600"
              }`}>
                {(totals.depositAmount - totals.withdrawAmount).toLocaleString()}
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
