"use client";

import React, { useState } from "react";

interface BankAccount {
  id: string;
  code: string;
  bankName: string;
  accountNo: string;
  accountHolder: string;
  memo: string;
}

// 이지판매재고관리 원본 데이터 100% 복제
const ORIGINAL_ACCOUNTS: BankAccount[] = [
  {
    id: "1",
    code: "B001",
    bankName: "국민은행",
    accountNo: "123-456-789012",
    accountHolder: "테스트사업장",
    memo: "주거래은행",
  },
  {
    id: "2",
    code: "B002",
    bankName: "신한은행",
    accountNo: "110-123-456789",
    accountHolder: "테스트사업장",
    memo: "급여이체용",
  },
  {
    id: "3",
    code: "B003",
    bankName: "우리은행",
    accountNo: "1002-123-456789",
    accountHolder: "테스트사업장",
    memo: "비상자금",
  },
];

const BANK_CODES = [
  { code: "004", name: "국민은행" },
  { code: "088", name: "신한은행" },
  { code: "020", name: "우리은행" },
  { code: "081", name: "하나은행" },
  { code: "003", name: "기업은행" },
  { code: "011", name: "농협은행" },
  { code: "090", name: "카카오뱅크" },
  { code: "089", name: "케이뱅크" },
  { code: "092", name: "토스뱅크" },
  { code: "023", name: "SC제일은행" },
  { code: "027", name: "씨티은행" },
  { code: "039", name: "경남은행" },
  { code: "034", name: "광주은행" },
  { code: "031", name: "대구은행" },
  { code: "032", name: "부산은행" },
  { code: "037", name: "전북은행" },
  { code: "035", name: "제주은행" },
];

export function BankAccountRegistration() {
  const [accounts, setAccounts] = useState<BankAccount[]>(ORIGINAL_ACCOUNTS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit">("add");

  const [formData, setFormData] = useState<Omit<BankAccount, "id">>({
    code: "",
    bankName: "",
    accountNo: "",
    accountHolder: "",
    memo: "",
  });

  const filteredAccounts = accounts.filter(
    (a) =>
      a.bankName.includes(searchQuery) ||
      a.code.includes(searchQuery) ||
      a.accountNo.includes(searchQuery) ||
      a.accountHolder.includes(searchQuery)
  );

  const handleAdd = () => {
    setModalMode("add");
    setFormData({
      code: `B${String(accounts.length + 1).padStart(3, "0")}`,
      bankName: "",
      accountNo: "",
      accountHolder: "",
      memo: "",
    });
    setIsModalOpen(true);
  };

  const handleEdit = () => {
    if (!selectedId) return;
    const account = accounts.find((a) => a.id === selectedId);
    if (!account) return;
    setModalMode("edit");
    const { id, ...rest } = account;
    setFormData(rest);
    setIsModalOpen(true);
  };

  const handleDelete = () => {
    if (!selectedId) return;
    if (confirm("선택한 계좌를 삭제하시겠습니까?")) {
      setAccounts(accounts.filter((a) => a.id !== selectedId));
      setSelectedId(null);
    }
  };

  const handleSave = () => {
    if (!formData.bankName || !formData.accountNo) {
      alert("은행명과 계좌번호는 필수 입력 항목입니다.");
      return;
    }

    if (modalMode === "add") {
      const newAccount: BankAccount = {
        id: Date.now().toString(),
        ...formData,
      };
      setAccounts([...accounts, newAccount]);
    } else {
      setAccounts(
        accounts.map((a) => (a.id === selectedId ? { ...a, ...formData } : a))
      );
    }
    setIsModalOpen(false);
  };

  const handleRowDoubleClick = (account: BankAccount) => {
    setSelectedId(account.id);
    setModalMode("edit");
    const { id, ...rest } = account;
    setFormData(rest);
    setIsModalOpen(true);
  };

  const handleBankCodeChange = (bankCode: string) => {
    const bank = BANK_CODES.find((b) => b.code === bankCode);
    if (bank) {
      setFormData({ ...formData, bankName: bank.name });
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">자사은행계좌등록</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button
          onClick={handleAdd}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
          <span>➕</span> 추가
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
          disabled={!selectedId}
        >
          <span>✏️</span> 수정
        </button>
        <button
          onClick={handleDelete}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
          disabled={!selectedId}
        >
          <span>🗑️</span> 삭제
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <span className="text-xs">검색:</span>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-32 rounded border border-gray-400 px-2 py-0.5 text-xs"
          placeholder="은행명/계좌번호"
        />
        <button className="rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          검색
        </button>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto p-2">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-20">코드</th>
              <th className="border border-gray-400 px-2 py-1 w-32">은행명</th>
              <th className="border border-gray-400 px-2 py-1 w-40">계좌번호</th>
              <th className="border border-gray-400 px-2 py-1 w-32">예금주</th>
              <th className="border border-gray-400 px-2 py-1">간단메모</th>
            </tr>
          </thead>
          <tbody>
            {filteredAccounts.map((acc) => (
              <tr
                key={acc.id}
                className={`cursor-pointer ${
                  selectedId === acc.id ? "bg-[#316AC5] text-white" : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(acc.id)}
                onDoubleClick={() => handleRowDoubleClick(acc)}
              >
                <td className="border border-gray-300 px-2 py-1">{acc.code}</td>
                <td className="border border-gray-300 px-2 py-1">{acc.bankName}</td>
                <td className="border border-gray-300 px-2 py-1">{acc.accountNo}</td>
                <td className="border border-gray-300 px-2 py-1">{acc.accountHolder}</td>
                <td className="border border-gray-300 px-2 py-1">{acc.memo}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredAccounts.length}건 | loading ok
      </div>

      {/* 모달 */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[450px] rounded border border-gray-400 bg-[#F0EDE4] shadow-lg">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between rounded-t border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">
                {modalMode === "add" ? "계좌 추가" : "계좌 수정"}
              </span>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-white hover:text-gray-200"
              >
                ✕
              </button>
            </div>

            {/* 모달 내용 */}
            <div className="p-4 space-y-3">
              <div className="flex items-center gap-2">
                <label className="w-20 text-right text-xs">코드:</label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  className="w-24 rounded border border-gray-400 px-2 py-1 text-xs"
                  readOnly={modalMode === "edit"}
                />
              </div>
              <div className="flex items-center gap-2">
                <label className="w-20 text-right text-xs">은행코드:</label>
                <select
                  onChange={(e) => handleBankCodeChange(e.target.value)}
                  className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                >
                  <option value="">선택</option>
                  {BANK_CODES.map((bank) => (
                    <option key={bank.code} value={bank.code}>
                      {bank.code} - {bank.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label className="w-20 text-right text-xs">은행명:</label>
                <input
                  type="text"
                  value={formData.bankName}
                  onChange={(e) => setFormData({ ...formData, bankName: e.target.value })}
                  className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                />
              </div>
              <div className="flex items-center gap-2">
                <label className="w-20 text-right text-xs">계좌번호:</label>
                <input
                  type="text"
                  value={formData.accountNo}
                  onChange={(e) => setFormData({ ...formData, accountNo: e.target.value })}
                  className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                  placeholder="000-000-000000"
                />
              </div>
              <div className="flex items-center gap-2">
                <label className="w-20 text-right text-xs">예금주:</label>
                <input
                  type="text"
                  value={formData.accountHolder}
                  onChange={(e) => setFormData({ ...formData, accountHolder: e.target.value })}
                  className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                />
              </div>
              <div className="flex items-center gap-2">
                <label className="w-20 text-right text-xs">간단메모:</label>
                <textarea
                  value={formData.memo}
                  onChange={(e) => setFormData({ ...formData, memo: e.target.value })}
                  className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                  rows={3}
                />
              </div>
            </div>

            {/* 모달 푸터 */}
            <div className="flex justify-end gap-2 border-t bg-gray-200 px-4 py-2">
              <button
                onClick={handleSave}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200"
              >
                저장
              </button>
              <button
                onClick={() => setIsModalOpen(false)}
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
