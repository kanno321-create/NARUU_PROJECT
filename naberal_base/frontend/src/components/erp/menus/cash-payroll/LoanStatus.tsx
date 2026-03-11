"use client";

import React, { useState } from "react";

interface LoanItem {
  id: string;
  loanNo: string;
  bankName: string;
  loanType: string;
  loanDate: string;
  maturityDate: string;
  loanAmount: number;
  interestRate: number;
  repaidAmount: number;
  remainingAmount: number;
  monthlyPayment: number;
  status: string;
  memo: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: LoanItem[] = [
  {
    id: "1",
    loanNo: "L2023-001",
    bankName: "기업은행",
    loanType: "운전자금",
    loanDate: "2023-01-15",
    maturityDate: "2026-01-15",
    loanAmount: 50000000,
    interestRate: 4.5,
    repaidAmount: 20000000,
    remainingAmount: 30000000,
    monthlyPayment: 1500000,
    status: "상환중",
    memo: "분할상환",
  },
  {
    id: "2",
    loanNo: "L2024-001",
    bankName: "국민은행",
    loanType: "시설자금",
    loanDate: "2024-03-01",
    maturityDate: "2029-03-01",
    loanAmount: 100000000,
    interestRate: 4.2,
    repaidAmount: 10000000,
    remainingAmount: 90000000,
    monthlyPayment: 2000000,
    status: "상환중",
    memo: "시설투자",
  },
  {
    id: "3",
    loanNo: "L2024-002",
    bankName: "신한은행",
    loanType: "운전자금",
    loanDate: "2024-06-01",
    maturityDate: "2025-06-01",
    loanAmount: 20000000,
    interestRate: 5.0,
    repaidAmount: 10000000,
    remainingAmount: 10000000,
    monthlyPayment: 1700000,
    status: "상환중",
    memo: "단기차입",
  },
  {
    id: "4",
    loanNo: "L2022-001",
    bankName: "우리은행",
    loanType: "운전자금",
    loanDate: "2022-01-01",
    maturityDate: "2024-12-31",
    loanAmount: 30000000,
    interestRate: 3.8,
    repaidAmount: 30000000,
    remainingAmount: 0,
    monthlyPayment: 0,
    status: "상환완료",
    memo: "",
  },
];

export function LoanStatus() {
  const [bankFilter, setBankFilter] = useState("전체");
  const [statusFilter, setStatusFilter] = useState("전체");
  const [data, setData] = useState<LoanItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState<LoanItem | null>(null);
  const [isNew, setIsNew] = useState(false);

  const banks = ["전체", ...new Set(data.map((d) => d.bankName))];

  const filteredData = data.filter(
    (item) =>
      (bankFilter === "전체" || item.bankName === bankFilter) &&
      (statusFilter === "전체" || item.status === statusFilter)
  );

  // 총계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      loanAmount: acc.loanAmount + item.loanAmount,
      repaidAmount: acc.repaidAmount + item.repaidAmount,
      remainingAmount: acc.remainingAmount + item.remainingAmount,
      monthlyPayment: acc.monthlyPayment + item.monthlyPayment,
    }),
    { loanAmount: 0, repaidAmount: 0, remainingAmount: 0, monthlyPayment: 0 }
  );

  const handleNew = () => {
    setEditItem({
      id: String(Date.now()),
      loanNo: "",
      bankName: "",
      loanType: "운전자금",
      loanDate: new Date().toISOString().split("T")[0],
      maturityDate: "",
      loanAmount: 0,
      interestRate: 0,
      repaidAmount: 0,
      remainingAmount: 0,
      monthlyPayment: 0,
      status: "상환중",
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
      editItem.remainingAmount = editItem.loanAmount - editItem.repaidAmount;
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
    if (selectedId && window.confirm("선택한 대출 정보를 삭제하시겠습니까?")) {
      setData(data.filter((d) => d.id !== selectedId));
      setSelectedId(null);
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">대출현황</span>
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
            <option value="상환중">상환중</option>
            <option value="상환완료">상환완료</option>
          </select>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색
        </button>
      </div>

      {/* 요약 정보 */}
      <div className="grid grid-cols-4 gap-2 border-b bg-red-50 px-3 py-2">
        <div className="bg-white px-3 py-2 rounded border text-center">
          <div className="text-xs text-gray-600">총 대출액</div>
          <div className="text-sm font-bold">{totals.loanAmount.toLocaleString()}원</div>
        </div>
        <div className="bg-white px-3 py-2 rounded border text-center">
          <div className="text-xs text-gray-600">상환액</div>
          <div className="text-sm font-bold text-blue-600">{totals.repaidAmount.toLocaleString()}원</div>
        </div>
        <div className="bg-white px-3 py-2 rounded border text-center">
          <div className="text-xs text-gray-600">잔여액</div>
          <div className="text-sm font-bold text-red-600">{totals.remainingAmount.toLocaleString()}원</div>
        </div>
        <div className="bg-white px-3 py-2 rounded border text-center">
          <div className="text-xs text-gray-600">월 상환액</div>
          <div className="text-sm font-bold">{totals.monthlyPayment.toLocaleString()}원</div>
        </div>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-24">대출번호</th>
              <th className="border border-gray-400 px-2 py-1 w-20">은행</th>
              <th className="border border-gray-400 px-2 py-1 w-20">대출종류</th>
              <th className="border border-gray-400 px-2 py-1 w-24">대출일</th>
              <th className="border border-gray-400 px-2 py-1 w-24">만기일</th>
              <th className="border border-gray-400 px-2 py-1 w-28">대출액</th>
              <th className="border border-gray-400 px-2 py-1 w-16">이율(%)</th>
              <th className="border border-gray-400 px-2 py-1 w-28">상환액</th>
              <th className="border border-gray-400 px-2 py-1 w-28">잔액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">월상환액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">상태</th>
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
                    : item.status === "상환완료"
                    ? "bg-gray-100 text-gray-500"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
                onDoubleClick={handleEdit}
              >
                <td className="border border-gray-300 px-2 py-1">{item.loanNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.bankName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.loanType}</td>
                <td className="border border-gray-300 px-2 py-1">{item.loanDate}</td>
                <td className="border border-gray-300 px-2 py-1">{item.maturityDate}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.loanAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  {item.interestRate}%
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">
                  {item.repaidAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-red-600 font-medium">
                  {item.remainingAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.monthlyPayment.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  item.status === "상환완료" ? "text-green-600" : "text-orange-600"
                }`}>
                  {item.status}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.memo}</td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={5}>
                (합계)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.loanAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.repaidAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.remainingAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.monthlyPayment.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={2}></td>
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
          <div className="w-[500px] bg-white shadow-lg">
            <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">{isNew ? "대출 등록" : "대출 수정"}</span>
              <button onClick={() => setShowModal(false)} className="text-white hover:text-gray-200">✕</button>
            </div>
            <div className="p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs mb-1">대출번호 *</label>
                  <input
                    type="text"
                    value={editItem.loanNo}
                    onChange={(e) => setEditItem({ ...editItem, loanNo: e.target.value })}
                    placeholder="L2024-001"
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
                  </select>
                </div>
                <div>
                  <label className="block text-xs mb-1">대출종류</label>
                  <select
                    value={editItem.loanType}
                    onChange={(e) => setEditItem({ ...editItem, loanType: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  >
                    <option value="운전자금">운전자금</option>
                    <option value="시설자금">시설자금</option>
                    <option value="기타">기타</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs mb-1">이율(%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={editItem.interestRate}
                    onChange={(e) => setEditItem({ ...editItem, interestRate: Number(e.target.value) })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">대출일</label>
                  <input
                    type="date"
                    value={editItem.loanDate}
                    onChange={(e) => setEditItem({ ...editItem, loanDate: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">만기일</label>
                  <input
                    type="date"
                    value={editItem.maturityDate}
                    onChange={(e) => setEditItem({ ...editItem, maturityDate: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">대출액</label>
                  <input
                    type="number"
                    value={editItem.loanAmount}
                    onChange={(e) => setEditItem({ ...editItem, loanAmount: Number(e.target.value) })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">상환액</label>
                  <input
                    type="number"
                    value={editItem.repaidAmount}
                    onChange={(e) => setEditItem({ ...editItem, repaidAmount: Number(e.target.value) })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">월상환액</label>
                  <input
                    type="number"
                    value={editItem.monthlyPayment}
                    onChange={(e) => setEditItem({ ...editItem, monthlyPayment: Number(e.target.value) })}
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
                    <option value="상환중">상환중</option>
                    <option value="상환완료">상환완료</option>
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
