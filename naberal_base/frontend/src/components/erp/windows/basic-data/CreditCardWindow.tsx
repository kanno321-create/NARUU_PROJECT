"use client";

import React, { useState } from "react";

interface CreditCard {
  id: string;
  code: string;        // 코드
  cardName: string;    // 카드명
  feeRate: number;     // 수수료율(%)
}

// 이지판매재고관리 원본 데이터 100% 복제 (2025-12-05 스크린샷 기준)
const ORIGINAL_CARDS: CreditCard[] = [
  { id: "1", code: "01", cardName: "신한카드", feeRate: 2.5 },
  { id: "2", code: "02", cardName: "국민카드", feeRate: 2.3 },
  { id: "3", code: "03", cardName: "삼성카드", feeRate: 2.4 },
  { id: "4", code: "04", cardName: "현대카드", feeRate: 2.2 },
  { id: "5", code: "05", cardName: "롯데카드", feeRate: 2.5 },
];

const emptyCard: CreditCard = {
  id: "",
  code: "",
  cardName: "",
  feeRate: 0,
};

export function CreditCardWindow() {
  const [cards, setCards] = useState<CreditCard[]>(ORIGINAL_CARDS);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRow, setSelectedRow] = useState<number | null>(null);

  // 모달 상태
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit">("add");
  const [editForm, setEditForm] = useState<CreditCard>(emptyCard);

  const filteredCards = cards.filter(
    (c) =>
      c.cardName.includes(searchQuery) ||
      c.code.includes(searchQuery)
  );

  // 툴바 버튼 핸들러
  const handleAdd = () => {
    const nextCode = String(cards.length + 1).padStart(2, "0");
    setEditForm({ ...emptyCard, id: String(Date.now()), code: nextCode });
    setModalMode("add");
    setShowModal(true);
  };

  const handleEdit = () => {
    if (selectedRow === null) {
      alert("수정할 카드를 선택하세요.");
      return;
    }
    const card = filteredCards[selectedRow];
    setEditForm({ ...card });
    setModalMode("edit");
    setShowModal(true);
  };

  const handleDelete = () => {
    if (selectedRow === null) {
      alert("삭제할 카드를 선택하세요.");
      return;
    }
    if (confirm("선택한 카드를 삭제하시겠습니까?")) {
      const card = filteredCards[selectedRow];
      setCards(cards.filter((c) => c.id !== card.id));
      setSelectedRow(null);
    }
  };

  const handleRefresh = () => {
    setCards([...ORIGINAL_CARDS]);
    setSelectedRow(null);
    setSearchQuery("");
  };

  const handleSearch = () => {
    // 검색은 실시간으로 되므로 별도 처리 불필요
  };

  const handleViewAll = () => {
    setSearchQuery("");
  };

  // 모달 저장
  const handleSave = () => {
    if (!editForm.cardName) {
      alert("카드명을 입력하세요.");
      return;
    }
    if (!editForm.code) {
      alert("코드를 입력하세요.");
      return;
    }

    if (modalMode === "add") {
      setCards([...cards, editForm]);
    } else {
      setCards(
        cards.map((c) => (c.id === editForm.id ? editForm : c))
      );
    }
    setShowModal(false);
    setSelectedRow(null);
  };

  const handleCancel = () => {
    setShowModal(false);
  };

  // 행 더블클릭으로 수정
  const handleRowDoubleClick = (index: number) => {
    setSelectedRow(index);
    const card = filteredCards[index];
    setEditForm({ ...card });
    setModalMode("edit");
    setShowModal(true);
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 툴바 - 이지판매재고관리 스타일 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button
          onClick={handleAdd}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-green-600">⊕</span> 추가
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-blue-600">✎</span> 수정
        </button>
        <button
          onClick={handleDelete}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-red-600">✕</span> 삭제
        </button>
        <div className="mx-1 h-6 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
          <span>A</span> 미리보기
        </button>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-blue-600">↻</span> 새로고침
        </button>
        <div className="mx-1 h-6 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
          <span>▤</span> 표시항목
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
          <span className="text-green-700">📊</span> 엑셀입력
        </button>
      </div>

      {/* 검색 영역 */}
      <div className="flex items-center gap-2 border-b bg-gray-100 px-4 py-2">
        <span className="text-sm">카드명:</span>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-40 rounded border border-gray-400 px-2 py-1 text-sm"
        />
        <button
          onClick={handleSearch}
          className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
        >
          검 색(F)
        </button>
        <button
          onClick={handleViewAll}
          className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
        >
          전체보기
        </button>
      </div>

      {/* 그리드 - 이지판매재고관리 컬럼 100% */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 text-center font-normal">
                <input type="checkbox" />
              </th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">코드</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">카드명</th>
              <th className="border border-gray-400 px-2 py-1 text-right font-normal">수수료율(%)</th>
            </tr>
          </thead>
          <tbody>
            {filteredCards.map((card, index) => (
              <tr
                key={card.id}
                className={`cursor-pointer ${
                  selectedRow === index ? "bg-[#316AC5] text-white" : "bg-white hover:bg-gray-100"
                }`}
                onClick={() => setSelectedRow(index)}
                onDoubleClick={() => handleRowDoubleClick(index)}
              >
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <input type="checkbox" />
                </td>
                <td className="border border-gray-300 px-2 py-1">{card.code}</td>
                <td className="border border-gray-300 px-2 py-1">{card.cardName}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">{card.feeRate.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="flex items-center justify-end border-t bg-gray-100 px-4 py-1 text-sm text-gray-600">
        <span>전체 {cards.length} 항목</span>
        <span className="mx-4">|</span>
        <span>{filteredCards.length} 항목표시</span>
      </div>

      {/* 신용카드 정보등록 모달 - 이지판매재고관리 100% 복제 */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-[350px] rounded bg-gray-200 shadow-lg">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between border-b border-gray-400 bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">신용카드 정보입력</span>
              <button
                onClick={handleCancel}
                className="text-white hover:text-gray-200"
              >
                ✕
              </button>
            </div>

            {/* 모달 내용 */}
            <div className="bg-[#F0EDE4] p-4">
              <fieldset className="rounded border border-gray-400 p-3">
                <legend className="px-2 text-sm text-blue-700">카드정보</legend>
                <div className="grid grid-cols-[80px_1fr] gap-2 text-sm">
                  <label className="py-1 text-right">코드:</label>
                  <input
                    type="text"
                    value={editForm.code}
                    onChange={(e) => setEditForm({ ...editForm, code: e.target.value })}
                    className="w-20 border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">카드명:</label>
                  <input
                    type="text"
                    value={editForm.cardName}
                    onChange={(e) => setEditForm({ ...editForm, cardName: e.target.value })}
                    className="w-full border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">수수료율:</label>
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      step="0.1"
                      value={editForm.feeRate}
                      onChange={(e) => setEditForm({ ...editForm, feeRate: Number(e.target.value) })}
                      className="w-20 border border-gray-400 px-2 py-1 text-right"
                    />
                    <span>%</span>
                  </div>
                </div>
              </fieldset>
              <p className="mt-3 text-sm text-gray-600">
                새로운 신용카드의 정보를 등록합니다.
              </p>
            </div>

            {/* 모달 푸터 - 이지판매재고관리 스타일 */}
            <div className="flex justify-end gap-2 border-t border-gray-400 bg-gray-200 px-4 py-3">
              <button
                onClick={handleSave}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
              >
                저장
              </button>
              <button
                onClick={handleCancel}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
