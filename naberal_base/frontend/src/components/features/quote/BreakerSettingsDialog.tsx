import React from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface BreakerSettingsDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function BreakerSettingsDialog({ open, onOpenChange }: BreakerSettingsDialogProps) {
    const [settings, setSettings] = React.useState({
        mainBrand: "",
        mainGrade: "economy",
        branchBrand: "",
        branchGrade: "economy",
        accessoryBrand: "",
    });

    const handleSave = () => {
        // Save settings to global store
        onOpenChange(false);
        alert("차단기 설정이 저장되었습니다.");
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>차단기 설정</DialogTitle>
                </DialogHeader>
                <div className="py-4">
                    <p className="mb-4 text-sm text-text-subtle">
                        차단기 브랜드별 세부 설정을 할 수 있습니다.
                    </p>
                    <div className="space-y-4">
                        {/* Main Breaker Settings */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                    메인 차단기 등급
                                </label>
                                <select
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                    value={settings.mainGrade}
                                    onChange={(e) => setSettings({ ...settings, mainGrade: e.target.value })}
                                >
                                    <option value="economy">경제형</option>
                                    <option value="standard">표준형</option>
                                </select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                    메인 차단기 브랜드
                                </label>
                                <select
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                    value={settings.mainBrand}
                                    onChange={(e) => setSettings({ ...settings, mainBrand: e.target.value })}
                                >
                                    <option value="">선택하세요</option>
                                    <option value="상도차단기">상도차단기</option>
                                    <option value="LS산전">LS산전</option>
                                    <option value="대륙차단기">대륙차단기</option>
                                    <option value="비츠로">비츠로</option>
                                </select>
                            </div>
                        </div>

                        {/* Branch Breaker Settings */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                    분기 차단기 등급
                                </label>
                                <select
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                    value={settings.branchGrade}
                                    onChange={(e) => setSettings({ ...settings, branchGrade: e.target.value })}
                                >
                                    <option value="economy">경제형</option>
                                    <option value="standard">표준형</option>
                                </select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                    분기 차단기 브랜드
                                </label>
                                <select
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                    value={settings.branchBrand}
                                    onChange={(e) => setSettings({ ...settings, branchBrand: e.target.value })}
                                >
                                    <option value="">선택하세요</option>
                                    <option value="상도차단기">상도차단기</option>
                                    <option value="LS산전">LS산전</option>
                                    <option value="대륙차단기">대륙차단기</option>
                                    <option value="비츠로">비츠로</option>
                                </select>
                            </div>
                        </div>

                        {/* Accessory Settings */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                부속자재 기본 브랜드
                            </label>
                            <select
                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                value={settings.accessoryBrand}
                                onChange={(e) => setSettings({ ...settings, accessoryBrand: e.target.value })}
                            >
                                <option value="">선택하세요</option>
                                <option value="한국산업">한국산업</option>
                                <option value="삼성">삼성</option>
                                <option value="LG">LG</option>
                                <option value="기타">기타</option>
                            </select>
                        </div>
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        취소
                    </Button>
                    <Button onClick={handleSave} className="bg-brand hover:bg-brand-strong">
                        저장
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
