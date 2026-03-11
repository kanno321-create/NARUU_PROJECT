"use client";

import React, { useState } from "react";

interface OutboundStatementItem {
  id: string;
  outboundNo: string;
  outboundDate: string;
  customerCode: string;
  customerName: string;
  businessNo: string;
  itemCode: string;
  itemName: string;
  specification: string;
  unit: string;
  qty: number;
  unitPrice: number;
  supplyAmount: number;
  taxAmount: number;
  totalAmount: number;
  warehouse: string;
  salesOrderNo: string;
  memo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: OutboundStatementItem[] = [
  {
    id: "1",
    outboundNo: "OB2024120001",
    outboundDate: "2025-12-05",
    customerCode: "C001",
    customerName: "테스트전자",
    businessNo: "111-22-33333",
    itemCode: "P001",
    itemName: "SBE-104 차단기",
    specification: "4P 100AF 75AT",
    unit: "EA",
    qty: 20,
    unitPrice: 55000,
    supplyAmount: 1100000,
    taxAmount: 110000,
    totalAmount: 1210000,
    warehouse: "본사창고",
    salesOrderNo: "SO2024120001",
    memo: "",
  },
  {
    id: "2",
    outboundNo: "OB2024120002",
    outboundDate: "2025-12-05",
    customerCode: "C002",
    customerName: "제고상사",
    businessNo: "222-33-44444",
    itemCode: "P003",
    itemName: "외함 600×800×200",
    specification: "STEEL 1.6T",
    unit: "면",
    qty: 5,
    unitPrice: 150000,
    supplyAmount: 750000,
    taxAmount: 75000,
    totalAmount: 825000,
    warehouse: "본사창고",
    salesOrderNo: "SO2024120002",
    memo: "",
  },
  {
    id: "3",
    outboundNo: "OB2024120003",
    outboundDate: "2025-12-04",
    customerCode: "C003",
    customerName: "신규산업",
    businessNo: "333-44-55555",
    itemCode: "P002",
    itemName: "SBE-204 차단기",
    specification: "4P 200AF 150AT",
    unit: "EA",
    qty: 10,
    unitPrice: 100000,
    supplyAmount: 1000000,
    taxAmount: 100000,
    totalAmount: 1100000,
    warehouse: "본사창고",
    salesOrderNo: "SO2024120003",
    memo: "부분출고",
  },
  {
    id: "4",
    outboundNo: "OB2024120004",
    outboundDate: "2025-12-04",
    customerCode: "C004",
    customerName: "VIP무역",
    businessNo: "444-55-66666",
    itemCode: "P004",
    itemName: "BUS-BAR 3T×15",
    specification: "COPPER",
    unit: "KG",
    qty: 50,
    unitPrice: 25000,
    supplyAmount: 1250000,
    taxAmount: 125000,
    totalAmount: 1375000,
    warehouse: "본사창고",
    salesOrderNo: "SO2024120004",
    memo: "",
  },
  {
    id: "5",
    outboundNo: "OB2024120005",
    outboundDate: "2025-12-03",
    customerCode: "C005",
    customerName: "일반기업",
    businessNo: "555-66-77777",
    itemCode: "P006",
    itemName: "TERMINAL BLOCK",
    specification: "600V",
    unit: "EA",
    qty: 100,
    unitPrice: 5000,
    supplyAmount: 500000,
    taxAmount: 50000,
    totalAmount: 550000,
    warehouse: "제2창고",
    salesOrderNo: "SO2024120005",
    memo: "",
  },
];

export function OutboundStatement() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [customerFilter, setCustomerFilter] = useState("");
  const [warehouseFilter, setWarehouseFilter] = useState("전체");
  const [data] = useState<OutboundStatementItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      (customerFilter === "" || item.customerName.includes(customerFilter)) &&
      (warehouseFilter === "전체" || item.warehouse === warehouseFilter)
  );

  // 거래처별 집계
  const customerSummary = filteredData.reduce((acc, item) => {
    if (!acc[item.customerName]) {
      acc[item.customerName] = { count: 0, amount: 0 };
    }
    acc[item.customerName].count += 1;
    acc[item.customerName].amount += item.totalAmount;
    return acc;
  }, {} as Record<string, { count: number; amount: number }>);

  // 합계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      qty: acc.qty + item.qty,
      supplyAmount: acc.supplyAmount + item.supplyAmount,
      taxAmount: acc.taxAmount + item.taxAmount,
      totalAmount: acc.totalAmount + item.totalAmount,
    }),
    { qty: 0, supplyAmount: 0, taxAmount: 0, totalAmount: 0 }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">출고명세서</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🖨️</span> 명세서인쇄
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📧</span> 이메일
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
            className="rounded border border-gray-400 px-2 py-1 text-xs w-28"
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">창고:</span>
          <select
            value={warehouseFilter}
            onChange={(e) => setWarehouseFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="본사창고">본사창고</option>
            <option value="제2창고">제2창고</option>
          </select>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          조 회(F)
        </button>
      </div>

      {/* 거래처별 요약 */}
      <div className="border-b bg-red-50 px-3 py-2">
        <div className="text-xs font-medium mb-1">▶ 거래처별 출고현황</div>
        <div className="flex gap-4 text-xs flex-wrap">
          {Object.entries(customerSummary).map(([customer, summary]) => (
            <div key={customer} className="bg-white px-3 py-1 rounded border">
              <div className="font-medium">{customer}</div>
              <div>건수: {summary.count}건</div>
              <div className="text-red-600">{summary.amount.toLocaleString()}원</div>
            </div>
          ))}
        </div>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-28">출고번호</th>
              <th className="border border-gray-400 px-2 py-1 w-24">출고일자</th>
              <th className="border border-gray-400 px-2 py-1 w-24">거래처</th>
              <th className="border border-gray-400 px-2 py-1 w-28">사업자번호</th>
              <th className="border border-gray-400 px-2 py-1 w-20">품목코드</th>
              <th className="border border-gray-400 px-2 py-1">품목명</th>
              <th className="border border-gray-400 px-2 py-1 w-24">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-12">단위</th>
              <th className="border border-gray-400 px-2 py-1 w-14">수량</th>
              <th className="border border-gray-400 px-2 py-1 w-20">단가</th>
              <th className="border border-gray-400 px-2 py-1 w-24">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">세액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">합계금액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">창고</th>
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
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.outboundNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.outboundDate}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.businessNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.itemCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.itemName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.specification}</td>
                <td className="border border-gray-300 px-2 py-1 text-center">{item.unit}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">{item.qty.toLocaleString()}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">{item.unitPrice.toLocaleString()}</td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${selectedId === item.id ? "" : "text-blue-600"}`}>
                  {item.supplyAmount.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${selectedId === item.id ? "" : "text-red-600"}`}>
                  {item.taxAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium">
                  {item.totalAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.warehouse}</td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={8}>
                (합계: {filteredData.length}건)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.qty.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.supplyAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.taxAmount.toLocaleString()}
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
        총 {filteredData.length}건 | 공급가액: {totals.supplyAmount.toLocaleString()} | 세액: {totals.taxAmount.toLocaleString()} | 합계: {totals.totalAmount.toLocaleString()} | loading ok
      </div>
    </div>
  );
}
