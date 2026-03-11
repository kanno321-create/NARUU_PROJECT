'use client';

import React, { useState, useEffect } from 'react';

interface CashBalanceCarryoverWindowProps {
  onClose: () => void;
}

export default function CashBalanceCarryoverWindow({ onClose }: CashBalanceCarryoverWindowProps) {
  // 이월정보 상태 - 이지판매재고관리 필드 복제
  const [formData, setFormData] = useState({
    carryoverAmount: 0,
    carryoverDate: '2025-12-05',
  });

  // 저장된 데이터 로드
  useEffect(() => {
    const savedData = localStorage.getItem('erp_cash_balance_carryover');
    if (savedData) {
      const parsed = JSON.parse(savedData);
      setFormData(parsed);
    }
  }, []);

  const handleSave = () => {
    // localStorage에 저장
    localStorage.setItem('erp_cash_balance_carryover', JSON.stringify(formData));
    alert('현금 잔고 이월정보가 저장되었습니다.');
    onClose();
  };

  const handleCancel = () => {
    onClose();
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  return (
    <div className="flex flex-col h-full bg-gray-200 p-4">
      {/* 이월정보 섹션 - 이지판매재고관리 레이아웃 복제 */}
      <div className="mb-4">
        <div className="text-sm font-medium text-blue-600 mb-3">이월정보</div>
        <div className="space-y-3">
          {/* 이월금액 */}
          <div className="flex items-center gap-2">
            <label className="w-20 text-sm text-right">이월금액:</label>
            <input
              type="text"
              value={formatNumber(formData.carryoverAmount)}
              onChange={(e) => {
                const value = parseInt(e.target.value.replace(/,/g, '')) || 0;
                setFormData({ ...formData, carryoverAmount: value });
              }}
              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm text-right"
            />
          </div>

          {/* 이월일자 */}
          <div className="flex items-center gap-2">
            <label className="w-20 text-sm text-right">이월일자:</label>
            <input
              type="date"
              value={formData.carryoverDate}
              onChange={(e) => setFormData({ ...formData, carryoverDate: e.target.value })}
              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
            />
          </div>
        </div>
      </div>

      {/* 설명 텍스트 */}
      <div className="text-xs text-gray-500 mb-4">현금 잔고의 이월정보를 등록합니다.</div>

      {/* 버튼 영역 */}
      <div className="flex items-center justify-end gap-2 mt-auto">
        <button
          onClick={handleSave}
          className="px-6 py-1.5 bg-gray-100 border border-gray-400 rounded text-sm hover:bg-gray-200"
        >
          저 장
        </button>
        <button
          onClick={handleCancel}
          className="px-6 py-1.5 bg-gray-100 border border-gray-400 rounded text-sm hover:bg-gray-200"
        >
          취 소
        </button>
      </div>
    </div>
  );
}
