"use client";

import React, { useState } from "react";

interface BondDebtItem {
  id: string;
  bondDebtType: "채권" | "채무";
  category: "채권이월" | "채무이월";
  relatedItemCode: string;
  relatedItemName: string;
  carryoverAmount: number;
  carryoverDate: string;
}

// 이지판매재고관리 원본 데이터 100% 복제
const ORIGINAL_ITEMS: BondDebtItem[] = [];

export function BondDebtCarryover() {
  const [items, setItems] = useState<BondDebtItem[]>(ORIGINAL_ITEMS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit">("add");

  const [formData, setFormData] = useState<Omit<BondDebtItem, "id">>({
    bondDebtType: "채권",
    category: "채권이월",
    relatedItemCode: "",
    relatedItemName: "",
    carryoverAmount: 0,
    carryoverDate: "2025년 12월 05일",
  });

  const filteredItems = items.filter(
    (item) =>
      item.relatedItemName.includes(searchQuery) ||
      item.relatedItemCode.includes(searchQuery) ||
      item.category.includes(searchQuery)
  );

  const handleAdd = () => {
    setModalMode("add");
    setFormData({
      bondDebtType: "채권",
      category: "채권이월",
      relatedItemCode: "",
      relatedItemName: "",
      carryoverAmount: 0,
      carryoverDate: "2025년 12월 05일",
    });
    setIsModalOpen(true);
  };

  const handleEdit = () => {
    if (!selectedId) return;
    const item = items.find((i) => i.id === selectedId);
    if (!item) return;
    setModalMode("edit");
    const { id, ...rest } = item;
    setFormData(rest);
    setIsModalOpen(true);
  };

  const handleDelete = () => {
    if (!selectedId) return;
    if (confirm("선택한 항목을 삭제하시겠습니까?")) {
      setItems(items.filter((i) => i.id !== selectedId));
      setSelectedId(null);
    }
  };

  const handleSave = () => {
    if (!formData.relatedItemCode) {
      alert("관련항목을 선택하세요.");
      return;
    }

    if (modalMode === "add") {
      const newItem: BondDebtItem = {
        id: Date.now().toString(),
        ...formData,
        bondDebtType: formData.category === "채권이월" ? "채권" : "채무",
      };
      setItems([...items, newItem]);
    } else {
      setItems(
        items.map((i) => (i.id === selectedId ? { ...i, ...formData } : i))
      );
    }
    setIsModalOpen(false);
  };

  const handleCategoryChange = (category: "채권이월" | "채무이월") => {
    setFormData({
      ...formData,
      category,
      bondDebtType: category === "채권이월" ? "채권" : "채무",
    });
  };

  const handleRowDoubleClick = (item: BondDebtItem) => {
    setSelectedId(item.id);
    setModalMode("edit");
    const { id, ...rest } = item;
    setFormData(rest);
    setIsModalOpen(true);
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">채권채무이월</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button
          onClick={handleAdd}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
          <span>➕</span> 추가
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
          disabled={!selectedId}
        >
          <span>✏️</span> 수정
        </button>
        <button
          onClick={handleDelete}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
          disabled={!selectedId}
        >
          <span>🗑️</span> 삭제
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
      </div>

      {/* 검색 바 */}
      <div className="flex items-center gap-2 border-b bg-white px-2 py-1">
        <span className="text-xs">구분명:</span>
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

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-20">채권/채무</th>
              <th className="border border-gray-400 px-2 py-1 w-24">구분</th>
              <th className="border border-gray-400 px-2 py-1 w-28">관련항목코드</th>
              <th className="border border-gray-400 px-2 py-1 w-32">관련항목명</th>
              <th className="border border-gray-400 px-2 py-1 w-28">이월금액</th>
              <th className="border border-gray-400 px-2 py-1 w-28">이월일자</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.length === 0 ? (
              <tr>
                <td colSpan={6} className="border border-gray-300 px-2 py-8 text-center text-gray-500">
                  등록된 데이터가 없습니다. 추가 버튼을 클릭하여 새 항목을 등록하세요.
                </td>
              </tr>
            ) : (
              filteredItems.map((item) => (
                <tr
                  key={item.id}
                  className={`cursor-pointer ${
                    selectedId === item.id ? "bg-[#316AC5] text-white" : "hover:bg-gray-100"
                  }`}
                  onClick={() => setSelectedId(item.id)}
                  onDoubleClick={() => handleRowDoubleClick(item)}
                >
                  <td className="border border-gray-300 px-2 py-1">{item.bondDebtType}</td>
                  <td className="border border-gray-300 px-2 py-1">{item.category}</td>
                  <td className="border border-gray-300 px-2 py-1">{item.relatedItemCode}</td>
                  <td className="border border-gray-300 px-2 py-1">{item.relatedItemName}</td>
                  <td className="border border-gray-300 px-2 py-1 text-right">
                    {item.carryoverAmount.toLocaleString()}
                  </td>
                  <td className="border border-gray-300 px-2 py-1">{item.carryoverDate}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredItems.length}건 | loading ok
      </div>

      {/* 모달 */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[400px] rounded border border-gray-400 bg-[#F0EDE4] shadow-lg">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between rounded-t border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">채권/채무이월</span>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-white hover:text-gray-200"
              >
                ✕
              </button>
            </div>

            {/* 모달 내용 */}
            <div className="p-4">
              <fieldset className="rounded border border-gray-400 p-3">
                <legend className="px-2 text-xs text-blue-700">이월정보</legend>
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <label className="w-20 text-right text-xs">구분:</label>
                    <select
                      value={formData.category}
                      onChange={(e) => handleCategoryChange(e.target.value as "채권이월" | "채무이월")}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    >
                      <option value="채권이월">채권이월</option>
                      <option value="채무이월">채무이월</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-20 text-right text-xs">그룹명:</label>
                    <select
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    >
                      <option value="채권이월">채권이월</option>
                      <option value="채무이월">채무이월</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-20 text-right text-xs">관련항목:</label>
                    <input
                      type="text"
                      value={formData.relatedItemCode}
                      onChange={(e) => setFormData({ ...formData, relatedItemCode: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    />
                    <button className="rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
                      ...
                    </button>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-20 text-right text-xs">이월금액:</label>
                    <input
                      type="number"
                      value={formData.carryoverAmount}
                      onChange={(e) => setFormData({ ...formData, carryoverAmount: Number(e.target.value) })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs text-right"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-20 text-right text-xs">이월일자:</label>
                    <select
                      value={formData.carryoverDate}
                      onChange={(e) => setFormData({ ...formData, carryoverDate: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    >
                      <option value="2025년 12월 05일">2025년 12월 05일</option>
                      <option value="2025년 11월 30일">2025년 11월 30일</option>
                      <option value="2025년 10월 31일">2025년 10월 31일</option>
                    </select>
                  </div>
                </div>
                <p className="mt-3 text-xs text-gray-600">
                  채권/채무 이월 정보를 등록합니다.
                </p>
              </fieldset>
            </div>

            {/* 모달 푸터 */}
            <div className="flex justify-center gap-2 border-t bg-gray-200 px-4 py-2">
              <button
                onClick={handleSave}
                className="rounded border border-gray-400 bg-gray-100 px-6 py-1 text-xs hover:bg-gray-200"
              >
                저 장
              </button>
              <button
                onClick={() => setIsModalOpen(false)}
                className="rounded border border-gray-400 bg-gray-100 px-6 py-1 text-xs hover:bg-gray-200"
              >
                취 소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
