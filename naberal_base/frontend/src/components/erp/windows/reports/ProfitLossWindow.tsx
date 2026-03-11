"use client";

import React, { useState } from "react";
import { Search, Printer, Download, PieChart } from "lucide-react";

interface ProfitLossItem {
    id: string;
    category: string;
    item: string;
    currentMonth: number;
    prevMonth: number;
    change: number;
    changeRate: number;
}

export function ProfitLossWindow() {
    const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));
    const [items] = useState<ProfitLossItem[]>([
        { id: "1", category: "매출", item: "상품매출", currentMonth: 85000000, prevMonth: 78000000, change: 7000000, changeRate: 9.0 },
        { id: "2", category: "매출", item: "서비스매출", currentMonth: 12000000, prevMonth: 10000000, change: 2000000, changeRate: 20.0 },
        { id: "3", category: "매출원가", item: "상품매입", currentMonth: 55000000, prevMonth: 50000000, change: 5000000, changeRate: 10.0 },
        { id: "4", category: "판관비", item: "인건비", currentMonth: 15000000, prevMonth: 15000000, change: 0, changeRate: 0 },
        { id: "5", category: "판관비", item: "임차료", currentMonth: 5000000, prevMonth: 5000000, change: 0, changeRate: 0 },
        { id: "6", category: "판관비", item: "기타경비", currentMonth: 3000000, prevMonth: 2500000, change: 500000, changeRate: 20.0 },
    ]);

    const totalRevenue = items.filter(i => i.category === "매출").reduce((sum, item) => sum + item.currentMonth, 0);
    const totalCost = items.filter(i => i.category === "매출원가").reduce((sum, item) => sum + item.currentMonth, 0);
    const totalExpense = items.filter(i => i.category === "판관비").reduce((sum, item) => sum + item.currentMonth, 0);
    const netProfit = totalRevenue - totalCost - totalExpense;

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"><Search className="h-4 w-4" />조회</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Printer className="h-4 w-4" />인쇄</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Download className="h-4 w-4" />엑셀</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><PieChart className="h-4 w-4" />차트</button>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    <div className="rounded-lg border border-teal-200 bg-teal-50 p-2 text-center text-sm text-teal-700">손익계산서 - 수익/비용 분석</div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <label className="text-sm font-medium">조회월</label>
                            <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} className="rounded border px-3 py-1.5 text-sm" />
                        </div>
                    </div>

                    <div className="grid grid-cols-4 gap-4">
                        <div className="rounded-lg bg-blue-50 p-3 text-center">
                            <div className="text-xs text-blue-600">총 매출</div>
                            <div className="text-lg font-bold text-blue-700">{totalRevenue.toLocaleString()}</div>
                        </div>
                        <div className="rounded-lg bg-orange-50 p-3 text-center">
                            <div className="text-xs text-orange-600">매출원가</div>
                            <div className="text-lg font-bold text-orange-700">{totalCost.toLocaleString()}</div>
                        </div>
                        <div className="rounded-lg bg-red-50 p-3 text-center">
                            <div className="text-xs text-red-600">판관비</div>
                            <div className="text-lg font-bold text-red-700">{totalExpense.toLocaleString()}</div>
                        </div>
                        <div className={`rounded-lg p-3 text-center ${netProfit >= 0 ? "bg-green-50" : "bg-red-50"}`}>
                            <div className={`text-xs ${netProfit >= 0 ? "text-green-600" : "text-red-600"}`}>순이익</div>
                            <div className={`text-lg font-bold ${netProfit >= 0 ? "text-green-700" : "text-red-700"}`}>{netProfit.toLocaleString()}</div>
                        </div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-24 px-2 py-2 text-left">구분</th>
                                    <th className="px-2 py-2 text-left">항목</th>
                                    <th className="w-28 px-2 py-2 text-right">당월</th>
                                    <th className="w-28 px-2 py-2 text-right">전월</th>
                                    <th className="w-24 px-2 py-2 text-right">증감</th>
                                    <th className="w-20 px-2 py-2 text-right">증감률</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item) => (
                                    <tr key={item.id} className="border-b hover:bg-surface-secondary">
                                        <td className="px-2 py-2">
                                            <span className={`rounded px-2 py-0.5 text-xs ${item.category === "매출" ? "bg-blue-100 text-blue-700" : item.category === "매출원가" ? "bg-orange-100 text-orange-700" : "bg-red-100 text-red-700"}`}>{item.category}</span>
                                        </td>
                                        <td className="px-2 py-2">{item.item}</td>
                                        <td className="px-2 py-2 text-right font-medium">{item.currentMonth.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right">{item.prevMonth.toLocaleString()}</td>
                                        <td className={`px-2 py-2 text-right ${item.change >= 0 ? "text-green-600" : "text-red-600"}`}>{item.change >= 0 ? "+" : ""}{item.change.toLocaleString()}</td>
                                        <td className={`px-2 py-2 text-right ${item.changeRate >= 0 ? "text-green-600" : "text-red-600"}`}>{item.changeRate >= 0 ? "+" : ""}{item.changeRate}%</td>
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
