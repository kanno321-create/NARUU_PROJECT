"use client";

import React, { useState } from "react";

interface PurchaseTaxInvoiceItem {
  id: string;
  invoiceNo: string;
  issueDate: string;
  supplierCode: string;
  supplierName: string;
  businessNo: string;
  representative: string;
  supplyAmount: number;
  taxAmount: number;
  totalAmount: number;
  invoiceType: string;
  receiveType: string;
  approvalNo: string;
  status: string;
  memo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: PurchaseTaxInvoiceItem[] = [
  {
    id: "1",
    invoiceNo: "PT2024120001",
    issueDate: "2025-12-05",
    supplierCode: "S001",
    supplierName: "공급업체A",
    businessNo: "111-22-33333",
    representative: "김공급",
    supplyAmount: 5000000,
    taxAmount: 500000,
    totalAmount: 5500000,
    invoiceType: "세금계산서",
    receiveType: "전자",
    approvalNo: "20251205-12345678",
    status: "정상",
    memo: "",
  },
  {
    id: "2",
    invoiceNo: "PT2024120002",
    issueDate: "2025-12-04",
    supplierCode: "S002",
    supplierName: "공급업체B",
    businessNo: "222-33-44444",
    representative: "이공급",
    supplyAmount: 3200000,
    taxAmount: 320000,
    totalAmount: 3520000,
    invoiceType: "세금계산서",
    receiveType: "전자",
    approvalNo: "20251204-23456789",
    status: "정상",
    memo: "정기 납품",
  },
  {
    id: "3",
    invoiceNo: "PT2024120003",
    issueDate: "2025-12-03",
    supplierCode: "S003",
    supplierName: "공급업체C",
    businessNo: "333-44-55555",
    representative: "박공급",
    supplyAmount: 8500000,
    taxAmount: 850000,
    totalAmount: 9350000,
    invoiceType: "세금계산서",
    receiveType: "수기",
    approvalNo: "",
    status: "미확인",
    memo: "확인 필요",
  },
  {
    id: "4",
    invoiceNo: "PT2024120004",
    issueDate: "2025-12-02",
    supplierCode: "S004",
    supplierName: "공급업체D",
    businessNo: "444-55-66666",
    representative: "최공급",
    supplyAmount: 12000000,
    taxAmount: 1200000,
    totalAmount: 13200000,
    invoiceType: "계산서",
    receiveType: "전자",
    approvalNo: "20251202-34567890",
    status: "정상",
    memo: "면세품목",
  },
  {
    id: "5",
    invoiceNo: "PT2024120005",
    issueDate: "2025-12-01",
    supplierCode: "S001",
    supplierName: "공급업체A",
    businessNo: "111-22-33333",
    representative: "김공급",
    supplyAmount: 1800000,
    taxAmount: 180000,
    totalAmount: 1980000,
    invoiceType: "세금계산서",
    receiveType: "전자",
    approvalNo: "20251201-45678901",
    status: "수정",
    memo: "수정 발급",
  },
];

export function PurchaseTaxInvoice() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [supplierFilter, setSupplierFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("전체");
  const [data] = useState<PurchaseTaxInvoiceItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      (supplierFilter === "" || item.supplierName.includes(supplierFilter)) &&
      (typeFilter === "전체" || item.invoiceType === typeFilter)
  );

  // 유형별 집계
  const typeSummary = filteredData.reduce((acc, item) => {
    if (!acc[item.invoiceType]) {
      acc[item.invoiceType] = { count: 0, supplyAmount: 0, taxAmount: 0 };
    }
    acc[item.invoiceType].count += 1;
    acc[item.invoiceType].supplyAmount += item.supplyAmount;
    acc[item.invoiceType].taxAmount += item.taxAmount;
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

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">매입세금계산서</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>➕</span> 수기등록
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📥</span> 전자수신
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>✅</span> 확인처리
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🗑️</span> 삭제
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
          <span className="text-xs">공급자:</span>
          <input
            type="text"
            value={supplierFilter}
            onChange={(e) => setSupplierFilter(e.target.value)}
            placeholder="공급자명"
            className="rounded border border-gray-400 px-2 py-1 text-xs w-32"
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
            <option value="세금계산서">세금계산서</option>
            <option value="계산서">계산서</option>
          </select>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색(F)
        </button>
      </div>

      {/* 유형별 요약 */}
      <div className="border-b bg-purple-50 px-3 py-2">
        <div className="text-xs font-medium mb-1">▶ 유형별 집계</div>
        <div className="flex gap-4 text-xs">
          {Object.entries(typeSummary).map(([type, summary]) => (
            <div key={type} className="bg-white px-3 py-1 rounded border">
              <div className="font-medium text-purple-700">{type}</div>
              <div>건수: {summary.count}건</div>
              <div className="text-blue-600">공급가액: {summary.supplyAmount.toLocaleString()}</div>
              <div className="text-red-600">세액: {summary.taxAmount.toLocaleString()}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-28">계산서번호</th>
              <th className="border border-gray-400 px-2 py-1 w-24">발급일자</th>
              <th className="border border-gray-400 px-2 py-1">공급자명</th>
              <th className="border border-gray-400 px-2 py-1 w-28">사업자번호</th>
              <th className="border border-gray-400 px-2 py-1 w-28">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">세액</th>
              <th className="border border-gray-400 px-2 py-1 w-28">합계금액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">유형</th>
              <th className="border border-gray-400 px-2 py-1 w-16">수신</th>
              <th className="border border-gray-400 px-2 py-1 w-36">승인번호</th>
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
                    : item.status === "미확인"
                    ? "bg-yellow-50 hover:bg-yellow-100"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.invoiceNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.issueDate}</td>
                <td className="border border-gray-300 px-2 py-1">{item.supplierName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.businessNo}</td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">
                  {item.supplyAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-red-600">
                  {item.taxAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium">
                  {item.totalAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">{item.invoiceType}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  selectedId === item.id ? "" : item.receiveType === "전자" ? "text-blue-600" : "text-gray-600"
                }`}>
                  {item.receiveType}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-xs">{item.approvalNo || "-"}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  selectedId === item.id ? "" : item.status === "정상" ? "text-green-600" : item.status === "미확인" ? "text-orange-600" : "text-purple-600"
                }`}>
                  {item.status}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.memo}</td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={4}>
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
              <td className="border border-gray-400 px-2 py-1" colSpan={5}></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredData.length}건 | 전자: {filteredData.filter(d => d.receiveType === "전자").length}건 | 수기: {filteredData.filter(d => d.receiveType === "수기").length}건 | loading ok
      </div>
    </div>
  );
}
