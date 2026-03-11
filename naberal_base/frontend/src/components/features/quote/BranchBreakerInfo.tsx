"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChevronDown, ChevronUp, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface BranchBreakerItem {
    type: string;
    poles: string;
    capacity: string;
    quantity: number;
    brand?: string;
}

interface BranchBreakerInfoProps {
    data: BranchBreakerItem[];
    onChange: (data: BranchBreakerItem[]) => void;
}

export function BranchBreakerInfo({ data, onChange }: BranchBreakerInfoProps) {
    const [isOpen, setIsOpen] = React.useState(true);
    const [newItem, setNewItem] = React.useState<BranchBreakerItem>({
        type: "MCCB",
        poles: "2P",
        capacity: "20A",
        quantity: 1,
        brand: "",
    });

    const types = ["MCCB", "ELB"];
    const poles = ["2P", "3P", "4P"];
    const capacities = [
        "15A", "20A", "30A", "40A", "50A", "60A", "75A", "100A",
        "125A", "150A", "175A", "200A", "225A", "250A", "300A"
    ];
    const brands = ["상도차단기", "LS산전", "대륙차단기", "비츠로"];

    const handleAdd = () => {
        // 중복 차단기 확인: 같은 type + poles + capacity + brand가 이미 존재하면 수량만 증가
        const existingIndex = data.findIndex(
            (item) =>
                item.type === newItem.type &&
                item.poles === newItem.poles &&
                item.capacity === newItem.capacity &&
                (item.brand || "") === (newItem.brand || "")
        );

        if (existingIndex >= 0) {
            const updated = [...data];
            updated[existingIndex] = {
                ...updated[existingIndex],
                quantity: updated[existingIndex].quantity + newItem.quantity,
            };
            onChange(updated);
        } else {
            onChange([...data, { ...newItem }]);
        }

        // 모든 필드 초기화 (CEO 요청: 추가 버튼 누르면 처음으로 되돌아가기)
        setNewItem({
            type: "MCCB",
            poles: "2P",
            capacity: "20A",
            quantity: 1,
            brand: "",
        });
    };

    const handleRemove = (index: number) => {
        const newData = [...data];
        newData.splice(index, 1);
        onChange(newData);
    };

    return (
        <Card className="mb-4">
            <CardHeader
                className="cursor-pointer flex-row items-center justify-between bg-surface-tertiary py-3"
                onClick={() => setIsOpen(!isOpen)}
            >
                <CardTitle className="text-sm font-semibold">분기 차단기</CardTitle>
                {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </CardHeader>
            {isOpen && (
                <CardContent className="pt-4">
                    {/* Input Row */}
                    <div className="mb-4 flex items-end gap-2">
                        <div className="w-[80px] space-y-1">
                            <label className="text-xs font-medium text-text-subtle">종류</label>
                            <select
                                className="flex h-9 w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                                value={newItem.type}
                                onChange={(e) => setNewItem({ ...newItem, type: e.target.value })}
                            >
                                {types.map((t) => <option key={t} value={t}>{t}</option>)}
                            </select>
                        </div>
                        <div className="w-[60px] space-y-1">
                            <label className="text-xs font-medium text-text-subtle">극수</label>
                            <select
                                className="flex h-9 w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                                value={newItem.poles}
                                onChange={(e) => setNewItem({ ...newItem, poles: e.target.value })}
                            >
                                {poles.map((p) => <option key={p} value={p}>{p}</option>)}
                            </select>
                        </div>
                        <div className="w-[80px] space-y-1">
                            <label className="text-xs font-medium text-text-subtle">용량</label>
                            <select
                                className="flex h-9 w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                                value={newItem.capacity}
                                onChange={(e) => setNewItem({ ...newItem, capacity: e.target.value })}
                            >
                                {capacities.map((c) => <option key={c} value={c}>{c}</option>)}
                            </select>
                        </div>
                        <div className="w-[90px] space-y-1">
                            <label className="text-xs font-medium text-text-subtle">브랜드</label>
                            <select
                                className="flex h-9 w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                                value={newItem.brand}
                                onChange={(e) => setNewItem({ ...newItem, brand: e.target.value })}
                            >
                                <option value="">미지정</option>
                                {brands.map((b) => <option key={b} value={b}>{b}</option>)}
                            </select>
                        </div>
                        <div className="w-[60px] space-y-1">
                            <label className="text-xs font-medium text-text-subtle">수량</label>
                            <Input
                                type="number"
                                className="h-9 px-2 text-center text-xs"
                                min={1}
                                value={newItem.quantity}
                                onChange={(e) => setNewItem({ ...newItem, quantity: parseInt(e.target.value) || 1 })}
                            />
                        </div>
                        <Button size="sm" className="h-9 w-[60px]" onClick={handleAdd}>
                            추가
                        </Button>
                    </div>

                    {/* List */}
                    <div className="max-h-[200px] overflow-y-auto rounded-md border bg-surface">
                        {data.length === 0 ? (
                            <div className="p-4 text-center text-sm text-text-subtle italic">
                                추가된 분기 차단기가 없습니다
                            </div>
                        ) : (
                            data.map((item, idx) => (
                                <div
                                    key={idx}
                                    className="flex items-center justify-between border-b px-3 py-2 text-sm last:border-0 hover:bg-surface-tertiary"
                                >
                                    <div className="flex gap-2">
                                        <span className={cn("font-medium", item.type === "ELB" ? "text-red-500" : "text-text")}>
                                            {item.type}
                                        </span>
                                        <span>{item.poles}</span>
                                        <span>{item.capacity}</span>
                                        {item.brand && (
                                            <span className="text-xs text-blue-600">[{item.brand}]</span>
                                        )}
                                        <span className="text-text-subtle">x {item.quantity}</span>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-6 w-6 text-text-subtle hover:text-red-500"
                                        onClick={() => handleRemove(idx)}
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>
                            ))
                        )}
                    </div>
                </CardContent>
            )}
        </Card>
    );
}
