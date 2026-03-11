"use client";

import React, { useState } from "react";

interface KpiItem {
  id: string;
  category: string;
  name: string;
  currentValue: number;
  targetValue: number;
  previousValue: number;
  unit: string;
  status: "good" | "warning" | "bad";
}

interface TopCustomer {
  rank: number;
  customerCode: string;
  customerName: string;
  salesAmount: number;
  salesQty: number;
  profitAmount: number;
  profitRate: number;
}

interface TopItem {
  rank: number;
  itemCode: string;
  itemName: string;
  salesQty: number;
  salesAmount: number;
  profitAmount: number;
  profitRate: number;
}

// 이지판매재고관리 원본 데이터 복제
const KPI_DATA: KpiItem[] = [
  { id: "1", category: "매출", name: "월매출액", currentValue: 165000000, targetValue: 150000000, previousValue: 148000000, unit: "원", status: "good" },
  { id: "2", category: "매출", name: "월매출건수", currentValue: 245, targetValue: 200, previousValue: 212, unit: "건", status: "good" },
  { id: "3", category: "매출", name: "평균거래금액", currentValue: 673469, targetValue: 750000, previousValue: 698113, unit: "원", status: "warning" },
  { id: "4", category: "수익", name: "매출총이익", currentValue: 46200000, targetValue: 42000000, previousValue: 41440000, unit: "원", status: "good" },
  { id: "5", category: "수익", name: "매출이익률", currentValue: 28.0, targetValue: 28.0, previousValue: 28.0, unit: "%", status: "good" },
  { id: "6", category: "수익", name: "영업이익", currentValue: 19800000, targetValue: 18000000, previousValue: 17760000, unit: "원", status: "good" },
  { id: "7", category: "매입", name: "월매입액", currentValue: 118800000, targetValue: 110000000, previousValue: 106560000, unit: "원", status: "warning" },
  { id: "8", category: "매입", name: "매입건수", currentValue: 185, targetValue: 150, previousValue: 165, unit: "건", status: "warning" },
  { id: "9", category: "재고", name: "기말재고금액", currentValue: 125000000, targetValue: 100000000, previousValue: 115000000, unit: "원", status: "bad" },
  { id: "10", category: "재고", name: "재고회전율", currentValue: 1.32, targetValue: 1.5, previousValue: 1.28, unit: "회", status: "warning" },
  { id: "11", category: "채권", name: "매출채권잔액", currentValue: 85000000, targetValue: 70000000, previousValue: 78000000, unit: "원", status: "bad" },
  { id: "12", category: "채권", name: "채권회수율", currentValue: 92.5, targetValue: 95.0, previousValue: 93.2, unit: "%", status: "warning" },
];

const TOP_CUSTOMERS: TopCustomer[] = [
  { rank: 1, customerCode: "C003", customerName: "현대건설(주)", salesAmount: 45000000, salesQty: 68, profitAmount: 13500000, profitRate: 30.0 },
  { rank: 2, customerCode: "C001", customerName: "(주)삼성전자", salesAmount: 38500000, salesQty: 52, profitAmount: 10780000, profitRate: 28.0 },
  { rank: 3, customerCode: "C002", customerName: "(주)LG전자", salesAmount: 25800000, salesQty: 38, profitAmount: 7224000, profitRate: 28.0 },
  { rank: 4, customerCode: "C005", customerName: "SK하이닉스", salesAmount: 22000000, salesQty: 35, profitAmount: 5940000, profitRate: 27.0 },
  { rank: 5, customerCode: "C008", customerName: "포스코건설", salesAmount: 18500000, salesQty: 28, profitAmount: 5180000, profitRate: 28.0 },
];

const TOP_ITEMS: TopItem[] = [
  { rank: 1, itemCode: "P001", itemName: "SBE-104 차단기", salesQty: 98, salesAmount: 18620000, profitAmount: 5586000, profitRate: 30.0 },
  { rank: 2, itemCode: "P004", itemName: "외함 600×800×200", salesQty: 25, salesAmount: 15000000, profitAmount: 5250000, profitRate: 35.0 },
  { rank: 3, itemCode: "P007", itemName: "BUS-BAR 3T×15", salesQty: 320, salesAmount: 9600000, profitAmount: 2880000, profitRate: 30.0 },
  { rank: 4, itemCode: "P002", itemName: "ABN-204 차단기", salesQty: 42, salesAmount: 8820000, profitAmount: 2470000, profitRate: 28.0 },
  { rank: 5, itemCode: "P003", itemName: "SEE-52 누전차단기", salesQty: 185, salesAmount: 5550000, profitAmount: 1498000, profitRate: 27.0 },
];

export function ManagementDashboard() {
  const [year, setYear] = useState("2025");
  const [month, setMonth] = useState("12");
  const [kpiData] = useState<KpiItem[]>(KPI_DATA);
  const [topCustomers] = useState<TopCustomer[]>(TOP_CUSTOMERS);
  const [topItems] = useState<TopItem[]>(TOP_ITEMS);

  // 요약 지표 계산
  const salesAmount = kpiData.find((k) => k.name === "월매출액")?.currentValue || 0;
  const grossProfit = kpiData.find((k) => k.name === "매출총이익")?.currentValue || 0;
  const operatingProfit = kpiData.find((k) => k.name === "영업이익")?.currentValue || 0;
  const receivables = kpiData.find((k) => k.name === "매출채권잔액")?.currentValue || 0;
  const inventory = kpiData.find((k) => k.name === "기말재고금액")?.currentValue || 0;

  const getStatusColor = (status: string) => {
    switch (status) {
      case "good":
        return "bg-green-100 text-green-700";
      case "warning":
        return "bg-yellow-100 text-yellow-700";
      case "bad":
        return "bg-red-100 text-red-700";
      default:
        return "";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "good":
        return "▲";
      case "warning":
        return "●";
      case "bad":
        return "▼";
      default:
        return "";
    }
  };

  // KPI 카테고리별 그룹화
  const kpiByCategory = kpiData.reduce(
    (acc, item) => {
      if (!acc[item.category]) acc[item.category] = [];
      acc[item.category].push(item);
      return acc;
    },
    {} as Record<string, KpiItem[]>
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">경영현황</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🖨️</span> 인쇄
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📊</span> 차트
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 엑셀
        </button>
      </div>

      {/* 검색 조건 */}
      <div className="flex items-center gap-4 border-b bg-white px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="text-xs">기준년월:</span>
          <select
            value={year}
            onChange={(e) => setYear(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="2025">2025년</option>
            <option value="2024">2024년</option>
          </select>
          <select
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            {Array.from({ length: 12 }, (_, i) => (
              <option key={i + 1} value={String(i + 1).padStart(2, "0")}>
                {i + 1}월
              </option>
            ))}
          </select>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          조 회(F)
        </button>
      </div>

      {/* 대시보드 콘텐츠 */}
      <div className="flex-1 overflow-auto p-3">
        {/* 핵심 지표 카드 */}
        <div className="mb-4">
          <div className="text-xs font-medium mb-2">▶ 핵심 경영지표</div>
          <div className="grid grid-cols-5 gap-2">
            <div className="rounded border bg-white p-3 shadow-sm">
              <div className="text-xs text-gray-500 mb-1">월 매출액</div>
              <div className="text-xl font-bold text-blue-600">
                {(salesAmount / 100000000).toFixed(2)}억
              </div>
              <div className="text-xs text-green-600">▲ 전월대비 +11.5%</div>
            </div>
            <div className="rounded border bg-white p-3 shadow-sm">
              <div className="text-xs text-gray-500 mb-1">매출총이익</div>
              <div className="text-xl font-bold text-green-600">
                {(grossProfit / 10000000).toFixed(1)}백만
              </div>
              <div className="text-xs text-green-600">▲ 전월대비 +11.5%</div>
            </div>
            <div className="rounded border bg-white p-3 shadow-sm">
              <div className="text-xs text-gray-500 mb-1">영업이익</div>
              <div className="text-xl font-bold text-green-700">
                {(operatingProfit / 10000000).toFixed(1)}백만
              </div>
              <div className="text-xs text-green-600">▲ 전월대비 +11.5%</div>
            </div>
            <div className="rounded border bg-white p-3 shadow-sm">
              <div className="text-xs text-gray-500 mb-1">매출채권</div>
              <div className="text-xl font-bold text-orange-600">
                {(receivables / 10000000).toFixed(1)}백만
              </div>
              <div className="text-xs text-red-600">▼ 목표대비 +21.4%</div>
            </div>
            <div className="rounded border bg-white p-3 shadow-sm">
              <div className="text-xs text-gray-500 mb-1">재고자산</div>
              <div className="text-xl font-bold text-red-600">
                {(inventory / 100000000).toFixed(2)}억
              </div>
              <div className="text-xs text-red-600">▼ 목표대비 +25.0%</div>
            </div>
          </div>
        </div>

        {/* KPI 상세 */}
        <div className="mb-4">
          <div className="text-xs font-medium mb-2">▶ KPI 상세현황</div>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(kpiByCategory).map(([category, items]) => (
              <div key={category} className="rounded border bg-white">
                <div className="bg-gray-100 px-3 py-1 text-xs font-medium border-b">
                  {category}
                </div>
                <table className="w-full text-xs">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-2 py-1 text-left">지표</th>
                      <th className="px-2 py-1 text-right">실적</th>
                      <th className="px-2 py-1 text-right">목표</th>
                      <th className="px-2 py-1 text-right">달성률</th>
                      <th className="px-2 py-1 text-center w-12">상태</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((item) => {
                      const achievementRate =
                        item.targetValue !== 0
                          ? (item.currentValue / item.targetValue) * 100
                          : 0;
                      return (
                        <tr key={item.id} className="border-t">
                          <td className="px-2 py-1">{item.name}</td>
                          <td className="px-2 py-1 text-right font-medium">
                            {item.unit === "원"
                              ? item.currentValue.toLocaleString()
                              : item.unit === "%"
                                ? item.currentValue.toFixed(1)
                                : item.currentValue.toLocaleString()}
                            <span className="text-gray-500 text-xs ml-1">
                              {item.unit !== "원" ? item.unit : ""}
                            </span>
                          </td>
                          <td className="px-2 py-1 text-right text-gray-500">
                            {item.unit === "원"
                              ? item.targetValue.toLocaleString()
                              : item.unit === "%"
                                ? item.targetValue.toFixed(1)
                                : item.targetValue.toLocaleString()}
                          </td>
                          <td
                            className={`px-2 py-1 text-right ${
                              achievementRate >= 100
                                ? "text-green-600"
                                : achievementRate >= 90
                                  ? "text-yellow-600"
                                  : "text-red-600"
                            }`}
                          >
                            {achievementRate.toFixed(1)}%
                          </td>
                          <td className="px-2 py-1 text-center">
                            <span
                              className={`inline-block px-2 py-0.5 rounded text-xs ${getStatusColor(item.status)}`}
                            >
                              {getStatusIcon(item.status)}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        </div>

        {/* TOP5 현황 */}
        <div className="grid grid-cols-2 gap-3">
          {/* TOP5 거래처 */}
          <div className="rounded border bg-white">
            <div className="bg-blue-50 px-3 py-1 text-xs font-medium border-b">
              ▶ TOP 5 거래처
            </div>
            <table className="w-full text-xs">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-2 py-1 w-8">순위</th>
                  <th className="px-2 py-1 text-left">거래처명</th>
                  <th className="px-2 py-1 text-right">매출액</th>
                  <th className="px-2 py-1 text-right">이익</th>
                  <th className="px-2 py-1 text-right">이익률</th>
                </tr>
              </thead>
              <tbody>
                {topCustomers.map((customer) => (
                  <tr key={customer.rank} className="border-t hover:bg-gray-50">
                    <td className="px-2 py-1 text-center font-bold text-blue-600">
                      {customer.rank}
                    </td>
                    <td className="px-2 py-1">{customer.customerName}</td>
                    <td className="px-2 py-1 text-right text-blue-600">
                      {customer.salesAmount.toLocaleString()}
                    </td>
                    <td className="px-2 py-1 text-right text-green-600">
                      {customer.profitAmount.toLocaleString()}
                    </td>
                    <td className="px-2 py-1 text-right">
                      {customer.profitRate.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* TOP5 품목 */}
          <div className="rounded border bg-white">
            <div className="bg-green-50 px-3 py-1 text-xs font-medium border-b">
              ▶ TOP 5 품목
            </div>
            <table className="w-full text-xs">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-2 py-1 w-8">순위</th>
                  <th className="px-2 py-1 text-left">품목명</th>
                  <th className="px-2 py-1 text-right">매출액</th>
                  <th className="px-2 py-1 text-right">이익</th>
                  <th className="px-2 py-1 text-right">이익률</th>
                </tr>
              </thead>
              <tbody>
                {topItems.map((item) => (
                  <tr key={item.rank} className="border-t hover:bg-gray-50">
                    <td className="px-2 py-1 text-center font-bold text-green-600">
                      {item.rank}
                    </td>
                    <td className="px-2 py-1">{item.itemName}</td>
                    <td className="px-2 py-1 text-right text-blue-600">
                      {item.salesAmount.toLocaleString()}
                    </td>
                    <td className="px-2 py-1 text-right text-green-600">
                      {item.profitAmount.toLocaleString()}
                    </td>
                    <td className="px-2 py-1 text-right">
                      {item.profitRate.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        {year}년 {month}월 경영현황 | 매출: {salesAmount.toLocaleString()}원 | 영업이익:{" "}
        {operatingProfit.toLocaleString()}원 | loading ok
      </div>
    </div>
  );
}
