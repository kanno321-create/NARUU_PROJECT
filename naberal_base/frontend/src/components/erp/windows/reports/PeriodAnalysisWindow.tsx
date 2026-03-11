"use client";

import React, { useState } from "react";
import { Search, Printer, Download, TrendingUp } from "lucide-react";

interface PeriodData {
    id: string;
    period: string;
    salesAmount: number;
    purchaseAmount: number;
    grossProfit: number;
    expenseAmount: number;
    netProfit: number;
    profitRate: number;
}

export function PeriodAnalysisWindow() {
    const [year, setYear] = useState(new Date().getFullYear().toString());
    const [items] = useState<PeriodData[]>([
        { id: "1", period: "1월", salesAmount: 85000000, purchaseAmount: 55000000, grossProfit: 30000000, expenseAmount: 12000000, netProfit: 18000000, profitRate: 21.2 },
        { id: "2", period: "2월", salesAmount: 92000000, purchaseAmount: 58000000, grossProfit: 34000000, expenseAmount: 13000000, netProfit: 21000000, profitRate: 22.8 },
        { id: "3", period: "3월", salesAmount: 78000000, purchaseAmount: 52000000, grossProfit: 26000000, expenseAmount: 11000000, netProfit: 15000000, profitRate: 19.2 },
    ]);

    const totalSales = items.reduce((sum, item) => sum + item.salesAmount, 0);
    const totalProfit = items.reduce((sum, item) => sum + item.netProfit, 0);

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"><Search className="h-4 w-4" />조회</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Printer className="h-4 w-4" />인쇄</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Download className="h-4 w-4" />엑셀</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><TrendingUp className="h-4 w-4" />추세</button>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-2 text-center text-sm text-indigo-700">기간별분석 - 월별/분기별 손익 분석</div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <label className="text-sm font-medium">조회년도</label>
                            <select value={year} onChange={(e) => setYear(e.target.value)} className="rounded border px-3 py-1.5 text-sm">
                                <option value="2024">2024년</option>
                                <option value="2023">2023년</option>
                                <option value="2022">2022년</option>
                            </select>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="rounded-lg bg-indigo-50 p-4 text-center">
                            <div className="text-sm text-indigo-600">누적 매출</div>
                            <div className="text-2xl font-bold text-indigo-700">{totalSales.toLocaleString()} 원</div>
                        </div>
                        <div className="rounded-lg bg-green-50 p-4 text-center">
                            <div className="text-sm text-green-600">누적 순이익</div>
                            <div className="text-2xl font-bold text-green-700">{totalProfit.toLocaleString()} 원</div>
                        </div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-20 px-2 py-2 text-left">기간</th>
                                    <th className="w-28 px-2 py-2 text-right">매출액</th>
                                    <th className="w-28 px-2 py-2 text-right">매입액</th>
                                    <th className="w-28 px-2 py-2 text-right">매출총이익</th>
                                    <th className="w-28 px-2 py-2 text-right">판관비</th>
                                    <th className="w-28 px-2 py-2 text-right">순이익</th>
                                    <th className="w-20 px-2 py-2 text-right">이익률</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item) => (
                                    <tr key={item.id} className="border-b hover:bg-surface-secondary">
                                        <td className="px-2 py-2 font-medium">{item.period}</td>
                                        <td className="px-2 py-2 text-right">{item.salesAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right">{item.purchaseAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right">{item.grossProfit.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right text-red-600">{item.expenseAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right font-medium text-green-600">{item.netProfit.toLocaleString()}</td>
                                        <td className={`px-2 py-2 text-right ${item.profitRate >= 20 ? "text-green-600" : "text-orange-600"}`}>{item.profitRate}%</td>
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
