"use client";

import React, { useState } from "react";
import { Search, Printer, Download, BarChart3 } from "lucide-react";

interface CustomerSales {
    id: string;
    customerCode: string;
    customerName: string;
    salesCount: number;
    totalAmount: number;
    totalVat: number;
    grandTotal: number;
    receivable: number;
}

export function CustomerSalesWindow() {
    const [startDate, setStartDate] = useState(new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split("T")[0]);
    const [endDate, setEndDate] = useState(new Date().toISOString().split("T")[0]);
    const [items] = useState<CustomerSales[]>([
        { id: "1", customerCode: "C001", customerName: "(주)한국전자", salesCount: 15, totalAmount: 45000000, totalVat: 4500000, grandTotal: 49500000, receivable: 5500000 },
        { id: "2", customerCode: "C002", customerName: "삼성물산(주)", salesCount: 8, totalAmount: 28000000, totalVat: 2800000, grandTotal: 30800000, receivable: 0 },
        { id: "3", customerCode: "C003", customerName: "(주)대한상사", salesCount: 12, totalAmount: 18500000, totalVat: 1850000, grandTotal: 20350000, receivable: 3300000 },
    ]);

    const totalSales = items.reduce((sum, item) => sum + item.grandTotal, 0);
    const totalReceivable = items.reduce((sum, item) => sum + item.receivable, 0);

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"><Search className="h-4 w-4" />조회</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Printer className="h-4 w-4" />인쇄</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Download className="h-4 w-4" />엑셀</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><BarChart3 className="h-4 w-4" />차트</button>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    <div className="rounded-lg border border-green-200 bg-green-50 p-2 text-center text-sm text-green-700">거래처별매출현황 - 거래처별 매출 집계</div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <label className="text-sm font-medium">조회기간</label>
                            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="rounded border px-3 py-1.5 text-sm" />
                            <span>~</span>
                            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="rounded border px-3 py-1.5 text-sm" />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="rounded-lg bg-blue-50 p-4 text-center">
                            <div className="text-sm text-blue-600">총 매출액</div>
                            <div className="text-2xl font-bold text-blue-700">{totalSales.toLocaleString()} 원</div>
                        </div>
                        <div className="rounded-lg bg-red-50 p-4 text-center">
                            <div className="text-sm text-red-600">미수금 합계</div>
                            <div className="text-2xl font-bold text-red-700">{totalReceivable.toLocaleString()} 원</div>
                        </div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-24 px-2 py-2 text-left">거래처코드</th>
                                    <th className="px-2 py-2 text-left">거래처명</th>
                                    <th className="w-20 px-2 py-2 text-right">건수</th>
                                    <th className="w-28 px-2 py-2 text-right">공급가액</th>
                                    <th className="w-24 px-2 py-2 text-right">부가세</th>
                                    <th className="w-28 px-2 py-2 text-right">합계</th>
                                    <th className="w-28 px-2 py-2 text-right">미수금</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item) => (
                                    <tr key={item.id} className="border-b hover:bg-surface-secondary">
                                        <td className="px-2 py-2 text-brand">{item.customerCode}</td>
                                        <td className="px-2 py-2">{item.customerName}</td>
                                        <td className="px-2 py-2 text-right">{item.salesCount}</td>
                                        <td className="px-2 py-2 text-right">{item.totalAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right">{item.totalVat.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right font-medium">{item.grandTotal.toLocaleString()}</td>
                                        <td className={`px-2 py-2 text-right ${item.receivable > 0 ? "text-red-600 font-medium" : ""}`}>{item.receivable.toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
