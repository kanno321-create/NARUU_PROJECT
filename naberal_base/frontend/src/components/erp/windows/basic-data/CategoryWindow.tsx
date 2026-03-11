"use client";

import React, { useState } from "react";
import { Plus, Search, Trash2, Save, Tag } from "lucide-react";

interface Category {
    id: string;
    code: string;
    name: string;
    parentId: string | null;
    depth: number;
    sortOrder: number;
    isActive: boolean;
    note: string;
}

export function CategoryWindow() {
    const [categories, setCategories] = useState<Category[]>([
        { id: "1", code: "CAT001", name: "차단기", parentId: null, depth: 0, sortOrder: 1, isActive: true, note: "" },
        { id: "2", code: "CAT002", name: "배선용차단기", parentId: "1", depth: 1, sortOrder: 1, isActive: true, note: "" },
        { id: "3", code: "CAT003", name: "누전차단기", parentId: "1", depth: 1, sortOrder: 2, isActive: true, note: "" },
        { id: "4", code: "CAT004", name: "외함", parentId: null, depth: 0, sortOrder: 2, isActive: true, note: "" },
    ]);

    const [searchQuery, setSearchQuery] = useState("");
    const [selectedId, setSelectedId] = useState<string | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [editForm, setEditForm] = useState<Partial<Category>>({});

    const filteredCategories = categories.filter((c) => c.name.includes(searchQuery) || c.code.includes(searchQuery));

    const handleAdd = () => {
        const newCat: Category = { id: String(Date.now()), code: `CAT${String(categories.length + 1).padStart(3, "0")}`, name: "", parentId: null, depth: 0, sortOrder: categories.length + 1, isActive: true, note: "" };
        setCategories([...categories, newCat]); setSelectedId(newCat.id); setEditForm(newCat); setIsEditing(true);
    };

    const handleEdit = (cat: Category) => { setSelectedId(cat.id); setEditForm(cat); setIsEditing(true); };
    const handleSave = () => { if (selectedId && editForm.name) { setCategories(categories.map((c) => (c.id === selectedId ? { ...c, ...editForm } as Category : c))); setIsEditing(false); } };
    const handleDelete = (id: string) => { if (confirm("삭제하시겠습니까?")) { setCategories(categories.filter((c) => c.id !== id)); if (selectedId === id) { setSelectedId(null); setIsEditing(false); } } };

    const getParentName = (parentId: string | null) => parentId ? categories.find((c) => c.id === parentId)?.name || "" : "";

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button onClick={handleAdd} className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"><Plus className="h-4 w-4" />신규</button>
                {isEditing && <button onClick={handleSave} className="flex items-center gap-1 rounded bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700"><Save className="h-4 w-4" />저장</button>}
                <div className="ml-auto relative">
                    <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-subtle" />
                    <input type="text" placeholder="분류 검색..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="rounded border py-1.5 pl-8 pr-3 text-sm focus:border-brand focus:outline-none" />
                </div>
            </div>

            <div className="flex flex-1 overflow-hidden">
                <div className="w-1/2 overflow-auto border-r">
                    <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-surface"><tr className="border-b"><th className="px-3 py-2 text-left">코드</th><th className="px-3 py-2 text-left">분류명</th><th className="px-3 py-2 text-left">상위분류</th><th className="px-3 py-2 text-center">사용</th><th className="px-3 py-2 text-center">관리</th></tr></thead>
                        <tbody>
                            {filteredCategories.map((cat) => (
                                <tr key={cat.id} className={`border-b cursor-pointer hover:bg-surface-secondary ${selectedId === cat.id ? "bg-brand/10" : ""}`} onClick={() => handleEdit(cat)}>
                                    <td className="px-3 py-2">{cat.code}</td>
                                    <td className="px-3 py-2 font-medium" style={{ paddingLeft: `${cat.depth * 16 + 12}px` }}><Tag className="mr-1 inline h-4 w-4 text-text-subtle" />{cat.name || "(신규)"}</td>
                                    <td className="px-3 py-2">{getParentName(cat.parentId)}</td>
                                    <td className="px-3 py-2 text-center"><span className={`rounded px-2 py-0.5 text-xs ${cat.isActive ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}`}>{cat.isActive ? "Y" : "N"}</span></td>
                                    <td className="px-3 py-2 text-center"><button onClick={(e) => { e.stopPropagation(); handleDelete(cat.id); }} className="rounded p-1 hover:bg-red-100 hover:text-red-600"><Trash2 className="h-4 w-4" /></button></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="flex-1 overflow-auto p-4">
                    {selectedId && isEditing ? (
                        <div className="space-y-4">
                            <h3 className="font-medium">품목분류 정보</h3>
                            <div className="grid grid-cols-2 gap-4">
                                <div><label className="mb-1 block text-sm font-medium">분류코드</label><input type="text" value={editForm.code || ""} onChange={(e) => setEditForm({ ...editForm, code: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" /></div>
                                <div><label className="mb-1 block text-sm font-medium">분류명 *</label><input type="text" value={editForm.name || ""} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" /></div>
                                <div><label className="mb-1 block text-sm font-medium">상위분류</label>
                                    <select value={editForm.parentId || ""} onChange={(e) => setEditForm({ ...editForm, parentId: e.target.value || null, depth: e.target.value ? 1 : 0 })} className="w-full rounded border px-3 py-2 text-sm">
                                        <option value="">없음 (최상위)</option>
                                        {categories.filter((c) => c.id !== selectedId && c.depth === 0).map((c) => (<option key={c.id} value={c.id}>{c.name}</option>))}
                                    </select>
                                </div>
                                <div><label className="mb-1 block text-sm font-medium">정렬순서</label><input type="number" value={editForm.sortOrder || 0} onChange={(e) => setEditForm({ ...editForm, sortOrder: Number(e.target.value) })} className="w-full rounded border px-3 py-2 text-sm" /></div>
                                <div className="flex items-center gap-2"><input type="checkbox" id="isActive" checked={editForm.isActive ?? true} onChange={(e) => setEditForm({ ...editForm, isActive: e.target.checked })} className="h-4 w-4" /><label htmlFor="isActive" className="text-sm">사용</label></div>
                                <div><label className="mb-1 block text-sm font-medium">비고</label><input type="text" value={editForm.note || ""} onChange={(e) => setEditForm({ ...editForm, note: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" /></div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex h-full items-center justify-center text-text-subtle">분류를 선택하거나 신규 버튼을 클릭하세요</div>
                    )}
                </div>
            </div>
        </div>
    );
}
