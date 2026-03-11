"use client";

import React, { useState } from "react";

interface TransactionStatementItem {
  id: string;
  statementNo: string;
  statementDate: string;
  customerCode: string;
  customerName: string;
  businessNo: string;
  representative: string;
  totalAmount: number;
  taxAmount: number;
  grandTotal: number;
  itemCount: number;
  issueType: string;
  printStatus: string;
  memo: string;
}

interface StatementDetailItem {
  id: string;
  productCode: string;
  productName: string;
  spec: string;
  unit: string;
  quantity: number;
  unitPrice: number;
  supplyAmount: number;
  taxAmount: number;
  totalAmount: number;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: TransactionStatementItem[] = [
  {
    id: "1",
    statementNo: "TS2024120001",
    statementDate: "2025-12-05",
    customerCode: "C001",
    customerName: "테스트전자",
    businessNo: "123-45-67890",
    representative: "김대표",
    totalAmount: 5000000,
    taxAmount: 500000,
    grandTotal: 5500000,
    itemCount: 5,
    issueType: "발행",
    printStatus: "출력완료",
    memo: "12월 납품건",
  },
  {
    id: "2",
    statementNo: "TS2024120002",
    statementDate: "2025-12-04",
    customerCode: "C002",
    customerName: "제고상사",
    businessNo: "234-56-78901",
    representative: "이사장",
    totalAmount: 3200000,
    taxAmount: 320000,
    grandTotal: 3520000,
    itemCount: 3,
    issueType: "발행",
    printStatus: "미출력",
    memo: "",
  },
  {
    id: "3",
    statementNo: "TS2024120003",
    statementDate: "2025-12-03",
    customerCode: "C003",
    customerName: "신규산업",
    businessNo: "345-67-89012",
    representative: "박신규",
    totalAmount: 8500000,
    taxAmount: 850000,
    grandTotal: 9350000,
    itemCount: 8,
    issueType: "발행",
    printStatus: "출력완료",
    memo: "긴급 납품",
  },
  {
    id: "4",
    statementNo: "TS2024120004",
    statementDate: "2025-12-02",
    customerCode: "C004",
    customerName: "VIP무역",
    businessNo: "456-78-90123",
    representative: "최VIP",
    totalAmount: 12000000,
    taxAmount: 1200000,
    grandTotal: 13200000,
    itemCount: 12,
    issueType: "발행",
    printStatus: "출력완료",
    memo: "대량주문",
  },
  {
    id: "5",
    statementNo: "TS2024120005",
    statementDate: "2025-12-01",
    customerCode: "C005",
    customerName: "일반기업",
    businessNo: "567-89-01234",
    representative: "정일반",
    totalAmount: 1800000,
    taxAmount: 180000,
    grandTotal: 1980000,
    itemCount: 2,
    issueType: "미발행",
    printStatus: "미출력",
    memo: "",
  },
];

const SAMPLE_DETAILS: StatementDetailItem[] = [
  { id: "1", productCode: "P001", productName: "전자부품A", spec: "규격A", unit: "EA", quantity: 100, unitPrice: 10000, supplyAmount: 1000000, taxAmount: 100000, totalAmount: 1100000 },
  { id: "2", productCode: "P002", productName: "전자부품B", spec: "규격B", unit: "EA", quantity: 50, unitPrice: 20000, supplyAmount: 1000000, taxAmount: 100000, totalAmount: 1100000 },
  { id: "3", productCode: "P003", productName: "케이블", spec: "5M", unit: "M", quantity: 200, unitPrice: 5000, supplyAmount: 1000000, taxAmount: 100000, totalAmount: 1100000 },
  { id: "4", productCode: "P004", productName: "커넥터", spec: "대형", unit: "SET", quantity: 20, unitPrice: 50000, supplyAmount: 1000000, taxAmount: 100000, totalAmount: 1100000 },
  { id: "5", productCode: "P005", productName: "기타자재", spec: "혼합", unit: "식", quantity: 1, unitPrice: 1000000, supplyAmount: 1000000, taxAmount: 100000, totalAmount: 1100000 },
];

interface DetailModalProps {
  item: TransactionStatementItem;
  onClose: () => void;
}

function DetailModal({ item, onClose }: DetailModalProps) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded shadow-lg w-[900px] max-h-[90vh] overflow-hidden flex flex-col">
        {/* 모달 헤더 */}
        <div className="flex items-center justify-between bg-gradient-to-r from-blue-600 to-blue-400 px-4 py-2">
          <span className="text-white font-medium">
            거래명세서 상세 - {item.statementNo}
          </span>
          <button onClick={onClose} className="text-white hover:text-gray-200 text-xl font-bold">×</button>
        </div>

        {/* 기본 정보 */}
        <div className="p-4 border-b bg-gray-50">
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">명세서번호:</span>
              <span className="ml-2 font-medium">{item.statementNo}</span>
            </div>
            <div>
              <span className="text-gray-500">작성일자:</span>
              <span className="ml-2">{item.statementDate}</span>
            </div>
            <div>
              <span className="text-gray-500">거래처:</span>
              <span className="ml-2 font-medium">{item.customerName}</span>
            </div>
            <div>
              <span className="text-gray-500">사업자번호:</span>
              <span className="ml-2">{item.businessNo}</span>
            </div>
          </div>
        </div>

        {/* 품목 목록 */}
        <div className="flex-1 overflow-auto p-4">
          <div className="text-sm font-medium mb-2">품목 내역</div>
          <table className="w-full border-collapse text-xs">
            <thead className="bg-[#E8E4D9]">
              <tr>
                <th className="border border-gray-400 px-2 py-1 w-20">품목코드</th>
                <th className="border border-gray-400 px-2 py-1">품명</th>
                <th className="border border-gray-400 px-2 py-1 w-20">규격</th>
                <th className="border border-gray-400 px-2 py-1 w-16">단위</th>
                <th className="border border-gray-400 px-2 py-1 w-16">수량</th>
                <th className="border border-gray-400 px-2 py-1 w-24">단가</th>
                <th className="border border-gray-400 px-2 py-1 w-24">공급가액</th>
                <th className="border border-gray-400 px-2 py-1 w-20">세액</th>
                <th className="border border-gray-400 px-2 py-1 w-24">합계</th>
              </tr>
            </thead>
            <tbody>
              {SAMPLE_DETAILS.map((detail) => (
                <tr key={detail.id} className="hover:bg-gray-100">
                  <td className="border border-gray-300 px-2 py-1">{detail.productCode}</td>
                  <td className="border border-gray-300 px-2 py-1">{detail.productName}</td>
                  <td className="border border-gray-300 px-2 py-1">{detail.spec}</td>
                  <td className="border border-gray-300 px-2 py-1 text-center">{detail.unit}</td>
                  <td className="border border-gray-300 px-2 py-1 text-right">{detail.quantity}</td>
                  <td className="border border-gray-300 px-2 py-1 text-right">{detail.unitPrice.toLocaleString()}</td>
                  <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">{detail.supplyAmount.toLocaleString()}</td>
                  <td className="border border-gray-300 px-2 py-1 text-right text-red-600">{detail.taxAmount.toLocaleString()}</td>
                  <td className="border border-gray-300 px-2 py-1 text-right font-medium">{detail.totalAmount.toLocaleString()}</td>
                </tr>
              ))}
              <tr className="bg-gray-200 font-medium">
                <td className="border border-gray-400 px-2 py-1" colSpan={6}>(합   계)</td>
                <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">{item.totalAmount.toLocaleString()}</td>
                <td className="border border-gray-400 px-2 py-1 text-right text-red-600">{item.taxAmount.toLocaleString()}</td>
                <td className="border border-gray-400 px-2 py-1 text-right">{item.grandTotal.toLocaleString()}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* 모달 푸터 */}
        <div className="flex justify-end gap-2 px-4 py-3 border-t bg-gray-50">
          <button className="px-4 py-1.5 text-sm border border-gray-400 rounded hover:bg-gray-100">인쇄</button>
          <button className="px-4 py-1.5 text-sm border border-gray-400 rounded hover:bg-gray-100">PDF 저장</button>
          <button onClick={onClose} className="px-4 py-1.5 text-sm bg-gray-500 text-white rounded hover:bg-gray-600">닫기</button>
        </div>
      </div>
    </div>
  );
}

export function TransactionStatementManagement() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [customerFilter, setCustomerFilter] = useState("");
  const [issueFilter, setIssueFilter] = useState("전체");
  const [data] = useState<TransactionStatementItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detailItem, setDetailItem] = useState<TransactionStatementItem | null>(null);

  const filteredData = data.filter(
    (item) =>
      (customerFilter === "" || item.customerName.includes(customerFilter)) &&
      (issueFilter === "전체" || item.issueType === issueFilter)
  );

  // 합계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      totalAmount: acc.totalAmount + item.totalAmount,
      taxAmount: acc.taxAmount + item.taxAmount,
      grandTotal: acc.grandTotal + item.grandTotal,
    }),
    { totalAmount: 0, taxAmount: 0, grandTotal: 0 }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">거래명세서관리</span>
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
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🖨️</span> 인쇄
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 엑셀변환
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📧</span> 이메일전송
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
          <span className="text-xs">발행상태:</span>
          <select
            value={issueFilter}
            onChange={(e) => setIssueFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="발행">발행</option>
            <option value="미발행">미발행</option>
          </select>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색(F)
        </button>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-28">명세서번호</th>
              <th className="border border-gray-400 px-2 py-1 w-24">작성일자</th>
              <th className="border border-gray-400 px-2 py-1 w-20">거래처코드</th>
              <th className="border border-gray-400 px-2 py-1">거래처명</th>
              <th className="border border-gray-400 px-2 py-1 w-28">사업자번호</th>
              <th className="border border-gray-400 px-2 py-1 w-28">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">세액</th>
              <th className="border border-gray-400 px-2 py-1 w-28">합계금액</th>
              <th className="border border-gray-400 px-2 py-1 w-16">품목수</th>
              <th className="border border-gray-400 px-2 py-1 w-16">발행</th>
              <th className="border border-gray-400 px-2 py-1 w-16">출력</th>
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
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
                onDoubleClick={() => setDetailItem(item)}
              >
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.statementNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.statementDate}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.businessNo}</td>
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
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  selectedId === item.id ? "" : item.issueType === "발행" ? "text-blue-600" : "text-orange-600"
                }`}>
                  {item.issueType}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  selectedId === item.id ? "" : item.printStatus === "출력완료" ? "text-green-600" : "text-gray-500"
                }`}>
                  {item.printStatus}
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

      {/* 상세 모달 */}
      {detailItem && <DetailModal item={detailItem} onClose={() => setDetailItem(null)} />}
    </div>
  );
}
