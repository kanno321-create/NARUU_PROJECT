"use client";

import React, { useState, useCallback, useEffect } from "react";
import { Search, Printer, Download, AlertTriangle, X } from "lucide-react";
import { api, type ERPSale } from "@/lib/api";

interface Receivable {
    id: string;
    customerCode: string;
    customerName: string;
    customerId: string;
    salesDate: string;
    dueDate: string;
    originalAmount: number;
    paidAmount: number;
    balance: number;
    overdueDays: number;
}

interface LedgerEntry {
    date: string;
    voucherNumber: string;
    amount: number;
    collectedAmount: number;
    balance: number;
}

export function ReceivableListWindow() {
    const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split("T")[0]);
    const [items, setItems] = useState<Receivable[]>([]);
    const [showOverdueOnly, setShowOverdueOnly] = useState(false);
    const [loading, setLoading] = useState(false);

    // Customer detail modal state
    const [selectedCustomer, setSelectedCustomer] = useState<Receivable | null>(null);
    const [ledgerEntries, setLedgerEntries] = useState<LedgerEntry[]>([]);
    const [ledgerLoading, setLedgerLoading] = useState(false);

    const displayItems = showOverdueOnly ? items.filter(i => i.overdueDays > 0) : items;
    const totalBalance = displayItems.reduce((sum, item) => sum + item.balance, 0);
    const overdueAmount = displayItems.filter(i => i.overdueDays > 0).reduce((sum, item) => sum + item.balance, 0);

    // Fetch receivable data from API
    const handleSearch = useCallback(async () => {
        setLoading(true);
        try {
            const salesData = await api.erp.sales.list({
                end_date: asOfDate,
                limit: 100,
            });
            if (salesData.items && salesData.items.length > 0) {
                const receivableMap = new Map<string, Receivable>();
                const today = new Date(asOfDate);

                for (const sale of salesData.items) {
                    const customerId = sale.customer_id;
                    const customerName = sale.customer?.name || "미지정";
                    const customerCode = sale.customer?.code || "-";
                    const saleDate = sale.sale_date;
                    // Due date defaults to 30 days after sale
                    const dueDateObj = new Date(saleDate);
                    dueDateObj.setDate(dueDateObj.getDate() + 30);
                    const dueDate = dueDateObj.toISOString().split("T")[0];
                    const balance = sale.total_amount - (sale.cost_amount || 0);

                    if (balance > 0) {
                        const overdueDays = Math.max(0, Math.floor((today.getTime() - dueDateObj.getTime()) / (1000 * 60 * 60 * 24)));
                        const existing = receivableMap.get(customerId);
                        if (existing) {
                            existing.originalAmount += sale.total_amount;
                            existing.paidAmount += sale.cost_amount || 0;
                            existing.balance += balance;
                            existing.overdueDays = Math.max(existing.overdueDays, overdueDays);
                        } else {
                            receivableMap.set(customerId, {
                                id: customerId,
                                customerCode,
                                customerName,
                                customerId,
                                salesDate: saleDate,
                                dueDate,
                                originalAmount: sale.total_amount,
                                paidAmount: sale.cost_amount || 0,
                                balance,
                                overdueDays,
                            });
                        }
                    }
                }

                const result = Array.from(receivableMap.values());
                if (result.length > 0) {
                    setItems(result);
                }
            }
        } catch (error) {
            console.error("Failed to fetch receivable data:", error);
        } finally {
            setLoading(false);
        }
    }, [asOfDate]);

    // Load on mount
    useEffect(() => {
        handleSearch();
    }, [handleSearch]);

    // Double-click handler: show customer sales ledger modal
    const handleCustomerDetail = async (item: Receivable) => {
        setSelectedCustomer(item);
        setLedgerLoading(true);
        try {
            const salesData = await api.erp.sales.list({
                customer_id: item.customerId,
                limit: 50,
            });
            if (salesData.items) {
                let runningBalance = 0;
                const entries: LedgerEntry[] = salesData.items.map((sale: ERPSale) => {
                    runningBalance += sale.total_amount - (sale.cost_amount || 0);
                    return {
                        date: sale.sale_date,
                        voucherNumber: sale.sale_number,
                        amount: sale.total_amount,
                        collectedAmount: sale.cost_amount || 0,
                        balance: runningBalance,
                    };
                });
                setLedgerEntries(entries);
            }
        } catch (error) {
            console.error("Failed to fetch ledger:", error);
            // Show fallback data derived from selected item
            setLedgerEntries([{
                date: item.salesDate,
                voucherNumber: "-",
                amount: item.originalAmount,
                collectedAmount: item.paidAmount,
                balance: item.balance,
            }]);
        } finally {
            setLedgerLoading(false);
        }
    };

    // Print handler
    const handlePrint = () => {
        window.print();
    };

    // Excel/CSV download handler
    const handleExcelDownload = () => {
        const header = "거래처코드,거래처명,매출일,만기일,원금액,수금액,잔액,연체일";
        const csvContent = displayItems.map(i =>
            `${i.customerCode},${i.customerName},${i.salesDate},${i.dueDate},${i.originalAmount},${i.paidAmount},${i.balance},${i.overdueDays}`
        ).join('\n');

        const blob = new Blob(['\uFEFF' + header + '\n' + csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `미수금현황_${asOfDate}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    // Toggle overdue filter
    const handleToggleOverdue = () => {
        setShowOverdueOnly(!showOverdueOnly);
    };

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button
                    onClick={handleSearch}
                    disabled={loading}
                    className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark disabled:opacity-50"
                >
                    <Search className="h-4 w-4" />{loading ? "조회중..." : "조회"}
                </button>
                <button
                    onClick={handlePrint}
                    className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"
                >
                    <Printer className="h-4 w-4" />인쇄
                </button>
                <button
                    onClick={handleExcelDownload}
                    className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"
                >
                    <Download className="h-4 w-4" />엑셀
                </button>
                <button
                    onClick={handleToggleOverdue}
                    className={`flex items-center gap-1 rounded border px-3 py-1.5 text-sm ${showOverdueOnly ? "bg-orange-100 border-orange-400 text-orange-700" : "hover:bg-surface-secondary text-orange-600"}`}
                >
                    <AlertTriangle className="h-4 w-4" />연체{showOverdueOnly ? " (필터 ON)" : ""}
                </button>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    <div className="rounded-lg border border-blue-200 bg-blue-50 p-2 text-center text-sm text-blue-700">
                        미수금현황 - 거래처별 미수금 내역 {showOverdueOnly && "(연체 건만 표시)"}
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <label className="text-sm font-medium">기준일자</label>
                            <input type="date" value={asOfDate} onChange={(e) => setAsOfDate(e.target.value)} className="rounded border px-3 py-1.5 text-sm" />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="rounded-lg bg-blue-50 p-4 text-center">
                            <div className="text-sm text-blue-600">총 미수금</div>
                            <div className="text-2xl font-bold text-blue-700">{totalBalance.toLocaleString()} 원</div>
                        </div>
                        <div className="rounded-lg bg-red-50 p-4 text-center">
                            <div className="text-sm text-red-600">연체금액</div>
                            <div className="text-2xl font-bold text-red-700">{overdueAmount.toLocaleString()} 원</div>
                        </div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-24 px-2 py-2 text-left">거래처코드</th>
                                    <th className="px-2 py-2 text-left">거래처명</th>
                                    <th className="w-24 px-2 py-2 text-left">매출일</th>
                                    <th className="w-24 px-2 py-2 text-left">만기일</th>
                                    <th className="w-28 px-2 py-2 text-right">원금액</th>
                                    <th className="w-28 px-2 py-2 text-right">수금액</th>
                                    <th className="w-28 px-2 py-2 text-right">잔액</th>
                                    <th className="w-20 px-2 py-2 text-right">연체일</th>
                                </tr>
                            </thead>
                            <tbody>
                                {displayItems.map((item) => (
                                    <tr
                                        key={item.id}
                                        className={`border-b hover:bg-surface-secondary cursor-pointer select-none ${item.overdueDays > 30 ? "bg-red-50" : ""}`}
                                        onDoubleClick={() => handleCustomerDetail(item)}
                                        title="더블클릭하여 매출원장 보기"
                                    >
                                        <td className="px-2 py-2 text-brand">{item.customerCode}</td>
                                        <td className="px-2 py-2">{item.customerName}</td>
                                        <td className="px-2 py-2">{item.salesDate}</td>
                                        <td className="px-2 py-2">{item.dueDate}</td>
                                        <td className="px-2 py-2 text-right">{item.originalAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right text-green-600">{item.paidAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right font-medium text-blue-600">{item.balance.toLocaleString()}</td>
                                        <td className={`px-2 py-2 text-right ${item.overdueDays > 30 ? "text-red-600 font-bold" : item.overdueDays > 0 ? "text-orange-600" : ""}`}>
                                            {item.overdueDays > 0 ? `${item.overdueDays}일` : "-"}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* Customer Sales Ledger Modal */}
            {selectedCustomer && (
                <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/50">
                    <div className="w-[600px] max-h-[80%] rounded-lg border border-surface-tertiary bg-surface shadow-xl flex flex-col">
                        <div className="flex items-center justify-between border-b bg-brand px-4 py-2">
                            <span className="font-medium text-white">
                                매출원장 - {selectedCustomer.customerName}
                            </span>
                            <button
                                onClick={() => setSelectedCustomer(null)}
                                className="rounded p-1 text-white hover:bg-white/20"
                            >
                                <X className="h-4 w-4" />
                            </button>
                        </div>
                        <div className="flex-1 overflow-auto p-4">
                            <div className="mb-4 grid grid-cols-3 gap-3 text-sm">
                                <div className="rounded bg-surface-secondary p-2">
                                    <div className="text-text-subtle">거래처코드</div>
                                    <div className="font-medium">{selectedCustomer.customerCode}</div>
                                </div>
                                <div className="rounded bg-surface-secondary p-2">
                                    <div className="text-text-subtle">총 미수금</div>
                                    <div className="font-medium text-blue-600">{selectedCustomer.balance.toLocaleString()} 원</div>
                                </div>
                                <div className="rounded bg-surface-secondary p-2">
                                    <div className="text-text-subtle">연체일</div>
                                    <div className={`font-medium ${selectedCustomer.overdueDays > 0 ? "text-red-600" : ""}`}>
                                        {selectedCustomer.overdueDays > 0 ? `${selectedCustomer.overdueDays}일` : "-"}
                                    </div>
                                </div>
                            </div>

                            {ledgerLoading ? (
                                <div className="flex items-center justify-center py-8">
                                    <div className="text-sm text-text-subtle">조회 중...</div>
                                </div>
                            ) : (
                                <div className="rounded border">
                                    <table className="w-full text-sm">
                                        <thead className="bg-surface-secondary">
                                            <tr className="border-b">
                                                <th className="px-3 py-2 text-left">날짜</th>
                                                <th className="px-3 py-2 text-left">전표번호</th>
                                                <th className="px-3 py-2 text-right">금액</th>
                                                <th className="px-3 py-2 text-right">수금액</th>
                                                <th className="px-3 py-2 text-right">잔액</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {ledgerEntries.map((entry, idx) => (
                                                <tr key={idx} className="border-b hover:bg-surface-secondary">
                                                    <td className="px-3 py-2">{entry.date}</td>
                                                    <td className="px-3 py-2 text-brand">{entry.voucherNumber}</td>
                                                    <td className="px-3 py-2 text-right">{entry.amount.toLocaleString()}</td>
                                                    <td className="px-3 py-2 text-right text-green-600">{entry.collectedAmount.toLocaleString()}</td>
                                                    <td className="px-3 py-2 text-right font-medium text-blue-600">{entry.balance.toLocaleString()}</td>
                                                </tr>
                                            ))}
                                            {ledgerEntries.length === 0 && (
                                                <tr>
                                                    <td colSpan={5} className="px-3 py-4 text-center text-text-subtle">
                                                        매출 기록이 없습니다.
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                        <div className="flex justify-end border-t px-4 py-3">
                            <button
                                onClick={() => setSelectedCustomer(null)}
                                className="rounded border px-4 py-1.5 text-sm hover:bg-surface-secondary"
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
