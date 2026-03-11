"use client";

import React, { useState } from "react";

interface InboundItem {
  id: string;
  inboundNo: string;
  inboundDate: string;
  supplierCode: string;
  supplierName: string;
  itemCode: string;
  itemName: string;
  specification: string;
  unit: string;
  orderQty: number;
  inboundQty: number;
  remainQty: number;
  unitPrice: number;
  totalAmount: number;
  warehouse: string;
  status: string;
  memo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: InboundItem[] = [
  {
    id: "1",
    inboundNo: "IB2024120001",
    inboundDate: "2025-12-05",
    supplierCode: "S001",
    supplierName: "상도전기",
    itemCode: "P001",
    itemName: "SBE-104 차단기",
    specification: "4P 100AF 75AT",
    unit: "EA",
    orderQty: 50,
    inboundQty: 50,
    remainQty: 0,
    unitPrice: 45000,
    totalAmount: 2250000,
    warehouse: "본사창고",
    status: "완료",
    memo: "",
  },
  {
    id: "2",
    inboundNo: "IB2024120002",
    inboundDate: "2025-12-05",
    supplierCode: "S002",
    supplierName: "LS산전",
    itemCode: "P002",
    itemName: "ABN-204 차단기",
    specification: "4P 200AF 150AT",
    unit: "EA",
    orderQty: 30,
    inboundQty: 20,
    remainQty: 10,
    unitPrice: 85000,
    totalAmount: 1700000,
    warehouse: "본사창고",
    status: "부분입고",
    memo: "잔여분 12/10 입고예정",
  },
  {
    id: "3",
    inboundNo: "IB2024120003",
    inboundDate: "2025-12-04",
    supplierCode: "S003",
    supplierName: "금속공업사",
    itemCode: "P003",
    itemName: "외함 600×800×200",
    specification: "STEEL 1.6T",
    unit: "면",
    orderQty: 10,
    inboundQty: 10,
    remainQty: 0,
    unitPrice: 120000,
    totalAmount: 1200000,
    warehouse: "본사창고",
    status: "완료",
    memo: "",
  },
  {
    id: "4",
    inboundNo: "IB2024120004",
    inboundDate: "2025-12-04",
    supplierCode: "S004",
    supplierName: "동부금속",
    itemCode: "P004",
    itemName: "BUS-BAR 3T×15",
    specification: "COPPER",
    unit: "KG",
    orderQty: 100,
    inboundQty: 100,
    remainQty: 0,
    unitPrice: 20000,
    totalAmount: 2000000,
    warehouse: "본사창고",
    status: "완료",
    memo: "",
  },
  {
    id: "5",
    inboundNo: "IB2024120005",
    inboundDate: "2025-12-03",
    supplierCode: "S005",
    supplierName: "부품상사",
    itemCode: "P006",
    itemName: "TERMINAL BLOCK",
    specification: "600V",
    unit: "EA",
    orderQty: 200,
    inboundQty: 200,
    remainQty: 0,
    unitPrice: 4000,
    totalAmount: 800000,
    warehouse: "제2창고",
    status: "완료",
    memo: "",
  },
  {
    id: "6",
    inboundNo: "IB2024120006",
    inboundDate: "2025-12-03",
    supplierCode: "S001",
    supplierName: "상도전기",
    itemCode: "P005",
    itemName: "MC-22 마그네트",
    specification: "22A",
    unit: "EA",
    orderQty: 50,
    inboundQty: 0,
    remainQty: 50,
    unitPrice: 35000,
    totalAmount: 0,
    warehouse: "본사창고",
    status: "미입고",
    memo: "배송지연",
  },
];

export function InboundStatus() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [supplierFilter, setSupplierFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("전체");
  const [data] = useState<InboundItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      (supplierFilter === "" || item.supplierName.includes(supplierFilter)) &&
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
      orderQty: acc.orderQty + item.orderQty,
      inboundQty: acc.inboundQty + item.inboundQty,
      remainQty: acc.remainQty + item.remainQty,
      totalAmount: acc.totalAmount + item.totalAmount,
    }),
    { orderQty: 0, inboundQty: 0, remainQty: 0, totalAmount: 0 }
  );

  const getStatusColor = (status: string, isSelected: boolean) => {
    if (isSelected) return "";
    switch (status) {
      case "완료": return "text-green-600";
      case "부분입고": return "text-orange-600";
      case "미입고": return "text-red-600";
      default: return "";
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">입고현황</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>➕</span> 입고등록
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>✏️</span> 수정
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🗑️</span> 삭제
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
          <span className="text-xs">상태:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="완료">완료</option>
            <option value="부분입고">부분입고</option>
            <option value="미입고">미입고</option>
          </select>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          조 회(F)
        </button>
      </div>

      {/* 상태별 요약 */}
      <div className="flex items-center gap-6 border-b bg-blue-50 px-3 py-2 text-xs">
        <span className="font-medium">입고현황:</span>
        <span className="text-green-600">완료: {statusSummary["완료"] || 0}건</span>
        <span className="text-orange-600">부분입고: {statusSummary["부분입고"] || 0}건</span>
        <span className="text-red-600">미입고: {statusSummary["미입고"] || 0}건</span>
        <span className="ml-4 font-bold">총 입고금액: {totals.totalAmount.toLocaleString()}원</span>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-28">입고번호</th>
              <th className="border border-gray-400 px-2 py-1 w-24">입고일자</th>
              <th className="border border-gray-400 px-2 py-1 w-24">공급업체</th>
              <th className="border border-gray-400 px-2 py-1 w-20">품목코드</th>
              <th className="border border-gray-400 px-2 py-1">품목명</th>
              <th className="border border-gray-400 px-2 py-1 w-24">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-12">단위</th>
              <th className="border border-gray-400 px-2 py-1 w-16">발주수량</th>
              <th className="border border-gray-400 px-2 py-1 w-16">입고수량</th>
              <th className="border border-gray-400 px-2 py-1 w-16">잔량</th>
              <th className="border border-gray-400 px-2 py-1 w-20">단가</th>
              <th className="border border-gray-400 px-2 py-1 w-24">금액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">창고</th>
              <th className="border border-gray-400 px-2 py-1 w-16">상태</th>
              <th className="border border-gray-400 px-2 py-1">비고</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr
                key={item.id}
                className={`cursor-pointer ${
                  selectedId === item.id
                    ? "bg-[#316AC5] text-white"
                    : item.status === "미입고"
                    ? "bg-red-50 hover:bg-red-100"
                    : item.status === "부분입고"
                    ? "bg-yellow-50 hover:bg-yellow-100"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.inboundNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.inboundDate}</td>
                <td className="border border-gray-300 px-2 py-1">{item.supplierName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.itemCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.itemName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.specification}</td>
                <td className="border border-gray-300 px-2 py-1 text-center">{item.unit}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">{item.orderQty.toLocaleString()}</td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${selectedId === item.id ? "" : "text-blue-600"}`}>
                  {item.inboundQty.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${selectedId === item.id ? "" : item.remainQty > 0 ? "text-red-600" : ""}`}>
                  {item.remainQty.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">{item.unitPrice.toLocaleString()}</td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium">
                  {item.totalAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.warehouse}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${getStatusColor(item.status, selectedId === item.id)}`}>
                  {item.status}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.memo}</td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={7}>
                (합계: {filteredData.length}건)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.orderQty.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.inboundQty.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.remainQty.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
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
        총 {filteredData.length}건 | 입고완료: {statusSummary["완료"] || 0} | 부분입고: {statusSummary["부분입고"] || 0} | 미입고: {statusSummary["미입고"] || 0} | loading ok
      </div>
    </div>
  );
}
