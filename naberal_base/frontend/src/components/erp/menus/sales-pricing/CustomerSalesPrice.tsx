"use client";

import React, { useState } from "react";

interface CustomerSalesPriceItem {
  id: string;
  customerCode: string;
  customerName: string;
  productCode: string;
  productName: string;
  spec: string;
  standardPrice: number;
  salesPrice: number;
  discountRate: number;
  applyDate: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: CustomerSalesPriceItem[] = [
  {
    id: "1",
    customerCode: "c001",
    customerName: "테스트사업장",
    productCode: "e0001",
    productName: "핸드폰케이스",
    spec: "10×10",
    standardPrice: 15000,
    salesPrice: 12000,
    discountRate: 20,
    applyDate: "2025-01-01",
  },
  {
    id: "2",
    customerCode: "c001",
    customerName: "테스트사업장",
    productCode: "e0002",
    productName: "노트북케이스",
    spec: "20×25",
    standardPrice: 25000,
    salesPrice: 20000,
    discountRate: 20,
    applyDate: "2025-01-01",
  },
  {
    id: "3",
    customerCode: "c002",
    customerName: "제고사업장",
    productCode: "e0001",
    productName: "핸드폰케이스",
    spec: "10×10",
    standardPrice: 15000,
    salesPrice: 13500,
    discountRate: 10,
    applyDate: "2025-02-01",
  },
  {
    id: "4",
    customerCode: "c002",
    customerName: "제고사업장",
    productCode: "e0003",
    productName: "키보드케이스",
    spec: "300×400",
    standardPrice: 8000,
    salesPrice: 7000,
    discountRate: 12.5,
    applyDate: "2025-02-01",
  },
];

export function CustomerSalesPrice() {
  const [customerSearch, setCustomerSearch] = useState("");
  const [productSearch, setProductSearch] = useState("");
  const [data, setData] = useState<CustomerSalesPriceItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState<CustomerSalesPriceItem | null>(null);

  const filteredData = data.filter(
    (item) =>
      (customerSearch === "" ||
        item.customerCode.includes(customerSearch) ||
        item.customerName.includes(customerSearch)) &&
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
        <span className="text-sm font-medium text-white">거래처별판매단가</span>
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
            value={customerSearch}
            onChange={(e) => setCustomerSearch(e.target.value)}
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
              <th className="border border-gray-400 px-2 py-1 w-24">표준단가</th>
              <th className="border border-gray-400 px-2 py-1 w-24">판매단가</th>
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
                <td className="border border-gray-300 px-2 py-1">{item.customerCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.productCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.productName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.spec}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.standardPrice.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600 font-medium">
                  {item.salesPrice.toLocaleString()}
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
              <span className="text-sm font-medium text-white">판매단가 수정</span>
              <button onClick={() => setShowModal(false)} className="text-white hover:text-gray-200">✕</button>
            </div>
            <div className="p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs mb-1">거래처코드</label>
                  <input
                    type="text"
                    value={editItem.customerCode}
                    disabled
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs bg-gray-100"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">거래처명</label>
                  <input
                    type="text"
                    value={editItem.customerName}
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
                  <label className="block text-xs mb-1">표준단가</label>
                  <input
                    type="number"
                    value={editItem.standardPrice}
                    disabled
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs bg-gray-100"
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
