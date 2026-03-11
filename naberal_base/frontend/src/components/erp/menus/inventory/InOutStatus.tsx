"use client";

import React, { useState } from "react";

interface InOutItem {
  id: string;
  transDate: string;
  transType: string;
  transNo: string;
  partnerCode: string;
  partnerName: string;
  itemCode: string;
  itemName: string;
  specification: string;
  unit: string;
  inboundQty: number;
  outboundQty: number;
  stockQty: number;
  unitPrice: number;
  inboundAmount: number;
  outboundAmount: number;
  warehouse: string;
  memo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: InOutItem[] = [
  {
    id: "1",
    transDate: "2025-12-05",
    transType: "입고",
    transNo: "IB2024120001",
    partnerCode: "S001",
    partnerName: "상도전기",
    itemCode: "P001",
    itemName: "SBE-104 차단기",
    specification: "4P 100AF 75AT",
    unit: "EA",
    inboundQty: 50,
    outboundQty: 0,
    stockQty: 120,
    unitPrice: 45000,
    inboundAmount: 2250000,
    outboundAmount: 0,
    warehouse: "본사창고",
    memo: "",
  },
  {
    id: "2",
    transDate: "2025-12-05",
    transType: "출고",
    transNo: "OB2024120001",
    partnerCode: "C001",
    partnerName: "테스트전자",
    itemCode: "P001",
    itemName: "SBE-104 차단기",
    specification: "4P 100AF 75AT",
    unit: "EA",
    inboundQty: 0,
    outboundQty: 20,
    stockQty: 100,
    unitPrice: 55000,
    inboundAmount: 0,
    outboundAmount: 1100000,
    warehouse: "본사창고",
    memo: "",
  },
  {
    id: "3",
    transDate: "2025-12-04",
    transType: "입고",
    transNo: "IB2024120003",
    partnerCode: "S003",
    partnerName: "금속공업사",
    itemCode: "P003",
    itemName: "외함 600×800×200",
    specification: "STEEL 1.6T",
    unit: "면",
    inboundQty: 10,
    outboundQty: 0,
    stockQty: 25,
    unitPrice: 120000,
    inboundAmount: 1200000,
    outboundAmount: 0,
    warehouse: "본사창고",
    memo: "",
  },
  {
    id: "4",
    transDate: "2025-12-04",
    transType: "출고",
    transNo: "OB2024120002",
    partnerCode: "C002",
    partnerName: "제고상사",
    itemCode: "P003",
    itemName: "외함 600×800×200",
    specification: "STEEL 1.6T",
    unit: "면",
    inboundQty: 0,
    outboundQty: 5,
    stockQty: 20,
    unitPrice: 150000,
    inboundAmount: 0,
    outboundAmount: 750000,
    warehouse: "본사창고",
    memo: "",
  },
  {
    id: "5",
    transDate: "2025-12-03",
    transType: "조정",
    transNo: "ADJ2024120001",
    partnerCode: "",
    partnerName: "재고실사",
    itemCode: "P006",
    itemName: "TERMINAL BLOCK",
    specification: "600V",
    unit: "EA",
    inboundQty: 10,
    outboundQty: 0,
    stockQty: 410,
    unitPrice: 4000,
    inboundAmount: 40000,
    outboundAmount: 0,
    warehouse: "제2창고",
    memo: "재고실사 조정",
  },
  {
    id: "6",
    transDate: "2025-12-03",
    transType: "출고",
    transNo: "OB2024120005",
    partnerCode: "C005",
    partnerName: "일반기업",
    itemCode: "P006",
    itemName: "TERMINAL BLOCK",
    specification: "600V",
    unit: "EA",
    inboundQty: 0,
    outboundQty: 100,
    stockQty: 400,
    unitPrice: 5000,
    inboundAmount: 0,
    outboundAmount: 500000,
    warehouse: "제2창고",
    memo: "",
  },
  {
    id: "7",
    transDate: "2025-12-02",
    transType: "입고",
    transNo: "IB2024120004",
    partnerCode: "S004",
    partnerName: "동부금속",
    itemCode: "P004",
    itemName: "BUS-BAR 3T×15",
    specification: "COPPER",
    unit: "KG",
    inboundQty: 100,
    outboundQty: 0,
    stockQty: 200,
    unitPrice: 20000,
    inboundAmount: 2000000,
    outboundAmount: 0,
    warehouse: "본사창고",
    memo: "",
  },
  {
    id: "8",
    transDate: "2025-12-02",
    transType: "출고",
    transNo: "OB2024120004",
    partnerCode: "C004",
    partnerName: "VIP무역",
    itemCode: "P004",
    itemName: "BUS-BAR 3T×15",
    specification: "COPPER",
    unit: "KG",
    inboundQty: 0,
    outboundQty: 50,
    stockQty: 150,
    unitPrice: 25000,
    inboundAmount: 0,
    outboundAmount: 1250000,
    warehouse: "본사창고",
    memo: "",
  },
];

export function InOutStatus() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [typeFilter, setTypeFilter] = useState("전체");
  const [itemFilter, setItemFilter] = useState("");
  const [warehouseFilter, setWarehouseFilter] = useState("전체");
  const [data] = useState<InOutItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      (typeFilter === "전체" || item.transType === typeFilter) &&
      (itemFilter === "" || item.itemName.includes(itemFilter) || item.itemCode.includes(itemFilter)) &&
      (warehouseFilter === "전체" || item.warehouse === warehouseFilter)
  );

  // 유형별 집계
  const typeSummary = filteredData.reduce((acc, item) => {
    if (!acc[item.transType]) {
      acc[item.transType] = { count: 0, inbound: 0, outbound: 0 };
    }
    acc[item.transType].count += 1;
    acc[item.transType].inbound += item.inboundAmount;
    acc[item.transType].outbound += item.outboundAmount;
    return acc;
  }, {} as Record<string, { count: number; inbound: number; outbound: number }>);

  // 합계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      inboundQty: acc.inboundQty + item.inboundQty,
      outboundQty: acc.outboundQty + item.outboundQty,
      inboundAmount: acc.inboundAmount + item.inboundAmount,
      outboundAmount: acc.outboundAmount + item.outboundAmount,
    }),
    { inboundQty: 0, outboundQty: 0, inboundAmount: 0, outboundAmount: 0 }
  );

  const getTypeColor = (type: string, isSelected: boolean) => {
    if (isSelected) return "";
    switch (type) {
      case "입고": return "text-blue-600";
      case "출고": return "text-red-600";
      case "조정": return "text-purple-600";
      default: return "";
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">입출고현황</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-blue-100 px-2 py-0.5 text-xs hover:bg-blue-200">
          <span>📥</span> 입고등록
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-red-100 px-2 py-0.5 text-xs hover:bg-red-200">
          <span>📤</span> 출고등록
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📊</span> 분석
        </button>
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
            <option value="조정">조정</option>
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
        <div className="flex items-center gap-6 text-xs">
          <span className="font-medium">유형별 현황:</span>
          {typeSummary["입고"] && (
            <span className="text-blue-600">
              입고: {typeSummary["입고"].count}건 ({typeSummary["입고"].inbound.toLocaleString()}원)
            </span>
          )}
          {typeSummary["출고"] && (
            <span className="text-red-600">
              출고: {typeSummary["출고"].count}건 ({typeSummary["출고"].outbound.toLocaleString()}원)
            </span>
          )}
          {typeSummary["조정"] && (
            <span className="text-purple-600">
              조정: {typeSummary["조정"].count}건
            </span>
          )}
          <span className="ml-4 font-bold">
            순입출고: {(totals.inboundAmount - totals.outboundAmount).toLocaleString()}원
          </span>
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
              <th className="border border-gray-400 px-2 py-1 w-20">품목코드</th>
              <th className="border border-gray-400 px-2 py-1">품목명</th>
              <th className="border border-gray-400 px-2 py-1 w-24">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-12">단위</th>
              <th className="border border-gray-400 px-2 py-1 w-16">입고수량</th>
              <th className="border border-gray-400 px-2 py-1 w-16">출고수량</th>
              <th className="border border-gray-400 px-2 py-1 w-16">재고</th>
              <th className="border border-gray-400 px-2 py-1 w-24">입고금액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">출고금액</th>
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
                    : item.transType === "조정"
                    ? "bg-purple-50 hover:bg-purple-100"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1">{item.transDate}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center font-medium ${getTypeColor(item.transType, selectedId === item.id)}`}>
                  {item.transType}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.transNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.partnerName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.itemCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.itemName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.specification}</td>
                <td className="border border-gray-300 px-2 py-1 text-center">{item.unit}</td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${selectedId === item.id ? "" : item.inboundQty > 0 ? "text-blue-600" : ""}`}>
                  {item.inboundQty > 0 ? item.inboundQty.toLocaleString() : "-"}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${selectedId === item.id ? "" : item.outboundQty > 0 ? "text-red-600" : ""}`}>
                  {item.outboundQty > 0 ? item.outboundQty.toLocaleString() : "-"}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium">
                  {item.stockQty.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${selectedId === item.id ? "" : item.inboundAmount > 0 ? "text-blue-600" : ""}`}>
                  {item.inboundAmount > 0 ? item.inboundAmount.toLocaleString() : "-"}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${selectedId === item.id ? "" : item.outboundAmount > 0 ? "text-red-600" : ""}`}>
                  {item.outboundAmount > 0 ? item.outboundAmount.toLocaleString() : "-"}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.warehouse}</td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={8}>
                (합계: {filteredData.length}건)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.inboundQty.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.outboundQty.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.inboundAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.outboundAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredData.length}건 | 입고: {typeSummary["입고"]?.count || 0} | 출고: {typeSummary["출고"]?.count || 0} | 조정: {typeSummary["조정"]?.count || 0} | loading ok
      </div>
    </div>
  );
}
