"use client";

import React, { useState } from "react";

interface CompanySummaryDetailItem {
  id: string;
  vendorCode: string;
  vendorName: string;
  productCode: string;
  productName: string;
  spec: string;
  purchaseQty: number;
  supplyAmount: number;
  tax: number;
  purchaseAmount: number;
  avgUnitPrice: number;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: CompanySummaryDetailItem[] = [
  {
    id: "1",
    vendorCode: "v001",
    vendorName: "공급업체A",
    productCode: "p001",
    productName: "원자재A",
    spec: "100×50",
    purchaseQty: 250,
    supplyAmount: 237500,
    tax: 23750,
    purchaseAmount: 261250,
    avgUnitPrice: 950,
  },
  {
    id: "2",
    vendorCode: "v001",
    vendorName: "공급업체A",
    productCode: "p002",
    productName: "원자재B",
    spec: "200×100",
    purchaseQty: 50,
    supplyAmount: 100000,
    tax: 10000,
    purchaseAmount: 110000,
    avgUnitPrice: 2000,
  },
  {
    id: "3",
    vendorCode: "v002",
    vendorName: "공급업체B",
    productCode: "p003",
    productName: "부품A",
    spec: "50×30",
    purchaseQty: 200,
    supplyAmount: 100000,
    tax: 10000,
    purchaseAmount: 110000,
    avgUnitPrice: 500,
  },
  {
    id: "4",
    vendorCode: "v003",
    vendorName: "공급업체C",
    productCode: "p001",
    productName: "원자재A",
    spec: "100×50",
    purchaseQty: 150,
    supplyAmount: 142500,
    tax: 14250,
    purchaseAmount: 156750,
    avgUnitPrice: 950,
  },
];

export function PurchaseByCompanySummaryDetail() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [vendorSearch, setVendorSearch] = useState("");
  const [data] = useState<CompanySummaryDetailItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      item.vendorCode.includes(vendorSearch) ||
      item.vendorName.includes(vendorSearch)
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
        <span className="text-sm font-medium text-white">업체별매입집계표(상세)</span>
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
        • 업체별매입집계표(상세): 거래처(업체)별, 상품별로 상세 매입 내역을 표시합니다.
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
          <span className="text-xs">거래처검색:</span>
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
              <th className="border border-gray-400 px-2 py-1 w-16">업체코드</th>
              <th className="border border-gray-400 px-2 py-1 w-24">업체명</th>
              <th className="border border-gray-400 px-2 py-1 w-16">상품코드</th>
              <th className="border border-gray-400 px-2 py-1 w-24">상품명</th>
              <th className="border border-gray-400 px-2 py-1 w-16">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-14">매입수량</th>
              <th className="border border-gray-400 px-2 py-1 w-24">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">세액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">매입금액</th>
              <th className="border border-gray-400 px-2 py-1">평균단가</th>
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
                <td className="border border-gray-300 px-2 py-1">{item.vendorCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.vendorName}</td>
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
                  {item.avgUnitPrice.toLocaleString()}
                </td>
              </tr>
            ))}
            {/* 누계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={5}>
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
