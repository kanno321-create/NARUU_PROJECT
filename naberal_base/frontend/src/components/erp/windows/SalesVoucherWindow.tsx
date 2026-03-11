"use client";

import React, { useState, useEffect } from "react";
import { DraggableModal } from "../common";
import { api, ERPSaleCreate, ERPSaleItem } from "@/lib/api";
import { useWindowContextOptional } from "../ERPContext";
import { useERPData } from "@/contexts/ERPDataContext";
import TaxInvoiceModal from "./documents/TaxInvoiceModal";
import TransactionStatementModal from "./documents/TransactionStatementModal";

// 상품 품목 인터페이스
interface ProductItem {
  id: string;
  type: string;        // 구분
  productName: string; // 상품명
  spec: string;        // 규격
  unit: string;        // 단위
  quantity: number;    // 수량
  unitPrice: number;   // 단가
  supplyPrice: number; // 공급가액
  memo: string;        // 메모
  vat: number;         // 부가세액
}

// 결제 항목 인터페이스
interface PaymentItem {
  id: string;
  type: string;    // 결제유형
  amount: number;  // 금액
  memo: string;    // 메모
}

// 거래처 인터페이스
interface Customer {
  id: string;      // 추가: 백엔드 ID
  code: string;
  name: string;
  phone: string;
  fax: string;
  representative: string;
  creditLimit: number;
  receivable: number;
  payable: number;
  lastTransaction: string;
  commissionRate: number;
}

// 상품 인터페이스
interface Product {
  code: string;
  name: string;
  spec: string;
  unit: string;
  price: number;
  stock: number;
  lastSale: string;
  lastPrice: number;
  optimalStock: number;
}

// 사원 항목 인터페이스
interface EmployeeItem {
  code: string;
  name: string;
  department: string;
}

export function SalesVoucherWindow() {
  // 윈도우 컨텍스트 (취소 버튼용)
  const windowContext = useWindowContextOptional();
  const { companyInfo } = useERPData();

  // 문서 모달 상태
  const [showTaxInvoice, setShowTaxInvoice] = useState(false);
  const [showTransactionStatement, setShowTransactionStatement] = useState(false);
  const [transactionStatementMode, setTransactionStatementMode] = useState<"standard" | "full">("standard");

  // 기본정보 상태
  const [saleDate, setSaleDate] = useState(new Date().toISOString().split("T")[0]);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [selectedEmployee, setSelectedEmployee] = useState<EmployeeItem | null>(null);
  const [vatType, setVatType] = useState("부가세별도");
  const [vatRate, setVatRate] = useState(10);

  // 상품 목록 상태
  const [items, setItems] = useState<ProductItem[]>([]);
  const [selectedItemIndex, setSelectedItemIndex] = useState<number | null>(null);

  // 결제 탭 상태
  const [paymentTab, setPaymentTab] = useState<"cash" | "bank" | "bill" | "card">("cash");
  const [cashPayments, setCashPayments] = useState<PaymentItem[]>([]);
  const [bankPayments, setBankPayments] = useState<PaymentItem[]>([]);
  const [billPayments, setBillPayments] = useState<PaymentItem[]>([]);
  const [cardPayments, setCardPayments] = useState<PaymentItem[]>([]);

  // 기타비용 상태
  const [expenses, setExpenses] = useState(0);
  const [cardFee, setCardFee] = useState(0);
  const [bankFee, setBankFee] = useState(0);
  const [discount, setDiscount] = useState(0);

  // 선택된 상품 정보
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  // 모달 상태
  const [showCustomerModal, setShowCustomerModal] = useState(false);
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);
  const [showProductModal, setShowProductModal] = useState(false);
  const [showCashModal, setShowCashModal] = useState(false);
  const [showBankModal, setShowBankModal] = useState(false);
  const [showBillModal, setShowBillModal] = useState(false);
  const [showCardModal, setShowCardModal] = useState(false);
  const [showMemoModal, setShowMemoModal] = useState(false);
  const [memo, setMemo] = useState("");

  // 검색 상태
  const [customerSearch, setCustomerSearch] = useState("");
  const [employeeSearch, setEmployeeSearch] = useState("");
  const [productSearch, setProductSearch] = useState("");

  // API 데이터 상태
  const [apiCustomers, setApiCustomers] = useState<Customer[]>([]);
  const [apiProducts, setApiProducts] = useState<Product[]>([]);
  const [apiEmployees, setApiEmployees] = useState<EmployeeItem[]>([]);

  // 거래처 모달 열릴 때 또는 검색어 변경 시 API 호출
  useEffect(() => {
    if (!showCustomerModal) return;
    api.erp.customers.list({ search: customerSearch, limit: 50 })
      .then(res => {
        setApiCustomers(res.items.map(c => ({
          id: c.id,
          code: c.code,
          name: c.name,
          phone: c.phone || '',
          fax: c.fax || '',
          representative: c.ceo_name || '',
          creditLimit: c.credit_limit || 0,
          receivable: c.current_receivable || 0,
          payable: 0,
          lastTransaction: '',
          commissionRate: 0,
        })));
      })
      .catch(() => setApiCustomers([]));
  }, [showCustomerModal, customerSearch]);

  // 상품 모달 열릴 때 또는 검색어 변경 시 API 호출
  useEffect(() => {
    if (!showProductModal) return;
    api.erp.products.list({ search: productSearch, limit: 50 })
      .then(res => {
        setApiProducts(res.items.map(p => ({
          code: p.code,
          name: p.name,
          spec: p.spec || '',
          unit: p.unit,
          price: p.selling_price,
          stock: 0,
          lastSale: '',
          lastPrice: p.selling_price,
          optimalStock: p.safety_stock,
        })));
      })
      .catch(() => setApiProducts([]));
  }, [showProductModal, productSearch]);

  // 사원 모달 열릴 때 또는 검색어 변경 시 API 호출
  useEffect(() => {
    if (!showEmployeeModal) return;
    api.erp.employees.list({ search: employeeSearch, limit: 50 })
      .then(res => {
        setApiEmployees(res.map(e => ({
          code: e.emp_no || e.id || '',
          name: e.name,
          department: e.department || '',
        })));
      })
      .catch(() => setApiEmployees([]));
  }, [showEmployeeModal, employeeSearch]);

  // 결제 모달 폼 상태
  const [cashForm, setCashForm] = useState({ type: "현금입금", amount: 0 });
  const [bankForm, setBankForm] = useState({ type: "은행으로 입금", fromAccount: "", toAccount: "", amount: 0, fee: 0 });
  const [billForm, setBillForm] = useState({ type: "어음수취", billNo: "", amount: 0, dueDate: new Date().toISOString().split("T")[0] });
  const [cardForm, setCardForm] = useState({ type: "카드입금", cardType: "", amount: 0, approvalNo: "", memberName: "", paymentDate: new Date().toISOString().split("T")[0], installment: 1, feeRate: 0 });

  // 계산
  const supplyTotal = items.reduce((sum, item) => sum + item.supplyPrice, 0);
  const vatTotal = items.reduce((sum, item) => sum + item.vat, 0);
  const productAmount = supplyTotal + vatTotal - discount;
  const salesAmount = productAmount + expenses + cardFee;

  const totalCash = cashPayments.reduce((sum, p) => sum + p.amount, 0);
  const totalBank = bankPayments.reduce((sum, p) => sum + p.amount, 0);
  const totalBill = billPayments.reduce((sum, p) => sum + p.amount, 0);
  const totalCard = cardPayments.reduce((sum, p) => sum + p.amount, 0);
  const totalPayment = totalCash + totalBank + totalBill + totalCard;
  const unpaidAmount = salesAmount - totalPayment;

  const formatNumber = (n: number) => n.toLocaleString();

  // 상품 선택
  const handleSelectProduct = (product: Product) => {
    const newItem: ProductItem = {
      id: String(Date.now()),
      type: "과세",
      productName: product.name,
      spec: product.spec,
      unit: product.unit,
      quantity: 1,
      unitPrice: product.price,
      supplyPrice: product.price,
      memo: "",
      vat: Math.round(product.price * 0.1),
    };
    setItems([...items, newItem]);
    setSelectedProduct(product);
    setShowProductModal(false);
  };

  // 상품 삭제
  const handleDeleteItem = () => {
    if (selectedItemIndex === null) {
      alert("삭제할 상품을 선택하세요.");
      return;
    }
    setItems(items.filter((_, idx) => idx !== selectedItemIndex));
    setSelectedItemIndex(null);
  };

  // 할인율 적용
  const handleApplyDiscount = () => {
    const rate = prompt("할인율(%)을 입력하세요:", "0");
    if (rate) {
      const discountRate = parseFloat(rate) / 100;
      setItems(items.map(item => ({
        ...item,
        supplyPrice: Math.round(item.unitPrice * item.quantity * (1 - discountRate)),
        vat: Math.round(item.unitPrice * item.quantity * (1 - discountRate) * 0.1),
      })));
    }
  };

  // 거래처 선택
  const handleSelectCustomer = (customer: Customer) => {
    setSelectedCustomer(customer);
    setShowCustomerModal(false);
  };

  // 사원 선택
  const handleSelectEmployee = (employee: EmployeeItem) => {
    setSelectedEmployee(employee);
    setShowEmployeeModal(false);
  };

  // 결제 저장 핸들러들
  const handleSaveCash = () => {
    if (cashForm.amount <= 0) { alert("금액을 입력하세요."); return; }
    setCashPayments([...cashPayments, { id: String(Date.now()), type: cashForm.type, amount: cashForm.amount, memo: "" }]);
    setCashForm({ type: "현금입금", amount: 0 });
    setShowCashModal(false);
  };

  const handleSaveBank = () => {
    if (bankForm.amount <= 0) { alert("금액을 입력하세요."); return; }
    setBankPayments([...bankPayments, { id: String(Date.now()), type: bankForm.type, amount: bankForm.amount, memo: `${bankForm.fromAccount} → ${bankForm.toAccount}` }]);
    setBankFee(prev => prev + bankForm.fee);
    setBankForm({ type: "은행으로 입금", fromAccount: "", toAccount: "", amount: 0, fee: 0 });
    setShowBankModal(false);
  };

  const handleSaveBill = () => {
    if (billForm.amount <= 0) { alert("금액을 입력하세요."); return; }
    setBillPayments([...billPayments, { id: String(Date.now()), type: billForm.type, amount: billForm.amount, memo: `${billForm.billNo}` }]);
    setBillForm({ type: "어음수취", billNo: "", amount: 0, dueDate: new Date().toISOString().split("T")[0] });
    setShowBillModal(false);
  };

  const handleSaveCard = () => {
    if (cardForm.amount <= 0) { alert("금액을 입력하세요."); return; }
    setCardPayments([...cardPayments, { id: String(Date.now()), type: cardForm.type, amount: cardForm.amount, memo: cardForm.cardType }]);
    setCardFee(prev => prev + Math.round(cardForm.amount * cardForm.feeRate / 100));
    setCardForm({ type: "카드입금", cardType: "", amount: 0, approvalNo: "", memberName: "", paymentDate: new Date().toISOString().split("T")[0], installment: 1, feeRate: 0 });
    setShowCardModal(false);
  };

  // 저장
  const handleSave = async () => {
    if (!selectedCustomer) { alert("거래처를 선택하세요."); return; }
    if (items.length === 0) { alert("상품을 추가하세요."); return; }

    try {
      const saleData: ERPSaleCreate = {
        sale_date: saleDate,
        customer_id: selectedCustomer.id,
        status: "confirmed",
        memo: memo,
        items: items.map(item => ({
          product_name: item.productName,
          spec: item.spec,
          unit: item.unit,
          quantity: item.quantity,
          unit_price: item.unitPrice,
          supply_amount: item.supplyPrice,
          tax_amount: item.vat,
          total_amount: item.supplyPrice + item.vat,
          memo: item.memo,
        }))
      };

      const result = await api.erp.sales.create(saleData);

      // 고객 미수금 즉시 업데이트
      if (selectedCustomer) {
        setSelectedCustomer({
          ...selectedCustomer,
          receivable: selectedCustomer.receivable + (typeof result.total_amount === 'string' ? parseFloat(result.total_amount) : result.total_amount),
        });
      }

      // 신용한도 경고 또는 오류 표시
      if (result.error) {
        alert(
          `저장되었습니다. 전표번호: ${result.sale_number}\n\n` +
          `❌ 오류: ${result.error.message}\n` +
          `신용한도가 초과되었습니다.`
        );
      } else if (result.warning) {
        alert(
          `저장되었습니다. 전표번호: ${result.sale_number}\n\n` +
          `⚠️ 경고: ${result.warning.message}\n` +
          `신용한도 사용률: ${result.warning.usage_percent}%`
        );
      } else {
        alert(`저장되었습니다. 전표번호: ${result.sale_number}`);
      }

      // 입력 폼 초기화
      setItems([]);
      setMemo("");

    } catch (error) {
      alert(`저장 실패: ${error}`);
    }
  };

  // 저장 후 추가
  const handleSaveAndAdd = () => {
    handleSave();
    setItems([]);
    setCashPayments([]); setBankPayments([]); setBillPayments([]); setCardPayments([]);
    setExpenses(0); setCardFee(0); setBankFee(0); setDiscount(0);
  };

  const currentPayments = paymentTab === "cash" ? cashPayments : paymentTab === "bank" ? bankPayments : paymentTab === "bill" ? billPayments : cardPayments;

  return (
    <div className="flex h-full flex-col bg-white">
      {/* 상단 탭 바 */}
      <div className="flex items-center justify-between border-b bg-gray-50 px-4 py-2">
        <h2 className="text-lg font-semibold text-gray-800">매출전표</h2>
        <div className="flex gap-2">
          <button
            onClick={() => {
              if (!selectedCustomer) { alert("거래처를 선택하세요."); return; }
              if (items.length === 0) { alert("상품을 추가하세요."); return; }
              setShowTaxInvoice(true);
            }}
            className="rounded-md bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700"
          >
            전자세금계산서
          </button>
          <button
            onClick={() => {
              if (!selectedCustomer) { alert("거래처를 선택하세요."); return; }
              if (items.length === 0) { alert("상품을 추가하세요."); return; }
              setTransactionStatementMode("standard");
              setShowTransactionStatement(true);
            }}
            className="rounded-md bg-gray-200 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-300"
          >
            거래명세서
          </button>
          <button
            onClick={() => {
              if (!selectedCustomer) { alert("거래처를 선택하세요."); return; }
              if (items.length === 0) { alert("상품을 추가하세요."); return; }
              setTransactionStatementMode("full");
              setShowTransactionStatement(true);
            }}
            className="rounded-md bg-gray-200 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-300"
          >
            거래명세서(전장)
          </button>
          <button
            onClick={() => setShowMemoModal(true)}
            className="rounded-md bg-gray-200 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-300"
          >
            메모사항
          </button>
        </div>
      </div>

      {/* 메인 컨텐츠 */}
      <div className="flex-1 overflow-auto p-4">
        {/* 일반 정보 섹션 */}
        <div className="mb-4 rounded-lg border bg-white p-4 shadow-sm">
          <h3 className="mb-3 text-sm font-semibold text-blue-600">일반 정보</h3>
          <div className="grid grid-cols-4 gap-4">
            <div>
              <label className="mb-1 block text-xs text-gray-500">매출일자</label>
              <input
                type="date"
                value={saleDate}
                onChange={(e) => setSaleDate(e.target.value)}
                className="w-full rounded-md border px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">거래처</label>
              <div className="flex gap-1">
                <input
                  type="text"
                  value={selectedCustomer?.name || ""}
                  readOnly
                  placeholder="거래처 선택"
                  className="flex-1 rounded-md border bg-gray-50 px-3 py-2 text-sm"
                />
                <button
                  onClick={() => setShowCustomerModal(true)}
                  className="rounded-md bg-blue-600 px-3 py-2 text-white hover:bg-blue-700"
                >
                  ...
                </button>
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">담당사원</label>
              <div className="flex gap-1">
                <input
                  type="text"
                  value={selectedEmployee?.name || ""}
                  readOnly
                  placeholder="담당자 선택"
                  className="flex-1 rounded-md border bg-gray-50 px-3 py-2 text-sm"
                />
                <button
                  onClick={() => setShowEmployeeModal(true)}
                  className="rounded-md bg-blue-600 px-3 py-2 text-white hover:bg-blue-700"
                >
                  ...
                </button>
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">부가세율</label>
              <div className="flex gap-2">
                <select
                  value={vatType}
                  onChange={(e) => {
                    const newType = e.target.value;
                    setVatType(newType);
                    if (newType === "영세율" || newType === "면세") {
                      setVatRate(0);
                    } else {
                      setVatRate(10);
                    }
                    // 기존 아이템 재계산
                    setItems(prev => prev.map(item => {
                      const rate = (newType === "영세율" || newType === "면세") ? 0 : 10;
                      if (newType === "부가세포함") {
                        const total = item.unitPrice * item.quantity;
                        const supply = Math.round(total / 1.1);
                        return { ...item, supplyPrice: supply, vat: total - supply };
                      }
                      return { ...item, vat: Math.round(item.supplyPrice * rate / 100) };
                    }));
                  }}
                  className="flex-1 rounded-md border px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                >
                  <option>부가세별도</option>
                  <option>부가세포함</option>
                  <option>영세율</option>
                  <option>면세</option>
                </select>
                <div className="flex items-center gap-1">
                  <input
                    type="number"
                    value={vatRate}
                    onChange={(e) => setVatRate(Number(e.target.value))}
                    className="w-16 rounded-md border px-2 py-2 text-right text-sm"
                  />
                  <span className="text-sm text-gray-500">%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 판매 상품 섹션 */}
        <div className="mb-4 rounded-lg border bg-white p-4 shadow-sm">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-blue-600">
              판매 상품 ({items.length} 품목)
            </h3>
            <div className="flex gap-2">
              <button
                onClick={handleApplyDiscount}
                className="rounded-md bg-yellow-500 px-3 py-1.5 text-sm text-white hover:bg-yellow-600"
              >
                할인율 적용
              </button>
              <button
                onClick={() => setShowProductModal(true)}
                className="rounded-md bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700"
              >
                + 추가
              </button>
              <button
                onClick={handleDeleteItem}
                className="rounded-md bg-red-500 px-3 py-1.5 text-sm text-white hover:bg-red-600"
              >
                삭제
              </button>
            </div>
          </div>
          <div className="max-h-48 overflow-auto rounded-md border">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-gray-100">
                <tr>
                  <th className="px-2 py-2 text-left font-medium text-gray-600">구분</th>
                  <th className="px-2 py-2 text-left font-medium text-gray-600">상품명</th>
                  <th className="px-2 py-2 text-left font-medium text-gray-600">규격</th>
                  <th className="px-2 py-2 text-left font-medium text-gray-600">단위</th>
                  <th className="px-2 py-2 text-right font-medium text-gray-600">수량</th>
                  <th className="px-2 py-2 text-right font-medium text-gray-600">단가</th>
                  <th className="px-2 py-2 text-right font-medium text-gray-600">공급가액</th>
                  <th className="px-2 py-2 text-left font-medium text-gray-600">메모</th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-gray-400">
                      상품을 추가해주세요
                    </td>
                  </tr>
                ) : (
                  items.map((item, idx) => (
                    <tr
                      key={item.id}
                      className={`cursor-pointer border-b hover:bg-blue-50 ${selectedItemIndex === idx ? "bg-blue-100" : ""}`}
                      onClick={() => setSelectedItemIndex(idx)}
                    >
                      <td className="px-2 py-2">{item.type}</td>
                      <td className="px-2 py-2">{item.productName || "-"}</td>
                      <td className="px-2 py-2">{item.spec || "-"}</td>
                      <td className="px-2 py-2">{item.unit}</td>
                      <td className="px-2 py-2 text-right">{item.quantity}</td>
                      <td className="px-2 py-2 text-right">{formatNumber(item.unitPrice)}</td>
                      <td className="px-2 py-2 text-right font-medium">{formatNumber(item.supplyPrice)}</td>
                      <td className="px-2 py-2 text-gray-500">{item.memo || "-"}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* 하단 3단 레이아웃 */}
        <div className="grid grid-cols-3 gap-4">
          {/* 상품대금 */}
          <div className="rounded-lg border bg-white p-4 shadow-sm">
            <h3 className="mb-3 text-sm font-semibold text-blue-600">상품대금</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">공급가액</span>
                <span className="font-medium text-blue-600">{formatNumber(supplyTotal)}원</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">세액</span>
                <span className="text-blue-600">{formatNumber(vatTotal)}원</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-500">할인액(-)</span>
                <input
                  type="number"
                  value={discount}
                  onChange={(e) => setDiscount(Number(e.target.value))}
                  className="w-24 rounded border px-2 py-1 text-right text-sm"
                />
              </div>
              <div className="border-t pt-2">
                <div className="flex justify-between">
                  <span className="font-medium">상품대금</span>
                  <span className="font-bold text-lg">{formatNumber(productAmount)}원</span>
                </div>
              </div>
            </div>
          </div>

          {/* 기타비용 */}
          <div className="rounded-lg border bg-white p-4 shadow-sm">
            <h3 className="mb-3 text-sm font-semibold text-blue-600">기타비용</h3>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-gray-500">제비용(+)</span>
                <input
                  type="number"
                  value={expenses}
                  onChange={(e) => setExpenses(Number(e.target.value))}
                  className="w-24 rounded border px-2 py-1 text-right text-sm"
                />
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">카드수수료(+)</span>
                <span>{formatNumber(cardFee)}원</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">은행수수료</span>
                <span>{formatNumber(bankFee)}원</span>
              </div>
              <div className="border-t pt-2">
                <div className="flex justify-between">
                  <span className="font-medium">매출액</span>
                  <span className="font-bold text-lg text-green-600">{formatNumber(salesAmount)}원</span>
                </div>
              </div>
            </div>
          </div>

          {/* 대금결제 */}
          <div className="rounded-lg border bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-blue-600">대금결제</h3>
              <div className="flex rounded-md border">
                {["cash", "bank", "bill", "card"].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => {
                      setPaymentTab(tab as any);
                      if (tab === "cash") setShowCashModal(true);
                      else if (tab === "bank") setShowBankModal(true);
                      else if (tab === "bill") setShowBillModal(true);
                      else setShowCardModal(true);
                    }}
                    className={`px-2 py-1 text-xs ${paymentTab === tab ? "bg-blue-600 text-white" : "bg-white text-gray-600 hover:bg-gray-100"}`}
                  >
                    {tab === "cash" ? "현금" : tab === "bank" ? "은행" : tab === "bill" ? "어음" : "카드"}
                  </button>
                ))}
              </div>
            </div>
            <div className="mb-2 max-h-20 overflow-auto rounded border bg-gray-50">
              {currentPayments.length === 0 ? (
                <div className="py-4 text-center text-xs text-gray-400">결제내역 없음</div>
              ) : (
                <table className="w-full text-xs">
                  <tbody>
                    {currentPayments.map((p) => (
                      <tr key={p.id} className="border-b">
                        <td className="px-2 py-1">{p.type}</td>
                        <td className="px-2 py-1 text-right font-medium">{formatNumber(p.amount)}원</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">결제금액</span>
                <span className="font-medium text-blue-600">{formatNumber(totalPayment)}원</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">미결제금액</span>
                <span className={`font-bold ${unpaidAmount > 0 ? "text-red-500" : "text-green-600"}`}>
                  {formatNumber(unpaidAmount)}원
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* 선택된 업체/상품 정보 */}
        <div className="mt-4 grid grid-cols-2 gap-4">
          <div className="rounded-lg border bg-gray-50 p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-700">선택된 업체 정보</h3>
            {selectedCustomer ? (
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex justify-between"><span className="text-gray-500">대표자:</span><span className="font-medium">{selectedCustomer.representative}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">팩스:</span><span>{selectedCustomer.fax}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">전화:</span><span>{selectedCustomer.phone}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">최종거래:</span><span>{selectedCustomer.lastTransaction}</span></div>
              </div>
            ) : (
              <p className="text-xs text-gray-400">거래처를 선택해주세요</p>
            )}
          </div>
          <div className="rounded-lg border bg-gray-50 p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-700">선택된 상품 정보</h3>
            {selectedProduct ? (
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex justify-between"><span className="text-gray-500">보유재고:</span><span className="font-medium">{formatNumber(selectedProduct.stock)}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">최종단가:</span><span>{formatNumber(selectedProduct.lastPrice)}원</span></div>
                <div className="flex justify-between"><span className="text-gray-500">최종매출:</span><span>{selectedProduct.lastSale}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">적정재고:</span><span>{formatNumber(selectedProduct.optimalStock)}</span></div>
              </div>
            ) : (
              <p className="text-xs text-gray-400">상품을 선택해주세요</p>
            )}
          </div>
        </div>
      </div>

      {/* 하단 버튼 */}
      <div className="flex items-center justify-end border-t bg-gray-50 px-4 py-3">
        <div className="flex gap-2">
          <button
            onClick={handleSaveAndAdd}
            className="rounded-md border bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
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
            onClick={() => windowContext?.closeThisWindow()}
            className="rounded-md border bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
          >
            취 소
          </button>
        </div>
      </div>

      {/* 거래처 선택 모달 */}
      <DraggableModal
        isOpen={showCustomerModal}
        onClose={() => setShowCustomerModal(false)}
        title="거래처 선택"
        width="500px"
      >
        <div className="p-4">
          <div className="mb-3 flex gap-2">
            <input
              type="text"
              value={customerSearch}
              onChange={(e) => setCustomerSearch(e.target.value)}
              placeholder="검색어 입력"
              className="flex-1 rounded-md border px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
            <button className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">검색</button>
          </div>
          <div className="max-h-64 overflow-auto rounded-md border">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-gray-100">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">코드</th>
                  <th className="px-3 py-2 text-left font-medium">거래처명</th>
                  <th className="px-3 py-2 text-left font-medium">전화번호</th>
                  <th className="px-3 py-2 text-left font-medium">대표자</th>
                </tr>
              </thead>
              <tbody>
                {apiCustomers.map((customer) => (
                  <tr
                    key={customer.code}
                    className="cursor-pointer border-b hover:bg-blue-50"
                    onClick={() => handleSelectCustomer(customer)}
                  >
                    <td className="px-3 py-2 font-mono text-xs">{customer.code}</td>
                    <td className="px-3 py-2">{customer.name}</td>
                    <td className="px-3 py-2">{customer.phone}</td>
                    <td className="px-3 py-2">{customer.representative}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="flex justify-end border-t px-4 py-3">
          <span className="mr-auto text-sm text-gray-500">총 {apiCustomers.length}개</span>
          <button onClick={() => setShowCustomerModal(false)} className="rounded-md bg-gray-200 px-4 py-2 text-sm hover:bg-gray-300">닫기</button>
        </div>
      </DraggableModal>

      {/* 사원 선택 모달 */}
      <DraggableModal
        isOpen={showEmployeeModal}
        onClose={() => setShowEmployeeModal(false)}
        title="담당사원 선택"
        width="400px"
      >
        <div className="p-4">
          <div className="mb-3 flex gap-2">
            <input
              type="text"
              value={employeeSearch}
              onChange={(e) => setEmployeeSearch(e.target.value)}
              placeholder="검색어 입력"
              className="flex-1 rounded-md border px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
            <button className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">검색</button>
          </div>
          <div className="max-h-48 overflow-auto rounded-md border">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-gray-100">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">코드</th>
                  <th className="px-3 py-2 text-left font-medium">성명</th>
                  <th className="px-3 py-2 text-left font-medium">부서</th>
                </tr>
              </thead>
              <tbody>
                {apiEmployees.filter(e => e.name.includes(employeeSearch)).map((emp) => (
                  <tr
                    key={emp.code}
                    className="cursor-pointer border-b hover:bg-blue-50"
                    onClick={() => handleSelectEmployee(emp)}
                  >
                    <td className="px-3 py-2 font-mono text-xs">{emp.code}</td>
                    <td className="px-3 py-2">{emp.name}</td>
                    <td className="px-3 py-2">{emp.department}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="flex justify-end border-t px-4 py-3">
          <button onClick={() => setShowEmployeeModal(false)} className="rounded-md bg-gray-200 px-4 py-2 text-sm hover:bg-gray-300">닫기</button>
        </div>
      </DraggableModal>

      {/* 현금 결제 모달 */}
      <DraggableModal
        isOpen={showCashModal}
        onClose={() => setShowCashModal(false)}
        title="현금 결제"
        width="320px"
      >
        <div className="p-4">
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-xs text-gray-500">구분</label>
              <select value={cashForm.type} onChange={(e) => setCashForm({ ...cashForm, type: e.target.value })} className="w-full rounded-md border px-3 py-2 text-sm">
                <option>현금입금</option>
                <option>현금출금</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">금액</label>
              <div className="flex gap-1">
                <input type="number" value={cashForm.amount} onChange={(e) => setCashForm({ ...cashForm, amount: Number(e.target.value) })} className="flex-1 rounded-md border px-3 py-2 text-right text-sm" />
                <button
                  onClick={() => setCashForm({ ...cashForm, amount: unpaidAmount > 0 ? unpaidAmount : 0 })}
                  className="rounded-md bg-blue-500 px-3 py-2 text-sm text-white hover:bg-blue-600 whitespace-nowrap"
                >
                  전액
                </button>
              </div>
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-2 border-t px-4 py-3">
          <button onClick={() => setShowCashModal(false)} className="rounded-md bg-gray-200 px-4 py-2 text-sm hover:bg-gray-300">취소</button>
          <button onClick={handleSaveCash} className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">저장</button>
        </div>
      </DraggableModal>

      {/* 계좌 결제 모달 */}
      <DraggableModal
        isOpen={showBankModal}
        onClose={() => setShowBankModal(false)}
        title="계좌 결제"
        width="380px"
      >
        <div className="p-4">
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-xs text-gray-500">구분</label>
              <select value={bankForm.type} onChange={(e) => setBankForm({ ...bankForm, type: e.target.value })} className="w-full rounded-md border px-3 py-2 text-sm">
                <option>은행으로 입금</option>
                <option>은행으로 지급</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="mb-1 block text-xs text-gray-500">출금계좌</label>
                <input type="text" value={bankForm.fromAccount} onChange={(e) => setBankForm({ ...bankForm, fromAccount: e.target.value })} className="w-full rounded-md border px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-500">입금계좌</label>
                <input type="text" value={bankForm.toAccount} onChange={(e) => setBankForm({ ...bankForm, toAccount: e.target.value })} className="w-full rounded-md border px-3 py-2 text-sm" />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">금액</label>
              <div className="flex gap-1">
                <input type="number" value={bankForm.amount} onChange={(e) => setBankForm({ ...bankForm, amount: Number(e.target.value) })} className="flex-1 rounded-md border px-3 py-2 text-right text-sm" />
                <button
                  onClick={() => setBankForm({ ...bankForm, amount: unpaidAmount > 0 ? unpaidAmount : 0 })}
                  className="rounded-md bg-blue-500 px-3 py-2 text-sm text-white hover:bg-blue-600 whitespace-nowrap"
                >
                  전액
                </button>
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">수수료</label>
              <input type="number" value={bankForm.fee} onChange={(e) => setBankForm({ ...bankForm, fee: Number(e.target.value) })} className="w-full rounded-md border px-3 py-2 text-right text-sm" />
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-2 border-t px-4 py-3">
          <button onClick={() => setShowBankModal(false)} className="rounded-md bg-gray-200 px-4 py-2 text-sm hover:bg-gray-300">취소</button>
          <button onClick={handleSaveBank} className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">저장</button>
        </div>
      </DraggableModal>

      {/* 어음 결제 모달 */}
      <DraggableModal
        isOpen={showBillModal}
        onClose={() => setShowBillModal(false)}
        title="어음 결제"
        width="320px"
      >
        <div className="p-4">
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-xs text-gray-500">구분</label>
              <select value={billForm.type} onChange={(e) => setBillForm({ ...billForm, type: e.target.value })} className="w-full rounded-md border px-3 py-2 text-sm">
                <option>어음수취</option>
                <option>어음발행</option>
                <option>어음양도</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">어음번호</label>
              <input type="text" value={billForm.billNo} onChange={(e) => setBillForm({ ...billForm, billNo: e.target.value })} className="w-full rounded-md border px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">금액</label>
              <div className="flex gap-1">
                <input type="number" value={billForm.amount} onChange={(e) => setBillForm({ ...billForm, amount: Number(e.target.value) })} className="flex-1 rounded-md border px-3 py-2 text-right text-sm" />
                <button
                  onClick={() => setBillForm({ ...billForm, amount: unpaidAmount > 0 ? unpaidAmount : 0 })}
                  className="rounded-md bg-blue-500 px-3 py-2 text-sm text-white hover:bg-blue-600 whitespace-nowrap"
                >
                  전액
                </button>
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">만기일</label>
              <input type="date" value={billForm.dueDate} onChange={(e) => setBillForm({ ...billForm, dueDate: e.target.value })} className="w-full rounded-md border px-3 py-2 text-sm" />
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-2 border-t px-4 py-3">
          <button onClick={() => setShowBillModal(false)} className="rounded-md bg-gray-200 px-4 py-2 text-sm hover:bg-gray-300">취소</button>
          <button onClick={handleSaveBill} className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">저장</button>
        </div>
      </DraggableModal>

      {/* 카드 결제 모달 */}
      <DraggableModal
        isOpen={showCardModal}
        onClose={() => setShowCardModal(false)}
        title="카드 결제"
        width="360px"
      >
        <div className="p-4">
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-xs text-gray-500">구분</label>
              <select value={cardForm.type} onChange={(e) => setCardForm({ ...cardForm, type: e.target.value })} className="w-full rounded-md border px-3 py-2 text-sm">
                <option>카드입금</option>
                <option>카드출금</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">카드종류</label>
              <input type="text" value={cardForm.cardType} onChange={(e) => setCardForm({ ...cardForm, cardType: e.target.value })} className="w-full rounded-md border px-3 py-2 text-sm" placeholder="신한카드, 국민카드..." />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">금액</label>
              <div className="flex gap-1">
                <input type="number" value={cardForm.amount} onChange={(e) => setCardForm({ ...cardForm, amount: Number(e.target.value) })} className="flex-1 rounded-md border px-3 py-2 text-right text-sm" />
                <button
                  onClick={() => setCardForm({ ...cardForm, amount: unpaidAmount > 0 ? unpaidAmount : 0 })}
                  className="rounded-md bg-blue-500 px-3 py-2 text-sm text-white hover:bg-blue-600 whitespace-nowrap"
                >
                  전액
                </button>
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">승인번호</label>
              <input type="text" value={cardForm.approvalNo} onChange={(e) => setCardForm({ ...cardForm, approvalNo: e.target.value })} className="w-full rounded-md border px-3 py-2 text-sm" />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="mb-1 block text-xs text-gray-500">결제일자</label>
                <input type="date" value={cardForm.paymentDate} onChange={(e) => setCardForm({ ...cardForm, paymentDate: e.target.value })} className="w-full rounded-md border px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-500">할부개월</label>
                <div className="flex items-center gap-1">
                  <input type="number" value={cardForm.installment} onChange={(e) => setCardForm({ ...cardForm, installment: Number(e.target.value) })} className="w-full rounded-md border px-3 py-2 text-right text-sm" />
                  <span className="text-xs text-gray-500">개월</span>
                </div>
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">수수료율</label>
              <div className="flex items-center gap-1">
                <input type="number" step="0.1" value={cardForm.feeRate} onChange={(e) => setCardForm({ ...cardForm, feeRate: Number(e.target.value) })} className="w-24 rounded-md border px-3 py-2 text-right text-sm" />
                <span className="text-xs text-gray-500">%</span>
              </div>
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-2 border-t px-4 py-3">
          <button onClick={() => setShowCardModal(false)} className="rounded-md bg-gray-200 px-4 py-2 text-sm hover:bg-gray-300">취소</button>
          <button onClick={handleSaveCard} className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">저장</button>
        </div>
      </DraggableModal>

      {/* 메모 모달 */}
      <DraggableModal
        isOpen={showMemoModal}
        onClose={() => setShowMemoModal(false)}
        title="메모사항"
        width="400px"
      >
        <div className="p-4">
          <textarea
            value={memo}
            onChange={(e) => setMemo(e.target.value)}
            className="h-40 w-full rounded-md border p-3 text-sm focus:border-blue-500 focus:outline-none"
            placeholder="메모를 입력하세요..."
          />
        </div>
        <div className="flex justify-end gap-2 border-t px-4 py-3">
          <button onClick={() => setShowMemoModal(false)} className="rounded-md bg-gray-200 px-4 py-2 text-sm hover:bg-gray-300">취소</button>
          <button onClick={() => setShowMemoModal(false)} className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">저장</button>
        </div>
      </DraggableModal>

      {/* 상품 선택 모달 (10% 크기 증가: 500px → 550px) */}
      <DraggableModal
        isOpen={showProductModal}
        onClose={() => setShowProductModal(false)}
        title="상품 선택"
        width="550px"
      >
        <div className="p-4">
          <div className="mb-3 flex gap-2">
            <input
              type="text"
              value={productSearch}
              onChange={(e) => setProductSearch(e.target.value)}
              placeholder="상품명 또는 코드로 검색"
              className="flex-1 rounded-md border px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
            <button className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">검색</button>
          </div>
          <div className="max-h-80 overflow-auto rounded-md border">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-gray-100">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">코드</th>
                  <th className="px-3 py-2 text-left font-medium">상품명</th>
                  <th className="px-3 py-2 text-left font-medium">규격</th>
                  <th className="px-3 py-2 text-left font-medium">단위</th>
                  <th className="px-3 py-2 text-right font-medium">단가</th>
                  <th className="px-3 py-2 text-right font-medium">재고</th>
                </tr>
              </thead>
              <tbody>
                {apiProducts.map((product) => (
                  <tr
                    key={product.code}
                    className="cursor-pointer border-b hover:bg-blue-50"
                    onClick={() => handleSelectProduct(product)}
                  >
                    <td className="px-3 py-2 font-mono text-xs">{product.code}</td>
                    <td className="px-3 py-2 font-medium">{product.name}</td>
                    <td className="px-3 py-2 text-gray-600">{product.spec}</td>
                    <td className="px-3 py-2">{product.unit}</td>
                    <td className="px-3 py-2 text-right">{formatNumber(product.price)}원</td>
                    <td className="px-3 py-2 text-right">
                      <span className={product.stock < product.optimalStock ? "text-red-500" : "text-green-600"}>
                        {formatNumber(product.stock)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="flex justify-end border-t px-4 py-3">
          <span className="mr-auto text-sm text-gray-500">총 {apiProducts.length}개</span>
          <button onClick={() => setShowProductModal(false)} className="rounded-md bg-gray-200 px-4 py-2 text-sm hover:bg-gray-300">닫기</button>
        </div>
      </DraggableModal>

      {/* 전자세금계산서 모달 */}
      <TaxInvoiceModal
        isOpen={showTaxInvoice}
        onClose={() => setShowTaxInvoice(false)}
        transactionDate={saleDate}
        documentNumber={`S-${Date.now().toString().slice(-8)}`}
        supplierBusinessNumber={companyInfo.businessNumber || ""}
        supplierCompanyName={companyInfo.companyName || ""}
        supplierCeoName={companyInfo.ceoName || ""}
        supplierAddress={`${companyInfo.address || ""} ${companyInfo.addressDetail || ""}`.trim()}
        supplierBusinessType={companyInfo.businessType || ""}
        supplierBusinessItem={companyInfo.businessCategory || ""}
        customerBusinessNumber={""}
        customerCompanyName={selectedCustomer?.name || ""}
        customerCeoName={selectedCustomer?.representative || ""}
        customerAddress={""}
        customerBusinessType={""}
        customerBusinessItem={""}
        items={items.map((item) => ({
          id: item.id,
          productName: item.productName,
          spec: item.spec,
          unit: item.unit,
          quantity: item.quantity,
          unitPrice: item.unitPrice,
          supplyAmount: item.supplyPrice,
          vatAmount: item.vat,
          memo: item.memo,
        }))}
        totalSupplyAmount={supplyTotal}
        totalVatAmount={vatTotal}
        totalAmount={supplyTotal + vatTotal}
      />

      {/* 거래명세서 모달 */}
      <TransactionStatementModal
        isOpen={showTransactionStatement}
        onClose={() => setShowTransactionStatement(false)}
        mode={transactionStatementMode}
        transactionDate={saleDate}
        documentNumber={`T-${Date.now().toString().slice(-8)}`}
        supplierBusinessNumber={companyInfo.businessNumber || ""}
        supplierCompanyName={companyInfo.companyName || ""}
        supplierCeoName={companyInfo.ceoName || ""}
        supplierAddress={`${companyInfo.address || ""} ${companyInfo.addressDetail || ""}`.trim()}
        supplierPhone={companyInfo.tel || ""}
        supplierFax={companyInfo.fax || ""}
        customerBusinessNumber={""}
        customerCompanyName={selectedCustomer?.name || ""}
        customerCeoName={selectedCustomer?.representative || ""}
        customerAddress={""}
        customerPhone={selectedCustomer?.phone || ""}
        customerFax={selectedCustomer?.fax || ""}
        items={items.map((item) => ({
          id: item.id,
          productName: item.productName,
          spec: item.spec,
          unit: item.unit,
          quantity: item.quantity,
          unitPrice: item.unitPrice,
          supplyAmount: item.supplyPrice,
          vatAmount: item.vat,
          memo: item.memo,
        }))}
        totalSupplyAmount={supplyTotal}
        totalVatAmount={vatTotal}
        totalAmount={supplyTotal + vatTotal}
      />
    </div>
  );
}
