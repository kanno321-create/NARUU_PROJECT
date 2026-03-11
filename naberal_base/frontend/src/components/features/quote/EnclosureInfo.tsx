"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface EnclosureInfoProps {
    data: any;
    onChange: (data: any) => void;
}

export function EnclosureInfo({ data, onChange }: EnclosureInfoProps) {
    const [isOpen, setIsOpen] = React.useState(true);

    const locations = ["옥내", "옥외", "계량기함"];
    const types = ["기성함", "제작함"];
    const materials = [
        "STEEL 1.0T", "STEEL 1.6T",
        "SUS201 1.0T", "SUS201 1.2T", "SUS201 1.5T",
        "SUS304 1.2T", "SUS304 1.5T", "SUS304 2.0T"
    ];

    return (
        <Card className="mb-4">
            <CardHeader
                className="cursor-pointer flex-row items-center justify-between bg-surface-tertiary py-3"
                onClick={() => setIsOpen(!isOpen)}
            >
                <div className="flex items-center gap-4">
                    <CardTitle className="text-sm font-semibold">외함정보</CardTitle>
                    <div className="flex rounded-full bg-surface-secondary p-0.5" onClick={(e) => e.stopPropagation()}>
                        {locations.map((loc) => (
                            <button
                                key={loc}
                                className={cn(
                                    "rounded-full px-3 py-1 text-xs font-medium transition-all",
                                    data.location === loc
                                        ? "bg-brand text-white shadow-sm"
                                        : "text-text-subtle hover:text-text"
                                )}
                                onClick={() => onChange({ ...data, location: loc })}
                            >
                                {loc}
                            </button>
                        ))}
                    </div>
                </div>
                {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </CardHeader>
            {isOpen && (
                <CardContent className="pt-4">
                    <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-text-subtle">함체타입</label>
                            <select
                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                value={data.type || ""}
                                onChange={(e) => onChange({ ...data, type: e.target.value })}
                            >
                                <option value="">선택하세요</option>
                                {types.map((t) => (
                                    <option key={t} value={t}>{t}</option>
                                ))}
                            </select>
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-text-subtle">재질</label>
                            <select
                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                value={data.material || ""}
                                onChange={(e) => onChange({ ...data, material: e.target.value })}
                            >
                                <option value="">선택하세요</option>
                                {materials.map((m) => (
                                    <option key={m} value={m}>{m}</option>
                                ))}
                            </select>
                        </div>
                        <div className="col-span-2 space-y-1">
                            <label className="text-xs font-medium text-text-subtle">특이사항</label>
                            <Input
                                placeholder="특이사항을 입력하세요"
                                value={data.specialRequest || ""}
                                onChange={(e) => onChange({ ...data, specialRequest: e.target.value })}
                            />
                        </div>
                    </div>
                </CardContent>
            )}
        </Card>
    );
}
