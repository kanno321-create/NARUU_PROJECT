"use client";

import React, { useState } from "react";

interface PurchaseItem {
  id: string;
  date: string;
  vendorCode: string;
  vendorName: string;
  productCode: string;
  productName: string;
  spec: string;
  qty: number;
  unitPrice: number;
  supplyAmount: number;
  tax: number;
  totalAmount: number;
  memo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: PurchaseItem[] = [
  {
    id: "1",
    date: "2025-12-05",
    vendorCode: "v001",
    vendorName: "공급업체A",
    productCode: "p001",
    productName: "원자재A",
    spec: "100×50",
    qty: 100,
    unitPrice: 1000,
    supplyAmount: 100000,
    tax: 10000,
    totalAmount: 110000,
    memo: "",
  },
  {
    id: "2",
    date: "2025-12-05",
    vendorCode: "v001",
    vendorName: "공급업체A",
    productCode: "p002",
    productName: "원자재B",
    spec: "200×100",
    qty: 50,
    unitPrice: 2000,
    supplyAmount: 100000,
    tax: 10000,
    totalAmount: 110000,
    memo: "",
  },
  {
    id: "3",
    date: "2025-12-04",
    vendorCode: "v002",
    vendorName: "공급업체B",
    productCode: "p003",
    productName: "부품A",
    spec: "50×30",
    qty: 200,
    unitPrice: 500,
    supplyAmount: 100000,
    tax: 10000,
    totalAmount: 110000,
    memo: "긴급발주",
  },
  {
    id: "4",
    date: "2025-12-03",
    vendorCode: "v003",
    vendorName: "공급업체C",
    productCode: "p001",
    productName: "원자재A",
    spec: "100×50",
    qty: 150,
    unitPrice: 950,
    supplyAmount: 142500,
    tax: 14250,
    totalAmount: 156750,
    memo: "",
  },
];

export function PurchaseStatement() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [vendorSearch, setVendorSearch] = useState("");
  const [productSearch, setProductSearch] = useState("");
  const [data] = useState<PurchaseItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      (vendorSearch === "" ||
        item.vendorCode.includes(vendorSearch) ||
        item.vendorName.includes(vendorSearch)) &&
      (productSearch === "" ||
        item.productCode.includes(productSearch) ||
        item.productName.includes(productSearch))
  );

  // 일계 계산 (오늘 날짜)
  const dailyData = filteredData.filter((item) => item.date === "2025-12-05");
  const dailyTotals = dailyData.reduce(
    (acc, item) => ({
      qty: acc.qty + item.qty,
      supplyAmount: acc.supplyAmount + item.supplyAmount,
      tax: acc.tax + item.tax,
      totalAmount: acc.totalAmount + item.totalAmount,
    }),
    { qty: 0, supplyAmount: 0, tax: 0, totalAmount: 0 }
  );

  // 월계 계산 (이번 달)
  const monthlyData = filteredData.filter((item) =>
    item.date.startsWith("2025-12")
  );
  const monthlyTotals = monthlyData.reduce(
    (acc, item) => ({
      qty: acc.qty + item.qty,
      supplyAmount: acc.supplyAmount + item.supplyAmount,
      tax: acc.tax + item.tax,
      totalAmount: acc.totalAmount + item.totalAmount,
    }),
    { qty: 0, supplyAmount: 0, tax: 0, totalAmount: 0 }
  );

  // 누계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      qty: acc.qty + item.qty,
      supplyAmount: acc.supplyAmount + item.supplyAmount,
      tax: acc.tax + item.tax,
      totalAmount: acc.totalAmount + item.totalAmount,
    }),
    { qty: 0, supplyAmount: 0, tax: 0, totalAmount: 0 }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">매입명세서</span>
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
        <div className="flex items-center gap-2">
          <span className="text-xs">상품:</span>
          <input
            type="text"
            value={productSearch}
            onChange={(e) => setProductSearch(e.target.value)}
            placeholder="상품명/코드"
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
              <th className="border border-gray-400 px-2 py-1 w-16">거래처코드</th>
              <th className="border border-gray-400 px-2 py-1 w-24">거래처명</th>
              <th className="border border-gray-400 px-2 py-1 w-16">상품코드</th>
              <th className="border border-gray-400 px-2 py-1 w-24">상품명</th>
              <th className="border border-gray-400 px-2 py-1 w-16">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-14">수량</th>
              <th className="border border-gray-400 px-2 py-1 w-20">단가</th>
              <th className="border border-gray-400 px-2 py-1 w-24">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">세액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">합계금액</th>
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
                <td className="border border-gray-300 px-2 py-1">{item.vendorCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.vendorName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.productCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.productName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.spec}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.qty}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.unitPrice.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.supplyAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.tax.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.totalAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.memo}</td>
              </tr>
            ))}
            {/* 일계 행 */}
            <tr className="bg-yellow-50 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={6}>
                (일계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {dailyTotals.qty}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {dailyTotals.supplyAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {dailyTotals.tax.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {dailyTotals.totalAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
            </tr>
            {/* 월계 행 */}
            <tr className="bg-blue-50 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={6}>
                (월계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {monthlyTotals.qty}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {monthlyTotals.supplyAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {monthlyTotals.tax.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {monthlyTotals.totalAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
            </tr>
            {/* 누계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={6}>
                (누계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.qty}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.supplyAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.tax.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.totalAmount.toLocaleString()}
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
