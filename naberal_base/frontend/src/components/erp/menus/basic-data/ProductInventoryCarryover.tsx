"use client";

import React, { useState } from "react";

interface InventoryItem {
  id: string;
  productCode: string;
  productName: string;
  spec: string;
  detailSpec: string;
  carryoverDate: string;
  carryoverQty: number;
  carryoverPrice: number;
}

// 이지판매재고관리 원본 데이터 100% 복제 (2025-12-05 스크린샷 기준)
const ORIGINAL_ITEMS: InventoryItem[] = [
  {
    id: "1",
    productCode: "s0001",
    productName: "핸드폰케이스",
    spec: "10*10",
    detailSpec: "100*100",
    carryoverDate: "2025-12-05",
    carryoverQty: 100,
    carryoverPrice: 10000,
  },
  {
    id: "2",
    productCode: "s0002",
    productName: "노트북케이스",
    spec: "20*25",
    detailSpec: "200*300",
    carryoverDate: "2025-12-05",
    carryoverQty: 150,
    carryoverPrice: 15000,
  },
  {
    id: "3",
    productCode: "s0003",
    productName: "키보드케이스",
    spec: "300*400",
    detailSpec: "350*450",
    carryoverDate: "2025-12-05",
    carryoverQty: 200,
    carryoverPrice: 4500,
  },
];

export function ProductInventoryCarryover() {
  const [items, setItems] = useState<InventoryItem[]>(ORIGINAL_ITEMS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDate, setSelectedDate] = useState("2025년 12월 05일");
  const [editingCell, setEditingCell] = useState<{ id: string; field: string } | null>(null);

  const filteredItems = items.filter(
    (item) =>
      item.productName.includes(searchQuery) ||
      item.productCode.includes(searchQuery)
  );

  const handleCellDoubleClick = (id: string, field: string) => {
    setEditingCell({ id, field });
  };

  const handleCellChange = (id: string, field: keyof InventoryItem, value: string | number) => {
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
    item: InventoryItem,
    field: keyof InventoryItem,
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
        <span className="text-sm font-medium text-white">상품재고이월</span>
      </div>

      {/* 검색 바 */}
      <div className="flex items-center justify-between border-b bg-white px-2 py-1">
        <div className="flex items-center gap-2">
          <span className="text-xs">상품명:</span>
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
              <th className="border border-gray-400 px-2 py-1 w-20">상품코드</th>
              <th className="border border-gray-400 px-2 py-1 w-32">상품명</th>
              <th className="border border-gray-400 px-2 py-1 w-24">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-24">상세규격</th>
              <th className="border border-gray-400 px-2 py-1 w-28">이월일자</th>
              <th className="border border-gray-400 px-2 py-1 w-24">이월수량</th>
              <th className="border border-gray-400 px-2 py-1 w-24">이월단가</th>
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
                <td className="border border-gray-300 px-2 py-1">{item.productCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.productName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.spec}</td>
                <td className="border border-gray-300 px-2 py-1">{item.detailSpec}</td>
                <td className="border border-gray-300 px-2 py-1">
                  {renderEditableCell(item, "carryoverDate", "text")}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">
                  {renderEditableCell(item, "carryoverQty", "number")}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">
                  {renderEditableCell(item, "carryoverPrice", "number")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredItems.length}개 상품 | 더블클릭하여 수량/단가 수정 가능
      </div>
    </div>
  );
}
