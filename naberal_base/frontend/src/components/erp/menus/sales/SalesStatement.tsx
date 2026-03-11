"use client";

import React, { useState } from "react";

interface SalesItem {
  id: string;
  salesDate: string;
  customerName: string;
  productCode: string;
  productName: string;
  spec: string;
  detailSpec: string;
  category: string;
  quantity: number;
  unitPrice: number;
  supplyAmount: number;
  tax: number;
  salesCost: number;
  salesAmount: number;
  profit: number;
  isSample: boolean;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: SalesItem[] = [
  {
    id: "1",
    salesDate: "2025-12-05",
    customerName: "테스트사업장",
    productCode: "e0001",
    productName: "핸드폰케이스",
    spec: "10×10",
    detailSpec: "100×100",
    category: "매출",
    quantity: 1,
    unitPrice: 12000,
    supplyAmount: 12000,
    tax: 1200,
    salesCost: 10000,
    salesAmount: 13200,
    profit: 3200,
    isSample: false,
  },
  {
    id: "2",
    salesDate: "2025-12-05",
    customerName: "테스트사업장",
    productCode: "e0002",
    productName: "노트북케이스",
    spec: "20×25",
    detailSpec: "200×300",
    category: "매출",
    quantity: 10,
    unitPrice: 20000,
    supplyAmount: 200000,
    tax: 20000,
    salesCost: 150000,
    salesAmount: 220000,
    profit: 70000,
    isSample: false,
  },
  {
    id: "3",
    salesDate: "2025-12-05",
    customerName: "제고사업장",
    productCode: "e0002",
    productName: "노트북케이스",
    spec: "25×25",
    detailSpec: "250×300",
    category: "매출",
    quantity: 5,
    unitPrice: 20000,
    supplyAmount: 100000,
    tax: 10000,
    salesCost: 75000,
    salesAmount: 110000,
    profit: 35000,
    isSample: false,
  },
  {
    id: "4",
    salesDate: "2025-12-05",
    customerName: "제고사업장",
    productCode: "e0003",
    productName: "키보드케이스",
    spec: "300×400",
    detailSpec: "350×450",
    category: "매출",
    quantity: 3,
    unitPrice: 7000,
    supplyAmount: 21000,
    tax: 2100,
    salesCost: 13500,
    salesAmount: 23100,
    profit: 9600,
    isSample: false,
  },
];

export function SalesStatement() {
  const [startDate, setStartDate] = useState("2025-12-05");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [customerSearch, setCustomerSearch] = useState("");
  const [productSearch, setProductSearch] = useState("");
  const [data] = useState<SalesItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      (customerSearch === "" || item.customerName.includes(customerSearch)) &&
      (productSearch === "" ||
        item.productCode.includes(productSearch) ||
        item.productName.includes(productSearch))
  );

  // 일계, 월계, 누계 계산
  const dayTotals = filteredData.reduce(
    (acc, item) => ({
      quantity: acc.quantity + item.quantity,
      supplyAmount: acc.supplyAmount + item.supplyAmount,
      tax: acc.tax + item.tax,
      salesCost: acc.salesCost + item.salesCost,
      salesAmount: acc.salesAmount + item.salesAmount,
      profit: acc.profit + item.profit,
    }),
    { quantity: 0, supplyAmount: 0, tax: 0, salesCost: 0, salesAmount: 0, profit: 0 }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">매출명세서</span>
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
      <div className="flex flex-wrap items-center gap-4 border-b bg-white px-3 py-2">
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
          <span className="text-xs">거래처검색:</span>
          <input
            type="text"
            value={customerSearch}
            onChange={(e) => setCustomerSearch(e.target.value)}
            className="w-28 rounded border border-gray-400 px-2 py-1 text-xs"
          />
          <button className="rounded border border-gray-400 bg-gray-100 px-2 py-1 text-xs hover:bg-gray-200">
            ...
          </button>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">상품검색:</span>
          <input
            type="text"
            value={productSearch}
            onChange={(e) => setProductSearch(e.target.value)}
            className="w-28 rounded border border-gray-400 px-2 py-1 text-xs"
          />
          <button className="rounded border border-gray-400 bg-gray-100 px-2 py-1 text-xs hover:bg-gray-200">
            ...
          </button>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">사원검색:</span>
          <input
            type="text"
            className="w-28 rounded border border-gray-400 px-2 py-1 text-xs"
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
              <th className="border border-gray-400 px-2 py-1 w-24">매출일자</th>
              <th className="border border-gray-400 px-2 py-1 w-24">매출처(고객명)</th>
              <th className="border border-gray-400 px-2 py-1 w-20">상품코드</th>
              <th className="border border-gray-400 px-2 py-1 w-28">품목명</th>
              <th className="border border-gray-400 px-2 py-1 w-20">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-24">상세규격</th>
              <th className="border border-gray-400 px-2 py-1 w-16">구분</th>
              <th className="border border-gray-400 px-2 py-1 w-16">수량</th>
              <th className="border border-gray-400 px-2 py-1 w-20">단가</th>
              <th className="border border-gray-400 px-2 py-1 w-24">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">세액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">매출원가</th>
              <th className="border border-gray-400 px-2 py-1 w-24">매출원가</th>
              <th className="border border-gray-400 px-2 py-1 w-20">이익</th>
              <th className="border border-gray-400 px-2 py-1 w-16">견품제외</th>
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
                <td className="border border-gray-300 px-2 py-1">{item.salesDate}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.productCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.productName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.spec}</td>
                <td className="border border-gray-300 px-2 py-1">{item.detailSpec}</td>
                <td className="border border-gray-300 px-2 py-1">{item.category}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.quantity}
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
                  {item.salesCost.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.salesAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.profit.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  {item.isSample ? "✓" : ""}
                </td>
              </tr>
            ))}
            {/* 일계 행 */}
            <tr className="bg-yellow-50">
              <td className="border border-gray-400 px-2 py-1" colSpan={2}>
                (일계:2025-12-05)
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={5}></td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {dayTotals.quantity}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {dayTotals.supplyAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {dayTotals.tax.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {dayTotals.salesCost.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {dayTotals.salesAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {dayTotals.profit.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
            </tr>
            {/* 월계 행 */}
            <tr className="bg-blue-50">
              <td className="border border-gray-400 px-2 py-1" colSpan={2}>
                (월계:2025-12)
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={5}></td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {dayTotals.quantity}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {dayTotals.supplyAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {dayTotals.tax.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {dayTotals.salesCost.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {dayTotals.salesAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right font-medium">
                {dayTotals.profit.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
            </tr>
            {/* 누계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={2}>
                (누계)
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={5}></td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {dayTotals.quantity}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {dayTotals.supplyAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {dayTotals.tax.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {dayTotals.salesCost.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {dayTotals.salesAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {dayTotals.profit.toLocaleString()}
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
