"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp, Plus, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface MainBreakerInfoProps {
    data: any[];
    onChange: (data: any[]) => void;
    onSettingsClick?: () => void;
}

export function MainBreakerInfo({ data, onChange, onSettingsClick }: MainBreakerInfoProps) {
    const [isOpen, setIsOpen] = React.useState(true);

    const poles = ["2P", "3P", "4P"];
    const capacities = [
        "15A", "20A", "30A", "40A", "50A", "60A", "75A", "100A",
        "125A", "150A", "175A", "200A", "225A", "250A", "300A",
        "350A", "400A", "500A", "600A", "700A", "800A", "1000A", "1200A"
    ];

    const handleAdd = () => {
        onChange([...data, { type: "MCCB", poles: "4P", capacity: "100A" }]);
    };

    const handleRemove = (index: number) => {
        const newData = [...data];
        newData.splice(index, 1);
        onChange(newData);
    };

    const handleChange = (index: number, field: string, value: any) => {
        const newData = [...data];
        newData[index] = { ...newData[index], [field]: value };
        onChange(newData);
    };

    return (
        <Card className="mb-4">
            <CardHeader
                className="cursor-pointer flex-row items-center justify-between bg-surface-tertiary py-3"
                onClick={() => setIsOpen(!isOpen)}
            >
                <div className="flex items-center gap-4">
                    <CardTitle className="text-sm font-semibold">메인 차단기 ({data.length})</CardTitle>
                    <Button
                        size="sm"
                        variant="outline"
                        className="h-7 text-xs"
                        onClick={(e) => {
                            e.stopPropagation();
                            onSettingsClick?.();
                        }}
                    >
                        설정
                    </Button>
                </div>
                {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </CardHeader>
            {isOpen && (
                <CardContent className="pt-4">
                    <div className="flex flex-col gap-4">
                        {data.map((item, index) => (
                            <div key={index} className="relative rounded-md border border-border p-3">
                                <div className="mb-3 flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-surface-tertiary text-xs font-bold text-text-subtle">
                                            {index + 1}
                                        </span>
                                        <div className="flex gap-1">
                                            <button
                                                className={cn(
                                                    "rounded px-2 py-1 text-xs font-medium transition-all",
                                                    item.type === "MCCB"
                                                        ? "bg-brand text-white"
                                                        : "bg-surface-secondary text-text-subtle hover:bg-surface-tertiary"
                                                )}
                                                onClick={() => handleChange(index, "type", "MCCB")}
                                            >
                                                MCCB
                                            </button>
                                            <button
                                                className={cn(
                                                    "rounded px-2 py-1 text-xs font-medium transition-all",
                                                    item.type === "ELB"
                                                        ? "bg-red-500 text-white"
                                                        : "bg-surface-secondary text-text-subtle hover:bg-surface-tertiary"
                                                )}
                                                onClick={() => handleChange(index, "type", "ELB")}
                                            >
                                                ELB
                                            </button>
                                        </div>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-6 w-6 text-text-subtle hover:text-red-500"
                                        onClick={() => handleRemove(index)}
                                    >
                                        <Trash2 className="h-3 w-3" />
                                    </Button>
                                </div>

                                <div className="grid grid-cols-2 gap-2">
                                    <div className="space-y-1">
                                        <label className="text-[10px] font-medium text-text-subtle">극수</label>
                                        <select
                                            className="flex h-8 w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                                            value={item.poles || ""}
                                            onChange={(e) => handleChange(index, "poles", e.target.value)}
                                        >
                                            <option value="">선택</option>
                                            {poles.map((p) => (
                                                <option key={p} value={p}>{p}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-[10px] font-medium text-text-subtle">용량</label>
                                        <select
                                            className="flex h-8 w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                                            value={item.capacity || ""}
                                            onChange={(e) => handleChange(index, "capacity", e.target.value)}
                                        >
                                            <option value="">선택</option>
                                            {capacities.map((c) => (
                                                <option key={c} value={c}>{c}</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                            </div>
                        ))}

                        <Button
                            variant="outline"
                            className="w-full border-dashed text-text-subtle hover:border-brand hover:text-brand"
                            onClick={handleAdd}
                        >
                            <Plus className="mr-2 h-4 w-4" />
                            메인 차단기 추가
                        </Button>
                    </div>
                </CardContent>
            )}
        </Card>
    );
}
