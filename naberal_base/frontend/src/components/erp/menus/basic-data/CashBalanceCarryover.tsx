"use client";

import React, { useState } from "react";

export function CashBalanceCarryover() {
  const [carryoverAmount, setCarryoverAmount] = useState(0);
  const [carryoverDate, setCarryoverDate] = useState("2025년 12월 05일");
  const [isSaved, setIsSaved] = useState(false);

  const handleSave = () => {
    if (carryoverAmount < 0) {
      alert("이월금액은 0 이상이어야 합니다.");
      return;
    }
    setIsSaved(true);
    alert(`현금 잔고 이월이 저장되었습니다.\n이월금액: ${carryoverAmount.toLocaleString()}원\n이월일자: ${carryoverDate}`);
  };

  const handleCancel = () => {
    setCarryoverAmount(0);
    setCarryoverDate("2025년 12월 05일");
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">현금잔고이월</span>
      </div>

      {/* 내용 */}
      <div className="flex flex-1 items-center justify-center p-4">
        <div className="w-[280px] rounded border border-gray-400 bg-[#F0EDE4] shadow-lg">
          {/* 헤더 */}
          <div className="flex items-center justify-between rounded-t border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
            <span className="text-sm font-medium text-white">현금잔고이월</span>
          </div>

          {/* 내용 */}
          <div className="p-4">
            <fieldset className="rounded border border-gray-400 p-3">
              <legend className="px-2 text-xs text-blue-700">이월정보</legend>
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <label className="w-16 text-right text-xs">이월금액:</label>
                  <input
                    type="number"
                    value={carryoverAmount}
                    onChange={(e) => setCarryoverAmount(Number(e.target.value))}
                    className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs text-right"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <label className="w-16 text-right text-xs">이월일자:</label>
                  <select
                    value={carryoverDate}
                    onChange={(e) => setCarryoverDate(e.target.value)}
                    className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                  >
                    <option value="2025년 12월 05일">2025년 12월 05일</option>
                    <option value="2025년 11월 30일">2025년 11월 30일</option>
                    <option value="2025년 10월 31일">2025년 10월 31일</option>
                    <option value="2025년 09월 30일">2025년 09월 30일</option>
                  </select>
                </div>
              </div>
              <p className="mt-3 text-xs text-gray-600">
                현금 잔고의 이월정보를 등록합니다.
              </p>
            </fieldset>
          </div>

          {/* 푸터 */}
          <div className="flex justify-center gap-2 border-t bg-gray-200 px-4 py-2">
            <button
              onClick={handleSave}
              className="rounded border border-gray-400 bg-gray-100 px-6 py-1 text-xs hover:bg-gray-200"
            >
              저 장
            </button>
            <button
              onClick={handleCancel}
              className="rounded border border-gray-400 bg-gray-100 px-6 py-1 text-xs hover:bg-gray-200"
            >
              취 소
            </button>
          </div>
        </div>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        {isSaved ? "저장됨" : "loading ok"}
      </div>
    </div>
  );
}
