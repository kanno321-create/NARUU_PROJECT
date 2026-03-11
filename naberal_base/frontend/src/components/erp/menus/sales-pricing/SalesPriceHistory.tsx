"use client";

import React, { useState } from "react";

interface SalesPriceHistoryItem {
  id: string;
  changeDate: string;
  productCode: string;
  productName: string;
  spec: string;
  beforePrice: number;
  afterPrice: number;
  changeRate: number;
  changeReason: string;
  changedBy: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: SalesPriceHistoryItem[] = [
  {
    id: "1",
    changeDate: "2025-12-01",
    productCode: "e0001",
    productName: "핸드폰케이스",
    spec: "10×10",
    beforePrice: 14000,
    afterPrice: 15000,
    changeRate: 7.1,
    changeReason: "원가상승 반영",
    changedBy: "관리자",
  },
  {
    id: "2",
    changeDate: "2025-12-01",
    productCode: "e0002",
    productName: "노트북케이스",
    spec: "20×25",
    beforePrice: 23000,
    afterPrice: 25000,
    changeRate: 8.7,
    changeReason: "원가상승 반영",
    changedBy: "관리자",
  },
  {
    id: "3",
    changeDate: "2025-11-15",
    productCode: "e0003",
    productName: "키보드케이스",
    spec: "300×400",
    beforePrice: 9000,
    afterPrice: 8000,
    changeRate: -11.1,
    changeReason: "재고정리 할인",
    changedBy: "관리자",
  },
  {
    id: "4",
    changeDate: "2025-11-01",
    productCode: "p001",
    productName: "원자재A",
    spec: "100×50",
    beforePrice: 1400,
    afterPrice: 1500,
    changeRate: 7.1,
    changeReason: "환율 변동",
    changedBy: "관리자",
  },
  {
    id: "5",
    changeDate: "2025-10-15",
    productCode: "e0001",
    productName: "핸드폰케이스",
    spec: "10×10",
    beforePrice: 13000,
    afterPrice: 14000,
    changeRate: 7.7,
    changeReason: "시장가격 조정",
    changedBy: "관리자",
  },
];

export function SalesPriceHistory() {
  const [startDate, setStartDate] = useState("2025-10-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [productSearch, setProductSearch] = useState("");
  const [data] = useState<SalesPriceHistoryItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      item.changeDate >= startDate &&
      item.changeDate <= endDate &&
      (productSearch === "" ||
        item.productCode.includes(productSearch) ||
        item.productName.includes(productSearch))
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">판매단가변경이력</span>
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
          <span className="text-xs">상품:</span>
          <input
            type="text"
            value={productSearch}
            onChange={(e) => setProductSearch(e.target.value)}
            placeholder="상품명/코드"
            className="w-32 rounded border border-gray-400 px-2 py-1 text-xs"
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
              <th className="border border-gray-400 px-2 py-1 w-24">변경일자</th>
              <th className="border border-gray-400 px-2 py-1 w-20">상품코드</th>
              <th className="border border-gray-400 px-2 py-1 w-28">상품명</th>
              <th className="border border-gray-400 px-2 py-1 w-16">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-24">변경전단가</th>
              <th className="border border-gray-400 px-2 py-1 w-24">변경후단가</th>
              <th className="border border-gray-400 px-2 py-1 w-16">변동율(%)</th>
              <th className="border border-gray-400 px-2 py-1 w-28">변경사유</th>
              <th className="border border-gray-400 px-2 py-1">변경자</th>
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
                <td className="border border-gray-300 px-2 py-1">{item.changeDate}</td>
                <td className="border border-gray-300 px-2 py-1">{item.productCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.productName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.spec}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.beforePrice.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600 font-medium">
                  {item.afterPrice.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right font-medium ${
                  item.changeRate > 0 ? "text-red-600" : item.changeRate < 0 ? "text-blue-600" : ""
                }`}>
                  {item.changeRate > 0 ? "+" : ""}{item.changeRate}%
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.changeReason}</td>
                <td className="border border-gray-300 px-2 py-1">{item.changedBy}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 하단 요약 */}
      <div className="flex items-center gap-6 border-t bg-yellow-50 px-3 py-2 text-xs">
        <span className="font-medium">이력 요약:</span>
        <span className="text-red-600">
          인상: {filteredData.filter((d) => d.changeRate > 0).length}건
        </span>
        <span className="text-blue-600">
          인하: {filteredData.filter((d) => d.changeRate < 0).length}건
        </span>
        <span>
          평균 변동율: {filteredData.length > 0
            ? (filteredData.reduce((acc, d) => acc + d.changeRate, 0) / filteredData.length).toFixed(1)
            : 0}%
        </span>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredData.length}건 | loading ok
      </div>
    </div>
  );
}
