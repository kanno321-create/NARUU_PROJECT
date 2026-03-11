"use client";

import React, { useState } from "react";

interface ReceivablesPayablesItem {
  id: string;
  customerCode: string;
  customerName: string;
  customerType: string;
  prevBalance: number;
  transactionAmount: number;
  collectionPayment: number;
  currentBalance: number;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: ReceivablesPayablesItem[] = [
  {
    id: "1",
    customerCode: "c001",
    customerName: "테스트사업장",
    customerType: "매출처",
    prevBalance: 100000,
    transactionAmount: 233200,
    collectionPayment: 180000,
    currentBalance: 153200,
  },
  {
    id: "2",
    customerCode: "c002",
    customerName: "제고사업장",
    customerType: "매출처",
    prevBalance: 50000,
    transactionAmount: 133100,
    collectionPayment: 150000,
    currentBalance: 33100,
  },
  {
    id: "3",
    customerCode: "v001",
    customerName: "공급업체A",
    customerType: "매입처",
    prevBalance: -50000,
    transactionAmount: -371250,
    collectionPayment: -300000,
    currentBalance: -121250,
  },
  {
    id: "4",
    customerCode: "v002",
    customerName: "공급업체B",
    customerType: "매입처",
    prevBalance: 0,
    transactionAmount: -110000,
    collectionPayment: -50000,
    currentBalance: -60000,
  },
  {
    id: "5",
    customerCode: "v003",
    customerName: "공급업체C",
    customerType: "매입처",
    prevBalance: -30000,
    transactionAmount: -156750,
    collectionPayment: -80000,
    currentBalance: -106750,
  },
];

export function ReceivablesPayablesByCustomer() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [customerSearch, setCustomerSearch] = useState("");
  const [customerType, setCustomerType] = useState("전체");
  const [data] = useState<ReceivablesPayablesItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      (item.customerCode.includes(customerSearch) ||
        item.customerName.includes(customerSearch)) &&
      (customerType === "전체" || item.customerType === customerType)
  );

  // 누계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      prevBalance: acc.prevBalance + item.prevBalance,
      transactionAmount: acc.transactionAmount + item.transactionAmount,
      collectionPayment: acc.collectionPayment + item.collectionPayment,
      currentBalance: acc.currentBalance + item.currentBalance,
    }),
    { prevBalance: 0, transactionAmount: 0, collectionPayment: 0, currentBalance: 0 }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">거래처별미수미지급현황</span>
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
          <span className="text-xs">구분:</span>
          <select
            value={customerType}
            onChange={(e) => setCustomerType(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="매출처">매출처(미수)</option>
            <option value="매입처">매입처(미지급)</option>
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
              <th className="border border-gray-400 px-2 py-1 w-20">거래처코드</th>
              <th className="border border-gray-400 px-2 py-1 w-28">거래처명</th>
              <th className="border border-gray-400 px-2 py-1 w-16">구분</th>
              <th className="border border-gray-400 px-2 py-1 w-28">전기잔액</th>
              <th className="border border-gray-400 px-2 py-1 w-28">거래금액</th>
              <th className="border border-gray-400 px-2 py-1 w-28">수금/지급</th>
              <th className="border border-gray-400 px-2 py-1">현잔액</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr
                key={item.id}
                className={`cursor-pointer ${
                  selectedId === item.id
                    ? "bg-[#316AC5] text-white"
                    : item.customerType === "매입처"
                    ? "bg-red-50 hover:bg-red-100"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1">{item.customerCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerType}</td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${
                  item.prevBalance < 0 ? "text-red-600" : ""
                }`}>
                  {item.prevBalance.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${
                  item.transactionAmount < 0 ? "text-red-600" : ""
                }`}>
                  {item.transactionAmount.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${
                  item.collectionPayment < 0 ? "text-red-600" : ""
                }`}>
                  {item.collectionPayment.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right font-medium ${
                  item.currentBalance < 0 ? "text-red-600" : "text-blue-600"
                }`}>
                  {item.currentBalance.toLocaleString()}
                </td>
              </tr>
            ))}
            {/* 누계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={3}>
                (누계)
              </td>
              <td className={`border border-gray-400 px-2 py-1 text-right ${
                totals.prevBalance < 0 ? "text-red-600" : ""
              }`}>
                {totals.prevBalance.toLocaleString()}
              </td>
              <td className={`border border-gray-400 px-2 py-1 text-right ${
                totals.transactionAmount < 0 ? "text-red-600" : ""
              }`}>
                {totals.transactionAmount.toLocaleString()}
              </td>
              <td className={`border border-gray-400 px-2 py-1 text-right ${
                totals.collectionPayment < 0 ? "text-red-600" : ""
              }`}>
                {totals.collectionPayment.toLocaleString()}
              </td>
              <td className={`border border-gray-400 px-2 py-1 text-right ${
                totals.currentBalance < 0 ? "text-red-600" : "text-blue-600"
              }`}>
                {totals.currentBalance.toLocaleString()}
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
