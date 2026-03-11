"use client";

import React, { useState } from "react";
import { Search, Printer, Download, BarChart3 } from "lucide-react";

interface SupplierPurchase {
    id: string;
    supplierCode: string;
    supplierName: string;
    purchaseCount: number;
    totalAmount: number;
    totalVat: number;
    grandTotal: number;
    payable: number;
}

export function SupplierPurchaseWindow() {
    const [startDate, setStartDate] = useState(new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split("T")[0]);
    const [endDate, setEndDate] = useState(new Date().toISOString().split("T")[0]);
    const [items] = useState<SupplierPurchase[]>([
        { id: "1", supplierCode: "S001", supplierName: "(주)공급업체", purchaseCount: 12, totalAmount: 35000000, totalVat: 3500000, grandTotal: 38500000, payable: 10000000 },
        { id: "2", supplierCode: "S002", supplierName: "대한부품(주)", purchaseCount: 8, totalAmount: 22000000, totalVat: 2200000, grandTotal: 24200000, payable: 12000000 },
        { id: "3", supplierCode: "S003", supplierName: "삼성소재(주)", purchaseCount: 15, totalAmount: 18500000, totalVat: 1850000, grandTotal: 20350000, payable: 8500000 },
    ]);

    const totalPurchase = items.reduce((sum, item) => sum + item.grandTotal, 0);
    const totalPayable = items.reduce((sum, item) => sum + item.payable, 0);

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
                    <div className="rounded-lg border border-amber-200 bg-amber-50 p-2 text-center text-sm text-amber-700">공급자별매입현황 - 공급자별 매입 집계</div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <label className="text-sm font-medium">조회기간</label>
                            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="rounded border px-3 py-1.5 text-sm" />
                            <span>~</span>
                            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="rounded border px-3 py-1.5 text-sm" />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="rounded-lg bg-amber-50 p-4 text-center">
                            <div className="text-sm text-amber-600">총 매입액</div>
                            <div className="text-2xl font-bold text-amber-700">{totalPurchase.toLocaleString()} 원</div>
                        </div>
                        <div className="rounded-lg bg-orange-50 p-4 text-center">
                            <div className="text-sm text-orange-600">미지급금 합계</div>
                            <div className="text-2xl font-bold text-orange-700">{totalPayable.toLocaleString()} 원</div>
                        </div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-24 px-2 py-2 text-left">공급자코드</th>
                                    <th className="px-2 py-2 text-left">공급자명</th>
                                    <th className="w-20 px-2 py-2 text-right">건수</th>
                                    <th className="w-28 px-2 py-2 text-right">공급가액</th>
                                    <th className="w-24 px-2 py-2 text-right">부가세</th>
                                    <th className="w-28 px-2 py-2 text-right">합계</th>
                                    <th className="w-28 px-2 py-2 text-right">미지급금</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item) => (
                                    <tr key={item.id} className="border-b hover:bg-surface-secondary">
                                        <td className="px-2 py-2 text-brand">{item.supplierCode}</td>
                                        <td className="px-2 py-2">{item.supplierName}</td>
                                        <td className="px-2 py-2 text-right">{item.purchaseCount}</td>
                                        <td className="px-2 py-2 text-right">{item.totalAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right">{item.totalVat.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right font-medium">{item.grandTotal.toLocaleString()}</td>
                                        <td className={`px-2 py-2 text-right ${item.payable > 0 ? "text-orange-600 font-medium" : ""}`}>{item.payable.toLocaleString()}</td>
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
