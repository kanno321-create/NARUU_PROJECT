"use client";

import React, { useState, useEffect } from "react";
import { useERPData } from "@/contexts/ERPDataContext";

interface BankAccount {
  id: string;
  code: string;          // 은행코드
  bankName: string;      // 은행명
  accountNumber: string; // 계좌번호
  accountHolder: string; // 예금주
  memo: string;          // 간단메모
}

// 이지판매재고관리 원본 데이터 100% 복제 (2025-12-05 스크린샷 기준)
const ORIGINAL_ACCOUNTS: BankAccount[] = [
  { id: "1", code: "01", bankName: "부산은행", accountNumber: "123-456-789012", accountHolder: "홍길동", memo: "" },
  { id: "2", code: "02", bankName: "하나은행", accountNumber: "234-567-890123", accountHolder: "홍길동", memo: "" },
  { id: "3", code: "03", bankName: "국민은행", accountNumber: "345-678-901234", accountHolder: "홍길동", memo: "" },
  { id: "4", code: "04", bankName: "신한은행", accountNumber: "456-789-012345", accountHolder: "홍길동", memo: "" },
  { id: "5", code: "05", bankName: "우리은행", accountNumber: "567-890-123456", accountHolder: "홍길동", memo: "" },
];

const emptyAccount: BankAccount = {
  id: "",
  code: "",
  bankName: "",
  accountNumber: "",
  accountHolder: "",
  memo: "",
};

export function BankAccountWindow() {
  const { bankAccounts: ctxBankAccounts, fetchBankAccounts, addBankAccount, updateBankAccount, deleteBankAccount } = useERPData();
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRow, setSelectedRow] = useState<number | null>(null);

  // 컨텍스트에서 은행계좌 데이터 동기화
  useEffect(() => {
    if (ctxBankAccounts.length > 0) {
      setAccounts(ctxBankAccounts.map(a => ({
        id: a.id,
        code: a.id.substring(0, 2),
        bankName: a.bank_name,
        accountNumber: a.account_number,
        accountHolder: a.account_holder,
        memo: a.memo || "",
      })));
    }
  }, [ctxBankAccounts]);

  // 마운트 시 은행계좌 데이터 로드
  useEffect(() => {
    fetchBankAccounts();
  }, [fetchBankAccounts]);

  // 모달 상태
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit">("add");
  const [editForm, setEditForm] = useState<BankAccount>(emptyAccount);

  const filteredAccounts = accounts.filter(
    (a) =>
      a.bankName.includes(searchQuery) ||
      a.code.includes(searchQuery) ||
      a.accountNumber.includes(searchQuery)
  );

  // 툴바 버튼 핸들러
  const handleAdd = () => {
    const nextCode = String(accounts.length + 1).padStart(2, "0");
    setEditForm({ ...emptyAccount, id: String(Date.now()), code: nextCode });
    setModalMode("add");
    setShowModal(true);
  };

  const handleEdit = () => {
    if (selectedRow === null) {
      alert("수정할 계좌를 선택하세요.");
      return;
    }
    const account = filteredAccounts[selectedRow];
    setEditForm({ ...account });
    setModalMode("edit");
    setShowModal(true);
  };

  const handleDelete = async () => {
    if (selectedRow === null) {
      alert("삭제할 계좌를 선택하세요.");
      return;
    }
    if (confirm("선택한 계좌를 삭제하시겠습니까?")) {
      const account = filteredAccounts[selectedRow];
      await deleteBankAccount(account.id);
      setSelectedRow(null);
    }
  };

  const handleRefresh = () => {
    fetchBankAccounts();
    setSelectedRow(null);
    setSearchQuery("");
  };

  const handleSearch = () => {
    // 검색은 실시간으로 되므로 별도 처리 불필요
  };

  const handleViewAll = () => {
    setSearchQuery("");
  };

  // 모달 저장 (DB 연동)
  const handleSave = async () => {
    if (!editForm.bankName) {
      alert("은행명을 입력하세요.");
      return;
    }

    const payload = {
      bank_name: editForm.bankName,
      account_number: editForm.accountNumber,
      account_holder: editForm.accountHolder,
      memo: editForm.memo,
    };

    if (modalMode === "add") {
      await addBankAccount(payload as any);
    } else {
      await updateBankAccount(editForm.id, payload as any);
    }
    setShowModal(false);
    setSelectedRow(null);
  };

  const handleCancel = () => {
    setShowModal(false);
  };

  // 행 더블클릭으로 수정
  const handleRowDoubleClick = (index: number) => {
    setSelectedRow(index);
    const account = filteredAccounts[index];
    setEditForm({ ...account });
    setModalMode("edit");
    setShowModal(true);
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 툴바 - 이지판매재고관리 스타일 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button
          onClick={handleAdd}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-green-600">⊕</span> 추가
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-blue-600">✎</span> 수정
        </button>
        <button
          onClick={handleDelete}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-red-600">✕</span> 삭제
        </button>
        <div className="mx-1 h-6 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
          <span>A</span> 미리보기
        </button>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-blue-600">↻</span> 새로고침
        </button>
        <div className="mx-1 h-6 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
          <span>▤</span> 표시항목
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
          <span className="text-green-700">📊</span> 엑셀입력
        </button>
      </div>

      {/* 검색 영역 */}
      <div className="flex items-center gap-2 border-b bg-gray-100 px-4 py-2">
        <span className="text-sm">은행명:</span>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-40 rounded border border-gray-400 px-2 py-1 text-sm"
        />
        <button
          onClick={handleSearch}
          className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
        >
          검 색(F)
        </button>
        <button
          onClick={handleViewAll}
          className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
        >
          전체보기
        </button>
      </div>

      {/* 그리드 - 이지판매재고관리 컬럼 100% */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 text-center font-normal">
                <input type="checkbox" />
              </th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">은행코드</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">은행명</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">계좌번호</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">예금주</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">간단메모</th>
            </tr>
          </thead>
          <tbody>
            {filteredAccounts.map((account, index) => (
              <tr
                key={account.id}
                className={`cursor-pointer ${
                  selectedRow === index ? "bg-[#316AC5] text-white" : "bg-white hover:bg-gray-100"
                }`}
                onClick={() => setSelectedRow(index)}
                onDoubleClick={() => handleRowDoubleClick(index)}
              >
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <input type="checkbox" />
                </td>
                <td className="border border-gray-300 px-2 py-1">{account.code}</td>
                <td className="border border-gray-300 px-2 py-1">{account.bankName}</td>
                <td className="border border-gray-300 px-2 py-1">{account.accountNumber}</td>
                <td className="border border-gray-300 px-2 py-1">{account.accountHolder}</td>
                <td className="border border-gray-300 px-2 py-1">{account.memo}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="flex items-center justify-end border-t bg-gray-100 px-4 py-1 text-sm text-gray-600">
        <span>전체 {accounts.length} 항목</span>
        <span className="mx-4">|</span>
        <span>{filteredAccounts.length} 항목표시</span>
      </div>

      {/* 자사은행계좌 정보등록 모달 - 이지판매재고관리 100% 복제 */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-[400px] rounded bg-gray-200 shadow-lg">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between border-b border-gray-400 bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">자사은행계좌 정보입력</span>
              <button
                onClick={handleCancel}
                className="text-white hover:text-gray-200"
              >
                ✕
              </button>
            </div>

            {/* 모달 내용 */}
            <div className="bg-[#F0EDE4] p-4">
              <fieldset className="rounded border border-gray-400 p-3">
                <legend className="px-2 text-sm text-blue-700">계좌정보</legend>
                <div className="grid grid-cols-[80px_1fr] gap-2 text-sm">
                  <label className="py-1 text-right">은행코드:</label>
                  <input
                    type="text"
                    value={editForm.code}
                    onChange={(e) => setEditForm({ ...editForm, code: e.target.value })}
                    className="w-20 border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">은행명:</label>
                  <input
                    type="text"
                    value={editForm.bankName}
                    onChange={(e) => setEditForm({ ...editForm, bankName: e.target.value })}
                    className="w-48 border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">계좌번호:</label>
                  <input
                    type="text"
                    value={editForm.accountNumber}
                    onChange={(e) => setEditForm({ ...editForm, accountNumber: e.target.value })}
                    className="w-full border border-gray-400 px-2 py-1"
                    placeholder="000-000-000000"
                  />

                  <label className="py-1 text-right">예금주:</label>
                  <input
                    type="text"
                    value={editForm.accountHolder}
                    onChange={(e) => setEditForm({ ...editForm, accountHolder: e.target.value })}
                    className="w-32 border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">간단메모:</label>
                  <input
                    type="text"
                    value={editForm.memo}
                    onChange={(e) => setEditForm({ ...editForm, memo: e.target.value })}
                    className="w-full border border-gray-400 px-2 py-1"
                  />
                </div>
              </fieldset>
              <p className="mt-3 text-sm text-gray-600">
                새로운 자사은행계좌의 정보를 등록합니다.
              </p>
            </div>

            {/* 모달 푸터 - 이지판매재고관리 스타일 */}
            <div className="flex justify-end gap-2 border-t border-gray-400 bg-gray-200 px-4 py-3">
              <button
                onClick={handleSave}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
              >
                저장
              </button>
              <button
                onClick={handleCancel}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
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
