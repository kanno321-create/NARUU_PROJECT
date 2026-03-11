"use client";

import React, { useState } from "react";

interface ProductSummaryItem {
  id: string;
  productCode: string;
  productName: string;
  spec: string;
  detailSpec: string;
  salesQty: number;
  supplyAmount: number;
  tax: number;
  salesAmount: number;
  salesCost: number;
  salesProfit: number;
  profitMargin: number;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: ProductSummaryItem[] = [
  {
    id: "1",
    productCode: "e0001",
    productName: "핸드폰케이스",
    spec: "10×10",
    detailSpec: "100×100",
    salesQty: 1,
    supplyAmount: 12000,
    tax: 1200,
    salesAmount: 13200,
    salesCost: 10000,
    salesProfit: 3200,
    profitMargin: 24.2,
  },
  {
    id: "2",
    productCode: "e0002",
    productName: "노트북케이스",
    spec: "20×25",
    detailSpec: "200×300",
    salesQty: 15,
    supplyAmount: 300000,
    tax: 30000,
    salesAmount: 330000,
    salesCost: 225000,
    salesProfit: 105000,
    profitMargin: 31.8,
  },
  {
    id: "3",
    productCode: "e0003",
    productName: "키보드케이스",
    spec: "300×400",
    detailSpec: "350×450",
    salesQty: 3,
    supplyAmount: 21000,
    tax: 2100,
    salesAmount: 23100,
    salesCost: 13500,
    salesProfit: 9600,
    profitMargin: 41.6,
  },
];

export function SalesByProductSummary() {
  const [startDate, setStartDate] = useState("2025-12-05");
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
      salesQty: acc.salesQty + item.salesQty,
      supplyAmount: acc.supplyAmount + item.supplyAmount,
      tax: acc.tax + item.tax,
      salesAmount: acc.salesAmount + item.salesAmount,
      salesCost: acc.salesCost + item.salesCost,
      salesProfit: acc.salesProfit + item.salesProfit,
    }),
    {
      salesQty: 0,
      supplyAmount: 0,
      tax: 0,
      salesAmount: 0,
      salesCost: 0,
      salesProfit: 0,
    }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">상품별매출집계표</span>
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
              <th className="border border-gray-400 px-2 py-1 w-20">상품코드</th>
              <th className="border border-gray-400 px-2 py-1 w-28">상품명</th>
              <th className="border border-gray-400 px-2 py-1 w-20">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-24">상세규격</th>
              <th className="border border-gray-400 px-2 py-1 w-16">매출수량</th>
              <th className="border border-gray-400 px-2 py-1 w-24">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">세액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">매출액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">매출원가</th>
              <th className="border border-gray-400 px-2 py-1 w-24">매출이익</th>
              <th className="border border-gray-400 px-2 py-1">이익률(%)</th>
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
                <td className="border border-gray-300 px-2 py-1">{item.detailSpec}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.salesQty}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.supplyAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.tax.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.salesAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.salesCost.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.salesProfit.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.profitMargin.toFixed(1)}
                </td>
              </tr>
            ))}
            {/* 누계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={4}>
                (누계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.salesQty}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.supplyAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.tax.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.salesAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.salesCost.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.salesProfit.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {((totals.salesProfit / totals.salesAmount) * 100).toFixed(1)}
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
