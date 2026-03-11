"use client";

import React, { useState } from "react";
import { Search, Printer, Download, Shield } from "lucide-react";

interface CreditInfo {
    id: string;
    customerCode: string;
    customerName: string;
    creditLimit: number;
    currentBalance: number;
    availableCredit: number;
    utilizationRate: number;
    creditGrade: string;
    paymentHistory: string;
}

export function CreditInfoWindow() {
    const [searchText, setSearchText] = useState("");
    const [items] = useState<CreditInfo[]>([
        { id: "1", customerCode: "C001", customerName: "(주)한국전자", creditLimit: 50000000, currentBalance: 5500000, availableCredit: 44500000, utilizationRate: 11.0, creditGrade: "A", paymentHistory: "양호" },
        { id: "2", customerCode: "C002", customerName: "삼성물산(주)", creditLimit: 100000000, currentBalance: 0, availableCredit: 100000000, utilizationRate: 0, creditGrade: "AA", paymentHistory: "우수" },
        { id: "3", customerCode: "C003", customerName: "(주)대한상사", creditLimit: 30000000, currentBalance: 3300000, availableCredit: 26700000, utilizationRate: 11.0, creditGrade: "B", paymentHistory: "보통" },
        { id: "4", customerCode: "C005", customerName: "동양산업(주)", creditLimit: 20000000, currentBalance: 18000000, availableCredit: 2000000, utilizationRate: 90.0, creditGrade: "C", paymentHistory: "주의" },
    ]);

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"><Search className="h-4 w-4" />조회</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Printer className="h-4 w-4" />인쇄</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Download className="h-4 w-4" />엑셀</button>
                <div className="ml-auto relative">
                    <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-subtle" />
                    <input type="text" value={searchText} onChange={(e) => setSearchText(e.target.value)} placeholder="거래처 검색..." className="rounded border py-1.5 pl-8 pr-3 text-sm" />
                </div>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-2 text-center text-sm text-slate-700">
                        <Shield className="inline h-4 w-4 mr-1" />여신정보관리 - 거래처별 신용한도 및 현황
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-24 px-2 py-2 text-left">거래처코드</th>
                                    <th className="px-2 py-2 text-left">거래처명</th>
                                    <th className="w-28 px-2 py-2 text-right">여신한도</th>
                                    <th className="w-28 px-2 py-2 text-right">미수잔액</th>
                                    <th className="w-28 px-2 py-2 text-right">가용한도</th>
                                    <th className="w-20 px-2 py-2 text-right">사용률</th>
                                    <th className="w-16 px-2 py-2 text-center">등급</th>
                                    <th className="w-20 px-2 py-2 text-center">결제이력</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item) => (
                                    <tr key={item.id} className={`border-b hover:bg-surface-secondary ${item.utilizationRate >= 80 ? "bg-red-50" : ""}`}>
                                        <td className="px-2 py-2 text-brand">{item.customerCode}</td>
                                        <td className="px-2 py-2">{item.customerName}</td>
                                        <td className="px-2 py-2 text-right">{item.creditLimit.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right text-blue-600">{item.currentBalance.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right font-medium text-green-600">{item.availableCredit.toLocaleString()}</td>
                                        <td className={`px-2 py-2 text-right ${item.utilizationRate >= 80 ? "text-red-600 font-bold" : item.utilizationRate >= 50 ? "text-orange-600" : "text-green-600"}`}>{item.utilizationRate}%</td>
                                        <td className="px-2 py-2 text-center">
                                            <span className={`rounded px-2 py-0.5 text-xs font-bold ${item.creditGrade === "AA" ? "bg-green-200 text-green-800" : item.creditGrade === "A" ? "bg-blue-200 text-blue-800" : item.creditGrade === "B" ? "bg-yellow-200 text-yellow-800" : "bg-red-200 text-red-800"}`}>{item.creditGrade}</span>
                                        </td>
                                        <td className="px-2 py-2 text-center">
                                            <span className={`rounded px-2 py-0.5 text-xs ${item.paymentHistory === "우수" ? "bg-green-100 text-green-700" : item.paymentHistory === "양호" ? "bg-blue-100 text-blue-700" : item.paymentHistory === "보통" ? "bg-yellow-100 text-yellow-700" : "bg-red-100 text-red-700"}`}>{item.paymentHistory}</span>
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
