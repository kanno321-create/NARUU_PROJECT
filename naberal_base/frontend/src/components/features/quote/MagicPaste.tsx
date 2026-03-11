"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Sparkles } from "lucide-react";

interface MagicPasteProps {
    onPaste: (text: string) => void;
}

export function MagicPaste({ onPaste }: MagicPasteProps) {
    const [text, setText] = React.useState("");
    const [isOpen, setIsOpen] = React.useState(false);

    const handleProcess = () => {
        if (text.trim()) {
            onPaste(text);
            setIsOpen(false);
            setText("");
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
                <Button
                    variant="outline"
                    className="gap-2 border-brand text-brand hover:bg-brand hover:text-white"
                >
                    <Sparkles className="h-4 w-4" />
                    AI 매직 페이스트
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>AI 매직 페이스트 ✨</DialogTitle>
                    <DialogDescription>
                        카톡 메시지, 엑셀, 메모장 내용을 복사해서 붙여넣으세요.
                        <br />
                        AI가 자동으로 견적서를 작성해드립니다.
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <Textarea
                        placeholder="예: 30분기 10개, 20분기 5개, 메인 100A 4P..."
                        className="h-[200px]"
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                    />
                </div>
                <DialogFooter>
                    <Button onClick={handleProcess} className="bg-brand hover:bg-brand-strong">
                        자동 입력 실행
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
