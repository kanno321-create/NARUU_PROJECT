"use client";

import React, { useState } from "react";
import { Search, Printer, Download, BarChart3 } from "lucide-react";

interface MonthlyData {
    id: string;
    month: string;
    sales: number;
    purchase: number;
    profit: number;
}

export function MonthlyChartWindow() {
    const [year, setYear] = useState(new Date().getFullYear().toString());
    const [items] = useState<MonthlyData[]>([
        { id: "1", month: "1월", sales: 85000000, purchase: 55000000, profit: 30000000 },
        { id: "2", month: "2월", sales: 92000000, purchase: 58000000, profit: 34000000 },
        { id: "3", month: "3월", sales: 78000000, purchase: 52000000, profit: 26000000 },
        { id: "4", month: "4월", sales: 95000000, purchase: 60000000, profit: 35000000 },
        { id: "5", month: "5월", sales: 88000000, purchase: 56000000, profit: 32000000 },
        { id: "6", month: "6월", sales: 102000000, purchase: 65000000, profit: 37000000 },
    ]);

    const maxSales = Math.max(...items.map(i => i.sales));

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"><Search className="h-4 w-4" />조회</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Printer className="h-4 w-4" />인쇄</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Download className="h-4 w-4" />엑셀</button>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    <div className="rounded-lg border border-cyan-200 bg-cyan-50 p-2 text-center text-sm text-cyan-700">월별추이분석 - 매출/매입/손익 추이</div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <label className="text-sm font-medium">조회년도</label>
                            <select value={year} onChange={(e) => setYear(e.target.value)} className="rounded border px-3 py-1.5 text-sm">
                                <option value="2024">2024년</option>
                                <option value="2023">2023년</option>
                            </select>
                        </div>
                    </div>

                    <div className="rounded border p-4">
                        <div className="mb-4 flex items-center gap-4 text-sm">
                            <span className="flex items-center gap-1"><span className="h-3 w-3 rounded bg-blue-500"></span>매출</span>
                            <span className="flex items-center gap-1"><span className="h-3 w-3 rounded bg-orange-500"></span>매입</span>
                            <span className="flex items-center gap-1"><span className="h-3 w-3 rounded bg-green-500"></span>손익</span>
                        </div>
                        <div className="space-y-3">
                            {items.map((item) => (
                                <div key={item.id} className="space-y-1">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="w-12 font-medium">{item.month}</span>
                                        <span className="text-xs text-text-subtle">{item.sales.toLocaleString()}</span>
                                    </div>
                                    <div className="flex gap-1">
                                        <div className="h-4 rounded bg-blue-500" style={{ width: `${(item.sales / maxSales) * 100}%` }}></div>
                                    </div>
                                    <div className="flex gap-1">
                                        <div className="h-4 rounded bg-orange-500" style={{ width: `${(item.purchase / maxSales) * 100}%` }}></div>
                                    </div>
                                    <div className="flex gap-1">
                                        <div className="h-4 rounded bg-green-500" style={{ width: `${(item.profit / maxSales) * 100}%` }}></div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-20 px-2 py-2 text-left">월</th>
                                    <th className="w-28 px-2 py-2 text-right">매출</th>
                                    <th className="w-28 px-2 py-2 text-right">매입</th>
                                    <th className="w-28 px-2 py-2 text-right">손익</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item) => (
                                    <tr key={item.id} className="border-b hover:bg-surface-secondary">
                                        <td className="px-2 py-2 font-medium">{item.month}</td>
                                        <td className="px-2 py-2 text-right text-blue-600">{item.sales.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right text-orange-600">{item.purchase.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right font-medium text-green-600">{item.profit.toLocaleString()}</td>
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
