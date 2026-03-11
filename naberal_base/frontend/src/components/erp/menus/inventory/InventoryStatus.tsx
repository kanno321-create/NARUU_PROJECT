"use client";

import React, { useState } from "react";

interface InventoryItem {
  id: string;
  itemCode: string;
  itemName: string;
  specification: string;
  unit: string;
  warehouse: string;
  prevQty: number;
  inboundQty: number;
  outboundQty: number;
  adjustQty: number;
  currentQty: number;
  unitCost: number;
  totalCost: number;
  safetyStock: number;
  status: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: InventoryItem[] = [
  {
    id: "1",
    itemCode: "P001",
    itemName: "SBE-104 차단기",
    specification: "4P 100AF 75AT",
    unit: "EA",
    warehouse: "본사창고",
    prevQty: 100,
    inboundQty: 50,
    outboundQty: 30,
    adjustQty: 0,
    currentQty: 120,
    unitCost: 45000,
    totalCost: 5400000,
    safetyStock: 50,
    status: "정상",
  },
  {
    id: "2",
    itemCode: "P002",
    itemName: "SBE-204 차단기",
    specification: "4P 200AF 150AT",
    unit: "EA",
    warehouse: "본사창고",
    prevQty: 50,
    inboundQty: 20,
    outboundQty: 25,
    adjustQty: -2,
    currentQty: 43,
    unitCost: 85000,
    totalCost: 3655000,
    safetyStock: 30,
    status: "정상",
  },
  {
    id: "3",
    itemCode: "P003",
    itemName: "외함 600×800×200",
    specification: "STEEL 1.6T",
    unit: "면",
    warehouse: "본사창고",
    prevQty: 20,
    inboundQty: 10,
    outboundQty: 15,
    adjustQty: 0,
    currentQty: 15,
    unitCost: 120000,
    totalCost: 1800000,
    safetyStock: 10,
    status: "정상",
  },
  {
    id: "4",
    itemCode: "P004",
    itemName: "BUS-BAR 3T×15",
    specification: "COPPER",
    unit: "KG",
    warehouse: "본사창고",
    prevQty: 200,
    inboundQty: 100,
    outboundQty: 150,
    adjustQty: 0,
    currentQty: 150,
    unitCost: 20000,
    totalCost: 3000000,
    safetyStock: 100,
    status: "정상",
  },
  {
    id: "5",
    itemCode: "P005",
    itemName: "MC-22 마그네트",
    specification: "22A",
    unit: "EA",
    warehouse: "본사창고",
    prevQty: 30,
    inboundQty: 0,
    outboundQty: 25,
    adjustQty: 0,
    currentQty: 5,
    unitCost: 35000,
    totalCost: 175000,
    safetyStock: 20,
    status: "부족",
  },
  {
    id: "6",
    itemCode: "P006",
    itemName: "TERMINAL BLOCK",
    specification: "600V",
    unit: "EA",
    warehouse: "제2창고",
    prevQty: 500,
    inboundQty: 200,
    outboundQty: 300,
    adjustQty: 10,
    currentQty: 410,
    unitCost: 4000,
    totalCost: 1640000,
    safetyStock: 200,
    status: "정상",
  },
  {
    id: "7",
    itemCode: "P007",
    itemName: "E.T (접지단자)",
    specification: "100AF용",
    unit: "EA",
    warehouse: "본사창고",
    prevQty: 100,
    inboundQty: 50,
    outboundQty: 80,
    adjustQty: 0,
    currentQty: 70,
    unitCost: 4500,
    totalCost: 315000,
    safetyStock: 50,
    status: "정상",
  },
  {
    id: "8",
    itemCode: "P008",
    itemName: "P-COVER 아크릴",
    specification: "600×800",
    unit: "EA",
    warehouse: "본사창고",
    prevQty: 25,
    inboundQty: 10,
    outboundQty: 20,
    adjustQty: 0,
    currentQty: 15,
    unitCost: 17000,
    totalCost: 255000,
    safetyStock: 15,
    status: "경고",
  },
];

export function InventoryStatus() {
  const [baseDate, setBaseDate] = useState("2025-12-05");
  const [warehouseFilter, setWarehouseFilter] = useState("전체");
  const [itemFilter, setItemFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("전체");
  const [data] = useState<InventoryItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      (warehouseFilter === "전체" || item.warehouse === warehouseFilter) &&
      (itemFilter === "" || item.itemName.includes(itemFilter) || item.itemCode.includes(itemFilter)) &&
      (statusFilter === "전체" || item.status === statusFilter)
  );

  // 상태별 집계
  const statusSummary = filteredData.reduce((acc, item) => {
    acc[item.status] = (acc[item.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // 합계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      prevQty: acc.prevQty + item.prevQty,
      inboundQty: acc.inboundQty + item.inboundQty,
      outboundQty: acc.outboundQty + item.outboundQty,
      adjustQty: acc.adjustQty + item.adjustQty,
      currentQty: acc.currentQty + item.currentQty,
      totalCost: acc.totalCost + item.totalCost,
    }),
    { prevQty: 0, inboundQty: 0, outboundQty: 0, adjustQty: 0, currentQty: 0, totalCost: 0 }
  );

  const getStatusColor = (status: string, isSelected: boolean) => {
    if (isSelected) return "";
    switch (status) {
      case "정상": return "text-green-600";
      case "경고": return "text-orange-600";
      case "부족": return "text-red-600";
      default: return "";
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">재고현황</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📊</span> 재고분석
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>⚠️</span> 부족품목
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🖨️</span> 인쇄
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 엑셀
        </button>
      </div>

      {/* 검색 조건 */}
      <div className="flex items-center gap-4 border-b bg-white px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="text-xs">기준일:</span>
          <input
            type="date"
            value={baseDate}
            onChange={(e) => setBaseDate(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
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
        <div className="flex items-center gap-2">
          <span className="text-xs">품목:</span>
          <input
            type="text"
            value={itemFilter}
            onChange={(e) => setItemFilter(e.target.value)}
            placeholder="품목코드/품목명"
            className="rounded border border-gray-400 px-2 py-1 text-xs w-32"
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">상태:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="정상">정상</option>
            <option value="경고">경고</option>
            <option value="부족">부족</option>
          </select>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          조 회(F)
        </button>
      </div>

      {/* 상태별 요약 */}
      <div className="flex items-center gap-6 border-b bg-green-50 px-3 py-2 text-xs">
        <span className="font-medium">재고상태:</span>
        <span className="text-green-600">정상: {statusSummary["정상"] || 0}건</span>
        <span className="text-orange-600">경고: {statusSummary["경고"] || 0}건</span>
        <span className="text-red-600">부족: {statusSummary["부족"] || 0}건</span>
        <span className="ml-4 font-bold">총 재고금액: {totals.totalCost.toLocaleString()}원</span>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-20">품목코드</th>
              <th className="border border-gray-400 px-2 py-1">품목명</th>
              <th className="border border-gray-400 px-2 py-1 w-28">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-12">단위</th>
              <th className="border border-gray-400 px-2 py-1 w-20">창고</th>
              <th className="border border-gray-400 px-2 py-1 w-16">전기재고</th>
              <th className="border border-gray-400 px-2 py-1 w-16">입고</th>
              <th className="border border-gray-400 px-2 py-1 w-16">출고</th>
              <th className="border border-gray-400 px-2 py-1 w-16">조정</th>
              <th className="border border-gray-400 px-2 py-1 w-16">현재고</th>
              <th className="border border-gray-400 px-2 py-1 w-20">단가</th>
              <th className="border border-gray-400 px-2 py-1 w-24">재고금액</th>
              <th className="border border-gray-400 px-2 py-1 w-16">안전재고</th>
              <th className="border border-gray-400 px-2 py-1 w-14">상태</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr
                key={item.id}
                className={`cursor-pointer ${
                  selectedId === item.id
                    ? "bg-[#316AC5] text-white"
                    : item.status === "부족"
                    ? "bg-red-50 hover:bg-red-100"
                    : item.status === "경고"
                    ? "bg-yellow-50 hover:bg-yellow-100"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.itemCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.itemName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.specification}</td>
                <td className="border border-gray-300 px-2 py-1 text-center">{item.unit}</td>
                <td className="border border-gray-300 px-2 py-1">{item.warehouse}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">{item.prevQty.toLocaleString()}</td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${selectedId === item.id ? "" : "text-blue-600"}`}>
                  {item.inboundQty.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${selectedId === item.id ? "" : "text-red-600"}`}>
                  {item.outboundQty.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${selectedId === item.id ? "" : item.adjustQty !== 0 ? "text-purple-600" : ""}`}>
                  {item.adjustQty}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium">
                  {item.currentQty.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.unitCost.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium">
                  {item.totalCost.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">{item.safetyStock}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${getStatusColor(item.status, selectedId === item.id)}`}>
                  {item.status}
                </td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={5}>
                (합계: {filteredData.length}건)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.prevQty.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.inboundQty.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.outboundQty.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.adjustQty}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.currentQty.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.totalCost.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={2}></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredData.length}건 | 정상: {statusSummary["정상"] || 0} | 경고: {statusSummary["경고"] || 0} | 부족: {statusSummary["부족"] || 0} | loading ok
      </div>
    </div>
  );
}
