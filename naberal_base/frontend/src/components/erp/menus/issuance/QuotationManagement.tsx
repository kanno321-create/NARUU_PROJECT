"use client";

import React, { useState } from "react";

interface QuotationItem {
  id: string;
  quotationNo: string;
  quotationDate: string;
  validUntil: string;
  customerCode: string;
  customerName: string;
  contactPerson: string;
  contactPhone: string;
  totalAmount: number;
  taxAmount: number;
  grandTotal: number;
  itemCount: number;
  status: string;
  orderConverted: boolean;
  memo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: QuotationItem[] = [
  {
    id: "1",
    quotationNo: "QT2024120001",
    quotationDate: "2025-12-05",
    validUntil: "2025-12-20",
    customerCode: "C001",
    customerName: "테스트전자",
    contactPerson: "김담당",
    contactPhone: "010-1234-5678",
    totalAmount: 8500000,
    taxAmount: 850000,
    grandTotal: 9350000,
    itemCount: 5,
    status: "발송완료",
    orderConverted: false,
    memo: "견적 요청",
  },
  {
    id: "2",
    quotationNo: "QT2024120002",
    quotationDate: "2025-12-04",
    validUntil: "2025-12-19",
    customerCode: "C002",
    customerName: "제고상사",
    contactPerson: "이담당",
    contactPhone: "010-2345-6789",
    totalAmount: 4200000,
    taxAmount: 420000,
    grandTotal: 4620000,
    itemCount: 3,
    status: "수주전환",
    orderConverted: true,
    memo: "",
  },
  {
    id: "3",
    quotationNo: "QT2024120003",
    quotationDate: "2025-12-03",
    validUntil: "2025-12-18",
    customerCode: "C003",
    customerName: "신규산업",
    contactPerson: "박담당",
    contactPhone: "010-3456-7890",
    totalAmount: 15000000,
    taxAmount: 1500000,
    grandTotal: 16500000,
    itemCount: 10,
    status: "작성중",
    orderConverted: false,
    memo: "대형 프로젝트",
  },
  {
    id: "4",
    quotationNo: "QT2024120004",
    quotationDate: "2025-12-02",
    validUntil: "2025-12-17",
    customerCode: "C004",
    customerName: "VIP무역",
    contactPerson: "최담당",
    contactPhone: "010-4567-8901",
    totalAmount: 22000000,
    taxAmount: 2200000,
    grandTotal: 24200000,
    itemCount: 15,
    status: "발송완료",
    orderConverted: false,
    memo: "연간계약건",
  },
  {
    id: "5",
    quotationNo: "QT2024120005",
    quotationDate: "2025-12-01",
    validUntil: "2025-12-16",
    customerCode: "C005",
    customerName: "일반기업",
    contactPerson: "정담당",
    contactPhone: "010-5678-9012",
    totalAmount: 3000000,
    taxAmount: 300000,
    grandTotal: 3300000,
    itemCount: 2,
    status: "견적마감",
    orderConverted: false,
    memo: "예산초과로 마감",
  },
];

export function QuotationManagement() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [customerFilter, setCustomerFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("전체");
  const [data] = useState<QuotationItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      (customerFilter === "" || item.customerName.includes(customerFilter)) &&
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
      case "수주전환": return "text-green-600";
      case "발송완료": return "text-blue-600";
      case "작성중": return "text-orange-600";
      case "견적마감": return "text-gray-500";
      default: return "";
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">견적서관리</span>
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
          <span>🔄</span> 수주전환
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🖨️</span> 인쇄
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📧</span> 이메일
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
            <option value="작성중">작성중</option>
            <option value="발송완료">발송완료</option>
            <option value="수주전환">수주전환</option>
            <option value="견적마감">견적마감</option>
          </select>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색(F)
        </button>
      </div>

      {/* 상태별 요약 */}
      <div className="flex items-center gap-4 border-b bg-yellow-50 px-3 py-2 text-xs">
        <span className="font-medium">상태별 현황:</span>
        <span className="text-orange-600">작성중: {statusSummary["작성중"] || 0}건</span>
        <span className="text-blue-600">발송완료: {statusSummary["발송완료"] || 0}건</span>
        <span className="text-green-600">수주전환: {statusSummary["수주전환"] || 0}건</span>
        <span className="text-gray-500">견적마감: {statusSummary["견적마감"] || 0}건</span>
        <span className="ml-4 font-bold">총 견적금액: {totals.grandTotal.toLocaleString()}원</span>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-28">견적번호</th>
              <th className="border border-gray-400 px-2 py-1 w-24">견적일자</th>
              <th className="border border-gray-400 px-2 py-1 w-24">유효기간</th>
              <th className="border border-gray-400 px-2 py-1">거래처명</th>
              <th className="border border-gray-400 px-2 py-1 w-20">담당자</th>
              <th className="border border-gray-400 px-2 py-1 w-28">연락처</th>
              <th className="border border-gray-400 px-2 py-1 w-28">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">세액</th>
              <th className="border border-gray-400 px-2 py-1 w-28">합계금액</th>
              <th className="border border-gray-400 px-2 py-1 w-16">품목수</th>
              <th className="border border-gray-400 px-2 py-1 w-20">상태</th>
              <th className="border border-gray-400 px-2 py-1 w-16">수주</th>
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
                    : item.orderConverted
                    ? "bg-green-50 hover:bg-green-100"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.quotationNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.quotationDate}</td>
                <td className="border border-gray-300 px-2 py-1">{item.validUntil}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.contactPerson}</td>
                <td className="border border-gray-300 px-2 py-1">{item.contactPhone}</td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">
                  {item.totalAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-red-600">
                  {item.taxAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium">
                  {item.grandTotal.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">{item.itemCount}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${getStatusColor(item.status, selectedId === item.id)}`}>
                  {item.status}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  {item.orderConverted ? "✓" : "-"}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.memo}</td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={6}>
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
        총 {filteredData.length}건 | 수주전환: {filteredData.filter(d => d.orderConverted).length}건 | loading ok
      </div>
    </div>
  );
}
