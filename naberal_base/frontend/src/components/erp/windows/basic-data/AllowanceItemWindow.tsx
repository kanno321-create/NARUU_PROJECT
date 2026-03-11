"use client";

import React, { useState } from "react";
import { Plus, Search, Trash2, Save } from "lucide-react";

interface AllowanceItem {
    id: string;
    code: string;
    name: string;
    type: "고정" | "변동";
    isTaxable: boolean;
    isActive: boolean;
    note: string;
}

export function AllowanceItemWindow() {
    const [items, setItems] = useState<AllowanceItem[]>([
        { id: "1", code: "AL001", name: "기본급", type: "고정", isTaxable: true, isActive: true, note: "" },
        { id: "2", code: "AL002", name: "식대", type: "고정", isTaxable: false, isActive: true, note: "비과세" },
        { id: "3", code: "AL003", name: "교통비", type: "고정", isTaxable: false, isActive: true, note: "비과세" },
        { id: "4", code: "AL004", name: "야근수당", type: "변동", isTaxable: true, isActive: true, note: "" },
    ]);

    const [searchQuery, setSearchQuery] = useState("");
    const [selectedId, setSelectedId] = useState<string | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [editForm, setEditForm] = useState<Partial<AllowanceItem>>({});

    const filteredItems = items.filter((i) => i.name.includes(searchQuery) || i.code.includes(searchQuery));

    const handleAdd = () => {
        const newItem: AllowanceItem = { id: String(Date.now()), code: `AL${String(items.length + 1).padStart(3, "0")}`, name: "", type: "고정", isTaxable: true, isActive: true, note: "" };
        setItems([...items, newItem]); setSelectedId(newItem.id); setEditForm(newItem); setIsEditing(true);
    };

    const handleEdit = (item: AllowanceItem) => { setSelectedId(item.id); setEditForm(item); setIsEditing(true); };
    const handleSave = () => { if (selectedId && editForm.name) { setItems(items.map((i) => (i.id === selectedId ? { ...i, ...editForm } as AllowanceItem : i))); setIsEditing(false); } };
    const handleDelete = (id: string) => { if (confirm("삭제하시겠습니까?")) { setItems(items.filter((i) => i.id !== id)); if (selectedId === id) { setSelectedId(null); setIsEditing(false); } } };

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button onClick={handleAdd} className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"><Plus className="h-4 w-4" />신규</button>
                {isEditing && <button onClick={handleSave} className="flex items-center gap-1 rounded bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700"><Save className="h-4 w-4" />저장</button>}
                <div className="ml-auto relative">
                    <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-subtle" />
                    <input type="text" placeholder="수당항목 검색..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="rounded border py-1.5 pl-8 pr-3 text-sm focus:border-brand focus:outline-none" />
                </div>
            </div>

            <div className="flex flex-1 overflow-hidden">
                <div className="w-1/2 overflow-auto border-r">
                    <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-surface"><tr className="border-b"><th className="px-3 py-2 text-left">코드</th><th className="px-3 py-2 text-left">수당명</th><th className="px-3 py-2 text-center">구분</th><th className="px-3 py-2 text-center">과세</th><th className="px-3 py-2 text-center">관리</th></tr></thead>
                        <tbody>
                            {filteredItems.map((item) => (
                                <tr key={item.id} className={`border-b cursor-pointer hover:bg-surface-secondary ${selectedId === item.id ? "bg-brand/10" : ""}`} onClick={() => handleEdit(item)}>
                                    <td className="px-3 py-2">{item.code}</td>
                                    <td className="px-3 py-2 font-medium">{item.name || "(신규)"}</td>
                                    <td className="px-3 py-2 text-center"><span className={`rounded px-2 py-0.5 text-xs ${item.type === "고정" ? "bg-blue-100 text-blue-800" : "bg-purple-100 text-purple-800"}`}>{item.type}</span></td>
                                    <td className="px-3 py-2 text-center"><span className={`rounded px-2 py-0.5 text-xs ${item.isTaxable ? "bg-red-100 text-red-800" : "bg-green-100 text-green-800"}`}>{item.isTaxable ? "과세" : "비과세"}</span></td>
                                    <td className="px-3 py-2 text-center"><button onClick={(e) => { e.stopPropagation(); handleDelete(item.id); }} className="rounded p-1 hover:bg-red-100 hover:text-red-600"><Trash2 className="h-4 w-4" /></button></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="flex-1 overflow-auto p-4">
                    {selectedId && isEditing ? (
                        <div className="space-y-4">
                            <h3 className="font-medium">수당항목 정보</h3>
                            <div className="grid grid-cols-2 gap-4">
                                <div><label className="mb-1 block text-sm font-medium">수당코드</label><input type="text" value={editForm.code || ""} onChange={(e) => setEditForm({ ...editForm, code: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" /></div>
                                <div><label className="mb-1 block text-sm font-medium">수당명 *</label><input type="text" value={editForm.name || ""} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" /></div>
                                <div><label className="mb-1 block text-sm font-medium">구분</label>
                                    <select value={editForm.type || "고정"} onChange={(e) => setEditForm({ ...editForm, type: e.target.value as "고정" | "변동" })} className="w-full rounded border px-3 py-2 text-sm"><option value="고정">고정</option><option value="변동">변동</option></select>
                                </div>
                                <div className="flex items-center gap-4">
                                    <div className="flex items-center gap-2"><input type="checkbox" id="isTaxable" checked={editForm.isTaxable ?? true} onChange={(e) => setEditForm({ ...editForm, isTaxable: e.target.checked })} className="h-4 w-4" /><label htmlFor="isTaxable" className="text-sm">과세</label></div>
                                    <div className="flex items-center gap-2"><input type="checkbox" id="isActive" checked={editForm.isActive ?? true} onChange={(e) => setEditForm({ ...editForm, isActive: e.target.checked })} className="h-4 w-4" /><label htmlFor="isActive" className="text-sm">사용</label></div>
                                </div>
                                <div className="col-span-2"><label className="mb-1 block text-sm font-medium">비고</label><input type="text" value={editForm.note || ""} onChange={(e) => setEditForm({ ...editForm, note: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" /></div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex h-full items-center justify-center text-text-subtle">수당항목을 선택하거나 신규 버튼을 클릭하세요</div>
                    )}
                </div>
            </div>
        </div>
    );
}
