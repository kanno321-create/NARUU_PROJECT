"use client";

import React, { useState } from "react";

interface UnissuedSalesItem {
  id: string;
  salesDate: string;
  salesNo: string;
  customerCode: string;
  customerName: string;
  businessNo: string;
  productName: string;
  supplyAmount: number;
  taxAmount: number;
  totalAmount: number;
  dueDate: string;
  daysOverdue: number;
  reason: string;
  selected: boolean;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: UnissuedSalesItem[] = [
  {
    id: "1",
    salesDate: "2025-12-05",
    salesNo: "SL2024120001",
    customerCode: "C001",
    customerName: "테스트전자",
    businessNo: "123-45-67890",
    productName: "전자부품 외 3종",
    supplyAmount: 5000000,
    taxAmount: 500000,
    totalAmount: 5500000,
    dueDate: "2025-12-10",
    daysOverdue: 0,
    reason: "발행대기",
    selected: false,
  },
  {
    id: "2",
    salesDate: "2025-12-04",
    salesNo: "SL2024120002",
    customerCode: "C002",
    customerName: "제고상사",
    businessNo: "234-56-78901",
    productName: "케이블 외 2종",
    supplyAmount: 3200000,
    taxAmount: 320000,
    totalAmount: 3520000,
    dueDate: "2025-12-09",
    daysOverdue: 0,
    reason: "발행대기",
    selected: false,
  },
  {
    id: "3",
    salesDate: "2025-11-25",
    salesNo: "SL2024110015",
    customerCode: "C003",
    customerName: "신규산업",
    businessNo: "345-67-89012",
    productName: "커넥터 외 5종",
    supplyAmount: 8500000,
    taxAmount: 850000,
    totalAmount: 9350000,
    dueDate: "2025-11-30",
    daysOverdue: 5,
    reason: "거래처 확인중",
    selected: false,
  },
  {
    id: "4",
    salesDate: "2025-11-20",
    salesNo: "SL2024110010",
    customerCode: "C004",
    customerName: "VIP무역",
    businessNo: "456-78-90123",
    productName: "대형장비",
    supplyAmount: 12000000,
    taxAmount: 1200000,
    totalAmount: 13200000,
    dueDate: "2025-11-25",
    daysOverdue: 10,
    reason: "금액조정중",
    selected: false,
  },
  {
    id: "5",
    salesDate: "2025-11-15",
    salesNo: "SL2024110005",
    customerCode: "C005",
    customerName: "일반기업",
    businessNo: "567-89-01234",
    productName: "소모품",
    supplyAmount: 1800000,
    taxAmount: 180000,
    totalAmount: 1980000,
    dueDate: "2025-11-20",
    daysOverdue: 15,
    reason: "보류",
    selected: false,
  },
];

export function UnissuedSalesList() {
  const [startDate, setStartDate] = useState("2025-11-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [customerFilter, setCustomerFilter] = useState("");
  const [overdueFilter, setOverdueFilter] = useState("전체");
  const [data, setData] = useState<UnissuedSalesItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectAll, setSelectAll] = useState(false);

  const filteredData = data.filter(
    (item) =>
      (customerFilter === "" || item.customerName.includes(customerFilter)) &&
      (overdueFilter === "전체" ||
        (overdueFilter === "정상" && item.daysOverdue === 0) ||
        (overdueFilter === "연체" && item.daysOverdue > 0))
  );

  // 합계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      supplyAmount: acc.supplyAmount + item.supplyAmount,
      taxAmount: acc.taxAmount + item.taxAmount,
      totalAmount: acc.totalAmount + item.totalAmount,
    }),
    { supplyAmount: 0, taxAmount: 0, totalAmount: 0 }
  );

  // 연체 현황
  const overdueSummary = {
    normal: filteredData.filter(d => d.daysOverdue === 0).length,
    overdue: filteredData.filter(d => d.daysOverdue > 0).length,
    overdueAmount: filteredData.filter(d => d.daysOverdue > 0).reduce((sum, d) => sum + d.totalAmount, 0),
  };

  const handleSelectAll = () => {
    const newSelectAll = !selectAll;
    setSelectAll(newSelectAll);
    setData(data.map(item => ({ ...item, selected: newSelectAll })));
  };

  const handleSelectItem = (id: string) => {
    setData(data.map(item =>
      item.id === id ? { ...item, selected: !item.selected } : item
    ));
  };

  const selectedCount = data.filter(d => d.selected).length;
  const selectedAmount = data.filter(d => d.selected).reduce((sum, d) => sum + d.totalAmount, 0);

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">미발행 매출리스트</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-blue-100 px-2 py-0.5 text-xs hover:bg-blue-200">
          <span>📄</span> 세금계산서 일괄발행
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📄</span> 거래명세서 발행
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📊</span> 보고서
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 엑셀
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
            value={customerFilter}
            onChange={(e) => setCustomerFilter(e.target.value)}
            placeholder="거래처명"
            className="rounded border border-gray-400 px-2 py-1 text-xs w-32"
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">상태:</span>
          <select
            value={overdueFilter}
            onChange={(e) => setOverdueFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="정상">정상</option>
            <option value="연체">발행기한 초과</option>
          </select>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색(F)
        </button>
      </div>

      {/* 선택 현황 및 연체 현황 */}
      <div className="flex items-center justify-between border-b bg-yellow-50 px-3 py-2 text-xs">
        <div className="flex items-center gap-4">
          <span className="font-medium">선택현황:</span>
          <span className="text-blue-600">{selectedCount}건 선택 / {selectedAmount.toLocaleString()}원</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="font-medium">발행현황:</span>
          <span className="text-green-600">정상: {overdueSummary.normal}건</span>
          <span className="text-red-600">기한초과: {overdueSummary.overdue}건 ({overdueSummary.overdueAmount.toLocaleString()}원)</span>
        </div>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-8">
                <input
                  type="checkbox"
                  checked={selectAll}
                  onChange={handleSelectAll}
                  className="cursor-pointer"
                />
              </th>
              <th className="border border-gray-400 px-2 py-1 w-24">매출일자</th>
              <th className="border border-gray-400 px-2 py-1 w-28">매출번호</th>
              <th className="border border-gray-400 px-2 py-1">거래처명</th>
              <th className="border border-gray-400 px-2 py-1 w-28">사업자번호</th>
              <th className="border border-gray-400 px-2 py-1">품명</th>
              <th className="border border-gray-400 px-2 py-1 w-28">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">세액</th>
              <th className="border border-gray-400 px-2 py-1 w-28">합계금액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">발행기한</th>
              <th className="border border-gray-400 px-2 py-1 w-16">경과일</th>
              <th className="border border-gray-400 px-2 py-1 w-24">사유</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr
                key={item.id}
                className={`cursor-pointer ${
                  selectedId === item.id
                    ? "bg-[#316AC5] text-white"
                    : item.daysOverdue > 7
                    ? "bg-red-100 hover:bg-red-200"
                    : item.daysOverdue > 0
                    ? "bg-yellow-50 hover:bg-yellow-100"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <input
                    type="checkbox"
                    checked={item.selected}
                    onChange={() => handleSelectItem(item.id)}
                    onClick={(e) => e.stopPropagation()}
                    className="cursor-pointer"
                  />
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.salesDate}</td>
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.salesNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.businessNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.productName}</td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">
                  {item.supplyAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-red-600">
                  {item.taxAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium">
                  {item.totalAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.dueDate}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center font-medium ${
                  selectedId === item.id ? "" : item.daysOverdue > 7 ? "text-red-600" : item.daysOverdue > 0 ? "text-orange-600" : "text-green-600"
                }`}>
                  {item.daysOverdue > 0 ? `+${item.daysOverdue}일` : "-"}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.reason}</td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={6}>
                (합계: {filteredData.length}건)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.supplyAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.taxAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.totalAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={3}></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredData.length}건 | 선택: {selectedCount}건 | loading ok
      </div>
    </div>
  );
}
