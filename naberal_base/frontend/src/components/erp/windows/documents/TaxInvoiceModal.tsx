"use client";

import React, { useRef, useState } from "react";
import { Printer, Phone, Settings, Search, Plus, Trash2 } from "lucide-react";
import { useERPData } from "@/contexts/ERPDataContext";

interface SalesItem {
    id: string;
    productName: string;
    spec: string;
    unit: string;
    quantity: number;
    unitPrice: number;
    supplyAmount: number;
    vatAmount: number;
    memo: string;
}

interface TaxInvoiceProps {
    isOpen: boolean;
    onClose: () => void;
    // 거래 정보
    transactionDate: string;
    documentNumber: string;
    // 공급자 정보
    supplierBusinessNumber: string;
    supplierCompanyName: string;
    supplierCeoName: string;
    supplierAddress: string;
    supplierBusinessType: string; // 업태
    supplierBusinessItem: string; // 종목
    // 공급받는자 정보
    customerBusinessNumber: string;
    customerCompanyName: string;
    customerCeoName: string;
    customerAddress: string;
    customerBusinessType: string;
    customerBusinessItem: string;
    // 상품 정보
    items: SalesItem[];
    // 합계
    totalSupplyAmount: number;
    totalVatAmount: number;
    totalAmount: number;
    // 발행 옵션
    onIssue?: () => void;
}

export default function TaxInvoiceModal({
    isOpen,
    onClose,
    transactionDate: initialTransactionDate,
    documentNumber: initialDocumentNumber,
    supplierBusinessNumber: initialSupplierBN,
    supplierCompanyName: initialSupplierName,
    supplierCeoName: initialSupplierCeo,
    supplierAddress: initialSupplierAddress,
    supplierBusinessType: initialSupplierType,
    supplierBusinessItem: initialSupplierItem,
    customerBusinessNumber: initialCustomerBN,
    customerCompanyName: initialCustomerName,
    customerCeoName: initialCustomerCeo,
    customerAddress: initialCustomerAddress,
    customerBusinessType: initialCustomerType,
    customerBusinessItem: initialCustomerItem,
    items: initialItems,
    totalSupplyAmount: initialTotalSupply,
    totalVatAmount: initialTotalVat,
    totalAmount: initialTotalAmount,
    onIssue,
}: TaxInvoiceProps) {
    const { customers } = useERPData();
    const printRef = useRef<HTMLDivElement>(null);
    const [showPageSettings, setShowPageSettings] = useState(false);
    const [pageSettings, setPageSettings] = useState({
        paperSize: "A4",
        orientation: "portrait",
        margin: "10mm",
    });

    // Editable state for customer info (사업자번호 검색으로 자동 채움)
    const [customerBN, setCustomerBN] = useState(initialCustomerBN);
    const [customerName, setCustomerName] = useState(initialCustomerName);
    const [customerCeo, setCustomerCeo] = useState(initialCustomerCeo);
    const [customerAddress, setCustomerAddress] = useState(initialCustomerAddress);
    const [customerType, setCustomerType] = useState(initialCustomerType);
    const [customerItem, setCustomerItem] = useState(initialCustomerItem);
    const [searchLoading, setSearchLoading] = useState(false);

    // Editable items with auto-calculation
    const [editableItems, setEditableItems] = useState<SalesItem[]>(
        initialItems.length > 0 ? initialItems : []
    );

    // Computed totals from editable items
    const computedTotalSupply = editableItems.reduce((sum, item) => sum + item.supplyAmount, 0);
    const computedTotalVat = editableItems.reduce((sum, item) => sum + item.vatAmount, 0);
    const computedTotalAmount = computedTotalSupply + computedTotalVat;

    // Use computed totals if items have been edited, otherwise use props
    const totalSupplyAmount = editableItems.length > 0 ? computedTotalSupply : initialTotalSupply;
    const totalVatAmount = editableItems.length > 0 ? computedTotalVat : initialTotalVat;
    const totalAmount = editableItems.length > 0 ? computedTotalAmount : initialTotalAmount;
    const items = editableItems.length > 0 ? editableItems : initialItems;

    if (!isOpen) return null;

    // 사업자번호 검색 핸들러 (ERPDataContext 사용)
    const handleBusinessNumberSearch = async () => {
        if (!customerBN.trim()) {
            alert("사업자번호를 입력해주세요.");
            return;
        }
        setSearchLoading(true);
        try {
            const cleaned = customerBN.replace(/-/g, "");
            const matched = customers.find(c =>
                c.business_number?.replace(/-/g, "") === cleaned
            ) || customers.find(c =>
                c.name.includes(customerBN) || c.code.includes(customerBN)
            );
            if (matched) {
                setCustomerName(matched.name || "");
                setCustomerCeo(matched.ceo_name || "");
                setCustomerAddress(matched.address || "");
                if (matched.business_number) {
                    setCustomerBN(matched.business_number);
                }
            } else {
                alert("일치하는 거래처를 찾을 수 없습니다.");
            }
        } finally {
            setSearchLoading(false);
        }
    };

    // 품목 추가 핸들러
    const handleAddItem = () => {
        const newItem: SalesItem = {
            id: Date.now().toString(),
            productName: "",
            spec: "",
            unit: "EA",
            quantity: 0,
            unitPrice: 0,
            supplyAmount: 0,
            vatAmount: 0,
            memo: "",
        };
        setEditableItems([...editableItems, newItem]);
    };

    // 품목 삭제 핸들러
    const handleRemoveItem = (itemId: string) => {
        setEditableItems(editableItems.filter((item) => item.id !== itemId));
    };

    // 품목 수정 핸들러 (수량 x 단가 = 공급가액, 세액 = 공급가액 x 10%)
    const handleItemChange = (itemId: string, field: keyof SalesItem, value: string | number) => {
        setEditableItems((prev) =>
            prev.map((item) => {
                if (item.id !== itemId) return item;
                const updated = { ...item, [field]: value };
                // 수량 또는 단가 변경 시 자동 계산
                if (field === "quantity" || field === "unitPrice") {
                    const qty = field === "quantity" ? Number(value) : updated.quantity;
                    const price = field === "unitPrice" ? Number(value) : updated.unitPrice;
                    updated.supplyAmount = qty * price;
                    updated.vatAmount = Math.round(updated.supplyAmount * 0.1);
                }
                return updated;
            })
        );
    };

    const handlePageSettings = () => {
        setShowPageSettings(true);
    };

    const handleFaxSend = () => {
        alert("Fax 전송 기능은 별도의 Fax 서비스 연동이 필요합니다.");
    };

    const handleElectronicInvoice = () => {
        if (onIssue) {
            onIssue();
        } else {
            alert("전자세금계산서 전송 기능은 홈택스 연동이 필요합니다.");
        }
    };

    const handlePrint = () => {
        const printContent = printRef.current;
        if (!printContent) return;

        const printWindow = window.open("", "_blank");
        if (!printWindow) return;

        printWindow.document.write(`
            <html>
                <head>
                    <title>전자세금계산서</title>
                    <style>
                        @page { size: A4; margin: 10mm; }
                        body { font-family: 'Malgun Gothic', sans-serif; font-size: 9px; }
                        table { border-collapse: collapse; width: 100%; }
                        th, td { border: 1px solid #1e3a8a; padding: 2px 4px; }
                        .red-invoice th, .red-invoice td { border-color: #dc2626; }
                        .page-break { page-break-after: always; }
                        @media print { .no-print { display: none; } }
                    </style>
                </head>
                <body>
                    ${printContent.innerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    };

    const handlePreview = () => {
        window.print();
    };

    const formatNumber = (num: number) => num.toLocaleString();

    // 사업자번호를 배열로 분리
    const splitBusinessNumber = (bn: string) => {
        const cleaned = bn.replace(/-/g, "");
        return cleaned.split("");
    };

    // 단일 세금계산서 렌더링
    const renderInvoice = (type: "supplier" | "customer") => {
        const isSupplier = type === "supplier";
        const borderColor = isSupplier ? "border-red-600" : "border-blue-800";
        const textColor = isSupplier ? "text-red-600" : "text-blue-800";
        const bgColor = isSupplier ? "bg-red-50" : "bg-blue-50";
        const headerBg = isSupplier ? "bg-red-100" : "bg-blue-100";
        const supplierBnDigits = splitBusinessNumber(initialSupplierBN);
        const customerBnDigits = splitBusinessNumber(customerBN);

        return (
            <div className={`p-4 bg-white mb-4`}>
                <table className={`w-full border-2 ${borderColor} text-[9px]`}>
                    {/* 제목 헤더 */}
                    <thead>
                        <tr>
                            <th colSpan={12} className={`border ${borderColor} ${headerBg} py-2`}>
                                <div className="flex justify-between items-center px-2">
                                    <span className={`${textColor} text-lg font-bold`}>
                                        세 금 계 산 서
                                        <span className="text-[10px] font-normal ml-2">(공급자보관용/공급받는자보관용)</span>
                                    </span>
                                    <div className="text-right">
                                        <div className={textColor}>책 번 호: 권</div>
                                        <div className={textColor}>일련번호: {initialDocumentNumber}</div>
                                    </div>
                                </div>
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {/* 공급자 정보 */}
                        <tr>
                            <td rowSpan={4} className={`border ${borderColor} ${bgColor} ${textColor} text-center font-bold w-8 writing-vertical`}>
                                공급자
                            </td>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center w-16`}>등록번호</td>
                            {supplierBnDigits.map((digit, i) => (
                                <td key={i} className={`border ${borderColor} text-center w-6 font-bold`}>
                                    {digit}
                                </td>
                            ))}
                            <td rowSpan={4} className={`border ${borderColor} ${bgColor} ${textColor} text-center font-bold w-8`}>
                                공급받는자
                            </td>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center w-16`}>등록번호</td>
                            {customerBnDigits.map((digit, i) => (
                                <td key={i} className={`border ${borderColor} text-center w-6 font-bold`}>
                                    {digit}
                                </td>
                            ))}
                        </tr>
                        <tr>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>상호</td>
                            <td colSpan={4} className={`border ${borderColor}`}>{initialSupplierName}</td>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>성명</td>
                            <td colSpan={4} className={`border ${borderColor}`}>{initialSupplierCeo}</td>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>상호</td>
                            <td colSpan={4} className={`border ${borderColor}`}>{customerName}</td>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>성명</td>
                            <td colSpan={4} className={`border ${borderColor}`}>{customerCeo}</td>
                        </tr>
                        <tr>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>주소</td>
                            <td colSpan={10} className={`border ${borderColor} text-[8px]`}>{initialSupplierAddress}</td>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>주소</td>
                            <td colSpan={10} className={`border ${borderColor} text-[8px]`}>{customerAddress}</td>
                        </tr>
                        <tr>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>업태</td>
                            <td colSpan={4} className={`border ${borderColor}`}>{initialSupplierType}</td>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>종목</td>
                            <td colSpan={4} className={`border ${borderColor}`}>{initialSupplierItem}</td>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>업태</td>
                            <td colSpan={4} className={`border ${borderColor}`}>{customerType}</td>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>종목</td>
                            <td colSpan={4} className={`border ${borderColor}`}>{customerItem}</td>
                        </tr>

                        {/* 작성일자 및 금액 */}
                        <tr className={headerBg}>
                            <td colSpan={2} className={`border ${borderColor} ${textColor} text-center`}>작성일자</td>
                            <td colSpan={10} className={`border ${borderColor}`}>
                                <div className="flex">
                                    {initialTransactionDate.split("-").map((part, i) => (
                                        <React.Fragment key={i}>
                                            {part.split("").map((digit, j) => (
                                                <span key={j} className="w-4 text-center border-r last:border-r-0">{digit}</span>
                                            ))}
                                            {i < 2 && <span className="px-1">{i === 0 ? "년" : "월"}</span>}
                                        </React.Fragment>
                                    ))}
                                    <span className="px-1">일</span>
                                </div>
                            </td>
                            <td colSpan={2} className={`border ${borderColor} ${textColor} text-center`}>공급가액</td>
                            <td colSpan={4} className={`border ${borderColor} text-right font-bold`}>{formatNumber(totalSupplyAmount)}</td>
                            <td colSpan={2} className={`border ${borderColor} ${textColor} text-center`}>세액</td>
                            <td colSpan={4} className={`border ${borderColor} text-right font-bold`}>{formatNumber(totalVatAmount)}</td>
                        </tr>

                        {/* 품목 헤더 */}
                        <tr className={bgColor}>
                            <td className={`border ${borderColor} ${textColor} text-center`}>월</td>
                            <td className={`border ${borderColor} ${textColor} text-center`}>일</td>
                            <td colSpan={6} className={`border ${borderColor} ${textColor} text-center`}>품목</td>
                            <td className={`border ${borderColor} ${textColor} text-center`}>규격</td>
                            <td className={`border ${borderColor} ${textColor} text-center`}>수량</td>
                            <td className={`border ${borderColor} ${textColor} text-center`}>단가</td>
                            <td colSpan={3} className={`border ${borderColor} ${textColor} text-center`}>공급가액</td>
                            <td colSpan={3} className={`border ${borderColor} ${textColor} text-center`}>세액</td>
                            <td colSpan={2} className={`border ${borderColor} ${textColor} text-center`}>비고</td>
                        </tr>

                        {/* 품목 목록 */}
                        {Array.from({ length: Math.max(4, items.length) }).map((_, index) => {
                            const item = items[index];
                            const date = new Date(initialTransactionDate);
                            return (
                                <tr key={index}>
                                    <td className={`border ${borderColor} text-center`}>{item ? date.getMonth() + 1 : ""}</td>
                                    <td className={`border ${borderColor} text-center`}>{item ? date.getDate() : ""}</td>
                                    <td colSpan={6} className={`border ${borderColor}`}>{item?.productName || ""}</td>
                                    <td className={`border ${borderColor}`}>{item?.spec || ""}</td>
                                    <td className={`border ${borderColor} text-right`}>{item ? formatNumber(item.quantity) : ""}</td>
                                    <td className={`border ${borderColor} text-right`}>{item ? formatNumber(item.unitPrice) : ""}</td>
                                    <td colSpan={3} className={`border ${borderColor} text-right`}>{item ? formatNumber(item.supplyAmount) : ""}</td>
                                    <td colSpan={3} className={`border ${borderColor} text-right`}>{item ? formatNumber(item.vatAmount) : ""}</td>
                                    <td colSpan={2} className={`border ${borderColor}`}></td>
                                </tr>
                            );
                        })}

                        {/* 합계 */}
                        <tr className={bgColor}>
                            <td colSpan={2} className={`border ${borderColor} ${textColor} text-center font-bold`}>합계</td>
                            <td colSpan={2} className={`border ${borderColor} ${textColor} text-center`}>현금</td>
                            <td colSpan={3} className={`border ${borderColor} text-right`}></td>
                            <td colSpan={2} className={`border ${borderColor} ${textColor} text-center`}>수표</td>
                            <td colSpan={3} className={`border ${borderColor} text-right`}></td>
                            <td colSpan={2} className={`border ${borderColor} ${textColor} text-center`}>어음</td>
                            <td colSpan={3} className={`border ${borderColor} text-right`}></td>
                            <td colSpan={2} className={`border ${borderColor} ${textColor} text-center`}>외상미수금</td>
                            <td colSpan={2} className={`border ${borderColor} text-right font-bold`}>{formatNumber(totalAmount)}</td>
                        </tr>

                        {/* 영수/청구 */}
                        <tr>
                            <td colSpan={10} className={`border ${borderColor} text-center`}>
                                위 금액을 <span className="font-bold">영수 / 청구</span> 함
                            </td>
                            <td colSpan={12} className={`border ${borderColor} ${textColor} text-right text-[8px]`}>
                                이 계산서는 영수 함
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        );
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="flex h-[90vh] w-[900px] flex-col rounded-lg bg-gray-200 shadow-xl">
                {/* 헤더 툴바 */}
                <div className="flex items-center justify-between border-b bg-gray-300 px-2 py-1">
                    <div className="flex items-center gap-1">
                        <span className="text-sm font-bold">세금계산서</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <button
                            onClick={handlePageSettings}
                            className="flex items-center gap-1 rounded border bg-white px-2 py-1 text-xs hover:bg-gray-100"
                        >
                            <Settings size={14} />
                            페이지설정
                        </button>
                        <button
                            onClick={handlePreview}
                            className="flex items-center gap-1 rounded border bg-white px-2 py-1 text-xs hover:bg-gray-100"
                        >
                            <Printer size={14} />
                            미리보기
                        </button>
                        <button
                            onClick={onClose}
                            className="flex items-center gap-1 rounded border bg-white px-2 py-1 text-xs hover:bg-gray-100"
                        >
                            취소
                        </button>
                        <button
                            onClick={handlePrint}
                            className="flex items-center gap-1 rounded border bg-white px-2 py-1 text-xs hover:bg-gray-100"
                        >
                            인쇄(P)
                        </button>
                        <button
                            onClick={handleElectronicInvoice}
                            className="flex items-center gap-1 rounded border bg-yellow-100 px-2 py-1 text-xs hover:bg-yellow-200"
                        >
                            전자세금계산서 전송
                        </button>
                        <button
                            onClick={handleFaxSend}
                            className="flex items-center gap-1 rounded border bg-white px-2 py-1 text-xs hover:bg-gray-100"
                        >
                            <Phone size={14} />
                            Fax 전송
                        </button>
                        <button
                            onClick={onClose}
                            className="flex items-center gap-1 rounded border bg-white px-2 py-1 text-xs hover:bg-gray-100"
                        >
                            종료(Esc)
                        </button>
                    </div>
                </div>

                {/* 사업자번호 검색 & 품목 추가 영역 */}
                <div className="border-b bg-gray-100 px-3 py-2 space-y-2">
                    {/* 사업자번호 검색 */}
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-medium w-20">공급받는자</span>
                        <input
                            type="text"
                            value={customerBN}
                            onChange={(e) => setCustomerBN(e.target.value)}
                            className="w-36 rounded border px-2 py-1 text-xs"
                            placeholder="사업자번호"
                        />
                        <button
                            onClick={handleBusinessNumberSearch}
                            disabled={searchLoading}
                            className="flex items-center gap-1 rounded border bg-white px-2 py-1 text-xs hover:bg-gray-50 disabled:opacity-50"
                        >
                            <Search size={12} />
                            {searchLoading ? "검색중..." : "검색"}
                        </button>
                        <span className="text-xs text-gray-500">|</span>
                        <span className="text-xs">상호: {customerName}</span>
                        <span className="text-xs text-gray-500">|</span>
                        <span className="text-xs">대표: {customerCeo}</span>
                    </div>
                    {/* 품목 추가 */}
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-medium w-20">품목 관리</span>
                        <button
                            onClick={handleAddItem}
                            className="flex items-center gap-1 rounded border bg-blue-50 px-2 py-1 text-xs text-blue-700 hover:bg-blue-100"
                        >
                            <Plus size={12} />
                            품목 추가
                        </button>
                        {editableItems.length > 0 && (
                            <span className="text-xs text-gray-500">
                                공급가액: {computedTotalSupply.toLocaleString()}원 | 세액: {computedTotalVat.toLocaleString()}원 | 합계: {computedTotalAmount.toLocaleString()}원
                            </span>
                        )}
                    </div>
                    {/* 품목 편집 테이블 */}
                    {editableItems.length > 0 && (
                        <div className="max-h-32 overflow-auto rounded border bg-white">
                            <table className="w-full text-xs">
                                <thead className="sticky top-0 bg-gray-50">
                                    <tr>
                                        <th className="px-2 py-1 text-left">품목명</th>
                                        <th className="px-2 py-1 text-left w-20">규격</th>
                                        <th className="px-2 py-1 text-right w-16">수량</th>
                                        <th className="px-2 py-1 text-right w-24">단가</th>
                                        <th className="px-2 py-1 text-right w-24">공급가액</th>
                                        <th className="px-2 py-1 text-right w-20">세액</th>
                                        <th className="px-2 py-1 w-8"></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {editableItems.map((item) => (
                                        <tr key={item.id} className="border-t hover:bg-gray-50">
                                            <td className="px-1 py-0.5">
                                                <input
                                                    type="text"
                                                    value={item.productName}
                                                    onChange={(e) => handleItemChange(item.id, "productName", e.target.value)}
                                                    className="w-full border-0 bg-transparent px-1 py-0.5 text-xs focus:ring-1 focus:ring-blue-300"
                                                    placeholder="품목명"
                                                />
                                            </td>
                                            <td className="px-1 py-0.5">
                                                <input
                                                    type="text"
                                                    value={item.spec}
                                                    onChange={(e) => handleItemChange(item.id, "spec", e.target.value)}
                                                    className="w-full border-0 bg-transparent px-1 py-0.5 text-xs focus:ring-1 focus:ring-blue-300"
                                                    placeholder="규격"
                                                />
                                            </td>
                                            <td className="px-1 py-0.5">
                                                <input
                                                    type="number"
                                                    value={item.quantity || ""}
                                                    onChange={(e) => handleItemChange(item.id, "quantity", Number(e.target.value))}
                                                    className="w-full border-0 bg-transparent px-1 py-0.5 text-xs text-right focus:ring-1 focus:ring-blue-300"
                                                    min={0}
                                                />
                                            </td>
                                            <td className="px-1 py-0.5">
                                                <input
                                                    type="number"
                                                    value={item.unitPrice || ""}
                                                    onChange={(e) => handleItemChange(item.id, "unitPrice", Number(e.target.value))}
                                                    className="w-full border-0 bg-transparent px-1 py-0.5 text-xs text-right focus:ring-1 focus:ring-blue-300"
                                                    min={0}
                                                />
                                            </td>
                                            <td className="px-1 py-0.5 text-right text-xs font-medium">
                                                {item.supplyAmount.toLocaleString()}
                                            </td>
                                            <td className="px-1 py-0.5 text-right text-xs">
                                                {item.vatAmount.toLocaleString()}
                                            </td>
                                            <td className="px-1 py-0.5 text-center">
                                                <button
                                                    onClick={() => handleRemoveItem(item.id)}
                                                    className="text-red-400 hover:text-red-600"
                                                >
                                                    <Trash2 size={12} />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                {/* 미리보기 영역 */}
                <div className="flex-1 overflow-auto bg-gray-400 p-4">
                    <div ref={printRef} className="mx-auto w-[700px] bg-white shadow-lg">
                        {/* 공급자용 (빨간색) */}
                        {renderInvoice("supplier")}
                        {/* 공급받는자용 (파란색) */}
                        {renderInvoice("customer")}
                    </div>
                </div>
            </div>

            {/* 페이지 설정 모달 */}
            {showPageSettings && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50">
                    <div className="w-[400px] rounded-lg bg-white shadow-xl">
                        <div className="border-b px-4 py-3">
                            <h3 className="text-lg font-semibold">페이지 설정</h3>
                        </div>
                        <div className="p-4 space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">용지 크기</label>
                                <select
                                    value={pageSettings.paperSize}
                                    onChange={(e) => setPageSettings({ ...pageSettings, paperSize: e.target.value })}
                                    className="w-full rounded border px-3 py-2 text-sm"
                                >
                                    <option value="A4">A4 (210 x 297mm)</option>
                                    <option value="A5">A5 (148 x 210mm)</option>
                                    <option value="Letter">Letter (8.5 x 11in)</option>
                                </select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">방향</label>
                                <select
                                    value={pageSettings.orientation}
                                    onChange={(e) => setPageSettings({ ...pageSettings, orientation: e.target.value })}
                                    className="w-full rounded border px-3 py-2 text-sm"
                                >
                                    <option value="portrait">세로</option>
                                    <option value="landscape">가로</option>
                                </select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">여백</label>
                                <select
                                    value={pageSettings.margin}
                                    onChange={(e) => setPageSettings({ ...pageSettings, margin: e.target.value })}
                                    className="w-full rounded border px-3 py-2 text-sm"
                                >
                                    <option value="5mm">좁게 (5mm)</option>
                                    <option value="10mm">보통 (10mm)</option>
                                    <option value="15mm">넓게 (15mm)</option>
                                    <option value="20mm">매우 넓게 (20mm)</option>
                                </select>
                            </div>
                        </div>
                        <div className="flex justify-end gap-2 border-t px-4 py-3">
                            <button
                                onClick={() => setShowPageSettings(false)}
                                className="rounded border px-4 py-2 text-sm hover:bg-gray-100"
                            >
                                취소
                            </button>
                            <button
                                onClick={() => setShowPageSettings(false)}
                                className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
                            >
                                확인
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
