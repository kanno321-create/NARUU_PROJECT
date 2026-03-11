"use client";

import React, { useState } from "react";

interface BankTransactionItem {
  id: string;
  date: string;
  accountNo: string;
  bankName: string;
  accountName: string;
  transType: string;
  description: string;
  depositAmount: number;
  withdrawAmount: number;
  balance: number;
  memo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: BankTransactionItem[] = [
  {
    id: "1",
    date: "2025-12-05",
    accountNo: "123-456-789012",
    bankName: "기업은행",
    accountName: "법인운영계좌",
    transType: "입금",
    description: "테스트사업장 수금",
    depositAmount: 180000,
    withdrawAmount: 0,
    balance: 5180000,
    memo: "현금수금",
  },
  {
    id: "2",
    date: "2025-12-05",
    accountNo: "123-456-789012",
    bankName: "기업은행",
    accountName: "법인운영계좌",
    transType: "출금",
    description: "공급업체A 지급",
    depositAmount: 0,
    withdrawAmount: 300000,
    balance: 4880000,
    memo: "계좌이체",
  },
  {
    id: "3",
    date: "2025-12-04",
    accountNo: "987-654-321098",
    bankName: "국민은행",
    accountName: "급여계좌",
    transType: "출금",
    description: "12월 급여지급",
    depositAmount: 0,
    withdrawAmount: 3500000,
    balance: 1500000,
    memo: "급여",
  },
  {
    id: "4",
    date: "2025-12-04",
    accountNo: "123-456-789012",
    bankName: "기업은행",
    accountName: "법인운영계좌",
    transType: "입금",
    description: "제고사업장 수금",
    depositAmount: 150000,
    withdrawAmount: 0,
    balance: 5000000,
    memo: "계좌이체",
  },
  {
    id: "5",
    date: "2025-12-03",
    accountNo: "123-456-789012",
    bankName: "기업은행",
    accountName: "법인운영계좌",
    transType: "출금",
    description: "사무용품 구매",
    depositAmount: 0,
    withdrawAmount: 50000,
    balance: 4850000,
    memo: "",
  },
];

export function BankTransactionStatus() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [bankFilter, setBankFilter] = useState("전체");
  const [transTypeFilter, setTransTypeFilter] = useState("전체");
  const [data] = useState<BankTransactionItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const banks = ["전체", ...new Set(data.map((d) => d.bankName))];

  const filteredData = data.filter(
    (item) =>
      (bankFilter === "전체" || item.bankName === bankFilter) &&
      (transTypeFilter === "전체" || item.transType === transTypeFilter)
  );

  // 통장별 집계
  const accountSummary = filteredData.reduce((acc, item) => {
    const key = item.accountNo;
    if (!acc[key]) {
      acc[key] = {
        accountNo: item.accountNo,
        bankName: item.bankName,
        accountName: item.accountName,
        totalDeposit: 0,
        totalWithdraw: 0,
        lastBalance: 0,
      };
    }
    acc[key].totalDeposit += item.depositAmount;
    acc[key].totalWithdraw += item.withdrawAmount;
    acc[key].lastBalance = item.balance;
    return acc;
  }, {} as Record<string, { accountNo: string; bankName: string; accountName: string; totalDeposit: number; totalWithdraw: number; lastBalance: number }>);

  // 누계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      depositAmount: acc.depositAmount + item.depositAmount,
      withdrawAmount: acc.withdrawAmount + item.withdrawAmount,
    }),
    { depositAmount: 0, withdrawAmount: 0 }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">통장별입출금현황</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📊</span> 보고서출력
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 엑셀변환
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🖨️</span> 인쇄
        </button>
      </div>

      {/* 검색 조건 */}
      <div className="flex items-center gap-4 border-b bg-white px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="text-xs">기간선택:</span>
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
          <span className="text-xs">은행:</span>
          <select
            value={bankFilter}
            onChange={(e) => setBankFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            {banks.map((bank) => (
              <option key={bank} value={bank}>{bank}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">구분:</span>
          <select
            value={transTypeFilter}
            onChange={(e) => setTransTypeFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="입금">입금</option>
            <option value="출금">출금</option>
          </select>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색(F)
        </button>
      </div>

      {/* 통장별 요약 */}
      <div className="border-b bg-blue-50 px-3 py-2">
        <div className="text-xs font-medium mb-1">▶ 통장별 요약</div>
        <div className="flex gap-4 text-xs">
          {Object.values(accountSummary).map((acc) => (
            <div key={acc.accountNo} className="bg-white px-3 py-1 rounded border">
              <div className="font-medium">{acc.bankName} - {acc.accountName}</div>
              <div className="text-blue-600">입금: {acc.totalDeposit.toLocaleString()}원</div>
              <div className="text-red-600">출금: {acc.totalWithdraw.toLocaleString()}원</div>
              <div className="font-bold">잔액: {acc.lastBalance.toLocaleString()}원</div>
            </div>
          ))}
        </div>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-24">일자</th>
              <th className="border border-gray-400 px-2 py-1 w-28">계좌번호</th>
              <th className="border border-gray-400 px-2 py-1 w-20">은행</th>
              <th className="border border-gray-400 px-2 py-1 w-24">계좌명</th>
              <th className="border border-gray-400 px-2 py-1 w-16">구분</th>
              <th className="border border-gray-400 px-2 py-1 w-32">적요</th>
              <th className="border border-gray-400 px-2 py-1 w-28">입금액</th>
              <th className="border border-gray-400 px-2 py-1 w-28">출금액</th>
              <th className="border border-gray-400 px-2 py-1 w-28">잔액</th>
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
                    : item.transType === "출금"
                    ? "bg-red-50 hover:bg-red-100"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1">{item.date}</td>
                <td className="border border-gray-300 px-2 py-1">{item.accountNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.bankName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.accountName}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center font-medium ${
                  item.transType === "입금" ? "text-blue-600" : "text-red-600"
                }`}>
                  {item.transType}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.description}</td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">
                  {item.depositAmount > 0 ? item.depositAmount.toLocaleString() : ""}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-red-600">
                  {item.withdrawAmount > 0 ? item.withdrawAmount.toLocaleString() : ""}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium">
                  {item.balance.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.memo}</td>
              </tr>
            ))}
            {/* 누계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={6}>
                (누계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.depositAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.withdrawAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {(totals.depositAmount - totals.withdrawAmount).toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
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
