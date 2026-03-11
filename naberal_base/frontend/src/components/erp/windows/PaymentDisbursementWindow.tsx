"use client";

import React, { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import { useWindowContextOptional } from "../ERPContext";

// ============================================
// 지급전표 윈도우 - 이지판매재고관리 100% 복제
// NABERAL Modern Design 적용
// ============================================

interface PaymentItem {
  id: string;
  type: string;        // 구분 (현금/은행/어음/카드)
  bankName: string;    // 은행명
  amount: number;      // 금액
  memo: string;        // 비고
  // 카드 전용
  cardName: string;    // 카드사
  cardNumber: string;  // 카드번호
  approvalNo: string;  // 승인번호
  // 어음 전용
  billNo: string;      // 어음번호
  billDate: string;    // 어음일자
  dueDate: string;     // 만기일
  issuer: string;      // 발행인
}

interface Supplier {
  code: string;
  name: string;
  representative: string;
  phone: string;
  fax: string;
  creditLimit: number;
  receivable: number;  // 미수금액
  payable: number;     // 미지급액
  lastTransaction: string;
  purchaseCommission: number; // 매입수수료(%)
}

interface Employee {
  code: string;
  name: string;
  department: string;
}

// ORIGINAL_SUPPLIERS, ORIGINAL_EMPLOYEES, ORIGINAL_BANKS, ORIGINAL_CARDS replaced with API-loaded state

const emptyPaymentItem: PaymentItem = {
  id: "",
  type: "현금",
  bankName: "",
  amount: 0,
  memo: "",
  cardName: "",
  cardNumber: "",
  approvalNo: "",
  billNo: "",
  billDate: "",
  dueDate: "",
  issuer: "",
};

export function PaymentDisbursementWindow() {
  const windowContext = useWindowContextOptional();

  // 거래처명 자동완성
  const [supplierSearch, setSupplierSearch] = useState('');
  const [supplierSuggestions, setSupplierSuggestions] = useState<any[]>([]);
  const [showSupplierSuggestions, setShowSupplierSuggestions] = useState(false);

  // 거래처 검색 디바운스
  useEffect(() => {
    if (!supplierSearch || supplierSearch.length < 2) {
      setSupplierSuggestions([]);
      setShowSupplierSuggestions(false);
      return;
    }
    const timer = setTimeout(() => {
      api.erp.customers.list({ search: supplierSearch, limit: 10 }).then(res => {
        setSupplierSuggestions(res.items);
        setShowSupplierSuggestions(true);
      }).catch(() => {});
    }, 300);
    return () => clearTimeout(timer);
  }, [supplierSearch]);

  // API에서 로드되는 데이터
  const [apiSuppliers, setApiSuppliers] = useState<Supplier[]>([]);
  const [apiEmployees, setApiEmployees] = useState<Employee[]>([]);
  const [apiBanks, setApiBanks] = useState<{ code: string; name: string; accountNumber: string }[]>([]);
  const [apiCards] = useState<{ code: string; name: string; feeRate: number }[]>([]);

  // 거래처 모달 API 로드
  useEffect(() => {
    if (!showSupplierModal) return;
    api.erp.customers.list({ search: supplierSearchQuery || undefined, limit: 50 }).then(res => {
      setApiSuppliers(res.items.map((c: any) => ({
        code: String(c.id || c.code || ""),
        name: c.name || c.company_name || "",
        representative: c.representative || c.contact_person || "",
        phone: c.phone || "",
        fax: c.fax || "",
        creditLimit: c.credit_limit || 0,
        receivable: c.receivable || 0,
        payable: c.payable || 0,
        lastTransaction: c.last_transaction || "",
        purchaseCommission: c.purchase_commission || 0,
      })));
    }).catch(() => setApiSuppliers([]));
  }, [showSupplierModal, supplierSearchQuery]);

  // 직원/은행 목록 API 로드
  useEffect(() => {
    api.erp.employees.list().then((res: any) => {
      const items = Array.isArray(res) ? res : (res?.items || []);
      setApiEmployees(items.map((e: any) => ({
        code: e.code || e.id || "",
        name: e.name || "",
        department: e.department || "",
      })));
    }).catch(() => setApiEmployees([]));

    api.erp.bankAccounts.list().then((res: any) => {
      const items = Array.isArray(res) ? res : (res?.items || []);
      setApiBanks(items.map((b: any) => ({
        code: b.code || b.id || "",
        name: b.bank_name || b.name || "",
        accountNumber: b.account_number || b.accountNo || "",
      })));
    }).catch(() => setApiBanks([]));
  }, []);

  // 기본정보
  const [paymentDate, setPaymentDate] = useState("2025년 12월 05일");
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const [memo, setMemo] = useState("");

  // 대금결제방법 탭
  const [activePaymentTab, setActivePaymentTab] = useState<"현금" | "은행" | "어음" | "카드">("현금");

  // 결제 항목들
  const [paymentItems, setPaymentItems] = useState<PaymentItem[]>([]);
  const [selectedPaymentRow, setSelectedPaymentRow] = useState<number | null>(null);

  // 은행수수료, 지급시에누리
  const [bankFee, setBankFee] = useState(0);
  const [discount, setDiscount] = useState(0);

  // 모달 상태
  const [showSupplierModal, setShowSupplierModal] = useState(false);
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);
  const [showCashModal, setShowCashModal] = useState(false);
  const [showBankModal, setShowBankModal] = useState(false);
  const [showBillModal, setShowBillModal] = useState(false);
  const [showCardModal, setShowCardModal] = useState(false);

  // 검색
  const [supplierSearchQuery, setSupplierSearchQuery] = useState("");
  const [employeeSearchQuery, setEmployeeSearchQuery] = useState("");

  // 현금 입력 폼
  const [cashForm, setCashForm] = useState({ amount: 0, memo: "" });

  // 은행 입력 폼
  const [bankForm, setBankForm] = useState({
    bankName: "",
    amount: 0,
    memo: "",
  });

  // 어음 입력 폼
  const [billForm, setBillForm] = useState({
    billNo: "",
    billDate: "",
    dueDate: "",
    issuer: "",
    amount: 0,
    memo: "",
  });

  // 카드 입력 폼
  const [cardForm, setCardForm] = useState({
    cardName: "",
    cardNumber: "",
    approvalNo: "",
    amount: 0,
    memo: "",
  });

  // 필터된 데이터 (거래처는 API에서 이미 필터링됨)
  const filteredSuppliers = apiSuppliers;

  const filteredEmployees = apiEmployees.filter(
    (e) =>
      e.name.includes(employeeSearchQuery) ||
      e.code.includes(employeeSearchQuery) ||
      e.department.includes(employeeSearchQuery)
  );

  // 합계 계산
  const totalAmount = paymentItems.reduce((sum, item) => sum + item.amount, 0);
  const netAmount = totalAmount - bankFee - discount;

  // 거래처 선택
  const handleSelectSupplier = (supplier: Supplier) => {
    setSelectedSupplier(supplier);
    setShowSupplierModal(false);
    setSupplierSearchQuery("");
  };

  // 사원 선택
  const handleSelectEmployee = (employee: Employee) => {
    setSelectedEmployee(employee);
    setShowEmployeeModal(false);
    setEmployeeSearchQuery("");
  };

  // 현금 결제 추가
  const handleAddCash = () => {
    if (cashForm.amount <= 0) {
      alert("금액을 입력하세요.");
      return;
    }
    const newItem: PaymentItem = {
      ...emptyPaymentItem,
      id: String(Date.now()),
      type: "현금",
      amount: cashForm.amount,
      memo: cashForm.memo,
    };
    setPaymentItems([...paymentItems, newItem]);
    setCashForm({ amount: 0, memo: "" });
    setShowCashModal(false);
  };

  // 은행 결제 추가
  const handleAddBank = () => {
    if (!bankForm.bankName) {
      alert("은행을 선택하세요.");
      return;
    }
    if (bankForm.amount <= 0) {
      alert("금액을 입력하세요.");
      return;
    }
    const newItem: PaymentItem = {
      ...emptyPaymentItem,
      id: String(Date.now()),
      type: "은행",
      bankName: bankForm.bankName,
      amount: bankForm.amount,
      memo: bankForm.memo,
    };
    setPaymentItems([...paymentItems, newItem]);
    setBankForm({ bankName: "", amount: 0, memo: "" });
    setShowBankModal(false);
  };

  // 어음 결제 추가
  const handleAddBill = () => {
    if (!billForm.billNo) {
      alert("어음번호를 입력하세요.");
      return;
    }
    if (billForm.amount <= 0) {
      alert("금액을 입력하세요.");
      return;
    }
    const newItem: PaymentItem = {
      ...emptyPaymentItem,
      id: String(Date.now()),
      type: "어음",
      billNo: billForm.billNo,
      billDate: billForm.billDate,
      dueDate: billForm.dueDate,
      issuer: billForm.issuer,
      amount: billForm.amount,
      memo: billForm.memo,
    };
    setPaymentItems([...paymentItems, newItem]);
    setBillForm({ billNo: "", billDate: "", dueDate: "", issuer: "", amount: 0, memo: "" });
    setShowBillModal(false);
  };

  // 카드 결제 추가
  const handleAddCard = () => {
    if (!cardForm.cardName) {
      alert("카드사를 선택하세요.");
      return;
    }
    if (cardForm.amount <= 0) {
      alert("금액을 입력하세요.");
      return;
    }
    const newItem: PaymentItem = {
      ...emptyPaymentItem,
      id: String(Date.now()),
      type: "카드",
      cardName: cardForm.cardName,
      cardNumber: cardForm.cardNumber,
      approvalNo: cardForm.approvalNo,
      amount: cardForm.amount,
      memo: cardForm.memo,
    };
    setPaymentItems([...paymentItems, newItem]);
    setCardForm({ cardName: "", cardNumber: "", approvalNo: "", amount: 0, memo: "" });
    setShowCardModal(false);
  };

  // 결제 항목 삭제
  const handleDeletePayment = () => {
    if (selectedPaymentRow === null) {
      alert("삭제할 항목을 선택하세요.");
      return;
    }
    if (confirm("선택한 결제 항목을 삭제하시겠습니까?")) {
      setPaymentItems(paymentItems.filter((_, idx) => idx !== selectedPaymentRow));
      setSelectedPaymentRow(null);
    }
  };

  // 저장 - api.erp.payments.create() 호출
  const handleSave = async () => {
    if (!selectedSupplier) {
      alert("지급한거래처를 선택하세요.");
      return;
    }
    if (paymentItems.length === 0) {
      alert("결제 항목을 추가하세요.");
      return;
    }
    try {
      await api.erp.payments.create({
        payment_type: "disbursement",
        payment_date: new Date().toISOString().slice(0, 10),
        customer_id: selectedSupplier.code,
        amount: totalAmount,
        payment_method: paymentItems[0]?.type || "현금",
        memo: memo || undefined,
      });
      alert(`지급전표가 저장되었습니다.\n거래처: ${selectedSupplier.name}\n총 지급액: ${totalAmount.toLocaleString()}원`);
    } catch (err) {
      alert(`지급전표 저장에 실패했습니다.\n거래처: ${selectedSupplier.name}\n총 지급액: ${totalAmount.toLocaleString()}원\n(오프라인 저장)`);
    }
  };

  // 신규 - 폼 초기화
  const handleNew = () => {
    setSelectedSupplier(null);
    setSelectedEmployee(null);
    setMemo("");
    setPaymentItems([]);
    setBankFee(0);
    setDiscount(0);
    setSupplierSearch('');
  };

  // 인쇄
  const handlePrint = () => {
    window.print();
  };

  // 저장 후 추가
  const handleSaveAndAdd = async () => {
    await handleSave();
    handleNew();
  };

  // 취소 = 창닫기
  const handleCancel = () => {
    if (windowContext) {
      windowContext.closeThisWindow();
    } else {
      setSelectedSupplier(null);
      setSelectedEmployee(null);
      setMemo("");
      setPaymentItems([]);
      setBankFee(0);
      setDiscount(0);
    }
  };

  // 탭 버튼 클릭 시 해당 모달 열기
  const handlePaymentTabClick = (tab: "현금" | "은행" | "어음" | "카드") => {
    setActivePaymentTab(tab);
    if (tab === "현금") setShowCashModal(true);
    else if (tab === "은행") setShowBankModal(true);
    else if (tab === "어음") setShowBillModal(true);
    else if (tab === "카드") setShowCardModal(true);
  };

  return (
    <div className="flex h-full flex-col bg-white">
      {/* ■ 기본정보 섹션 */}
      <div className="border-b border-gray-200 p-4">
        <div className="mb-2 flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700">■ 기본정보</span>
        </div>

        <div className="flex gap-6">
          {/* 좌측: 기본정보 입력 */}
          <div className="flex-1 space-y-3">
            <div className="flex items-center gap-4">
              {/* 지급한일자 */}
              <div className="flex items-center gap-2">
                <label className="w-20 text-sm text-gray-600">지급한일자</label>
                <select
                  value={paymentDate}
                  onChange={(e) => setPaymentDate(e.target.value)}
                  className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
                >
                  <option value="2025년 12월 05일">2025년 12월 05일</option>
                  <option value="2025년 12월 04일">2025년 12월 04일</option>
                  <option value="2025년 12월 03일">2025년 12월 03일</option>
                </select>
              </div>

              {/* 지급한거래처(O) - 자동완성 */}
              <div className="relative flex items-center gap-2">
                <label className="text-sm text-gray-600">지급한거래처(O)</label>
                <input
                  type="text"
                  value={selectedSupplier ? selectedSupplier.name : supplierSearch}
                  onChange={(e) => {
                    setSupplierSearch(e.target.value);
                    if (selectedSupplier) setSelectedSupplier(null);
                  }}
                  className="w-40 rounded-md border border-gray-300 px-3 py-1.5 text-sm"
                  placeholder="거래처명 입력..."
                />
                <button
                  onClick={() => setShowSupplierModal(true)}
                  className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm hover:bg-gray-50"
                >
                  ...
                </button>
                {showSupplierSuggestions && supplierSuggestions.length > 0 && (
                  <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-300 rounded shadow-lg z-50 max-h-48 overflow-y-auto">
                    {supplierSuggestions.map((s: any) => (
                      <div
                        key={s.id}
                        onClick={() => {
                          setSelectedSupplier({
                            code: s.code || s.id,
                            name: s.name,
                            representative: s.ceo_name || '',
                            phone: s.phone || '',
                            fax: s.fax || '',
                            creditLimit: s.credit_limit || 0,
                            receivable: 0,
                            payable: s.current_receivable || 0,
                            lastTransaction: '',
                            purchaseCommission: 0,
                          });
                          setSupplierSearch('');
                          setShowSupplierSuggestions(false);
                        }}
                        className="px-3 py-2 text-sm hover:bg-blue-50 cursor-pointer"
                      >
                        {s.name} {s.ceo_name ? `(${s.ceo_name})` : ''}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* 지급담당(U) */}
              <div className="flex items-center gap-2">
                <label className="text-sm text-gray-600">지급담당(U)</label>
                <input
                  type="text"
                  value={selectedEmployee?.name || ""}
                  readOnly
                  className="w-24 rounded-md border border-gray-300 bg-gray-50 px-3 py-1.5 text-sm"
                  placeholder=""
                />
                <button
                  onClick={() => setShowEmployeeModal(true)}
                  className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm hover:bg-gray-50"
                >
                  ...
                </button>
              </div>
            </div>
          </div>

          {/* 우측: 메모사항 */}
          <div className="w-64">
            <label className="mb-1 block text-sm text-gray-600">메모사항</label>
            <textarea
              value={memo}
              onChange={(e) => setMemo(e.target.value)}
              className="h-16 w-full resize-none rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              placeholder=""
            />
          </div>
        </div>
      </div>

      {/* 메인 컨텐츠 영역 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 좌측: 대금결제방법 */}
        <div className="flex-1 border-r border-gray-200 p-4">
          {/* ■ 대금결제방법 */}
          <div className="mb-3 flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">■ 대금결제방법</span>
            <div className="flex">
              {(["현금", "은행", "어음", "카드"] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => handlePaymentTabClick(tab)}
                  className={`border px-4 py-1 text-sm ${
                    activePaymentTab === tab
                      ? "border-blue-600 bg-blue-600 text-white"
                      : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50"
                  } ${tab === "현금" ? "rounded-l-md" : ""} ${tab === "카드" ? "rounded-r-md" : ""}`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>

          {/* 결제 그리드 */}
          <div className="mb-4 h-48 overflow-auto rounded-lg border border-gray-200">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-gray-100">
                <tr>
                  <th className="border-b border-gray-200 px-3 py-2 text-left font-medium text-gray-600">구분</th>
                  <th className="border-b border-gray-200 px-3 py-2 text-left font-medium text-gray-600">상세</th>
                  <th className="border-b border-gray-200 px-3 py-2 text-right font-medium text-gray-600">거래금액</th>
                  <th className="border-b border-gray-200 px-3 py-2 text-left font-medium text-gray-600">비고</th>
                </tr>
              </thead>
              <tbody>
                {paymentItems.map((item, index) => (
                  <tr
                    key={item.id}
                    onClick={() => setSelectedPaymentRow(index)}
                    onDoubleClick={handleDeletePayment}
                    className={`cursor-pointer ${
                      selectedPaymentRow === index
                        ? "bg-blue-600 text-white"
                        : "hover:bg-gray-50"
                    }`}
                  >
                    <td className="border-b border-gray-100 px-3 py-2">{item.type}</td>
                    <td className="border-b border-gray-100 px-3 py-2">
                      {item.type === "현금" && "-"}
                      {item.type === "은행" && item.bankName}
                      {item.type === "어음" && `${item.billNo} (${item.dueDate})`}
                      {item.type === "카드" && `${item.cardName} ${item.approvalNo}`}
                    </td>
                    <td className="border-b border-gray-100 px-3 py-2 text-right">
                      {item.amount.toLocaleString()}
                    </td>
                    <td className="border-b border-gray-100 px-3 py-2">{item.memo}</td>
                  </tr>
                ))}
                {paymentItems.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-3 py-8 text-center text-gray-400">
                      결제 항목이 없습니다. 대금결제방법 탭을 클릭하여 추가하세요.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* 합계 영역 */}
          <div className="space-y-2 rounded-lg border border-gray-200 bg-gray-50 p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">합계:</span>
              <span className="text-lg font-bold text-red-600">{totalAmount.toLocaleString()}</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">은행수수료:</span>
                <input
                  type="number"
                  value={bankFee || ""}
                  onChange={(e) => setBankFee(Number(e.target.value))}
                  className="w-28 rounded-md border border-gray-300 px-2 py-1 text-right text-sm focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">지급시에누리:</span>
                <input
                  type="number"
                  value={discount || ""}
                  onChange={(e) => setDiscount(Number(e.target.value))}
                  className="w-28 rounded-md border border-gray-300 px-2 py-1 text-right text-sm focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div className="h-4 w-40 rounded bg-red-200" style={{ width: `${Math.min(100, (discount / (totalAmount || 1)) * 100)}%` }} />
            </div>
          </div>
        </div>

        {/* 우측: 지급하는 업체는... */}
        <div className="w-80 p-4">
          <div className="mb-3">
            <span className="text-sm font-medium text-gray-700">▶ 지급하는 업체는...</span>
          </div>

          {selectedSupplier ? (
            <div className="space-y-3 rounded-lg border border-gray-200 bg-gray-50 p-4">
              <div className="border-b border-gray-200 pb-2">
                <div className="text-lg font-bold text-gray-800">{selectedSupplier.name}</div>
                <div className="text-sm text-gray-500">{selectedSupplier.code}</div>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">신용한도:</span>
                  <span className="font-medium">{selectedSupplier.creditLimit.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">미지급금액:</span>
                  <span className="font-medium text-red-600">{selectedSupplier.payable.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">최종거래:</span>
                  <span className="font-medium">{selectedSupplier.lastTransaction}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">전화번호:</span>
                  <span className="font-medium">{selectedSupplier.phone}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex h-40 items-center justify-center rounded-lg border border-dashed border-gray-300 bg-gray-50">
              <span className="text-sm text-gray-400">거래처를 선택하세요</span>
            </div>
          )}
        </div>
      </div>

      {/* 하단 버튼 영역 */}
      <div className="flex items-center justify-end gap-2 border-t border-gray-200 bg-gray-50 px-4 py-3">
        <button
          onClick={handleNew}
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          신 규
        </button>
        <button
          onClick={handleSaveAndAdd}
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          저장후추가
        </button>
        <button
          onClick={handleSave}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          저 장
        </button>
        <button
          onClick={handlePrint}
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          인 쇄
        </button>
        <button
          onClick={handleCancel}
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          취 소
        </button>
      </div>

      {/* ========== 모달들 ========== */}

      {/* 거래처 선택 모달 */}
      {showSupplierModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[500px] rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
              <span className="font-medium text-gray-800">거래처 선택</span>
              <button
                onClick={() => {
                  setShowSupplierModal(false);
                  setSupplierSearchQuery("");
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="p-4">
              {/* 검색옵션 */}
              <div className="mb-4 rounded-lg border border-gray-200 bg-gray-50 p-3">
                <div className="text-sm font-medium text-gray-700">검색옵션</div>
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-sm text-gray-600">검색어</span>
                  <input
                    type="text"
                    value={supplierSearchQuery}
                    onChange={(e) => setSupplierSearchQuery(e.target.value)}
                    className="flex-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
                    placeholder="거래처명, 코드, 대표자"
                  />
                  <button className="rounded-md bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300">
                    검 색
                  </button>
                  <button
                    onClick={() => setSupplierSearchQuery("")}
                    className="rounded-md bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
                  >
                    전체검색
                  </button>
                </div>
              </div>

              {/* 거래처 목록 */}
              <div className="h-64 overflow-auto rounded-lg border border-gray-200">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-gray-100">
                    <tr>
                      <th className="border-b border-gray-200 px-3 py-2 text-left font-medium text-gray-600">코드</th>
                      <th className="border-b border-gray-200 px-3 py-2 text-left font-medium text-gray-600">거래처명</th>
                      <th className="border-b border-gray-200 px-3 py-2 text-left font-medium text-gray-600">대표자</th>
                      <th className="border-b border-gray-200 px-3 py-2 text-right font-medium text-gray-600">미지급금액</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredSuppliers.map((supplier) => (
                      <tr
                        key={supplier.code}
                        onClick={() => handleSelectSupplier(supplier)}
                        className="cursor-pointer hover:bg-blue-50"
                      >
                        <td className="border-b border-gray-100 px-3 py-2">{supplier.code}</td>
                        <td className="border-b border-gray-100 px-3 py-2">{supplier.name}</td>
                        <td className="border-b border-gray-100 px-3 py-2">{supplier.representative}</td>
                        <td className="border-b border-gray-100 px-3 py-2 text-right text-red-600">
                          {supplier.payable.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-3 flex justify-between text-sm text-gray-500">
                <span>총 {filteredSuppliers.length}개 검색됨</span>
              </div>
            </div>

            <div className="flex justify-end gap-2 border-t border-gray-200 px-4 py-3">
              <button
                onClick={() => {
                  setShowSupplierModal(false);
                  setSupplierSearchQuery("");
                }}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm hover:bg-gray-50"
              >
                확 인
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 사원 선택 모달 */}
      {showEmployeeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[400px] rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
              <span className="font-medium text-gray-800">사원 선택</span>
              <button
                onClick={() => {
                  setShowEmployeeModal(false);
                  setEmployeeSearchQuery("");
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="p-4">
              {/* 검색옵션 */}
              <div className="mb-4 rounded-lg border border-gray-200 bg-gray-50 p-3">
                <div className="text-sm font-medium text-gray-700">검색옵션</div>
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-sm text-gray-600">검색어</span>
                  <input
                    type="text"
                    value={employeeSearchQuery}
                    onChange={(e) => setEmployeeSearchQuery(e.target.value)}
                    className="flex-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
                  />
                  <button className="rounded-md bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300">
                    검 색
                  </button>
                  <button
                    onClick={() => setEmployeeSearchQuery("")}
                    className="rounded-md bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
                  >
                    전체검색
                  </button>
                </div>
              </div>

              {/* 사원 목록 */}
              <div className="h-48 overflow-auto rounded-lg border border-gray-200">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-gray-100">
                    <tr>
                      <th className="border-b border-gray-200 px-3 py-2 text-left font-medium text-gray-600">코드</th>
                      <th className="border-b border-gray-200 px-3 py-2 text-left font-medium text-gray-600">성명</th>
                      <th className="border-b border-gray-200 px-3 py-2 text-left font-medium text-gray-600">부서</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredEmployees.map((employee) => (
                      <tr
                        key={employee.code}
                        onClick={() => handleSelectEmployee(employee)}
                        className="cursor-pointer hover:bg-blue-50"
                      >
                        <td className="border-b border-gray-100 px-3 py-2">{employee.code}</td>
                        <td className="border-b border-gray-100 px-3 py-2">{employee.name}</td>
                        <td className="border-b border-gray-100 px-3 py-2">{employee.department}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-3 flex justify-between text-sm text-gray-500">
                <span>총 {filteredEmployees.length}개 검색됨</span>
              </div>
            </div>

            <div className="flex justify-end gap-2 border-t border-gray-200 px-4 py-3">
              <button
                onClick={() => {
                  setShowEmployeeModal(false);
                  setEmployeeSearchQuery("");
                }}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm hover:bg-gray-50"
              >
                확 인
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 현금 결제 모달 */}
      {showCashModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[350px] rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-200 bg-blue-600 px-4 py-2">
              <span className="font-medium text-white">현금 결제</span>
              <button
                onClick={() => setShowCashModal(false)}
                className="text-white/80 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="p-4">
              <div className="space-y-4">
                <div>
                  <label className="mb-1 block text-sm text-gray-600">금액</label>
                  <input
                    type="number"
                    value={cashForm.amount || ""}
                    onChange={(e) => setCashForm({ ...cashForm, amount: Number(e.target.value) })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-right text-sm focus:border-blue-500 focus:outline-none"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-600">비고</label>
                  <input
                    type="text"
                    value={cashForm.memo}
                    onChange={(e) => setCashForm({ ...cashForm, memo: e.target.value })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 border-t border-gray-200 px-4 py-3">
              <button
                onClick={handleAddCash}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                확 인
              </button>
              <button
                onClick={() => setShowCashModal(false)}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm hover:bg-gray-50"
              >
                취 소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 은행 결제 모달 */}
      {showBankModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[400px] rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-200 bg-blue-600 px-4 py-2">
              <span className="font-medium text-white">계좌 결제</span>
              <button
                onClick={() => setShowBankModal(false)}
                className="text-white/80 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="p-4">
              <div className="space-y-4">
                <div>
                  <label className="mb-1 block text-sm text-gray-600">은행</label>
                  <select
                    value={bankForm.bankName}
                    onChange={(e) => setBankForm({ ...bankForm, bankName: e.target.value })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  >
                    <option value="">선택하세요</option>
                    {apiBanks.map((bank) => (
                      <option key={bank.code} value={bank.name}>
                        {bank.name} ({bank.accountNumber})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-600">금액</label>
                  <input
                    type="number"
                    value={bankForm.amount || ""}
                    onChange={(e) => setBankForm({ ...bankForm, amount: Number(e.target.value) })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-right text-sm focus:border-blue-500 focus:outline-none"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-600">비고</label>
                  <input
                    type="text"
                    value={bankForm.memo}
                    onChange={(e) => setBankForm({ ...bankForm, memo: e.target.value })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 border-t border-gray-200 px-4 py-3">
              <button
                onClick={handleAddBank}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                확 인
              </button>
              <button
                onClick={() => setShowBankModal(false)}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm hover:bg-gray-50"
              >
                취 소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 어음 결제 모달 */}
      {showBillModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[450px] rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-200 bg-blue-600 px-4 py-2">
              <span className="font-medium text-white">어음 결제</span>
              <button
                onClick={() => setShowBillModal(false)}
                className="text-white/80 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="p-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-sm text-gray-600">어음번호</label>
                  <input
                    type="text"
                    value={billForm.billNo}
                    onChange={(e) => setBillForm({ ...billForm, billNo: e.target.value })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-600">발행인</label>
                  <input
                    type="text"
                    value={billForm.issuer}
                    onChange={(e) => setBillForm({ ...billForm, issuer: e.target.value })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-600">어음일자</label>
                  <input
                    type="date"
                    value={billForm.billDate}
                    onChange={(e) => setBillForm({ ...billForm, billDate: e.target.value })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-600">만기일</label>
                  <input
                    type="date"
                    value={billForm.dueDate}
                    onChange={(e) => setBillForm({ ...billForm, dueDate: e.target.value })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div className="col-span-2">
                  <label className="mb-1 block text-sm text-gray-600">금액</label>
                  <input
                    type="number"
                    value={billForm.amount || ""}
                    onChange={(e) => setBillForm({ ...billForm, amount: Number(e.target.value) })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-right text-sm focus:border-blue-500 focus:outline-none"
                    placeholder="0"
                  />
                </div>
                <div className="col-span-2">
                  <label className="mb-1 block text-sm text-gray-600">비고</label>
                  <input
                    type="text"
                    value={billForm.memo}
                    onChange={(e) => setBillForm({ ...billForm, memo: e.target.value })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 border-t border-gray-200 px-4 py-3">
              <button
                onClick={handleAddBill}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                확 인
              </button>
              <button
                onClick={() => setShowBillModal(false)}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm hover:bg-gray-50"
              >
                취 소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 카드 결제 모달 */}
      {showCardModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[400px] rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-200 bg-blue-600 px-4 py-2">
              <span className="font-medium text-white">카드 결제</span>
              <button
                onClick={() => setShowCardModal(false)}
                className="text-white/80 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="p-4">
              <div className="space-y-4">
                <div>
                  <label className="mb-1 block text-sm text-gray-600">카드사</label>
                  <select
                    value={cardForm.cardName}
                    onChange={(e) => setCardForm({ ...cardForm, cardName: e.target.value })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  >
                    <option value="">선택하세요</option>
                    {apiCards.map((card) => (
                      <option key={card.code} value={card.name}>
                        {card.name} (수수료 {card.feeRate}%)
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-600">카드번호</label>
                  <input
                    type="text"
                    value={cardForm.cardNumber}
                    onChange={(e) => setCardForm({ ...cardForm, cardNumber: e.target.value })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                    placeholder="0000-0000-0000-0000"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-600">승인번호</label>
                  <input
                    type="text"
                    value={cardForm.approvalNo}
                    onChange={(e) => setCardForm({ ...cardForm, approvalNo: e.target.value })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-600">금액</label>
                  <input
                    type="number"
                    value={cardForm.amount || ""}
                    onChange={(e) => setCardForm({ ...cardForm, amount: Number(e.target.value) })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-right text-sm focus:border-blue-500 focus:outline-none"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-600">비고</label>
                  <input
                    type="text"
                    value={cardForm.memo}
                    onChange={(e) => setCardForm({ ...cardForm, memo: e.target.value })}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 border-t border-gray-200 px-4 py-3">
              <button
                onClick={handleAddCard}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                확 인
              </button>
              <button
                onClick={() => setShowCardModal(false)}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm hover:bg-gray-50"
              >
                취 소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
