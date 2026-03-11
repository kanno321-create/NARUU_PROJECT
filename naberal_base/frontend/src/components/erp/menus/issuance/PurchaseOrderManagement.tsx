"use client";

import React, { useState } from "react";

interface PurchaseOrderItem {
  id: string;
  orderNo: string;
  orderDate: string;
  deliveryDate: string;
  supplierCode: string;
  supplierName: string;
  contactPerson: string;
  contactPhone: string;
  totalAmount: number;
  taxAmount: number;
  grandTotal: number;
  itemCount: number;
  status: string;
  receivedQty: number;
  totalQty: number;
  memo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: PurchaseOrderItem[] = [
  {
    id: "1",
    orderNo: "PO2024120001",
    orderDate: "2025-12-05",
    deliveryDate: "2025-12-10",
    supplierCode: "S001",
    supplierName: "공급업체A",
    contactPerson: "김담당",
    contactPhone: "010-1234-5678",
    totalAmount: 5000000,
    taxAmount: 500000,
    grandTotal: 5500000,
    itemCount: 5,
    status: "발주완료",
    receivedQty: 0,
    totalQty: 100,
    memo: "정기발주",
  },
  {
    id: "2",
    orderNo: "PO2024120002",
    orderDate: "2025-12-04",
    deliveryDate: "2025-12-08",
    supplierCode: "S002",
    supplierName: "공급업체B",
    contactPerson: "이담당",
    contactPhone: "010-2345-6789",
    totalAmount: 3200000,
    taxAmount: 320000,
    grandTotal: 3520000,
    itemCount: 3,
    status: "부분입고",
    receivedQty: 30,
    totalQty: 50,
    memo: "",
  },
  {
    id: "3",
    orderNo: "PO2024120003",
    orderDate: "2025-12-03",
    deliveryDate: "2025-12-07",
    supplierCode: "S003",
    supplierName: "공급업체C",
    contactPerson: "박담당",
    contactPhone: "010-3456-7890",
    totalAmount: 8500000,
    taxAmount: 850000,
    grandTotal: 9350000,
    itemCount: 8,
    status: "입고완료",
    receivedQty: 200,
    totalQty: 200,
    memo: "긴급발주",
  },
  {
    id: "4",
    orderNo: "PO2024120004",
    orderDate: "2025-12-02",
    deliveryDate: "2025-12-12",
    supplierCode: "S004",
    supplierName: "공급업체D",
    contactPerson: "최담당",
    contactPhone: "010-4567-8901",
    totalAmount: 12000000,
    taxAmount: 1200000,
    grandTotal: 13200000,
    itemCount: 12,
    status: "발주완료",
    receivedQty: 0,
    totalQty: 150,
    memo: "대량발주",
  },
  {
    id: "5",
    orderNo: "PO2024120005",
    orderDate: "2025-12-01",
    deliveryDate: "2025-12-05",
    supplierCode: "S001",
    supplierName: "공급업체A",
    contactPerson: "김담당",
    contactPhone: "010-1234-5678",
    totalAmount: 1800000,
    taxAmount: 180000,
    grandTotal: 1980000,
    itemCount: 2,
    status: "취소",
    receivedQty: 0,
    totalQty: 20,
    memo: "고객 취소",
  },
];

export function PurchaseOrderManagement() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [supplierFilter, setSupplierFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("전체");
  const [data] = useState<PurchaseOrderItem[]>(ORIGINAL_DATA);
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
      totalAmount: acc.totalAmount + item.totalAmount,
      taxAmount: acc.taxAmount + item.taxAmount,
      grandTotal: acc.grandTotal + item.grandTotal,
    }),
    { totalAmount: 0, taxAmount: 0, grandTotal: 0 }
  );

  const getStatusColor = (status: string, isSelected: boolean) => {
    if (isSelected) return "";
    switch (status) {
      case "입고완료": return "text-green-600";
      case "부분입고": return "text-blue-600";
      case "발주완료": return "text-orange-600";
      case "취소": return "text-gray-500 line-through";
      default: return "";
    }
  };

  const getRowBgColor = (status: string, isSelected: boolean) => {
    if (isSelected) return "bg-[#316AC5] text-white";
    switch (status) {
      case "입고완료": return "bg-green-50 hover:bg-green-100";
      case "취소": return "bg-gray-100 hover:bg-gray-200";
      default: return "hover:bg-gray-100";
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">발주서관리</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>➕</span> 신규등록
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>✏️</span> 수정
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🗑️</span> 삭제
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 복사
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-green-100 px-2 py-0.5 text-xs hover:bg-green-200">
          <span>📥</span> 입고처리
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-red-100 px-2 py-0.5 text-xs hover:bg-red-200">
          <span>❌</span> 취소
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🖨️</span> 인쇄
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📧</span> FAX/이메일
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
            <option value="발주완료">발주완료</option>
            <option value="부분입고">부분입고</option>
            <option value="입고완료">입고완료</option>
            <option value="취소">취소</option>
          </select>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색(F)
        </button>
      </div>

      {/* 상태별 요약 */}
      <div className="flex items-center gap-4 border-b bg-yellow-50 px-3 py-2 text-xs">
        <span className="font-medium">상태별 현황:</span>
        <span className="text-orange-600">발주완료: {statusSummary["발주완료"] || 0}건</span>
        <span className="text-blue-600">부분입고: {statusSummary["부분입고"] || 0}건</span>
        <span className="text-green-600">입고완료: {statusSummary["입고완료"] || 0}건</span>
        <span className="text-gray-500">취소: {statusSummary["취소"] || 0}건</span>
        <span className="ml-4 font-bold">총 발주금액: {totals.grandTotal.toLocaleString()}원</span>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-28">발주번호</th>
              <th className="border border-gray-400 px-2 py-1 w-24">발주일자</th>
              <th className="border border-gray-400 px-2 py-1 w-24">납기일자</th>
              <th className="border border-gray-400 px-2 py-1">공급업체</th>
              <th className="border border-gray-400 px-2 py-1 w-20">담당자</th>
              <th className="border border-gray-400 px-2 py-1 w-28">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">세액</th>
              <th className="border border-gray-400 px-2 py-1 w-28">합계금액</th>
              <th className="border border-gray-400 px-2 py-1 w-16">품목수</th>
              <th className="border border-gray-400 px-2 py-1 w-20">입고현황</th>
              <th className="border border-gray-400 px-2 py-1 w-20">상태</th>
              <th className="border border-gray-400 px-2 py-1">비고</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr
                key={item.id}
                className={`cursor-pointer ${getRowBgColor(item.status, selectedId === item.id)}`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.orderNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.orderDate}</td>
                <td className="border border-gray-300 px-2 py-1">{item.deliveryDate}</td>
                <td className="border border-gray-300 px-2 py-1">{item.supplierName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.contactPerson}</td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${
                  selectedId === item.id ? "" : item.status === "취소" ? "text-gray-400" : "text-blue-600"
                }`}>
                  {item.totalAmount.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${
                  selectedId === item.id ? "" : item.status === "취소" ? "text-gray-400" : "text-red-600"
                }`}>
                  {item.taxAmount.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right font-medium ${
                  selectedId === item.id ? "" : item.status === "취소" ? "text-gray-400" : ""
                }`}>
                  {item.grandTotal.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">{item.itemCount}</td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  {item.receivedQty}/{item.totalQty}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${getStatusColor(item.status, selectedId === item.id)}`}>
                  {item.status}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.memo}</td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={5}>
                (합계: {filteredData.length}건)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.totalAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.taxAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.grandTotal.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={4}></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredData.length}건 | loading ok
      </div>
    </div>
  );
}
