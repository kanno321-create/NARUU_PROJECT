"use client";

import React, { useState, useMemo } from "react";
import { Plus, Search, Trash2, Save, Printer, FileText, Eye, X } from "lucide-react";
import { PrintPreviewModal } from "../../common/PrintPreviewModal";
import { DraggableModal } from "../../common/DraggableModal";
import { useERPData } from "@/contexts/ERPDataContext";

interface SalesSlipItem {
    id: string;
    productCode: string;
    productName: string;
    quantity: number;
    unitPrice: number;
    amount: number;
    vat: number;
    total: number;
}

interface SalesSlip {
    id: string;
    slipNo: string;
    date: string;
    customerCode: string;
    customerName: string;
    items: SalesSlipItem[];
    supplyAmount: number;
    vatAmount: number;
    totalAmount: number;
    note: string;
}

export function SalesSlipWindow() {
    // ERPDataContext에서 데이터 가져오기
    const { customers, customersLoading, products, sales, addSale } = useERPData();

    const [slipNo, setSlipNo] = useState(`SL${new Date().toISOString().slice(0, 10).replace(/-/g, "")}-001`);
    const [slipDate, setSlipDate] = useState(new Date().toISOString().split("T")[0]);
    const [customerCode, setCustomerCode] = useState("");
    const [customerName, setCustomerName] = useState("");
    const [items, setItems] = useState<SalesSlipItem[]>([
        { id: "1", productCode: "", productName: "", quantity: 0, unitPrice: 0, amount: 0, vat: 0, total: 0 },
    ]);
    const [note, setNote] = useState("");
    const [savedSlips, setSavedSlips] = useState<SalesSlip[]>([]);
    const [showPrintPreview, setShowPrintPreview] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    // 거래처 검색 팝업 상태
    const [showCustomerSearch, setShowCustomerSearch] = useState(false);
    const [customerSearchQuery, setCustomerSearchQuery] = useState("");
    // 상품 검색 팝업 상태
    const [showProductSearch, setShowProductSearch] = useState(false);
    const [productSearchQuery, setProductSearchQuery] = useState("");
    const [activeProductRowId, setActiveProductRowId] = useState<string | null>(null);

    // ERPDataContext의 customers를 변환하여 사용
    const registeredCustomers = useMemo(() =>
        customers.map(c => ({
            code: c.code,
            name: c.name,
            type: c.customer_type,
            phone: c.phone || "",
        })),
        [customers]
    );

    // 거래처 검색 결과 필터링
    const filteredCustomers = useMemo(() =>
        registeredCustomers.filter(
            (c) =>
                c.name.includes(customerSearchQuery) ||
                c.code.includes(customerSearchQuery) ||
                c.phone.includes(customerSearchQuery)
        ),
        [registeredCustomers, customerSearchQuery]
    );

    // ERPDataContext의 products를 사용한 상품 목록
    const registeredProducts = useMemo(() =>
        products.map(p => ({
            code: p.code,
            name: p.name,
            spec: p.specification || "",
            unit: p.unit || "EA",
            price: p.selling_price || 0,
        })),
        [products]
    );

    // 상품 검색 결과 필터링
    const filteredProducts = useMemo(() =>
        registeredProducts.filter(
            (p) =>
                p.name.includes(productSearchQuery) ||
                p.code.includes(productSearchQuery) ||
                p.spec.includes(productSearchQuery)
        ),
        [registeredProducts, productSearchQuery]
    );

    // 거래처 선택 핸들러
    const handleSelectCustomer = (customer: { code: string; name: string; type: string; phone: string }) => {
        setCustomerCode(customer.code);
        setCustomerName(customer.name);
        setShowCustomerSearch(false);
        setCustomerSearchQuery("");
    };

    // 상품 선택 핸들러
    const handleSelectProduct = (product: { code: string; name: string; spec: string; unit: string; price: number }) => {
        if (activeProductRowId) {
            setItems(items.map(item => {
                if (item.id === activeProductRowId) {
                    const updated = {
                        ...item,
                        productCode: product.code,
                        productName: product.name,
                        unitPrice: product.price,
                    };
                    // 수량이 있으면 금액 재계산
                    if (updated.quantity > 0) {
                        updated.amount = updated.quantity * updated.unitPrice;
                        updated.vat = Math.round(updated.amount * 0.1);
                        updated.total = updated.amount + updated.vat;
                    }
                    return updated;
                }
                return item;
            }));
        }
        setShowProductSearch(false);
        setProductSearchQuery("");
        setActiveProductRowId(null);
    };

    // 상품코드 F2 검색 핸들러
    const handleProductCodeKeyDown = (e: React.KeyboardEvent, itemId: string) => {
        if (e.key === "F2") {
            e.preventDefault();
            setActiveProductRowId(itemId);
            setShowProductSearch(true);
        } else if (e.key === "Enter") {
            // 코드로 상품 자동 검색
            const item = items.find(i => i.id === itemId);
            if (item) {
                const found = registeredProducts.find(p => p.code === item.productCode);
                if (found) {
                    handleSelectProduct(found);
                }
            }
        }
    };

    // 상품 검색 버튼 클릭 핸들러
    const openProductSearch = (itemId: string) => {
        setActiveProductRowId(itemId);
        setShowProductSearch(true);
    };

    // 거래처 코드 입력 시 F2 검색 또는 자동 완성
    const handleCustomerCodeKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "F2") {
            e.preventDefault();
            setShowCustomerSearch(true);
        } else if (e.key === "Enter") {
            // 코드로 거래처 자동 검색
            const found = registeredCustomers.find((c) => c.code === customerCode);
            if (found) {
                setCustomerName(found.name);
            }
        }
    };

    const handleAddRow = () => {
        setItems([...items, { id: String(Date.now()), productCode: "", productName: "", quantity: 0, unitPrice: 0, amount: 0, vat: 0, total: 0 }]);
    };

    const handleRemoveRow = (id: string) => {
        if (items.length > 1) setItems(items.filter((item) => item.id !== id));
    };

    const handleItemChange = (id: string, field: keyof SalesSlipItem, value: string | number) => {
        setItems(items.map((item) => {
            if (item.id === id) {
                const updated = { ...item, [field]: value };
                if (field === "quantity" || field === "unitPrice") {
                    updated.amount = updated.quantity * updated.unitPrice;
                    updated.vat = Math.round(updated.amount * 0.1);
                    updated.total = updated.amount + updated.vat;
                }
                return updated;
            }
            return item;
        }));
    };

    const totalSupply = items.reduce((sum, item) => sum + item.amount, 0);
    const totalVat = items.reduce((sum, item) => sum + item.vat, 0);
    const grandTotal = items.reduce((sum, item) => sum + item.total, 0);

    // 저장 기능
    const handleSave = () => {
        // 유효성 검사
        if (!customerCode || !customerName) {
            alert("거래처 정보를 입력해주세요.");
            return;
        }

        const validItems = items.filter(item => item.productCode || item.productName || item.quantity > 0);
        if (validItems.length === 0) {
            alert("품목 정보를 입력해주세요.");
            return;
        }

        const newSlip: SalesSlip = {
            id: String(Date.now()),
            slipNo,
            date: slipDate,
            customerCode,
            customerName,
            items: validItems,
            supplyAmount: totalSupply,
            vatAmount: totalVat,
            totalAmount: grandTotal,
            note,
        };

        // 기존 전표 수정 또는 새 전표 추가
        const existingIndex = savedSlips.findIndex(s => s.slipNo === slipNo);
        if (existingIndex >= 0) {
            const updated = [...savedSlips];
            updated[existingIndex] = newSlip;
            setSavedSlips(updated);
            alert(`전표 ${slipNo}이(가) 수정되었습니다.`);
        } else {
            setSavedSlips([...savedSlips, newSlip]);
            alert(`전표 ${slipNo}이(가) 저장되었습니다.`);
        }
    };

    // 신규 전표
    const handleNew = () => {
        const nextNo = `SL${new Date().toISOString().slice(0, 10).replace(/-/g, "")}-${String(savedSlips.length + 1).padStart(3, "0")}`;
        setSlipNo(nextNo);
        setSlipDate(new Date().toISOString().split("T")[0]);
        setCustomerCode("");
        setCustomerName("");
        setItems([{ id: "1", productCode: "", productName: "", quantity: 0, unitPrice: 0, amount: 0, vat: 0, total: 0 }]);
        setNote("");
    };

    // 인쇄미리보기 데이터 준비
    const printColumns = [
        { key: "productCode", label: "품목코드", width: "100px" },
        { key: "productName", label: "품목명", width: "200px" },
        { key: "quantity", label: "수량", width: "80px", align: "right" as const },
        { key: "unitPrice", label: "단가", width: "100px", align: "right" as const },
        { key: "amount", label: "공급가액", width: "100px", align: "right" as const },
        { key: "vat", label: "부가세", width: "80px", align: "right" as const },
        { key: "total", label: "합계", width: "100px", align: "right" as const },
    ];

    const printData = items.filter(item => item.productCode || item.productName || item.quantity > 0);

    const printHeaderInfo = [
        { label: "전표번호", value: slipNo },
        { label: "거래처코드", value: customerCode },
        { label: "거래처명", value: customerName },
    ];

    const printSummary = [
        { label: "공급가액", value: totalSupply },
        { label: "부가세", value: totalVat },
        { label: "합계금액", value: grandTotal },
    ];

    return (
        <div className="flex h-full flex-col">
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button
                    onClick={handleSave}
                    className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"
                >
                    <Save className="h-4 w-4" />저장
                </button>
                <button
                    onClick={handleNew}
                    className="flex items-center gap-1 rounded bg-gray-600 px-3 py-1.5 text-sm text-white hover:bg-gray-700"
                >
                    <FileText className="h-4 w-4" />신규
                </button>
                <button
                    onClick={() => setShowPrintPreview(true)}
                    className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"
                >
                    <Eye className="h-4 w-4" />인쇄미리보기
                </button>
                <button
                    onClick={() => window.print()}
                    className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"
                >
                    <Printer className="h-4 w-4" />인쇄
                </button>
                <div className="ml-auto relative">
                    <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-subtle" />
                    <input type="text" placeholder="전표 검색..." className="rounded border py-1.5 pl-8 pr-3 text-sm focus:border-brand focus:outline-none" />
                </div>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    <div className="grid grid-cols-5 gap-4">
                        <div>
                            <label className="mb-1 block text-sm font-medium">전표번호</label>
                            <input type="text" value={slipNo} readOnly className="w-full rounded border bg-gray-100 px-3 py-2 text-sm" />
                        </div>
                        <div>
                            <label className="mb-1 block text-sm font-medium">전표일자</label>
                            <input type="date" value={slipDate} onChange={(e) => setSlipDate(e.target.value)} className="w-full rounded border px-3 py-2 text-sm" />
                        </div>
                        <div>
                            <label className="mb-1 block text-sm font-medium">거래처코드</label>
                            <div className="flex gap-1">
                                <input
                                    type="text"
                                    value={customerCode}
                                    onChange={(e) => setCustomerCode(e.target.value)}
                                    onKeyDown={handleCustomerCodeKeyDown}
                                    className="flex-1 rounded border px-3 py-2 text-sm"
                                    placeholder="F2: 검색"
                                />
                                <button
                                    onClick={() => setShowCustomerSearch(true)}
                                    className="rounded bg-blue-500 px-2 py-2 text-white hover:bg-blue-600"
                                    title="거래처 검색 (F2)"
                                >
                                    <Search className="h-4 w-4" />
                                </button>
                            </div>
                        </div>
                        <div className="col-span-2">
                            <label className="mb-1 block text-sm font-medium">거래처명</label>
                            <input type="text" value={customerName} onChange={(e) => setCustomerName(e.target.value)} className="w-full rounded border px-3 py-2 text-sm bg-gray-50" readOnly />
                        </div>
                    </div>

                    <div className="rounded border">
                        <table className="w-full text-sm">
                            <thead className="bg-surface">
                                <tr className="border-b">
                                    <th className="w-10 px-2 py-2 text-center">No</th>
                                    <th className="px-2 py-2 text-left">품목코드</th>
                                    <th className="px-2 py-2 text-left">품목명</th>
                                    <th className="w-20 px-2 py-2 text-right">수량</th>
                                    <th className="w-28 px-2 py-2 text-right">단가</th>
                                    <th className="w-28 px-2 py-2 text-right">공급가액</th>
                                    <th className="w-24 px-2 py-2 text-right">부가세</th>
                                    <th className="w-28 px-2 py-2 text-right">합계</th>
                                    <th className="w-10 px-2 py-2"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item, idx) => (
                                    <tr key={item.id} className="border-b">
                                        <td className="px-2 py-1 text-center text-text-subtle">{idx + 1}</td>
                                        <td className="px-1 py-1">
                                            <div className="flex gap-1">
                                                <input
                                                    type="text"
                                                    value={item.productCode}
                                                    onChange={(e) => handleItemChange(item.id, "productCode", e.target.value)}
                                                    onKeyDown={(e) => handleProductCodeKeyDown(e, item.id)}
                                                    className="w-full rounded border px-2 py-1 text-sm"
                                                    placeholder="F2: 검색"
                                                />
                                                <button
                                                    onClick={() => openProductSearch(item.id)}
                                                    className="rounded bg-blue-500 px-1 text-white hover:bg-blue-600"
                                                    title="상품 검색 (F2)"
                                                >
                                                    <Search className="h-3 w-3" />
                                                </button>
                                            </div>
                                        </td>
                                        <td className="px-1 py-1"><input type="text" value={item.productName} readOnly className="w-full rounded border bg-gray-50 px-2 py-1 text-sm" /></td>
                                        <td className="px-1 py-1"><input type="number" value={item.quantity} onChange={(e) => handleItemChange(item.id, "quantity", Number(e.target.value))} className="w-full rounded border px-2 py-1 text-sm text-right" /></td>
                                        <td className="px-1 py-1"><input type="number" value={item.unitPrice} onChange={(e) => handleItemChange(item.id, "unitPrice", Number(e.target.value))} className="w-full rounded border px-2 py-1 text-sm text-right" /></td>
                                        <td className="px-2 py-1 text-right">{item.amount.toLocaleString()}</td>
                                        <td className="px-2 py-1 text-right">{item.vat.toLocaleString()}</td>
                                        <td className="px-2 py-1 text-right font-medium">{item.total.toLocaleString()}</td>
                                        <td className="px-1 py-1"><button onClick={() => handleRemoveRow(item.id)} className="rounded p-1 hover:bg-red-100 hover:text-red-600"><Trash2 className="h-4 w-4" /></button></td>
                                    </tr>
                                ))}
                            </tbody>
                            <tfoot className="bg-surface-secondary">
                                <tr>
                                    <td colSpan={5} className="px-2 py-2"><button onClick={handleAddRow} className="flex items-center gap-1 text-sm text-brand hover:text-brand-dark"><Plus className="h-4 w-4" />행 추가</button></td>
                                    <td className="px-2 py-2 text-right font-medium">{totalSupply.toLocaleString()}</td>
                                    <td className="px-2 py-2 text-right font-medium">{totalVat.toLocaleString()}</td>
                                    <td className="px-2 py-2 text-right font-bold text-brand">{grandTotal.toLocaleString()}</td>
                                    <td></td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>

                    <div><label className="mb-1 block text-sm font-medium">비고</label><textarea value={note} onChange={(e) => setNote(e.target.value)} rows={2} className="w-full rounded border px-3 py-2 text-sm" placeholder="메모 입력..." /></div>
                </div>
            </div>

            {/* 인쇄 미리보기 모달 */}
            <PrintPreviewModal
                isOpen={showPrintPreview}
                onClose={() => setShowPrintPreview(false)}
                title="매출전표"
                subtitle="Sales Slip"
                date={slipDate}
                columns={printColumns}
                data={printData}
                headerInfo={printHeaderInfo}
                summary={printSummary}
                note={note}
            />

            {/* 거래처 검색 팝업 - 드래그 가능, 메인창 밖으로 이동 가능 */}
            <DraggableModal
                isOpen={showCustomerSearch}
                onClose={() => {
                    setShowCustomerSearch(false);
                    setCustomerSearchQuery("");
                }}
                title="거래처 검색"
                width="450px"
                showOverlay={false}
            >
                <div className="p-4">
                    <div className="mb-3 flex gap-2">
                        <input
                            type="text"
                            value={customerSearchQuery}
                            onChange={(e) => setCustomerSearchQuery(e.target.value)}
                            placeholder="거래처명, 코드, 전화번호로 검색..."
                            className="flex-1 rounded border px-3 py-2 text-sm"
                            autoFocus
                        />
                        <button
                            onClick={() => setCustomerSearchQuery("")}
                            className="rounded border px-3 py-2 text-sm hover:bg-gray-100"
                        >
                            초기화
                        </button>
                    </div>
                    <div className="max-h-64 overflow-auto rounded border">
                        <table className="w-full text-sm">
                            <thead className="sticky top-0 bg-gray-100">
                                <tr>
                                    <th className="border-b px-3 py-2 text-left">코드</th>
                                    <th className="border-b px-3 py-2 text-left">거래처명</th>
                                    <th className="border-b px-3 py-2 text-left">구분</th>
                                    <th className="border-b px-3 py-2 text-left">전화번호</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredCustomers.length === 0 ? (
                                    <tr>
                                        <td colSpan={4} className="px-3 py-8 text-center text-gray-500">
                                            검색 결과가 없습니다.
                                        </td>
                                    </tr>
                                ) : (
                                    filteredCustomers.map((customer) => (
                                        <tr
                                            key={customer.code}
                                            onClick={() => handleSelectCustomer(customer)}
                                            className="cursor-pointer hover:bg-blue-50"
                                        >
                                            <td className="border-b px-3 py-2">{customer.code}</td>
                                            <td className="border-b px-3 py-2 font-medium">{customer.name}</td>
                                            <td className="border-b px-3 py-2">{customer.type}</td>
                                            <td className="border-b px-3 py-2">{customer.phone}</td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                    <div className="mt-3 text-xs text-gray-500">
                        거래처를 클릭하여 선택하세요. ({filteredCustomers.length}건)
                    </div>
                </div>
            </DraggableModal>

            {/* 상품 검색 팝업 - 드래그 가능, 메인창 밖으로 이동 가능 */}
            <DraggableModal
                isOpen={showProductSearch}
                onClose={() => {
                    setShowProductSearch(false);
                    setProductSearchQuery("");
                    setActiveProductRowId(null);
                }}
                title="상품 검색"
                width="550px"
                showOverlay={false}
            >
                <div className="p-4">
                    <div className="mb-3 flex gap-2">
                        <input
                            type="text"
                            value={productSearchQuery}
                            onChange={(e) => setProductSearchQuery(e.target.value)}
                            placeholder="상품명, 코드, 규격으로 검색..."
                            className="flex-1 rounded border px-3 py-2 text-sm"
                            autoFocus
                        />
                        <button
                            onClick={() => setProductSearchQuery("")}
                            className="rounded border px-3 py-2 text-sm hover:bg-gray-100"
                        >
                            초기화
                        </button>
                    </div>
                    <div className="max-h-64 overflow-auto rounded border">
                        <table className="w-full text-sm">
                            <thead className="sticky top-0 bg-gray-100">
                                <tr>
                                    <th className="border-b px-3 py-2 text-left">코드</th>
                                    <th className="border-b px-3 py-2 text-left">상품명</th>
                                    <th className="border-b px-3 py-2 text-left">규격</th>
                                    <th className="border-b px-3 py-2 text-left">단위</th>
                                    <th className="border-b px-3 py-2 text-right">단가</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredProducts.length === 0 ? (
                                    <tr>
                                        <td colSpan={5} className="px-3 py-8 text-center text-gray-500">
                                            검색 결과가 없습니다.
                                        </td>
                                    </tr>
                                ) : (
                                    filteredProducts.map((product) => (
                                        <tr
                                            key={product.code}
                                            onClick={() => handleSelectProduct(product)}
                                            className="cursor-pointer hover:bg-blue-50"
                                        >
                                            <td className="border-b px-3 py-2">{product.code}</td>
                                            <td className="border-b px-3 py-2 font-medium">{product.name}</td>
                                            <td className="border-b px-3 py-2">{product.spec}</td>
                                            <td className="border-b px-3 py-2">{product.unit}</td>
                                            <td className="border-b px-3 py-2 text-right">{product.price.toLocaleString()}원</td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                    <div className="mt-3 text-xs text-gray-500">
                        상품을 클릭하여 선택하세요. ({filteredProducts.length}건)
                    </div>
                </div>
            </DraggableModal>
        </div>
    );
}
