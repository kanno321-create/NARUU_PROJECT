"use client";

import React, { useState } from "react";
import { Plus, Search, Trash2, Save, Printer, FileText, Eye } from "lucide-react";
import { PrintPreviewModal } from "../../common/PrintPreviewModal";

interface PurchaseSlipItem {
    id: string;
    productCode: string;
    productName: string;
    quantity: number;
    unitPrice: number;
    amount: number;
    vat: number;
    total: number;
}

interface PurchaseSlip {
    id: string;
    slipNo: string;
    date: string;
    supplierCode: string;
    supplierName: string;
    items: PurchaseSlipItem[];
    supplyAmount: number;
    vatAmount: number;
    totalAmount: number;
    note: string;
}

const SAVED_SLIPS: PurchaseSlip[] = [];

export function PurchaseSlipWindow() {
    const [slipNo, setSlipNo] = useState(`PU${new Date().toISOString().slice(0, 10).replace(/-/g, "")}-001`);
    const [slipDate, setSlipDate] = useState(new Date().toISOString().split("T")[0]);
    const [supplierCode, setSupplierCode] = useState("");
    const [supplierName, setSupplierName] = useState("");
    const [items, setItems] = useState<PurchaseSlipItem[]>([
        { id: "1", productCode: "", productName: "", quantity: 0, unitPrice: 0, amount: 0, vat: 0, total: 0 },
    ]);
    const [note, setNote] = useState("");
    const [savedSlips, setSavedSlips] = useState<PurchaseSlip[]>(SAVED_SLIPS);
    const [showPrintPreview, setShowPrintPreview] = useState(false);

    const handleAddRow = () => {
        setItems([...items, { id: String(Date.now()), productCode: "", productName: "", quantity: 0, unitPrice: 0, amount: 0, vat: 0, total: 0 }]);
    };

    const handleRemoveRow = (id: string) => {
        if (items.length > 1) setItems(items.filter((item) => item.id !== id));
    };

    const handleItemChange = (id: string, field: keyof PurchaseSlipItem, value: string | number) => {
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
    const totalVat = items.reduce((sum, item) => sum + item.vat, 0);
    const grandTotal = items.reduce((sum, item) => sum + item.total, 0);

    const handleSave = () => {
        if (!supplierCode || !supplierName) {
            alert("공급자 정보를 입력해주세요.");
            return;
        }
        const validItems = items.filter(item => item.productCode || item.productName || item.quantity > 0);
        if (validItems.length === 0) {
            alert("품목 정보를 입력해주세요.");
            return;
        }
        const newSlip: PurchaseSlip = {
            id: String(Date.now()),
            slipNo,
            date: slipDate,
            supplierCode,
            supplierName,
            items: validItems,
            supplyAmount: totalSupply,
            vatAmount: totalVat,
            totalAmount: grandTotal,
            note,
        };
        const existingIndex = savedSlips.findIndex(s => s.slipNo === slipNo);
        if (existingIndex >= 0) {
            const updated = [...savedSlips];
            updated[existingIndex] = newSlip;
            setSavedSlips(updated);
            alert(`전표 ${slipNo}이(가) 수정되었습니다.`);
        } else {
            setSavedSlips([...savedSlips, newSlip]);
            alert(`전표 ${slipNo}이(가) 저장되었습니다.`);
        }
    };

    const handleNew = () => {
        const nextNo = `PU${new Date().toISOString().slice(0, 10).replace(/-/g, "")}-${String(savedSlips.length + 1).padStart(3, "0")}`;
        setSlipNo(nextNo);
        setSlipDate(new Date().toISOString().split("T")[0]);
        setSupplierCode("");
        setSupplierName("");
        setItems([{ id: "1", productCode: "", productName: "", quantity: 0, unitPrice: 0, amount: 0, vat: 0, total: 0 }]);
        setNote("");
    };

    const printColumns = [
        { key: "productCode", label: "품목코드", width: "100px" },
        { key: "productName", label: "품목명", width: "200px" },
        { key: "quantity", label: "수량", width: "80px", align: "right" as const },
        { key: "unitPrice", label: "단가", width: "100px", align: "right" as const },
        { key: "amount", label: "공급가액", width: "100px", align: "right" as const },
        { key: "vat", label: "부가세", width: "80px", align: "right" as const },
        { key: "total", label: "합계", width: "100px", align: "right" as const },
    ];
    const printData = items.filter(item => item.productCode || item.productName || item.quantity > 0);
    const printHeaderInfo = [
        { label: "전표번호", value: slipNo },
        { label: "공급자코드", value: supplierCode },
        { label: "공급자명", value: supplierName },
    ];
    const printSummary = [
        { label: "공급가액", value: totalSupply },
        { label: "부가세", value: totalVat },
        { label: "합계금액", value: grandTotal },
    ];

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button onClick={handleSave} className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"><Save className="h-4 w-4" />저장</button>
                <button onClick={handleNew} className="flex items-center gap-1 rounded bg-gray-600 px-3 py-1.5 text-sm text-white hover:bg-gray-700"><FileText className="h-4 w-4" />신규</button>
                <button onClick={() => setShowPrintPreview(true)} className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Eye className="h-4 w-4" />인쇄미리보기</button>
                <button onClick={() => window.print()} className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"><Printer className="h-4 w-4" />인쇄</button>
                <div className="ml-auto relative">
                    <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-subtle" />
                    <input type="text" placeholder="전표 검색..." className="rounded border py-1.5 pl-8 pr-3 text-sm focus:border-brand focus:outline-none" />
                </div>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    <div className="grid grid-cols-5 gap-4">
                        <div><label className="mb-1 block text-sm font-medium">전표번호</label><input type="text" value={slipNo} readOnly className="w-full rounded border bg-gray-100 px-3 py-2 text-sm" /></div>
                        <div><label className="mb-1 block text-sm font-medium">전표일자</label><input type="date" value={slipDate} onChange={(e) => setSlipDate(e.target.value)} className="w-full rounded border px-3 py-2 text-sm" /></div>
                        <div><label className="mb-1 block text-sm font-medium">공급자코드</label><input type="text" value={supplierCode} onChange={(e) => setSupplierCode(e.target.value)} className="w-full rounded border px-3 py-2 text-sm" placeholder="F2: 검색" /></div>
                        <div className="col-span-2"><label className="mb-1 block text-sm font-medium">공급자명</label><input type="text" value={supplierName} onChange={(e) => setSupplierName(e.target.value)} className="w-full rounded border px-3 py-2 text-sm" /></div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-10 px-2 py-2 text-center">No</th>
                                    <th className="px-2 py-2 text-left">품목코드</th>
                                    <th className="px-2 py-2 text-left">품목명</th>
                                    <th className="w-20 px-2 py-2 text-right">수량</th>
                                    <th className="w-28 px-2 py-2 text-right">단가</th>
                                    <th className="w-28 px-2 py-2 text-right">공급가액</th>
                                    <th className="w-24 px-2 py-2 text-right">부가세</th>
                                    <th className="w-28 px-2 py-2 text-right">합계</th>
                                    <th className="w-10 px-2 py-2"></th>
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
                                        <td className="px-2 py-1 text-right">{item.vat.toLocaleString()}</td>
                                        <td className="px-2 py-1 text-right font-medium">{item.total.toLocaleString()}</td>
                                        <td className="px-1 py-1"><button onClick={() => handleRemoveRow(item.id)} className="rounded p-1 hover:bg-red-100 hover:text-red-600"><Trash2 className="h-4 w-4" /></button></td>
                                    </tr>
                                ))}
                            </tbody>
                            <tfoot className="bg-surface-secondary">
                                <tr>
                                    <td colSpan={5} className="px-2 py-2"><button onClick={handleAddRow} className="flex items-center gap-1 text-sm text-brand hover:text-brand-dark"><Plus className="h-4 w-4" />행 추가</button></td>
                                    <td className="px-2 py-2 text-right font-medium">{totalSupply.toLocaleString()}</td>
                                    <td className="px-2 py-2 text-right font-medium">{totalVat.toLocaleString()}</td>
                                    <td className="px-2 py-2 text-right font-bold text-brand">{grandTotal.toLocaleString()}</td>
                                    <td></td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>

                    <div><label className="mb-1 block text-sm font-medium">비고</label><textarea value={note} onChange={(e) => setNote(e.target.value)} rows={2} className="w-full rounded border px-3 py-2 text-sm" placeholder="메모 입력..." /></div>
                </div>
            </div>

            <PrintPreviewModal
                isOpen={showPrintPreview}
                onClose={() => setShowPrintPreview(false)}
                title="매입전표"
                subtitle="Purchase Slip"
                date={slipDate}
                columns={printColumns}
                data={printData}
                headerInfo={printHeaderInfo}
                summary={printSummary}
                note={note}
            />
        </div>
    );
}
