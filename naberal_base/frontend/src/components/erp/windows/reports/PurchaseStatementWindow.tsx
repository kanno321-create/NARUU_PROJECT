"use client";

import React, { useState } from "react";
import { Search, Printer, Download, FileText } from "lucide-react";

interface PurchaseItem {
    id: string;
    date: string;
    slipNo: string;
    supplierName: string;
    productName: string;
    quantity: number;
    unitPrice: number;
    amount: number;
    vat: number;
    total: number;
}

export function PurchaseStatementWindow() {
    const [startDate, setStartDate] = useState(new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split("T")[0]);
    const [endDate, setEndDate] = useState(new Date().toISOString().split("T")[0]);
    const [searchText, setSearchText] = useState("");
    const [items] = useState<PurchaseItem[]>([
        { id: "1", date: "2024-01-12", slipNo: "P-20240112-001", supplierName: "(주)공급업체", productName: "원자재 A", quantity: 100, unitPrice: 50000, amount: 5000000, vat: 500000, total: 5500000 },
        { id: "2", date: "2024-01-14", slipNo: "P-20240114-001", supplierName: "대한부품(주)", productName: "부품 B형", quantity: 50, unitPrice: 120000, amount: 6000000, vat: 600000, total: 6600000 },
        { id: "3", date: "2024-01-16", slipNo: "P-20240116-001", supplierName: "삼성소재(주)", productName: "소재 C", quantity: 200, unitPrice: 25000, amount: 5000000, vat: 500000, total: 5500000 },
    ]);

    const totalAmount = items.reduce((sum, item) => sum + item.amount, 0);
    const totalVat = items.reduce((sum, item) => sum + item.vat, 0);
    const grandTotal = items.reduce((sum, item) => sum + item.total, 0);

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"><Search className="h-4 w-4" />조회</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Printer className="h-4 w-4" />인쇄</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Download className="h-4 w-4" />엑셀</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><FileText className="h-4 w-4" />PDF</button>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    <div className="rounded-lg border border-orange-200 bg-orange-50 p-2 text-center text-sm text-orange-700">매입명세서 - 기간별 매입 상세 내역</div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <label className="text-sm font-medium">조회기간</label>
                            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="rounded border px-3 py-1.5 text-sm" />
                            <span>~</span>
                            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="rounded border px-3 py-1.5 text-sm" />
                        </div>
                        <div className="relative flex-1">
                            <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-subtle" />
                            <input type="text" value={searchText} onChange={(e) => setSearchText(e.target.value)} placeholder="공급자/상품 검색..." className="w-full rounded border py-1.5 pl-8 pr-3 text-sm" />
                        </div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-24 px-2 py-2 text-left">일자</th>
                                    <th className="w-32 px-2 py-2 text-left">전표번호</th>
                                    <th className="px-2 py-2 text-left">공급자명</th>
                                    <th className="px-2 py-2 text-left">상품명</th>
                                    <th className="w-16 px-2 py-2 text-right">수량</th>
                                    <th className="w-24 px-2 py-2 text-right">단가</th>
                                    <th className="w-28 px-2 py-2 text-right">공급가액</th>
                                    <th className="w-24 px-2 py-2 text-right">부가세</th>
                                    <th className="w-28 px-2 py-2 text-right">합계</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item) => (
                                    <tr key={item.id} className="border-b hover:bg-surface-secondary">
                                        <td className="px-2 py-2">{item.date}</td>
                                        <td className="px-2 py-2 text-brand">{item.slipNo}</td>
                                        <td className="px-2 py-2">{item.supplierName}</td>
                                        <td className="px-2 py-2">{item.productName}</td>
                                        <td className="px-2 py-2 text-right">{item.quantity}</td>
                                        <td className="px-2 py-2 text-right">{item.unitPrice.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right">{item.amount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right">{item.vat.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right font-medium">{item.total.toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                            <tfoot className="bg-surface-secondary">
                                <tr>
                                    <td colSpan={6} className="px-2 py-2 text-right font-medium">합계</td>
                                    <td className="px-2 py-2 text-right font-bold">{totalAmount.toLocaleString()}</td>
                                    <td className="px-2 py-2 text-right font-bold">{totalVat.toLocaleString()}</td>
                                    <td className="px-2 py-2 text-right font-bold text-orange-600">{grandTotal.toLocaleString()}</td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
