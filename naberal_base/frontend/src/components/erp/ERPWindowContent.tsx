"use client";

import React from "react";

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

// 환경설정 개별 윈도우 (9개)
import { BasicSettingsWindow } from "./windows/settings/BasicSettingsWindow";
import { FormSettingsWindow } from "./windows/settings/FormSettingsWindow";
import { SMSSettingsWindow } from "./windows/settings/SMSSettingsWindow";
import { PrintSettingsWindow } from "./windows/settings/PrintSettingsWindow";
import { BackupSettingsWindow } from "./windows/settings/BackupSettingsWindow";
import { BusinessSettingsWindow } from "./windows/settings/BusinessSettingsWindow";
import { EmailSettingsWindow } from "./windows/settings/EmailSettingsWindow";
import { FaxSettingsWindow } from "./windows/settings/FaxSettingsWindow";
import { TaxInvoiceSettingsWindow } from "./windows/settings/TaxInvoiceSettingsWindow";

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

import { UnissuedSalesList } from "./menus/issuance/UnissuedSalesList";
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

interface ERPWindowContentProps {
    type: string;
}

export default function ERPWindowContent({ type }: ERPWindowContentProps) {
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

        // 전표작성 (10개)
        case "sales-voucher":
        case "sales-slip":
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

        // 환경설정
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

        // 전자전송
        case "sms-send":
            return <SmsWindow />;
        case "fax-send":
            return <FaxWindow />;
        case "unissued-sales-list":
            return <UnissuedSalesList />;

        // 상단 툴바
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
        case "salary":
            return <PayrollWindow />;
        case "quotation":
        case "estimate-management":
            return <QuotationWindow />;

        default:
            return (
                <div className="flex h-full flex-col items-center justify-center p-8">
                    <p className="text-lg font-medium text-text-subtle">{type}</p>
                    <p className="mt-2 text-sm text-text-subtle">이 기능을 사용할 준비가 되었습니다.</p>
                </div>
            );
    }
}
