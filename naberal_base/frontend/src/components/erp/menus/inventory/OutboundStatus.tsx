"use client";

import React, { useState } from "react";

interface OutboundItem {
  id: string;
  outboundNo: string;
  outboundDate: string;
  customerCode: string;
  customerName: string;
  itemCode: string;
  itemName: string;
  specification: string;
  unit: string;
  requestQty: number;
  outboundQty: number;
  remainQty: number;
  unitPrice: number;
  totalAmount: number;
  warehouse: string;
  outboundType: string;
  status: string;
  memo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: OutboundItem[] = [
  {
    id: "1",
    outboundNo: "OB2024120001",
    outboundDate: "2025-12-05",
    customerCode: "C001",
    customerName: "테스트전자",
    itemCode: "P001",
    itemName: "SBE-104 차단기",
    specification: "4P 100AF 75AT",
    unit: "EA",
    requestQty: 20,
    outboundQty: 20,
    remainQty: 0,
    unitPrice: 55000,
    totalAmount: 1100000,
    warehouse: "본사창고",
    outboundType: "판매출고",
    status: "완료",
    memo: "",
  },
  {
    id: "2",
    outboundNo: "OB2024120002",
    outboundDate: "2025-12-05",
    customerCode: "C002",
    customerName: "제고상사",
    itemCode: "P003",
    itemName: "외함 600×800×200",
    specification: "STEEL 1.6T",
    unit: "면",
    requestQty: 5,
    outboundQty: 5,
    remainQty: 0,
    unitPrice: 150000,
    totalAmount: 750000,
    warehouse: "본사창고",
    outboundType: "판매출고",
    status: "완료",
    memo: "",
  },
  {
    id: "3",
    outboundNo: "OB2024120003",
    outboundDate: "2025-12-04",
    customerCode: "C003",
    customerName: "신규산업",
    itemCode: "P002",
    itemName: "SBE-204 차단기",
    specification: "4P 200AF 150AT",
    unit: "EA",
    requestQty: 15,
    outboundQty: 10,
    remainQty: 5,
    unitPrice: 100000,
    totalAmount: 1000000,
    warehouse: "본사창고",
    outboundType: "판매출고",
    status: "부분출고",
    memo: "재고부족으로 부분출고",
  },
  {
    id: "4",
    outboundNo: "OB2024120004",
    outboundDate: "2025-12-04",
    customerCode: "C004",
    customerName: "VIP무역",
    itemCode: "P004",
    itemName: "BUS-BAR 3T×15",
    specification: "COPPER",
    unit: "KG",
    requestQty: 50,
    outboundQty: 50,
    remainQty: 0,
    unitPrice: 25000,
    totalAmount: 1250000,
    warehouse: "본사창고",
    outboundType: "판매출고",
    status: "완료",
    memo: "",
  },
  {
    id: "5",
    outboundNo: "OB2024120005",
    outboundDate: "2025-12-03",
    customerCode: "C005",
    customerName: "일반기업",
    itemCode: "P006",
    itemName: "TERMINAL BLOCK",
    specification: "600V",
    unit: "EA",
    requestQty: 100,
    outboundQty: 100,
    remainQty: 0,
    unitPrice: 5000,
    totalAmount: 500000,
    warehouse: "제2창고",
    outboundType: "판매출고",
    status: "완료",
    memo: "",
  },
  {
    id: "6",
    outboundNo: "OB2024120006",
    outboundDate: "2025-12-03",
    customerCode: "",
    customerName: "현장투입",
    itemCode: "P005",
    itemName: "MC-22 마그네트",
    specification: "22A",
    unit: "EA",
    requestQty: 10,
    outboundQty: 5,
    remainQty: 5,
    unitPrice: 35000,
    totalAmount: 175000,
    warehouse: "본사창고",
    outboundType: "현장출고",
    status: "부분출고",
    memo: "재고부족",
  },
];

export function OutboundStatus() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [customerFilter, setCustomerFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("전체");
  const [statusFilter, setStatusFilter] = useState("전체");
  const [data] = useState<OutboundItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      (customerFilter === "" || item.customerName.includes(customerFilter)) &&
      (typeFilter === "전체" || item.outboundType === typeFilter) &&
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
      requestQty: acc.requestQty + item.requestQty,
      outboundQty: acc.outboundQty + item.outboundQty,
      remainQty: acc.remainQty + item.remainQty,
      totalAmount: acc.totalAmount + item.totalAmount,
    }),
    { requestQty: 0, outboundQty: 0, remainQty: 0, totalAmount: 0 }
  );

  const getStatusColor = (status: string, isSelected: boolean) => {
    if (isSelected) return "";
    switch (status) {
      case "완료": return "text-green-600";
      case "부분출고": return "text-orange-600";
      default: return "";
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">출고현황</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>➕</span> 출고등록
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
          <span className="text-xs">유형:</span>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="판매출고">판매출고</option>
            <option value="현장출고">현장출고</option>
          </select>
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
            <option value="부분출고">부분출고</option>
          </select>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          조 회(F)
        </button>
      </div>

      {/* 상태별 요약 */}
      <div className="flex items-center gap-6 border-b bg-red-50 px-3 py-2 text-xs">
        <span className="font-medium">출고현황:</span>
        <span className="text-green-600">완료: {statusSummary["완료"] || 0}건</span>
        <span className="text-orange-600">부분출고: {statusSummary["부분출고"] || 0}건</span>
        <span className="ml-4 font-bold">총 출고금액: {totals.totalAmount.toLocaleString()}원</span>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-28">출고번호</th>
              <th className="border border-gray-400 px-2 py-1 w-24">출고일자</th>
              <th className="border border-gray-400 px-2 py-1 w-24">거래처</th>
              <th className="border border-gray-400 px-2 py-1 w-20">품목코드</th>
              <th className="border border-gray-400 px-2 py-1">품목명</th>
              <th className="border border-gray-400 px-2 py-1 w-24">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-12">단위</th>
              <th className="border border-gray-400 px-2 py-1 w-16">요청수량</th>
              <th className="border border-gray-400 px-2 py-1 w-16">출고수량</th>
              <th className="border border-gray-400 px-2 py-1 w-16">잔량</th>
              <th className="border border-gray-400 px-2 py-1 w-20">단가</th>
              <th className="border border-gray-400 px-2 py-1 w-24">금액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">창고</th>
              <th className="border border-gray-400 px-2 py-1 w-20">출고유형</th>
              <th className="border border-gray-400 px-2 py-1 w-16">상태</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr
                key={item.id}
                className={`cursor-pointer ${
                  selectedId === item.id
                    ? "bg-[#316AC5] text-white"
                    : item.status === "부분출고"
                    ? "bg-yellow-50 hover:bg-yellow-100"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.outboundNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.outboundDate}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.itemCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.itemName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.specification}</td>
                <td className="border border-gray-300 px-2 py-1 text-center">{item.unit}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">{item.requestQty.toLocaleString()}</td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${selectedId === item.id ? "" : "text-red-600"}`}>
                  {item.outboundQty.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${selectedId === item.id ? "" : item.remainQty > 0 ? "text-orange-600" : ""}`}>
                  {item.remainQty.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">{item.unitPrice.toLocaleString()}</td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium">
                  {item.totalAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.warehouse}</td>
                <td className="border border-gray-300 px-2 py-1 text-center">{item.outboundType}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${getStatusColor(item.status, selectedId === item.id)}`}>
                  {item.status}
                </td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={7}>
                (합계: {filteredData.length}건)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.requestQty.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.outboundQty.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-orange-600">
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
        총 {filteredData.length}건 | 완료: {statusSummary["완료"] || 0} | 부분출고: {statusSummary["부분출고"] || 0} | loading ok
      </div>
    </div>
  );
}
