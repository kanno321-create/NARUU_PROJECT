"use client";

import React, { useState } from "react";

interface CarryoverItem {
  id: string;
  customerCode: string;
  customerName: string;
  carryoverDate: string;
  receivable: number;  // 미수금
  payable: number;     // 미지급금
}

// 이지판매재고관리 원본 데이터 100% 복제 (2025-12-05 스크린샷 기준)
const ORIGINAL_ITEMS: CarryoverItem[] = [
  {
    id: "1",
    customerCode: "m001",
    customerName: "테스트사업장",
    carryoverDate: "2025-12-05",
    receivable: 1500000,
    payable: 0,
  },
  {
    id: "2",
    customerCode: "m002",
    customerName: "이지사업장",
    carryoverDate: "2025-12-05",
    receivable: 0,
    payable: 21312,
  },
  {
    id: "3",
    customerCode: "m003",
    customerName: "재고사업장",
    carryoverDate: "2025-12-05",
    receivable: 750000,
    payable: 0,
  },
];

export function ReceivablePayableCarryover() {
  const [items, setItems] = useState<CarryoverItem[]>(ORIGINAL_ITEMS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDate, setSelectedDate] = useState("2025년 12월 05일");
  const [editingCell, setEditingCell] = useState<{ id: string; field: string } | null>(null);

  const filteredItems = items.filter(
    (item) =>
      item.customerName.includes(searchQuery) ||
      item.customerCode.includes(searchQuery)
  );

  const handleCellDoubleClick = (id: string, field: string) => {
    setEditingCell({ id, field });
  };

  const handleCellChange = (id: string, field: keyof CarryoverItem, value: string | number) => {
    setItems(
      items.map((item) =>
        item.id === id ? { ...item, [field]: value } : item
      )
    );
  };

  const handleCellBlur = () => {
    setEditingCell(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === "Tab") {
      setEditingCell(null);
    }
  };

  const handleBatchDateChange = () => {
    const newDate = prompt("이월일자를 입력하세요 (YYYY-MM-DD):", "2025-12-05");
    if (newDate) {
      setItems(
        items.map((item) => ({ ...item, carryoverDate: newDate }))
      );
    }
  };

  const renderEditableCell = (
    item: CarryoverItem,
    field: keyof CarryoverItem,
    type: "text" | "number" = "text"
  ) => {
    const isEditing = editingCell?.id === item.id && editingCell?.field === field;
    const value = item[field];

    if (isEditing) {
      return (
        <input
          type={type}
          value={value}
          onChange={(e) =>
            handleCellChange(
              item.id,
              field,
              type === "number" ? Number(e.target.value) : e.target.value
            )
          }
          onBlur={handleCellBlur}
          onKeyDown={handleKeyDown}
          autoFocus
          className="w-full border-none bg-white px-1 py-0 text-xs outline-none"
        />
      );
    }

    return (
      <span
        onDoubleClick={() => handleCellDoubleClick(item.id, field)}
        className="cursor-pointer"
      >
        {type === "number" && typeof value === "number"
          ? value.toLocaleString()
          : value}
      </span>
    );
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">미수미지급금이월</span>
      </div>

      {/* 검색 바 */}
      <div className="flex items-center justify-between border-b bg-white px-2 py-1">
        <div className="flex items-center gap-2">
          <span className="text-xs">업체명:</span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-40 rounded border border-gray-400 px-2 py-0.5 text-xs"
          />
          <button className="rounded border border-gray-400 bg-gray-100 px-3 py-0.5 text-xs hover:bg-gray-200">
            검 색(F)
          </button>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="rounded border border-gray-400 px-2 py-0.5 text-xs"
          >
            <option value="2025년 12월 05일">2025년 12월 05일</option>
            <option value="2025년 11월 30일">2025년 11월 30일</option>
            <option value="2025년 10월 31일">2025년 10월 31일</option>
          </select>
          <button
            onClick={handleBatchDateChange}
            className="rounded border border-gray-400 bg-gray-100 px-3 py-0.5 text-xs hover:bg-gray-200"
          >
            날짜전체입력
          </button>
        </div>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-24">업체코드</th>
              <th className="border border-gray-400 px-2 py-1 w-32">업체명</th>
              <th className="border border-gray-400 px-2 py-1 w-28">이월일자</th>
              <th className="border border-gray-400 px-2 py-1 w-28">미수금</th>
              <th className="border border-gray-400 px-2 py-1 w-28">미지급금</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.map((item) => (
              <tr
                key={item.id}
                className={`${
                  selectedId === item.id ? "bg-[#316AC5] text-white" : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1">{item.customerCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerName}</td>
                <td className="border border-gray-300 px-2 py-1">
                  {renderEditableCell(item, "carryoverDate", "text")}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">
                  {renderEditableCell(item, "receivable", "number")}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">
                  {renderEditableCell(item, "payable", "number")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredItems.length}개 업체 | 더블클릭하여 금액 수정 가능
      </div>
    </div>
  );
}
