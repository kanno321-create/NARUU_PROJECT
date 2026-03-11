"use client";

import React, { useState } from "react";

interface CreditCard {
  id: string;
  code: string;
  cardName: string;
  feeRate: number;
}

// 이지판매재고관리 원본 데이터 100% 복제 (2025-12-05 스크린샷 기준)
const ORIGINAL_CARDS: CreditCard[] = [
  { id: "1", code: "ca001", cardName: "신한카드", feeRate: 0 },
  { id: "2", code: "ca002", cardName: "국민카드", feeRate: 0 },
  { id: "3", code: "ca003", cardName: "하나카드", feeRate: 0 },
];

export function CreditCardRegistration() {
  const [cards, setCards] = useState<CreditCard[]>(ORIGINAL_CARDS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit">("add");

  const [formData, setFormData] = useState<Omit<CreditCard, "id">>({
    code: "",
    cardName: "",
    feeRate: 0,
  });

  const filteredCards = cards.filter(
    (card) =>
      card.cardName.includes(searchQuery) ||
      card.code.includes(searchQuery)
  );

  const handleAdd = () => {
    setModalMode("add");
    setFormData({
      code: `ca${String(cards.length + 1).padStart(3, "0")}`,
      cardName: "",
      feeRate: 0,
    });
    setIsModalOpen(true);
  };

  const handleEdit = () => {
    if (!selectedId) return;
    const card = cards.find((c) => c.id === selectedId);
    if (!card) return;
    setModalMode("edit");
    const { id, ...rest } = card;
    setFormData(rest);
    setIsModalOpen(true);
  };

  const handleDelete = () => {
    if (!selectedId) return;
    if (confirm("선택한 카드를 삭제하시겠습니까?")) {
      setCards(cards.filter((c) => c.id !== selectedId));
      setSelectedId(null);
    }
  };

  const handleSave = () => {
    if (!formData.cardName) {
      alert("카드명은 필수 입력 항목입니다.");
      return;
    }

    if (modalMode === "add") {
      const newCard: CreditCard = {
        id: Date.now().toString(),
        ...formData,
      };
      setCards([...cards, newCard]);
    } else {
      setCards(
        cards.map((c) => (c.id === selectedId ? { ...c, ...formData } : c))
      );
    }
    setIsModalOpen(false);
  };

  const handleRowDoubleClick = (card: CreditCard) => {
    setSelectedId(card.id);
    setModalMode("edit");
    const { id, ...rest } = card;
    setFormData(rest);
    setIsModalOpen(true);
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">신용카드등록</span>
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
          <span>🔤</span> 미리보기
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 표시항목
        </button>
      </div>

      {/* 검색 바 */}
      <div className="flex items-center gap-2 border-b bg-white px-2 py-1">
        <span className="text-xs">카드명:</span>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-40 rounded border border-gray-400 px-2 py-0.5 text-xs"
        />
        <button className="rounded border border-gray-400 bg-gray-100 px-3 py-0.5 text-xs hover:bg-gray-200">
          검 색(F)
        </button>
        <button
          onClick={() => setSearchQuery("")}
          className="rounded border border-gray-400 bg-gray-100 px-3 py-0.5 text-xs hover:bg-gray-200"
        >
          전체보기
        </button>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-32">코드</th>
              <th className="border border-gray-400 px-2 py-1 w-32">수수료율</th>
              <th className="border border-gray-400 px-2 py-1">신용카드명</th>
            </tr>
          </thead>
          <tbody>
            {filteredCards.map((card) => (
              <tr
                key={card.id}
                className={`cursor-pointer ${
                  selectedId === card.id ? "bg-[#316AC5] text-white" : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(card.id)}
                onDoubleClick={() => handleRowDoubleClick(card)}
              >
                <td className="border border-gray-300 px-2 py-1">{card.code}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">{card.feeRate}</td>
                <td className="border border-gray-300 px-2 py-1">{card.cardName}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="flex justify-between border-t bg-gray-100 px-3 py-1 text-xs">
        <span className="text-green-600">loading ok</span>
        <span>전체 {cards.length} 항목 &nbsp;&nbsp; {filteredCards.length} 항목표시</span>
      </div>

      {/* 모달 */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[400px] rounded border border-gray-400 bg-[#F0EDE4] shadow-lg">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between rounded-t border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">신용카드 등록</span>
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
                <legend className="px-2 text-xs text-blue-700">신용카드등록</legend>
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <label className="w-20 text-right text-xs">코드:</label>
                    <input
                      type="text"
                      value={formData.code}
                      onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-20 text-right text-xs">카드명:</label>
                    <input
                      type="text"
                      value={formData.cardName}
                      onChange={(e) => setFormData({ ...formData, cardName: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-20 text-right text-xs">수수료율:</label>
                    <input
                      type="number"
                      value={formData.feeRate}
                      onChange={(e) => setFormData({ ...formData, feeRate: Number(e.target.value) })}
                      className="w-24 rounded border border-gray-400 px-2 py-1 text-xs text-right"
                      step="0.1"
                    />
                    <span className="text-xs">%</span>
                  </div>
                </div>
                <p className="mt-3 text-xs text-gray-600">
                  사용할 신용카드 정보를 등록합니다.
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
                취소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
