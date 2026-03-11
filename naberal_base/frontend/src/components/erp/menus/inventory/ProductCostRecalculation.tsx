"use client";

import React, { useState } from "react";

interface CostRecalcItem {
  id: string;
  itemCode: string;
  itemName: string;
  specification: string;
  unit: string;
  warehouse: string;
  currentQty: number;
  currentCost: number;
  currentTotal: number;
  avgPurchaseCost: number;
  lastPurchaseCost: number;
  newCost: number;
  newTotal: number;
  costDiff: number;
  costDiffRate: number;
  lastCalcDate: string;
  status: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: CostRecalcItem[] = [
  {
    id: "1",
    itemCode: "P001",
    itemName: "SBE-104 차단기",
    specification: "4P 100AF 75AT",
    unit: "EA",
    warehouse: "본사창고",
    currentQty: 120,
    currentCost: 45000,
    currentTotal: 5400000,
    avgPurchaseCost: 44500,
    lastPurchaseCost: 45000,
    newCost: 44500,
    newTotal: 5340000,
    costDiff: -60000,
    costDiffRate: -1.11,
    lastCalcDate: "2025-12-01",
    status: "재계산가능",
  },
  {
    id: "2",
    itemCode: "P002",
    itemName: "SBE-204 차단기",
    specification: "4P 200AF 150AT",
    unit: "EA",
    warehouse: "본사창고",
    currentQty: 43,
    currentCost: 85000,
    currentTotal: 3655000,
    avgPurchaseCost: 84000,
    lastPurchaseCost: 85000,
    newCost: 84000,
    newTotal: 3612000,
    costDiff: -43000,
    costDiffRate: -1.18,
    lastCalcDate: "2025-12-01",
    status: "재계산가능",
  },
  {
    id: "3",
    itemCode: "P003",
    itemName: "외함 600×800×200",
    specification: "STEEL 1.6T",
    unit: "면",
    warehouse: "본사창고",
    currentQty: 15,
    currentCost: 120000,
    currentTotal: 1800000,
    avgPurchaseCost: 118000,
    lastPurchaseCost: 120000,
    newCost: 118000,
    newTotal: 1770000,
    costDiff: -30000,
    costDiffRate: -1.67,
    lastCalcDate: "2025-12-01",
    status: "재계산가능",
  },
  {
    id: "4",
    itemCode: "P004",
    itemName: "BUS-BAR 3T×15",
    specification: "COPPER",
    unit: "KG",
    warehouse: "본사창고",
    currentQty: 150,
    currentCost: 20000,
    currentTotal: 3000000,
    avgPurchaseCost: 20500,
    lastPurchaseCost: 21000,
    newCost: 20500,
    newTotal: 3075000,
    costDiff: 75000,
    costDiffRate: 2.5,
    lastCalcDate: "2025-12-01",
    status: "재계산가능",
  },
  {
    id: "5",
    itemCode: "P005",
    itemName: "MC-22 마그네트",
    specification: "22A",
    unit: "EA",
    warehouse: "본사창고",
    currentQty: 5,
    currentCost: 35000,
    currentTotal: 175000,
    avgPurchaseCost: 35000,
    lastPurchaseCost: 35000,
    newCost: 35000,
    newTotal: 175000,
    costDiff: 0,
    costDiffRate: 0,
    lastCalcDate: "2025-12-05",
    status: "최신",
  },
  {
    id: "6",
    itemCode: "P006",
    itemName: "TERMINAL BLOCK",
    specification: "600V",
    unit: "EA",
    warehouse: "제2창고",
    currentQty: 410,
    currentCost: 4000,
    currentTotal: 1640000,
    avgPurchaseCost: 3900,
    lastPurchaseCost: 4000,
    newCost: 3900,
    newTotal: 1599000,
    costDiff: -41000,
    costDiffRate: -2.5,
    lastCalcDate: "2025-12-01",
    status: "재계산가능",
  },
  {
    id: "7",
    itemCode: "P007",
    itemName: "E.T (접지단자)",
    specification: "100AF용",
    unit: "EA",
    warehouse: "본사창고",
    currentQty: 70,
    currentCost: 4500,
    currentTotal: 315000,
    avgPurchaseCost: 4500,
    lastPurchaseCost: 4500,
    newCost: 4500,
    newTotal: 315000,
    costDiff: 0,
    costDiffRate: 0,
    lastCalcDate: "2025-12-05",
    status: "최신",
  },
  {
    id: "8",
    itemCode: "P008",
    itemName: "P-COVER 아크릴",
    specification: "600×800",
    unit: "EA",
    warehouse: "본사창고",
    currentQty: 15,
    currentCost: 17000,
    currentTotal: 255000,
    avgPurchaseCost: 16500,
    lastPurchaseCost: 17000,
    newCost: 16500,
    newTotal: 247500,
    costDiff: -7500,
    costDiffRate: -2.94,
    lastCalcDate: "2025-12-01",
    status: "재계산가능",
  },
];

export function ProductCostRecalculation() {
  const [baseDate, setBaseDate] = useState("2025-12-05");
  const [calcMethod, setCalcMethod] = useState("이동평균법");
  const [warehouseFilter, setWarehouseFilter] = useState("전체");
  const [statusFilter, setStatusFilter] = useState("전체");
  const [data, setData] = useState<CostRecalcItem[]>(ORIGINAL_DATA);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [showConfirm, setShowConfirm] = useState(false);

  const filteredData = data.filter(
    (item) =>
      (warehouseFilter === "전체" || item.warehouse === warehouseFilter) &&
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
      currentTotal: acc.currentTotal + item.currentTotal,
      newTotal: acc.newTotal + item.newTotal,
      costDiff: acc.costDiff + item.costDiff,
    }),
    { currentTotal: 0, newTotal: 0, costDiff: 0 }
  );

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(filteredData.filter(d => d.status === "재계산가능").map(d => d.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectItem = (id: string, checked: boolean) => {
    if (checked) {
      setSelectedIds([...selectedIds, id]);
    } else {
      setSelectedIds(selectedIds.filter(i => i !== id));
    }
  };

  const handleRecalculate = () => {
    setShowConfirm(true);
  };

  const confirmRecalculate = () => {
    // 선택된 항목들의 원가 재계산 적용
    const updatedData = data.map(item => {
      if (selectedIds.includes(item.id)) {
        return {
          ...item,
          currentCost: item.newCost,
          currentTotal: item.newTotal,
          costDiff: 0,
          costDiffRate: 0,
          lastCalcDate: baseDate,
          status: "최신",
        };
      }
      return item;
    });
    setData(updatedData);
    setSelectedIds([]);
    setShowConfirm(false);
  };

  const getStatusColor = (status: string, isSelected: boolean) => {
    if (isSelected) return "";
    return status === "최신" ? "text-green-600" : "text-orange-600";
  };

  const getDiffColor = (diff: number, isSelected: boolean) => {
    if (isSelected) return "";
    if (diff > 0) return "text-red-600";
    if (diff < 0) return "text-blue-600";
    return "";
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">상품원가재계산</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button
          onClick={handleRecalculate}
          disabled={selectedIds.length === 0}
          className={`flex items-center gap-1 rounded border px-2 py-0.5 text-xs ${
            selectedIds.length > 0
              ? "border-blue-400 bg-blue-100 hover:bg-blue-200"
              : "border-gray-300 bg-gray-100 text-gray-400 cursor-not-allowed"
          }`}
        >
          <span>📊</span> 선택항목 재계산({selectedIds.length})
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-orange-100 px-2 py-0.5 text-xs hover:bg-orange-200">
          <span>⚡</span> 전체재계산
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 재계산내역
        </button>
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
          <span className="text-xs">기준일:</span>
          <input
            type="date"
            value={baseDate}
            onChange={(e) => setBaseDate(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">계산방법:</span>
          <select
            value={calcMethod}
            onChange={(e) => setCalcMethod(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="이동평균법">이동평균법</option>
            <option value="선입선출법">선입선출법</option>
            <option value="최종매입가법">최종매입가법</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">창고:</span>
          <select
            value={warehouseFilter}
            onChange={(e) => setWarehouseFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="본사창고">본사창고</option>
            <option value="제2창고">제2창고</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">상태:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="재계산가능">재계산가능</option>
            <option value="최신">최신</option>
          </select>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          조 회(F)
        </button>
      </div>

      {/* 요약 정보 */}
      <div className="flex items-center gap-6 border-b bg-yellow-50 px-3 py-2 text-xs">
        <span className="font-medium">원가현황:</span>
        <span className="text-orange-600">재계산필요: {statusSummary["재계산가능"] || 0}건</span>
        <span className="text-green-600">최신: {statusSummary["최신"] || 0}건</span>
        <span className="ml-4">현재재고금액: {totals.currentTotal.toLocaleString()}원</span>
        <span>→</span>
        <span>재계산후금액: {totals.newTotal.toLocaleString()}원</span>
        <span className={`font-bold ${totals.costDiff < 0 ? "text-blue-600" : totals.costDiff > 0 ? "text-red-600" : ""}`}>
          (차이: {totals.costDiff > 0 ? "+" : ""}{totals.costDiff.toLocaleString()}원)
        </span>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-10">
                <input
                  type="checkbox"
                  onChange={(e) => handleSelectAll(e.target.checked)}
                  checked={selectedIds.length === filteredData.filter(d => d.status === "재계산가능").length && selectedIds.length > 0}
                />
              </th>
              <th className="border border-gray-400 px-2 py-1 w-20">품목코드</th>
              <th className="border border-gray-400 px-2 py-1">품목명</th>
              <th className="border border-gray-400 px-2 py-1 w-24">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-12">단위</th>
              <th className="border border-gray-400 px-2 py-1 w-20">창고</th>
              <th className="border border-gray-400 px-2 py-1 w-14">수량</th>
              <th className="border border-gray-400 px-2 py-1 w-20">현재단가</th>
              <th className="border border-gray-400 px-2 py-1 w-24">현재금액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">평균매입가</th>
              <th className="border border-gray-400 px-2 py-1 w-20">신규단가</th>
              <th className="border border-gray-400 px-2 py-1 w-24">신규금액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">차액</th>
              <th className="border border-gray-400 px-2 py-1 w-16">변동률</th>
              <th className="border border-gray-400 px-2 py-1 w-24">최종계산일</th>
              <th className="border border-gray-400 px-2 py-1 w-20">상태</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => {
              const isRowSelected = selectedIds.includes(item.id);
              return (
                <tr
                  key={item.id}
                  className={`cursor-pointer ${
                    isRowSelected
                      ? "bg-blue-100"
                      : item.status === "재계산가능"
                      ? "bg-yellow-50 hover:bg-yellow-100"
                      : "hover:bg-gray-100"
                  }`}
                >
                  <td className="border border-gray-300 px-2 py-1 text-center">
                    {item.status === "재계산가능" && (
                      <input
                        type="checkbox"
                        checked={isRowSelected}
                        onChange={(e) => handleSelectItem(item.id, e.target.checked)}
                      />
                    )}
                  </td>
                  <td className="border border-gray-300 px-2 py-1 font-medium">{item.itemCode}</td>
                  <td className="border border-gray-300 px-2 py-1">{item.itemName}</td>
                  <td className="border border-gray-300 px-2 py-1">{item.specification}</td>
                  <td className="border border-gray-300 px-2 py-1 text-center">{item.unit}</td>
                  <td className="border border-gray-300 px-2 py-1">{item.warehouse}</td>
                  <td className="border border-gray-300 px-2 py-1 text-right">{item.currentQty.toLocaleString()}</td>
                  <td className="border border-gray-300 px-2 py-1 text-right">{item.currentCost.toLocaleString()}</td>
                  <td className="border border-gray-300 px-2 py-1 text-right">{item.currentTotal.toLocaleString()}</td>
                  <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">{item.avgPurchaseCost.toLocaleString()}</td>
                  <td className="border border-gray-300 px-2 py-1 text-right font-medium">{item.newCost.toLocaleString()}</td>
                  <td className="border border-gray-300 px-2 py-1 text-right font-medium">{item.newTotal.toLocaleString()}</td>
                  <td className={`border border-gray-300 px-2 py-1 text-right font-medium ${getDiffColor(item.costDiff, false)}`}>
                    {item.costDiff !== 0 ? (item.costDiff > 0 ? "+" : "") + item.costDiff.toLocaleString() : "-"}
                  </td>
                  <td className={`border border-gray-300 px-2 py-1 text-right ${getDiffColor(item.costDiffRate, false)}`}>
                    {item.costDiffRate !== 0 ? (item.costDiffRate > 0 ? "+" : "") + item.costDiffRate.toFixed(2) + "%" : "-"}
                  </td>
                  <td className="border border-gray-300 px-2 py-1 text-center">{item.lastCalcDate}</td>
                  <td className={`border border-gray-300 px-2 py-1 text-center ${getStatusColor(item.status, false)}`}>
                    {item.status}
                  </td>
                </tr>
              );
            })}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={8}>
                (합계: {filteredData.length}건)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.currentTotal.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={2}></td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.newTotal.toLocaleString()}
              </td>
              <td className={`border border-gray-400 px-2 py-1 text-right ${getDiffColor(totals.costDiff, false)}`}>
                {totals.costDiff !== 0 ? (totals.costDiff > 0 ? "+" : "") + totals.costDiff.toLocaleString() : "-"}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={3}></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredData.length}건 | 선택: {selectedIds.length}건 | 계산방법: {calcMethod} | loading ok
      </div>

      {/* 확인 모달 */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[400px] rounded bg-white shadow-lg">
            <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-4 py-2">
              <span className="text-sm font-medium text-white">원가재계산 확인</span>
              <button onClick={() => setShowConfirm(false)} className="text-white hover:text-gray-200">✕</button>
            </div>
            <div className="p-4">
              <p className="text-sm mb-4">
                선택한 {selectedIds.length}개 품목의 원가를 재계산하시겠습니까?
              </p>
              <div className="bg-gray-50 rounded p-3 text-xs">
                <div className="flex justify-between mb-1">
                  <span>계산방법:</span>
                  <span className="font-medium">{calcMethod}</span>
                </div>
                <div className="flex justify-between mb-1">
                  <span>기준일:</span>
                  <span className="font-medium">{baseDate}</span>
                </div>
                <div className="flex justify-between">
                  <span>예상 차액:</span>
                  <span className={`font-medium ${totals.costDiff < 0 ? "text-blue-600" : "text-red-600"}`}>
                    {totals.costDiff > 0 ? "+" : ""}{totals.costDiff.toLocaleString()}원
                  </span>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 border-t bg-gray-50 px-4 py-2">
              <button onClick={() => setShowConfirm(false)} className="rounded border px-4 py-1 text-xs hover:bg-gray-100">
                취소
              </button>
              <button onClick={confirmRecalculate} className="rounded bg-blue-500 px-4 py-1 text-xs text-white hover:bg-blue-600">
                재계산 실행
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
