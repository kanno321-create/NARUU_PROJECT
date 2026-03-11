'use client';

import React, { useState } from 'react';

interface ReceivablePayableItem {
  id: string;
  companyCode: string;
  companyName: string;
  carryoverDate: string;
  receivable: number;
  payable: number;
}

interface ReceivablePayableCarryoverWindowProps {
  onClose: () => void;
}

export default function ReceivablePayableCarryoverWindow({ onClose }: ReceivablePayableCarryoverWindowProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDate, setSelectedDate] = useState('2025-12-05');

  // 이지판매재고관리 원본 데이터 그대로 복제
  const [items, setItems] = useState<ReceivablePayableItem[]>([
    { id: '1', companyCode: 'm001', companyName: '테스트사업장', carryoverDate: '2025-12-05', receivable: 1500000, payable: 0 },
    { id: '2', companyCode: 'm002', companyName: '이지사업장', carryoverDate: '2025-12-05', receivable: 0, payable: 21312 },
    { id: '3', companyCode: 'm003', companyName: '재고사업장', carryoverDate: '2025-12-05', receivable: 750000, payable: 0 },
  ]);

  const [selectedItem, setSelectedItem] = useState<ReceivablePayableItem | null>(null);

  const filteredItems = items.filter(item =>
    item.companyName.includes(searchTerm) || item.companyCode.includes(searchTerm)
  );

  const handleSearch = () => {
    // 검색 실행
  };

  const handleApplyDateToAll = () => {
    setItems(items.map(item => ({ ...item, carryoverDate: selectedDate })));
  };

  const handleCellEdit = (id: string, field: 'receivable' | 'payable', value: number) => {
    setItems(items.map(item =>
      item.id === id ? { ...item, [field]: value } : item
    ));
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* 상단 검색/필터 영역 - 이지판매재고관리 레이아웃 복제 */}
      <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-b from-gray-100 to-gray-200 border-b">
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-gray-700">업체명:</label>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-48 px-3 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder=""
          />
          <button
            onClick={handleSearch}
            className="px-4 py-1.5 bg-gray-100 border border-gray-300 rounded text-sm hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            검 색(F)
          </button>
        </div>

        <div className="flex items-center gap-3">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="px-3 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleApplyDateToAll}
            className="px-4 py-1.5 bg-gray-100 border border-gray-300 rounded text-sm hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            날짜전체입력
          </button>
        </div>
      </div>

      {/* 데이터 그리드 - 이지판매재고관리 컬럼 구조 복제 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse">
          <thead className="bg-blue-100 sticky top-0">
            <tr>
              <th className="border border-gray-300 px-3 py-2 text-left text-sm font-medium text-gray-700 w-24">업체코드</th>
              <th className="border border-gray-300 px-3 py-2 text-left text-sm font-medium text-gray-700 w-40">업체명</th>
              <th className="border border-gray-300 px-3 py-2 text-left text-sm font-medium text-gray-700 w-32">이월일자</th>
              <th className="border border-gray-300 px-3 py-2 text-right text-sm font-medium text-gray-700 w-32">미수금</th>
              <th className="border border-gray-300 px-3 py-2 text-right text-sm font-medium text-gray-700 w-32">미지급금</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.map((item, index) => (
              <tr
                key={item.id}
                className={`${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'} hover:bg-blue-50 cursor-pointer ${selectedItem?.id === item.id ? 'bg-blue-100' : ''}`}
                onClick={() => setSelectedItem(item)}
              >
                <td className="border border-gray-300 px-3 py-1.5 text-sm">{item.companyCode}</td>
                <td className="border border-gray-300 px-3 py-1.5 text-sm">{item.companyName}</td>
                <td className="border border-gray-300 px-3 py-1.5 text-sm">{item.carryoverDate}</td>
                <td className="border border-gray-300 px-3 py-1.5 text-sm text-right">
                  <input
                    type="text"
                    value={formatNumber(item.receivable)}
                    onChange={(e) => {
                      const value = parseInt(e.target.value.replace(/,/g, '')) || 0;
                      handleCellEdit(item.id, 'receivable', value);
                    }}
                    className="w-full text-right bg-transparent border-none focus:outline-none focus:bg-white focus:border focus:border-blue-500 px-1"
                  />
                </td>
                <td className="border border-gray-300 px-3 py-1.5 text-sm text-right">
                  <input
                    type="text"
                    value={formatNumber(item.payable)}
                    onChange={(e) => {
                      const value = parseInt(e.target.value.replace(/,/g, '')) || 0;
                      handleCellEdit(item.id, 'payable', value);
                    }}
                    className={`w-full text-right bg-transparent border-none focus:outline-none focus:bg-white focus:border focus:border-blue-500 px-1 ${item.payable === 0 ? 'text-blue-600' : ''}`}
                  />
                </td>
              </tr>
            ))}
            {/* 빈 행들 추가 - 이지판매재고관리 스타일 */}
            {Array.from({ length: Math.max(0, 20 - filteredItems.length) }).map((_, index) => (
              <tr key={`empty-${index}`} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                <td className="border border-gray-300 px-3 py-1.5 text-sm">&nbsp;</td>
                <td className="border border-gray-300 px-3 py-1.5 text-sm">&nbsp;</td>
                <td className="border border-gray-300 px-3 py-1.5 text-sm">&nbsp;</td>
                <td className="border border-gray-300 px-3 py-1.5 text-sm">&nbsp;</td>
                <td className="border border-gray-300 px-3 py-1.5 text-sm">&nbsp;</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 하단 합계 영역 */}
      <div className="px-4 py-2 bg-gray-100 border-t flex justify-end gap-6 text-sm">
        <span>미수금 합계: <strong className="text-blue-600">{formatNumber(items.reduce((sum, item) => sum + item.receivable, 0))}원</strong></span>
        <span>미지급금 합계: <strong className="text-red-600">{formatNumber(items.reduce((sum, item) => sum + item.payable, 0))}원</strong></span>
      </div>
    </div>
  );
}
