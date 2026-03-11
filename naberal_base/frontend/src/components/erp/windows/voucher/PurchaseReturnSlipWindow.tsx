"use client";

import React, { useState } from "react";
import { Plus, Search, Trash2, Save, Printer, FileText } from "lucide-react";

interface ReturnItem {
    id: string;
    productCode: string;
    productName: string;
    quantity: number;
    unitPrice: number;
    amount: number;
    vat: number;
    total: number;
    reason: string;
}

export function PurchaseReturnSlipWindow() {
    const [slipDate, setSlipDate] = useState(new Date().toISOString().split("T")[0]);
    const [supplierCode, setSupplierCode] = useState("");
    const [supplierName, setSupplierName] = useState("");
    const [originalSlipNo, setOriginalSlipNo] = useState("");
    const [items, setItems] = useState<ReturnItem[]>([
        { id: "1", productCode: "", productName: "", quantity: 0, unitPrice: 0, amount: 0, vat: 0, total: 0, reason: "" },
    ]);

    const handleAddRow = () => {
        setItems([...items, { id: String(Date.now()), productCode: "", productName: "", quantity: 0, unitPrice: 0, amount: 0, vat: 0, total: 0, reason: "" }]);
    };

    const handleRemoveRow = (id: string) => {
        if (items.length > 1) setItems(items.filter((item) => item.id !== id));
    };

    const handleItemChange = (id: string, field: keyof ReturnItem, value: string | number) => {
        setItems(items.map((item) => {
            if (item.id === id) {
                const updated = { ...item, [field]: value };
                if (field === "quantity" || field === "unitPrice") {
                    updated.amount = updated.quantity * updated.unitPrice;
                    updated.vat = Math.round(updated.amount * 0.1);
                    updated.total = updated.amount + updated.vat;
                }
                return updated;
            }
            return item;
        }));
    };

    const totalSupply = items.reduce((sum, item) => sum + item.amount, 0);
    const grandTotal = items.reduce((sum, item) => sum + item.total, 0);

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"><Save className="h-4 w-4" />저장</button>
                <button className="flex items-center gap-1 rounded bg-gray-600 px-3 py-1.5 text-sm text-white hover:bg-gray-700"><FileText className="h-4 w-4" />신규</button>
                <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Printer className="h-4 w-4" />인쇄</button>
                <div className="ml-auto relative">
                    <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-subtle" />
                    <input type="text" placeholder="전표 검색..." className="rounded border py-1.5 pl-8 pr-3 text-sm focus:border-brand focus:outline-none" />
                </div>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    <div className="rounded-lg border border-purple-200 bg-purple-50 p-2 text-center text-sm text-purple-700">매입반품전표 - 구매 후 반품 처리용</div>
                    <div className="grid grid-cols-5 gap-4">
                        <div><label className="mb-1 block text-sm font-medium">전표일자</label><input type="date" value={slipDate} onChange={(e) => setSlipDate(e.target.value)} className="w-full rounded border px-3 py-2 text-sm" /></div>
                        <div><label className="mb-1 block text-sm font-medium">원전표번호</label><input type="text" value={originalSlipNo} onChange={(e) => setOriginalSlipNo(e.target.value)} className="w-full rounded border px-3 py-2 text-sm" placeholder="F2: 검색" /></div>
                        <div><label className="mb-1 block text-sm font-medium">공급자코드</label><input type="text" value={supplierCode} onChange={(e) => setSupplierCode(e.target.value)} className="w-full rounded border px-3 py-2 text-sm" /></div>
                        <div className="col-span-2"><label className="mb-1 block text-sm font-medium">공급자명</label><input type="text" value={supplierName} onChange={(e) => setSupplierName(e.target.value)} className="w-full rounded border px-3 py-2 text-sm" /></div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-10 px-2 py-2">No</th>
                                    <th className="px-2 py-2 text-left">품목코드</th>
                                    <th className="px-2 py-2 text-left">품목명</th>
                                    <th className="w-20 px-2 py-2 text-right">수량</th>
                                    <th className="w-24 px-2 py-2 text-right">단가</th>
                                    <th className="w-24 px-2 py-2 text-right">공급가</th>
                                    <th className="w-24 px-2 py-2 text-right">합계</th>
                                    <th className="w-28 px-2 py-2 text-left">반품사유</th>
                                    <th className="w-10"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item, idx) => (
                                    <tr key={item.id} className="border-b">
                                        <td className="px-2 py-1 text-center text-text-subtle">{idx + 1}</td>
                                        <td className="px-1 py-1"><input type="text" value={item.productCode} onChange={(e) => handleItemChange(item.id, "productCode", e.target.value)} className="w-full rounded border px-2 py-1 text-sm" /></td>
                                        <td className="px-1 py-1"><input type="text" value={item.productName} onChange={(e) => handleItemChange(item.id, "productName", e.target.value)} className="w-full rounded border px-2 py-1 text-sm" /></td>
                                        <td className="px-1 py-1"><input type="number" value={item.quantity} onChange={(e) => handleItemChange(item.id, "quantity", Number(e.target.value))} className="w-full rounded border px-2 py-1 text-sm text-right" /></td>
                                        <td className="px-1 py-1"><input type="number" value={item.unitPrice} onChange={(e) => handleItemChange(item.id, "unitPrice", Number(e.target.value))} className="w-full rounded border px-2 py-1 text-sm text-right" /></td>
                                        <td className="px-2 py-1 text-right">{item.amount.toLocaleString()}</td>
                                        <td className="px-2 py-1 text-right font-medium">{item.total.toLocaleString()}</td>
                                        <td className="px-1 py-1"><input type="text" value={item.reason} onChange={(e) => handleItemChange(item.id, "reason", e.target.value)} className="w-full rounded border px-2 py-1 text-sm" placeholder="불량/파손" /></td>
                                        <td className="px-1 py-1"><button onClick={() => handleRemoveRow(item.id)} className="rounded p-1 hover:bg-red-100 hover:text-red-600"><Trash2 className="h-4 w-4" /></button></td>
                                    </tr>
                                ))}
                            </tbody>
                            <tfoot className="bg-surface-secondary">
                                <tr>
                                    <td colSpan={5} className="px-2 py-2"><button onClick={handleAddRow} className="flex items-center gap-1 text-sm text-brand hover:text-brand-dark"><Plus className="h-4 w-4" />행 추가</button></td>
                                    <td className="px-2 py-2 text-right font-medium">{totalSupply.toLocaleString()}</td>
                                    <td className="px-2 py-2 text-right font-bold text-purple-600">{grandTotal.toLocaleString()}</td>
                                    <td colSpan={2}></td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
