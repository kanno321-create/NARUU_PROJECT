"use client";

import React, { useState } from "react";

interface ProductDiscountItem {
  id: string;
  productCode: string;
  productName: string;
  category: string;
  discountRate: number;
  applyFrom: string;
  applyTo: string;
  minQty: number;
  status: string;
  memo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: ProductDiscountItem[] = [
  {
    id: "1",
    productCode: "e0001",
    productName: "핸드폰케이스",
    category: "전자제품",
    discountRate: 10,
    applyFrom: "2025-12-01",
    applyTo: "2025-12-31",
    minQty: 10,
    status: "적용중",
    memo: "연말 프로모션",
  },
  {
    id: "2",
    productCode: "e0002",
    productName: "노트북케이스",
    category: "전자제품",
    discountRate: 15,
    applyFrom: "2025-12-01",
    applyTo: "2025-12-31",
    minQty: 5,
    status: "적용중",
    memo: "연말 프로모션",
  },
  {
    id: "3",
    productCode: "e0003",
    productName: "키보드케이스",
    category: "전자제품",
    discountRate: 20,
    applyFrom: "2025-11-01",
    applyTo: "2025-11-30",
    minQty: 20,
    status: "만료",
    memo: "재고정리 할인",
  },
  {
    id: "4",
    productCode: "p001",
    productName: "원자재A",
    category: "원자재",
    discountRate: 5,
    applyFrom: "2025-01-01",
    applyTo: "2025-12-31",
    minQty: 100,
    status: "적용중",
    memo: "대량구매 할인",
  },
];

export function ProductDiscount() {
  const [productSearch, setProductSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("전체");
  const [data, setData] = useState<ProductDiscountItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState<ProductDiscountItem | null>(null);
  const [isNew, setIsNew] = useState(false);

  const filteredData = data.filter(
    (item) =>
      (productSearch === "" ||
        item.productCode.includes(productSearch) ||
        item.productName.includes(productSearch)) &&
      (statusFilter === "전체" || item.status === statusFilter)
  );

  const handleNew = () => {
    setEditItem({
      id: String(Date.now()),
      productCode: "",
      productName: "",
      category: "전자제품",
      discountRate: 0,
      applyFrom: new Date().toISOString().split("T")[0],
      applyTo: "",
      minQty: 1,
      status: "적용중",
      memo: "",
    });
    setIsNew(true);
    setShowModal(true);
  };

  const handleEdit = () => {
    const item = data.find((d) => d.id === selectedId);
    if (item) {
      setEditItem({ ...item });
      setIsNew(false);
      setShowModal(true);
    }
  };

  const handleSave = () => {
    if (editItem) {
      if (isNew) {
        setData([...data, editItem]);
      } else {
        setData(data.map((d) => (d.id === editItem.id ? editItem : d)));
      }
      setShowModal(false);
      setEditItem(null);
    }
  };

  const handleDelete = () => {
    if (selectedId && window.confirm("선택한 항목을 삭제하시겠습니까?")) {
      setData(data.filter((d) => d.id !== selectedId));
      setSelectedId(null);
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">상품별할인율</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button
          onClick={handleNew}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
          <span>➕</span> 신규
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
          <span>✏️</span> 수정
        </button>
        <button
          onClick={handleDelete}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
          <span>🗑️</span> 삭제
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 엑셀변환
        </button>
      </div>

      {/* 검색 조건 */}
      <div className="flex items-center gap-4 border-b bg-white px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="text-xs">상품:</span>
          <input
            type="text"
            value={productSearch}
            onChange={(e) => setProductSearch(e.target.value)}
            placeholder="상품명/코드"
            className="w-32 rounded border border-gray-400 px-2 py-1 text-xs"
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">상태:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="적용중">적용중</option>
            <option value="만료">만료</option>
          </select>
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
              <th className="border border-gray-400 px-2 py-1 w-16">분류</th>
              <th className="border border-gray-400 px-2 py-1 w-16">할인율(%)</th>
              <th className="border border-gray-400 px-2 py-1 w-24">적용시작</th>
              <th className="border border-gray-400 px-2 py-1 w-24">적용종료</th>
              <th className="border border-gray-400 px-2 py-1 w-16">최소수량</th>
              <th className="border border-gray-400 px-2 py-1 w-16">상태</th>
              <th className="border border-gray-400 px-2 py-1">비고</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr
                key={item.id}
                className={`cursor-pointer ${
                  selectedId === item.id
                    ? "bg-[#316AC5] text-white"
                    : item.status === "만료"
                    ? "bg-gray-100 text-gray-500"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
                onDoubleClick={handleEdit}
              >
                <td className="border border-gray-300 px-2 py-1">{item.productCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.productName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.category}</td>
                <td className="border border-gray-300 px-2 py-1 text-right text-red-600 font-medium">
                  {item.discountRate}%
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.applyFrom}</td>
                <td className="border border-gray-300 px-2 py-1">{item.applyTo}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">{item.minQty}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  item.status === "적용중" ? "text-green-600" : "text-gray-500"
                }`}>
                  {item.status}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.memo}</td>
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
          <div className="w-[450px] bg-white shadow-lg">
            <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">{isNew ? "할인율 등록" : "할인율 수정"}</span>
              <button onClick={() => setShowModal(false)} className="text-white hover:text-gray-200">✕</button>
            </div>
            <div className="p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs mb-1">상품코드 *</label>
                  <input
                    type="text"
                    value={editItem.productCode}
                    onChange={(e) => setEditItem({ ...editItem, productCode: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">상품명 *</label>
                  <input
                    type="text"
                    value={editItem.productName}
                    onChange={(e) => setEditItem({ ...editItem, productName: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">분류</label>
                  <select
                    value={editItem.category}
                    onChange={(e) => setEditItem({ ...editItem, category: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  >
                    <option value="전자제품">전자제품</option>
                    <option value="원자재">원자재</option>
                    <option value="부품">부품</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs mb-1">할인율(%) *</label>
                  <input
                    type="number"
                    value={editItem.discountRate}
                    onChange={(e) => setEditItem({ ...editItem, discountRate: Number(e.target.value) })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">적용시작일</label>
                  <input
                    type="date"
                    value={editItem.applyFrom}
                    onChange={(e) => setEditItem({ ...editItem, applyFrom: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">적용종료일</label>
                  <input
                    type="date"
                    value={editItem.applyTo}
                    onChange={(e) => setEditItem({ ...editItem, applyTo: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">최소수량</label>
                  <input
                    type="number"
                    value={editItem.minQty}
                    onChange={(e) => setEditItem({ ...editItem, minQty: Number(e.target.value) })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">상태</label>
                  <select
                    value={editItem.status}
                    onChange={(e) => setEditItem({ ...editItem, status: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  >
                    <option value="적용중">적용중</option>
                    <option value="만료">만료</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs mb-1">비고</label>
                <input
                  type="text"
                  value={editItem.memo}
                  onChange={(e) => setEditItem({ ...editItem, memo: e.target.value })}
                  className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                />
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
