"use client";

import React, { useState } from "react";
import { Search, Printer, Download, TrendingUp } from "lucide-react";

interface CustomerMargin {
    id: string;
    customerCode: string;
    customerName: string;
    salesAmount: number;
    costAmount: number;
    grossProfit: number;
    marginRate: number;
    rank: number;
}

export function CustomerMarginWindow() {
    const [startDate, setStartDate] = useState(new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split("T")[0]);
    const [endDate, setEndDate] = useState(new Date().toISOString().split("T")[0]);
    const [items] = useState<CustomerMargin[]>([
        { id: "1", customerCode: "C001", customerName: "(주)한국전자", salesAmount: 49500000, costAmount: 38000000, grossProfit: 11500000, marginRate: 23.2, rank: 1 },
        { id: "2", customerCode: "C002", customerName: "삼성물산(주)", salesAmount: 30800000, costAmount: 24000000, grossProfit: 6800000, marginRate: 22.1, rank: 2 },
        { id: "3", customerCode: "C003", customerName: "(주)대한상사", salesAmount: 20350000, costAmount: 16500000, grossProfit: 3850000, marginRate: 18.9, rank: 3 },
    ]);

    const totalProfit = items.reduce((sum, item) => sum + item.grossProfit, 0);
    const avgMargin = items.reduce((sum, item) => sum + item.marginRate, 0) / items.length;

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"><Search className="h-4 w-4" />조회</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Printer className="h-4 w-4" />인쇄</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Download className="h-4 w-4" />엑셀</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><TrendingUp className="h-4 w-4" />분석</button>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-2 text-center text-sm text-emerald-700">거래처별마진분석 - 거래처별 수익성 분석</div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <label className="text-sm font-medium">조회기간</label>
                            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="rounded border px-3 py-1.5 text-sm" />
                            <span>~</span>
                            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="rounded border px-3 py-1.5 text-sm" />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="rounded-lg bg-emerald-50 p-4 text-center">
                            <div className="text-sm text-emerald-600">총 마진</div>
                            <div className="text-2xl font-bold text-emerald-700">{totalProfit.toLocaleString()} 원</div>
                        </div>
                        <div className="rounded-lg bg-blue-50 p-4 text-center">
                            <div className="text-sm text-blue-600">평균 마진율</div>
                            <div className="text-2xl font-bold text-blue-700">{avgMargin.toFixed(1)}%</div>
                        </div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-12 px-2 py-2 text-center">순위</th>
                                    <th className="w-24 px-2 py-2 text-left">거래처코드</th>
                                    <th className="px-2 py-2 text-left">거래처명</th>
                                    <th className="w-28 px-2 py-2 text-right">매출액</th>
                                    <th className="w-28 px-2 py-2 text-right">원가</th>
                                    <th className="w-28 px-2 py-2 text-right">마진</th>
                                    <th className="w-20 px-2 py-2 text-right">마진율</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item) => (
                                    <tr key={item.id} className="border-b hover:bg-surface-secondary">
                                        <td className="px-2 py-2 text-center">
                                            <span className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${item.rank === 1 ? "bg-yellow-100 text-yellow-700" : item.rank === 2 ? "bg-gray-100 text-gray-700" : item.rank === 3 ? "bg-orange-100 text-orange-700" : "bg-surface"}`}>{item.rank}</span>
                                        </td>
                                        <td className="px-2 py-2 text-brand">{item.customerCode}</td>
                                        <td className="px-2 py-2">{item.customerName}</td>
                                        <td className="px-2 py-2 text-right">{item.salesAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right">{item.costAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right font-medium text-emerald-600">{item.grossProfit.toLocaleString()}</td>
                                        <td className={`px-2 py-2 text-right font-medium ${item.marginRate >= 20 ? "text-green-600" : "text-orange-600"}`}>{item.marginRate}%</td>
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
