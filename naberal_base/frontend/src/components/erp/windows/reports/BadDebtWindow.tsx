"use client";

import React, { useState } from "react";
import { Search, Printer, Download, AlertCircle } from "lucide-react";

interface BadDebt {
    id: string;
    customerCode: string;
    customerName: string;
    originalDate: string;
    originalAmount: number;
    collectedAmount: number;
    badDebtAmount: number;
    overdueDays: number;
    status: string;
}

export function BadDebtWindow() {
    const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split("T")[0]);
    const [items] = useState<BadDebt[]>([
        { id: "1", customerCode: "C010", customerName: "(주)부실기업", originalDate: "2023-06-15", originalAmount: 25000000, collectedAmount: 5000000, badDebtAmount: 20000000, overdueDays: 210, status: "부도" },
        { id: "2", customerCode: "C015", customerName: "신용불량(주)", originalDate: "2023-08-20", originalAmount: 12000000, collectedAmount: 2000000, badDebtAmount: 10000000, overdueDays: 150, status: "연체중" },
        { id: "3", customerCode: "C022", customerName: "한계기업(주)", originalDate: "2023-09-10", originalAmount: 8500000, collectedAmount: 0, badDebtAmount: 8500000, overdueDays: 120, status: "연체중" },
    ]);

    const totalBadDebt = items.reduce((sum, item) => sum + item.badDebtAmount, 0);

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"><Search className="h-4 w-4" />조회</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Printer className="h-4 w-4" />인쇄</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Download className="h-4 w-4" />엑셀</button>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    <div className="rounded-lg border border-red-200 bg-red-50 p-2 text-center text-sm text-red-700">
                        <AlertCircle className="inline h-4 w-4 mr-1" />불량채권현황 - 회수불능 채권 관리
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <label className="text-sm font-medium">기준일자</label>
                            <input type="date" value={asOfDate} onChange={(e) => setAsOfDate(e.target.value)} className="rounded border px-3 py-1.5 text-sm" />
                        </div>
                    </div>

                    <div className="rounded-lg bg-red-50 p-4 text-center">
                        <div className="text-sm text-red-600">불량채권 합계</div>
                        <div className="text-3xl font-bold text-red-700">{totalBadDebt.toLocaleString()} 원</div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-24 px-2 py-2 text-left">거래처코드</th>
                                    <th className="px-2 py-2 text-left">거래처명</th>
                                    <th className="w-24 px-2 py-2 text-left">발생일</th>
                                    <th className="w-28 px-2 py-2 text-right">원금액</th>
                                    <th className="w-28 px-2 py-2 text-right">회수액</th>
                                    <th className="w-28 px-2 py-2 text-right">불량액</th>
                                    <th className="w-20 px-2 py-2 text-right">연체일</th>
                                    <th className="w-20 px-2 py-2 text-center">상태</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item) => (
                                    <tr key={item.id} className="border-b bg-red-50 hover:bg-red-100">
                                        <td className="px-2 py-2 text-brand">{item.customerCode}</td>
                                        <td className="px-2 py-2">{item.customerName}</td>
                                        <td className="px-2 py-2">{item.originalDate}</td>
                                        <td className="px-2 py-2 text-right">{item.originalAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right text-green-600">{item.collectedAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right font-bold text-red-600">{item.badDebtAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right font-medium">{item.overdueDays}일</td>
                                        <td className="px-2 py-2 text-center">
                                            <span className={`rounded px-2 py-0.5 text-xs font-medium ${item.status === "부도" ? "bg-red-200 text-red-800" : "bg-orange-200 text-orange-800"}`}>{item.status}</span>
                                        </td>
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
