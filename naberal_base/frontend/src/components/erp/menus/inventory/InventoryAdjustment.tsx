"use client";

import React, { useState } from "react";

interface AdjustmentItem {
  id: string;
  adjustNo: string;
  adjustDate: string;
  adjustType: string;
  itemCode: string;
  itemName: string;
  specification: string;
  unit: string;
  warehouse: string;
  beforeQty: number;
  adjustQty: number;
  afterQty: number;
  unitCost: number;
  adjustAmount: number;
  reason: string;
  approver: string;
  status: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: AdjustmentItem[] = [
  {
    id: "1",
    adjustNo: "ADJ2024120001",
    adjustDate: "2025-12-05",
    adjustType: "증가",
    itemCode: "P006",
    itemName: "TERMINAL BLOCK",
    specification: "600V",
    unit: "EA",
    warehouse: "제2창고",
    beforeQty: 400,
    adjustQty: 10,
    afterQty: 410,
    unitCost: 4000,
    adjustAmount: 40000,
    reason: "재고실사 조정",
    approver: "김관리",
    status: "승인",
  },
  {
    id: "2",
    adjustNo: "ADJ2024120002",
    adjustDate: "2025-12-04",
    adjustType: "감소",
    itemCode: "P002",
    itemName: "SBE-204 차단기",
    specification: "4P 200AF 150AT",
    unit: "EA",
    warehouse: "본사창고",
    beforeQty: 45,
    adjustQty: -2,
    afterQty: 43,
    unitCost: 85000,
    adjustAmount: -170000,
    reason: "불량품 폐기",
    approver: "박관리",
    status: "승인",
  },
  {
    id: "3",
    adjustNo: "ADJ2024120003",
    adjustDate: "2025-12-03",
    adjustType: "증가",
    itemCode: "P007",
    itemName: "E.T (접지단자)",
    specification: "100AF용",
    unit: "EA",
    warehouse: "본사창고",
    beforeQty: 65,
    adjustQty: 5,
    afterQty: 70,
    unitCost: 4500,
    adjustAmount: 22500,
    reason: "전산오류 정정",
    approver: "김관리",
    status: "승인",
  },
  {
    id: "4",
    adjustNo: "ADJ2024120004",
    adjustDate: "2025-12-02",
    adjustType: "감소",
    itemCode: "P005",
    itemName: "MC-22 마그네트",
    specification: "22A",
    unit: "EA",
    warehouse: "본사창고",
    beforeQty: 32,
    adjustQty: -2,
    afterQty: 30,
    unitCost: 35000,
    adjustAmount: -70000,
    reason: "분실 처리",
    approver: "이관리",
    status: "대기",
  },
  {
    id: "5",
    adjustNo: "ADJ2024120005",
    adjustDate: "2025-12-01",
    adjustType: "감소",
    itemCode: "P008",
    itemName: "P-COVER 아크릴",
    specification: "600×800",
    unit: "EA",
    warehouse: "본사창고",
    beforeQty: 18,
    adjustQty: -3,
    afterQty: 15,
    unitCost: 17000,
    adjustAmount: -51000,
    reason: "파손 폐기",
    approver: "박관리",
    status: "승인",
  },
];

export function InventoryAdjustment() {
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [typeFilter, setTypeFilter] = useState("전체");
  const [statusFilter, setStatusFilter] = useState("전체");
  const [data] = useState<AdjustmentItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);

  const filteredData = data.filter(
    (item) =>
      (typeFilter === "전체" || item.adjustType === typeFilter) &&
      (statusFilter === "전체" || item.status === statusFilter)
  );

  // 유형별 집계
  const typeSummary = filteredData.reduce((acc, item) => {
    if (!acc[item.adjustType]) {
      acc[item.adjustType] = { count: 0, amount: 0 };
    }
    acc[item.adjustType].count += 1;
    acc[item.adjustType].amount += item.adjustAmount;
    return acc;
  }, {} as Record<string, { count: number; amount: number }>);

  // 합계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      adjustQty: acc.adjustQty + item.adjustQty,
      adjustAmount: acc.adjustAmount + item.adjustAmount,
    }),
    { adjustQty: 0, adjustAmount: 0 }
  );

  const getTypeColor = (type: string, isSelected: boolean) => {
    if (isSelected) return "";
    return type === "증가" ? "text-blue-600" : "text-red-600";
  };

  const getStatusColor = (status: string, isSelected: boolean) => {
    if (isSelected) return "";
    return status === "승인" ? "text-green-600" : "text-orange-600";
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">재고조정</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1 rounded border border-gray-400 bg-blue-100 px-2 py-0.5 text-xs hover:bg-blue-200"
        >
          <span>➕</span> 조정등록
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>✏️</span> 수정
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🗑️</span> 삭제
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-green-100 px-2 py-0.5 text-xs hover:bg-green-200">
          <span>✅</span> 승인
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-red-100 px-2 py-0.5 text-xs hover:bg-red-200">
          <span>❌</span> 반려
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
          <span className="text-xs">유형:</span>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="증가">증가</option>
            <option value="감소">감소</option>
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
            <option value="승인">승인</option>
            <option value="대기">대기</option>
          </select>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          조 회(F)
        </button>
      </div>

      {/* 유형별 요약 */}
      <div className="flex items-center gap-6 border-b bg-yellow-50 px-3 py-2 text-xs">
        <span className="font-medium">조정현황:</span>
        <span className="text-blue-600">
          증가: {typeSummary["증가"]?.count || 0}건 (+{(typeSummary["증가"]?.amount || 0).toLocaleString()}원)
        </span>
        <span className="text-red-600">
          감소: {typeSummary["감소"]?.count || 0}건 ({(typeSummary["감소"]?.amount || 0).toLocaleString()}원)
        </span>
        <span className={`ml-4 font-bold ${totals.adjustAmount >= 0 ? "text-blue-600" : "text-red-600"}`}>
          순조정금액: {totals.adjustAmount.toLocaleString()}원
        </span>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-28">조정번호</th>
              <th className="border border-gray-400 px-2 py-1 w-24">조정일자</th>
              <th className="border border-gray-400 px-2 py-1 w-14">유형</th>
              <th className="border border-gray-400 px-2 py-1 w-20">품목코드</th>
              <th className="border border-gray-400 px-2 py-1">품목명</th>
              <th className="border border-gray-400 px-2 py-1 w-24">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-12">단위</th>
              <th className="border border-gray-400 px-2 py-1 w-20">창고</th>
              <th className="border border-gray-400 px-2 py-1 w-16">조정전</th>
              <th className="border border-gray-400 px-2 py-1 w-16">조정수량</th>
              <th className="border border-gray-400 px-2 py-1 w-16">조정후</th>
              <th className="border border-gray-400 px-2 py-1 w-20">단가</th>
              <th className="border border-gray-400 px-2 py-1 w-24">조정금액</th>
              <th className="border border-gray-400 px-2 py-1">사유</th>
              <th className="border border-gray-400 px-2 py-1 w-16">승인자</th>
              <th className="border border-gray-400 px-2 py-1 w-14">상태</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr
                key={item.id}
                className={`cursor-pointer ${
                  selectedId === item.id
                    ? "bg-[#316AC5] text-white"
                    : item.status === "대기"
                    ? "bg-yellow-50 hover:bg-yellow-100"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.adjustNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.adjustDate}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center font-medium ${getTypeColor(item.adjustType, selectedId === item.id)}`}>
                  {item.adjustType}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.itemCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.itemName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.specification}</td>
                <td className="border border-gray-300 px-2 py-1 text-center">{item.unit}</td>
                <td className="border border-gray-300 px-2 py-1">{item.warehouse}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">{item.beforeQty.toLocaleString()}</td>
                <td className={`border border-gray-300 px-2 py-1 text-right font-medium ${getTypeColor(item.adjustType, selectedId === item.id)}`}>
                  {item.adjustQty > 0 ? "+" : ""}{item.adjustQty}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">{item.afterQty.toLocaleString()}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">{item.unitCost.toLocaleString()}</td>
                <td className={`border border-gray-300 px-2 py-1 text-right font-medium ${getTypeColor(item.adjustType, selectedId === item.id)}`}>
                  {item.adjustAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.reason}</td>
                <td className="border border-gray-300 px-2 py-1 text-center">{item.approver}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${getStatusColor(item.status, selectedId === item.id)}`}>
                  {item.status}
                </td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={9}>
                (합계: {filteredData.length}건)
              </td>
              <td className={`border border-gray-400 px-2 py-1 text-right ${totals.adjustQty >= 0 ? "text-blue-600" : "text-red-600"}`}>
                {totals.adjustQty > 0 ? "+" : ""}{totals.adjustQty}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={2}></td>
              <td className={`border border-gray-400 px-2 py-1 text-right ${totals.adjustAmount >= 0 ? "text-blue-600" : "text-red-600"}`}>
                {totals.adjustAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={3}></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredData.length}건 | 승인: {filteredData.filter(d => d.status === "승인").length} | 대기: {filteredData.filter(d => d.status === "대기").length} | loading ok
      </div>

      {/* 조정 등록 모달 */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[600px] rounded bg-white shadow-lg">
            <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-4 py-2">
              <span className="text-sm font-medium text-white">재고조정 등록</span>
              <button onClick={() => setShowModal(false)} className="text-white hover:text-gray-200">✕</button>
            </div>
            <div className="p-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium mb-1">조정일자</label>
                  <input type="date" className="w-full rounded border px-2 py-1 text-xs" defaultValue="2025-12-05" />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">조정유형</label>
                  <select className="w-full rounded border px-2 py-1 text-xs">
                    <option value="증가">증가</option>
                    <option value="감소">감소</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">품목코드</label>
                  <div className="flex gap-1">
                    <input type="text" className="flex-1 rounded border px-2 py-1 text-xs" placeholder="품목코드" />
                    <button className="rounded border px-2 py-1 text-xs bg-gray-100">🔍</button>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">품목명</label>
                  <input type="text" className="w-full rounded border px-2 py-1 text-xs" readOnly />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">창고</label>
                  <select className="w-full rounded border px-2 py-1 text-xs">
                    <option value="본사창고">본사창고</option>
                    <option value="제2창고">제2창고</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">현재고</label>
                  <input type="text" className="w-full rounded border px-2 py-1 text-xs" readOnly />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">조정수량</label>
                  <input type="number" className="w-full rounded border px-2 py-1 text-xs" placeholder="0" />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">조정후수량</label>
                  <input type="text" className="w-full rounded border px-2 py-1 text-xs" readOnly />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs font-medium mb-1">조정사유</label>
                  <textarea className="w-full rounded border px-2 py-1 text-xs h-16" placeholder="조정 사유를 입력하세요" />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 border-t bg-gray-50 px-4 py-2">
              <button onClick={() => setShowModal(false)} className="rounded border px-4 py-1 text-xs hover:bg-gray-100">
                취소
              </button>
              <button className="rounded bg-blue-500 px-4 py-1 text-xs text-white hover:bg-blue-600">
                저장
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
