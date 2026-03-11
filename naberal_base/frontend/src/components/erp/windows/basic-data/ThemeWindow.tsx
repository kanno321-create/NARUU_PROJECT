"use client";

import React, { useState } from "react";
import { Plus, Search, Trash2, Save, Palette } from "lucide-react";

interface Theme {
    id: string;
    code: string;
    name: string;
    description: string;
    sortOrder: number;
    isActive: boolean;
    note: string;
}

export function ThemeWindow() {
    const [themes, setThemes] = useState<Theme[]>([
        { id: "1", code: "TH001", name: "전기자재", description: "전기 관련 자재", sortOrder: 1, isActive: true, note: "" },
        { id: "2", code: "TH002", name: "조명기기", description: "조명 관련 자재", sortOrder: 2, isActive: true, note: "" },
        { id: "3", code: "TH003", name: "배관자재", description: "배관 관련 자재", sortOrder: 3, isActive: true, note: "" },
    ]);

    const [searchQuery, setSearchQuery] = useState("");
    const [selectedId, setSelectedId] = useState<string | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [editForm, setEditForm] = useState<Partial<Theme>>({});

    const filteredThemes = themes.filter((t) => t.name.includes(searchQuery) || t.code.includes(searchQuery));

    const handleAdd = () => {
        const newTheme: Theme = { id: String(Date.now()), code: `TH${String(themes.length + 1).padStart(3, "0")}`, name: "", description: "", sortOrder: themes.length + 1, isActive: true, note: "" };
        setThemes([...themes, newTheme]); setSelectedId(newTheme.id); setEditForm(newTheme); setIsEditing(true);
    };

    const handleEdit = (theme: Theme) => { setSelectedId(theme.id); setEditForm(theme); setIsEditing(true); };
    const handleSave = () => { if (selectedId && editForm.name) { setThemes(themes.map((t) => (t.id === selectedId ? { ...t, ...editForm } as Theme : t))); setIsEditing(false); } };
    const handleDelete = (id: string) => { if (confirm("삭제하시겠습니까?")) { setThemes(themes.filter((t) => t.id !== id)); if (selectedId === id) { setSelectedId(null); setIsEditing(false); } } };

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button onClick={handleAdd} className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"><Plus className="h-4 w-4" />신규</button>
                {isEditing && <button onClick={handleSave} className="flex items-center gap-1 rounded bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700"><Save className="h-4 w-4" />저장</button>}
                <div className="ml-auto relative">
                    <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-subtle" />
                    <input type="text" placeholder="테마 검색..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="rounded border py-1.5 pl-8 pr-3 text-sm focus:border-brand focus:outline-none" />
                </div>
            </div>

            <div className="flex flex-1 overflow-hidden">
                <div className="w-1/2 overflow-auto border-r">
                    <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-surface"><tr className="border-b"><th className="px-3 py-2 text-left">코드</th><th className="px-3 py-2 text-left">테마명</th><th className="px-3 py-2 text-left">설명</th><th className="px-3 py-2 text-center">사용</th><th className="px-3 py-2 text-center">관리</th></tr></thead>
                        <tbody>
                            {filteredThemes.map((theme) => (
                                <tr key={theme.id} className={`border-b cursor-pointer hover:bg-surface-secondary ${selectedId === theme.id ? "bg-brand/10" : ""}`} onClick={() => handleEdit(theme)}>
                                    <td className="px-3 py-2">{theme.code}</td>
                                    <td className="px-3 py-2 font-medium"><Palette className="mr-1 inline h-4 w-4 text-text-subtle" />{theme.name || "(신규)"}</td>
                                    <td className="px-3 py-2 text-text-subtle">{theme.description}</td>
                                    <td className="px-3 py-2 text-center"><span className={`rounded px-2 py-0.5 text-xs ${theme.isActive ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}`}>{theme.isActive ? "Y" : "N"}</span></td>
                                    <td className="px-3 py-2 text-center"><button onClick={(e) => { e.stopPropagation(); handleDelete(theme.id); }} className="rounded p-1 hover:bg-red-100 hover:text-red-600"><Trash2 className="h-4 w-4" /></button></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="flex-1 overflow-auto p-4">
                    {selectedId && isEditing ? (
                        <div className="space-y-4">
                            <h3 className="font-medium">테마 정보</h3>
                            <div className="grid grid-cols-2 gap-4">
                                <div><label className="mb-1 block text-sm font-medium">테마코드</label><input type="text" value={editForm.code || ""} onChange={(e) => setEditForm({ ...editForm, code: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" /></div>
                                <div><label className="mb-1 block text-sm font-medium">테마명 *</label><input type="text" value={editForm.name || ""} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" /></div>
                                <div className="col-span-2"><label className="mb-1 block text-sm font-medium">설명</label><input type="text" value={editForm.description || ""} onChange={(e) => setEditForm({ ...editForm, description: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" /></div>
                                <div><label className="mb-1 block text-sm font-medium">정렬순서</label><input type="number" value={editForm.sortOrder || 0} onChange={(e) => setEditForm({ ...editForm, sortOrder: Number(e.target.value) })} className="w-full rounded border px-3 py-2 text-sm" /></div>
                                <div className="flex items-center gap-2"><input type="checkbox" id="isActive" checked={editForm.isActive ?? true} onChange={(e) => setEditForm({ ...editForm, isActive: e.target.checked })} className="h-4 w-4" /><label htmlFor="isActive" className="text-sm">사용</label></div>
                                <div className="col-span-2"><label className="mb-1 block text-sm font-medium">비고</label><input type="text" value={editForm.note || ""} onChange={(e) => setEditForm({ ...editForm, note: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" /></div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex h-full items-center justify-center text-text-subtle">테마를 선택하거나 신규 버튼을 클릭하세요</div>
                    )}
                </div>
            </div>
        </div>
    );
}
