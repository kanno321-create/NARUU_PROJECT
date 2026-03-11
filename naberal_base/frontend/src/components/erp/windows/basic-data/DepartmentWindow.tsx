"use client";

import React, { useState } from "react";
import { Plus, Search, Trash2, Save, FolderTree } from "lucide-react";

interface Department {
    id: string;
    code: string;
    name: string;
    parentId: string | null;
    manager: string;
    tel: string;
    note: string;
}

export function DepartmentWindow() {
    const [departments, setDepartments] = useState<Department[]>([
        { id: "1", code: "D001", name: "경영지원팀", parentId: null, manager: "홍길동", tel: "02-1234-5678", note: "" },
        { id: "2", code: "D002", name: "영업팀", parentId: null, manager: "김철수", tel: "02-1234-5679", note: "" },
        { id: "3", code: "D003", name: "생산팀", parentId: null, manager: "이영희", tel: "02-1234-5680", note: "" },
    ]);

    const [searchQuery, setSearchQuery] = useState("");
    const [selectedId, setSelectedId] = useState<string | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [editForm, setEditForm] = useState<Partial<Department>>({});

    const filteredDepartments = departments.filter(
        (d) => d.name.toLowerCase().includes(searchQuery.toLowerCase()) || d.code.includes(searchQuery)
    );

    const handleAdd = () => {
        const newDept: Department = {
            id: String(Date.now()),
            code: `D${String(departments.length + 1).padStart(3, "0")}`,
            name: "",
            parentId: null,
            manager: "",
            tel: "",
            note: "",
        };
        setDepartments([...departments, newDept]);
        setSelectedId(newDept.id);
        setEditForm(newDept);
        setIsEditing(true);
    };

    const handleEdit = (dept: Department) => {
        setSelectedId(dept.id);
        setEditForm(dept);
        setIsEditing(true);
    };

    const handleSave = () => {
        if (selectedId && editForm.name) {
            setDepartments(departments.map((d) => (d.id === selectedId ? { ...d, ...editForm } as Department : d)));
            setIsEditing(false);
        }
    };

    const handleDelete = (id: string) => {
        if (confirm("삭제하시겠습니까?")) {
            setDepartments(departments.filter((d) => d.id !== id));
            if (selectedId === id) {
                setSelectedId(null);
                setIsEditing(false);
            }
        }
    };

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button onClick={handleAdd} className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark">
                    <Plus className="h-4 w-4" />
                    신규
                </button>
                {isEditing && (
                    <button onClick={handleSave} className="flex items-center gap-1 rounded bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700">
                        <Save className="h-4 w-4" />
                        저장
                    </button>
                )}
                <div className="ml-auto flex items-center gap-2">
                    <div className="relative">
                        <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-subtle" />
                        <input
                            type="text"
                            placeholder="부서 검색..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="rounded border py-1.5 pl-8 pr-3 text-sm focus:border-brand focus:outline-none"
                        />
                    </div>
                </div>
            </div>

            <div className="flex flex-1 overflow-hidden">
                <div className="w-1/2 overflow-auto border-r">
                    <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-surface">
                            <tr className="border-b">
                                <th className="px-3 py-2 text-left">코드</th>
                                <th className="px-3 py-2 text-left">부서명</th>
                                <th className="px-3 py-2 text-left">담당자</th>
                                <th className="px-3 py-2 text-left">연락처</th>
                                <th className="px-3 py-2 text-center">관리</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredDepartments.map((dept) => (
                                <tr
                                    key={dept.id}
                                    className={`border-b cursor-pointer hover:bg-surface-secondary ${selectedId === dept.id ? "bg-brand/10" : ""}`}
                                    onClick={() => handleEdit(dept)}
                                >
                                    <td className="px-3 py-2">{dept.code}</td>
                                    <td className="px-3 py-2 font-medium">
                                        <FolderTree className="mr-1 inline h-4 w-4 text-text-subtle" />
                                        {dept.name || "(신규)"}
                                    </td>
                                    <td className="px-3 py-2">{dept.manager}</td>
                                    <td className="px-3 py-2">{dept.tel}</td>
                                    <td className="px-3 py-2 text-center">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); handleDelete(dept.id); }}
                                            className="rounded p-1 hover:bg-red-100 hover:text-red-600"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="flex-1 overflow-auto p-4">
                    {selectedId && isEditing ? (
                        <div className="space-y-4">
                            <h3 className="font-medium">부서 정보</h3>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="mb-1 block text-sm font-medium">부서코드</label>
                                    <input type="text" value={editForm.code || ""} onChange={(e) => setEditForm({ ...editForm, code: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" />
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium">부서명 *</label>
                                    <input type="text" value={editForm.name || ""} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" />
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium">상위부서</label>
                                    <select value={editForm.parentId || ""} onChange={(e) => setEditForm({ ...editForm, parentId: e.target.value || null })} className="w-full rounded border px-3 py-2 text-sm">
                                        <option value="">없음</option>
                                        {departments.filter((d) => d.id !== selectedId).map((d) => (
                                            <option key={d.id} value={d.id}>{d.name}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium">담당자</label>
                                    <input type="text" value={editForm.manager || ""} onChange={(e) => setEditForm({ ...editForm, manager: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" />
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium">연락처</label>
                                    <input type="text" value={editForm.tel || ""} onChange={(e) => setEditForm({ ...editForm, tel: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" />
                                </div>
                                <div>
                                    <label className="mb-1 block text-sm font-medium">비고</label>
                                    <input type="text" value={editForm.note || ""} onChange={(e) => setEditForm({ ...editForm, note: e.target.value })} className="w-full rounded border px-3 py-2 text-sm" />
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex h-full items-center justify-center text-text-subtle">부서를 선택하거나 신규 버튼을 클릭하세요</div>
                    )}
                </div>
            </div>
        </div>
    );
}
