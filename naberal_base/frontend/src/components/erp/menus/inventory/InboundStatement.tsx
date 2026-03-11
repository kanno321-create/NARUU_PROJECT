"use client";

import React, { useState } from "react";

interface InboundStatementItem {
  id: string;
  inboundNo: string;
  inboundDate: string;
  supplierCode: string;
  supplierName: string;
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
  purchaseOrderNo: string;
  memo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: InboundStatementItem[] = [
  {
    id: "1",
    inboundNo: "IB2024120001",
    inboundDate: "2025-12-05",
    supplierCode: "S001",
    supplierName: "상도전기",
    businessNo: "123-45-67890",
    itemCode: "P001",
    itemName: "SBE-104 차단기",
    specification: "4P 100AF 75AT",
    unit: "EA",
    qty: 50,
    unitPrice: 45000,
    supplyAmount: 2250000,
    taxAmount: 225000,
    totalAmount: 2475000,
    warehouse: "본사창고",
    purchaseOrderNo: "PO2024110001",
    memo: "",
  },
  {
    id: "2",
    inboundNo: "IB2024120002",
    inboundDate: "2025-12-05",
    supplierCode: "S002",
    supplierName: "LS산전",
    businessNo: "234-56-78901",
    itemCode: "P002",
    itemName: "ABN-204 차단기",
    specification: "4P 200AF 150AT",
    unit: "EA",
    qty: 20,
    unitPrice: 85000,
    supplyAmount: 1700000,
    taxAmount: 170000,
    totalAmount: 1870000,
    warehouse: "본사창고",
    purchaseOrderNo: "PO2024110002",
    memo: "부분입고",
  },
  {
    id: "3",
    inboundNo: "IB2024120003",
    inboundDate: "2025-12-04",
    supplierCode: "S003",
    supplierName: "금속공업사",
    businessNo: "345-67-89012",
    itemCode: "P003",
    itemName: "외함 600×800×200",
    specification: "STEEL 1.6T",
    unit: "면",
    qty: 10,
    unitPrice: 120000,
    supplyAmount: 1200000,
    taxAmount: 120000,
    totalAmount: 1320000,
    warehouse: "본사창고",
    purchaseOrderNo: "PO2024110003",
    memo: "",
  },
  {
    id: "4",
    inboundNo: "IB2024120004",
    inboundDate: "2025-12-04",
    supplierCode: "S004",
    supplierName: "동부금속",
    businessNo: "456-78-90123",
    itemCode: "P004",
    itemName: "BUS-BAR 3T×15",
    specification: "COPPER",
    unit: "KG",
    qty: 100,
    unitPrice: 20000,
    supplyAmount: 2000000,
    taxAmount: 200000,
    totalAmount: 2200000,
    warehouse: "본사창고",
    purchaseOrderNo: "PO2024110004",
    memo: "",
  },
  {
    id: "5",
    inboundNo: "IB2024120005",
    inboundDate: "2025-12-03",
    supplierCode: "S005",
    supplierName: "부품상사",
    businessNo: "567-89-01234",
    itemCode: "P006",
    itemName: "TERMINAL BLOCK",
    specification: "600V",
    unit: "EA",
    qty: 200,
    unitPrice: 4000,
    supplyAmount: 800000,
    taxAmount: 80000,
    totalAmount: 880000,
    warehouse: "제2창고",
    purchaseOrderNo: "PO2024110005",
    memo: "",
  },
];

export function InboundStatement() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [supplierFilter, setSupplierFilter] = useState("");
  const [warehouseFilter, setWarehouseFilter] = useState("전체");
  const [data] = useState<InboundStatementItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      (supplierFilter === "" || item.supplierName.includes(supplierFilter)) &&
      (warehouseFilter === "전체" || item.warehouse === warehouseFilter)
  );

  // 공급업체별 집계
  const supplierSummary = filteredData.reduce((acc, item) => {
    if (!acc[item.supplierName]) {
      acc[item.supplierName] = { count: 0, amount: 0 };
    }
    acc[item.supplierName].count += 1;
    acc[item.supplierName].amount += item.totalAmount;
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
        <span className="text-sm font-medium text-white">입고명세서</span>
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
          <span className="text-xs">공급업체:</span>
          <input
            type="text"
            value={supplierFilter}
            onChange={(e) => setSupplierFilter(e.target.value)}
            placeholder="업체명"
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

      {/* 업체별 요약 */}
      <div className="border-b bg-blue-50 px-3 py-2">
        <div className="text-xs font-medium mb-1">▶ 업체별 입고현황</div>
        <div className="flex gap-4 text-xs flex-wrap">
          {Object.entries(supplierSummary).map(([supplier, summary]) => (
            <div key={supplier} className="bg-white px-3 py-1 rounded border">
              <div className="font-medium">{supplier}</div>
              <div>건수: {summary.count}건</div>
              <div className="text-blue-600">{summary.amount.toLocaleString()}원</div>
            </div>
          ))}
        </div>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-28">입고번호</th>
              <th className="border border-gray-400 px-2 py-1 w-24">입고일자</th>
              <th className="border border-gray-400 px-2 py-1 w-24">공급업체</th>
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
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.inboundNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.inboundDate}</td>
                <td className="border border-gray-300 px-2 py-1">{item.supplierName}</td>
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
