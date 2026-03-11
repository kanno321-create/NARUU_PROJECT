"use client";

import React, { useState } from "react";

interface VendorLedgerBItem {
  id: string;
  date: string;
  productCode: string;
  productName: string;
  spec: string;
  category: string;
  quantity: number;
  unitPrice: number;
  supplyAmount: number;
  tax: number;
  amount: number;
  receivable: number;
  slipNo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: VendorLedgerBItem[] = [
  {
    id: "1",
    date: "2025-12-05",
    productCode: "e0001",
    productName: "핸드폰케이스",
    spec: "10×10",
    category: "매출",
    quantity: 1,
    unitPrice: 12000,
    supplyAmount: 12000,
    tax: 1200,
    amount: 13200,
    receivable: 13200,
    slipNo: "1",
  },
  {
    id: "2",
    date: "2025-12-05",
    productCode: "e0002",
    productName: "노트북케이스",
    spec: "20×25",
    category: "매출",
    quantity: 10,
    unitPrice: 20000,
    supplyAmount: 200000,
    tax: 20000,
    amount: 220000,
    receivable: 233200,
    slipNo: "1",
  },
  {
    id: "3",
    date: "2025-12-05",
    productCode: "",
    productName: "외상수금",
    spec: "",
    category: "수금",
    quantity: 0,
    unitPrice: 0,
    supplyAmount: 0,
    tax: 0,
    amount: 100000,
    receivable: 133200,
    slipNo: "",
  },
];

export function SalesVendorLedgerB() {
  const [startDate, setStartDate] = useState("2025-12-05");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [vendorSearch, setVendorSearch] = useState("테스트사업장");
  const [data] = useState<VendorLedgerBItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // 합계 계산
  const totals = data.reduce(
    (acc, item) => ({
      quantity: acc.quantity + item.quantity,
      supplyAmount: acc.supplyAmount + item.supplyAmount,
      tax: acc.tax + item.tax,
      amount: acc.amount + item.amount,
    }),
    { quantity: 0, supplyAmount: 0, tax: 0, amount: 0 }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">매출처원장(B형)</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📊</span> 보고서추력
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🖨️</span> 표시항목 ▼
        </button>
      </div>

      {/* 안내 메시지 */}
      <div className="bg-blue-50 px-3 py-1 text-xs text-blue-700">
        • 환경설정에서 '매출건조작성시 원가재산' 항목이 체크를 해제하신 경우 원가관리(원가,재고금액,이익등) 보고서를 표시하기전에 원가재계산을 실행하셔야 정확한 데이터가 표시됩니다.
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
          회근판달금색(F2)
        </button>
        <div className="flex items-center gap-2">
          <span className="text-xs">매출처검색:</span>
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
              <th className="border border-gray-400 px-2 py-1 w-24">일자</th>
              <th className="border border-gray-400 px-2 py-1 w-20">상품코드</th>
              <th className="border border-gray-400 px-2 py-1 w-28">품목명</th>
              <th className="border border-gray-400 px-2 py-1 w-20">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-16">구분</th>
              <th className="border border-gray-400 px-2 py-1 w-16">수량</th>
              <th className="border border-gray-400 px-2 py-1 w-20">단가</th>
              <th className="border border-gray-400 px-2 py-1 w-24">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">세액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">금액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">미수금</th>
              <th className="border border-gray-400 px-2 py-1">전표번호</th>
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
                <td className="border border-gray-300 px-2 py-1">{item.productCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.productName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.spec}</td>
                <td className="border border-gray-300 px-2 py-1">{item.category}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.quantity > 0 ? item.quantity : ""}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.unitPrice > 0 ? item.unitPrice.toLocaleString() : ""}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.supplyAmount > 0 ? item.supplyAmount.toLocaleString() : ""}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.tax > 0 ? item.tax.toLocaleString() : ""}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.amount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.receivable.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.slipNo}</td>
              </tr>
            ))}
            {/* 일계 행 */}
            <tr className="bg-yellow-50">
              <td className="border border-gray-400 px-2 py-1" colSpan={5}>
                (일계:2025-12-05)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {totals.quantity}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {totals.supplyAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {totals.tax.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {totals.amount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={2}></td>
            </tr>
            {/* 월계 행 */}
            <tr className="bg-blue-50">
              <td className="border border-gray-400 px-2 py-1" colSpan={5}>
                (월계:2025-12)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {totals.quantity}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {totals.supplyAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {totals.tax.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {totals.amount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={2}></td>
            </tr>
            {/* 누계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={5}>
                (누계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.quantity}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.supplyAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.tax.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.amount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={2}></td>
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
