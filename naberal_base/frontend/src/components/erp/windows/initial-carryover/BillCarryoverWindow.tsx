'use client';

import React, { useState } from 'react';

interface BillItem {
  id: string;
  billNumber: string;
  billType: string;
  faceValue: number;
  dueDate: string;
  receiverPayer: string;
  receiveDate: string;
}

interface BillCarryoverWindowProps {
  onClose: () => void;
}

export default function BillCarryoverWindow({ onClose }: BillCarryoverWindowProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [items, setItems] = useState<BillItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<BillItem | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editMode, setEditMode] = useState<'add' | 'edit'>('add');

  // 모달 폼 상태 - 이지판매재고관리 필드 복제
  const [formData, setFormData] = useState({
    billType: '받을어음',
    billNumber: '',
    amount: 0,
    relatedCustomer: '',
    dueDate: '2025-12-05',
    carryoverDate: '2025-12-05',
  });

  // 어음구분 드롭다운 옵션 - 이지판매재고관리 원본 복제
  const billTypeOptions = ['받을어음', '지급어음'];

  const filteredItems = items.filter(item =>
    item.billNumber.includes(searchTerm)
  );

  const handleSearch = () => {
    // 검색 실행
  };

  const handleAdd = () => {
    setEditMode('add');
    setFormData({
      billType: '받을어음',
      billNumber: '',
      amount: 0,
      relatedCustomer: '',
      dueDate: '2025-12-05',
      carryoverDate: '2025-12-05',
    });
    setShowModal(true);
  };

  const handleEdit = () => {
    if (!selectedItem) return;
    setEditMode('edit');
    setFormData({
      billType: selectedItem.billType,
      billNumber: selectedItem.billNumber,
      amount: selectedItem.faceValue,
      relatedCustomer: selectedItem.receiverPayer,
      dueDate: selectedItem.dueDate,
      carryoverDate: selectedItem.receiveDate,
    });
    setShowModal(true);
  };

  const handleDelete = () => {
    if (!selectedItem) return;
    if (confirm('선택한 어음을 삭제하시겠습니까?')) {
      setItems(items.filter(item => item.id !== selectedItem.id));
      setSelectedItem(null);
    }
  };

  const handleRefresh = () => {
    // 새로고침
  };

  const handleSave = () => {
    if (editMode === 'add') {
      const newItem: BillItem = {
        id: Date.now().toString(),
        billNumber: formData.billNumber,
        billType: formData.billType,
        faceValue: formData.amount,
        dueDate: formData.dueDate,
        receiverPayer: formData.relatedCustomer,
        receiveDate: formData.carryoverDate,
      };
      setItems([...items, newItem]);
    } else {
      setItems(items.map(item =>
        item.id === selectedItem?.id
          ? {
              ...item,
              billNumber: formData.billNumber,
              billType: formData.billType,
              faceValue: formData.amount,
              dueDate: formData.dueDate,
              receiverPayer: formData.relatedCustomer,
              receiveDate: formData.carryoverDate,
            }
          : item
      ));
    }
    setShowModal(false);
  };

  const handleCancel = () => {
    setShowModal(false);
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* 상단 툴바 - 이지판매재고관리 레이아웃 복제 */}
      <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-b from-gray-100 to-gray-200 border-b">
        <button
          onClick={handleAdd}
          className="flex items-center gap-1 px-3 py-1.5 bg-white border border-gray-300 rounded text-sm hover:bg-gray-50"
        >
          <span className="w-5 h-5 flex items-center justify-center rounded-full bg-green-500 text-white text-xs">+</span>
          추가
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-1 px-3 py-1.5 bg-white border border-gray-300 rounded text-sm hover:bg-gray-50"
          disabled={!selectedItem}
        >
          <span className="w-5 h-5 flex items-center justify-center rounded-full bg-blue-500 text-white text-xs">✓</span>
          수정
        </button>
        <button
          onClick={handleDelete}
          className="flex items-center gap-1 px-3 py-1.5 bg-white border border-gray-300 rounded text-sm hover:bg-gray-50"
          disabled={!selectedItem}
        >
          <span className="w-5 h-5 flex items-center justify-center rounded-full bg-red-500 text-white text-xs">×</span>
          삭제
        </button>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-1 px-3 py-1.5 bg-white border border-gray-300 rounded text-sm hover:bg-gray-50"
        >
          <span className="w-5 h-5 flex items-center justify-center text-gray-500">↻</span>
          새로고침
        </button>
      </div>

      {/* 검색 영역 */}
      <div className="flex items-center gap-3 px-4 py-2 bg-gray-100 border-b">
        <label className="text-sm font-medium text-gray-700">어음번호:</label>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-48 px-3 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleSearch}
          className="px-4 py-1.5 bg-gray-100 border border-gray-300 rounded text-sm hover:bg-gray-200"
        >
          검 색(F)
        </button>
      </div>

      {/* 데이터 그리드 - 이지판매재고관리 컬럼 구조 복제 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse">
          <thead className="bg-blue-100 sticky top-0">
            <tr>
              <th className="border border-gray-300 px-3 py-2 text-left text-sm font-medium text-gray-700 w-32">어음번호</th>
              <th className="border border-gray-300 px-3 py-2 text-left text-sm font-medium text-gray-700 w-28">어음구분</th>
              <th className="border border-gray-300 px-3 py-2 text-right text-sm font-medium text-gray-700 w-32">액면가</th>
              <th className="border border-gray-300 px-3 py-2 text-left text-sm font-medium text-gray-700 w-32">어음만기일</th>
              <th className="border border-gray-300 px-3 py-2 text-left text-sm font-medium text-gray-700 w-40">수취/지급처</th>
              <th className="border border-gray-300 px-3 py-2 text-left text-sm font-medium text-gray-700 w-32">수취일</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.map((item, index) => (
              <tr
                key={item.id}
                className={`${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'} hover:bg-blue-50 cursor-pointer ${selectedItem?.id === item.id ? 'bg-blue-100' : ''}`}
                onClick={() => setSelectedItem(item)}
                onDoubleClick={handleEdit}
              >
                <td className="border border-gray-300 px-3 py-1.5 text-sm">{item.billNumber}</td>
                <td className="border border-gray-300 px-3 py-1.5 text-sm">{item.billType}</td>
                <td className="border border-gray-300 px-3 py-1.5 text-sm text-right">{formatNumber(item.faceValue)}</td>
                <td className="border border-gray-300 px-3 py-1.5 text-sm">{item.dueDate}</td>
                <td className="border border-gray-300 px-3 py-1.5 text-sm">{item.receiverPayer}</td>
                <td className="border border-gray-300 px-3 py-1.5 text-sm">{item.receiveDate}</td>
              </tr>
            ))}
            {/* 빈 행들 추가 */}
            {Array.from({ length: Math.max(0, 15 - filteredItems.length) }).map((_, index) => (
              <tr key={`empty-${index}`} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                <td className="border border-gray-300 px-3 py-1.5 text-sm">&nbsp;</td>
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

      {/* 모달 다이얼로그 - 이지판매재고관리 레이아웃 복제 */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-200 rounded shadow-lg w-96">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between px-3 py-2 bg-gray-300 rounded-t">
              <span className="text-sm font-medium">어음 이월</span>
              <button onClick={handleCancel} className="text-gray-600 hover:text-gray-800">×</button>
            </div>

            {/* 모달 바디 */}
            <div className="p-4 space-y-4">
              {/* 어음정보 섹션 */}
              <div>
                <div className="text-sm font-medium text-blue-600 mb-2">어음정보</div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <label className="w-20 text-sm text-right">어음구분:</label>
                    <select
                      value={formData.billType}
                      onChange={(e) => setFormData({ ...formData, billType: e.target.value })}
                      className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                    >
                      {billTypeOptions.map(option => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-20 text-sm text-right">어음번호:</label>
                    <input
                      type="text"
                      value={formData.billNumber}
                      onChange={(e) => setFormData({ ...formData, billNumber: e.target.value })}
                      className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-20 text-sm text-right">금액:</label>
                    <input
                      type="text"
                      value={formData.amount}
                      onChange={(e) => setFormData({ ...formData, amount: parseInt(e.target.value.replace(/,/g, '')) || 0 })}
                      className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm text-right"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-20 text-sm text-right">관련거래처:</label>
                    <input
                      type="text"
                      value={formData.relatedCustomer}
                      onChange={(e) => setFormData({ ...formData, relatedCustomer: e.target.value })}
                      className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                    <button className="px-2 py-1 bg-gray-100 border border-gray-300 rounded text-sm">...</button>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-20 text-sm text-right">만기일:</label>
                    <input
                      type="date"
                      value={formData.dueDate}
                      onChange={(e) => setFormData({ ...formData, dueDate: e.target.value })}
                      className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                  </div>
                </div>
                <div className="text-xs text-gray-500 mt-2">이월할 어음의 정보를 등록합니다.</div>
              </div>

              {/* 이월정보 섹션 */}
              <div>
                <div className="text-sm font-medium text-blue-600 mb-2">이월정보</div>
                <div className="flex items-center gap-2">
                  <label className="w-20 text-sm text-right">이월 일자:</label>
                  <input
                    type="date"
                    value={formData.carryoverDate}
                    onChange={(e) => setFormData({ ...formData, carryoverDate: e.target.value })}
                    className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                  />
                </div>
              </div>
            </div>

            {/* 모달 푸터 */}
            <div className="flex items-center justify-between px-4 py-3 bg-gray-100 rounded-b">
              <button className="text-sm text-blue-600 underline">관련항목&gt;&gt;</button>
              <div className="flex gap-2">
                <button
                  onClick={handleSave}
                  className="px-6 py-1.5 bg-gray-200 border border-gray-400 rounded text-sm hover:bg-gray-300"
                >
                  저 장
                </button>
                <button
                  onClick={handleCancel}
                  className="px-6 py-1.5 bg-gray-200 border border-gray-400 rounded text-sm hover:bg-gray-300"
                >
                  취 소
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
