"use client";

import React, { useState } from "react";
import { Search, Printer, Download, Clock } from "lucide-react";

interface Payable {
    id: string;
    supplierCode: string;
    supplierName: string;
    purchaseDate: string;
    dueDate: string;
    originalAmount: number;
    paidAmount: number;
    balance: number;
    daysRemaining: number;
}

export function PayableListWindow() {
    const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split("T")[0]);
    const [items] = useState<Payable[]>([
        { id: "1", supplierCode: "S001", supplierName: "(주)공급업체", purchaseDate: "2024-01-10", dueDate: "2024-02-10", originalAmount: 25000000, paidAmount: 15000000, balance: 10000000, daysRemaining: 25 },
        { id: "2", supplierCode: "S002", supplierName: "대한부품(주)", purchaseDate: "2024-01-05", dueDate: "2024-02-05", originalAmount: 12000000, paidAmount: 0, balance: 12000000, daysRemaining: 20 },
        { id: "3", supplierCode: "S003", supplierName: "삼성소재(주)", purchaseDate: "2023-12-25", dueDate: "2024-01-25", originalAmount: 8500000, paidAmount: 0, balance: 8500000, daysRemaining: -10 },
    ]);

    const totalBalance = items.reduce((sum, item) => sum + item.balance, 0);
    const urgentAmount = items.filter(i => i.daysRemaining <= 7).reduce((sum, item) => sum + item.balance, 0);

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"><Search className="h-4 w-4" />조회</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Printer className="h-4 w-4" />인쇄</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Download className="h-4 w-4" />엑셀</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary text-orange-600"><Clock className="h-4 w-4" />긴급</button>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    <div className="rounded-lg border border-orange-200 bg-orange-50 p-2 text-center text-sm text-orange-700">미지급금현황 - 공급업체별 미지급금 내역</div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <label className="text-sm font-medium">기준일자</label>
                            <input type="date" value={asOfDate} onChange={(e) => setAsOfDate(e.target.value)} className="rounded border px-3 py-1.5 text-sm" />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="rounded-lg bg-orange-50 p-4 text-center">
                            <div className="text-sm text-orange-600">총 미지급금</div>
                            <div className="text-2xl font-bold text-orange-700">{totalBalance.toLocaleString()} 원</div>
                        </div>
                        <div className="rounded-lg bg-red-50 p-4 text-center">
                            <div className="text-sm text-red-600">긴급 (7일 이내)</div>
                            <div className="text-2xl font-bold text-red-700">{urgentAmount.toLocaleString()} 원</div>
                        </div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-24 px-2 py-2 text-left">공급자코드</th>
                                    <th className="px-2 py-2 text-left">공급자명</th>
                                    <th className="w-24 px-2 py-2 text-left">매입일</th>
                                    <th className="w-24 px-2 py-2 text-left">지급일</th>
                                    <th className="w-28 px-2 py-2 text-right">원금액</th>
                                    <th className="w-28 px-2 py-2 text-right">지급액</th>
                                    <th className="w-28 px-2 py-2 text-right">잔액</th>
                                    <th className="w-20 px-2 py-2 text-right">잔여일</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item) => (
                                    <tr key={item.id} className={`border-b hover:bg-surface-secondary ${item.daysRemaining < 0 ? "bg-red-50" : item.daysRemaining <= 7 ? "bg-orange-50" : ""}`}>
                                        <td className="px-2 py-2 text-brand">{item.supplierCode}</td>
                                        <td className="px-2 py-2">{item.supplierName}</td>
                                        <td className="px-2 py-2">{item.purchaseDate}</td>
                                        <td className="px-2 py-2">{item.dueDate}</td>
                                        <td className="px-2 py-2 text-right">{item.originalAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right text-green-600">{item.paidAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right font-medium text-orange-600">{item.balance.toLocaleString()}</td>
                                        <td className={`px-2 py-2 text-right font-medium ${item.daysRemaining < 0 ? "text-red-600" : item.daysRemaining <= 7 ? "text-orange-600" : "text-green-600"}`}>
                                            {item.daysRemaining < 0 ? `${Math.abs(item.daysRemaining)}일 연체` : `${item.daysRemaining}일`}
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
