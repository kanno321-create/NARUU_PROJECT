"use client";

import React, { useState } from "react";

interface ItemInOutItem {
  id: string;
  itemCode: string;
  itemName: string;
  specification: string;
  unit: string;
  warehouse: string;
  prevQty: number;
  prevAmount: number;
  inboundQty: number;
  inboundAmount: number;
  outboundQty: number;
  outboundAmount: number;
  adjustQty: number;
  adjustAmount: number;
  currentQty: number;
  currentAmount: number;
  avgCost: number;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: ItemInOutItem[] = [
  {
    id: "1",
    itemCode: "P001",
    itemName: "SBE-104 차단기",
    specification: "4P 100AF 75AT",
    unit: "EA",
    warehouse: "본사창고",
    prevQty: 100,
    prevAmount: 4500000,
    inboundQty: 50,
    inboundAmount: 2250000,
    outboundQty: 30,
    outboundAmount: 1350000,
    adjustQty: 0,
    adjustAmount: 0,
    currentQty: 120,
    currentAmount: 5400000,
    avgCost: 45000,
  },
  {
    id: "2",
    itemCode: "P002",
    itemName: "SBE-204 차단기",
    specification: "4P 200AF 150AT",
    unit: "EA",
    warehouse: "본사창고",
    prevQty: 50,
    prevAmount: 4250000,
    inboundQty: 20,
    inboundAmount: 1700000,
    outboundQty: 25,
    outboundAmount: 2125000,
    adjustQty: -2,
    adjustAmount: -170000,
    currentQty: 43,
    currentAmount: 3655000,
    avgCost: 85000,
  },
  {
    id: "3",
    itemCode: "P003",
    itemName: "외함 600×800×200",
    specification: "STEEL 1.6T",
    unit: "면",
    warehouse: "본사창고",
    prevQty: 20,
    prevAmount: 2400000,
    inboundQty: 10,
    inboundAmount: 1200000,
    outboundQty: 15,
    outboundAmount: 1800000,
    adjustQty: 0,
    adjustAmount: 0,
    currentQty: 15,
    currentAmount: 1800000,
    avgCost: 120000,
  },
  {
    id: "4",
    itemCode: "P004",
    itemName: "BUS-BAR 3T×15",
    specification: "COPPER",
    unit: "KG",
    warehouse: "본사창고",
    prevQty: 200,
    prevAmount: 4000000,
    inboundQty: 100,
    inboundAmount: 2000000,
    outboundQty: 150,
    outboundAmount: 3000000,
    adjustQty: 0,
    adjustAmount: 0,
    currentQty: 150,
    currentAmount: 3000000,
    avgCost: 20000,
  },
  {
    id: "5",
    itemCode: "P005",
    itemName: "MC-22 마그네트",
    specification: "22A",
    unit: "EA",
    warehouse: "본사창고",
    prevQty: 30,
    prevAmount: 1050000,
    inboundQty: 0,
    inboundAmount: 0,
    outboundQty: 25,
    outboundAmount: 875000,
    adjustQty: 0,
    adjustAmount: 0,
    currentQty: 5,
    currentAmount: 175000,
    avgCost: 35000,
  },
  {
    id: "6",
    itemCode: "P006",
    itemName: "TERMINAL BLOCK",
    specification: "600V",
    unit: "EA",
    warehouse: "제2창고",
    prevQty: 500,
    prevAmount: 2000000,
    inboundQty: 200,
    inboundAmount: 800000,
    outboundQty: 300,
    outboundAmount: 1200000,
    adjustQty: 10,
    adjustAmount: 40000,
    currentQty: 410,
    currentAmount: 1640000,
    avgCost: 4000,
  },
  {
    id: "7",
    itemCode: "P007",
    itemName: "E.T (접지단자)",
    specification: "100AF용",
    unit: "EA",
    warehouse: "본사창고",
    prevQty: 100,
    prevAmount: 450000,
    inboundQty: 50,
    inboundAmount: 225000,
    outboundQty: 80,
    outboundAmount: 360000,
    adjustQty: 0,
    adjustAmount: 0,
    currentQty: 70,
    currentAmount: 315000,
    avgCost: 4500,
  },
  {
    id: "8",
    itemCode: "P008",
    itemName: "P-COVER 아크릴",
    specification: "600×800",
    unit: "EA",
    warehouse: "본사창고",
    prevQty: 25,
    prevAmount: 425000,
    inboundQty: 10,
    inboundAmount: 170000,
    outboundQty: 20,
    outboundAmount: 340000,
    adjustQty: 0,
    adjustAmount: 0,
    currentQty: 15,
    currentAmount: 255000,
    avgCost: 17000,
  },
];

export function ItemInOutStatement() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [itemFilter, setItemFilter] = useState("");
  const [warehouseFilter, setWarehouseFilter] = useState("전체");
  const [data] = useState<ItemInOutItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      (itemFilter === "" || item.itemName.includes(itemFilter) || item.itemCode.includes(itemFilter)) &&
      (warehouseFilter === "전체" || item.warehouse === warehouseFilter)
  );

  // 합계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      prevQty: acc.prevQty + item.prevQty,
      prevAmount: acc.prevAmount + item.prevAmount,
      inboundQty: acc.inboundQty + item.inboundQty,
      inboundAmount: acc.inboundAmount + item.inboundAmount,
      outboundQty: acc.outboundQty + item.outboundQty,
      outboundAmount: acc.outboundAmount + item.outboundAmount,
      adjustQty: acc.adjustQty + item.adjustQty,
      adjustAmount: acc.adjustAmount + item.adjustAmount,
      currentQty: acc.currentQty + item.currentQty,
      currentAmount: acc.currentAmount + item.currentAmount,
    }),
    {
      prevQty: 0, prevAmount: 0, inboundQty: 0, inboundAmount: 0,
      outboundQty: 0, outboundAmount: 0, adjustQty: 0, adjustAmount: 0,
      currentQty: 0, currentAmount: 0
    }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">품목별입출고명세서</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🖨️</span> 인쇄
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📊</span> 차트
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
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

      {/* 요약 정보 */}
      <div className="flex items-center gap-6 border-b bg-green-50 px-3 py-2 text-xs">
        <span className="font-medium">재고 요약:</span>
        <span>기초: {totals.prevAmount.toLocaleString()}원</span>
        <span className="text-blue-600">+ 입고: {totals.inboundAmount.toLocaleString()}원</span>
        <span className="text-red-600">- 출고: {totals.outboundAmount.toLocaleString()}원</span>
        <span className="text-purple-600">± 조정: {totals.adjustAmount.toLocaleString()}원</span>
        <span className="font-bold">= 현재고: {totals.currentAmount.toLocaleString()}원</span>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>품목코드</th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>품목명</th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>규격</th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>단위</th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>창고</th>
              <th className="border border-gray-400 px-2 py-1 bg-gray-200" colSpan={2}>기초재고</th>
              <th className="border border-gray-400 px-2 py-1 bg-blue-100" colSpan={2}>입고</th>
              <th className="border border-gray-400 px-2 py-1 bg-red-100" colSpan={2}>출고</th>
              <th className="border border-gray-400 px-2 py-1 bg-purple-100" colSpan={2}>조정</th>
              <th className="border border-gray-400 px-2 py-1 bg-green-100" colSpan={2}>현재고</th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>평균단가</th>
            </tr>
            <tr>
              <th className="border border-gray-400 px-1 py-1 bg-gray-200 w-14">수량</th>
              <th className="border border-gray-400 px-1 py-1 bg-gray-200 w-20">금액</th>
              <th className="border border-gray-400 px-1 py-1 bg-blue-100 w-14">수량</th>
              <th className="border border-gray-400 px-1 py-1 bg-blue-100 w-20">금액</th>
              <th className="border border-gray-400 px-1 py-1 bg-red-100 w-14">수량</th>
              <th className="border border-gray-400 px-1 py-1 bg-red-100 w-20">금액</th>
              <th className="border border-gray-400 px-1 py-1 bg-purple-100 w-14">수량</th>
              <th className="border border-gray-400 px-1 py-1 bg-purple-100 w-20">금액</th>
              <th className="border border-gray-400 px-1 py-1 bg-green-100 w-14">수량</th>
              <th className="border border-gray-400 px-1 py-1 bg-green-100 w-20">금액</th>
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
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.itemCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.itemName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.specification}</td>
                <td className="border border-gray-300 px-2 py-1 text-center">{item.unit}</td>
                <td className="border border-gray-300 px-2 py-1">{item.warehouse}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{item.prevQty.toLocaleString()}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{item.prevAmount.toLocaleString()}</td>
                <td className={`border border-gray-300 px-1 py-1 text-right ${selectedId === item.id ? "" : "text-blue-600"}`}>
                  {item.inboundQty > 0 ? item.inboundQty.toLocaleString() : "-"}
                </td>
                <td className={`border border-gray-300 px-1 py-1 text-right ${selectedId === item.id ? "" : "text-blue-600"}`}>
                  {item.inboundAmount > 0 ? item.inboundAmount.toLocaleString() : "-"}
                </td>
                <td className={`border border-gray-300 px-1 py-1 text-right ${selectedId === item.id ? "" : "text-red-600"}`}>
                  {item.outboundQty > 0 ? item.outboundQty.toLocaleString() : "-"}
                </td>
                <td className={`border border-gray-300 px-1 py-1 text-right ${selectedId === item.id ? "" : "text-red-600"}`}>
                  {item.outboundAmount > 0 ? item.outboundAmount.toLocaleString() : "-"}
                </td>
                <td className={`border border-gray-300 px-1 py-1 text-right ${selectedId === item.id ? "" : item.adjustQty !== 0 ? "text-purple-600" : ""}`}>
                  {item.adjustQty !== 0 ? item.adjustQty : "-"}
                </td>
                <td className={`border border-gray-300 px-1 py-1 text-right ${selectedId === item.id ? "" : item.adjustAmount !== 0 ? "text-purple-600" : ""}`}>
                  {item.adjustAmount !== 0 ? item.adjustAmount.toLocaleString() : "-"}
                </td>
                <td className={`border border-gray-300 px-1 py-1 text-right font-medium ${selectedId === item.id ? "" : "text-green-600"}`}>
                  {item.currentQty.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-1 py-1 text-right font-medium ${selectedId === item.id ? "" : "text-green-600"}`}>
                  {item.currentAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">{item.avgCost.toLocaleString()}</td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={5}>
                (합계: {filteredData.length}건)
              </td>
              <td className="border border-gray-400 px-1 py-1 text-right">{totals.prevQty.toLocaleString()}</td>
              <td className="border border-gray-400 px-1 py-1 text-right">{totals.prevAmount.toLocaleString()}</td>
              <td className="border border-gray-400 px-1 py-1 text-right text-blue-600">{totals.inboundQty.toLocaleString()}</td>
              <td className="border border-gray-400 px-1 py-1 text-right text-blue-600">{totals.inboundAmount.toLocaleString()}</td>
              <td className="border border-gray-400 px-1 py-1 text-right text-red-600">{totals.outboundQty.toLocaleString()}</td>
              <td className="border border-gray-400 px-1 py-1 text-right text-red-600">{totals.outboundAmount.toLocaleString()}</td>
              <td className="border border-gray-400 px-1 py-1 text-right text-purple-600">{totals.adjustQty}</td>
              <td className="border border-gray-400 px-1 py-1 text-right text-purple-600">{totals.adjustAmount.toLocaleString()}</td>
              <td className="border border-gray-400 px-1 py-1 text-right text-green-600">{totals.currentQty.toLocaleString()}</td>
              <td className="border border-gray-400 px-1 py-1 text-right text-green-600">{totals.currentAmount.toLocaleString()}</td>
              <td className="border border-gray-400 px-2 py-1"></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredData.length}건 | 현재고금액: {totals.currentAmount.toLocaleString()}원 | loading ok
      </div>
    </div>
  );
}
