"use client";

import React, { useState } from "react";
import { Plus, Search, Trash2, Save } from "lucide-react";

interface ThemeCategoryMargin {
    id: string;
    themeCode: string;
    themeName: string;
    marginGroupCode: string;
    marginGroupName: string;
    marginRate: number;
    isActive: boolean;
}

export function ThemeCategoryMarginWindow() {
    const [margins, setMargins] = useState<ThemeCategoryMargin[]>([
        { id: "1", themeCode: "TH001", themeName: "전기자재", marginGroupCode: "MG001", marginGroupName: "일반", marginRate: 20, isActive: true },
        { id: "2", themeCode: "TH002", themeName: "조명기기", marginGroupCode: "MG002", marginGroupName: "도매", marginRate: 15, isActive: true },
    ]);

    const [searchQuery, setSearchQuery] = useState("");
    const [selectedId, setSelectedId] = useState<string | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [editForm, setEditForm] = useState<Partial<ThemeCategoryMargin>>({});

    const filteredMargins = margins.filter((m) => m.themeName.includes(searchQuery) || m.marginGroupName.includes(searchQuery));

    const handleAdd = () => {
        const newMargin: ThemeCategoryMargin = { id: String(Date.now()), themeCode: "", themeName: "", marginGroupCode: "", marginGroupName: "", marginRate: 0, isActive: true };
        setMargins([...margins, newMargin]); setSelectedId(newMargin.id); setEditForm(newMargin); setIsEditing(true);
    };

    const handleEdit = (margin: ThemeCategoryMargin) => { setSelectedId(margin.id); setEditForm(margin); setIsEditing(true); };
    const handleSave = () => { if (selectedId && editForm.themeName) { setMargins(margins.map((m) => (m.id === selectedId ? { ...m, ...editForm } as ThemeCategoryMargin : m))); setIsEditing(false); } };
    const handleDelete = (id: string) => { if (confirm("삭제하시겠습니까?")) { setMargins(margins.filter((m) => m.id !== id)); if (selectedId === id) { setSelectedId(null); setIsEditing(false); } } };

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button onClick={handleAdd} className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"><Plus className="h-4 w-4" />신규</button>
                {isEditing && <button onClick={handleSave} className="flex items-center gap-1 rounded bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700"><Save className="h-4 w-4" />저장</button>}
                <div className="ml-auto relative">
                    <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-subtle" />
                    <input type="text" placeholder="검색..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="rounded border py-1.5 pl-8 pr-3 text-sm focus:border-brand focus:outline-none" />
                </div>
            </div>

            <div className="flex flex-1 overflow-hidden">
                <div className="w-1/2 overflow-auto border-r">
                    <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-surface"><tr className="border-b"><th className="px-3 py-2 text-left">테마</th><th className="px-3 py-2 text-left">마진그룹</th><th className="px-3 py-2 text-right">마진율</th><th className="px-3 py-2 text-center">사용</th><th className="px-3 py-2 text-center">관리</th></tr></thead>
                        <tbody>
                            {filteredMargins.map((margin) => (
                                <tr key={margin.id} className={`border-b cursor-pointer hover:bg-surface-secondary ${selectedId === margin.id ? "bg-brand/10" : ""}`} onClick={() => handleEdit(margin)}>
                                    <td className="px-3 py-2 font-medium">{margin.themeName || "(신규)"}</td>
                                    <td className="px-3 py-2">{margin.marginGroupName}</td>
                                    <td className="px-3 py-2 text-right">{margin.marginRate}%</td>
                                    <td className="px-3 py-2 text-center"><span className={`rounded px-2 py-0.5 text-xs ${margin.isActive ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}`}>{margin.isActive ? "Y" : "N"}</span></td>
                                    <td className="px-3 py-2 text-center"><button onClick={(e) => { e.stopPropagation(); handleDelete(margin.id); }} className="rounded p-1 hover:bg-red-100 hover:text-red-600"><Trash2 className="h-4 w-4" /></button></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="flex-1 overflow-auto p-4">
                    {selectedId && isEditing ? (
                        <div className="space-y-4">
                            <h3 className="font-medium">테마별 마진 설정</h3>
                            <div className="grid grid-cols-2 gap-4">
                                <div><label className="mb-1 block text-sm font-medium">테마코드</label><input type="text" value={editForm.themeCode || ""} onChange={(e) => setEditForm({ ...editForm, themeCode: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" /></div>
                                <div><label className="mb-1 block text-sm font-medium">테마명 *</label><input type="text" value={editForm.themeName || ""} onChange={(e) => setEditForm({ ...editForm, themeName: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" /></div>
                                <div><label className="mb-1 block text-sm font-medium">마진그룹코드</label><input type="text" value={editForm.marginGroupCode || ""} onChange={(e) => setEditForm({ ...editForm, marginGroupCode: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" /></div>
                                <div><label className="mb-1 block text-sm font-medium">마진그룹명</label><input type="text" value={editForm.marginGroupName || ""} onChange={(e) => setEditForm({ ...editForm, marginGroupName: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" /></div>
                                <div><label className="mb-1 block text-sm font-medium">마진율 (%)</label><input type="number" value={editForm.marginRate || 0} onChange={(e) => setEditForm({ ...editForm, marginRate: Number(e.target.value) })} className="w-full rounded border px-3 py-2 text-sm" /></div>
                                <div className="flex items-center gap-2"><input type="checkbox" id="isActive" checked={editForm.isActive ?? true} onChange={(e) => setEditForm({ ...editForm, isActive: e.target.checked })} className="h-4 w-4" /><label htmlFor="isActive" className="text-sm">사용</label></div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex h-full items-center justify-center text-text-subtle">항목을 선택하거나 신규 버튼을 클릭하세요</div>
                    )}
                </div>
            </div>
        </div>
    );
}
