"use client";

import React, { useState } from "react";

interface PurchasePriceHistoryItem {
  id: string;
  changeDate: string;
  vendorCode: string;
  vendorName: string;
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
const ORIGINAL_DATA: PurchasePriceHistoryItem[] = [
  {
    id: "1",
    changeDate: "2025-12-01",
    vendorCode: "v001",
    vendorName: "공급업체A",
    productCode: "p001",
    productName: "원자재A",
    spec: "100×50",
    beforePrice: 950,
    afterPrice: 1000,
    changeRate: 5.3,
    changeReason: "원자재가격 상승",
    changedBy: "관리자",
  },
  {
    id: "2",
    changeDate: "2025-12-01",
    vendorCode: "v001",
    vendorName: "공급업체A",
    productCode: "p002",
    productName: "원자재B",
    spec: "200×100",
    beforePrice: 1900,
    afterPrice: 2000,
    changeRate: 5.3,
    changeReason: "원자재가격 상승",
    changedBy: "관리자",
  },
  {
    id: "3",
    changeDate: "2025-11-15",
    vendorCode: "v002",
    vendorName: "공급업체B",
    productCode: "p003",
    productName: "부품A",
    spec: "50×30",
    beforePrice: 550,
    afterPrice: 500,
    changeRate: -9.1,
    changeReason: "대량구매 협상",
    changedBy: "관리자",
  },
  {
    id: "4",
    changeDate: "2025-11-01",
    vendorCode: "v003",
    vendorName: "공급업체C",
    productCode: "p001",
    productName: "원자재A",
    spec: "100×50",
    beforePrice: 1000,
    afterPrice: 950,
    changeRate: -5.0,
    changeReason: "경쟁입찰 결과",
    changedBy: "관리자",
  },
  {
    id: "5",
    changeDate: "2025-10-15",
    vendorCode: "v001",
    vendorName: "공급업체A",
    productCode: "p001",
    productName: "원자재A",
    spec: "100×50",
    beforePrice: 900,
    afterPrice: 950,
    changeRate: 5.6,
    changeReason: "환율 변동",
    changedBy: "관리자",
  },
];

export function PurchasePriceHistory() {
  const [startDate, setStartDate] = useState("2025-10-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [vendorSearch, setVendorSearch] = useState("");
  const [productSearch, setProductSearch] = useState("");
  const [data] = useState<PurchasePriceHistoryItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      item.changeDate >= startDate &&
      item.changeDate <= endDate &&
      (vendorSearch === "" ||
        item.vendorCode.includes(vendorSearch) ||
        item.vendorName.includes(vendorSearch)) &&
      (productSearch === "" ||
        item.productCode.includes(productSearch) ||
        item.productName.includes(productSearch))
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">매입단가변경이력</span>
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
              <th className="border border-gray-400 px-2 py-1 w-24">변경일자</th>
              <th className="border border-gray-400 px-2 py-1 w-16">거래처코드</th>
              <th className="border border-gray-400 px-2 py-1 w-24">거래처명</th>
              <th className="border border-gray-400 px-2 py-1 w-16">상품코드</th>
              <th className="border border-gray-400 px-2 py-1 w-24">상품명</th>
              <th className="border border-gray-400 px-2 py-1 w-14">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-20">변경전단가</th>
              <th className="border border-gray-400 px-2 py-1 w-20">변경후단가</th>
              <th className="border border-gray-400 px-2 py-1 w-14">변동율(%)</th>
              <th className="border border-gray-400 px-2 py-1 w-24">변경사유</th>
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
                <td className="border border-gray-300 px-2 py-1">{item.vendorCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.vendorName}</td>
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
