"use client";

import React, { useState } from "react";

interface ProductSummaryItem {
  id: string;
  productCode: string;
  productName: string;
  spec: string;
  purchaseQty: number;
  supplyAmount: number;
  tax: number;
  purchaseAmount: number;
  purchaseCost: number;
  vendorCount: number;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: ProductSummaryItem[] = [
  {
    id: "1",
    productCode: "p001",
    productName: "원자재A",
    spec: "100×50",
    purchaseQty: 400,
    supplyAmount: 380000,
    tax: 38000,
    purchaseAmount: 418000,
    purchaseCost: 950,
    vendorCount: 2,
  },
  {
    id: "2",
    productCode: "p002",
    productName: "원자재B",
    spec: "200×100",
    purchaseQty: 50,
    supplyAmount: 100000,
    tax: 10000,
    purchaseAmount: 110000,
    purchaseCost: 2000,
    vendorCount: 1,
  },
  {
    id: "3",
    productCode: "p003",
    productName: "부품A",
    spec: "50×30",
    purchaseQty: 200,
    supplyAmount: 100000,
    tax: 10000,
    purchaseAmount: 110000,
    purchaseCost: 500,
    vendorCount: 1,
  },
];

export function PurchaseByProductSummary() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [productSearch, setProductSearch] = useState("");
  const [data] = useState<ProductSummaryItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      item.productCode.includes(productSearch) ||
      item.productName.includes(productSearch)
  );

  // 누계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      purchaseQty: acc.purchaseQty + item.purchaseQty,
      supplyAmount: acc.supplyAmount + item.supplyAmount,
      tax: acc.tax + item.tax,
      purchaseAmount: acc.purchaseAmount + item.purchaseAmount,
    }),
    { purchaseQty: 0, supplyAmount: 0, tax: 0, purchaseAmount: 0 }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">상품별매입집계표</span>
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
          <span>🖨️</span> 표시항목 ▼
        </button>
      </div>

      {/* 안내 메시지 */}
      <div className="bg-blue-50 px-3 py-1 text-xs text-blue-700">
        • 상품별매입집계표: 상품별로 매입 금액을 집계하여 표시합니다.
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
          최근1달검색(F2)
        </button>
        <div className="flex items-center gap-2">
          <span className="text-xs">상품검색:</span>
          <input
            type="text"
            value={productSearch}
            onChange={(e) => setProductSearch(e.target.value)}
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
              <th className="border border-gray-400 px-2 py-1 w-16">상품코드</th>
              <th className="border border-gray-400 px-2 py-1 w-28">상품명</th>
              <th className="border border-gray-400 px-2 py-1 w-20">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-16">매입수량</th>
              <th className="border border-gray-400 px-2 py-1 w-24">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">세액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">매입금액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">평균단가</th>
              <th className="border border-gray-400 px-2 py-1">거래처수</th>
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
                <td className="border border-gray-300 px-2 py-1">{item.productCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.productName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.spec}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.purchaseQty}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.supplyAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.tax.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.purchaseAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.purchaseCost.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.vendorCount}
                </td>
              </tr>
            ))}
            {/* 누계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={3}>
                (누계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.purchaseQty}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.supplyAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.tax.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.purchaseAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
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
