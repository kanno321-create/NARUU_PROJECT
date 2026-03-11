"use client";

import React, { useState } from "react";

interface CustomerDiscountItem {
  id: string;
  customerCode: string;
  customerName: string;
  customerType: string;
  discountRate: number;
  applyFrom: string;
  applyTo: string;
  minOrderAmount: number;
  status: string;
  memo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: CustomerDiscountItem[] = [
  {
    id: "1",
    customerCode: "c001",
    customerName: "테스트사업장",
    customerType: "일반",
    discountRate: 10,
    applyFrom: "2025-01-01",
    applyTo: "2025-12-31",
    minOrderAmount: 100000,
    status: "적용중",
    memo: "VIP 고객",
  },
  {
    id: "2",
    customerCode: "c002",
    customerName: "제고사업장",
    customerType: "도매",
    discountRate: 15,
    applyFrom: "2025-01-01",
    applyTo: "2025-12-31",
    minOrderAmount: 500000,
    status: "적용중",
    memo: "대량구매 할인",
  },
  {
    id: "3",
    customerCode: "c003",
    customerName: "신규사업장",
    customerType: "일반",
    discountRate: 5,
    applyFrom: "2025-06-01",
    applyTo: "2025-12-31",
    minOrderAmount: 50000,
    status: "적용중",
    memo: "신규고객 할인",
  },
  {
    id: "4",
    customerCode: "c004",
    customerName: "구사업장",
    customerType: "특약점",
    discountRate: 20,
    applyFrom: "2024-01-01",
    applyTo: "2024-12-31",
    minOrderAmount: 1000000,
    status: "만료",
    memo: "특약점 할인",
  },
];

export function CustomerDiscount() {
  const [customerSearch, setCustomerSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("전체");
  const [data, setData] = useState<CustomerDiscountItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState<CustomerDiscountItem | null>(null);
  const [isNew, setIsNew] = useState(false);

  const filteredData = data.filter(
    (item) =>
      (customerSearch === "" ||
        item.customerCode.includes(customerSearch) ||
        item.customerName.includes(customerSearch)) &&
      (statusFilter === "전체" || item.status === statusFilter)
  );

  const handleNew = () => {
    setEditItem({
      id: String(Date.now()),
      customerCode: "",
      customerName: "",
      customerType: "일반",
      discountRate: 0,
      applyFrom: new Date().toISOString().split("T")[0],
      applyTo: "",
      minOrderAmount: 0,
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
        <span className="text-sm font-medium text-white">거래처별할인율</span>
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
              <th className="border border-gray-400 px-2 py-1 w-20">거래처코드</th>
              <th className="border border-gray-400 px-2 py-1 w-28">거래처명</th>
              <th className="border border-gray-400 px-2 py-1 w-16">유형</th>
              <th className="border border-gray-400 px-2 py-1 w-16">할인율(%)</th>
              <th className="border border-gray-400 px-2 py-1 w-24">적용시작</th>
              <th className="border border-gray-400 px-2 py-1 w-24">적용종료</th>
              <th className="border border-gray-400 px-2 py-1 w-24">최소주문금액</th>
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
                <td className="border border-gray-300 px-2 py-1">{item.customerCode}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.customerType}</td>
                <td className="border border-gray-300 px-2 py-1 text-right text-red-600 font-medium">
                  {item.discountRate}%
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.applyFrom}</td>
                <td className="border border-gray-300 px-2 py-1">{item.applyTo}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.minOrderAmount.toLocaleString()}
                </td>
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
                  <label className="block text-xs mb-1">거래처코드 *</label>
                  <input
                    type="text"
                    value={editItem.customerCode}
                    onChange={(e) => setEditItem({ ...editItem, customerCode: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">거래처명 *</label>
                  <input
                    type="text"
                    value={editItem.customerName}
                    onChange={(e) => setEditItem({ ...editItem, customerName: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">유형</label>
                  <select
                    value={editItem.customerType}
                    onChange={(e) => setEditItem({ ...editItem, customerType: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  >
                    <option value="일반">일반</option>
                    <option value="도매">도매</option>
                    <option value="특약점">특약점</option>
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
                  <label className="block text-xs mb-1">최소주문금액</label>
                  <input
                    type="number"
                    value={editItem.minOrderAmount}
                    onChange={(e) => setEditItem({ ...editItem, minOrderAmount: Number(e.target.value) })}
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
