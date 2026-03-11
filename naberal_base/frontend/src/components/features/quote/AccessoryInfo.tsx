"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChevronDown, ChevronUp, Trash2 } from "lucide-react";

interface AccessoryInfoProps {
    data: any[];
    onChange: (data: any[]) => void;
}

export function AccessoryInfo({ data, onChange }: AccessoryInfoProps) {
    const [isOpen, setIsOpen] = React.useState(true);

    // Magnet State
    const [magnet, setMagnet] = React.useState({
        model: "",
        timer: "NO",
        pbl: "NO",
        quantity: 1,
    });

    // Other Accessory State
    const [accessory, setAccessory] = React.useState({
        category: "",
        detail: "",
        spec: "",
        quantity: 1,
    });

    const magnets = [
        "MC-9", "MC-12", "MC-18", "MC-22", "MC-32",
        "MC-40", "MC-50", "MC-65", "MC-75", "MC-85",
        "MC-100", "MC-130", "MC-150"
    ];

    const handleAddMagnet = () => {
        if (!magnet.model) return;
        const newItem = {
            type: "MAGNET",
            name: `마그네트 ${magnet.model}`,
            details: `Timer:${magnet.timer}, PBL:${magnet.pbl}`,
            quantity: magnet.quantity,
        };
        onChange([...data, newItem]);
        setMagnet({ ...magnet, quantity: 1 });
    };

    const handleAddAccessory = () => {
        if (!accessory.category || !accessory.detail) return;

        const categoryMap: Record<string, string> = {
            meter: "계량기", "3ct": "3CT", timer: "타이머", eocr: "EOCR", condenser: "콘덴서", etc: "기타"
        };

        const newItem = {
            type: "ACCESSORY",
            name: `${categoryMap[accessory.category] || accessory.category} ${accessory.detail}`,
            details: accessory.spec || "-",
            quantity: accessory.quantity,
        };
        onChange([...data, newItem]);
        setAccessory({ category: "", detail: "", spec: "", quantity: 1 });
    };

    const getAccessoryOptions = (category: string) => {
        const options: Record<string, { details: string[], specs?: string[] | Record<string, string[]> }> = {
            'meter': {
                details: ['단상', '삼상'],
                specs: ['전자식', '기계식']
            },
            '3ct': {
                details: ['100/5A', '200/5A', '300/5A', '400/5A', '500/5A'],
                specs: ['부스바용', '환CT']
            },
            'timer': {
                details: ['일몰일출', '입력/출력'],
                specs: ['20A', '30A', '40A', '50A', '75A', '100A']
            },
            'eocr': {
                details: ['일반형', 'ZCT내장형'],
                specs: ['22', '32', '40', '60']
            },
            'condenser': {
                details: ['단상', '삼상'],
                specs: {
                    '단상': [
                        '10uF', '15uF', '20uF', '30uF', '40uF', '50uF', '75uF', '100uF', '150uF', '200uF', '250uF', '300uF', '400uF', '500uF', '1000uF',
                        '10KVA', '15KVA', '20KVA', '25KVA', '30KVA', '40KVA', '50KVA'
                    ],
                    '삼상': [
                        '10uF', '15uF', '20uF', '30uF', '40uF', '50uF', '75uF', '100uF', '200uF', '250uF', '300uF', '400uF', '500uF',
                        '10KVA', '15KVA', '20KVA', '25KVA', '30KVA', '35KVA', '40KVA', '50KVA', '60KVA', '75KVA', '100KVA'
                    ]
                }
            },
            'etc': {
                details: ['3구콘센트', '2구콘센트', '분전반소화기', 'TR', 'F/S', '수위센서', '단자커버', '단자피커버', '외함검침창'],
                specs: ['표준', '특수']
            }
        };
        return options[category] || { details: [], specs: [] };
    };

    const getAccessorySpecs = (category: string, detail: string): string[] => {
        const options = getAccessoryOptions(category);
        if (category === 'condenser') {
            const specs = options.specs as Record<string, string[]>;
            return specs[detail] || [];
        }
        return (options.specs as string[]) || [];
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
                <CardTitle className="text-sm font-semibold">부속자재</CardTitle>
                {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </CardHeader>
            {isOpen && (
                <CardContent className="pt-4">
                    {/* Magnet Section */}
                    <div className="mb-4 flex items-end gap-2 border-b pb-4">
                        <div className="w-[100px] space-y-1">
                            <label className="text-xs font-medium text-text-subtle">마그네트</label>
                            <select
                                className="flex h-9 w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                                value={magnet.model}
                                onChange={(e) => setMagnet({ ...magnet, model: e.target.value })}
                            >
                                <option value="">선택</option>
                                {magnets.map((m) => <option key={m} value={m}>{m}</option>)}
                            </select>
                        </div>
                        <div className="w-[80px] space-y-1">
                            <label className="text-xs font-medium text-text-subtle">타이머</label>
                            <select
                                className="flex h-9 w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                                value={magnet.timer}
                                onChange={(e) => setMagnet({ ...magnet, timer: e.target.value })}
                            >
                                <option value="YES">포함</option>
                                <option value="NO">제외</option>
                            </select>
                        </div>
                        <div className="w-[80px] space-y-1">
                            <label className="text-xs font-medium text-text-subtle">PBL</label>
                            <select
                                className="flex h-9 w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                                value={magnet.pbl}
                                onChange={(e) => setMagnet({ ...magnet, pbl: e.target.value })}
                            >
                                <option value="YES">포함</option>
                                <option value="NO">제외</option>
                            </select>
                        </div>
                        <div className="w-[60px] space-y-1">
                            <label className="text-xs font-medium text-text-subtle">수량</label>
                            <Input
                                type="number"
                                className="h-9 px-2 text-center text-xs"
                                min={1}
                                value={magnet.quantity}
                                onChange={(e) => setMagnet({ ...magnet, quantity: parseInt(e.target.value) || 1 })}
                            />
                        </div>
                        <Button size="sm" className="h-9 w-[60px]" onClick={handleAddMagnet}>
                            추가
                        </Button>
                    </div>

                    {/* Other Accessories Section */}
                    <div className="mb-4 flex items-end gap-2 border-b pb-4">
                        <div className="w-[100px] space-y-1">
                            <label className="text-xs font-medium text-text-subtle">부속자재</label>
                            <select
                                className="flex h-9 w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                                value={accessory.category}
                                onChange={(e) => {
                                    setAccessory({ ...accessory, category: e.target.value, detail: "", spec: "" });
                                }}
                            >
                                <option value="">선택</option>
                                <option value="meter">계량기</option>
                                <option value="3ct">3CT</option>
                                <option value="timer">타이머</option>
                                <option value="eocr">EOCR</option>
                                <option value="condenser">콘덴서</option>
                                <option value="etc">기타</option>
                            </select>
                        </div>
                        <div className="w-[100px] space-y-1">
                            <label className="text-xs font-medium text-text-subtle">세부선택</label>
                            <select
                                className="flex h-9 w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                                value={accessory.detail}
                                onChange={(e) => setAccessory({ ...accessory, detail: e.target.value, spec: "" })}
                                disabled={!accessory.category}
                            >
                                <option value="">선택</option>
                                {accessory.category && getAccessoryOptions(accessory.category).details.map((d) => (
                                    <option key={d} value={d}>{d}</option>
                                ))}
                            </select>
                        </div>
                        <div className="w-[100px] space-y-1">
                            <label className="text-xs font-medium text-text-subtle">규격</label>
                            <select
                                className="flex h-9 w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                                value={accessory.spec}
                                onChange={(e) => setAccessory({ ...accessory, spec: e.target.value })}
                                disabled={!accessory.detail}
                            >
                                <option value="">선택</option>
                                {accessory.category && accessory.detail && getAccessorySpecs(accessory.category, accessory.detail).map((s) => (
                                    <option key={s} value={s}>{s}</option>
                                ))}
                            </select>
                        </div>
                        <div className="w-[60px] space-y-1">
                            <label className="text-xs font-medium text-text-subtle">수량</label>
                            <Input
                                type="number"
                                className="h-9 px-2 text-center text-xs"
                                min={1}
                                value={accessory.quantity}
                                onChange={(e) => setAccessory({ ...accessory, quantity: parseInt(e.target.value) || 1 })}
                            />
                        </div>
                        <Button size="sm" className="h-9 w-[60px]" onClick={handleAddAccessory}>
                            추가
                        </Button>
                    </div>

                    {/* List */}
                    <div className="max-h-[200px] overflow-y-auto rounded-md border bg-surface">
                        {data.length === 0 ? (
                            <div className="p-4 text-center text-sm text-text-subtle italic">
                                추가된 부속자재가 없습니다
                            </div>
                        ) : (
                            data.map((item, idx) => (
                                <div
                                    key={idx}
                                    className="flex items-center justify-between border-b px-3 py-2 text-sm last:border-0 hover:bg-surface-tertiary"
                                >
                                    <div className="flex gap-2">
                                        <span className="font-medium">{item.name}</span>
                                        <span className="text-text-subtle text-xs">({item.details})</span>
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
