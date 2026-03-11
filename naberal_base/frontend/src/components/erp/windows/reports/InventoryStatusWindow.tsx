"use client";

import React, { useState } from "react";
import { Search, Printer, Download, Package } from "lucide-react";

interface InventoryItem {
    id: string;
    productCode: string;
    productName: string;
    category: string;
    currentQty: number;
    safetyQty: number;
    unitCost: number;
    totalValue: number;
    status: string;
}

export function InventoryStatusWindow() {
    const [searchText, setSearchText] = useState("");
    const [items] = useState<InventoryItem[]>([
        { id: "1", productCode: "P001", productName: "노트북 A형", category: "전자기기", currentQty: 45, safetyQty: 20, unitCost: 950000, totalValue: 42750000, status: "정상" },
        { id: "2", productCode: "P002", productName: "모니터 27인치", category: "전자기기", currentQty: 78, safetyQty: 30, unitCost: 280000, totalValue: 21840000, status: "정상" },
        { id: "3", productCode: "P003", productName: "키보드 무선", category: "주변기기", currentQty: 15, safetyQty: 50, unitCost: 65000, totalValue: 975000, status: "부족" },
        { id: "4", productCode: "P004", productName: "마우스 무선", category: "주변기기", currentQty: 0, safetyQty: 30, unitCost: 35000, totalValue: 0, status: "품절" },
    ]);

    const totalValue = items.reduce((sum, item) => sum + item.totalValue, 0);
    const lowStockCount = items.filter(i => i.status !== "정상").length;

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"><Search className="h-4 w-4" />조회</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Printer className="h-4 w-4" />인쇄</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Download className="h-4 w-4" />엑셀</button>
                <div className="ml-auto relative">
                    <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-subtle" />
                    <input type="text" value={searchText} onChange={(e) => setSearchText(e.target.value)} placeholder="상품 검색..." className="rounded border py-1.5 pl-8 pr-3 text-sm" />
                </div>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    <div className="rounded-lg border border-violet-200 bg-violet-50 p-2 text-center text-sm text-violet-700">
                        <Package className="inline h-4 w-4 mr-1" />재고현황 - 상품별 재고 및 재고금액
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="rounded-lg bg-violet-50 p-4 text-center">
                            <div className="text-sm text-violet-600">총 재고금액</div>
                            <div className="text-2xl font-bold text-violet-700">{totalValue.toLocaleString()} 원</div>
                        </div>
                        <div className="rounded-lg bg-orange-50 p-4 text-center">
                            <div className="text-sm text-orange-600">부족/품절 품목</div>
                            <div className="text-2xl font-bold text-orange-700">{lowStockCount} 건</div>
                        </div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-24 px-2 py-2 text-left">상품코드</th>
                                    <th className="px-2 py-2 text-left">상품명</th>
                                    <th className="w-24 px-2 py-2 text-left">카테고리</th>
                                    <th className="w-20 px-2 py-2 text-right">현재고</th>
                                    <th className="w-20 px-2 py-2 text-right">안전재고</th>
                                    <th className="w-24 px-2 py-2 text-right">단가</th>
                                    <th className="w-28 px-2 py-2 text-right">재고금액</th>
                                    <th className="w-16 px-2 py-2 text-center">상태</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item) => (
                                    <tr key={item.id} className={`border-b hover:bg-surface-secondary ${item.status === "품절" ? "bg-red-50" : item.status === "부족" ? "bg-orange-50" : ""}`}>
                                        <td className="px-2 py-2 text-brand">{item.productCode}</td>
                                        <td className="px-2 py-2">{item.productName}</td>
                                        <td className="px-2 py-2">{item.category}</td>
                                        <td className={`px-2 py-2 text-right font-medium ${item.currentQty < item.safetyQty ? "text-red-600" : ""}`}>{item.currentQty}</td>
                                        <td className="px-2 py-2 text-right text-text-subtle">{item.safetyQty}</td>
                                        <td className="px-2 py-2 text-right">{item.unitCost.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right font-medium">{item.totalValue.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-center">
                                            <span className={`rounded px-2 py-0.5 text-xs font-medium ${item.status === "정상" ? "bg-green-100 text-green-700" : item.status === "부족" ? "bg-orange-100 text-orange-700" : "bg-red-100 text-red-700"}`}>{item.status}</span>
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
