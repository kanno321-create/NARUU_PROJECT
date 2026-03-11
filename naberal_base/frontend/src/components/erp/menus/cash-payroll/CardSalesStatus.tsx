"use client";

import React, { useState } from "react";

interface CardSalesItem {
  id: string;
  salesDate: string;
  cardCompany: string;
  cardNo: string;
  approvalNo: string;
  salesAmount: number;
  feeRate: number;
  feeAmount: number;
  netAmount: number;
  depositDate: string;
  depositStatus: string;
  customerName: string;
  memo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: CardSalesItem[] = [
  {
    id: "1",
    salesDate: "2025-12-05",
    cardCompany: "삼성카드",
    cardNo: "****-****-****-1234",
    approvalNo: "12345678",
    salesAmount: 500000,
    feeRate: 2.2,
    feeAmount: 11000,
    netAmount: 489000,
    depositDate: "2025-12-08",
    depositStatus: "입금예정",
    customerName: "테스트고객",
    memo: "",
  },
  {
    id: "2",
    salesDate: "2025-12-05",
    cardCompany: "신한카드",
    cardNo: "****-****-****-5678",
    approvalNo: "87654321",
    salesAmount: 350000,
    feeRate: 2.0,
    feeAmount: 7000,
    netAmount: 343000,
    depositDate: "2025-12-08",
    depositStatus: "입금예정",
    customerName: "제고고객",
    memo: "",
  },
  {
    id: "3",
    salesDate: "2025-12-04",
    cardCompany: "현대카드",
    cardNo: "****-****-****-9012",
    approvalNo: "11223344",
    salesAmount: 280000,
    feeRate: 2.3,
    feeAmount: 6440,
    netAmount: 273560,
    depositDate: "2025-12-07",
    depositStatus: "입금완료",
    customerName: "신규고객",
    memo: "",
  },
  {
    id: "4",
    salesDate: "2025-12-03",
    cardCompany: "삼성카드",
    cardNo: "****-****-****-3456",
    approvalNo: "55667788",
    salesAmount: 420000,
    feeRate: 2.2,
    feeAmount: 9240,
    netAmount: 410760,
    depositDate: "2025-12-06",
    depositStatus: "입금완료",
    customerName: "VIP고객",
    memo: "할부3개월",
  },
  {
    id: "5",
    salesDate: "2025-12-02",
    cardCompany: "BC카드",
    cardNo: "****-****-****-7890",
    approvalNo: "99001122",
    salesAmount: 150000,
    feeRate: 2.5,
    feeAmount: 3750,
    netAmount: 146250,
    depositDate: "2025-12-05",
    depositStatus: "입금완료",
    customerName: "일반고객",
    memo: "",
  },
];

export function CardSalesStatus() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [cardCompanyFilter, setCardCompanyFilter] = useState("전체");
  const [statusFilter, setStatusFilter] = useState("전체");
  const [data] = useState<CardSalesItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const cardCompanies = ["전체", ...new Set(data.map((d) => d.cardCompany))];

  const filteredData = data.filter(
    (item) =>
      (cardCompanyFilter === "전체" || item.cardCompany === cardCompanyFilter) &&
      (statusFilter === "전체" || item.depositStatus === statusFilter)
  );

  // 카드사별 집계
  const companySummary = filteredData.reduce((acc, item) => {
    if (!acc[item.cardCompany]) {
      acc[item.cardCompany] = {
        count: 0,
        salesAmount: 0,
        feeAmount: 0,
        netAmount: 0,
      };
    }
    acc[item.cardCompany].count += 1;
    acc[item.cardCompany].salesAmount += item.salesAmount;
    acc[item.cardCompany].feeAmount += item.feeAmount;
    acc[item.cardCompany].netAmount += item.netAmount;
    return acc;
  }, {} as Record<string, { count: number; salesAmount: number; feeAmount: number; netAmount: number }>);

  // 총계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      salesAmount: acc.salesAmount + item.salesAmount,
      feeAmount: acc.feeAmount + item.feeAmount,
      netAmount: acc.netAmount + item.netAmount,
    }),
    { salesAmount: 0, feeAmount: 0, netAmount: 0 }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">카드매출현황</span>
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
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>💳</span> 입금처리
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
          <span className="text-xs">카드사:</span>
          <select
            value={cardCompanyFilter}
            onChange={(e) => setCardCompanyFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            {cardCompanies.map((company) => (
              <option key={company} value={company}>{company}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">입금상태:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="입금예정">입금예정</option>
            <option value="입금완료">입금완료</option>
          </select>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색(F)
        </button>
      </div>

      {/* 카드사별 요약 */}
      <div className="border-b bg-purple-50 px-3 py-2">
        <div className="text-xs font-medium mb-1">▶ 카드사별 집계</div>
        <div className="flex gap-3 text-xs">
          {Object.entries(companySummary).map(([company, summary]) => (
            <div key={company} className="bg-white px-3 py-1 rounded border">
              <div className="font-medium text-purple-700">{company}</div>
              <div>건수: {summary.count}건</div>
              <div className="text-blue-600">매출: {summary.salesAmount.toLocaleString()}</div>
              <div className="text-red-600">수수료: {summary.feeAmount.toLocaleString()}</div>
              <div className="font-bold">실입금: {summary.netAmount.toLocaleString()}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-24">매출일</th>
              <th className="border border-gray-400 px-2 py-1 w-20">카드사</th>
              <th className="border border-gray-400 px-2 py-1 w-36">카드번호</th>
              <th className="border border-gray-400 px-2 py-1 w-24">승인번호</th>
              <th className="border border-gray-400 px-2 py-1 w-28">매출금액</th>
              <th className="border border-gray-400 px-2 py-1 w-16">수수료율</th>
              <th className="border border-gray-400 px-2 py-1 w-24">수수료</th>
              <th className="border border-gray-400 px-2 py-1 w-28">실입금액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">입금예정일</th>
              <th className="border border-gray-400 px-2 py-1 w-20">입금상태</th>
              <th className="border border-gray-400 px-2 py-1 w-20">고객명</th>
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
                    : item.depositStatus === "입금완료"
                    ? "bg-green-50 hover:bg-green-100"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1">{item.salesDate}</td>
                <td className="border border-gray-300 px-2 py-1">{item.cardCompany}</td>
                <td className="border border-gray-300 px-2 py-1">{item.cardNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.approvalNo}</td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600 font-medium">
                  {item.salesAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  {item.feeRate}%
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-red-600">
                  {item.feeAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium">
                  {item.netAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.depositDate}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  item.depositStatus === "입금완료" ? "text-green-600" : "text-orange-600"
                }`}>
                  {item.depositStatus}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.customerName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.memo}</td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={4}>
                (합계: {filteredData.length}건)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.salesAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.feeAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.netAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={4}></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 하단 요약 */}
      <div className="flex items-center gap-6 border-t bg-yellow-50 px-3 py-2 text-xs">
        <span className="font-medium">요약:</span>
        <span className="text-blue-600">
          총 매출: {totals.salesAmount.toLocaleString()}원
        </span>
        <span className="text-red-600">
          총 수수료: {totals.feeAmount.toLocaleString()}원 ({((totals.feeAmount / totals.salesAmount) * 100).toFixed(2)}%)
        </span>
        <span className="text-green-600 font-bold">
          실입금액: {totals.netAmount.toLocaleString()}원
        </span>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredData.length}건 | loading ok
      </div>
    </div>
  );
}
