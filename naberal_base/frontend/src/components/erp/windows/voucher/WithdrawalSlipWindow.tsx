"use client";

import React, { useState, useCallback } from "react";
import { Plus, Search, Trash2, Save, Printer, FileText } from "lucide-react";
import { api } from "@/lib/api";

interface WithdrawalItem {
    id: string;
    accountCode: string;
    accountName: string;
    bankName: string;
    amount: number;
    note: string;
}

export function WithdrawalSlipWindow() {
    const [slipDate, setSlipDate] = useState(new Date().toISOString().split("T")[0]);
    const [items, setItems] = useState<WithdrawalItem[]>([
        { id: "1", accountCode: "", accountName: "", bankName: "", amount: 0, note: "" },
    ]);

    const handleAddRow = () => {
        setItems([...items, { id: String(Date.now()), accountCode: "", accountName: "", bankName: "", amount: 0, note: "" }]);
    };

    const handleRemoveRow = (id: string) => {
        if (items.length > 1) setItems(items.filter((item) => item.id !== id));
    };

    const handleItemChange = (id: string, field: keyof WithdrawalItem, value: string | number) => {
        setItems(items.map((item) => (item.id === id ? { ...item, [field]: value } : item)));
    };

    const totalAmount = items.reduce((sum, item) => sum + item.amount, 0);
    const [isSaving, setIsSaving] = useState(false);

    const handleSave = useCallback(async () => {
        if (isSaving) return;
        if (totalAmount <= 0) {
            alert("출금 금액을 입력해주세요.");
            return;
        }
        setIsSaving(true);
        try {
            await api.erp.payments.create({
                payment_type: "withdrawal",
                payment_date: slipDate,
                customer_id: items[0]?.accountCode || "withdrawal",
                amount: totalAmount,
                payment_method: "계좌이체",
                memo: items.map(i => `${i.bankName} ${i.accountName} ${i.note}`.trim()).filter(Boolean).join(", ") || undefined,
            });
            alert(`예금출금전표가 저장되었습니다.\n총 출금액: ${totalAmount.toLocaleString()}원`);
        } catch (err) {
            alert(`예금출금전표 저장 실패: ${err}`);
        } finally {
            setIsSaving(false);
        }
    }, [isSaving, totalAmount, slipDate, items]);

    const handleNew = useCallback(() => {
        setSlipDate(new Date().toISOString().split("T")[0]);
        setItems([{ id: "1", accountCode: "", accountName: "", bankName: "", amount: 0, note: "" }]);
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
                    <div className="rounded-lg border border-red-200 bg-red-50 p-2 text-center text-sm text-red-700">예금출금전표 - 계좌 출금 처리용</div>
                    <div className="grid grid-cols-4 gap-4">
                        <div><label className="mb-1 block text-sm font-medium">전표일자</label><input type="date" value={slipDate} onChange={(e) => setSlipDate(e.target.value)} className="w-full rounded border px-3 py-2 text-sm" /></div>
                        <div className="col-span-3 flex items-end">
                            <div className="rounded-lg bg-red-100 px-6 py-2 text-center">
                                <div className="text-xs text-red-600">출금 합계</div>
                                <div className="text-xl font-bold text-red-700">{totalAmount.toLocaleString()} 원</div>
                            </div>
                        </div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-10 px-2 py-2 text-center">No</th>
                                    <th className="w-28 px-2 py-2 text-left">계좌코드</th>
                                    <th className="px-2 py-2 text-left">계좌명</th>
                                    <th className="px-2 py-2 text-left">은행명</th>
                                    <th className="w-36 px-2 py-2 text-right">금액</th>
                                    <th className="px-2 py-2 text-left">비고</th>
                                    <th className="w-10 px-2 py-2"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item, idx) => (
                                    <tr key={item.id} className="border-b">
                                        <td className="px-2 py-1 text-center text-text-subtle">{idx + 1}</td>
                                        <td className="px-1 py-1"><input type="text" value={item.accountCode} onChange={(e) => handleItemChange(item.id, "accountCode", e.target.value)} className="w-full rounded border px-2 py-1 text-sm" /></td>
                                        <td className="px-1 py-1"><input type="text" value={item.accountName} onChange={(e) => handleItemChange(item.id, "accountName", e.target.value)} className="w-full rounded border px-2 py-1 text-sm" /></td>
                                        <td className="px-1 py-1"><input type="text" value={item.bankName} onChange={(e) => handleItemChange(item.id, "bankName", e.target.value)} className="w-full rounded border px-2 py-1 text-sm" /></td>
                                        <td className="px-1 py-1"><input type="number" value={item.amount} onChange={(e) => handleItemChange(item.id, "amount", Number(e.target.value))} className="w-full rounded border px-2 py-1 text-sm text-right" /></td>
                                        <td className="px-1 py-1"><input type="text" value={item.note} onChange={(e) => handleItemChange(item.id, "note", e.target.value)} className="w-full rounded border px-2 py-1 text-sm" /></td>
                                        <td className="px-1 py-1"><button onClick={() => handleRemoveRow(item.id)} className="rounded p-1 hover:bg-red-100 hover:text-red-600"><Trash2 className="h-4 w-4" /></button></td>
                                    </tr>
                                ))}
                            </tbody>
                            <tfoot className="bg-surface-secondary">
                                <tr>
                                    <td colSpan={7} className="px-2 py-2"><button onClick={handleAddRow} className="flex items-center gap-1 text-sm text-brand hover:text-brand-dark"><Plus className="h-4 w-4" />행 추가</button></td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
