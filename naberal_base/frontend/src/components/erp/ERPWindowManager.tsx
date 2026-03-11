"use client";

import React, { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import { API_BASE_URL } from "@/config/api";
import { cn } from "@/lib/utils";
import { X, Minus, Maximize2, Minimize2 } from "lucide-react";
import type { WindowConfig } from "@/app/erp/page";
import { WindowProvider, useWindowContextOptional } from "./ERPContext";

// 각 기능별 윈도우 컨텐츠
import { CustomerInfoWindow } from "./windows/CustomerInfoWindow";
import { ProductInfoWindow } from "./windows/ProductInfoWindow";
import { SettingsWindow } from "./windows/SettingsWindow";
import { ReportWindow } from "./windows/ReportWindow";
import { CollectionVoucherWindow } from "./windows/CollectionVoucherWindow";
import { PaymentDisbursementWindow } from "./windows/PaymentDisbursementWindow";
import { CompanyInfoWindow } from "./windows/CompanyInfoWindow";
import { SmsWindow } from "./windows/SmsWindow";
import { FaxWindow } from "./windows/FaxWindow";
import { TransactionStatementWindow } from "./windows/TransactionStatementWindow";
import { PurchaseOrderWindow } from "./windows/PurchaseOrderWindow";
import { PayrollWindow } from "./windows/PayrollWindow";
import { QuotationWindow } from "./windows/QuotationWindow";

// 개별 설정 윈도우 (9개)
import { BasicSettingsWindow } from "./windows/settings/BasicSettingsWindow";
import { FormSettingsWindow } from "./windows/settings/FormSettingsWindow";
import { SMSSettingsWindow } from "./windows/settings/SMSSettingsWindow";
import { PrintSettingsWindow } from "./windows/settings/PrintSettingsWindow";
import { BackupSettingsWindow } from "./windows/settings/BackupSettingsWindow";
import { BusinessSettingsWindow } from "./windows/settings/BusinessSettingsWindow";
import { EmailSettingsWindow } from "./windows/settings/EmailSettingsWindow";
import { FaxSettingsWindow } from "./windows/settings/FaxSettingsWindow";
import { TaxInvoiceSettingsWindow } from "./windows/settings/TaxInvoiceSettingsWindow";

// 기초자료등록 윈도우 (15개)
import {
    CompanyInfoWindow as BasicDataCompanyInfoWindow,
    CustomerWindow,
    ProductWindow,
    BankAccountWindow as BasicDataBankAccountWindow,
    DepartmentWindow,
    EmployeeWindow as BasicDataEmployeeWindow,
    IncomeExpenseItemWindow as BasicDataIncomeExpenseItemWindow,
    CreditCardWindow as BasicDataCreditCardWindow,
    CategoryWindow,
    ThemeWindow,
    MarginGroupWindow,
    ProductCategoryMarginWindow,
    ThemeCategoryMarginWindow,
    AllowanceItemWindow,
    DeductionItemWindow,
} from "./windows/basic-data";

// 전표작성 윈도우 (10개)
import {
    SalesSlipWindow,
    SalesVoucherWindow,
    PurchaseSlipWindow,
    PurchaseVoucherWindow,
    CollectionSlipWindow,
    PaymentSlipWindow,
    IncomeExpenseSlipWindow,
    SalesReturnSlipWindow,
    PurchaseReturnSlipWindow,
    DepositSlipWindow,
    WithdrawalSlipWindow,
} from "./windows/voucher";

// 보고서/명세서 윈도우 (15개)
import {
    SalesStatementWindow,
    CustomerSalesWindow,
    ProductSalesWindow,
    DailyReportWindow,
    PeriodAnalysisWindow,
    ProfitLossWindow,
    MonthlyChartWindow,
    CustomerMarginWindow,
    ReceivableListWindow,
    PayableListWindow,
    BadDebtWindow,
    CreditInfoWindow,
    InventoryStatusWindow,
    PurchaseStatementWindow,
    SupplierPurchaseWindow,
} from "./windows/reports";

// 기초이월 윈도우 (6개)
import {
    ProductInventoryCarryoverWindow,
    ReceivablePayableCarryoverWindow,
    BankBalanceCarryoverWindow,
    BillCarryoverWindow,
    DebtCreditCarryoverWindow,
    CashBalanceCarryoverWindow,
} from "./windows/initial-carryover";

// 재고관리 메뉴 (10개)
import {
    InventoryStatus,
    InboundStatus,
    OutboundStatus,
    InOutStatus,
    InventoryAdjustment,
    InboundStatement,
    OutboundStatement,
    InOutStatement,
    ItemInOutStatement,
    ProductCostRecalculation,
} from "./menus/inventory";

// 종합현황 메뉴 (5개)
import {
    CustomerLedger,
    SalesPurchaseSummary,
    ItemTransactionStatus,
    ProfitLossStatement,
    ManagementDashboard,
} from "./menus/summary";

// 발행관리 메뉴
import { UnissuedSalesList } from "./menus/issuance/UnissuedSalesList";

interface ERPWindowManagerProps {
    windows: WindowConfig[];
    onClose: (id: string) => void;
    onMinimize: (id: string) => void;
    onFocus: (id: string) => void;
    onUpdate: (id: string, updates: Partial<WindowConfig>) => void;
}

interface ERPWindowProps {
    config: WindowConfig;
    onClose: () => void;
    onMinimize: () => void;
    onFocus: () => void;
    onUpdate: (updates: Partial<WindowConfig>) => void;
}

// 윈도우 컨텐츠 렌더링
function getWindowContent(type: string) {
    switch (type) {
        // 기초자료등록 (15개)
        case "customer-info":
        case "customer":
            return <CustomerWindow />;
        case "product-info":
        case "product":
            return <ProductWindow />;
        case "company-info":
            return <BasicDataCompanyInfoWindow />;
        case "employee":
            return <BasicDataEmployeeWindow />;
        case "credit-card":
            return <BasicDataCreditCardWindow />;
        case "income-expense-item":
            return <BasicDataIncomeExpenseItemWindow />;
        case "bank-account":
            return <BasicDataBankAccountWindow />;
        case "department":
            return <DepartmentWindow />;
        case "category":
            return <CategoryWindow />;
        case "theme":
            return <ThemeWindow />;
        case "margin-group":
            return <MarginGroupWindow />;
        case "product-category-margin":
            return <ProductCategoryMarginWindow />;
        case "theme-category-margin":
            return <ThemeCategoryMarginWindow />;
        case "allowance-item":
            return <AllowanceItemWindow />;
        case "deduction-item":
            return <DeductionItemWindow />;

        // 전표작성 (9개)
        case "sales-voucher":
        case "sales-slip":  // sales-slip도 신버전 SalesVoucherWindow 사용
            return <SalesVoucherWindow />;
        case "purchase-voucher":
            return <PurchaseVoucherWindow />;
        case "purchase-slip":
            return <PurchaseSlipWindow />;
        case "collection-voucher":
        case "collection-slip":
            return <CollectionSlipWindow />;
        case "payment-voucher":
        case "payment-slip":
            return <PaymentSlipWindow />;
        case "income-expense-voucher":
        case "income-expense-slip":
            return <IncomeExpenseSlipWindow />;
        case "sales-return-slip":
            return <SalesReturnSlipWindow />;
        case "purchase-return-slip":
            return <PurchaseReturnSlipWindow />;
        case "deposit-slip":
            return <DepositSlipWindow />;
        case "withdrawal-slip":
            return <WithdrawalSlipWindow />;

        // 보고서/명세서 (15개)
        case "sales-statement":
            return <SalesStatementWindow />;
        case "customer-sales":
            return <CustomerSalesWindow />;
        case "product-sales":
            return <ProductSalesWindow />;
        case "daily-report":
        case "daily-report-detail":
            return <DailyReportWindow />;
        case "period-analysis":
            return <PeriodAnalysisWindow />;
        case "profit-loss":
            return <ProfitLossWindow />;
        case "monthly-chart":
            return <MonthlyChartWindow />;
        case "customer-margin":
            return <CustomerMarginWindow />;
        case "receivable-list":
            return <ReceivableListWindow />;
        case "payable-list":
            return <PayableListWindow />;
        case "bad-debt":
            return <BadDebtWindow />;
        case "credit-info":
            return <CreditInfoWindow />;
        case "inventory-status":
            return <InventoryStatusWindow />;
        case "purchase-statement":
            return <PurchaseStatementWindow />;
        case "supplier-purchase":
            return <SupplierPurchaseWindow />;

        // 환경설정 - 개별 윈도우로 연결
        case "basic-settings":
            return <BasicSettingsWindow />;
        case "form-settings":
            return <FormSettingsWindow />;
        case "sms-settings":
            return <SMSSettingsWindow />;
        case "print-settings":
            return <PrintSettingsWindow />;
        case "backup-settings":
            return <BackupSettingsWindow />;
        case "business-settings":
            return <BusinessSettingsWindow />;
        case "email-settings":
            return <EmailSettingsWindow />;
        case "fax-settings":
            return <FaxSettingsWindow />;
        case "tax-invoice-settings":
            return <TaxInvoiceSettingsWindow />;

        // 기초이월 (6개)
        case "inventory-carryover":
            return <ProductInventoryCarryoverWindow onClose={() => {}} />;
        case "receivable-payable-carryover":
            return <ReceivablePayableCarryoverWindow onClose={() => {}} />;
        case "bank-balance-carryover":
            return <BankBalanceCarryoverWindow onClose={() => {}} />;
        case "note-carryover":
            return <BillCarryoverWindow onClose={() => {}} />;
        case "bond-debt-carryover":
            return <DebtCreditCarryoverWindow onClose={() => {}} />;
        case "cash-balance-carryover":
            return <CashBalanceCarryoverWindow onClose={() => {}} />;

        // 재고관리 메뉴 (10개)
        case "stock-in-statement":
            return <InboundStatement />;
        case "stock-in-status":
            return <InboundStatus />;
        case "stock-out-statement":
            return <OutboundStatement />;
        case "stock-out-status":
            return <OutboundStatus />;
        case "stock-io-statement":
            return <InOutStatement />;
        case "product-stock-io-statement":
            return <ItemInOutStatement />;
        case "stock-io-status":
            return <InOutStatus />;
        case "stock-status":
            return <InventoryStatus />;
        case "inventory-adjust":
            return <InventoryAdjustment />;
        case "cost-recalc":
            return <ProductCostRecalculation />;

        // 종합현황 메뉴 (5개)
        case "customer-ledger":
            return <CustomerLedger />;
        case "sales-purchase-summary":
            return <SalesPurchaseSummary />;
        case "item-transaction-status":
            return <ItemTransactionStatus />;
        case "profit-loss-statement":
            return <ProfitLossStatement />;
        case "management-dashboard":
            return <ManagementDashboard />;

        // 기타
        case "search":
            return <SearchWindow />;

        // 전자전송 - 각각 전용 윈도우 사용
        case "sms-send":
            return <SmsWindow />;
        case "fax-send":
            return <FaxWindow />;
        case "email-send":
            return <EmailWindow />;
        case "sales-tax-invoice":
        case "tax-invoice":
        case "e-tax-invoice":
            return <TaxInvoiceWindow />;
        case "unissued-sales-list":
            return <UnissuedSalesList />;

        // 상단 툴바 추가 라우팅
        case "income-expense":
            return <IncomeExpenseSlipWindow />;
        case "receivable-alert":
            return <ReceivableListWindow />;
        case "settings":
            return <SettingsWindow />;
        case "transaction-statement":
        case "statement-management":
            return <TransactionStatementWindow />;
        case "purchase-order":
        case "order-management":
            return <PurchaseOrderWindow />;
        case "logistics":
            return <LogisticsWindow />;
        case "salary":
            return <PayrollWindow />;
        case "quotation":
        case "estimate-management":
            return <QuotationWindow />;

        default:
            return <GenericWindow type={type} />;
    }
}

// 범용 윈도우 컴포넌트
function GenericWindow({ type }: { type: string }) {
    return (
        <div className="flex h-full flex-col items-center justify-center p-8">
            <div className="text-center">
                <p className="text-lg font-medium text-text-subtle">{type}</p>
                <p className="mt-2 text-sm text-text-subtle">이 기능을 사용할 준비가 되었습니다.</p>
            </div>
        </div>
    );
}

// 사원등록 윈도우
function EmployeeWindow() {
    const [employees, setEmployees] = useState([
        { id: "1", name: "홍길동", department: "영업부", position: "대리", phone: "010-1234-5678" },
        { id: "2", name: "김철수", department: "관리부", position: "과장", phone: "010-2345-6789" },
    ]);
    const [newEmployee, setNewEmployee] = useState({ name: "", department: "", position: "", phone: "" });

    const handleAdd = () => {
        if (newEmployee.name) {
            setEmployees([...employees, { ...newEmployee, id: String(Date.now()) }]);
            setNewEmployee({ name: "", department: "", position: "", phone: "" });
        }
    };

    return (
        <div className="p-4">
            <h3 className="text-lg font-medium mb-4">사원등록</h3>
            <div className="mb-4 grid grid-cols-5 gap-2">
                <input
                    type="text"
                    placeholder="이름"
                    value={newEmployee.name}
                    onChange={(e) => setNewEmployee({ ...newEmployee, name: e.target.value })}
                    className="rounded border px-2 py-1 text-sm"
                />
                <input
                    type="text"
                    placeholder="부서"
                    value={newEmployee.department}
                    onChange={(e) => setNewEmployee({ ...newEmployee, department: e.target.value })}
                    className="rounded border px-2 py-1 text-sm"
                />
                <input
                    type="text"
                    placeholder="직급"
                    value={newEmployee.position}
                    onChange={(e) => setNewEmployee({ ...newEmployee, position: e.target.value })}
                    className="rounded border px-2 py-1 text-sm"
                />
                <input
                    type="text"
                    placeholder="연락처"
                    value={newEmployee.phone}
                    onChange={(e) => setNewEmployee({ ...newEmployee, phone: e.target.value })}
                    className="rounded border px-2 py-1 text-sm"
                />
                <button onClick={handleAdd} className="rounded bg-brand px-3 py-1 text-sm text-white">
                    추가
                </button>
            </div>
            <table className="w-full border-collapse text-sm">
                <thead>
                    <tr className="border-b bg-surface">
                        <th className="px-3 py-2 text-left">이름</th>
                        <th className="px-3 py-2 text-left">부서</th>
                        <th className="px-3 py-2 text-left">직급</th>
                        <th className="px-3 py-2 text-left">연락처</th>
                    </tr>
                </thead>
                <tbody>
                    {employees.map((emp) => (
                        <tr key={emp.id} className="border-b hover:bg-surface-secondary">
                            <td className="px-3 py-2">{emp.name}</td>
                            <td className="px-3 py-2">{emp.department}</td>
                            <td className="px-3 py-2">{emp.position}</td>
                            <td className="px-3 py-2">{emp.phone}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

// 신용카드 등록 윈도우
function CreditCardWindow() {
    const [cards, setCards] = useState([
        { id: "1", cardName: "법인카드", cardNumber: "1234-****-****-5678", bank: "국민카드" },
    ]);

    return (
        <div className="p-4">
            <h3 className="text-lg font-medium mb-4">신용카드등록</h3>
            <table className="w-full border-collapse text-sm">
                <thead>
                    <tr className="border-b bg-surface">
                        <th className="px-3 py-2 text-left">카드명</th>
                        <th className="px-3 py-2 text-left">카드번호</th>
                        <th className="px-3 py-2 text-left">카드사</th>
                    </tr>
                </thead>
                <tbody>
                    {cards.map((card) => (
                        <tr key={card.id} className="border-b hover:bg-surface-secondary">
                            <td className="px-3 py-2">{card.cardName}</td>
                            <td className="px-3 py-2">{card.cardNumber}</td>
                            <td className="px-3 py-2">{card.bank}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
            <button className="mt-4 rounded bg-brand px-4 py-2 text-sm text-white">카드 추가</button>
        </div>
    );
}

// 입출금항목 등록 윈도우
function IncomeExpenseItemWindow() {
    const [items, setItems] = useState([
        { id: "1", name: "급여", type: "지출", category: "인건비" },
        { id: "2", name: "매출입금", type: "수입", category: "영업" },
        { id: "3", name: "사무용품", type: "지출", category: "운영비" },
    ]);

    return (
        <div className="p-4">
            <h3 className="text-lg font-medium mb-4">입출금항목등록</h3>
            <table className="w-full border-collapse text-sm">
                <thead>
                    <tr className="border-b bg-surface">
                        <th className="px-3 py-2 text-left">항목명</th>
                        <th className="px-3 py-2 text-left">구분</th>
                        <th className="px-3 py-2 text-left">분류</th>
                    </tr>
                </thead>
                <tbody>
                    {items.map((item) => (
                        <tr key={item.id} className="border-b hover:bg-surface-secondary">
                            <td className="px-3 py-2">{item.name}</td>
                            <td className="px-3 py-2">
                                <span className={`rounded px-2 py-0.5 text-xs ${item.type === "수입" ? "bg-blue-100 text-blue-800" : "bg-red-100 text-red-800"}`}>
                                    {item.type}
                                </span>
                            </td>
                            <td className="px-3 py-2">{item.category}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
            <button className="mt-4 rounded bg-brand px-4 py-2 text-sm text-white">항목 추가</button>
        </div>
    );
}

// 자사은행계좌 등록 윈도우
function BankAccountWindow() {
    const [accounts, setAccounts] = useState([
        { id: "1", bankName: "국민은행", accountNumber: "123-456-789012", accountHolder: "㈜한국산업", purpose: "영업용" },
    ]);

    return (
        <div className="p-4">
            <h3 className="text-lg font-medium mb-4">자사은행계좌등록</h3>
            <table className="w-full border-collapse text-sm">
                <thead>
                    <tr className="border-b bg-surface">
                        <th className="px-3 py-2 text-left">은행명</th>
                        <th className="px-3 py-2 text-left">계좌번호</th>
                        <th className="px-3 py-2 text-left">예금주</th>
                        <th className="px-3 py-2 text-left">용도</th>
                    </tr>
                </thead>
                <tbody>
                    {accounts.map((acc) => (
                        <tr key={acc.id} className="border-b hover:bg-surface-secondary">
                            <td className="px-3 py-2">{acc.bankName}</td>
                            <td className="px-3 py-2">{acc.accountNumber}</td>
                            <td className="px-3 py-2">{acc.accountHolder}</td>
                            <td className="px-3 py-2">{acc.purpose}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
            <button className="mt-4 rounded bg-brand px-4 py-2 text-sm text-white">계좌 추가</button>
        </div>
    );
}

// 입출금전표 윈도우
function IncomeExpenseVoucherWindow() {
    return (
        <div className="p-4">
            <h3 className="text-lg font-medium mb-4">입출금전표</h3>
            <div className="space-y-4">
                <div className="flex gap-4">
                    <input type="date" className="rounded border px-3 py-2 text-sm" defaultValue={new Date().toISOString().split("T")[0]} />
                    <select className="rounded border px-3 py-2 text-sm">
                        <option value="income">입금</option>
                        <option value="expense">출금</option>
                    </select>
                </div>
                <div className="grid grid-cols-3 gap-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">항목</label>
                        <select className="w-full rounded border px-3 py-2 text-sm">
                            <option>급여</option>
                            <option>사무용품</option>
                            <option>매출입금</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">금액</label>
                        <input type="number" className="w-full rounded border px-3 py-2 text-sm" placeholder="0" />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">비고</label>
                        <input type="text" className="w-full rounded border px-3 py-2 text-sm" placeholder="메모" />
                    </div>
                </div>
                <button className="rounded bg-brand px-4 py-2 text-sm text-white">저장</button>
            </div>
        </div>
    );
}

// 전체검색 윈도우
function SearchWindow() {
    const [query, setQuery] = useState("");

    return (
        <div className="p-4">
            <h3 className="text-lg font-medium mb-4">전체검색</h3>
            <div className="flex gap-2 mb-4">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="검색어를 입력하세요..."
                    className="flex-1 rounded border px-3 py-2 text-sm"
                />
                <button className="rounded bg-brand px-4 py-2 text-sm text-white">검색</button>
            </div>
            <div className="text-sm text-text-subtle">
                거래처, 상품, 전표 등을 검색할 수 있습니다.
            </div>
        </div>
    );
}

// 기초이월 윈도우
function CarryoverWindow({ type }: { type: string }) {
    const titles: Record<string, string> = {
        "inventory-carryover": "상품재고이월",
        "receivable-carryover": "미수미지급금이월",
        "cash-carryover": "현금잔고이월",
    };

    return (
        <div className="p-4">
            <h3 className="text-lg font-medium mb-4">{titles[type] || "기초이월"}</h3>
            <div className="space-y-4">
                <div>
                    <label className="block text-sm font-medium mb-1">이월일자</label>
                    <input type="date" className="rounded border px-3 py-2 text-sm" />
                </div>
                <div>
                    <label className="block text-sm font-medium mb-1">이월금액</label>
                    <input type="number" className="rounded border px-3 py-2 text-sm" placeholder="0" />
                </div>
                <button className="rounded bg-brand px-4 py-2 text-sm text-white">이월 처리</button>
            </div>
        </div>
    );
}

// 이메일 전송 윈도우
function EmailWindow() {
    const [recipient, setRecipient] = useState("");
    const [cc, setCc] = useState("");
    const [subject, setSubject] = useState("");
    const [body, setBody] = useState("");
    const [attachments, setAttachments] = useState<string[]>([]);

    const handleSend = () => {
        if (!recipient) {
            alert("받는 사람 이메일을 입력하세요.");
            return;
        }
        if (!subject) {
            alert("제목을 입력하세요.");
            return;
        }
        alert(`이메일이 ${recipient}으로 전송되었습니다.`);
    };

    return (
        <div className="flex h-full flex-col bg-surface-secondary">
            {/* 타이틀바 */}
            <div className="flex items-center justify-between border-b border-surface-tertiary bg-gradient-to-r from-brand to-brand-strong px-3 py-1">
                <span className="text-sm font-medium text-white">이메일 전송</span>
            </div>

            <div className="flex-1 overflow-auto p-4">
                {/* 발송 설정 */}
                <fieldset className="mb-4 rounded border border-surface-tertiary p-3">
                    <legend className="px-2 text-sm text-brand">발송 설정</legend>
                    <div className="space-y-3">
                        <div className="flex items-center gap-2">
                            <label className="w-20 text-sm">보내는 사람</label>
                            <input
                                type="email"
                                value="admin@company.com"
                                readOnly
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-sm text-text"
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <label className="w-20 text-sm">받는 사람</label>
                            <input
                                type="email"
                                value={recipient}
                                onChange={(e) => setRecipient(e.target.value)}
                                placeholder="example@email.com"
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-sm text-text"
                            />
                            <button className="rounded border border-surface-tertiary bg-surface px-3 py-1 text-xs text-text hover:bg-surface-tertiary">
                                주소록
                            </button>
                        </div>
                        <div className="flex items-center gap-2">
                            <label className="w-20 text-sm">참조(CC)</label>
                            <input
                                type="email"
                                value={cc}
                                onChange={(e) => setCc(e.target.value)}
                                placeholder="참조할 이메일"
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-sm text-text"
                            />
                        </div>
                    </div>
                </fieldset>

                {/* 메일 내용 */}
                <fieldset className="mb-4 rounded border border-surface-tertiary p-3">
                    <legend className="px-2 text-sm text-brand">메일 내용</legend>
                    <div className="space-y-3">
                        <div className="flex items-center gap-2">
                            <label className="w-20 text-sm">제목</label>
                            <input
                                type="text"
                                value={subject}
                                onChange={(e) => setSubject(e.target.value)}
                                placeholder="이메일 제목을 입력하세요"
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-sm text-text"
                            />
                        </div>
                        <div>
                            <label className="mb-1 block text-sm">내용</label>
                            <textarea
                                value={body}
                                onChange={(e) => setBody(e.target.value)}
                                placeholder="이메일 내용을 입력하세요..."
                                rows={10}
                                className="w-full resize-none rounded border border-surface-tertiary bg-surface px-2 py-1 text-sm text-text"
                            />
                        </div>
                    </div>
                </fieldset>

                {/* 첨부파일 */}
                <fieldset className="rounded border border-surface-tertiary p-3">
                    <legend className="px-2 text-sm text-brand">첨부파일</legend>
                    <div className="flex items-center gap-2">
                        <button className="rounded border border-surface-tertiary bg-surface px-3 py-1 text-sm text-text hover:bg-surface-tertiary">
                            파일 첨부
                        </button>
                        <span className="text-xs text-text-subtle">
                            {attachments.length > 0 ? `${attachments.length}개 파일 첨부됨` : "첨부된 파일 없음"}
                        </span>
                    </div>
                </fieldset>
            </div>

            {/* 하단 버튼 */}
            <div className="flex justify-end gap-2 border-t border-surface-tertiary bg-surface-tertiary px-4 py-2">
                <button
                    onClick={handleSend}
                    className="rounded border border-brand bg-brand px-4 py-1.5 text-sm text-white hover:bg-brand-strong"
                >
                    이메일 전송
                </button>
                <button className="rounded border border-surface-tertiary bg-surface px-4 py-1.5 text-sm text-text hover:bg-surface-tertiary">
                    닫기
                </button>
            </div>
        </div>
    );
}

// 전자세금계산서 품목 타입
interface TaxInvoiceItem {
    id: string;
    date: string;
    name: string;
    spec: string;
    quantity: number;
    unitPrice: number;
    supplyAmount: number;
    taxAmount: number;
}

// 샘플 전표 데이터
const SAMPLE_VOUCHERS = [
    { id: 'v001', date: '2024-01-15', customer: '테스트거래처', items: [
        { name: '분전반', spec: '600x800x200', quantity: 1, unitPrice: 500000 },
        { name: 'ELB 2P 20A', spec: '상도 SIE-32', quantity: 5, unitPrice: 3300 },
    ]},
    { id: 'v002', date: '2024-01-20', customer: '이지산업', items: [
        { name: 'MCCB 4P 100A', spec: 'SBE-104', quantity: 2, unitPrice: 45000 },
        { name: '외함', spec: '옥내노출 700x500x200', quantity: 1, unitPrice: 180000 },
    ]},
    { id: 'v003', date: '2024-01-25', customer: '한국전기', items: [
        { name: 'ELB 3P 50A', spec: '상도 SEE-53', quantity: 3, unitPrice: 28000 },
    ]},
];

// 전자세금계산서 윈도우
function TaxInvoiceWindow() {
    const windowContext = useWindowContextOptional();
    const [invoiceType, setInvoiceType] = useState<"sales" | "purchase">("sales");
    const [invoiceDate, setInvoiceDate] = useState(new Date().toISOString().split("T")[0]);
    const [customerName, setCustomerName] = useState("");
    const [businessNumber, setBusinessNumber] = useState("");
    const [customerCeoName, setCustomerCeoName] = useState("");
    const [customerAddress, setCustomerAddress] = useState("");
    const [customerEmail, setCustomerEmail] = useState("");
    const [customerBusinessType, setCustomerBusinessType] = useState("");
    const [customerBusinessItem, setCustomerBusinessItem] = useState("");
    const [supplyAmount, setSupplyAmount] = useState("");
    const [taxAmount, setTaxAmount] = useState("");
    const [searchLoading, setSearchLoading] = useState(false);

    // 품목 관련 상태
    const [items, setItems] = useState<TaxInvoiceItem[]>([]);
    const [showLoadVoucherModal, setShowLoadVoucherModal] = useState(false);
    const [showPreviewModal, setShowPreviewModal] = useState(false);

    const recalcTotals = (updatedItems: TaxInvoiceItem[]) => {
        const totalSupply = updatedItems.reduce((sum, item) => sum + item.supplyAmount, 0);
        const totalTax = updatedItems.reduce((sum, item) => sum + item.taxAmount, 0);
        setSupplyAmount(totalSupply.toString());
        setTaxAmount(totalTax.toString());
    };

    const calculateTax = (amount: string) => {
        const num = parseFloat(amount) || 0;
        setTaxAmount(Math.floor(num * 0.1).toString());
    };

    // 사업자번호로 거래처 검색
    const handleSearchCustomer = async () => {
        if (!businessNumber.trim()) {
            alert("사업자번호를 입력하세요.");
            return;
        }
        setSearchLoading(true);
        try {
            const { api } = await import("@/lib/api");
            const result = await api.erp.customers.list({ search: businessNumber.replace(/-/g, '') });
            if (result.items && result.items.length > 0) {
                const customer = result.items[0];
                setCustomerName(customer.name);
                setBusinessNumber(customer.business_number || businessNumber);
                setCustomerCeoName(customer.ceo_name || "");
                setCustomerAddress(customer.address || "");
                setCustomerEmail(customer.email || "");
            } else {
                alert("일치하는 거래처를 찾을 수 없습니다.");
            }
        } catch (error) {
            console.error("Customer search failed:", error);
            alert("거래처 검색에 실패했습니다.");
        } finally {
            setSearchLoading(false);
        }
    };

    const handleIssue = () => {
        if (!customerName) {
            alert("거래처명을 입력하세요.");
            return;
        }
        if (!businessNumber) {
            alert("사업자번호를 입력하세요.");
            return;
        }
        if (!supplyAmount) {
            alert("공급가액을 입력하세요.");
            return;
        }
        alert("국세청 API 연동 준비 중입니다. 세금계산서 데이터가 저장되었습니다.");
    };

    // 빈 품목 행 추가 (인라인 편집)
    const handleAddItem = () => {
        const today = invoiceDate.slice(5).replace('-', '/');
        const newItemData: TaxInvoiceItem = {
            id: `item_${Date.now()}`,
            date: today,
            name: '',
            spec: '',
            quantity: 1,
            unitPrice: 0,
            supplyAmount: 0,
            taxAmount: 0,
        };
        setItems([...items, newItemData]);
    };

    // 품목 인라인 수정 핸들러
    const handleItemChange = (itemId: string, field: string, value: string | number) => {
        const updatedItems = items.map(item => {
            if (item.id !== itemId) return item;
            const updated = { ...item, [field]: value };
            if (field === 'quantity' || field === 'unitPrice') {
                const qty = field === 'quantity' ? (typeof value === 'number' ? value : parseInt(String(value)) || 0) : updated.quantity;
                const price = field === 'unitPrice' ? (typeof value === 'number' ? value : parseInt(String(value)) || 0) : updated.unitPrice;
                updated.quantity = qty;
                updated.unitPrice = price;
                updated.supplyAmount = qty * price;
                updated.taxAmount = Math.floor(qty * price * 0.1);
            }
            return updated;
        });
        setItems(updatedItems);
        recalcTotals(updatedItems);
    };

    // 전표 불러오기 핸들러
    const handleLoadVoucher = () => {
        setShowLoadVoucherModal(true);
    };

    // 전표 선택 확인
    const confirmLoadVoucher = (voucher: typeof SAMPLE_VOUCHERS[0]) => {
        setCustomerName(voucher.customer);

        const loadedItems: TaxInvoiceItem[] = voucher.items.map((item, idx) => {
            const itemSupply = item.quantity * item.unitPrice;
            const itemTax = Math.floor(itemSupply * 0.1);
            return {
                id: `item_${Date.now()}_${idx}`,
                date: voucher.date.slice(5).replace('-', '/'),
                name: item.name,
                spec: item.spec,
                quantity: item.quantity,
                unitPrice: item.unitPrice,
                supplyAmount: itemSupply,
                taxAmount: itemTax,
            };
        });

        setItems(loadedItems);
        recalcTotals(loadedItems);
        setShowLoadVoucherModal(false);
    };

    // 미리보기 핸들러
    const handlePreview = () => {
        if (!customerName) {
            alert("거래처명을 입력하세요.");
            return;
        }
        if (items.length === 0 && !supplyAmount) {
            alert("품목을 추가하거나 공급가액을 입력하세요.");
            return;
        }
        setShowPreviewModal(true);
    };

    // 품목 삭제
    const handleDeleteItem = (itemId: string) => {
        const updatedItems = items.filter(item => item.id !== itemId);
        setItems(updatedItems);
        recalcTotals(updatedItems);
    };

    const handleClose = () => {
        windowContext?.closeThisWindow();
    };

    const totalAmount = (parseFloat(supplyAmount) || 0) + (parseFloat(taxAmount) || 0);

    return (
        <div className="flex h-full flex-col bg-surface-secondary">
            {/* 타이틀바 */}
            <div className="flex items-center justify-between border-b border-surface-tertiary bg-gradient-to-r from-brand to-brand-strong px-3 py-1">
                <span className="text-sm font-medium text-white">전자세금계산서</span>
            </div>

            <div className="flex-1 overflow-auto p-4">
                {/* 발행 유형 */}
                <div className="mb-4 flex gap-4">
                    <label className="flex items-center gap-2">
                        <input
                            type="radio"
                            name="invoiceType"
                            checked={invoiceType === "sales"}
                            onChange={() => setInvoiceType("sales")}
                        />
                        <span className="text-sm">매출 세금계산서</span>
                    </label>
                    <label className="flex items-center gap-2">
                        <input
                            type="radio"
                            name="invoiceType"
                            checked={invoiceType === "purchase"}
                            onChange={() => setInvoiceType("purchase")}
                        />
                        <span className="text-sm">매입 세금계산서</span>
                    </label>
                </div>

                {/* 공급자 정보 */}
                <fieldset className="mb-4 rounded border border-surface-tertiary p-3">
                    <legend className="px-2 text-sm text-brand">공급자 정보</legend>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                        <div className="flex items-center gap-2">
                            <label className="w-24 text-text">사업자번호</label>
                            <input
                                type="text"
                                value="123-45-67890"
                                readOnly
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-text"
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <label className="w-24 text-text">상호</label>
                            <input
                                type="text"
                                value="한국산업주식회사"
                                readOnly
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-text"
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <label className="w-24 text-text">대표자</label>
                            <input
                                type="text"
                                value="김대표"
                                readOnly
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-text"
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <label className="w-24 text-text">업태/종목</label>
                            <input
                                type="text"
                                value="제조업 / 전기기기"
                                readOnly
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-text"
                            />
                        </div>
                        <div className="col-span-2 flex items-center gap-2">
                            <label className="w-24 text-text">주소</label>
                            <input
                                type="text"
                                value="서울시 강남구 테헤란로 123"
                                readOnly
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-text"
                            />
                        </div>
                        <div className="col-span-2 flex items-center gap-2">
                            <label className="w-24 text-text">이메일</label>
                            <input
                                type="text"
                                value="admin@company.com"
                                readOnly
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-text"
                            />
                        </div>
                    </div>
                </fieldset>

                {/* 공급받는자 정보 */}
                <fieldset className="mb-4 rounded border border-surface-tertiary p-3">
                    <legend className="px-2 text-sm text-brand">공급받는자 정보</legend>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                        <div className="flex items-center gap-2">
                            <label className="w-24 text-text">사업자번호</label>
                            <input
                                type="text"
                                value={businessNumber}
                                onChange={(e) => setBusinessNumber(e.target.value)}
                                placeholder="000-00-00000"
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-text"
                            />
                            <button
                                onClick={handleSearchCustomer}
                                disabled={searchLoading}
                                className="rounded border border-surface-tertiary bg-surface px-2 py-0.5 text-xs text-text hover:bg-surface-tertiary disabled:opacity-50"
                            >
                                {searchLoading ? "..." : "검색"}
                            </button>
                        </div>
                        <div className="flex items-center gap-2">
                            <label className="w-24 text-text">상호</label>
                            <input
                                type="text"
                                value={customerName}
                                onChange={(e) => setCustomerName(e.target.value)}
                                placeholder="거래처명"
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-text"
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <label className="w-24 text-text">대표자명</label>
                            <input
                                type="text"
                                value={customerCeoName}
                                onChange={(e) => setCustomerCeoName(e.target.value)}
                                placeholder="대표자명"
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-text"
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <label className="w-24 text-text">업태/종목</label>
                            <input
                                type="text"
                                value={customerBusinessType}
                                onChange={(e) => setCustomerBusinessType(e.target.value)}
                                placeholder="업태"
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-text"
                            />
                            <input
                                type="text"
                                value={customerBusinessItem}
                                onChange={(e) => setCustomerBusinessItem(e.target.value)}
                                placeholder="종목"
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-text"
                            />
                        </div>
                        <div className="col-span-2 flex items-center gap-2">
                            <label className="w-24 text-text">주소</label>
                            <input
                                type="text"
                                value={customerAddress}
                                onChange={(e) => setCustomerAddress(e.target.value)}
                                placeholder="사업장 주소"
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-text"
                            />
                        </div>
                        <div className="col-span-2 flex items-center gap-2">
                            <label className="w-24 text-text">이메일</label>
                            <input
                                type="email"
                                value={customerEmail}
                                onChange={(e) => setCustomerEmail(e.target.value)}
                                placeholder="이메일 주소"
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-text"
                            />
                        </div>
                    </div>
                </fieldset>

                {/* 세금계산서 정보 */}
                <fieldset className="mb-4 rounded border border-surface-tertiary p-3">
                    <legend className="px-2 text-sm text-brand">세금계산서 정보</legend>
                    <div className="space-y-3 text-sm">
                        <div className="flex items-center gap-2">
                            <label className="w-24 text-text">작성일자</label>
                            <input
                                type="date"
                                value={invoiceDate}
                                onChange={(e) => setInvoiceDate(e.target.value)}
                                className="rounded border border-surface-tertiary bg-surface px-2 py-1 text-text"
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <label className="w-24 text-text">공급가액</label>
                            <input
                                type="number"
                                value={supplyAmount}
                                onChange={(e) => {
                                    setSupplyAmount(e.target.value);
                                    calculateTax(e.target.value);
                                }}
                                placeholder="0"
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-right text-text"
                            />
                            <span className="text-text">원</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <label className="w-24 text-text">세액</label>
                            <input
                                type="number"
                                value={taxAmount}
                                onChange={(e) => setTaxAmount(e.target.value)}
                                placeholder="0"
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-right text-text"
                            />
                            <span className="text-text">원</span>
                        </div>
                        <div className="flex items-center gap-2 border-t border-surface-tertiary pt-2">
                            <label className="w-24 font-medium text-text">합계금액</label>
                            <span className="flex-1 text-right text-lg font-bold text-brand">
                                {totalAmount.toLocaleString()}원
                            </span>
                        </div>
                    </div>
                </fieldset>

                {/* 품목 정보 - 인라인 편집 */}
                <fieldset className="rounded border border-surface-tertiary p-3">
                    <legend className="px-2 text-sm text-brand">품목 정보</legend>
                    <div className="max-h-48 overflow-auto border border-surface-tertiary bg-surface">
                        <table className="w-full border-collapse text-xs">
                            <thead className="sticky top-0 bg-surface-secondary">
                                <tr>
                                    <th className="border-b border-surface-tertiary px-2 py-1 text-text w-20">월/일</th>
                                    <th className="border-b border-surface-tertiary px-2 py-1 text-text">품목</th>
                                    <th className="border-b border-surface-tertiary px-2 py-1 text-text">규격</th>
                                    <th className="border-b border-surface-tertiary px-2 py-1 text-text text-right w-16">수량</th>
                                    <th className="border-b border-surface-tertiary px-2 py-1 text-text text-right w-20">단가</th>
                                    <th className="border-b border-surface-tertiary px-2 py-1 text-text text-right w-24">공급가액</th>
                                    <th className="border-b border-surface-tertiary px-2 py-1 text-text text-right w-20">세액</th>
                                    <th className="border-b border-surface-tertiary px-2 py-1 text-text w-8"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.length === 0 ? (
                                    <tr>
                                        <td className="border-b border-surface-tertiary px-2 py-3 text-center text-text-subtle" colSpan={8}>
                                            아래 "추가" 버튼으로 품목을 추가하세요
                                        </td>
                                    </tr>
                                ) : (
                                    items.map((item) => (
                                        <tr key={item.id} className="hover:bg-surface-secondary">
                                            <td className="border-b border-surface-tertiary px-1 py-0.5">
                                                <input
                                                    type="text"
                                                    value={item.date}
                                                    onChange={(e) => handleItemChange(item.id, 'date', e.target.value)}
                                                    className="w-full rounded border border-surface-tertiary bg-surface px-1 py-0.5 text-center text-xs text-text"
                                                    placeholder="MM/DD"
                                                />
                                            </td>
                                            <td className="border-b border-surface-tertiary px-1 py-0.5">
                                                <input
                                                    type="text"
                                                    value={item.name}
                                                    onChange={(e) => handleItemChange(item.id, 'name', e.target.value)}
                                                    className="w-full rounded border border-surface-tertiary bg-surface px-1 py-0.5 text-xs text-text"
                                                    placeholder="품목명"
                                                />
                                            </td>
                                            <td className="border-b border-surface-tertiary px-1 py-0.5">
                                                <input
                                                    type="text"
                                                    value={item.spec}
                                                    onChange={(e) => handleItemChange(item.id, 'spec', e.target.value)}
                                                    className="w-full rounded border border-surface-tertiary bg-surface px-1 py-0.5 text-xs text-text"
                                                    placeholder="규격"
                                                />
                                            </td>
                                            <td className="border-b border-surface-tertiary px-1 py-0.5">
                                                <input
                                                    type="number"
                                                    value={item.quantity}
                                                    onChange={(e) => handleItemChange(item.id, 'quantity', parseInt(e.target.value) || 0)}
                                                    min="0"
                                                    className="w-full rounded border border-surface-tertiary bg-surface px-1 py-0.5 text-right text-xs text-text"
                                                />
                                            </td>
                                            <td className="border-b border-surface-tertiary px-1 py-0.5">
                                                <input
                                                    type="number"
                                                    value={item.unitPrice}
                                                    onChange={(e) => handleItemChange(item.id, 'unitPrice', parseInt(e.target.value) || 0)}
                                                    min="0"
                                                    className="w-full rounded border border-surface-tertiary bg-surface px-1 py-0.5 text-right text-xs text-text"
                                                />
                                            </td>
                                            <td className="border-b border-surface-tertiary px-2 py-1 text-right text-text">{item.supplyAmount.toLocaleString()}</td>
                                            <td className="border-b border-surface-tertiary px-2 py-1 text-right text-text">{item.taxAmount.toLocaleString()}</td>
                                            <td className="border-b border-surface-tertiary px-1 py-1 text-center">
                                                <button
                                                    onClick={() => handleDeleteItem(item.id)}
                                                    className="text-red-500 hover:text-red-700"
                                                    title="삭제"
                                                >
                                                    ×
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                    <div className="mt-2 flex gap-2">
                        <button onClick={handleAddItem} className="rounded border border-surface-tertiary bg-surface px-3 py-1 text-xs text-text hover:bg-surface-tertiary">
                            추가
                        </button>
                        <button onClick={handleLoadVoucher} className="rounded border border-surface-tertiary bg-surface px-3 py-1 text-xs text-text hover:bg-surface-tertiary">
                            전표 불러오기
                        </button>
                    </div>
                </fieldset>
            </div>

            {/* 하단 버튼 */}
            <div className="flex justify-end gap-2 border-t border-surface-tertiary bg-surface-tertiary px-4 py-2">
                <button
                    onClick={handleIssue}
                    className="rounded border border-brand bg-brand px-4 py-1.5 text-sm text-white hover:bg-brand-strong"
                >
                    세금계산서 발행
                </button>
                <button onClick={handlePreview} className="rounded border border-surface-tertiary bg-surface px-4 py-1.5 text-sm text-text hover:bg-surface-tertiary">
                    미리보기
                </button>
                <button onClick={handleClose} className="rounded border border-surface-tertiary bg-surface px-4 py-1.5 text-sm text-text hover:bg-surface-tertiary">
                    닫기
                </button>
            </div>

            {/* 전표 불러오기 모달 */}
            {showLoadVoucherModal && (
                <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/50">
                    <div className="w-[500px] rounded-lg border border-surface-tertiary bg-surface shadow-xl">
                        <div className="border-b border-surface-tertiary bg-brand px-4 py-2">
                            <span className="font-medium text-white">전표 불러오기</span>
                        </div>
                        <div className="max-h-80 overflow-auto p-4">
                            <table className="w-full border-collapse text-sm">
                                <thead className="sticky top-0 bg-surface-secondary">
                                    <tr>
                                        <th className="border-b border-surface-tertiary px-3 py-2 text-left text-text">전표번호</th>
                                        <th className="border-b border-surface-tertiary px-3 py-2 text-left text-text">날짜</th>
                                        <th className="border-b border-surface-tertiary px-3 py-2 text-left text-text">거래처</th>
                                        <th className="border-b border-surface-tertiary px-3 py-2 text-center text-text">품목수</th>
                                        <th className="border-b border-surface-tertiary px-3 py-2 text-text"></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {SAMPLE_VOUCHERS.map((voucher) => (
                                        <tr key={voucher.id} className="hover:bg-surface-secondary">
                                            <td className="border-b border-surface-tertiary px-3 py-2 text-text">{voucher.id}</td>
                                            <td className="border-b border-surface-tertiary px-3 py-2 text-text">{voucher.date}</td>
                                            <td className="border-b border-surface-tertiary px-3 py-2 text-text">{voucher.customer}</td>
                                            <td className="border-b border-surface-tertiary px-3 py-2 text-center text-text">{voucher.items.length}</td>
                                            <td className="border-b border-surface-tertiary px-3 py-2 text-center">
                                                <button
                                                    onClick={() => confirmLoadVoucher(voucher)}
                                                    className="rounded bg-brand px-3 py-1 text-xs text-white hover:bg-brand-strong"
                                                >
                                                    선택
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        <div className="flex justify-end border-t border-surface-tertiary px-4 py-3">
                            <button
                                onClick={() => setShowLoadVoucherModal(false)}
                                className="rounded border border-surface-tertiary bg-surface px-4 py-1.5 text-sm text-text hover:bg-surface-tertiary"
                            >
                                닫기
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* 미리보기 모달 */}
            {showPreviewModal && (
                <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/50">
                    <div className="w-[600px] max-h-[80%] rounded-lg border border-surface-tertiary bg-white shadow-xl overflow-hidden flex flex-col">
                        <div className="border-b border-gray-300 bg-blue-600 px-4 py-2">
                            <span className="font-medium text-white">전자세금계산서 미리보기</span>
                        </div>
                        <div className="flex-1 overflow-auto p-6">
                            {/* 세금계산서 양식 */}
                            <div className="border-2 border-black">
                                {/* 헤더 */}
                                <div className="border-b-2 border-black bg-blue-50 p-3 text-center">
                                    <h2 className="text-xl font-bold text-black">전 자 세 금 계 산 서</h2>
                                    <p className="text-sm text-gray-600">{invoiceType === 'sales' ? '(공급자 보관용)' : '(공급받는자 보관용)'}</p>
                                </div>

                                {/* 공급자/공급받는자 정보 */}
                                <div className="grid grid-cols-2 border-b border-black text-xs">
                                    <div className="border-r border-black p-2">
                                        <div className="mb-1 font-bold text-black">공급자</div>
                                        <div className="text-black">사업자번호: 123-45-67890</div>
                                        <div className="text-black">상호: 한국산업주식회사</div>
                                        <div className="text-black">대표자: 김대표</div>
                                        <div className="text-black">주소: 서울시 강남구 테헤란로 123</div>
                                        <div className="text-black">업태/종목: 제조업 / 전기기기</div>
                                    </div>
                                    <div className="p-2">
                                        <div className="mb-1 font-bold text-black">공급받는자</div>
                                        <div className="text-black">사업자번호: {businessNumber || '-'}</div>
                                        <div className="text-black">상호: {customerName || '-'}</div>
                                        <div className="text-black">대표자: {customerCeoName || '-'}</div>
                                        <div className="text-black">주소: {customerAddress || '-'}</div>
                                        <div className="text-black">업태/종목: {customerBusinessType || '-'} / {customerBusinessItem || '-'}</div>
                                        {customerEmail && <div className="text-black">이메일: {customerEmail}</div>}
                                    </div>
                                </div>

                                {/* 작성일자 및 금액 */}
                                <div className="grid grid-cols-4 border-b border-black text-xs">
                                    <div className="border-r border-black p-2">
                                        <div className="font-bold text-black">작성일자</div>
                                        <div className="text-black">{invoiceDate}</div>
                                    </div>
                                    <div className="border-r border-black p-2">
                                        <div className="font-bold text-black">공급가액</div>
                                        <div className="text-black">{parseInt(supplyAmount || '0').toLocaleString()}원</div>
                                    </div>
                                    <div className="border-r border-black p-2">
                                        <div className="font-bold text-black">세액</div>
                                        <div className="text-black">{parseInt(taxAmount || '0').toLocaleString()}원</div>
                                    </div>
                                    <div className="p-2">
                                        <div className="font-bold text-black">합계금액</div>
                                        <div className="font-bold text-blue-600">{totalAmount.toLocaleString()}원</div>
                                    </div>
                                </div>

                                {/* 품목 테이블 */}
                                <div className="text-xs">
                                    <table className="w-full border-collapse">
                                        <thead>
                                            <tr className="bg-gray-100">
                                                <th className="border border-black px-2 py-1 text-black">월/일</th>
                                                <th className="border border-black px-2 py-1 text-black">품목</th>
                                                <th className="border border-black px-2 py-1 text-black">규격</th>
                                                <th className="border border-black px-2 py-1 text-black">수량</th>
                                                <th className="border border-black px-2 py-1 text-black">단가</th>
                                                <th className="border border-black px-2 py-1 text-black">공급가액</th>
                                                <th className="border border-black px-2 py-1 text-black">세액</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {items.length > 0 ? items.map((item) => (
                                                <tr key={item.id}>
                                                    <td className="border border-black px-2 py-1 text-center text-black">{item.date}</td>
                                                    <td className="border border-black px-2 py-1 text-black">{item.name}</td>
                                                    <td className="border border-black px-2 py-1 text-black">{item.spec}</td>
                                                    <td className="border border-black px-2 py-1 text-right text-black">{item.quantity}</td>
                                                    <td className="border border-black px-2 py-1 text-right text-black">{item.unitPrice.toLocaleString()}</td>
                                                    <td className="border border-black px-2 py-1 text-right text-black">{item.supplyAmount.toLocaleString()}</td>
                                                    <td className="border border-black px-2 py-1 text-right text-black">{item.taxAmount.toLocaleString()}</td>
                                                </tr>
                                            )) : (
                                                <tr>
                                                    <td className="border border-black px-2 py-1 text-center text-black">{invoiceDate.slice(5).replace('-', '/')}</td>
                                                    <td className="border border-black px-2 py-1 text-black">-</td>
                                                    <td className="border border-black px-2 py-1 text-black">-</td>
                                                    <td className="border border-black px-2 py-1 text-right text-black">1</td>
                                                    <td className="border border-black px-2 py-1 text-right text-black">{parseInt(supplyAmount || '0').toLocaleString()}</td>
                                                    <td className="border border-black px-2 py-1 text-right text-black">{parseInt(supplyAmount || '0').toLocaleString()}</td>
                                                    <td className="border border-black px-2 py-1 text-right text-black">{parseInt(taxAmount || '0').toLocaleString()}</td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                        <div className="flex justify-end gap-2 border-t border-gray-200 bg-gray-50 px-4 py-3">
                            <button
                                onClick={() => window.print()}
                                className="rounded bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700"
                            >
                                인쇄
                            </button>
                            <button
                                onClick={() => setShowPreviewModal(false)}
                                className="rounded border border-gray-300 bg-white px-4 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
                            >
                                닫기
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// 택배사별 배송조회 URL 매핑
const COURIER_TRACKING_URLS: Record<string, string> = {
    daeshin: "https://www.ds3211.co.kr/freight/tracking",
    kyungdong: "https://kdexp.com/delivery/delivery.do",
    cj: "https://www.cjlogistics.com/ko/tool/parcel/tracking",
    hanjin: "https://www.hanjin.com/kor/CMS/DeliveryMgr/WaybillResult.do",
    lotte: "https://www.lotteglogis.com/home/reservation/tracking/index",
    post: "https://service.epost.go.kr/trace.RetrieveDomRi498.postal",
    logen: "https://www.ilogen.com/web/personal/trace",
};

// 물류송장전송 윈도우
function LogisticsWindow() {
    const windowContext = useWindowContextOptional();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [trackingNumber, setTrackingNumber] = useState("");
    const [courier, setCourier] = useState("daeshin");
    const [recipient, setRecipient] = useState("");
    const [phone, setPhone] = useState("");
    const [address, setAddress] = useState("");
    const [ocrProcessing, setOcrProcessing] = useState(false);
    const [ocrResult, setOcrResult] = useState("");

    const handleImageUpload = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        if (!file.type.startsWith("image/")) {
            alert("이미지 파일만 업로드 가능합니다.");
            return;
        }

        setOcrProcessing(true);
        setOcrResult("");

        try {
            // OCR: 서버사이드 API 연동 준비 (tesseract.js 미설치 시 안내)
            // TODO[KIS-OCR]: 서버사이드 OCR API 연동 후 활성화
            const formData = new FormData();
            formData.append("file", file);
            const res = await fetch(`${API_BASE_URL}/v1/ocr/recognize`, {
                method: "POST",
                body: formData,
            }).catch(() => null);
            if (res && res.ok) {
                const data = await res.json();
                const text = data.text || "";
                setOcrResult(text);
                const trackingMatch = text.match(/\d{10,14}/);
                if (trackingMatch) {
                    setTrackingNumber(trackingMatch[0]);
                }
                const phoneMatch = text.match(/01[016789]-?\d{3,4}-?\d{4}/);
                if (phoneMatch) {
                    setPhone(phoneMatch[0]);
                }
            } else {
                alert("OCR 서버가 준비되지 않았습니다.\n운송장번호와 수취인 정보를 수동으로 입력해주세요.");
            }
        } catch (err) {
            alert("OCR 처리 중 오류가 발생했습니다.\n수동으로 입력해주세요.");
        } finally {
            setOcrProcessing(false);
        }
    };

    const handleTrackDelivery = () => {
        if (!trackingNumber) {
            alert("운송장번호를 입력하세요.");
            return;
        }
        const baseUrl = COURIER_TRACKING_URLS[courier];
        if (baseUrl) {
            window.open(baseUrl, "_blank");
        }
    };

    const handleSendInvoice = () => {
        if (!trackingNumber || !recipient || !phone) {
            alert("모든 필수 항목을 입력하세요.");
            return;
        }

        // SMS 전송 구조 재활용 (localStorage 기반)
        const smsHistory = JSON.parse(localStorage.getItem("sms-history") || "[]");
        const courierNames: Record<string, string> = {
            daeshin: "대신화물", kyungdong: "경동화물", cj: "CJ대한통운",
            hanjin: "한진택배", lotte: "롯데택배", post: "우체국택배", logen: "로젠택배",
        };
        const msg = `[송장안내] ${courierNames[courier] || courier}\n운송장번호: ${trackingNumber}\n수취인: ${recipient}`;
        smsHistory.unshift({
            sender: "01044389180",
            recipients: [phone],
            message: msg,
            type: "LMS",
            sentAt: new Date().toISOString(),
            status: "queued",
        });
        localStorage.setItem("sms-history", JSON.stringify(smsHistory));
        alert(`송장 정보가 ${phone}으로 전송되었습니다.\n운송장번호: ${trackingNumber}\n수취인: ${recipient}`);
    };

    const handleClose = () => {
        windowContext?.closeThisWindow();
    };

    return (
        <div className="relative flex h-full flex-col bg-surface-secondary">
            <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFileChange}
            />
            <div className="flex items-center justify-between border-b border-surface-tertiary bg-gradient-to-r from-brand to-brand-strong px-3 py-1">
                <span className="text-sm font-medium text-white">물류송장전송</span>
            </div>
            <div className="flex-1 overflow-auto p-4">
                <fieldset className="mb-4 rounded border border-surface-tertiary p-3">
                    <legend className="px-2 text-sm text-brand">송장 정보</legend>
                    <div className="space-y-3">
                        <div className="flex items-center gap-2">
                            <label className="w-24 text-sm">택배사</label>
                            <select
                                value={courier}
                                onChange={(e) => setCourier(e.target.value)}
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-sm text-text"
                            >
                                <option value="daeshin">대신화물</option>
                                <option value="kyungdong">경동화물</option>
                                <option value="cj">CJ대한통운</option>
                                <option value="hanjin">한진택배</option>
                                <option value="lotte">롯데택배</option>
                                <option value="post">우체국택배</option>
                                <option value="logen">로젠택배</option>
                            </select>
                        </div>
                        <div className="flex items-center gap-2">
                            <label className="w-24 text-sm">운송장번호</label>
                            <input
                                type="text"
                                value={trackingNumber}
                                onChange={(e) => setTrackingNumber(e.target.value)}
                                placeholder="운송장번호 입력"
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-sm text-text"
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <label className="w-24 text-sm">이미지 인식</label>
                            <button
                                onClick={handleImageUpload}
                                disabled={ocrProcessing}
                                className="rounded border border-surface-tertiary bg-surface px-3 py-1 text-sm text-text hover:bg-surface-tertiary disabled:opacity-50"
                            >
                                {ocrProcessing ? "인식 중..." : "이미지 첨부 (OCR)"}
                            </button>
                            {ocrResult && (
                                <span className="text-xs text-green-600">OCR 인식 완료</span>
                            )}
                        </div>
                        {ocrResult && (
                            <div className="rounded border border-surface-tertiary bg-gray-50 p-2">
                                <p className="mb-1 text-xs font-medium text-text-subtle">OCR 인식 결과:</p>
                                <pre className="max-h-20 overflow-auto text-xs text-text">{ocrResult}</pre>
                            </div>
                        )}
                    </div>
                </fieldset>
                <fieldset className="mb-4 rounded border border-surface-tertiary p-3">
                    <legend className="px-2 text-sm text-brand">수취인 정보</legend>
                    <div className="space-y-3">
                        <div className="flex items-center gap-2">
                            <label className="w-24 text-sm">수취인명</label>
                            <input
                                type="text"
                                value={recipient}
                                onChange={(e) => setRecipient(e.target.value)}
                                placeholder="수취인명"
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-sm text-text"
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <label className="w-24 text-sm">연락처</label>
                            <input
                                type="tel"
                                value={phone}
                                onChange={(e) => setPhone(e.target.value)}
                                placeholder="010-0000-0000"
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-sm text-text"
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <label className="w-24 text-sm">배송주소</label>
                            <input
                                type="text"
                                value={address}
                                onChange={(e) => setAddress(e.target.value)}
                                placeholder="배송 주소"
                                className="flex-1 rounded border border-surface-tertiary bg-surface px-2 py-1 text-sm text-text"
                            />
                        </div>
                    </div>
                </fieldset>
            </div>
            <div className="flex justify-end gap-2 border-t border-surface-tertiary bg-surface-tertiary px-4 py-2">
                <button
                    onClick={handleTrackDelivery}
                    className="rounded border border-blue-400 bg-blue-50 px-4 py-1.5 text-sm text-blue-700 hover:bg-blue-100"
                >
                    배송조회
                </button>
                <button
                    onClick={handleSendInvoice}
                    className="rounded border border-brand bg-brand px-4 py-1.5 text-sm text-white hover:bg-brand-strong"
                >
                    송장전송
                </button>
                <button
                    onClick={handleClose}
                    className="rounded border border-surface-tertiary bg-surface px-4 py-1.5 text-sm text-text hover:bg-surface-tertiary"
                >
                    닫기
                </button>
            </div>
        </div>
    );
}

// 재고 윈도우
function InventoryWindow({ type }: { type: string }) {
    const titles: Record<string, string> = {
        "inventory-adjust": "재고조정",
        "cost-recalc": "원가재계산",
    };

    return (
        <div className="p-4 bg-surface">
            <h3 className="text-lg font-medium mb-4 text-text-strong">{titles[type] || "재고관리"}</h3>
            {type === "inventory-adjust" ? (
                <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium mb-1 text-text">상품</label>
                            <select className="w-full rounded border border-surface-tertiary bg-surface px-3 py-2 text-sm text-text">
                                <option>상품 선택</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1 text-text">조정수량</label>
                            <input type="number" className="w-full rounded border border-surface-tertiary bg-surface px-3 py-2 text-sm text-text" placeholder="0" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1 text-text">사유</label>
                            <input type="text" className="w-full rounded border border-surface-tertiary bg-surface px-3 py-2 text-sm text-text" placeholder="조정 사유" />
                        </div>
                    </div>
                    <button className="rounded bg-brand px-4 py-2 text-sm text-white hover:bg-brand-strong">재고 조정</button>
                </div>
            ) : (
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1 text-text">재계산 기준일</label>
                        <input type="date" className="rounded border border-surface-tertiary bg-surface px-3 py-2 text-sm text-text" />
                    </div>
                    <button className="rounded bg-brand px-4 py-2 text-sm text-white hover:bg-brand-strong">원가 재계산</button>
                </div>
            )}
        </div>
    );
}

// 모바일 감지 훅
function useIsMobile() {
    const [isMobile, setIsMobile] = useState(false);

    useEffect(() => {
        const checkMobile = () => {
            setIsMobile(window.innerWidth < 1024);
        };
        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    return isMobile;
}

// 단일 윈도우 컴포넌트
function ERPWindow({ config, onClose, onMinimize, onFocus, onUpdate }: ERPWindowProps) {
    const windowRef = useRef<HTMLDivElement>(null);
    const [isDragging, setIsDragging] = useState(false);
    const [isResizing, setIsResizing] = useState<string | null>(null);
    const [isMaximized, setIsMaximized] = useState(false);
    const [isOpening, setIsOpening] = useState(true);
    const [prevState, setPrevState] = useState({ x: config.x, y: config.y, width: config.width, height: config.height });
    const dragOffset = useRef({ x: 0, y: 0 });
    const resizeStart = useRef({ x: 0, y: 0, width: 0, height: 0, windowX: 0, windowY: 0 });
    const isMobile = useIsMobile();

    // 윈도우 열림 애니메이션
    useEffect(() => {
        const timer = setTimeout(() => setIsOpening(false), 50);
        return () => clearTimeout(timer);
    }, []);

    // 드래그 시작
    const handleDragStart = (e: React.MouseEvent) => {
        if ((e.target as HTMLElement).closest("button")) return;
        e.preventDefault();
        setIsDragging(true);
        dragOffset.current = {
            x: e.clientX - config.x,
            y: e.clientY - config.y,
        };
        onFocus();
    };

    // 리사이즈 시작
    const handleResizeStart = (e: React.MouseEvent, direction: string) => {
        e.preventDefault();
        e.stopPropagation();
        setIsResizing(direction);
        resizeStart.current = {
            x: e.clientX,
            y: e.clientY,
            width: config.width,
            height: config.height,
            windowX: config.x,
            windowY: config.y,
        };
        onFocus();
    };

    // 최대화/복원
    const toggleMaximize = () => {
        if (isMaximized) {
            onUpdate(prevState);
            setIsMaximized(false);
        } else {
            setPrevState({ x: config.x, y: config.y, width: config.width, height: config.height });
            onUpdate({ x: 0, y: 0, width: window.innerWidth - 300, height: window.innerHeight - 150 });
            setIsMaximized(true);
        }
    };

    // 드래그/리사이즈 핸들러
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (isDragging) {
                const newX = e.clientX - dragOffset.current.x;
                const newY = e.clientY - dragOffset.current.y;
                onUpdate({ x: newX, y: newY });
            } else if (isResizing) {
                const deltaX = e.clientX - resizeStart.current.x;
                const deltaY = e.clientY - resizeStart.current.y;
                const minWidth = 400;
                const minHeight = 300;

                let newWidth = resizeStart.current.width;
                let newHeight = resizeStart.current.height;
                let newX = resizeStart.current.windowX;
                let newY = resizeStart.current.windowY;

                if (isResizing.includes("e")) {
                    newWidth = Math.max(minWidth, resizeStart.current.width + deltaX);
                }
                if (isResizing.includes("w")) {
                    const potentialWidth = resizeStart.current.width - deltaX;
                    if (potentialWidth >= minWidth) {
                        newWidth = potentialWidth;
                        newX = resizeStart.current.windowX + deltaX;
                    }
                }
                if (isResizing.includes("s")) {
                    newHeight = Math.max(minHeight, resizeStart.current.height + deltaY);
                }
                if (isResizing.includes("n")) {
                    const potentialHeight = resizeStart.current.height - deltaY;
                    if (potentialHeight >= minHeight) {
                        newHeight = potentialHeight;
                        newY = resizeStart.current.windowY + deltaY;
                    }
                }

                onUpdate({ x: newX, y: newY, width: newWidth, height: newHeight });
            }
        };

        const handleMouseUp = () => {
            setIsDragging(false);
            setIsResizing(null);
        };

        if (isDragging || isResizing) {
            document.addEventListener("mousemove", handleMouseMove);
            document.addEventListener("mouseup", handleMouseUp);
        }

        return () => {
            document.removeEventListener("mousemove", handleMouseMove);
            document.removeEventListener("mouseup", handleMouseUp);
        };
    }, [isDragging, isResizing, onUpdate]);

    if (config.minimized) return null;

    // 모바일에서는 전체화면으로 표시
    const mobileStyles = isMobile ? {
        left: 0,
        top: 0,
        width: '100vw',
        height: '100vh',
        zIndex: config.zIndex + 1000, // 모바일에서 최상위
    } : {
        left: config.x,
        top: config.y,
        width: config.width,
        height: config.height,
        zIndex: config.zIndex,
    };

    return (
        <div
            ref={windowRef}
            className={cn(
                "fixed flex flex-col bg-surface shadow-2xl overflow-hidden",
                // 드래그/리사이즈 중에는 transition 비활성화 (즉시 반응)
                isDragging || isResizing
                    ? "transition-none"
                    : "transition-all duration-300 ease-out",
                // 모바일에서는 전체화면, 데스크탑에서는 윈도우 형태
                isMobile ? "inset-0 rounded-none border-0" : "rounded-lg border border-surface-tertiary",
                !isMobile && isDragging && "cursor-grabbing",
                isOpening
                    ? "opacity-0 scale-95 translate-y-4"
                    : "opacity-100 scale-100 translate-y-0"
            )}
            style={mobileStyles}
            onMouseDown={onFocus}
        >
            {/* 타이틀 바 */}
            <div
                className={cn(
                    "flex h-10 items-center justify-between border-b bg-surface px-3 select-none",
                    !isMobile && "cursor-grab"
                )}
                onMouseDown={!isMobile ? handleDragStart : undefined}
            >
                <span className="text-sm font-medium truncate">{config.title}</span>
                <div className="flex items-center gap-1">
                    {/* 최소화/최대화 버튼 - 데스크탑에서만 표시 */}
                    {!isMobile && (
                        <>
                            <button
                                onClick={onMinimize}
                                className="rounded p-1 hover:bg-surface-secondary"
                                title="최소화"
                            >
                                <Minus className="h-4 w-4" />
                            </button>
                            <button
                                onClick={toggleMaximize}
                                className="rounded p-1 hover:bg-surface-secondary"
                                title={isMaximized ? "복원" : "최대화"}
                            >
                                {isMaximized ? (
                                    <Minimize2 className="h-4 w-4" />
                                ) : (
                                    <Maximize2 className="h-4 w-4" />
                                )}
                            </button>
                        </>
                    )}
                    <button
                        onClick={onClose}
                        className="rounded p-1.5 hover:bg-red-100 hover:text-red-600"
                        title="닫기"
                    >
                        <X className={cn("h-4 w-4", isMobile && "h-5 w-5")} />
                    </button>
                </div>
            </div>

            {/* 컨텐츠 */}
            <div className="flex-1 overflow-auto">
                <WindowProvider windowId={config.id} onClose={onClose}>
                    {getWindowContent(config.type)}
                </WindowProvider>
            </div>

            {/* 8방향 리사이즈 핸들 - 데스크탑에서만 표시 */}
            {!isMaximized && !isMobile && (
                <>
                    {/* 모서리 */}
                    <div
                        className="absolute -left-1 -top-1 h-3 w-3 cursor-nw-resize"
                        onMouseDown={(e) => handleResizeStart(e, "nw")}
                    />
                    <div
                        className="absolute -right-1 -top-1 h-3 w-3 cursor-ne-resize"
                        onMouseDown={(e) => handleResizeStart(e, "ne")}
                    />
                    <div
                        className="absolute -bottom-1 -left-1 h-3 w-3 cursor-sw-resize"
                        onMouseDown={(e) => handleResizeStart(e, "sw")}
                    />
                    <div
                        className="absolute -bottom-1 -right-1 h-3 w-3 cursor-se-resize"
                        onMouseDown={(e) => handleResizeStart(e, "se")}
                    />
                    {/* 변 */}
                    <div
                        className="absolute -top-1 left-2 right-2 h-2 cursor-n-resize"
                        onMouseDown={(e) => handleResizeStart(e, "n")}
                    />
                    <div
                        className="absolute -bottom-1 left-2 right-2 h-2 cursor-s-resize"
                        onMouseDown={(e) => handleResizeStart(e, "s")}
                    />
                    <div
                        className="absolute -left-1 bottom-2 top-2 w-2 cursor-w-resize"
                        onMouseDown={(e) => handleResizeStart(e, "w")}
                    />
                    <div
                        className="absolute -right-1 bottom-2 top-2 w-2 cursor-e-resize"
                        onMouseDown={(e) => handleResizeStart(e, "e")}
                    />
                </>
            )}
        </div>
    );
}

export function ERPWindowManager({
    windows,
    onClose,
    onMinimize,
    onFocus,
    onUpdate,
}: ERPWindowManagerProps) {
    const [mounted, setMounted] = useState(false);
    useEffect(() => setMounted(true), []);

    // Portal: document.body에 직접 렌더링 → 부모 overflow/transform 영향 제거
    if (!mounted) return null;

    return createPortal(
        <>
            {windows.map((window) => (
                <ERPWindow
                    key={window.id}
                    config={window}
                    onClose={() => onClose(window.id)}
                    onMinimize={() => onMinimize(window.id)}
                    onFocus={() => onFocus(window.id)}
                    onUpdate={(updates) => onUpdate(window.id, updates)}
                />
            ))}
        </>,
        document.body
    );
}

export type { WindowConfig as ERPWindow };
