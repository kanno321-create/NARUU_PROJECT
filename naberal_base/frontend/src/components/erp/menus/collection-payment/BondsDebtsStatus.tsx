"use client";

import React, { useState } from "react";

interface BondsDebtsStatusItem {
  id: string;
  customerCode: string;
  customerName: string;
  customerType: string;
  prevBond: number;
  currentBond: number;
  prevDebt: number;
  currentDebt: number;
  netBalance: number;
  status: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: BondsDebtsStatusItem[] = [
  {
    id: "1",
    customerCode: "c001",
    customerName: "테스트사업장",
    customerType: "매출처",
    prevBond: 100000,
    currentBond: 153200,
    prevDebt: 0,
    currentDebt: 0,
    netBalance: 153200,
    status: "채권",
  },
  {
    id: "2",
    customerCode: "c002",
    customerName: "제고사업장",
    customerType: "매출처",
    prevBond: 50000,
    currentBond: 33100,
    prevDebt: 0,
    currentDebt: 0,
    netBalance: 33100,
    status: "채권",
  },
  {
    id: "3",
    customerCode: "v001",
    customerName: "공급업체A",
    customerType: "매입처",
    prevBond: 0,
    currentBond: 0,
    prevDebt: 50000,
    currentDebt: 121250,
    netBalance: -121250,
    status: "채무",
  },
  {
    id: "4",
    customerCode: "v002",
    customerName: "공급업체B",
    customerType: "매입처",
    prevBond: 0,
    currentBond: 0,
    prevDebt: 0,
    currentDebt: 60000,
    netBalance: -60000,
    status: "채무",
  },
  {
    id: "5",
    customerCode: "v003",
    customerName: "공급업체C",
    customerType: "매입처",
    prevBond: 0,
    currentBond: 0,
    prevDebt: 30000,
    currentDebt: 106750,
    netBalance: -106750,
    status: "채무",
  },
];

export function BondsDebtsStatus() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [customerSearch, setCustomerSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("전체");
  const [data] = useState<BondsDebtsStatusItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      (customerSearch === "" ||
        item.customerCode.includes(customerSearch) ||
        item.customerName.includes(customerSearch)) &&
      (statusFilter === "전체" || item.status === statusFilter)
  );

  // 누계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      prevBond: acc.prevBond + item.prevBond,
      currentBond: acc.currentBond + item.currentBond,
      prevDebt: acc.prevDebt + item.prevDebt,
      currentDebt: acc.currentDebt + item.currentDebt,
      netBalance: acc.netBalance + item.netBalance,
    }),
    { prevBond: 0, currentBond: 0, prevDebt: 0, currentDebt: 0, netBalance: 0 }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">채권채무현황</span>
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
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🖨️</span> 표시항목 ▼
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
          <span className="text-xs">상태:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="채권">채권(받을돈)</option>
            <option value="채무">채무(줄돈)</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">거래처검색:</span>
          <input
            type="text"
            value={customerSearch}
            onChange={(e) => setCustomerSearch(e.target.value)}
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
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>구분</th>
              <th className="border border-gray-400 px-2 py-1 bg-blue-100" colSpan={2}>채권(받을금액)</th>
              <th className="border border-gray-400 px-2 py-1 bg-red-100" colSpan={2}>채무(줄금액)</th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>순잔액</th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>상태</th>
            </tr>
            <tr>
              <th className="border border-gray-400 px-2 py-1 bg-blue-50 w-24">전기잔액</th>
              <th className="border border-gray-400 px-2 py-1 bg-blue-50 w-24">현잔액</th>
              <th className="border border-gray-400 px-2 py-1 bg-red-50 w-24">전기잔액</th>
              <th className="border border-gray-400 px-2 py-1 bg-red-50 w-24">현잔액</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr
                key={item.id}
                className={`cursor-pointer ${
                  selectedId === item.id
                    ? "bg-[#316AC5] text-white"
                    : item.status === "채무"
                    ? "bg-red-50 hover:bg-red-100"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1">{item.customerCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerType}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.prevBond.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${
                  item.currentBond > 0 ? "text-blue-600 font-medium" : ""
                }`}>
                  {item.currentBond.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.prevDebt.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${
                  item.currentDebt > 0 ? "text-red-600 font-medium" : ""
                }`}>
                  {item.currentDebt.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right font-bold ${
                  item.netBalance < 0 ? "text-red-600" : "text-blue-600"
                }`}>
                  {item.netBalance.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-center font-medium ${
                  item.status === "채무" ? "text-red-600" : "text-blue-600"
                }`}>
                  {item.status}
                </td>
              </tr>
            ))}
            {/* 누계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={3}>
                (누계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.prevBond.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.currentBond.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.prevDebt.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.currentDebt.toLocaleString()}
              </td>
              <td className={`border border-gray-400 px-2 py-1 text-right font-bold ${
                totals.netBalance < 0 ? "text-red-600" : "text-blue-600"
              }`}>
                {totals.netBalance.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 하단 요약 정보 */}
      <div className="flex items-center gap-6 border-t bg-yellow-50 px-3 py-2 text-xs">
        <span className="font-medium">요약:</span>
        <span className="text-blue-600">
          총 채권: {totals.currentBond.toLocaleString()}원
        </span>
        <span className="text-red-600">
          총 채무: {totals.currentDebt.toLocaleString()}원
        </span>
        <span className={totals.netBalance >= 0 ? "text-blue-600 font-bold" : "text-red-600 font-bold"}>
          순잔액: {totals.netBalance.toLocaleString()}원
        </span>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredData.length}건 | loading ok
      </div>
    </div>
  );
}
