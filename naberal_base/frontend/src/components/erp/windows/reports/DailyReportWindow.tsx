"use client";

import React, { useState } from "react";
import { Search, Printer, Download, Calendar } from "lucide-react";

interface DailyReport {
    id: string;
    date: string;
    salesCount: number;
    salesAmount: number;
    purchaseCount: number;
    purchaseAmount: number;
    collectionAmount: number;
    paymentAmount: number;
    profit: number;
}

export function DailyReportWindow() {
    const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));
    const [items] = useState<DailyReport[]>([
        { id: "1", date: "2024-01-15", salesCount: 5, salesAmount: 12000000, purchaseCount: 3, purchaseAmount: 8000000, collectionAmount: 10000000, paymentAmount: 5000000, profit: 4000000 },
        { id: "2", date: "2024-01-16", salesCount: 8, salesAmount: 18500000, purchaseCount: 2, purchaseAmount: 6500000, collectionAmount: 15000000, paymentAmount: 4000000, profit: 12000000 },
        { id: "3", date: "2024-01-17", salesCount: 3, salesAmount: 7200000, purchaseCount: 4, purchaseAmount: 9800000, collectionAmount: 5000000, paymentAmount: 8000000, profit: -2600000 },
    ]);

    const totalSales = items.reduce((sum, item) => sum + item.salesAmount, 0);
    const totalPurchase = items.reduce((sum, item) => sum + item.purchaseAmount, 0);
    const totalProfit = items.reduce((sum, item) => sum + item.profit, 0);

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"><Search className="h-4 w-4" />조회</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Printer className="h-4 w-4" />인쇄</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Download className="h-4 w-4" />엑셀</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Calendar className="h-4 w-4" />월력</button>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-2 text-center text-sm text-yellow-700">일일업무현황 - 일자별 매출/매입/수금/지급 현황</div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <label className="text-sm font-medium">조회월</label>
                            <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} className="rounded border px-3 py-1.5 text-sm" />
                        </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                        <div className="rounded-lg bg-blue-50 p-4 text-center">
                            <div className="text-sm text-blue-600">총 매출액</div>
                            <div className="text-xl font-bold text-blue-700">{totalSales.toLocaleString()}</div>
                        </div>
                        <div className="rounded-lg bg-orange-50 p-4 text-center">
                            <div className="text-sm text-orange-600">총 매입액</div>
                            <div className="text-xl font-bold text-orange-700">{totalPurchase.toLocaleString()}</div>
                        </div>
                        <div className={`rounded-lg p-4 text-center ${totalProfit >= 0 ? "bg-green-50" : "bg-red-50"}`}>
                            <div className={`text-sm ${totalProfit >= 0 ? "text-green-600" : "text-red-600"}`}>총 이익</div>
                            <div className={`text-xl font-bold ${totalProfit >= 0 ? "text-green-700" : "text-red-700"}`}>{totalProfit.toLocaleString()}</div>
                        </div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-24 px-2 py-2 text-left">일자</th>
                                    <th className="w-16 px-2 py-2 text-right">매출건</th>
                                    <th className="w-28 px-2 py-2 text-right">매출액</th>
                                    <th className="w-16 px-2 py-2 text-right">매입건</th>
                                    <th className="w-28 px-2 py-2 text-right">매입액</th>
                                    <th className="w-28 px-2 py-2 text-right">수금액</th>
                                    <th className="w-28 px-2 py-2 text-right">지급액</th>
                                    <th className="w-28 px-2 py-2 text-right">손익</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item) => (
                                    <tr key={item.id} className="border-b hover:bg-surface-secondary">
                                        <td className="px-2 py-2">{item.date}</td>
                                        <td className="px-2 py-2 text-right">{item.salesCount}</td>
                                        <td className="px-2 py-2 text-right text-blue-600">{item.salesAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right">{item.purchaseCount}</td>
                                        <td className="px-2 py-2 text-right text-orange-600">{item.purchaseAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right">{item.collectionAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right">{item.paymentAmount.toLocaleString()}</td>
                                        <td className={`px-2 py-2 text-right font-medium ${item.profit >= 0 ? "text-green-600" : "text-red-600"}`}>{item.profit.toLocaleString()}</td>
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
