"use client";

import React, { useState } from "react";

interface CustomerPurchasePriceItem {
  id: string;
  vendorCode: string;
  vendorName: string;
  productCode: string;
  productName: string;
  spec: string;
  standardCost: number;
  purchasePrice: number;
  discountRate: number;
  applyDate: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: CustomerPurchasePriceItem[] = [
  {
    id: "1",
    vendorCode: "v001",
    vendorName: "공급업체A",
    productCode: "p001",
    productName: "원자재A",
    spec: "100×50",
    standardCost: 1200,
    purchasePrice: 1000,
    discountRate: 16.7,
    applyDate: "2025-01-01",
  },
  {
    id: "2",
    vendorCode: "v001",
    vendorName: "공급업체A",
    productCode: "p002",
    productName: "원자재B",
    spec: "200×100",
    standardCost: 2500,
    purchasePrice: 2000,
    discountRate: 20,
    applyDate: "2025-01-01",
  },
  {
    id: "3",
    vendorCode: "v002",
    vendorName: "공급업체B",
    productCode: "p003",
    productName: "부품A",
    spec: "50×30",
    standardCost: 600,
    purchasePrice: 500,
    discountRate: 16.7,
    applyDate: "2025-02-01",
  },
  {
    id: "4",
    vendorCode: "v003",
    vendorName: "공급업체C",
    productCode: "p001",
    productName: "원자재A",
    spec: "100×50",
    standardCost: 1200,
    purchasePrice: 950,
    discountRate: 20.8,
    applyDate: "2025-02-01",
  },
];

export function CustomerPurchasePrice() {
  const [vendorSearch, setVendorSearch] = useState("");
  const [productSearch, setProductSearch] = useState("");
  const [data, setData] = useState<CustomerPurchasePriceItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState<CustomerPurchasePriceItem | null>(null);

  const filteredData = data.filter(
    (item) =>
      (vendorSearch === "" ||
        item.vendorCode.includes(vendorSearch) ||
        item.vendorName.includes(vendorSearch)) &&
      (productSearch === "" ||
        item.productCode.includes(productSearch) ||
        item.productName.includes(productSearch))
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
      setData(data.map((d) => (d.id === editItem.id ? editItem : d)));
      setShowModal(false);
      setEditItem(null);
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">거래처별매입단가</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>➕</span> 신규
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
          <span>✏️</span> 수정
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🗑️</span> 삭제
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
          <span className="text-xs">거래처:</span>
          <input
            type="text"
            value={vendorSearch}
            onChange={(e) => setVendorSearch(e.target.value)}
            placeholder="거래처명/코드"
            className="w-32 rounded border border-gray-400 px-2 py-1 text-xs"
          />
        </div>
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
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색
        </button>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-20">거래처코드</th>
              <th className="border border-gray-400 px-2 py-1 w-28">거래처명</th>
              <th className="border border-gray-400 px-2 py-1 w-20">상품코드</th>
              <th className="border border-gray-400 px-2 py-1 w-28">상품명</th>
              <th className="border border-gray-400 px-2 py-1 w-16">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-24">표준원가</th>
              <th className="border border-gray-400 px-2 py-1 w-24">매입단가</th>
              <th className="border border-gray-400 px-2 py-1 w-16">할인율(%)</th>
              <th className="border border-gray-400 px-2 py-1">적용일자</th>
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
                <td className="border border-gray-300 px-2 py-1">{item.vendorCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.vendorName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.productCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.productName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.spec}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.standardCost.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600 font-medium">
                  {item.purchasePrice.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-red-600">
                  {item.discountRate}%
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.applyDate}</td>
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
              <span className="text-sm font-medium text-white">매입단가 수정</span>
              <button onClick={() => setShowModal(false)} className="text-white hover:text-gray-200">✕</button>
            </div>
            <div className="p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs mb-1">거래처코드</label>
                  <input
                    type="text"
                    value={editItem.vendorCode}
                    disabled
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs bg-gray-100"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">거래처명</label>
                  <input
                    type="text"
                    value={editItem.vendorName}
                    disabled
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs bg-gray-100"
                  />
                </div>
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
                  <label className="block text-xs mb-1">표준원가</label>
                  <input
                    type="number"
                    value={editItem.standardCost}
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
                  <label className="block text-xs mb-1">할인율(%)</label>
                  <input
                    type="number"
                    value={editItem.discountRate}
                    onChange={(e) => setEditItem({ ...editItem, discountRate: Number(e.target.value) })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">적용일자</label>
                  <input
                    type="date"
                    value={editItem.applyDate}
                    onChange={(e) => setEditItem({ ...editItem, applyDate: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
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
