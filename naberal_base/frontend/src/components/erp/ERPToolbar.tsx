"use client";

import React from "react";
import { cn } from "@/lib/utils";
import {
    Store,
    Package,
    FileOutput,
    FileInput,
    Wallet,
    Receipt,
    ArrowRightLeft,
    AlertCircle,
    FileCheck,
    MessageSquare,
    Printer,
    Truck,
    Settings,
    Calculator,
} from "lucide-react";

interface ERPToolbarProps {
    onToolClick: (type: string, title: string) => void;
}

interface ToolbarItem {
    id: string;
    label: string;
    icon: React.ElementType;
    color?: string;
}

// 상단 툴바 버튼 정의 (탭별기능.txt 기반)
const toolbarItems: ToolbarItem[] = [
    { id: "customer-info", label: "거래처정보", icon: Store, color: "text-blue-600" },
    { id: "product-info", label: "상품정보", icon: Package, color: "text-green-600" },
    { id: "sales-voucher", label: "매출전표", icon: FileOutput, color: "text-emerald-600" },
    { id: "purchase-voucher", label: "매입전표", icon: FileInput, color: "text-orange-600" },
    { id: "payment-voucher", label: "지급전표", icon: Wallet, color: "text-red-600" },
    { id: "collection-voucher", label: "수금전표", icon: Receipt, color: "text-purple-600" },
    { id: "income-expense", label: "입출금(경비)", icon: ArrowRightLeft, color: "text-cyan-600" },
    { id: "receivable-alert", label: "미수금리스트", icon: AlertCircle, color: "text-rose-600" },
    { id: "tax-invoice", label: "전자세금계산서", icon: FileCheck, color: "text-indigo-600" },
    { id: "sms-send", label: "문자발송", icon: MessageSquare, color: "text-pink-600" },
    { id: "fax-send", label: "팩스발송", icon: Printer, color: "text-gray-600" },
    { id: "logistics", label: "물류송장", icon: Truck, color: "text-sky-600" },
    { id: "settings", label: "환경설정", icon: Settings, color: "text-slate-600" },
    { id: "salary", label: "급여대장", icon: Calculator, color: "text-violet-600" },
];

export function ERPToolbar({ onToolClick }: ERPToolbarProps) {
    return (
        <div className="flex items-center gap-1 border-b bg-surface px-2 py-1 overflow-x-auto">
            {toolbarItems.map((item) => {
                const Icon = item.icon;
                return (
                    <button
                        key={item.id}
                        onClick={() => onToolClick(item.id, item.label)}
                        className={cn(
                            "flex flex-col items-center gap-0.5 rounded px-2 py-1.5 transition-colors hover:bg-brand/10 min-w-[60px]",
                            "group"
                        )}
                        title={item.label}
                    >
                        <div className={cn(
                            "flex h-8 w-8 items-center justify-center rounded-lg bg-surface-secondary transition-colors group-hover:bg-brand/20",
                        )}>
                            <Icon className={cn("h-5 w-5", item.color)} />
                        </div>
                        <span className="text-[10px] text-text-subtle group-hover:text-brand whitespace-nowrap">
                            {item.label}
                        </span>
                    </button>
                );
            })}

            {/* 구분선 및 빠른 검색 */}
            <div className="mx-2 h-10 w-px bg-border" />
            <div className="flex items-center gap-2 ml-auto">
                <input
                    type="text"
                    placeholder="전체검색..."
                    className="rounded border border-surface-tertiary bg-surface px-3 py-1.5 text-sm text-text focus:border-brand focus:outline-none w-[180px]"
                />
                <button
                    className="rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-strong"
                    onClick={() => onToolClick("search", "전체검색")}
                >
                    검색
                </button>
            </div>
        </div>
    );
}
