'use client';

import React, { useState } from 'react';

interface DebtCreditItem {
  id: string;
  debtCreditType: string; // 채권/채무
  category: string; // 구분 (채권이월/채무이월)
  relatedItemCode: string;
  relatedItemName: string;
  carryoverAmount: number;
  carryoverDate: string;
}

interface DebtCreditCarryoverWindowProps {
  onClose: () => void;
}

// 관련항목 검색용 샘플 데이터
const SAMPLE_RELATED_ITEMS = [
  { code: 'm001', name: '테스트사업장', type: '거래처' },
  { code: 'm002', name: '이지사업장', type: '거래처' },
  { code: 'm003', name: '재고사업장', type: '거래처' },
  { code: 'p001', name: '핸드폰케이스', type: '상품' },
  { code: 'p002', name: '노트북케이스', type: '상품' },
  { code: 'b001', name: '국민은행 123-456', type: '계좌' },
  { code: 'b002', name: '신한은행 789-012', type: '계좌' },
];

export default function DebtCreditCarryoverWindow({ onClose }: DebtCreditCarryoverWindowProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [items, setItems] = useState<DebtCreditItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<DebtCreditItem | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editMode, setEditMode] = useState<'add' | 'edit'>('add');

  // 관련항목 검색 모달 상태
  const [showSearchModal, setShowSearchModal] = useState(false);
  const [relatedSearchTerm, setRelatedSearchTerm] = useState('');

  // 모달 폼 상태 - 이지판매재고관리 필드 복제
  const [formData, setFormData] = useState({
    category: '채권이월',
    groupName: '',
    relatedItem: '',
    relatedItemCode: '',
    carryoverAmount: 0,
    carryoverDate: '2025-12-05',
  });

  // 구분 드롭다운 옵션 - 이지판매재고관리 원본 복제
  const categoryOptions = ['채권이월', '채무이월'];

  const filteredItems = items.filter(item =>
    item.category.includes(searchTerm) || item.relatedItemName.includes(searchTerm)
  );

  const handleSearch = () => {
    // 검색 실행
  };

  const handleAdd = () => {
    setEditMode('add');
    setFormData({
      category: '채권이월',
      groupName: '',
      relatedItem: '',
      relatedItemCode: '',
      carryoverAmount: 0,
      carryoverDate: '2025-12-05',
    });
    setShowModal(true);
  };

  const handleEdit = () => {
    if (!selectedItem) return;
    setEditMode('edit');
    setFormData({
      category: selectedItem.category,
      groupName: '',
      relatedItem: selectedItem.relatedItemName,
      relatedItemCode: selectedItem.relatedItemCode,
      carryoverAmount: selectedItem.carryoverAmount,
      carryoverDate: selectedItem.carryoverDate,
    });
    setShowModal(true);
  };

  const handleDelete = () => {
    if (!selectedItem) return;
    if (confirm('선택한 항목을 삭제하시겠습니까?')) {
      setItems(items.filter(item => item.id !== selectedItem.id));
      setSelectedItem(null);
    }
  };

  const handleRefresh = () => {
    // 새로고침
  };

  const handleSave = () => {
    const debtCreditType = formData.category === '채권이월' ? '채권' : '채무';

    if (editMode === 'add') {
      const newItem: DebtCreditItem = {
        id: Date.now().toString(),
        debtCreditType: debtCreditType,
        category: formData.category,
        relatedItemCode: formData.relatedItemCode,
        relatedItemName: formData.relatedItem,
        carryoverAmount: formData.carryoverAmount,
        carryoverDate: formData.carryoverDate,
      };
      setItems([...items, newItem]);
    } else {
      setItems(items.map(item =>
        item.id === selectedItem?.id
          ? {
              ...item,
              debtCreditType: debtCreditType,
              category: formData.category,
              relatedItemCode: formData.relatedItemCode,
              relatedItemName: formData.relatedItem,
              carryoverAmount: formData.carryoverAmount,
              carryoverDate: formData.carryoverDate,
            }
          : item
      ));
    }
    setShowModal(false);
  };

  const handleCancel = () => {
    setShowModal(false);
  };

  const handleRelatedItemSearch = () => {
    // 관련항목 검색 팝업 열기
    setRelatedSearchTerm('');
    setShowSearchModal(true);
  };

  // 관련항목 선택 핸들러
  const handleSelectRelatedItem = (item: { code: string; name: string; type: string }) => {
    setFormData({
      ...formData,
      relatedItemCode: item.code,
      relatedItem: item.name,
    });
    setShowSearchModal(false);
  };

  // 관련항목 필터링
  const filteredRelatedItems = SAMPLE_RELATED_ITEMS.filter(item =>
    item.name.includes(relatedSearchTerm) || item.code.includes(relatedSearchTerm)
  );

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
        <label className="text-sm font-medium text-gray-700">구분명:</label>
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
              <th className="border border-gray-300 px-3 py-2 text-left text-sm font-medium text-gray-700 w-24">채권/채무</th>
              <th className="border border-gray-300 px-3 py-2 text-left text-sm font-medium text-gray-700 w-28">구분</th>
              <th className="border border-gray-300 px-3 py-2 text-left text-sm font-medium text-gray-700 w-32">관련항목코드</th>
              <th className="border border-gray-300 px-3 py-2 text-left text-sm font-medium text-gray-700 w-40">관련항목명</th>
              <th className="border border-gray-300 px-3 py-2 text-right text-sm font-medium text-gray-700 w-32">이월금액</th>
              <th className="border border-gray-300 px-3 py-2 text-left text-sm font-medium text-gray-700 w-32">이월일자</th>
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
                <td className="border border-gray-300 px-3 py-1.5 text-sm">{item.debtCreditType}</td>
                <td className="border border-gray-300 px-3 py-1.5 text-sm">{item.category}</td>
                <td className="border border-gray-300 px-3 py-1.5 text-sm">{item.relatedItemCode}</td>
                <td className="border border-gray-300 px-3 py-1.5 text-sm">{item.relatedItemName}</td>
                <td className="border border-gray-300 px-3 py-1.5 text-sm text-right">{formatNumber(item.carryoverAmount)}</td>
                <td className="border border-gray-300 px-3 py-1.5 text-sm">{item.carryoverDate}</td>
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
              <span className="text-sm font-medium">채권/채무이월</span>
              <button onClick={handleCancel} className="text-gray-600 hover:text-gray-800">×</button>
            </div>

            {/* 모달 바디 */}
            <div className="p-4 space-y-4">
              {/* 이월정보 섹션 */}
              <div>
                <div className="text-sm font-medium text-blue-600 mb-2">이월정보</div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <label className="w-20 text-sm text-right">구분:</label>
                    <select
                      value={formData.category}
                      onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                      className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                    >
                      {categoryOptions.map(option => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-20 text-sm text-right">그룹명:</label>
                    <input
                      type="text"
                      value={formData.groupName}
                      onChange={(e) => setFormData({ ...formData, groupName: e.target.value })}
                      className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-20 text-sm text-right">관련항목:</label>
                    <input
                      type="text"
                      value={formData.relatedItem}
                      onChange={(e) => setFormData({ ...formData, relatedItem: e.target.value })}
                      className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                    <button
                      onClick={handleRelatedItemSearch}
                      className="px-2 py-1 bg-gray-100 border border-gray-300 rounded text-sm"
                    >
                      ...
                    </button>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-20 text-sm text-right">이월금액:</label>
                    <input
                      type="text"
                      value={formData.carryoverAmount}
                      onChange={(e) => setFormData({ ...formData, carryoverAmount: parseInt(e.target.value.replace(/,/g, '')) || 0 })}
                      className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm text-right"
                    />
                  </div>
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
                <div className="text-xs text-gray-500 mt-2">채권/채무 이월 정보를 등록합니다.</div>
              </div>
            </div>

            {/* 모달 푸터 */}
            <div className="flex items-center justify-end px-4 py-3 bg-gray-100 rounded-b gap-2">
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
      )}

      {/* 관련항목 검색 모달 */}
      {showSearchModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60]">
          <div className="bg-white rounded shadow-lg w-80">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between px-3 py-2 bg-gray-200 rounded-t">
              <span className="text-sm font-medium">관련항목 검색</span>
              <button
                onClick={() => setShowSearchModal(false)}
                className="text-gray-600 hover:text-gray-800"
              >
                ×
              </button>
            </div>

            {/* 검색 입력 */}
            <div className="p-3 border-b">
              <input
                type="text"
                value={relatedSearchTerm}
                onChange={(e) => setRelatedSearchTerm(e.target.value)}
                placeholder="코드 또는 이름으로 검색..."
                className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoFocus
              />
            </div>

            {/* 검색 결과 목록 */}
            <div className="max-h-60 overflow-y-auto">
              {filteredRelatedItems.map((item) => (
                <div
                  key={item.code}
                  onClick={() => handleSelectRelatedItem(item)}
                  className="flex items-center gap-2 px-3 py-2 hover:bg-blue-50 cursor-pointer border-b border-gray-100"
                >
                  <span className="text-xs px-1.5 py-0.5 bg-gray-200 rounded">{item.type}</span>
                  <span className="text-sm text-gray-500">{item.code}</span>
                  <span className="text-sm font-medium">{item.name}</span>
                </div>
              ))}
              {filteredRelatedItems.length === 0 && (
                <div className="px-3 py-4 text-center text-sm text-gray-500">
                  검색 결과가 없습니다.
                </div>
              )}
            </div>

            {/* 모달 푸터 */}
            <div className="flex items-center justify-end px-3 py-2 bg-gray-100 rounded-b">
              <button
                onClick={() => setShowSearchModal(false)}
                className="px-4 py-1.5 bg-gray-200 border border-gray-300 rounded text-sm hover:bg-gray-300"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
