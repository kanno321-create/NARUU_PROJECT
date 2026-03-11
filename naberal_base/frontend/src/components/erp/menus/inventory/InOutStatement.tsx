"use client";

import React, { useState } from "react";

interface InOutStatementItem {
  id: string;
  transDate: string;
  transType: string;
  transNo: string;
  partnerCode: string;
  partnerName: string;
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
  refNo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: InOutStatementItem[] = [
  {
    id: "1",
    transDate: "2025-12-05",
    transType: "입고",
    transNo: "IB2024120001",
    partnerCode: "S001",
    partnerName: "상도전기",
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
    refNo: "PO2024110001",
  },
  {
    id: "2",
    transDate: "2025-12-05",
    transType: "출고",
    transNo: "OB2024120001",
    partnerCode: "C001",
    partnerName: "테스트전자",
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
    refNo: "SO2024120001",
  },
  {
    id: "3",
    transDate: "2025-12-04",
    transType: "입고",
    transNo: "IB2024120003",
    partnerCode: "S003",
    partnerName: "금속공업사",
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
    refNo: "PO2024110003",
  },
  {
    id: "4",
    transDate: "2025-12-04",
    transType: "출고",
    transNo: "OB2024120002",
    partnerCode: "C002",
    partnerName: "제고상사",
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
    refNo: "SO2024120002",
  },
  {
    id: "5",
    transDate: "2025-12-03",
    transType: "입고",
    transNo: "IB2024120005",
    partnerCode: "S005",
    partnerName: "부품상사",
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
    refNo: "PO2024110005",
  },
  {
    id: "6",
    transDate: "2025-12-03",
    transType: "출고",
    transNo: "OB2024120005",
    partnerCode: "C005",
    partnerName: "일반기업",
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
    refNo: "SO2024120005",
  },
];

export function InOutStatement() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [typeFilter, setTypeFilter] = useState("전체");
  const [partnerFilter, setPartnerFilter] = useState("");
  const [warehouseFilter, setWarehouseFilter] = useState("전체");
  const [data] = useState<InOutStatementItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      (typeFilter === "전체" || item.transType === typeFilter) &&
      (partnerFilter === "" || item.partnerName.includes(partnerFilter)) &&
      (warehouseFilter === "전체" || item.warehouse === warehouseFilter)
  );

  // 유형별 집계
  const typeSummary = filteredData.reduce((acc, item) => {
    if (!acc[item.transType]) {
      acc[item.transType] = { count: 0, supplyAmount: 0, taxAmount: 0, totalAmount: 0 };
    }
    acc[item.transType].count += 1;
    acc[item.transType].supplyAmount += item.supplyAmount;
    acc[item.transType].taxAmount += item.taxAmount;
    acc[item.transType].totalAmount += item.totalAmount;
    return acc;
  }, {} as Record<string, { count: number; supplyAmount: number; taxAmount: number; totalAmount: number }>);

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

  const getTypeColor = (type: string, isSelected: boolean) => {
    if (isSelected) return "";
    return type === "입고" ? "text-blue-600" : "text-red-600";
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">입출고명세서</span>
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
          <span className="text-xs">유형:</span>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="입고">입고</option>
            <option value="출고">출고</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">거래처:</span>
          <input
            type="text"
            value={partnerFilter}
            onChange={(e) => setPartnerFilter(e.target.value)}
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

      {/* 유형별 요약 */}
      <div className="border-b bg-purple-50 px-3 py-2">
        <div className="text-xs font-medium mb-1">▶ 입출고 요약</div>
        <div className="flex gap-6 text-xs">
          {typeSummary["입고"] && (
            <div className="bg-white px-4 py-2 rounded border">
              <div className="font-medium text-blue-600">입고</div>
              <div>건수: {typeSummary["입고"].count}건</div>
              <div className="text-blue-600">공급가액: {typeSummary["입고"].supplyAmount.toLocaleString()}</div>
              <div className="text-blue-600 font-medium">합계: {typeSummary["입고"].totalAmount.toLocaleString()}</div>
            </div>
          )}
          {typeSummary["출고"] && (
            <div className="bg-white px-4 py-2 rounded border">
              <div className="font-medium text-red-600">출고</div>
              <div>건수: {typeSummary["출고"].count}건</div>
              <div className="text-red-600">공급가액: {typeSummary["출고"].supplyAmount.toLocaleString()}</div>
              <div className="text-red-600 font-medium">합계: {typeSummary["출고"].totalAmount.toLocaleString()}</div>
            </div>
          )}
          <div className="bg-white px-4 py-2 rounded border">
            <div className="font-medium">순입출고</div>
            <div className={`font-bold ${((typeSummary["입고"]?.totalAmount || 0) - (typeSummary["출고"]?.totalAmount || 0)) >= 0 ? "text-blue-600" : "text-red-600"}`}>
              {((typeSummary["입고"]?.totalAmount || 0) - (typeSummary["출고"]?.totalAmount || 0)).toLocaleString()}원
            </div>
          </div>
        </div>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-24">일자</th>
              <th className="border border-gray-400 px-2 py-1 w-14">유형</th>
              <th className="border border-gray-400 px-2 py-1 w-28">전표번호</th>
              <th className="border border-gray-400 px-2 py-1 w-24">거래처</th>
              <th className="border border-gray-400 px-2 py-1 w-28">사업자번호</th>
              <th className="border border-gray-400 px-2 py-1 w-20">품목코드</th>
              <th className="border border-gray-400 px-2 py-1">품목명</th>
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
                    : item.transType === "입고"
                    ? "bg-blue-50 hover:bg-blue-100"
                    : "bg-red-50 hover:bg-red-100"
                }`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1">{item.transDate}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center font-medium ${getTypeColor(item.transType, selectedId === item.id)}`}>
                  {item.transType}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.transNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.partnerName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.businessNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.itemCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.itemName}</td>
                <td className="border border-gray-300 px-2 py-1 text-center">{item.unit}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">{item.qty.toLocaleString()}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">{item.unitPrice.toLocaleString()}</td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${getTypeColor(item.transType, selectedId === item.id)}`}>
                  {item.supplyAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.taxAmount.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right font-medium ${getTypeColor(item.transType, selectedId === item.id)}`}>
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
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.supplyAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
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
        총 {filteredData.length}건 | 입고: {typeSummary["입고"]?.count || 0} | 출고: {typeSummary["출고"]?.count || 0} | loading ok
      </div>
    </div>
  );
}
