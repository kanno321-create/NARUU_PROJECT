"use client";

import React, { useState } from "react";

interface ProductPriceItem {
  id: string;
  productCode: string;
  productName: string;
  category: string;
  spec: string;
  unit: string;
  purchasePrice: number;
  salesPrice: number;
  marginRate: number;
  lastUpdated: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: ProductPriceItem[] = [
  {
    id: "1",
    productCode: "e0001",
    productName: "핸드폰케이스",
    category: "전자제품",
    spec: "10×10",
    unit: "EA",
    purchasePrice: 10000,
    salesPrice: 15000,
    marginRate: 33.3,
    lastUpdated: "2025-12-01",
  },
  {
    id: "2",
    productCode: "e0002",
    productName: "노트북케이스",
    category: "전자제품",
    spec: "20×25",
    unit: "EA",
    purchasePrice: 15000,
    salesPrice: 25000,
    marginRate: 40,
    lastUpdated: "2025-12-01",
  },
  {
    id: "3",
    productCode: "e0003",
    productName: "키보드케이스",
    category: "전자제품",
    spec: "300×400",
    unit: "EA",
    purchasePrice: 4500,
    salesPrice: 8000,
    marginRate: 43.8,
    lastUpdated: "2025-12-01",
  },
  {
    id: "4",
    productCode: "p001",
    productName: "원자재A",
    category: "원자재",
    spec: "100×50",
    unit: "KG",
    purchasePrice: 1000,
    salesPrice: 1500,
    marginRate: 33.3,
    lastUpdated: "2025-11-15",
  },
  {
    id: "5",
    productCode: "p002",
    productName: "원자재B",
    category: "원자재",
    spec: "200×100",
    unit: "KG",
    purchasePrice: 2000,
    salesPrice: 3000,
    marginRate: 33.3,
    lastUpdated: "2025-11-15",
  },
];

export function ProductPriceEdit() {
  const [productSearch, setProductSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("전체");
  const [data, setData] = useState<ProductPriceItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState<ProductPriceItem | null>(null);

  const categories = ["전체", ...new Set(data.map((d) => d.category))];

  const filteredData = data.filter(
    (item) =>
      (productSearch === "" ||
        item.productCode.includes(productSearch) ||
        item.productName.includes(productSearch)) &&
      (categoryFilter === "전체" || item.category === categoryFilter)
  );

  const handleEdit = () => {
    const item = data.find((d) => d.id === selectedId);
    if (item) {
      setEditItem({ ...item });
      setShowModal(true);
    }
  };

  const handleSave = () => {
    if (editItem) {
      // 마진율 자동 계산
      const margin = editItem.salesPrice - editItem.purchasePrice;
      const marginRate = editItem.salesPrice > 0 ? (margin / editItem.salesPrice) * 100 : 0;
      const updatedItem = {
        ...editItem,
        marginRate: Math.round(marginRate * 10) / 10,
        lastUpdated: new Date().toISOString().split("T")[0],
      };
      setData(data.map((d) => (d.id === updatedItem.id ? updatedItem : d)));
      setShowModal(false);
      setEditItem(null);
    }
  };

  const handleBulkUpdate = (rate: number) => {
    // 선택된 항목 또는 전체에 대해 일괄 단가 조정
    const confirmed = window.confirm(`전체 상품의 판매단가를 ${rate}% 조정하시겠습니까?`);
    if (confirmed) {
      setData(
        data.map((item) => ({
          ...item,
          salesPrice: Math.round(item.salesPrice * (1 + rate / 100)),
          lastUpdated: new Date().toISOString().split("T")[0],
        }))
      );
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">상품별단가수정</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
          <span>✏️</span> 수정
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button
          onClick={() => handleBulkUpdate(5)}
          className="flex items-center gap-1 rounded border border-gray-400 bg-yellow-100 px-2 py-0.5 text-xs hover:bg-yellow-200"
        >
          <span>📈</span> 일괄인상(5%)
        </button>
        <button
          onClick={() => handleBulkUpdate(-5)}
          className="flex items-center gap-1 rounded border border-gray-400 bg-yellow-100 px-2 py-0.5 text-xs hover:bg-yellow-200"
        >
          <span>📉</span> 일괄인하(5%)
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 엑셀변환
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📥</span> 엑셀가져오기
        </button>
      </div>

      {/* 검색 조건 */}
      <div className="flex items-center gap-4 border-b bg-white px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="text-xs">분류:</span>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            {categories.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">상품검색:</span>
          <input
            type="text"
            value={productSearch}
            onChange={(e) => setProductSearch(e.target.value)}
            placeholder="상품명/코드"
            className="w-32 rounded border border-gray-400 px-2 py-1 text-xs"
          />
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색
        </button>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-20">상품코드</th>
              <th className="border border-gray-400 px-2 py-1 w-28">상품명</th>
              <th className="border border-gray-400 px-2 py-1 w-20">분류</th>
              <th className="border border-gray-400 px-2 py-1 w-20">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-12">단위</th>
              <th className="border border-gray-400 px-2 py-1 w-24">매입단가</th>
              <th className="border border-gray-400 px-2 py-1 w-24">판매단가</th>
              <th className="border border-gray-400 px-2 py-1 w-16">마진율(%)</th>
              <th className="border border-gray-400 px-2 py-1">최종수정일</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr
                key={item.id}
                className={`cursor-pointer ${
                  selectedId === item.id
                    ? "bg-[#316AC5] text-white"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
                onDoubleClick={handleEdit}
              >
                <td className="border border-gray-300 px-2 py-1">{item.productCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.productName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.category}</td>
                <td className="border border-gray-300 px-2 py-1">{item.spec}</td>
                <td className="border border-gray-300 px-2 py-1">{item.unit}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.purchasePrice.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600 font-medium">
                  {item.salesPrice.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right ${
                  item.marginRate >= 30 ? "text-green-600" : "text-red-600"
                }`}>
                  {item.marginRate}%
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.lastUpdated}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredData.length}건 | loading ok
      </div>

      {/* 수정 모달 */}
      {showModal && editItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-[400px] bg-white shadow-lg">
            <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">상품단가 수정</span>
              <button onClick={() => setShowModal(false)} className="text-white hover:text-gray-200">✕</button>
            </div>
            <div className="p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs mb-1">상품코드</label>
                  <input
                    type="text"
                    value={editItem.productCode}
                    disabled
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs bg-gray-100"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">상품명</label>
                  <input
                    type="text"
                    value={editItem.productName}
                    disabled
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs bg-gray-100"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">매입단가 *</label>
                  <input
                    type="number"
                    value={editItem.purchasePrice}
                    onChange={(e) => setEditItem({ ...editItem, purchasePrice: Number(e.target.value) })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">판매단가 *</label>
                  <input
                    type="number"
                    value={editItem.salesPrice}
                    onChange={(e) => setEditItem({ ...editItem, salesPrice: Number(e.target.value) })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
              </div>
              <div className="bg-yellow-50 p-2 rounded text-xs">
                <span className="font-medium">예상 마진율: </span>
                <span className={editItem.salesPrice > editItem.purchasePrice ? "text-green-600" : "text-red-600"}>
                  {editItem.salesPrice > 0
                    ? Math.round(((editItem.salesPrice - editItem.purchasePrice) / editItem.salesPrice) * 1000) / 10
                    : 0}%
                </span>
              </div>
            </div>
            <div className="flex justify-end gap-2 border-t bg-gray-100 px-4 py-2">
              <button
                onClick={handleSave}
                className="rounded border border-gray-400 bg-blue-500 px-4 py-1 text-xs text-white hover:bg-blue-600"
              >
                저장
              </button>
              <button
                onClick={() => setShowModal(false)}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200"
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
