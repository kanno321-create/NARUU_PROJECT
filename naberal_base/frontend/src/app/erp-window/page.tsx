"use client";

import React, { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ERPDataProvider } from "@/contexts/ERPDataContext";

// getWindowContent를 재사용하기 위해 동적 임포트
import dynamic from "next/dynamic";

const ERPWindowContent = dynamic(
    () => import("@/components/erp/ERPWindowContent"),
    { ssr: false }
);

function ERPWindowInner() {
    const searchParams = useSearchParams();
    const type = searchParams.get("type") || "generic";
    const title = searchParams.get("title") || type;

    return (
        <ERPDataProvider>
            <div className="h-screen w-screen overflow-hidden bg-surface flex flex-col">
                {/* 타이틀 바 (드래그 영역 없음 - OS 타이틀바 사용) */}
                <div className="flex h-8 items-center border-b bg-surface-secondary px-3 shrink-0">
                    <span className="text-sm font-medium text-text truncate">{title}</span>
                </div>
                {/* 컨텐츠 */}
                <div className="flex-1 overflow-auto">
                    <ERPWindowContent type={type} />
                </div>
            </div>
        </ERPDataProvider>
    );
}

export default function ERPWindowPage() {
    return (
        <Suspense fallback={<div className="flex h-screen items-center justify-center">로딩 중...</div>}>
            <ERPWindowInner />
        </Suspense>
    );
}
