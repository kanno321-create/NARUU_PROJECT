"use client";

import React, { useState } from "react";

interface ItemTransaction {
  id: string;
  itemCode: string;
  itemName: string;
  specification: string;
  category: string;
  unit: string;
  openingQty: number;
  openingAmount: number;
  purchaseQty: number;
  purchaseAmount: number;
  salesQty: number;
  salesAmount: number;
  adjustQty: number;
  adjustAmount: number;
  closingQty: number;
  closingAmount: number;
  avgCost: number;
  turnoverRate: number;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: ItemTransaction[] = [
  {
    id: "1",
    itemCode: "P001",
    itemName: "SBE-104",
    specification: "4P 100AF 75AT 14kA",
    category: "MCCB(배선용차단기)",
    unit: "EA",
    openingQty: 45,
    openingAmount: 562500,
    purchaseQty: 120,
    purchaseAmount: 1500000,
    salesQty: 98,
    salesAmount: 1862000,
    adjustQty: 0,
    adjustAmount: 0,
    closingQty: 67,
    closingAmount: 837500,
    avgCost: 12500,
    turnoverRate: 146.3,
  },
  {
    id: "2",
    itemCode: "P002",
    itemName: "ABN-204",
    specification: "4P 200AF 150AT 35kA",
    category: "MCCB(배선용차단기)",
    unit: "EA",
    openingQty: 20,
    openingAmount: 700000,
    purchaseQty: 50,
    purchaseAmount: 1750000,
    salesQty: 42,
    salesAmount: 2226000,
    adjustQty: 0,
    adjustAmount: 0,
    closingQty: 28,
    closingAmount: 980000,
    avgCost: 35000,
    turnoverRate: 150.0,
  },
  {
    id: "3",
    itemCode: "P003",
    itemName: "SEE-52",
    specification: "2P 50AF 30AT 14kA",
    category: "ELB(누전차단기)",
    unit: "EA",
    openingQty: 85,
    openingAmount: 680000,
    purchaseQty: 200,
    purchaseAmount: 1600000,
    salesQty: 185,
    salesAmount: 2775000,
    adjustQty: -2,
    adjustAmount: -16000,
    closingQty: 98,
    closingAmount: 784000,
    avgCost: 8000,
    turnoverRate: 188.8,
  },
  {
    id: "4",
    itemCode: "P004",
    itemName: "외함 600×800×200",
    specification: "옥내노출 STEEL 1.6T",
    category: "외함",
    unit: "면",
    openingQty: 12,
    openingAmount: 1440000,
    purchaseQty: 30,
    purchaseAmount: 3600000,
    salesQty: 25,
    salesAmount: 4500000,
    adjustQty: 0,
    adjustAmount: 0,
    closingQty: 17,
    closingAmount: 2040000,
    avgCost: 120000,
    turnoverRate: 147.1,
  },
  {
    id: "5",
    itemCode: "P005",
    itemName: "MC-22",
    specification: "45×65×85mm",
    category: "마그네트",
    unit: "EA",
    openingQty: 25,
    openingAmount: 875000,
    purchaseQty: 60,
    purchaseAmount: 2100000,
    salesQty: 52,
    salesAmount: 2860000,
    adjustQty: 0,
    adjustAmount: 0,
    closingQty: 33,
    closingAmount: 1155000,
    avgCost: 35000,
    turnoverRate: 157.6,
  },
  {
    id: "6",
    itemCode: "P006",
    itemName: "TERMINAL BLOCK",
    specification: "600V",
    category: "부속자재",
    unit: "EA",
    openingQty: 500,
    openingAmount: 2000000,
    purchaseQty: 800,
    purchaseAmount: 3200000,
    salesQty: 720,
    salesAmount: 4320000,
    adjustQty: -10,
    adjustAmount: -40000,
    closingQty: 570,
    closingAmount: 2280000,
    avgCost: 4000,
    turnoverRate: 126.3,
  },
  {
    id: "7",
    itemCode: "P007",
    itemName: "BUS-BAR 3T×15",
    specification: "COPPER",
    category: "부속자재",
    unit: "KG",
    openingQty: 150,
    openingAmount: 3000000,
    purchaseQty: 350,
    purchaseAmount: 7000000,
    salesQty: 320,
    salesAmount: 9600000,
    adjustQty: 0,
    adjustAmount: 0,
    closingQty: 180,
    closingAmount: 3600000,
    avgCost: 20000,
    turnoverRate: 177.8,
  },
  {
    id: "8",
    itemCode: "P008",
    itemName: "SBS-403",
    specification: "3P 400AF 300AT 35kA",
    category: "MCCB(배선용차단기)",
    unit: "EA",
    openingQty: 8,
    openingAmount: 944000,
    purchaseQty: 15,
    purchaseAmount: 1770000,
    salesQty: 12,
    salesAmount: 2160000,
    adjustQty: 0,
    adjustAmount: 0,
    closingQty: 11,
    closingAmount: 1298000,
    avgCost: 118000,
    turnoverRate: 109.1,
  },
  {
    id: "9",
    itemCode: "P009",
    itemName: "P-COVER",
    specification: "아크릴(PC)",
    category: "부속자재",
    unit: "EA",
    openingQty: 30,
    openingAmount: 480000,
    purchaseQty: 80,
    purchaseAmount: 1280000,
    salesQty: 65,
    salesAmount: 1560000,
    adjustQty: 0,
    adjustAmount: 0,
    closingQty: 45,
    closingAmount: 720000,
    avgCost: 16000,
    turnoverRate: 144.4,
  },
  {
    id: "10",
    itemCode: "P010",
    itemName: "INSULATOR",
    specification: "EPOXY 40×40",
    category: "부속자재",
    unit: "EA",
    openingQty: 200,
    openingAmount: 220000,
    purchaseQty: 500,
    purchaseAmount: 550000,
    salesQty: 450,
    salesAmount: 675000,
    adjustQty: 0,
    adjustAmount: 0,
    closingQty: 250,
    closingAmount: 275000,
    avgCost: 1100,
    turnoverRate: 180.0,
  },
];

export function ItemTransactionStatus() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-31");
  const [categoryFilter, setCategoryFilter] = useState("전체");
  const [searchText, setSearchText] = useState("");
  const [data] = useState<ItemTransaction[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const categories = ["전체", ...new Set(data.map((item) => item.category))];

  const filteredData = data.filter(
    (item) =>
      (categoryFilter === "전체" || item.category === categoryFilter) &&
      (searchText === "" ||
        item.itemCode.includes(searchText) ||
        item.itemName.includes(searchText))
  );

  // 합계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      openingQty: acc.openingQty + item.openingQty,
      openingAmount: acc.openingAmount + item.openingAmount,
      purchaseQty: acc.purchaseQty + item.purchaseQty,
      purchaseAmount: acc.purchaseAmount + item.purchaseAmount,
      salesQty: acc.salesQty + item.salesQty,
      salesAmount: acc.salesAmount + item.salesAmount,
      adjustQty: acc.adjustQty + item.adjustQty,
      adjustAmount: acc.adjustAmount + item.adjustAmount,
      closingQty: acc.closingQty + item.closingQty,
      closingAmount: acc.closingAmount + item.closingAmount,
    }),
    {
      openingQty: 0,
      openingAmount: 0,
      purchaseQty: 0,
      purchaseAmount: 0,
      salesQty: 0,
      salesAmount: 0,
      adjustQty: 0,
      adjustAmount: 0,
      closingQty: 0,
      closingAmount: 0,
    }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">품목별거래현황</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🖨️</span> 인쇄
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📊</span> 차트
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
          <span className="text-xs">분류:</span>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">검색:</span>
          <input
            type="text"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="품목코드/품목명"
            className="w-32 rounded border border-gray-400 px-2 py-1 text-xs"
          />
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          조 회(F)
        </button>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>
                품목코드
              </th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>
                품목명
              </th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>
                규격
              </th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>
                분류
              </th>
              <th className="border border-gray-400 px-2 py-1" colSpan={2}>
                기초재고
              </th>
              <th className="border border-gray-400 px-2 py-1" colSpan={2}>
                매입(입고)
              </th>
              <th className="border border-gray-400 px-2 py-1" colSpan={2}>
                매출(출고)
              </th>
              <th className="border border-gray-400 px-2 py-1" colSpan={2}>
                조정
              </th>
              <th className="border border-gray-400 px-2 py-1" colSpan={2}>
                기말재고
              </th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>
                회전율
              </th>
            </tr>
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-14">수량</th>
              <th className="border border-gray-400 px-2 py-1 w-20">금액</th>
              <th className="border border-gray-400 px-2 py-1 w-14">수량</th>
              <th className="border border-gray-400 px-2 py-1 w-20">금액</th>
              <th className="border border-gray-400 px-2 py-1 w-14">수량</th>
              <th className="border border-gray-400 px-2 py-1 w-20">금액</th>
              <th className="border border-gray-400 px-2 py-1 w-14">수량</th>
              <th className="border border-gray-400 px-2 py-1 w-20">금액</th>
              <th className="border border-gray-400 px-2 py-1 w-14">수량</th>
              <th className="border border-gray-400 px-2 py-1 w-20">금액</th>
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
                <td className="border border-gray-300 px-2 py-1">
                  {item.itemCode}
                </td>
                <td className="border border-gray-300 px-2 py-1 font-medium">
                  {item.itemName}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-xs">
                  {item.specification}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-xs">
                  {item.category}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.openingQty.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.openingAmount.toLocaleString()}
                </td>
                <td
                  className={`border border-gray-300 px-2 py-1 text-right ${
                    selectedId === item.id ? "" : "text-blue-600"
                  }`}
                >
                  {item.purchaseQty.toLocaleString()}
                </td>
                <td
                  className={`border border-gray-300 px-2 py-1 text-right ${
                    selectedId === item.id ? "" : "text-blue-600"
                  }`}
                >
                  {item.purchaseAmount.toLocaleString()}
                </td>
                <td
                  className={`border border-gray-300 px-2 py-1 text-right ${
                    selectedId === item.id ? "" : "text-red-600"
                  }`}
                >
                  {item.salesQty.toLocaleString()}
                </td>
                <td
                  className={`border border-gray-300 px-2 py-1 text-right ${
                    selectedId === item.id ? "" : "text-red-600"
                  }`}
                >
                  {item.salesAmount.toLocaleString()}
                </td>
                <td
                  className={`border border-gray-300 px-2 py-1 text-right ${
                    selectedId === item.id
                      ? ""
                      : item.adjustQty !== 0
                        ? item.adjustQty > 0
                          ? "text-green-600"
                          : "text-orange-600"
                        : ""
                  }`}
                >
                  {item.adjustQty !== 0 ? item.adjustQty.toLocaleString() : ""}
                </td>
                <td
                  className={`border border-gray-300 px-2 py-1 text-right ${
                    selectedId === item.id
                      ? ""
                      : item.adjustAmount !== 0
                        ? item.adjustAmount > 0
                          ? "text-green-600"
                          : "text-orange-600"
                        : ""
                  }`}
                >
                  {item.adjustAmount !== 0
                    ? item.adjustAmount.toLocaleString()
                    : ""}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium">
                  {item.closingQty.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium">
                  {item.closingAmount.toLocaleString()}
                </td>
                <td
                  className={`border border-gray-300 px-2 py-1 text-right ${
                    selectedId === item.id
                      ? ""
                      : item.turnoverRate >= 150
                        ? "text-green-600"
                        : item.turnoverRate < 100
                          ? "text-orange-600"
                          : ""
                  }`}
                >
                  {item.turnoverRate.toFixed(1)}%
                </td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td
                className="border border-gray-400 px-2 py-1"
                colSpan={4}
              >
                합 계 ({filteredData.length}건)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.openingQty.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.openingAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.purchaseQty.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.purchaseAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.salesQty.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.salesAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.adjustQty !== 0 ? totals.adjustQty.toLocaleString() : ""}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.adjustAmount !== 0
                  ? totals.adjustAmount.toLocaleString()
                  : ""}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.closingQty.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.closingAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredData.length}건 | 기초재고:{" "}
        {totals.openingAmount.toLocaleString()} | 매입:{" "}
        {totals.purchaseAmount.toLocaleString()} | 매출:{" "}
        {totals.salesAmount.toLocaleString()} | 기말재고:{" "}
        {totals.closingAmount.toLocaleString()} | loading ok
      </div>
    </div>
  );
}
