"use client";

import React, { useState } from "react";

interface PLItem {
  id: string;
  level: number;
  code: string;
  name: string;
  currentAmount: number;
  previousAmount: number;
  budgetAmount: number;
  note: string;
  isTotal?: boolean;
  isHeader?: boolean;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: PLItem[] = [
  // 매출
  { id: "1", level: 0, code: "I", name: "매출액", currentAmount: 1833500000, previousAmount: 1650000000, budgetAmount: 1800000000, note: "", isHeader: true },
  { id: "2", level: 1, code: "I-1", name: "상품매출", currentAmount: 1680000000, previousAmount: 1520000000, budgetAmount: 1650000000, note: "" },
  { id: "3", level: 1, code: "I-2", name: "제품매출", currentAmount: 125000000, previousAmount: 105000000, budgetAmount: 120000000, note: "" },
  { id: "4", level: 1, code: "I-3", name: "용역매출", currentAmount: 28500000, previousAmount: 25000000, budgetAmount: 30000000, note: "" },

  // 매출원가
  { id: "5", level: 0, code: "II", name: "매출원가", currentAmount: 1330500000, previousAmount: 1215000000, budgetAmount: 1300000000, note: "", isHeader: true },
  { id: "6", level: 1, code: "II-1", name: "기초상품재고액", currentAmount: 125000000, previousAmount: 118000000, budgetAmount: 120000000, note: "" },
  { id: "7", level: 1, code: "II-2", name: "당기상품매입액", currentAmount: 1313000000, previousAmount: 1185000000, budgetAmount: 1280000000, note: "" },
  { id: "8", level: 1, code: "II-3", name: "기말상품재고액", currentAmount: -107500000, previousAmount: -88000000, budgetAmount: -100000000, note: "" },

  // 매출총이익
  { id: "9", level: 0, code: "III", name: "매출총이익", currentAmount: 503000000, previousAmount: 435000000, budgetAmount: 500000000, note: "", isTotal: true },

  // 판매비와관리비
  { id: "10", level: 0, code: "IV", name: "판매비와관리비", currentAmount: 285000000, previousAmount: 268000000, budgetAmount: 280000000, note: "", isHeader: true },
  { id: "11", level: 1, code: "IV-1", name: "급여", currentAmount: 145000000, previousAmount: 138000000, budgetAmount: 145000000, note: "" },
  { id: "12", level: 1, code: "IV-2", name: "퇴직급여", currentAmount: 12000000, previousAmount: 11500000, budgetAmount: 12000000, note: "" },
  { id: "13", level: 1, code: "IV-3", name: "복리후생비", currentAmount: 18000000, previousAmount: 16500000, budgetAmount: 18000000, note: "" },
  { id: "14", level: 1, code: "IV-4", name: "임차료", currentAmount: 36000000, previousAmount: 36000000, budgetAmount: 36000000, note: "" },
  { id: "15", level: 1, code: "IV-5", name: "감가상각비", currentAmount: 15000000, previousAmount: 14000000, budgetAmount: 15000000, note: "" },
  { id: "16", level: 1, code: "IV-6", name: "세금과공과", currentAmount: 8500000, previousAmount: 7800000, budgetAmount: 8000000, note: "" },
  { id: "17", level: 1, code: "IV-7", name: "통신비", currentAmount: 5500000, previousAmount: 5200000, budgetAmount: 5500000, note: "" },
  { id: "18", level: 1, code: "IV-8", name: "수도광열비", currentAmount: 12000000, previousAmount: 11000000, budgetAmount: 12000000, note: "" },
  { id: "19", level: 1, code: "IV-9", name: "운반비", currentAmount: 18000000, previousAmount: 16000000, budgetAmount: 17000000, note: "" },
  { id: "20", level: 1, code: "IV-10", name: "소모품비", currentAmount: 8000000, previousAmount: 7500000, budgetAmount: 8000000, note: "" },
  { id: "21", level: 1, code: "IV-11", name: "기타경비", currentAmount: 7000000, previousAmount: 4500000, budgetAmount: 3500000, note: "" },

  // 영업이익
  { id: "22", level: 0, code: "V", name: "영업이익", currentAmount: 218000000, previousAmount: 167000000, budgetAmount: 220000000, note: "", isTotal: true },

  // 영업외수익
  { id: "23", level: 0, code: "VI", name: "영업외수익", currentAmount: 12500000, previousAmount: 8500000, budgetAmount: 10000000, note: "", isHeader: true },
  { id: "24", level: 1, code: "VI-1", name: "이자수익", currentAmount: 5500000, previousAmount: 4200000, budgetAmount: 5000000, note: "" },
  { id: "25", level: 1, code: "VI-2", name: "잡이익", currentAmount: 7000000, previousAmount: 4300000, budgetAmount: 5000000, note: "" },

  // 영업외비용
  { id: "26", level: 0, code: "VII", name: "영업외비용", currentAmount: 25000000, previousAmount: 22000000, budgetAmount: 24000000, note: "", isHeader: true },
  { id: "27", level: 1, code: "VII-1", name: "이자비용", currentAmount: 18500000, previousAmount: 16500000, budgetAmount: 18000000, note: "" },
  { id: "28", level: 1, code: "VII-2", name: "기타손실", currentAmount: 6500000, previousAmount: 5500000, budgetAmount: 6000000, note: "" },

  // 법인세차감전순이익
  { id: "29", level: 0, code: "VIII", name: "법인세차감전순이익", currentAmount: 205500000, previousAmount: 153500000, budgetAmount: 206000000, note: "", isTotal: true },

  // 법인세비용
  { id: "30", level: 0, code: "IX", name: "법인세비용", currentAmount: 45210000, previousAmount: 33770000, budgetAmount: 45320000, note: "", isHeader: true },

  // 당기순이익
  { id: "31", level: 0, code: "X", name: "당기순이익", currentAmount: 160290000, previousAmount: 119730000, budgetAmount: 160680000, note: "", isTotal: true },
];

export function ProfitLossStatement() {
  const [year, setYear] = useState("2025");
  const [period, setPeriod] = useState("연간");
  const [data] = useState<PLItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // 계산된 지표
  const salesAmount = data.find((d) => d.code === "I")?.currentAmount || 0;
  const grossProfit = data.find((d) => d.code === "III")?.currentAmount || 0;
  const operatingProfit = data.find((d) => d.code === "V")?.currentAmount || 0;
  const netProfit = data.find((d) => d.code === "X")?.currentAmount || 0;

  const grossProfitRate = salesAmount > 0 ? ((grossProfit / salesAmount) * 100).toFixed(1) : "0.0";
  const operatingProfitRate = salesAmount > 0 ? ((operatingProfit / salesAmount) * 100).toFixed(1) : "0.0";
  const netProfitRate = salesAmount > 0 ? ((netProfit / salesAmount) * 100).toFixed(1) : "0.0";

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">손익계산서</span>
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
          <span className="text-xs">년도:</span>
          <select
            value={year}
            onChange={(e) => setYear(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="2025">2025년</option>
            <option value="2024">2024년</option>
            <option value="2023">2023년</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">기간:</span>
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="연간">연간</option>
            <option value="1분기">1분기</option>
            <option value="2분기">2분기</option>
            <option value="3분기">3분기</option>
            <option value="4분기">4분기</option>
          </select>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          조 회(F)
        </button>
      </div>

      {/* 요약 현황 */}
      <div className="border-b bg-yellow-50 px-3 py-2">
        <div className="text-xs font-medium mb-2">▶ 손익 요약</div>
        <div className="grid grid-cols-6 gap-2 text-xs">
          <div className="rounded border bg-white px-3 py-2">
            <div className="text-gray-500">매출액</div>
            <div className="text-lg font-bold text-blue-600">
              {(salesAmount / 100000000).toFixed(1)}억
            </div>
          </div>
          <div className="rounded border bg-white px-3 py-2">
            <div className="text-gray-500">매출총이익</div>
            <div className="text-lg font-bold text-green-600">
              {(grossProfit / 100000000).toFixed(1)}억
            </div>
            <div className="text-xs text-gray-500">{grossProfitRate}%</div>
          </div>
          <div className="rounded border bg-white px-3 py-2">
            <div className="text-gray-500">영업이익</div>
            <div className="text-lg font-bold text-green-700">
              {(operatingProfit / 100000000).toFixed(1)}억
            </div>
            <div className="text-xs text-gray-500">{operatingProfitRate}%</div>
          </div>
          <div className="rounded border bg-white px-3 py-2">
            <div className="text-gray-500">당기순이익</div>
            <div className="text-lg font-bold text-indigo-600">
              {(netProfit / 100000000).toFixed(1)}억
            </div>
            <div className="text-xs text-gray-500">{netProfitRate}%</div>
          </div>
          <div className="rounded border bg-white px-3 py-2">
            <div className="text-gray-500">전년대비</div>
            <div className="text-lg font-bold text-red-600">
              +{(((netProfit - 119730000) / 119730000) * 100).toFixed(1)}%
            </div>
          </div>
          <div className="rounded border bg-white px-3 py-2">
            <div className="text-gray-500">예산대비</div>
            <div className="text-lg font-bold text-purple-600">
              {(((netProfit - 160680000) / 160680000) * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-16">계정코드</th>
              <th className="border border-gray-400 px-2 py-1">계정과목</th>
              <th className="border border-gray-400 px-2 py-1 w-28">당기금액</th>
              <th className="border border-gray-400 px-2 py-1 w-28">전기금액</th>
              <th className="border border-gray-400 px-2 py-1 w-28">예산금액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">예산대비</th>
              <th className="border border-gray-400 px-2 py-1 w-20">전년대비</th>
              <th className="border border-gray-400 px-2 py-1 w-24">비고</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item) => {
              const budgetVariance = item.budgetAmount !== 0
                ? ((item.currentAmount - item.budgetAmount) / Math.abs(item.budgetAmount)) * 100
                : 0;
              const previousVariance = item.previousAmount !== 0
                ? ((item.currentAmount - item.previousAmount) / Math.abs(item.previousAmount)) * 100
                : 0;

              return (
                <tr
                  key={item.id}
                  className={`cursor-pointer ${
                    selectedId === item.id
                      ? "bg-[#316AC5] text-white"
                      : item.isTotal
                        ? "bg-blue-100 font-bold"
                        : item.isHeader
                          ? "bg-gray-100 font-medium"
                          : "hover:bg-gray-50"
                  }`}
                  onClick={() => setSelectedId(item.id)}
                >
                  <td className="border border-gray-300 px-2 py-1">{item.code}</td>
                  <td
                    className="border border-gray-300 px-2 py-1"
                    style={{ paddingLeft: `${item.level * 16 + 8}px` }}
                  >
                    {item.name}
                  </td>
                  <td
                    className={`border border-gray-300 px-2 py-1 text-right ${
                      selectedId === item.id
                        ? ""
                        : item.currentAmount < 0
                          ? "text-red-600"
                          : item.isTotal
                            ? "text-blue-700"
                            : ""
                    }`}
                  >
                    {item.currentAmount.toLocaleString()}
                  </td>
                  <td className="border border-gray-300 px-2 py-1 text-right text-gray-600">
                    {item.previousAmount.toLocaleString()}
                  </td>
                  <td className="border border-gray-300 px-2 py-1 text-right text-gray-600">
                    {item.budgetAmount.toLocaleString()}
                  </td>
                  <td
                    className={`border border-gray-300 px-2 py-1 text-right ${
                      selectedId === item.id
                        ? ""
                        : budgetVariance > 0
                          ? "text-green-600"
                          : budgetVariance < 0
                            ? "text-red-600"
                            : ""
                    }`}
                  >
                    {budgetVariance.toFixed(1)}%
                  </td>
                  <td
                    className={`border border-gray-300 px-2 py-1 text-right ${
                      selectedId === item.id
                        ? ""
                        : previousVariance > 0
                          ? "text-green-600"
                          : previousVariance < 0
                            ? "text-red-600"
                            : ""
                    }`}
                  >
                    {previousVariance > 0 ? "+" : ""}{previousVariance.toFixed(1)}%
                  </td>
                  <td className="border border-gray-300 px-2 py-1">{item.note}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        {year}년 {period} 손익계산서 | 매출액: {salesAmount.toLocaleString()}원 | 영업이익:{" "}
        {operatingProfit.toLocaleString()}원 | 당기순이익: {netProfit.toLocaleString()}원 | loading ok
      </div>
    </div>
  );
}
