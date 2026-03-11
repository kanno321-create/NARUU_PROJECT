"use client";

import React, { useState } from "react";

interface BankAccountItem {
  id: string;
  accountNo: string;
  bankName: string;
  accountName: string;
  accountType: string;
  balance: number;
  openDate: string;
  status: string;
  memo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: BankAccountItem[] = [
  {
    id: "1",
    accountNo: "123-456-789012",
    bankName: "기업은행",
    accountName: "법인운영계좌",
    accountType: "보통예금",
    balance: 5000000,
    openDate: "2020-01-01",
    status: "사용중",
    memo: "주거래계좌",
  },
  {
    id: "2",
    accountNo: "987-654-321098",
    bankName: "국민은행",
    accountName: "급여계좌",
    accountType: "보통예금",
    balance: 2000000,
    openDate: "2020-03-15",
    status: "사용중",
    memo: "급여이체용",
  },
  {
    id: "3",
    accountNo: "111-222-333444",
    bankName: "신한은행",
    accountName: "적금계좌",
    accountType: "정기적금",
    balance: 10000000,
    openDate: "2023-01-01",
    status: "사용중",
    memo: "월 100만원",
  },
  {
    id: "4",
    accountNo: "555-666-777888",
    bankName: "우리은행",
    accountName: "예비계좌",
    accountType: "보통예금",
    balance: 500000,
    openDate: "2021-06-01",
    status: "미사용",
    memo: "",
  },
];

export function BankAccountManagement() {
  const [bankFilter, setBankFilter] = useState("전체");
  const [statusFilter, setStatusFilter] = useState("전체");
  const [data, setData] = useState<BankAccountItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState<BankAccountItem | null>(null);
  const [isNew, setIsNew] = useState(false);

  const banks = ["전체", ...new Set(data.map((d) => d.bankName))];

  const filteredData = data.filter(
    (item) =>
      (bankFilter === "전체" || item.bankName === bankFilter) &&
      (statusFilter === "전체" || item.status === statusFilter)
  );

  const totalBalance = filteredData.reduce((acc, item) => acc + item.balance, 0);

  const handleNew = () => {
    setEditItem({
      id: String(Date.now()),
      accountNo: "",
      bankName: "",
      accountName: "",
      accountType: "보통예금",
      balance: 0,
      openDate: new Date().toISOString().split("T")[0],
      status: "사용중",
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
    if (selectedId && window.confirm("선택한 계좌를 삭제하시겠습니까?")) {
      setData(data.filter((d) => d.id !== selectedId));
      setSelectedId(null);
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">통장관리</span>
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
          <span className="text-xs">은행:</span>
          <select
            value={bankFilter}
            onChange={(e) => setBankFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            {banks.map((bank) => (
              <option key={bank} value={bank}>{bank}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">상태:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="사용중">사용중</option>
            <option value="미사용">미사용</option>
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
              <th className="border border-gray-400 px-2 py-1 w-32">계좌번호</th>
              <th className="border border-gray-400 px-2 py-1 w-20">은행</th>
              <th className="border border-gray-400 px-2 py-1 w-28">계좌명</th>
              <th className="border border-gray-400 px-2 py-1 w-20">유형</th>
              <th className="border border-gray-400 px-2 py-1 w-28">잔액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">개설일</th>
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
                    : item.status === "미사용"
                    ? "bg-gray-100 text-gray-500"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
                onDoubleClick={handleEdit}
              >
                <td className="border border-gray-300 px-2 py-1">{item.accountNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.bankName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.accountName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.accountType}</td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600 font-medium">
                  {item.balance.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.openDate}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  item.status === "사용중" ? "text-green-600" : "text-gray-500"
                }`}>
                  {item.status}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.memo}</td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={4}>
                (합계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totalBalance.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={3}></td>
            </tr>
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
              <span className="text-sm font-medium text-white">{isNew ? "계좌 등록" : "계좌 수정"}</span>
              <button onClick={() => setShowModal(false)} className="text-white hover:text-gray-200">✕</button>
            </div>
            <div className="p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2">
                  <label className="block text-xs mb-1">계좌번호 *</label>
                  <input
                    type="text"
                    value={editItem.accountNo}
                    onChange={(e) => setEditItem({ ...editItem, accountNo: e.target.value })}
                    placeholder="000-000-000000"
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">은행 *</label>
                  <select
                    value={editItem.bankName}
                    onChange={(e) => setEditItem({ ...editItem, bankName: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  >
                    <option value="">선택</option>
                    <option value="기업은행">기업은행</option>
                    <option value="국민은행">국민은행</option>
                    <option value="신한은행">신한은행</option>
                    <option value="우리은행">우리은행</option>
                    <option value="하나은행">하나은행</option>
                    <option value="농협은행">농협은행</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs mb-1">계좌명 *</label>
                  <input
                    type="text"
                    value={editItem.accountName}
                    onChange={(e) => setEditItem({ ...editItem, accountName: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">유형</label>
                  <select
                    value={editItem.accountType}
                    onChange={(e) => setEditItem({ ...editItem, accountType: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  >
                    <option value="보통예금">보통예금</option>
                    <option value="정기예금">정기예금</option>
                    <option value="정기적금">정기적금</option>
                    <option value="당좌예금">당좌예금</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs mb-1">잔액</label>
                  <input
                    type="number"
                    value={editItem.balance}
                    onChange={(e) => setEditItem({ ...editItem, balance: Number(e.target.value) })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">개설일</label>
                  <input
                    type="date"
                    value={editItem.openDate}
                    onChange={(e) => setEditItem({ ...editItem, openDate: e.target.value })}
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
                    <option value="사용중">사용중</option>
                    <option value="미사용">미사용</option>
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
