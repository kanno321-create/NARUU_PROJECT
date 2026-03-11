"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import {
    ChevronDown,
    ChevronRight,
    Menu,
    Search,
    Building2,
    Users,
    Package,
    Store,
    ArrowRightLeft,
    Landmark,
    FileText,
    Receipt,
    Wallet,
    FileInput,
    FileOutput,
    FileCheck,
    MessageSquare,
    Printer,
    Settings,
    FileSpreadsheet,
    Calculator,
    Database,
    FolderSync,
    ClipboardList,
    ShoppingCart,
    FileEdit,
} from "lucide-react";

interface ERPSidebarProps {
    collapsed: boolean;
    onToggle: () => void;
    onMenuClick: (type: string, title: string) => void;
}

interface MenuItem {
    id: string;
    label: string;
    icon?: React.ElementType;
    children?: MenuItem[];
}

// 4그룹 경량화 메뉴 (보고서/명세서/원장은 AI 대화로 대체)
const menuStructure: MenuItem[] = [
    {
        id: "search",
        label: "전체검색",
        icon: Search,
    },
    {
        id: "basic-data",
        label: "기초자료",
        icon: Database,
        children: [
            { id: "company-info", label: "자사정보등록", icon: Building2 },
            { id: "employee", label: "사원정보등록", icon: Users },
            { id: "bank-account", label: "자사은행계좌등록", icon: Landmark },
            { id: "product", label: "상품등록", icon: Package },
            { id: "customer", label: "거래처등록", icon: Store },
        ],
    },
    {
        id: "carry-forward",
        label: "기초이월",
        icon: FolderSync,
        children: [
            { id: "inventory-carryover", label: "상품재고이월", icon: Package },
            { id: "receivable-payable-carryover", label: "미수미지급금이월", icon: ArrowRightLeft },
            { id: "bank-balance-carryover", label: "은행잔고이월", icon: Landmark },
        ],
    },
    {
        id: "voucher",
        label: "전표",
        icon: FileText,
        children: [
            { id: "sales-voucher", label: "매출전표", icon: FileOutput },
            { id: "purchase-voucher", label: "매입전표", icon: FileInput },
            { id: "collection-voucher", label: "수금전표", icon: Receipt },
            { id: "payment-voucher", label: "지급전표", icon: Wallet },
            { id: "income-expense-voucher", label: "입출금전표", icon: ArrowRightLeft },
        ],
    },
    {
        id: "operations",
        label: "업무관리",
        icon: ClipboardList,
        children: [
            { id: "inventory-adjust", label: "재고조정", icon: Calculator },
            { id: "estimate-management", label: "견적서관리", icon: FileEdit },
            { id: "order-management", label: "발주서관리", icon: ShoppingCart },
            { id: "statement-management", label: "거래명세표관리", icon: FileSpreadsheet },
            { id: "sales-tax-invoice", label: "매출세금계산서", icon: FileOutput },
            { id: "unissued-sales-list", label: "미발행 매출리스트", icon: ClipboardList },
            { id: "e-tax-invoice", label: "전자세금계산서", icon: FileCheck },
            { id: "sms-send", label: "문자발송", icon: MessageSquare },
            { id: "fax-send", label: "팩스발송", icon: Printer },
            { id: "settings", label: "환경설정", icon: Settings },
        ],
    },
];

export function ERPSidebar({ collapsed, onToggle, onMenuClick }: ERPSidebarProps) {
    const [expandedMenus, setExpandedMenus] = useState<Set<string>>(new Set(["basic-data"]));
    const [searchQuery, setSearchQuery] = useState("");

    const toggleMenu = (menuId: string) => {
        setExpandedMenus(prev => {
            const next = new Set(prev);
            if (next.has(menuId)) {
                next.delete(menuId);
            } else {
                next.add(menuId);
            }
            return next;
        });
    };

    const handleItemClick = (item: MenuItem) => {
        if (item.children) {
            toggleMenu(item.id);
        } else {
            onMenuClick(item.id, item.label);
        }
    };

    // 검색 필터링
    const filterMenuItems = (items: MenuItem[], query: string): MenuItem[] => {
        if (!query.trim()) return items;
        const lowerQuery = query.toLowerCase();
        return items.reduce<MenuItem[]>((acc, item) => {
            const matchesLabel = item.label.toLowerCase().includes(lowerQuery);
            const filteredChildren = item.children ? filterMenuItems(item.children, query) : [];
            if (matchesLabel || filteredChildren.length > 0) {
                acc.push({
                    ...item,
                    children: filteredChildren.length > 0 ? filteredChildren : item.children,
                });
            }
            return acc;
        }, []);
    };

    const filteredMenu = filterMenuItems(menuStructure, searchQuery);

    const renderMenuItem = (item: MenuItem, depth: number = 0) => {
        const hasChildren = item.children && item.children.length > 0;
        const isExpanded = expandedMenus.has(item.id) || searchQuery.trim().length > 0;
        const Icon = item.icon;

        return (
            <div key={item.id}>
                <button
                    onClick={() => handleItemClick(item)}
                    className={cn(
                        "flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-sm transition-colors hover:bg-brand/10",
                        depth > 0 && "ml-4",
                        !hasChildren && "hover:text-brand"
                    )}
                >
                    {hasChildren ? (
                        isExpanded ? (
                            <ChevronDown className="h-4 w-4 text-text-subtle" />
                        ) : (
                            <ChevronRight className="h-4 w-4 text-text-subtle" />
                        )
                    ) : (
                        <span className="w-4" />
                    )}
                    {Icon && <Icon className="h-4 w-4" />}
                    {!collapsed && <span className="flex-1 truncate">{item.label}</span>}
                </button>

                {hasChildren && isExpanded && !collapsed && (
                    <div className="mt-0.5 border-l border-border ml-3">
                        {item.children!.map(child => renderMenuItem(child, depth + 1))}
                    </div>
                )}
            </div>
        );
    };

    return (
        <div
            className={cn(
                "flex h-full flex-col border-r bg-surface transition-all duration-300",
                collapsed ? "w-[60px]" : "w-[260px]"
            )}
        >
            {/* 헤더 */}
            <div className="flex items-center justify-between border-b px-3 py-2">
                {!collapsed && (
                    <span className="text-sm font-semibold text-brand">ERP 메뉴</span>
                )}
                <button
                    onClick={onToggle}
                    className="rounded p-1 hover:bg-surface-secondary"
                >
                    <Menu className="h-5 w-5" />
                </button>
            </div>

            {/* 검색 */}
            {!collapsed && (
                <div className="border-b p-2">
                    <div className="relative">
                        <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-text-subtle" />
                        <input
                            type="text"
                            placeholder="메뉴 검색..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full rounded border border-surface-tertiary bg-surface py-1.5 pl-8 pr-3 text-sm text-text focus:border-brand focus:outline-none"
                        />
                    </div>
                </div>
            )}

            {/* 메뉴 목록 */}
            <div className="flex-1 overflow-y-auto p-2">
                {collapsed ? (
                    // 축소 모드: 아이콘만 표시
                    <div className="flex flex-col items-center gap-1">
                        {menuStructure.map(item => {
                            const Icon = item.icon;
                            return (
                                <button
                                    key={item.id}
                                    onClick={() => {
                                        if (!item.children) {
                                            onMenuClick(item.id, item.label);
                                        } else {
                                            onToggle(); // 사이드바 확장
                                        }
                                    }}
                                    className="rounded p-2 hover:bg-brand/10"
                                    title={item.label}
                                >
                                    {Icon && <Icon className="h-5 w-5" />}
                                </button>
                            );
                        })}
                    </div>
                ) : (
                    // 확장 모드: 전체 메뉴 표시
                    <div className="space-y-0.5">
                        {filteredMenu.map(item => renderMenuItem(item))}
                    </div>
                )}
            </div>

            {/* 하단 정보 */}
            {!collapsed && (
                <div className="border-t p-3 text-xs text-text-subtle">
                    <div className="flex items-center justify-between">
                        <span>(주)한국산업</span>
                        <span>v2.0</span>
                    </div>
                </div>
            )}
        </div>
    );
}
