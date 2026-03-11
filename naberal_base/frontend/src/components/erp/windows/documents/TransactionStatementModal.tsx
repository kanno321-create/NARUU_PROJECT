"use client";

import React, { useRef, useState } from "react";
import { X, Printer, FileText, Phone, Settings } from "lucide-react";

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

interface TransactionStatementProps {
    isOpen: boolean;
    onClose: () => void;
    mode: "standard" | "full"; // standard: 2장, full: 전장(1장)
    // 거래 정보
    transactionDate: string;
    documentNumber: string;
    // 공급자 정보
    supplierBusinessNumber: string;
    supplierCompanyName: string;
    supplierCeoName: string;
    supplierAddress: string;
    supplierPhone: string;
    supplierFax: string;
    // 공급받는자 정보
    customerBusinessNumber: string;
    customerCompanyName: string;
    customerCeoName: string;
    customerAddress: string;
    customerPhone: string;
    customerFax: string;
    // 상품 정보
    items: SalesItem[];
    // 합계
    totalSupplyAmount: number;
    totalVatAmount: number;
    totalAmount: number;
}

export default function TransactionStatementModal({
    isOpen,
    onClose,
    mode,
    transactionDate,
    documentNumber,
    supplierBusinessNumber,
    supplierCompanyName,
    supplierCeoName,
    supplierAddress,
    supplierPhone,
    supplierFax,
    customerBusinessNumber,
    customerCompanyName,
    customerCeoName,
    customerAddress,
    customerPhone,
    customerFax,
    items,
    totalSupplyAmount,
    totalVatAmount,
    totalAmount,
}: TransactionStatementProps) {
    const printRef = useRef<HTMLDivElement>(null);
    const [showPageSettings, setShowPageSettings] = useState(false);
    const [pageSettings, setPageSettings] = useState({
        paperSize: "A4",
        orientation: "portrait",
        margin: "10mm",
    });

    if (!isOpen) return null;

    // 페이지 설정 핸들러
    const handlePageSettings = () => {
        setShowPageSettings(true);
    };

    // 취소 핸들러
    const handleCancel = () => {
        onClose();
    };

    // Fax 전송 핸들러
    const handleFaxSend = () => {
        alert("Fax 전송 기능은 별도의 Fax 서비스 연동이 필요합니다.\n고객사 Fax: " + customerFax);
    };

    const handlePrint = () => {
        const printContent = printRef.current;
        if (!printContent) return;

        const printWindow = window.open("", "_blank");
        if (!printWindow) return;

        printWindow.document.write(`
            <html>
                <head>
                    <title>거래명세서</title>
                    <style>
                        @page { size: A4; margin: 10mm; }
                        body { font-family: 'Malgun Gothic', sans-serif; font-size: 10px; }
                        table { border-collapse: collapse; width: 100%; }
                        th, td { border: 1px solid #dc2626; padding: 2px 4px; }
                        .header { color: #dc2626; font-weight: bold; text-align: center; }
                        .blue-header { color: #2563eb; }
                        .blue-border th, .blue-border td { border-color: #2563eb; }
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

    const formatNumber = (num: number) => num.toLocaleString();
    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`;
    };

    // 단일 명세서 렌더링
    const renderStatement = (type: "supplier" | "customer", isFullPage: boolean = false) => {
        const isSupplier = type === "supplier";
        const borderColor = isSupplier ? "border-red-600" : "border-blue-600";
        const textColor = isSupplier ? "text-red-600" : "text-blue-600";
        const bgColor = isSupplier ? "bg-red-50" : "bg-blue-50";
        const rowCount = isFullPage ? 20 : 8;

        return (
            <div className={`p-4 bg-white ${isFullPage ? "" : "mb-4"}`}>
                <table className={`w-full border-2 ${borderColor} text-[10px]`}>
                    {/* 헤더 */}
                    <thead>
                        <tr>
                            <th colSpan={2} className={`border ${borderColor} p-1`}>
                                <div className="flex items-center justify-between">
                                    <span className={textColor}>거래일자</span>
                                    <span>{formatDate(transactionDate)}</span>
                                </div>
                            </th>
                            <th colSpan={4} className={`border ${borderColor} p-2 ${textColor} text-xl font-bold`}>
                                거래명세서
                                <div className={`text-[10px] font-normal ${textColor}`}>
                                    ({isSupplier ? "공급자보관용" : "공급받는자보관용"})
                                </div>
                                <div className="text-[10px] font-normal text-gray-600">1/1 페이지</div>
                            </th>
                            <th colSpan={2} className={`border ${borderColor} p-1`}>
                                <div className={`${bgColor} p-1`}>
                                    <div className={textColor}>인</div>
                                </div>
                            </th>
                        </tr>
                        <tr>
                            <th colSpan={2} className={`border ${borderColor} p-1`}>
                                <div className="flex items-center justify-between">
                                    <span className={textColor}>문서번호</span>
                                    <span>{documentNumber}</span>
                                </div>
                            </th>
                            <th colSpan={6} className={`border ${borderColor}`}></th>
                        </tr>
                    </thead>
                    <tbody>
                        {/* 공급자/공급받는자 정보 */}
                        <tr>
                            <td rowSpan={4} className={`border ${borderColor} ${bgColor} text-center w-6 ${textColor} font-bold`}>
                                <span className="writing-vertical">공급자</span>
                            </td>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center w-12`}>등록번호</td>
                            <td colSpan={2} className={`border ${borderColor} text-center font-bold`}>{supplierBusinessNumber}</td>
                            <td rowSpan={4} className={`border ${borderColor} ${bgColor} text-center w-6 ${textColor} font-bold`}>
                                <span className="writing-vertical">공급받는자</span>
                            </td>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center w-12`}>등록번호</td>
                            <td colSpan={2} className={`border ${borderColor} text-center font-bold`}>{customerBusinessNumber}</td>
                        </tr>
                        <tr>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>상호</td>
                            <td className={`border ${borderColor}`}>{supplierCompanyName}</td>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>성명</td>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>상호</td>
                            <td className={`border ${borderColor}`}>{customerCompanyName}</td>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>성명</td>
                        </tr>
                        <tr>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>주소</td>
                            <td colSpan={2} className={`border ${borderColor} text-[9px]`}>{supplierAddress}</td>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>주소</td>
                            <td colSpan={2} className={`border ${borderColor} text-[9px]`}>{customerAddress}</td>
                        </tr>
                        <tr>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>TEL</td>
                            <td className={`border ${borderColor}`}>{supplierPhone}</td>
                            <td className={`border ${borderColor}`}>{supplierFax}</td>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>TEL</td>
                            <td className={`border ${borderColor}`}>{customerPhone}</td>
                            <td className={`border ${borderColor}`}>{customerFax}</td>
                        </tr>
                        {/* 상품 헤더 */}
                        <tr className={`${bgColor}`}>
                            <td className={`border ${borderColor} ${textColor} text-center`}>NO</td>
                            <td className={`border ${borderColor} ${textColor} text-center`}>품목코드</td>
                            <td className={`border ${borderColor} ${textColor} text-center`}>상품명</td>
                            <td className={`border ${borderColor} ${textColor} text-center`}>규격</td>
                            <td className={`border ${borderColor} ${textColor} text-center`}>단위</td>
                            <td className={`border ${borderColor} ${textColor} text-center`}>수량</td>
                            <td className={`border ${borderColor} ${textColor} text-center`}>단가</td>
                            <td className={`border ${borderColor} ${textColor} text-center`}>공급가액</td>
                        </tr>
                        {/* 상품 목록 */}
                        {Array.from({ length: rowCount }).map((_, index) => {
                            const item = items[index];
                            return (
                                <tr key={index} className={index % 2 === 1 ? bgColor : ""}>
                                    <td className={`border ${borderColor} text-center`}>{item ? index + 1 : ""}</td>
                                    <td className={`border ${borderColor}`}>{item?.id?.slice(0, 8) || ""}</td>
                                    <td className={`border ${borderColor}`}>{item?.productName || ""}</td>
                                    <td className={`border ${borderColor}`}>{item?.spec || ""}</td>
                                    <td className={`border ${borderColor} text-center`}>{item?.unit || ""}</td>
                                    <td className={`border ${borderColor} text-right`}>{item ? formatNumber(item.quantity) : ""}</td>
                                    <td className={`border ${borderColor} text-right`}>{item ? formatNumber(item.unitPrice) : ""}</td>
                                    <td className={`border ${borderColor} text-right`}>{item ? formatNumber(item.supplyAmount) : ""}</td>
                                </tr>
                            );
                        })}
                        {/* 합계 */}
                        <tr className={bgColor}>
                            <td colSpan={2} className={`border ${borderColor} ${textColor} text-center font-bold`}>합계</td>
                            <td className={`border ${borderColor} ${textColor} text-center`}>세액</td>
                            <td className={`border ${borderColor} text-right font-bold`}>{formatNumber(totalVatAmount)}</td>
                            <td className={`border ${borderColor}`}></td>
                            <td className={`border ${borderColor} ${textColor} text-center`}>합계금액</td>
                            <td colSpan={2} className={`border ${borderColor} text-right font-bold`}>{formatNumber(totalAmount)}</td>
                        </tr>
                        {/* 결제/인수자 */}
                        <tr>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>결제</td>
                            <td colSpan={3} className={`border ${borderColor}`}>₩</td>
                            <td className={`border ${borderColor} ${bgColor} ${textColor} text-center`}>인수자</td>
                            <td colSpan={3} className={`border ${borderColor}`}></td>
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
                        <span className="text-sm font-bold">거래명세서{mode === "full" ? "(전장)" : ""}</span>
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
                            onClick={handlePrint}
                            className="flex items-center gap-1 rounded border bg-white px-2 py-1 text-xs hover:bg-gray-100"
                        >
                            <Printer size={14} />
                            인쇄
                        </button>
                        <button
                            onClick={handleCancel}
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

                {/* 미리보기 영역 */}
                <div className="flex-1 overflow-auto bg-gray-400 p-4">
                    <div ref={printRef} className="mx-auto w-[700px] bg-white shadow-lg">
                        {mode === "full" ? (
                            // 전장 모드: 1장
                            renderStatement("supplier", true)
                        ) : (
                            // 일반 모드: 2장 (공급자용 + 공급받는자용)
                            <>
                                {renderStatement("supplier")}
                                {renderStatement("customer")}
                            </>
                        )}
                    </div>
                </div>

                {/* 페이지 설정 모달 */}
                {showPageSettings && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                        <div className="w-80 rounded-lg bg-white p-4 shadow-xl">
                            <h3 className="mb-4 text-sm font-bold">페이지 설정</h3>
                            <div className="space-y-3">
                                <div>
                                    <label className="text-xs text-gray-600">용지 크기</label>
                                    <select
                                        value={pageSettings.paperSize}
                                        onChange={(e) => setPageSettings({ ...pageSettings, paperSize: e.target.value })}
                                        className="mt-1 w-full rounded border p-1 text-sm"
                                    >
                                        <option value="A4">A4</option>
                                        <option value="A3">A3</option>
                                        <option value="Letter">Letter</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-xs text-gray-600">방향</label>
                                    <select
                                        value={pageSettings.orientation}
                                        onChange={(e) => setPageSettings({ ...pageSettings, orientation: e.target.value })}
                                        className="mt-1 w-full rounded border p-1 text-sm"
                                    >
                                        <option value="portrait">세로</option>
                                        <option value="landscape">가로</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-xs text-gray-600">여백</label>
                                    <select
                                        value={pageSettings.margin}
                                        onChange={(e) => setPageSettings({ ...pageSettings, margin: e.target.value })}
                                        className="mt-1 w-full rounded border p-1 text-sm"
                                    >
                                        <option value="5mm">좁게 (5mm)</option>
                                        <option value="10mm">보통 (10mm)</option>
                                        <option value="15mm">넓게 (15mm)</option>
                                        <option value="20mm">매우 넓게 (20mm)</option>
                                    </select>
                                </div>
                            </div>
                            <div className="mt-4 flex justify-end gap-2">
                                <button
                                    onClick={() => setShowPageSettings(false)}
                                    className="rounded border px-3 py-1 text-xs hover:bg-gray-100"
                                >
                                    취소
                                </button>
                                <button
                                    onClick={() => setShowPageSettings(false)}
                                    className="rounded bg-blue-500 px-3 py-1 text-xs text-white hover:bg-blue-600"
                                >
                                    적용
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
