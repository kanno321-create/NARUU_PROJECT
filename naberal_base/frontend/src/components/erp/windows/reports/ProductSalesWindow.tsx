"use client";

import React, { useState } from "react";
import { Search, Printer, Download, BarChart3 } from "lucide-react";

interface ProductSales {
    id: string;
    productCode: string;
    productName: string;
    category: string;
    salesQty: number;
    totalAmount: number;
    avgPrice: number;
    profitRate: number;
}

export function ProductSalesWindow() {
    const [startDate, setStartDate] = useState(new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split("T")[0]);
    const [endDate, setEndDate] = useState(new Date().toISOString().split("T")[0]);
    const [items] = useState<ProductSales[]>([
        { id: "1", productCode: "P001", productName: "노트북 A형", category: "전자기기", salesQty: 45, totalAmount: 54000000, avgPrice: 1200000, profitRate: 15.5 },
        { id: "2", productCode: "P002", productName: "모니터 27인치", category: "전자기기", salesQty: 78, totalAmount: 27300000, avgPrice: 350000, profitRate: 12.3 },
        { id: "3", productCode: "P003", productName: "키보드 무선", category: "주변기기", salesQty: 156, totalAmount: 13260000, avgPrice: 85000, profitRate: 18.7 },
    ]);

    const totalQty = items.reduce((sum, item) => sum + item.salesQty, 0);
    const totalAmount = items.reduce((sum, item) => sum + item.totalAmount, 0);

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
                    <div className="rounded-lg border border-purple-200 bg-purple-50 p-2 text-center text-sm text-purple-700">상품별매출현황 - 상품별 매출 집계</div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <label className="text-sm font-medium">조회기간</label>
                            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="rounded border px-3 py-1.5 text-sm" />
                            <span>~</span>
                            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="rounded border px-3 py-1.5 text-sm" />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="rounded-lg bg-purple-50 p-4 text-center">
                            <div className="text-sm text-purple-600">총 판매수량</div>
                            <div className="text-2xl font-bold text-purple-700">{totalQty.toLocaleString()} 개</div>
                        </div>
                        <div className="rounded-lg bg-blue-50 p-4 text-center">
                            <div className="text-sm text-blue-600">총 매출액</div>
                            <div className="text-2xl font-bold text-blue-700">{totalAmount.toLocaleString()} 원</div>
                        </div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-24 px-2 py-2 text-left">상품코드</th>
                                    <th className="px-2 py-2 text-left">상품명</th>
                                    <th className="w-24 px-2 py-2 text-left">카테고리</th>
                                    <th className="w-20 px-2 py-2 text-right">판매수량</th>
                                    <th className="w-28 px-2 py-2 text-right">매출액</th>
                                    <th className="w-24 px-2 py-2 text-right">평균단가</th>
                                    <th className="w-20 px-2 py-2 text-right">이익률</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item) => (
                                    <tr key={item.id} className="border-b hover:bg-surface-secondary">
                                        <td className="px-2 py-2 text-brand">{item.productCode}</td>
                                        <td className="px-2 py-2">{item.productName}</td>
                                        <td className="px-2 py-2">{item.category}</td>
                                        <td className="px-2 py-2 text-right">{item.salesQty}</td>
                                        <td className="px-2 py-2 text-right font-medium">{item.totalAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right">{item.avgPrice.toLocaleString()}</td>
                                        <td className={`px-2 py-2 text-right ${item.profitRate >= 15 ? "text-green-600" : "text-orange-600"}`}>{item.profitRate}%</td>
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
