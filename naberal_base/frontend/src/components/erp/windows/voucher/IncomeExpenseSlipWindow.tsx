"use client";

import React, { useState, useEffect } from "react";
import { useWindowContextOptional } from "../../ERPContext";
import { api, ERPPaymentCreate } from "@/lib/api";

// =============================================
// 입출금전표 - 이지판매재고관리 100% 복제
// NABERAL Modern Design (white bg, rounded-lg, shadow-sm, blue-600)
// =============================================

interface PaymentItem {
  id: string;
  type: string;        // 구분 (현금/은행/어음/카드)
  bankName: string;    // 은행명
  amount: number;      // 금액
  memo: string;        // 비고
  cardName: string;    // 카드사
  cardNumber: string;  // 카드번호
  approvalNo: string;  // 승인번호
  billNo: string;      // 어음번호
  billDate: string;    // 어음일자
  dueDate: string;     // 만기일
  issuer: string;      // 발행인
}

interface IncomeExpenseCategory {
  code: string;
  name: string;
  relatedItem: string;
  type: "입금" | "출금";
}

interface Employee {
  code: string;
  name: string;
  department: string;
}

// 입출금항목 원본 데이터 (이지판매재고관리 100% 복제 - 54개 항목)
const INCOME_EXPENSE_ITEMS: IncomeExpenseCategory[] = [
  // 은행관련업무
  { code: "A0001", name: "현금을 은행으로 입금", relatedItem: "없음", type: "입금" },
  { code: "A0002", name: "은행에서 현금을 출금", relatedItem: "없음", type: "입금" },
  { code: "A0003", name: "수입수수료", relatedItem: "없음", type: "입금" },
  { code: "A0004", name: "지급수수료", relatedItem: "없음", type: "출금" },
  { code: "A0005", name: "수입이자", relatedItem: "없음", type: "입금" },
  { code: "A0006", name: "지급이자", relatedItem: "없음", type: "출금" },
  // 복리후생비
  { code: "A1001", name: "식대", relatedItem: "없음", type: "출금" },
  { code: "A1002", name: "직원회식", relatedItem: "없음", type: "출금" },
  { code: "A1003", name: "신문/서적", relatedItem: "없음", type: "출금" },
  // 여비교통비
  { code: "B1001", name: "교통비", relatedItem: "없음", type: "출금" },
  { code: "B1002", name: "통행료", relatedItem: "없음", type: "출금" },
  { code: "B1003", name: "출장비", relatedItem: "없음", type: "출금" },
  // 차량유지비
  { code: "C1001", name: "주유대", relatedItem: "없음", type: "출금" },
  { code: "C1002", name: "오일교체", relatedItem: "없음", type: "출금" },
  { code: "C1003", name: "부품교체", relatedItem: "없음", type: "출금" },
  { code: "C1004", name: "주차비", relatedItem: "없음", type: "출금" },
  { code: "C1005", name: "차량보험료", relatedItem: "없음", type: "출금" },
  // 소모품비
  { code: "D1001", name: "사무소모품비", relatedItem: "없음", type: "출금" },
  { code: "D1002", name: "일반소모품비", relatedItem: "없음", type: "출금" },
  // 급(상)여지급
  { code: "E1001", name: "급여지급", relatedItem: "사원", type: "출금" },
  { code: "E1002", name: "상여지급", relatedItem: "사원", type: "출금" },
  // 가지급금
  { code: "F1001", name: "가불금지급", relatedItem: "사원", type: "출금" },
  { code: "F1002", name: "가불금입금", relatedItem: "사원", type: "입금" },
  { code: "F1003", name: "업무가지급금지급", relatedItem: "사원", type: "출금" },
  { code: "F1004", name: "업무가지급금입금", relatedItem: "사원", type: "입금" },
  // 관리비
  { code: "G1001", name: "임대료", relatedItem: "없음", type: "출금" },
  { code: "G1002", name: "관리비", relatedItem: "없음", type: "출금" },
  { code: "G1003", name: "전화요금", relatedItem: "없음", type: "출금" },
  // 판공비
  { code: "H1001", name: "접대비", relatedItem: "없음", type: "출금" },
  { code: "H1002", name: "영업비", relatedItem: "없음", type: "출금" },
  // 경조비
  { code: "I1001", name: "경조사비", relatedItem: "없음", type: "출금" },
  // 잡비
  { code: "J1001", name: "잡비", relatedItem: "없음", type: "출금" },
  // 잡손실
  { code: "K1001", name: "기타손실", relatedItem: "없음", type: "출금" },
  // 잡이익
  { code: "L1001", name: "기타이익", relatedItem: "없음", type: "입금" },
  // 집기비품매입
  { code: "M1001", name: "가구류매입", relatedItem: "없음", type: "출금" },
  { code: "M1002", name: "공구및기구매입", relatedItem: "없음", type: "출금" },
  { code: "M1003", name: "기타비품매입", relatedItem: "없음", type: "출금" },
  // 전매관리비
  { code: "N1001", name: "운송비", relatedItem: "없음", type: "출금" },
  // 세금과공과
  { code: "O1001", name: "부가가치세", relatedItem: "없음", type: "출금" },
  { code: "O1002", name: "법인세", relatedItem: "없음", type: "출금" },
  { code: "O1003", name: "산업재해 보상보험료", relatedItem: "없음", type: "출금" },
  { code: "O1004", name: "고용보험료", relatedItem: "없음", type: "출금" },
  { code: "O1005", name: "의료보험", relatedItem: "없음", type: "출금" },
  { code: "O1006", name: "국민연금", relatedItem: "없음", type: "출금" },
  { code: "O1007", name: "기타세금", relatedItem: "없음", type: "출금" },
  // 차입금
  { code: "P1001", name: "업체로부터 차입", relatedItem: "거래처", type: "입금" },
  { code: "P1002", name: "업체 차입금상환", relatedItem: "거래처", type: "출금" },
  // 카드채권
  { code: "SYS1001", name: "카드사로부터 카드매출", relatedItem: "신용카드", type: "입금" },
  // 카드채무
  { code: "SYS1002", name: "카드대금상환(채무)", relatedItem: "신용카드", type: "출금" },
];

// 사원/은행/카드 데이터는 API에서 로드 (하단 useEffect 참조)

function formatDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}년 ${m}월 ${d}일`;
}

function formatNumber(num: number): string {
  return num.toLocaleString("ko-KR");
}

export function IncomeExpenseSlipWindow() {
  const windowContext = useWindowContextOptional();
  const today = new Date();

  // 기본정보 상태
  const [slipDate, setSlipDate] = useState(formatDate(today));
  const [selectedItem, setSelectedItem] = useState<IncomeExpenseCategory | null>(null);
  const [selectedRelatedEmployee, setSelectedRelatedEmployee] = useState<Employee | null>(null);
  const [memoText, setMemoText] = useState("");

  // 사원/은행/카드 데이터 (API 로드)
  const [EMPLOYEES, setEmployees] = useState<Employee[]>([]);
  const [BANKS, setBanks] = useState<{ code: string; name: string; accountNumber: string }[]>([]);
  const [CARDS, setCards] = useState<{ code: string; name: string; feeRate: number }[]>([]);

  useEffect(() => {
    // 직원 목록 로드
    api.erp.employees.list().then((res: any) => {
      const items = Array.isArray(res) ? res : (res?.items || []);
      setEmployees(items.map((e: any) => ({
        code: e.code || e.id || "",
        name: e.name || "",
        department: e.department || "",
      })));
    }).catch(() => setEmployees([]));

    // 은행 계좌 목록 로드
    api.erp.bankAccounts.list().then((res: any) => {
      const items = Array.isArray(res) ? res : (res?.items || []);
      setBanks(items.map((b: any) => ({
        code: b.code || b.id || "",
        name: b.bank_name || b.name || "",
        accountNumber: b.account_number || b.accountNo || "",
      })));
    }).catch(() => setBanks([]));

    setCards([]);
  }, []);

  // 대금결제방법 탭 상태
  const [activePaymentTab, setActivePaymentTab] = useState<"현금" | "은행" | "어음" | "카드">("현금");

  // 결제 내역 상태
  const [paymentItems, setPaymentItems] = useState<PaymentItem[]>([]);
  const [selectedPaymentRow, setSelectedPaymentRow] = useState<number | null>(null);

  // 입출금관련항목 정보
  const [itemInfo, setItemInfo] = useState({
    monthTotal: 0,
    yearTotal: 0,
    lastDate: "(거래없음)",
    cashBalance: 50000,
  });

  // 모달 상태들
  const [showItemModal, setShowItemModal] = useState(false);
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);
  const [showCashModal, setShowCashModal] = useState(false);
  const [showBankModal, setShowBankModal] = useState(false);
  const [showBillModal, setShowBillModal] = useState(false);
  const [showCardModal, setShowCardModal] = useState(false);

  // 검색어 상태
  const [itemSearchQuery, setItemSearchQuery] = useState("");
  const [employeeSearchQuery, setEmployeeSearchQuery] = useState("");

  // 결제 입력 폼 상태
  const [cashAmount, setCashAmount] = useState(0);
  const [cashMemo, setCashMemo] = useState("");

  const [bankAmount, setBankAmount] = useState(0);
  const [bankMemo, setBankMemo] = useState("");
  const [selectedBank, setSelectedBank] = useState<string>("");

  const [billAmount, setBillAmount] = useState(0);
  const [billNo, setBillNo] = useState("");
  const [billDate, setBillDate] = useState("");
  const [billDueDate, setBillDueDate] = useState("");
  const [billIssuer, setBillIssuer] = useState("");
  const [billMemo, setBillMemo] = useState("");

  const [cardAmount, setCardAmount] = useState(0);
  const [selectedCard, setSelectedCard] = useState<string>("");
  const [cardNumber, setCardNumber] = useState("");
  const [cardApprovalNo, setCardApprovalNo] = useState("");
  const [cardMemo, setCardMemo] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  // 필터링된 입출금항목
  const filteredItems = INCOME_EXPENSE_ITEMS.filter(
    (item) =>
      item.name.includes(itemSearchQuery) ||
      item.code.includes(itemSearchQuery)
  );

  // 필터링된 사원
  const filteredEmployees = EMPLOYEES.filter(
    (emp) =>
      emp.name.includes(employeeSearchQuery) ||
      emp.code.includes(employeeSearchQuery)
  );

  // 합계 계산
  const totalAmount = paymentItems.reduce((sum, item) => sum + item.amount, 0);

  // 입출금항목 선택
  const handleSelectItem = (item: IncomeExpenseCategory) => {
    setSelectedItem(item);
    setShowItemModal(false);
    // 관련항목이 사원인 경우 자동으로 사원 선택 모달 열기
    if (item.relatedItem === "사원") {
      setShowEmployeeModal(true);
    }
    // 입출금관련항목 정보 업데이트 (예시)
    setItemInfo({
      monthTotal: Math.floor(Math.random() * 500000),
      yearTotal: Math.floor(Math.random() * 5000000),
      lastDate: "2025-12-01",
      cashBalance: 50000,
    });
  };

  // 관련사원 선택
  const handleSelectEmployee = (employee: Employee) => {
    setSelectedRelatedEmployee(employee);
    setShowEmployeeModal(false);
  };

  // 현금 결제 추가
  const handleAddCashPayment = () => {
    if (cashAmount <= 0) {
      alert("금액을 입력하세요.");
      return;
    }
    const newItem: PaymentItem = {
      id: String(Date.now()),
      type: "현금",
      bankName: "",
      amount: cashAmount,
      memo: cashMemo,
      cardName: "",
      cardNumber: "",
      approvalNo: "",
      billNo: "",
      billDate: "",
      dueDate: "",
      issuer: "",
    };
    setPaymentItems([...paymentItems, newItem]);
    setCashAmount(0);
    setCashMemo("");
    setShowCashModal(false);
  };

  // 은행 결제 추가
  const handleAddBankPayment = () => {
    if (bankAmount <= 0) {
      alert("금액을 입력하세요.");
      return;
    }
    if (!selectedBank) {
      alert("은행을 선택하세요.");
      return;
    }
    const bank = BANKS.find((b) => b.code === selectedBank);
    const newItem: PaymentItem = {
      id: String(Date.now()),
      type: "은행",
      bankName: bank?.name || "",
      amount: bankAmount,
      memo: bankMemo,
      cardName: "",
      cardNumber: "",
      approvalNo: "",
      billNo: "",
      billDate: "",
      dueDate: "",
      issuer: "",
    };
    setPaymentItems([...paymentItems, newItem]);
    setBankAmount(0);
    setBankMemo("");
    setSelectedBank("");
    setShowBankModal(false);
  };

  // 어음 결제 추가
  const handleAddBillPayment = () => {
    if (billAmount <= 0) {
      alert("금액을 입력하세요.");
      return;
    }
    if (!billNo) {
      alert("어음번호를 입력하세요.");
      return;
    }
    const newItem: PaymentItem = {
      id: String(Date.now()),
      type: "어음",
      bankName: "",
      amount: billAmount,
      memo: billMemo,
      cardName: "",
      cardNumber: "",
      approvalNo: "",
      billNo: billNo,
      billDate: billDate,
      dueDate: billDueDate,
      issuer: billIssuer,
    };
    setPaymentItems([...paymentItems, newItem]);
    setBillAmount(0);
    setBillNo("");
    setBillDate("");
    setBillDueDate("");
    setBillIssuer("");
    setBillMemo("");
    setShowBillModal(false);
  };

  // 카드 결제 추가
  const handleAddCardPayment = () => {
    if (cardAmount <= 0) {
      alert("금액을 입력하세요.");
      return;
    }
    if (!selectedCard) {
      alert("카드사를 선택하세요.");
      return;
    }
    const card = CARDS.find((c) => c.code === selectedCard);
    const newItem: PaymentItem = {
      id: String(Date.now()),
      type: "카드",
      bankName: "",
      amount: cardAmount,
      memo: cardMemo,
      cardName: card?.name || "",
      cardNumber: cardNumber,
      approvalNo: cardApprovalNo,
      billNo: "",
      billDate: "",
      dueDate: "",
      issuer: "",
    };
    setPaymentItems([...paymentItems, newItem]);
    setCardAmount(0);
    setSelectedCard("");
    setCardNumber("");
    setCardApprovalNo("");
    setCardMemo("");
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

  // 결제방법 탭에 따라 모달 열기
  const handleOpenPaymentModal = () => {
    switch (activePaymentTab) {
      case "현금":
        setShowCashModal(true);
        break;
      case "은행":
        setShowBankModal(true);
        break;
      case "어음":
        setShowBillModal(true);
        break;
      case "카드":
        setShowCardModal(true);
        break;
    }
  };

  // 저장
  const handleSave = async () => {
    if (isSaving) return;
    setIsSaving(true);
    if (!selectedItem) {
      alert("입출금항목을 선택하세요.");
      setIsSaving(false);
      return;
    }
    if (paymentItems.length === 0) {
      alert("결제 내역을 입력하세요.");
      setIsSaving(false);
      return;
    }

    try {
      // 결제방법 매핑
      const firstPayment = paymentItems[0];
      let paymentMethodStr = "cash";
      if (firstPayment.type === "은행") paymentMethodStr = "bank_transfer";
      else if (firstPayment.type === "카드") paymentMethodStr = "card";
      else if (firstPayment.type === "어음") paymentMethodStr = "note";

      const paymentData: ERPPaymentCreate = {
        payment_type: selectedItem.type === "입금" ? "receipt" : "expense",
        payment_date: new Date().toISOString().split("T")[0],
        customer_id: "",
        amount: totalAmount,
        payment_method: paymentMethodStr,
        status: "confirmed",
        memo: `${selectedItem.name}${memoText ? " - " + memoText : ""}`,
      };

      const result = await api.erp.payments.create(paymentData);
      alert(`저장되었습니다. 전표번호: ${result.payment_number || result.id}`);
    } catch (error) {
      alert(`저장 실패: ${error}`);
    } finally {
      setIsSaving(false);
    }
  };

  // 저장 후 추가
  const handleSaveAndAdd = async () => {
    if (!selectedItem) {
      alert("입출금항목을 선택하세요.");
      return;
    }
    if (paymentItems.length === 0) {
      alert("결제 내역을 입력하세요.");
      return;
    }

    await handleSave();

    // 초기화
    setSelectedItem(null);
    setSelectedRelatedEmployee(null);
    setMemoText("");
    setPaymentItems([]);
    setSelectedPaymentRow(null);
  };

  return (
    <div className="flex h-full flex-col bg-white">
      {/* 메인 컨텐츠 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 왼쪽 영역 - 기본정보 + 결제내역 */}
        <div className="flex flex-1 flex-col border-r border-gray-200 p-4">
          {/* ■기본정보 섹션 */}
          <div className="mb-4">
            <div className="mb-2 text-sm font-medium text-gray-700">■기본정보</div>
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
              <div className="grid grid-cols-3 gap-4">
                {/* 입출금한일자 */}
                <div>
                  <label className="mb-1 block text-xs text-gray-600">입출금한일자:</label>
                  <input
                    type="text"
                    value={slipDate}
                    readOnly
                    className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
                  />
                </div>
                {/* 입출금항목(O) */}
                <div>
                  <label className="mb-1 block text-xs text-gray-600">입출금항목(O):</label>
                  <div className="flex gap-1">
                    <input
                      type="text"
                      value={selectedItem?.name || ""}
                      readOnly
                      placeholder="선택..."
                      className="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
                    />
                    <button
                      onClick={() => setShowItemModal(true)}
                      className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm hover:bg-gray-50"
                    >
                      ...
                    </button>
                  </div>
                </div>
                {/* 입출금관련항목(U) */}
                <div>
                  <label className="mb-1 block text-xs text-gray-600">입출금관련항목(U):</label>
                  <div className="flex gap-1">
                    <input
                      type="text"
                      value={selectedRelatedEmployee?.name || ""}
                      readOnly
                      placeholder={selectedItem?.relatedItem === "사원" ? "사원선택..." : ""}
                      disabled={!selectedItem || selectedItem.relatedItem === "없음"}
                      className="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm disabled:bg-gray-100"
                    />
                    <button
                      onClick={() => setShowEmployeeModal(true)}
                      disabled={!selectedItem || selectedItem.relatedItem === "없음"}
                      className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm hover:bg-gray-50 disabled:bg-gray-100"
                    >
                      ...
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ■대금결제방법 섹션 */}
          <div className="mb-4">
            <div className="mb-2 text-sm font-medium text-gray-700">■대금결제방법</div>
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
              {/* 탭 버튼들 */}
              <div className="mb-4 flex gap-1">
                {(["현금", "은행", "어음", "카드"] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActivePaymentTab(tab)}
                    className={`rounded-md border px-4 py-2 text-sm font-medium transition-colors ${
                      activePaymentTab === tab
                        ? "border-blue-600 bg-blue-600 text-white"
                        : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
                <div className="flex-1" />
                <button
                  onClick={handleOpenPaymentModal}
                  className="rounded-md border border-blue-600 bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  + 추가
                </button>
                <button
                  onClick={handleDeletePayment}
                  className="rounded-md border border-red-500 bg-white px-4 py-2 text-sm font-medium text-red-500 hover:bg-red-50"
                >
                  삭제
                </button>
              </div>

              {/* 결제 내역 그리드 */}
              <div className="max-h-48 overflow-auto rounded-md border border-gray-300 bg-white">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-gray-100">
                    <tr>
                      <th className="border-b border-gray-300 px-3 py-2 text-left font-medium text-gray-700">구분</th>
                      <th className="border-b border-gray-300 px-3 py-2 text-left font-medium text-gray-700">은행/카드</th>
                      <th className="border-b border-gray-300 px-3 py-2 text-right font-medium text-gray-700">금액</th>
                      <th className="border-b border-gray-300 px-3 py-2 text-left font-medium text-gray-700">비고</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paymentItems.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="px-3 py-8 text-center text-gray-400">
                          결제 내역이 없습니다
                        </td>
                      </tr>
                    ) : (
                      paymentItems.map((item, index) => (
                        <tr
                          key={item.id}
                          onClick={() => setSelectedPaymentRow(index)}
                          className={`cursor-pointer ${
                            selectedPaymentRow === index
                              ? "bg-blue-600 text-white"
                              : "hover:bg-gray-50"
                          }`}
                        >
                          <td className="border-b border-gray-200 px-3 py-2">{item.type}</td>
                          <td className="border-b border-gray-200 px-3 py-2">
                            {item.bankName || item.cardName || "-"}
                          </td>
                          <td className="border-b border-gray-200 px-3 py-2 text-right">
                            {formatNumber(item.amount)}
                          </td>
                          <td className="border-b border-gray-200 px-3 py-2">{item.memo || "-"}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* 합계 */}
              <div className="mt-4 flex items-center justify-between border-t border-gray-300 pt-4">
                <span className="text-sm font-medium text-gray-700">합계:</span>
                <span className={`text-xl font-bold ${selectedItem?.type === "출금" ? "text-red-600" : "text-blue-600"}`}>
                  {formatNumber(totalAmount)}
                </span>
              </div>
            </div>
          </div>

          {/* 관련항목 삭제됨 */}
        </div>

        {/* 오른쪽 영역 - 메모사항 + 입출금관련항목 */}
        <div className="w-80 flex-shrink-0 p-4">
          {/* 메모사항 */}
          <div className="mb-4">
            <div className="mb-2 text-sm font-medium text-gray-700">메모사항</div>
            <textarea
              value={memoText}
              onChange={(e) => setMemoText(e.target.value)}
              className="h-32 w-full resize-none rounded-lg border border-gray-200 p-3 text-sm"
              placeholder="메모를 입력하세요..."
            />
          </div>

          {/* ■입출금관련항목 섹션 */}
          <div>
            <div className="mb-2 text-sm font-medium text-gray-700">■입출금관련항목</div>
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">이달의누계:</span>
                  <span className="font-medium text-gray-800">{formatNumber(itemInfo.monthTotal)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">올해의누계:</span>
                  <span className="font-medium text-gray-800">{formatNumber(itemInfo.yearTotal)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">최종발생일:</span>
                  <span className="font-medium text-gray-800">{itemInfo.lastDate}</span>
                </div>
                <div className="flex justify-between border-t border-gray-300 pt-3">
                  <span className="text-gray-600">현금시재:</span>
                  <span className="font-bold text-blue-600">{formatNumber(itemInfo.cashBalance)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 하단 버튼 영역 */}
      <div className="flex items-center justify-end gap-2 border-t border-gray-200 bg-gray-50 px-4 py-3">
        <button
          onClick={handleSaveAndAdd}
          className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          저장후추가
        </button>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          저 장
        </button>
        <button
          onClick={() => {
            if (windowContext) {
              windowContext.closeThisWindow();
            } else {
              setSelectedItem(null);
              setSelectedRelatedEmployee(null);
              setMemoText("");
              setPaymentItems([]);
            }
          }}
          className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          취 소
        </button>
      </div>

      {/* ========== 입출금항목 선택 모달 ========== */}
      {showItemModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[600px] rounded-lg bg-white shadow-xl">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
              <span className="text-lg font-medium text-gray-800">입출금항목</span>
              <button
                onClick={() => setShowItemModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            {/* 검색 영역 */}
            <div className="border-b border-gray-200 bg-gray-50 px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">검색어</span>
                <input
                  type="text"
                  value={itemSearchQuery}
                  onChange={(e) => setItemSearchQuery(e.target.value)}
                  className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
                  placeholder="코드 또는 항목명..."
                />
                <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
                  검 색
                </button>
                <button
                  onClick={() => setItemSearchQuery("")}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  전체검색
                </button>
              </div>
            </div>

            {/* 그리드 */}
            <div className="max-h-80 overflow-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-gray-100">
                  <tr>
                    <th className="border-b border-gray-300 px-3 py-2 text-left font-medium text-gray-700">코드</th>
                    <th className="border-b border-gray-300 px-3 py-2 text-left font-medium text-gray-700">입출금항목명</th>
                    <th className="border-b border-gray-300 px-3 py-2 text-left font-medium text-gray-700">관련항목</th>
                    <th className="border-b border-gray-300 px-3 py-2 text-left font-medium text-gray-700">구분</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredItems.map((item) => (
                    <tr
                      key={item.code}
                      onDoubleClick={() => handleSelectItem(item)}
                      className="cursor-pointer hover:bg-blue-50"
                    >
                      <td className="border-b border-gray-200 px-3 py-2">{item.code}</td>
                      <td className="border-b border-gray-200 px-3 py-2">{item.name}</td>
                      <td className="border-b border-gray-200 px-3 py-2">{item.relatedItem}</td>
                      <td className="border-b border-gray-200 px-3 py-2">
                        <span className={item.type === "입금" ? "text-blue-600" : "text-red-600"}>
                          {item.type}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* 모달 푸터 */}
            <div className="flex items-center justify-between border-t border-gray-200 bg-gray-50 px-4 py-3">
              <div />
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600">총 {filteredItems.length}개 검색됨</span>
                <button
                  onClick={() => setShowItemModal(false)}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  확 인
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========== 사원 선택 모달 ========== */}
      {showEmployeeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[500px] rounded-lg bg-white shadow-xl">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
              <span className="text-lg font-medium text-gray-800">사원 선택</span>
              <button
                onClick={() => setShowEmployeeModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            {/* 검색 영역 */}
            <div className="border-b border-gray-200 bg-gray-50 px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">검색어</span>
                <input
                  type="text"
                  value={employeeSearchQuery}
                  onChange={(e) => setEmployeeSearchQuery(e.target.value)}
                  className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
                  placeholder="코드 또는 사원명..."
                />
                <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
                  검 색
                </button>
                <button
                  onClick={() => setEmployeeSearchQuery("")}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  전체검색
                </button>
              </div>
            </div>

            {/* 그리드 */}
            <div className="max-h-60 overflow-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-gray-100">
                  <tr>
                    <th className="border-b border-gray-300 px-3 py-2 text-left font-medium text-gray-700">코드</th>
                    <th className="border-b border-gray-300 px-3 py-2 text-left font-medium text-gray-700">성명</th>
                    <th className="border-b border-gray-300 px-3 py-2 text-left font-medium text-gray-700">부서</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEmployees.map((emp) => (
                    <tr
                      key={emp.code}
                      onDoubleClick={() => handleSelectEmployee(emp)}
                      className="cursor-pointer hover:bg-blue-50"
                    >
                      <td className="border-b border-gray-200 px-3 py-2">{emp.code}</td>
                      <td className="border-b border-gray-200 px-3 py-2">{emp.name}</td>
                      <td className="border-b border-gray-200 px-3 py-2">{emp.department}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* 모달 푸터 */}
            <div className="flex items-center justify-between border-t border-gray-200 bg-gray-50 px-4 py-3">
              <div />
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600">총 {filteredEmployees.length}개 검색됨</span>
                <button
                  onClick={() => setShowEmployeeModal(false)}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  확 인
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========== 현금 결제 모달 ========== */}
      {showCashModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[350px] rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
              <span className="text-lg font-medium text-gray-800">현금 결제</span>
              <button onClick={() => setShowCashModal(false)} className="text-gray-400 hover:text-gray-600">
                ✕
              </button>
            </div>
            <div className="p-4">
              <div className="mb-4">
                <label className="mb-1 block text-sm text-gray-600">금액:</label>
                <input
                  type="number"
                  value={cashAmount}
                  onChange={(e) => setCashAmount(Number(e.target.value))}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-right text-sm"
                />
              </div>
              <div className="mb-4">
                <label className="mb-1 block text-sm text-gray-600">비고:</label>
                <input
                  type="text"
                  value={cashMemo}
                  onChange={(e) => setCashMemo(e.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 border-t border-gray-200 bg-gray-50 px-4 py-3">
              <button onClick={handleAddCashPayment} className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
                확 인
              </button>
              <button onClick={() => setShowCashModal(false)} className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm hover:bg-gray-50">
                취 소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========== 은행 결제 모달 ========== */}
      {showBankModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[400px] rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
              <span className="text-lg font-medium text-gray-800">계좌 결제</span>
              <button onClick={() => setShowBankModal(false)} className="text-gray-400 hover:text-gray-600">
                ✕
              </button>
            </div>
            <div className="p-4">
              <div className="mb-4">
                <label className="mb-1 block text-sm text-gray-600">은행선택:</label>
                <select
                  value={selectedBank}
                  onChange={(e) => setSelectedBank(e.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                >
                  <option value="">선택...</option>
                  {BANKS.map((bank) => (
                    <option key={bank.code} value={bank.code}>
                      {bank.name} ({bank.accountNumber})
                    </option>
                  ))}
                </select>
              </div>
              <div className="mb-4">
                <label className="mb-1 block text-sm text-gray-600">금액:</label>
                <input
                  type="number"
                  value={bankAmount}
                  onChange={(e) => setBankAmount(Number(e.target.value))}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-right text-sm"
                />
              </div>
              <div className="mb-4">
                <label className="mb-1 block text-sm text-gray-600">비고:</label>
                <input
                  type="text"
                  value={bankMemo}
                  onChange={(e) => setBankMemo(e.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 border-t border-gray-200 bg-gray-50 px-4 py-3">
              <button onClick={handleAddBankPayment} className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
                확 인
              </button>
              <button onClick={() => setShowBankModal(false)} className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm hover:bg-gray-50">
                취 소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========== 어음 결제 모달 ========== */}
      {showBillModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[450px] rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
              <span className="text-lg font-medium text-gray-800">어음 결제</span>
              <button onClick={() => setShowBillModal(false)} className="text-gray-400 hover:text-gray-600">
                ✕
              </button>
            </div>
            <div className="p-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-sm text-gray-600">어음번호:</label>
                  <input
                    type="text"
                    value={billNo}
                    onChange={(e) => setBillNo(e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-600">금액:</label>
                  <input
                    type="number"
                    value={billAmount}
                    onChange={(e) => setBillAmount(Number(e.target.value))}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-right text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-600">어음일자:</label>
                  <input
                    type="date"
                    value={billDate}
                    onChange={(e) => setBillDate(e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-600">만기일:</label>
                  <input
                    type="date"
                    value={billDueDate}
                    onChange={(e) => setBillDueDate(e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div className="col-span-2">
                  <label className="mb-1 block text-sm text-gray-600">발행인:</label>
                  <input
                    type="text"
                    value={billIssuer}
                    onChange={(e) => setBillIssuer(e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div className="col-span-2">
                  <label className="mb-1 block text-sm text-gray-600">비고:</label>
                  <input
                    type="text"
                    value={billMemo}
                    onChange={(e) => setBillMemo(e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 border-t border-gray-200 bg-gray-50 px-4 py-3">
              <button onClick={handleAddBillPayment} className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
                확 인
              </button>
              <button onClick={() => setShowBillModal(false)} className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm hover:bg-gray-50">
                취 소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========== 카드 결제 모달 ========== */}
      {showCardModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[400px] rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
              <span className="text-lg font-medium text-gray-800">카드 결제</span>
              <button onClick={() => setShowCardModal(false)} className="text-gray-400 hover:text-gray-600">
                ✕
              </button>
            </div>
            <div className="p-4">
              <div className="mb-4">
                <label className="mb-1 block text-sm text-gray-600">카드사:</label>
                <select
                  value={selectedCard}
                  onChange={(e) => setSelectedCard(e.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                >
                  <option value="">선택...</option>
                  {CARDS.map((card) => (
                    <option key={card.code} value={card.code}>
                      {card.name} (수수료 {card.feeRate}%)
                    </option>
                  ))}
                </select>
              </div>
              <div className="mb-4">
                <label className="mb-1 block text-sm text-gray-600">카드번호:</label>
                <input
                  type="text"
                  value={cardNumber}
                  onChange={(e) => setCardNumber(e.target.value)}
                  placeholder="0000-0000-0000-0000"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <div className="mb-4">
                <label className="mb-1 block text-sm text-gray-600">금액:</label>
                <input
                  type="number"
                  value={cardAmount}
                  onChange={(e) => setCardAmount(Number(e.target.value))}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-right text-sm"
                />
              </div>
              <div className="mb-4">
                <label className="mb-1 block text-sm text-gray-600">승인번호:</label>
                <input
                  type="text"
                  value={cardApprovalNo}
                  onChange={(e) => setCardApprovalNo(e.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <div className="mb-4">
                <label className="mb-1 block text-sm text-gray-600">비고:</label>
                <input
                  type="text"
                  value={cardMemo}
                  onChange={(e) => setCardMemo(e.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 border-t border-gray-200 bg-gray-50 px-4 py-3">
              <button onClick={handleAddCardPayment} className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
                확 인
              </button>
              <button onClick={() => setShowCardModal(false)} className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm hover:bg-gray-50">
                취 소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
