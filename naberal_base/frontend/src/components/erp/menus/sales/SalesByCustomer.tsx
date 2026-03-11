"use client";

import React, { useState } from "react";

interface SalesData {
  id: string;
  customerCode: string;
  customerName: string;
  prevSalesAmount: number;
  prevSalesProfit: number;
  supplyAmount: number;
  tax: number;
  salesAmount: number;
  cost: number;
  salesProfit: number;
  profitMargin: number;
  totalProfit: number;
  profitAfterDiscount: number;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: SalesData[] = [
  {
    id: "1",
    customerCode: "m001",
    customerName: "테스트사업장",
    prevSalesAmount: 0,
    prevSalesProfit: 0,
    supplyAmount: 212000,
    tax: 21200,
    salesAmount: 233200,
    cost: 160000,
    salesProfit: 73200,
    profitMargin: 31.4,
    totalProfit: 233200,
    profitAfterDiscount: 73200,
  },
  {
    id: "2",
    customerCode: "m002",
    customerName: "제고사업장",
    prevSalesAmount: 0,
    prevSalesProfit: 0,
    supplyAmount: 121000,
    tax: 12100,
    salesAmount: 133100,
    cost: 88500,
    salesProfit: 44600,
    profitMargin: 33.5,
    totalProfit: 133100,
    profitAfterDiscount: 44600,
  },
];

export function SalesByCustomer() {
  const [startDate, setStartDate] = useState("2025-12-05");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [customerSearch, setCustomerSearch] = useState("");
  const [data] = useState<SalesData[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      item.customerCode.includes(customerSearch) ||
      item.customerName.includes(customerSearch)
  );

  // 누계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      supplyAmount: acc.supplyAmount + item.supplyAmount,
      tax: acc.tax + item.tax,
      salesAmount: acc.salesAmount + item.salesAmount,
      cost: acc.cost + item.cost,
      salesProfit: acc.salesProfit + item.salesProfit,
      totalProfit: acc.totalProfit + item.totalProfit,
      profitAfterDiscount: acc.profitAfterDiscount + item.profitAfterDiscount,
    }),
    {
      supplyAmount: 0,
      tax: 0,
      salesAmount: 0,
      cost: 0,
      salesProfit: 0,
      totalProfit: 0,
      profitAfterDiscount: 0,
    }
  );

  const handleSearch = () => {
    // 검색 실행
  };

  const handleExcel = () => {
    alert("엑셀로 내보내기");
  };

  const handlePrint = () => {
    alert("인쇄하기");
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">거래처별매출현황</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button
          onClick={handleExcel}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
          <span>📊</span> 보고서추력
        </button>
        <button
          onClick={handlePrint}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
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
          <span className="text-xs">거래처검색:</span>
          <input
            type="text"
            value={customerSearch}
            onChange={(e) => setCustomerSearch(e.target.value)}
            className="w-32 rounded border border-gray-400 px-2 py-1 text-xs"
          />
          <button className="rounded border border-gray-400 bg-gray-100 px-2 py-1 text-xs hover:bg-gray-200">
            ...
          </button>
        </div>
        <button
          onClick={handleSearch}
          className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200"
        >
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
              <th className="border border-gray-400 px-2 py-1 w-24">이전외출액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">이전외출이익</th>
              <th className="border border-gray-400 px-2 py-1 w-24">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">세액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">매출액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">원가</th>
              <th className="border border-gray-400 px-2 py-1 w-24">매출이익</th>
              <th className="border border-gray-400 px-2 py-1 w-20">매출이익합계</th>
              <th className="border border-gray-400 px-2 py-1">매출이익합계</th>
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
                <td className="border border-gray-300 px-2 py-1">{item.customerCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerName}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.prevSalesAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.prevSalesProfit.toLocaleString()}
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
                  {item.cost.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.salesProfit.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.totalProfit.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.profitAfterDiscount.toLocaleString()}
                </td>
              </tr>
            ))}
            {/* 누계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={2}>
                (누계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">0</td>
              <td className="border border-gray-400 px-2 py-1 text-right">0</td>
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
                {totals.cost.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.salesProfit.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.totalProfit.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.profitAfterDiscount.toLocaleString()}
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
