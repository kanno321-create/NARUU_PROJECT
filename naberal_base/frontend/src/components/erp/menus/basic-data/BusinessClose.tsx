"use client";

import React, { useState } from "react";

export function BusinessClose() {
  const [closeYear, setCloseYear] = useState("2025");
  const [closeMonth, setCloseMonth] = useState("12");
  const [deleteAfterClose, setDeleteAfterClose] = useState(false);
  const [deleteOrderQuote, setDeleteOrderQuote] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleStartClose = () => {
    if (!confirm(`${closeYear}년 ${closeMonth}월 마감을 시작하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.`)) {
      return;
    }

    setIsProcessing(true);

    // 마감 처리 시뮬레이션
    setTimeout(() => {
      setIsProcessing(false);
      alert(`${closeYear}년 ${closeMonth}월 마감이 완료되었습니다.`);
    }, 2000);
  };

  const handleCancel = () => {
    if (confirm("마감 설정을 취소하시겠습니까?")) {
      setCloseYear("2025");
      setCloseMonth("12");
      setDeleteAfterClose(false);
      setDeleteOrderQuote(false);
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">사업장 마감</span>
      </div>

      {/* 내용 */}
      <div className="flex flex-1 p-4">
        {/* 좌측 로고 영역 */}
        <div className="flex w-48 flex-col items-center justify-center rounded-l border border-gray-400 bg-gradient-to-br from-blue-900 to-blue-600 p-4">
          <div className="text-center text-white">
            <p className="text-2xl font-bold">Easy</p>
            <p className="text-2xl font-bold">Panme</p>
            <p className="mt-2 text-sm">이지판매재고관리</p>
          </div>
        </div>

        {/* 우측 설정 영역 */}
        <div className="flex-1 rounded-r border-y border-r border-gray-400 bg-white p-4">
          {/* 주의사항 */}
          <div className="mb-4">
            <h3 className="mb-2 font-medium text-sm">마감시 주의사항</h3>
            <div className="space-y-2 text-xs text-gray-600">
              <p>현재 사용중인 사업장을 마감하기 위한 설정을 합니다.</p>
              <p>마감을 하게되면 모든 거래 데이터가 삭제된후</p>
              <p>자동으로 이월작업이 실행됩니다.</p>
              <p className="mt-2">마감전 원가재계산으로 정확히 계산한뒤 사용하시면</p>
              <p>더 정확하게 이월작업이 이루어집니다.</p>
              <p className="mt-2">마감전까지 모든 거래 정보 백업이 자동으로</p>
              <p>생성되므로 언제든지 다시 확인할 수 있습니다.</p>
            </div>
          </div>

          {/* 마감설정 */}
          <fieldset className="mb-4 rounded border border-gray-400 p-3">
            <legend className="px-2 text-sm font-medium">마감설정</legend>
            <div className="flex items-center gap-2">
              <span className="text-sm">마감할 월:</span>
              <select
                value={closeYear}
                onChange={(e) => setCloseYear(e.target.value)}
                className="rounded border border-gray-400 px-2 py-1 text-sm"
              >
                <option value="2024">2024</option>
                <option value="2025">2025</option>
                <option value="2026">2026</option>
              </select>
              <span className="text-sm">년</span>
              <select
                value={closeMonth}
                onChange={(e) => setCloseMonth(e.target.value)}
                className="rounded border border-gray-400 px-2 py-1 text-sm"
              >
                {Array.from({ length: 12 }, (_, i) => (
                  <option key={i + 1} value={String(i + 1)}>
                    {i + 1}
                  </option>
                ))}
              </select>
              <span className="text-sm">월</span>
            </div>
            <div className="mt-3 space-y-2">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={deleteAfterClose}
                  onChange={(e) => setDeleteAfterClose(e.target.checked)}
                />
                마감월 이후의 데이터 삭제
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={deleteOrderQuote}
                  onChange={(e) => setDeleteOrderQuote(e.target.checked)}
                />
                발주서/견적서 데이터 삭제
              </label>
            </div>
          </fieldset>

          {/* 버튼 */}
          <div className="flex justify-end gap-2">
            <button
              onClick={handleStartClose}
              disabled={isProcessing}
              className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200 disabled:opacity-50"
            >
              {isProcessing ? "처리중..." : "마감작업 시작(S)"}
            </button>
            <button
              onClick={handleCancel}
              disabled={isProcessing}
              className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200 disabled:opacity-50"
            >
              취소(Esc)
            </button>
          </div>
        </div>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        {isProcessing ? "마감 작업 처리 중..." : "loading ok"}
      </div>
    </div>
  );
}
