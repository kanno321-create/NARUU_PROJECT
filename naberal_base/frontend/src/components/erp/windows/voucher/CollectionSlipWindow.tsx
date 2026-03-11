"use client";

import React, { useState, useCallback } from "react";
import { Plus, Search, Trash2, Save, Printer, FileText } from "lucide-react";
import { api } from "@/lib/api";

interface CollectionItem {
    id: string;
    type: "현금" | "카드" | "계좌이체" | "어음" | "기타";
    bankName: string;
    amount: number;
    note: string;
}

export function CollectionSlipWindow() {
    const [slipDate, setSlipDate] = useState(new Date().toISOString().split("T")[0]);
    const [customerCode, setCustomerCode] = useState("");
    const [customerName, setCustomerName] = useState("");
    const [items, setItems] = useState<CollectionItem[]>([
        { id: "1", type: "현금", bankName: "", amount: 0, note: "" },
    ]);

    const handleAddRow = () => {
        setItems([...items, { id: String(Date.now()), type: "현금", bankName: "", amount: 0, note: "" }]);
    };

    const handleRemoveRow = (id: string) => {
        if (items.length > 1) setItems(items.filter((item) => item.id !== id));
    };

    const handleItemChange = (id: string, field: keyof CollectionItem, value: string | number) => {
        setItems(items.map((item) => (item.id === id ? { ...item, [field]: value } : item)));
    };

    const totalAmount = items.reduce((sum, item) => sum + item.amount, 0);
    const [isSaving, setIsSaving] = useState(false);

    const handleSave = useCallback(async () => {
        if (isSaving) return;
        if (!customerCode && !customerName) {
            alert("거래처를 입력해주세요.");
            return;
        }
        if (totalAmount <= 0) {
            alert("수금 금액을 입력해주세요.");
            return;
        }
        setIsSaving(true);
        try {
            await api.erp.payments.create({
                payment_type: "collection",
                payment_date: slipDate,
                customer_id: customerCode || customerName,
                amount: totalAmount,
                payment_method: items[0]?.type || "현금",
                memo: items.map(i => i.note).filter(Boolean).join(", ") || undefined,
            });
            alert(`수금전표가 저장되었습니다.\n거래처: ${customerName || customerCode}\n총 수금액: ${totalAmount.toLocaleString()}원`);
        } catch (err) {
            alert(`수금전표 저장 실패: ${err}`);
        } finally {
            setIsSaving(false);
        }
    }, [isSaving, customerCode, customerName, totalAmount, slipDate, items]);

    const handleNew = useCallback(() => {
        setSlipDate(new Date().toISOString().split("T")[0]);
        setCustomerCode("");
        setCustomerName("");
        setItems([{ id: "1", type: "현금", bankName: "", amount: 0, note: "" }]);
    }, []);

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button onClick={handleSave} disabled={isSaving} className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark disabled:opacity-50"><Save className="h-4 w-4" />{isSaving ? "저장중..." : "저장"}</button>
                <button onClick={handleNew} className="flex items-center gap-1 rounded bg-gray-600 px-3 py-1.5 text-sm text-white hover:bg-gray-700"><FileText className="h-4 w-4" />신규</button>
                <button onClick={() => window.print()} className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Printer className="h-4 w-4" />인쇄</button>
                <div className="ml-auto relative">
                    <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-subtle" />
                    <input type="text" placeholder="전표 검색..." className="rounded border py-1.5 pl-8 pr-3 text-sm focus:border-brand focus:outline-none" />
                </div>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    <div className="grid grid-cols-4 gap-4">
                        <div><label className="mb-1 block text-sm font-medium">전표일자</label><input type="date" value={slipDate} onChange={(e) => setSlipDate(e.target.value)} className="w-full rounded border px-3 py-2 text-sm" /></div>
                        <div><label className="mb-1 block text-sm font-medium">거래처코드</label><input type="text" value={customerCode} onChange={(e) => setCustomerCode(e.target.value)} className="w-full rounded border px-3 py-2 text-sm" placeholder="F2: 검색" /></div>
                        <div className="col-span-2"><label className="mb-1 block text-sm font-medium">거래처명</label><input type="text" value={customerName} onChange={(e) => setCustomerName(e.target.value)} className="w-full rounded border px-3 py-2 text-sm" /></div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-10 px-2 py-2 text-center">No</th>
                                    <th className="w-32 px-2 py-2 text-left">수금유형</th>
                                    <th className="px-2 py-2 text-left">은행/카드사</th>
                                    <th className="w-36 px-2 py-2 text-right">금액</th>
                                    <th className="px-2 py-2 text-left">비고</th>
                                    <th className="w-10 px-2 py-2"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item, idx) => (
                                    <tr key={item.id} className="border-b">
                                        <td className="px-2 py-1 text-center text-text-subtle">{idx + 1}</td>
                                        <td className="px-1 py-1">
                                            <select value={item.type} onChange={(e) => handleItemChange(item.id, "type", e.target.value)} className="w-full rounded border px-2 py-1 text-sm">
                                                <option value="현금">현금</option>
                                                <option value="카드">카드</option>
                                                <option value="계좌이체">계좌이체</option>
                                                <option value="어음">어음</option>
                                                <option value="기타">기타</option>
                                            </select>
                                        </td>
                                        <td className="px-1 py-1"><input type="text" value={item.bankName} onChange={(e) => handleItemChange(item.id, "bankName", e.target.value)} className="w-full rounded border px-2 py-1 text-sm" /></td>
                                        <td className="px-1 py-1"><input type="number" value={item.amount} onChange={(e) => handleItemChange(item.id, "amount", Number(e.target.value))} className="w-full rounded border px-2 py-1 text-sm text-right" /></td>
                                        <td className="px-1 py-1"><input type="text" value={item.note} onChange={(e) => handleItemChange(item.id, "note", e.target.value)} className="w-full rounded border px-2 py-1 text-sm" /></td>
                                        <td className="px-1 py-1"><button onClick={() => handleRemoveRow(item.id)} className="rounded p-1 hover:bg-red-100 hover:text-red-600"><Trash2 className="h-4 w-4" /></button></td>
                                    </tr>
                                ))}
                            </tbody>
                            <tfoot className="bg-surface-secondary">
                                <tr>
                                    <td colSpan={3} className="px-2 py-2"><button onClick={handleAddRow} className="flex items-center gap-1 text-sm text-brand hover:text-brand-dark"><Plus className="h-4 w-4" />행 추가</button></td>
                                    <td className="px-2 py-2 text-right font-bold text-brand">{totalAmount.toLocaleString()}</td>
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
