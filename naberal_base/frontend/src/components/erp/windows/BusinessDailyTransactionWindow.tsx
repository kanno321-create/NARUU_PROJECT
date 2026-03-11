"use client";

import React, { useState } from "react";

interface Transaction {
  id: string;
  voucherNo: number;       // 전표번호
  customerName: string;    // 거래처
  manager: string;         // 담당자
  voucherType: string;     // 전표종류 (매출, 매입, 수금, 지급, 잡전회식 등)
  amount: number;          // 거래금액
  memo: string;            // 메모
  taxInvoiceCreated: boolean;   // 세금계산서작성
  taxInvoiceSent: boolean;      // 세금계산서전송
  statementCreated: boolean;    // 거래명세서작성
  statementSent: boolean;       // 거래명세서전송
}

// 이지판매재고관리 원본 데이터 100% 복제 (2025-12-05 스크린샷 기준)
const ORIGINAL_TRANSACTIONS: Transaction[] = [
  { id: "1", voucherNo: 1, customerName: "테스트사업장", manager: "김이지", voucherType: "매출", amount: 233200, memo: "", taxInvoiceCreated: false, taxInvoiceSent: false, statementCreated: false, statementSent: false },
  { id: "2", voucherNo: 2, customerName: "이지사업장", manager: "이지팬", voucherType: "매입", amount: 132000, memo: "", taxInvoiceCreated: false, taxInvoiceSent: false, statementCreated: false, statementSent: false },
  { id: "3", voucherNo: 3, customerName: "테스트사업장", manager: "김이지", voucherType: "수금", amount: 100000, memo: "", taxInvoiceCreated: false, taxInvoiceSent: false, statementCreated: false, statementSent: false },
  { id: "4", voucherNo: 4, customerName: "이지사업장", manager: "이지팬", voucherType: "지급", amount: 32000, memo: "", taxInvoiceCreated: false, taxInvoiceSent: false, statementCreated: false, statementSent: false },
  { id: "5", voucherNo: 5, customerName: "(없음)", manager: "(없음)", voucherType: "잡전회식", amount: 50000, memo: "", taxInvoiceCreated: false, taxInvoiceSent: false, statementCreated: false, statementSent: false },
  { id: "6", voucherNo: 7, customerName: "재고사업장", manager: "박재고", voucherType: "매출", amount: 133100, memo: "", taxInvoiceCreated: false, taxInvoiceSent: false, statementCreated: false, statementSent: false },
  { id: "7", voucherNo: 8, customerName: "재고사업장", manager: "박재고", voucherType: "매입", amount: 93500, memo: "", taxInvoiceCreated: false, taxInvoiceSent: false, statementCreated: false, statementSent: false },
];

const VOUCHER_TYPES = [
  "모든 거래",
  "매출",
  "매입",
  "수금",
  "지급",
  "입출금(경비)",
  "잡전회식",
];

export function BusinessDailyTransactionWindow() {
  const [transactions, setTransactions] = useState<Transaction[]>(ORIGINAL_TRANSACTIONS);
  const [selectedRow, setSelectedRow] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState("일별종합전표현황");

  // 필터
  const [selectedDate, setSelectedDate] = useState("2025-12-05");
  const [selectedVoucherType, setSelectedVoucherType] = useState("모든 거래");

  // 필터링된 전표 목록
  const filteredTransactions = transactions.filter((t) => {
    if (selectedVoucherType === "모든 거래") return true;
    return t.voucherType === selectedVoucherType;
  });

  // 새로고침
  const handleRefresh = () => {
    setTransactions([...ORIGINAL_TRANSACTIONS]);
    setSelectedRow(null);
    setSelectedVoucherType("모든 거래");
  };

  // 건표복사
  const handleCopyVoucher = () => {
    if (selectedRow === null) {
      alert("복사할 전표를 선택하세요.");
      return;
    }
    const original = filteredTransactions[selectedRow];
    const newVoucher: Transaction = {
      ...original,
      id: String(Date.now()),
      voucherNo: Math.max(...transactions.map((t) => t.voucherNo)) + 1,
    };
    setTransactions([...transactions, newVoucher]);
  };

  // 행 더블클릭으로 상세 보기
  const handleRowDoubleClick = (index: number) => {
    setSelectedRow(index);
    const t = filteredTransactions[index];
    alert(`전표번호: ${t.voucherNo}\n거래처: ${t.customerName}\n담당자: ${t.manager}\n전표종류: ${t.voucherType}\n거래금액: ${t.amount.toLocaleString()}원`);
  };

  // 전표종류별 색상
  const getVoucherTypeColor = (type: string) => {
    switch (type) {
      case "매출": return "text-blue-600";
      case "매입": return "text-red-600";
      case "수금": return "text-green-600";
      case "지급": return "text-orange-600";
      default: return "text-gray-600";
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 탭바 - 이지판매재고관리 스타일 */}
      <div className="flex items-center border-b bg-gray-200">
        {["일별종합전표현황", "전체검색(F11)", "인터넷검색~도움말(F1)", "일정관리"].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`border-r border-gray-400 px-4 py-1.5 text-sm ${
              activeTab === tab
                ? "bg-white font-medium"
                : "bg-gray-100 hover:bg-gray-50"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* 필터 영역 - 이지판매재고관리 스타일 */}
      <div className="flex items-center justify-between border-b bg-gray-100 px-4 py-2">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm">거래일자:</span>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="rounded border border-gray-400 px-2 py-1 text-sm"
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-red-600 font-medium">전표종류</span>
            <select
              value={selectedVoucherType}
              onChange={(e) => setSelectedVoucherType(e.target.value)}
              className="rounded border border-gray-400 px-2 py-1 text-sm"
            >
              {VOUCHER_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleRefresh}
            className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
          >
            새로고침
          </button>
          <button
            onClick={handleCopyVoucher}
            className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
          >
            건표복사
          </button>
        </div>
        <div className="flex items-center gap-2">
          <button className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
            자동조절(F3)
          </button>
          <button className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
            출력하기
          </button>
        </div>
      </div>

      {/* 그리드 - 이지판매재고관리 컬럼 100% */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="w-8 border border-gray-400 px-2 py-1 text-center font-normal">
                <input type="checkbox" />
              </th>
              <th className="w-20 border border-gray-400 px-2 py-1 text-center font-normal">전표번호</th>
              <th className="w-32 border border-gray-400 px-2 py-1 text-left font-normal">거래처</th>
              <th className="w-20 border border-gray-400 px-2 py-1 text-left font-normal">담당자</th>
              <th className="w-24 border border-gray-400 px-2 py-1 text-center font-normal">전표종류</th>
              <th className="w-28 border border-gray-400 px-2 py-1 text-right font-normal">거래금액</th>
              <th className="w-40 border border-gray-400 px-2 py-1 text-left font-normal">메모</th>
              <th className="w-24 border border-gray-400 px-2 py-1 text-center font-normal">세금계산서작성</th>
              <th className="w-24 border border-gray-400 px-2 py-1 text-center font-normal">세금계산서전송</th>
              <th className="w-24 border border-gray-400 px-2 py-1 text-center font-normal">거래명세서작성</th>
              <th className="w-24 border border-gray-400 px-2 py-1 text-center font-normal">거래명세서전송</th>
            </tr>
          </thead>
          <tbody>
            {filteredTransactions.map((transaction, index) => (
              <tr
                key={transaction.id}
                className={`cursor-pointer ${
                  selectedRow === index
                    ? "bg-[#316AC5] text-white"
                    : "bg-white hover:bg-gray-100"
                }`}
                onClick={() => setSelectedRow(index)}
                onDoubleClick={() => handleRowDoubleClick(index)}
              >
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <input type="checkbox" />
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  {transaction.voucherNo}
                </td>
                <td className="border border-gray-300 px-2 py-1">
                  {transaction.customerName}
                </td>
                <td className="border border-gray-300 px-2 py-1">
                  {transaction.manager}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  selectedRow === index ? "" : getVoucherTypeColor(transaction.voucherType)
                }`}>
                  {transaction.voucherType}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {transaction.amount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1">
                  {transaction.memo}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <input type="checkbox" checked={transaction.taxInvoiceCreated} readOnly />
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <input type="checkbox" checked={transaction.taxInvoiceSent} readOnly />
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <input type="checkbox" checked={transaction.statementCreated} readOnly />
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <input type="checkbox" checked={transaction.statementSent} readOnly />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="flex items-center justify-between border-t bg-gray-100 px-4 py-1 text-sm text-gray-600">
        <span>{selectedDate} 전표현황</span>
        <div className="flex items-center gap-4">
          <span>전체 {transactions.length} 건</span>
          <span>|</span>
          <span>조회 {filteredTransactions.length} 건</span>
          <span>|</span>
          <span className="text-blue-600">
            합계: {filteredTransactions.reduce((sum, t) => sum + t.amount, 0).toLocaleString()}원
          </span>
        </div>
      </div>
    </div>
  );
}
