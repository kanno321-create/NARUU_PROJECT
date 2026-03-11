"use client";

import React, { useState } from "react";

interface TaxInvoiceRegisterItem {
  id: string;
  invoiceNo: string;
  issueDate: string;
  invoiceType: string;
  transType: string;
  partnerCode: string;
  partnerName: string;
  businessNo: string;
  representative: string;
  supplyAmount: number;
  taxAmount: number;
  totalAmount: number;
  issueType: string;
  approvalNo: string;
  status: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: TaxInvoiceRegisterItem[] = [
  {
    id: "1",
    invoiceNo: "TI2024120001",
    issueDate: "2025-12-05",
    invoiceType: "세금계산서",
    transType: "매출",
    partnerCode: "C001",
    partnerName: "테스트전자",
    businessNo: "123-45-67890",
    representative: "김대표",
    supplyAmount: 5000000,
    taxAmount: 500000,
    totalAmount: 5500000,
    issueType: "전자",
    approvalNo: "20251205-12345678",
    status: "정상",
  },
  {
    id: "2",
    invoiceNo: "TI2024120002",
    issueDate: "2025-12-05",
    invoiceType: "세금계산서",
    transType: "매입",
    partnerCode: "S001",
    partnerName: "공급업체A",
    businessNo: "111-22-33333",
    representative: "이공급",
    supplyAmount: 3200000,
    taxAmount: 320000,
    totalAmount: 3520000,
    issueType: "전자",
    approvalNo: "20251205-23456789",
    status: "정상",
  },
  {
    id: "3",
    invoiceNo: "TI2024120003",
    issueDate: "2025-12-04",
    invoiceType: "세금계산서",
    transType: "매출",
    partnerCode: "C002",
    partnerName: "제고상사",
    businessNo: "234-56-78901",
    representative: "박사장",
    supplyAmount: 8500000,
    taxAmount: 850000,
    totalAmount: 9350000,
    issueType: "전자",
    approvalNo: "20251204-34567890",
    status: "정상",
  },
  {
    id: "4",
    invoiceNo: "TI2024120004",
    issueDate: "2025-12-04",
    invoiceType: "수정세금계산서",
    transType: "매출",
    partnerCode: "C001",
    partnerName: "테스트전자",
    businessNo: "123-45-67890",
    representative: "김대표",
    supplyAmount: -500000,
    taxAmount: -50000,
    totalAmount: -550000,
    issueType: "전자",
    approvalNo: "20251204-45678901",
    status: "수정",
  },
  {
    id: "5",
    invoiceNo: "TI2024120005",
    issueDate: "2025-12-03",
    invoiceType: "계산서",
    transType: "매출",
    partnerCode: "C003",
    partnerName: "신규산업",
    businessNo: "345-67-89012",
    representative: "최신규",
    supplyAmount: 2000000,
    taxAmount: 0,
    totalAmount: 2000000,
    issueType: "수기",
    approvalNo: "",
    status: "정상",
  },
  {
    id: "6",
    invoiceNo: "TI2024120006",
    issueDate: "2025-12-03",
    invoiceType: "세금계산서",
    transType: "매입",
    partnerCode: "S002",
    partnerName: "공급업체B",
    businessNo: "222-33-44444",
    representative: "정공급",
    supplyAmount: 4500000,
    taxAmount: 450000,
    totalAmount: 4950000,
    issueType: "전자",
    approvalNo: "20251203-56789012",
    status: "정상",
  },
];

export function TaxInvoiceRegister() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [transTypeFilter, setTransTypeFilter] = useState("전체");
  const [invoiceTypeFilter, setInvoiceTypeFilter] = useState("전체");
  const [partnerFilter, setPartnerFilter] = useState("");
  const [data] = useState<TaxInvoiceRegisterItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      (transTypeFilter === "전체" || item.transType === transTypeFilter) &&
      (invoiceTypeFilter === "전체" || item.invoiceType === invoiceTypeFilter) &&
      (partnerFilter === "" || item.partnerName.includes(partnerFilter))
  );

  // 거래유형별 집계
  const transTypeSummary = filteredData.reduce((acc, item) => {
    if (!acc[item.transType]) {
      acc[item.transType] = { count: 0, supplyAmount: 0, taxAmount: 0 };
    }
    acc[item.transType].count += 1;
    acc[item.transType].supplyAmount += item.supplyAmount;
    acc[item.transType].taxAmount += item.taxAmount;
    return acc;
  }, {} as Record<string, { count: number; supplyAmount: number; taxAmount: number }>);

  // 합계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      supplyAmount: acc.supplyAmount + item.supplyAmount,
      taxAmount: acc.taxAmount + item.taxAmount,
      totalAmount: acc.totalAmount + item.totalAmount,
    }),
    { supplyAmount: 0, taxAmount: 0, totalAmount: 0 }
  );

  // 매출/매입 별도 집계
  const salesTotal = filteredData
    .filter(d => d.transType === "매출")
    .reduce((sum, d) => sum + d.totalAmount, 0);
  const purchaseTotal = filteredData
    .filter(d => d.transType === "매입")
    .reduce((sum, d) => sum + d.totalAmount, 0);

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">세금계산서발행대장</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📊</span> 월별보고서
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 엑셀변환
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🖨️</span> 인쇄
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📤</span> 국세청제출
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
          <span className="text-xs">거래유형:</span>
          <select
            value={transTypeFilter}
            onChange={(e) => setTransTypeFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="매출">매출</option>
            <option value="매입">매입</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">계산서유형:</span>
          <select
            value={invoiceTypeFilter}
            onChange={(e) => setInvoiceTypeFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="세금계산서">세금계산서</option>
            <option value="수정세금계산서">수정세금계산서</option>
            <option value="계산서">계산서</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">거래처:</span>
          <input
            type="text"
            value={partnerFilter}
            onChange={(e) => setPartnerFilter(e.target.value)}
            placeholder="거래처명"
            className="rounded border border-gray-400 px-2 py-1 text-xs w-32"
          />
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색(F)
        </button>
      </div>

      {/* 유형별 요약 */}
      <div className="grid grid-cols-3 gap-2 border-b bg-blue-50 px-3 py-2">
        <div className="bg-white px-3 py-2 rounded border text-center">
          <div className="text-xs text-gray-600">매출 합계</div>
          <div className="text-sm font-bold text-blue-600">{salesTotal.toLocaleString()}원</div>
          <div className="text-xs text-gray-500">
            {transTypeSummary["매출"]?.count || 0}건
          </div>
        </div>
        <div className="bg-white px-3 py-2 rounded border text-center">
          <div className="text-xs text-gray-600">매입 합계</div>
          <div className="text-sm font-bold text-red-600">{purchaseTotal.toLocaleString()}원</div>
          <div className="text-xs text-gray-500">
            {transTypeSummary["매입"]?.count || 0}건
          </div>
        </div>
        <div className="bg-white px-3 py-2 rounded border text-center">
          <div className="text-xs text-gray-600">차액 (매출-매입)</div>
          <div className={`text-sm font-bold ${salesTotal - purchaseTotal >= 0 ? "text-green-600" : "text-red-600"}`}>
            {(salesTotal - purchaseTotal).toLocaleString()}원
          </div>
        </div>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-28">계산서번호</th>
              <th className="border border-gray-400 px-2 py-1 w-24">발급일자</th>
              <th className="border border-gray-400 px-2 py-1 w-20">유형</th>
              <th className="border border-gray-400 px-2 py-1 w-16">거래</th>
              <th className="border border-gray-400 px-2 py-1">거래처명</th>
              <th className="border border-gray-400 px-2 py-1 w-28">사업자번호</th>
              <th className="border border-gray-400 px-2 py-1 w-28">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">세액</th>
              <th className="border border-gray-400 px-2 py-1 w-28">합계금액</th>
              <th className="border border-gray-400 px-2 py-1 w-16">발행</th>
              <th className="border border-gray-400 px-2 py-1 w-36">승인번호</th>
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
                    : item.supplyAmount < 0
                    ? "bg-red-50 hover:bg-red-100"
                    : item.transType === "매출"
                    ? "bg-blue-50 hover:bg-blue-100"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.invoiceNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.issueDate}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  selectedId === item.id ? "" : item.invoiceType.includes("수정") ? "text-red-600" : ""
                }`}>
                  {item.invoiceType}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-center font-medium ${
                  selectedId === item.id ? "" : item.transType === "매출" ? "text-blue-600" : "text-red-600"
                }`}>
                  {item.transType}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.partnerName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.businessNo}</td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${
                  selectedId === item.id ? "" : item.supplyAmount < 0 ? "text-red-600" : "text-blue-600"
                }`}>
                  {item.supplyAmount.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${
                  selectedId === item.id ? "" : "text-red-600"
                }`}>
                  {item.taxAmount.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right font-medium ${
                  selectedId === item.id ? "" : item.totalAmount < 0 ? "text-red-600" : ""
                }`}>
                  {item.totalAmount.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  selectedId === item.id ? "" : item.issueType === "전자" ? "text-blue-600" : "text-gray-600"
                }`}>
                  {item.issueType}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-xs">{item.approvalNo || "-"}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  selectedId === item.id ? "" : item.status === "정상" ? "text-green-600" : "text-purple-600"
                }`}>
                  {item.status}
                </td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={6}>
                (합계: {filteredData.length}건)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.supplyAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.taxAmount.toLocaleString()}
              </td>
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
        총 {filteredData.length}건 | 매출: {transTypeSummary["매출"]?.count || 0}건 | 매입: {transTypeSummary["매입"]?.count || 0}건 | loading ok
      </div>
    </div>
  );
}
