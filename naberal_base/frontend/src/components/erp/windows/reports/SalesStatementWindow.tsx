"use client";

import React, { useState, useMemo } from "react";
import { Search, Printer, FileText, Download, RefreshCw } from "lucide-react";
import { useERPData } from "@/contexts/ERPDataContext";

interface SalesItem {
    id: string;
    date: string;
    slipNo: string;
    customerName: string;
    productName: string;
    quantity: number;
    unitPrice: number;
    amount: number;
    vat: number;
    total: number;
}

export function SalesStatementWindow() {
    const { sales, salesLoading, fetchSales, customers, products } = useERPData();

    const [startDate, setStartDate] = useState(new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split("T")[0]);
    const [endDate, setEndDate] = useState(new Date().toISOString().split("T")[0]);
    const [searchText, setSearchText] = useState("");

    // sales 데이터를 SalesItem 형식으로 변환
    const salesItems = useMemo(() => {
        const items: SalesItem[] = [];

        (Array.isArray(sales) ? sales : []).forEach((sale) => {
            // 고객 정보 찾기
            const customer = customers.find(c => c.id === sale.customer_id);
            const customerName = customer?.name || sale.customer_id || "알 수 없음";

            (Array.isArray(sale.items) ? sale.items : []).forEach((item, idx) => {
                // 상품 정보 찾기
                const product = products.find(p => p.id === item.product_id);
                const productName = product?.name || item.product_id || "알 수 없음";

                items.push({
                    id: `${sale.id}-${idx}`,
                    date: sale.slip_date,
                    slipNo: sale.id.substring(0, 8).toUpperCase(),
                    customerName,
                    productName,
                    quantity: item.quantity,
                    unitPrice: item.unit_price,
                    amount: item.quantity * item.unit_price,
                    vat: Math.round(item.quantity * item.unit_price * 0.1),
                    total: Math.round(item.quantity * item.unit_price * 1.1),
                });
            });
        });

        return items;
    }, [sales, customers, products]);

    // 필터링된 데이터
    const filteredItems = useMemo(() => {
        return salesItems.filter((item) => {
            // 날짜 필터
            const itemDate = new Date(item.date);
            const start = new Date(startDate);
            const end = new Date(endDate);
            end.setHours(23, 59, 59, 999);

            if (itemDate < start || itemDate > end) {
                return false;
            }

            // 검색 필터
            if (searchText) {
                const search = searchText.toLowerCase();
                return (
                    item.customerName.toLowerCase().includes(search) ||
                    item.productName.toLowerCase().includes(search) ||
                    item.slipNo.toLowerCase().includes(search)
                );
            }

            return true;
        });
    }, [salesItems, startDate, endDate, searchText]);

    const totalAmount = filteredItems.reduce((sum, item) => sum + item.amount, 0);
    const totalVat = filteredItems.reduce((sum, item) => sum + item.vat, 0);
    const grandTotal = filteredItems.reduce((sum, item) => sum + item.total, 0);

    const handleRefresh = async () => {
        await fetchSales();
    };

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button
                    onClick={handleRefresh}
                    disabled={salesLoading}
                    className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark disabled:opacity-50"
                >
                    <RefreshCw className={`h-4 w-4 ${salesLoading ? "animate-spin" : ""}`} />
                    {salesLoading ? "조회중..." : "조회"}
                </button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Printer className="h-4 w-4" />인쇄</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Download className="h-4 w-4" />엑셀</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><FileText className="h-4 w-4" />PDF</button>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    <div className="rounded-lg border border-blue-200 bg-blue-50 p-2 text-center text-sm text-blue-700">
                        매출명세서 - 기간별 매출 상세 내역 (총 {filteredItems.length}건)
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <label className="text-sm font-medium">조회기간</label>
                            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="rounded border px-3 py-1.5 text-sm" />
                            <span>~</span>
                            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="rounded border px-3 py-1.5 text-sm" />
                        </div>
                        <div className="relative flex-1">
                            <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-subtle" />
                            <input type="text" value={searchText} onChange={(e) => setSearchText(e.target.value)} placeholder="거래처/상품 검색..." className="w-full rounded border py-1.5 pl-8 pr-3 text-sm" />
                        </div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-24 px-2 py-2 text-left">일자</th>
                                    <th className="w-32 px-2 py-2 text-left">전표번호</th>
                                    <th className="px-2 py-2 text-left">거래처명</th>
                                    <th className="px-2 py-2 text-left">상품명</th>
                                    <th className="w-16 px-2 py-2 text-right">수량</th>
                                    <th className="w-24 px-2 py-2 text-right">단가</th>
                                    <th className="w-28 px-2 py-2 text-right">공급가액</th>
                                    <th className="w-24 px-2 py-2 text-right">부가세</th>
                                    <th className="w-28 px-2 py-2 text-right">합계</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredItems.length === 0 ? (
                                    <tr>
                                        <td colSpan={9} className="py-8 text-center text-gray-500">
                                            {salesLoading ? "데이터를 불러오는 중..." : "조회된 매출 데이터가 없습니다."}
                                        </td>
                                    </tr>
                                ) : (
                                    filteredItems.map((item) => (
                                        <tr key={item.id} className="border-b hover:bg-surface-secondary">
                                            <td className="px-2 py-2">{item.date}</td>
                                            <td className="px-2 py-2 text-brand">{item.slipNo}</td>
                                            <td className="px-2 py-2">{item.customerName}</td>
                                            <td className="px-2 py-2">{item.productName}</td>
                                            <td className="px-2 py-2 text-right">{item.quantity}</td>
                                            <td className="px-2 py-2 text-right">{item.unitPrice.toLocaleString()}</td>
                                            <td className="px-2 py-2 text-right">{item.amount.toLocaleString()}</td>
                                            <td className="px-2 py-2 text-right">{item.vat.toLocaleString()}</td>
                                            <td className="px-2 py-2 text-right font-medium">{item.total.toLocaleString()}</td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                            {filteredItems.length > 0 && (
                                <tfoot className="bg-surface-secondary">
                                    <tr>
                                        <td colSpan={6} className="px-2 py-2 text-right font-medium">합계</td>
                                        <td className="px-2 py-2 text-right font-bold">{totalAmount.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right font-bold">{totalVat.toLocaleString()}</td>
                                        <td className="px-2 py-2 text-right font-bold text-blue-600">{grandTotal.toLocaleString()}</td>
                                    </tr>
                                </tfoot>
                            )}
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
