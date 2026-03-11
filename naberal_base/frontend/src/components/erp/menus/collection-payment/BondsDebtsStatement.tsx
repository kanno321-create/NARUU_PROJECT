"use client";

import React, { useState } from "react";

interface BondsDebtsItem {
  id: string;
  date: string;
  docNo: string;
  customerCode: string;
  customerName: string;
  docType: string;
  bondAmount: number;
  debtAmount: number;
  balance: number;
  memo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: BondsDebtsItem[] = [
  {
    id: "1",
    date: "2025-12-05",
    docNo: "S2025120501",
    customerCode: "c001",
    customerName: "테스트사업장",
    docType: "매출",
    bondAmount: 233200,
    debtAmount: 0,
    balance: 153200,
    memo: "",
  },
  {
    id: "2",
    date: "2025-12-05",
    docNo: "R2025120501",
    customerCode: "c001",
    customerName: "테스트사업장",
    docType: "수금",
    bondAmount: 0,
    debtAmount: 180000,
    balance: 153200,
    memo: "현금수금",
  },
  {
    id: "3",
    date: "2025-12-04",
    docNo: "S2025120401",
    customerCode: "c002",
    customerName: "제고사업장",
    docType: "매출",
    bondAmount: 133100,
    debtAmount: 0,
    balance: 33100,
    memo: "",
  },
  {
    id: "4",
    date: "2025-12-04",
    docNo: "R2025120401",
    customerCode: "c002",
    customerName: "제고사업장",
    docType: "수금",
    bondAmount: 0,
    debtAmount: 150000,
    balance: 33100,
    memo: "계좌이체",
  },
  {
    id: "5",
    date: "2025-12-03",
    docNo: "P2025120301",
    customerCode: "v001",
    customerName: "공급업체A",
    docType: "매입",
    bondAmount: 0,
    debtAmount: 371250,
    balance: -121250,
    memo: "",
  },
  {
    id: "6",
    date: "2025-12-03",
    docNo: "Y2025120301",
    customerCode: "v001",
    customerName: "공급업체A",
    docType: "지급",
    bondAmount: 300000,
    debtAmount: 0,
    balance: -121250,
    memo: "계좌이체",
  },
];

export function BondsDebtsStatement() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [customerSearch, setCustomerSearch] = useState("");
  const [docTypeFilter, setDocTypeFilter] = useState("전체");
  const [data] = useState<BondsDebtsItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      (customerSearch === "" ||
        item.customerCode.includes(customerSearch) ||
        item.customerName.includes(customerSearch)) &&
      (docTypeFilter === "전체" || item.docType === docTypeFilter)
  );

  // 누계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      bondAmount: acc.bondAmount + item.bondAmount,
      debtAmount: acc.debtAmount + item.debtAmount,
    }),
    { bondAmount: 0, debtAmount: 0 }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">채권채무명세서</span>
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
          <span className="text-xs">유형:</span>
          <select
            value={docTypeFilter}
            onChange={(e) => setDocTypeFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="매출">매출</option>
            <option value="수금">수금</option>
            <option value="매입">매입</option>
            <option value="지급">지급</option>
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
              <th className="border border-gray-400 px-2 py-1 w-24">일자</th>
              <th className="border border-gray-400 px-2 py-1 w-28">전표번호</th>
              <th className="border border-gray-400 px-2 py-1 w-20">거래처코드</th>
              <th className="border border-gray-400 px-2 py-1 w-28">거래처명</th>
              <th className="border border-gray-400 px-2 py-1 w-16">유형</th>
              <th className="border border-gray-400 px-2 py-1 w-28">채권(차변)</th>
              <th className="border border-gray-400 px-2 py-1 w-28">채무(대변)</th>
              <th className="border border-gray-400 px-2 py-1 w-28">잔액</th>
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
                    : item.docType === "매입" || item.docType === "지급"
                    ? "bg-red-50 hover:bg-red-100"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1">{item.date}</td>
                <td className="border border-gray-300 px-2 py-1">{item.docNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.docType}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.bondAmount > 0 ? item.bondAmount.toLocaleString() : ""}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.debtAmount > 0 ? item.debtAmount.toLocaleString() : ""}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right font-medium ${
                  item.balance < 0 ? "text-red-600" : "text-blue-600"
                }`}>
                  {item.balance.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.memo}</td>
              </tr>
            ))}
            {/* 누계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={5}>
                (누계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.bondAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.debtAmount.toLocaleString()}
              </td>
              <td className={`border border-gray-400 px-2 py-1 text-right ${
                totals.bondAmount - totals.debtAmount < 0 ? "text-red-600" : "text-blue-600"
              }`}>
                {(totals.bondAmount - totals.debtAmount).toLocaleString()}
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
