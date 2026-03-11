"use client";

import React, { useState, useCallback } from "react";
import { fetchAPI } from "@/lib/api";

interface MonthlySummary {
  month: string;
  salesQty: number;
  salesAmount: number;
  salesCost: number;
  salesProfit: number;
  salesProfitRate: number;
  purchaseQty: number;
  purchaseAmount: number;
  netProfit: number;
}

interface CategorySummary {
  category: string;
  salesAmount: number;
  purchaseAmount: number;
  profit: number;
  profitRate: number;
}

export function SalesPurchaseSummary() {
  const currentYear = new Date().getFullYear().toString();
  const [year, setYear] = useState(currentYear);
  const [viewType, setViewType] = useState<"monthly" | "category">("monthly");
  const [monthlyData, setMonthlyData] = useState<MonthlySummary[]>([]);
  const [categoryData] = useState<CategorySummary[]>([]);
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const json = await fetchAPI<any>(`/v1/erp/reports/summary?year=${year}`);

      const items: MonthlySummary[] = (json.monthlyData || []).map(
        (item: MonthlySummary) => ({
          month: item.month || "",
          salesQty: item.salesQty || 0,
          salesAmount: item.salesAmount || 0,
          salesCost: item.salesCost || 0,
          salesProfit: item.salesProfit || 0,
          salesProfitRate: item.salesProfitRate || 0,
          purchaseQty: item.purchaseQty || 0,
          purchaseAmount: item.purchaseAmount || 0,
          netProfit: item.netProfit || 0,
        })
      );

      setMonthlyData(items);
      setLoaded(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : "데이터 로딩 실패";
      setError(message);
      setMonthlyData([]);
    } finally {
      setLoading(false);
    }
  }, [year]);

  // 월별 합계
  const monthlyTotals = monthlyData.reduce(
    (acc, item) => ({
      salesQty: acc.salesQty + item.salesQty,
      salesAmount: acc.salesAmount + item.salesAmount,
      salesCost: acc.salesCost + item.salesCost,
      salesProfit: acc.salesProfit + item.salesProfit,
      purchaseQty: acc.purchaseQty + item.purchaseQty,
      purchaseAmount: acc.purchaseAmount + item.purchaseAmount,
      netProfit: acc.netProfit + item.netProfit,
    }),
    {
      salesQty: 0,
      salesAmount: 0,
      salesCost: 0,
      salesProfit: 0,
      purchaseQty: 0,
      purchaseAmount: 0,
      netProfit: 0,
    }
  );

  const avgProfitRate =
    monthlyTotals.salesAmount > 0
      ? ((monthlyTotals.salesProfit / monthlyTotals.salesAmount) * 100).toFixed(
          1
        )
      : "0.0";

  // 카테고리 합계
  const categoryTotals = categoryData.reduce(
    (acc, item) => ({
      salesAmount: acc.salesAmount + item.salesAmount,
      purchaseAmount: acc.purchaseAmount + item.purchaseAmount,
      profit: acc.profit + item.profit,
    }),
    { salesAmount: 0, purchaseAmount: 0, profit: 0 }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">매출매입현황</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
          onClick={fetchData}
        >
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📊</span> 차트보기
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
          <span className="text-xs">년도:</span>
          <select
            value={year}
            onChange={(e) => setYear(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            {Array.from({ length: 5 }, (_, i) => {
              const y = new Date().getFullYear() - i;
              return (
                <option key={y} value={String(y)}>
                  {y}년
                </option>
              );
            })}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">보기:</span>
          <label className="flex items-center gap-1 text-xs">
            <input
              type="radio"
              name="viewType"
              checked={viewType === "monthly"}
              onChange={() => setViewType("monthly")}
            />
            월별
          </label>
          <label className="flex items-center gap-1 text-xs">
            <input
              type="radio"
              name="viewType"
              checked={viewType === "category"}
              onChange={() => setViewType("category")}
            />
            품목별
          </label>
        </div>
        <button
          className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200"
          onClick={fetchData}
        >
          조 회(F)
        </button>
      </div>

      {/* 에러 표시 */}
      {error && (
        <div className="bg-red-50 px-3 py-1 text-xs text-red-700">
          {error}
        </div>
      )}

      {/* 요약 현황 */}
      {loaded && (
        <div className="border-b bg-blue-50 px-3 py-2">
          <div className="text-xs font-medium mb-2">
            ▶ {year}년 매출/매입 요약
          </div>
          <div className="grid grid-cols-6 gap-2 text-xs">
            <div className="rounded border bg-white px-3 py-2">
              <div className="text-gray-500">총 매출액</div>
              <div className="text-lg font-bold text-blue-600">
                {monthlyTotals.salesAmount > 0
                  ? `${(monthlyTotals.salesAmount / 100000000).toFixed(1)}억`
                  : "0원"}
              </div>
            </div>
            <div className="rounded border bg-white px-3 py-2">
              <div className="text-gray-500">총 매입액</div>
              <div className="text-lg font-bold text-red-600">
                {monthlyTotals.purchaseAmount > 0
                  ? `${(monthlyTotals.purchaseAmount / 100000000).toFixed(1)}억`
                  : "0원"}
              </div>
            </div>
            <div className="rounded border bg-white px-3 py-2">
              <div className="text-gray-500">매출원가</div>
              <div className="text-lg font-bold text-gray-700">
                {monthlyTotals.salesCost > 0
                  ? `${(monthlyTotals.salesCost / 100000000).toFixed(1)}억`
                  : "0원"}
              </div>
            </div>
            <div className="rounded border bg-white px-3 py-2">
              <div className="text-gray-500">매출이익</div>
              <div className="text-lg font-bold text-green-600">
                {monthlyTotals.salesProfit > 0
                  ? `${(monthlyTotals.salesProfit / 100000000).toFixed(1)}억`
                  : "0원"}
              </div>
            </div>
            <div className="rounded border bg-white px-3 py-2">
              <div className="text-gray-500">이익률</div>
              <div className="text-lg font-bold text-purple-600">
                {avgProfitRate}%
              </div>
            </div>
            <div className="rounded border bg-white px-3 py-2">
              <div className="text-gray-500">순이익</div>
              <div className="text-lg font-bold text-indigo-600">
                {monthlyTotals.netProfit > 0
                  ? `${(monthlyTotals.netProfit / 100000000).toFixed(1)}억`
                  : "0원"}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center h-32 text-xs text-gray-500">
            데이터 로딩 중...
          </div>
        ) : !loaded ? (
          <div className="flex items-center justify-center h-32 text-xs text-gray-500">
            년도를 선택하고 조회 버튼을 클릭하세요.
          </div>
        ) : viewType === "monthly" ? (
          <table className="w-full border-collapse text-xs">
            <thead className="sticky top-0 bg-[#E8E4D9]">
              <tr>
                <th className="border border-gray-400 px-2 py-1 w-20">월</th>
                <th className="border border-gray-400 px-2 py-1" colSpan={5}>
                  매 출
                </th>
                <th className="border border-gray-400 px-2 py-1" colSpan={2}>
                  매 입
                </th>
                <th className="border border-gray-400 px-2 py-1 w-24">
                  순이익
                </th>
              </tr>
              <tr>
                <th className="border border-gray-400 px-2 py-1"></th>
                <th className="border border-gray-400 px-2 py-1 w-16">수량</th>
                <th className="border border-gray-400 px-2 py-1 w-24">
                  매출액
                </th>
                <th className="border border-gray-400 px-2 py-1 w-24">
                  매출원가
                </th>
                <th className="border border-gray-400 px-2 py-1 w-24">
                  매출이익
                </th>
                <th className="border border-gray-400 px-2 py-1 w-16">
                  이익률
                </th>
                <th className="border border-gray-400 px-2 py-1 w-16">수량</th>
                <th className="border border-gray-400 px-2 py-1 w-24">
                  매입액
                </th>
                <th className="border border-gray-400 px-2 py-1"></th>
              </tr>
            </thead>
            <tbody>
              {monthlyData.length === 0 ? (
                <tr>
                  <td colSpan={9} className="border border-gray-300 px-2 py-4 text-center text-gray-500">
                    조회 결과가 없습니다.
                  </td>
                </tr>
              ) : (
                <>
                  {monthlyData.map((item) => (
                    <tr
                      key={item.month}
                      className={`cursor-pointer ${
                        selectedMonth === item.month
                          ? "bg-[#316AC5] text-white"
                          : "hover:bg-gray-100"
                      }`}
                      onClick={() => setSelectedMonth(item.month)}
                    >
                      <td className="border border-gray-300 px-2 py-1 font-medium">
                        {item.month}
                      </td>
                      <td className="border border-gray-300 px-2 py-1 text-right">
                        {item.salesQty.toLocaleString()}
                      </td>
                      <td
                        className={`border border-gray-300 px-2 py-1 text-right ${
                          selectedMonth === item.month ? "" : "text-blue-600"
                        }`}
                      >
                        {item.salesAmount.toLocaleString()}
                      </td>
                      <td className="border border-gray-300 px-2 py-1 text-right">
                        {item.salesCost.toLocaleString()}
                      </td>
                      <td
                        className={`border border-gray-300 px-2 py-1 text-right ${
                          selectedMonth === item.month ? "" : "text-green-600"
                        }`}
                      >
                        {item.salesProfit.toLocaleString()}
                      </td>
                      <td
                        className={`border border-gray-300 px-2 py-1 text-right ${
                          selectedMonth === item.month
                            ? ""
                            : item.salesProfitRate >= 28
                              ? "text-green-600"
                              : ""
                        }`}
                      >
                        {item.salesProfitRate.toFixed(1)}%
                      </td>
                      <td className="border border-gray-300 px-2 py-1 text-right">
                        {item.purchaseQty.toLocaleString()}
                      </td>
                      <td
                        className={`border border-gray-300 px-2 py-1 text-right ${
                          selectedMonth === item.month ? "" : "text-red-600"
                        }`}
                      >
                        {item.purchaseAmount.toLocaleString()}
                      </td>
                      <td
                        className={`border border-gray-300 px-2 py-1 text-right font-medium ${
                          selectedMonth === item.month ? "" : "text-indigo-600"
                        }`}
                      >
                        {item.netProfit.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                  {/* 합계 행 */}
                  <tr className="bg-gray-200 font-medium">
                    <td className="border border-gray-400 px-2 py-1">합 계</td>
                    <td className="border border-gray-400 px-2 py-1 text-right">
                      {monthlyTotals.salesQty.toLocaleString()}
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                      {monthlyTotals.salesAmount.toLocaleString()}
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-right">
                      {monthlyTotals.salesCost.toLocaleString()}
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-right text-green-600">
                      {monthlyTotals.salesProfit.toLocaleString()}
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-right">
                      {avgProfitRate}%
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-right">
                      {monthlyTotals.purchaseQty.toLocaleString()}
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                      {monthlyTotals.purchaseAmount.toLocaleString()}
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-right text-indigo-600">
                      {monthlyTotals.netProfit.toLocaleString()}
                    </td>
                  </tr>
                </>
              )}
            </tbody>
          </table>
        ) : (
          <table className="w-full border-collapse text-xs">
            <thead className="sticky top-0 bg-[#E8E4D9]">
              <tr>
                <th className="border border-gray-400 px-2 py-1 w-40">
                  품목분류
                </th>
                <th className="border border-gray-400 px-2 py-1 w-28">
                  매출액
                </th>
                <th className="border border-gray-400 px-2 py-1 w-28">
                  매입액
                </th>
                <th className="border border-gray-400 px-2 py-1 w-28">이익</th>
                <th className="border border-gray-400 px-2 py-1 w-20">
                  이익률
                </th>
                <th className="border border-gray-400 px-2 py-1">비고</th>
              </tr>
            </thead>
            <tbody>
              {categoryData.length === 0 ? (
                <tr>
                  <td colSpan={6} className="border border-gray-300 px-2 py-4 text-center text-gray-500">
                    품목별 데이터가 없습니다.
                  </td>
                </tr>
              ) : (
                <>
                  {categoryData.map((item, idx) => (
                    <tr
                      key={item.category}
                      className={`cursor-pointer ${
                        idx % 2 === 0 ? "bg-white" : "bg-gray-50"
                      } hover:bg-gray-100`}
                    >
                      <td className="border border-gray-300 px-2 py-1 font-medium">
                        {item.category}
                      </td>
                      <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">
                        {item.salesAmount.toLocaleString()}
                      </td>
                      <td className="border border-gray-300 px-2 py-1 text-right text-red-600">
                        {item.purchaseAmount.toLocaleString()}
                      </td>
                      <td className="border border-gray-300 px-2 py-1 text-right text-green-600">
                        {item.profit.toLocaleString()}
                      </td>
                      <td
                        className={`border border-gray-300 px-2 py-1 text-right ${
                          item.profitRate >= 30
                            ? "text-green-600 font-medium"
                            : item.profitRate < 25
                              ? "text-orange-600"
                              : ""
                        }`}
                      >
                        {item.profitRate.toFixed(1)}%
                      </td>
                      <td className="border border-gray-300 px-2 py-1"></td>
                    </tr>
                  ))}
                  {/* 합계 행 */}
                  <tr className="bg-gray-200 font-medium">
                    <td className="border border-gray-400 px-2 py-1">합 계</td>
                    <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                      {categoryTotals.salesAmount.toLocaleString()}
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                      {categoryTotals.purchaseAmount.toLocaleString()}
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-right text-green-600">
                      {categoryTotals.profit.toLocaleString()}
                    </td>
                    <td className="border border-gray-400 px-2 py-1 text-right">
                      {categoryTotals.salesAmount > 0
                        ? (
                            (categoryTotals.profit / categoryTotals.salesAmount) *
                            100
                          ).toFixed(1)
                        : "0.0"}
                      %
                    </td>
                    <td className="border border-gray-400 px-2 py-1"></td>
                  </tr>
                </>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        {year}년 {viewType === "monthly" ? "월별" : "품목별"} 현황 | 매출:{" "}
        {monthlyTotals.salesAmount.toLocaleString()}원 | 매입:{" "}
        {monthlyTotals.purchaseAmount.toLocaleString()}원 | 이익:{" "}
        {monthlyTotals.salesProfit.toLocaleString()}원 | {loading ? "loading..." : loaded ? "loading ok" : "대기중"}
      </div>
    </div>
  );
}
