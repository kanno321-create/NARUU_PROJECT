"use client";

import React, { useState, useEffect } from "react";
import { Search, Download, Printer, RefreshCw, Calendar } from "lucide-react";
import { saleApi, purchaseApi, customerApi, type Sale, type Purchase, type Customer } from "@/lib/api/erp-api";

interface ReportWindowProps {
    reportType?: string;
}

export function ReportWindow({ reportType = "sales-statement" }: ReportWindowProps) {
    const [activeReport, setActiveReport] = useState(reportType);
    const [startDate, setStartDate] = useState(() => {
        const date = new Date();
        date.setMonth(date.getMonth() - 1);
        return date.toISOString().split("T")[0];
    });
    const [endDate, setEndDate] = useState(() => new Date().toISOString().split("T")[0]);
    const [loading, setLoading] = useState(false);
    const [salesData, setSalesData] = useState<Sale[]>([]);
    const [purchaseData, setPurchaseData] = useState<Purchase[]>([]);
    const [customers, setCustomers] = useState<Customer[]>([]);
    const [selectedCustomer, setSelectedCustomer] = useState("");

    // 데이터 조회
    const fetchData = async () => {
        setLoading(true);
        try {
            const [salesRes, purchaseRes, customersRes] = await Promise.all([
                saleApi.list({ start_date: startDate, end_date: endDate }),
                purchaseApi.list({ start_date: startDate, end_date: endDate }),
                customerApi.list(),
            ]);
            setSalesData(salesRes.items || []);
            setPurchaseData(purchaseRes.items || []);
            setCustomers(customersRes.items || []);
        } catch (error) {
            console.error("데이터 조회 실패:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [startDate, endDate]);

    // 인쇄
    const handlePrint = () => {
        window.print();
    };

    // 엑셀 다운로드 (CSV)
    const handleDownload = () => {
        let csvContent = "";
        let filename = "";

        if (activeReport === "sales-statement") {
            csvContent = "전표번호,일자,거래처,공급가액,부가세,합계,상태\n";
            salesData.forEach((sale) => {
                csvContent += `${sale.sale_number},${sale.sale_date},${sale.customer?.name || ""},${sale.supply_amount},${sale.tax_amount},${sale.total_amount},${sale.status}\n`;
            });
            filename = `매출명세서_${startDate}_${endDate}.csv`;
        } else if (activeReport === "purchase-statement") {
            csvContent = "전표번호,일자,거래처,공급가액,부가세,합계,상태\n";
            purchaseData.forEach((purchase) => {
                csvContent += `${purchase.purchase_number},${purchase.purchase_date},${purchase.supplier?.name || ""},${purchase.supply_amount},${purchase.tax_amount},${purchase.total_amount},${purchase.status}\n`;
            });
            filename = `매입명세서_${startDate}_${endDate}.csv`;
        }

        const blob = new Blob(["\ufeff" + csvContent], { type: "text/csv;charset=utf-8;" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();
    };

    // 통계 계산
    const calculateStats = (data: Sale[] | Purchase[]) => {
        const totalSupply = data.reduce((sum, item) => sum + Number(item.supply_amount || 0), 0);
        const totalTax = data.reduce((sum, item) => sum + Number(item.tax_amount || 0), 0);
        const totalAmount = data.reduce((sum, item) => sum + Number(item.total_amount || 0), 0);
        return { totalSupply, totalTax, totalAmount, count: data.length };
    };

    const reportTabs = [
        { id: "sales-statement", label: "매출명세서" },
        { id: "purchase-statement", label: "매입명세서" },
        { id: "customer-sales", label: "거래처별매출현황" },
        { id: "daily-report", label: "일계표" },
        { id: "profit-loss", label: "손익현황" },
    ];

    const salesStats = calculateStats(salesData);
    const purchaseStats = calculateStats(purchaseData);

    return (
        <div className="flex h-full flex-col">
            {/* 툴바 */}
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button
                    onClick={fetchData}
                    disabled={loading}
                    className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary disabled:opacity-50"
                >
                    <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                    조회
                </button>
                <button
                    onClick={handlePrint}
                    className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"
                >
                    <Printer className="h-4 w-4" />
                    인쇄
                </button>
                <button
                    onClick={handleDownload}
                    className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary"
                >
                    <Download className="h-4 w-4" />
                    다운로드
                </button>

                <div className="ml-4 flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-text-subtle" />
                    <input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        className="rounded border px-2 py-1 text-sm"
                    />
                    <span>~</span>
                    <input
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        className="rounded border px-2 py-1 text-sm"
                    />
                </div>
            </div>

            <div className="flex flex-1 overflow-hidden">
                {/* 탭 메뉴 */}
                <div className="w-44 border-r bg-surface-secondary p-2">
                    {reportTabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveReport(tab.id)}
                            className={`w-full rounded px-3 py-2 text-left text-sm ${
                                activeReport === tab.id
                                    ? "bg-brand text-white"
                                    : "hover:bg-surface"
                            }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* 보고서 내용 */}
                <div className="flex-1 overflow-auto p-4">
                    {activeReport === "sales-statement" && (
                        <div>
                            <h3 className="text-lg font-medium mb-4">매출명세서</h3>

                            {/* 요약 */}
                            <div className="mb-4 grid grid-cols-4 gap-4">
                                <div className="rounded border p-3">
                                    <div className="text-sm text-text-subtle">전표수</div>
                                    <div className="text-xl font-bold">{salesStats.count}건</div>
                                </div>
                                <div className="rounded border p-3">
                                    <div className="text-sm text-text-subtle">공급가액</div>
                                    <div className="text-xl font-bold">{salesStats.totalSupply.toLocaleString()}원</div>
                                </div>
                                <div className="rounded border p-3">
                                    <div className="text-sm text-text-subtle">부가세</div>
                                    <div className="text-xl font-bold">{salesStats.totalTax.toLocaleString()}원</div>
                                </div>
                                <div className="rounded border p-3">
                                    <div className="text-sm text-text-subtle">합계</div>
                                    <div className="text-xl font-bold text-brand">{salesStats.totalAmount.toLocaleString()}원</div>
                                </div>
                            </div>

                            {/* 테이블 */}
                            <table className="w-full border-collapse text-sm">
                                <thead>
                                    <tr className="border-b bg-surface">
                                        <th className="px-3 py-2 text-left">전표번호</th>
                                        <th className="px-3 py-2 text-left">일자</th>
                                        <th className="px-3 py-2 text-left">거래처</th>
                                        <th className="px-3 py-2 text-right">공급가액</th>
                                        <th className="px-3 py-2 text-right">부가세</th>
                                        <th className="px-3 py-2 text-right">합계</th>
                                        <th className="px-3 py-2 text-center">상태</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {salesData.map((sale) => (
                                        <tr key={sale.id} className="border-b hover:bg-surface-secondary">
                                            <td className="px-3 py-2">{sale.sale_number}</td>
                                            <td className="px-3 py-2">{sale.sale_date}</td>
                                            <td className="px-3 py-2">{sale.customer?.name}</td>
                                            <td className="px-3 py-2 text-right">{Number(sale.supply_amount || 0).toLocaleString()}</td>
                                            <td className="px-3 py-2 text-right">{Number(sale.tax_amount || 0).toLocaleString()}</td>
                                            <td className="px-3 py-2 text-right font-medium">{Number(sale.total_amount || 0).toLocaleString()}</td>
                                            <td className="px-3 py-2 text-center">
                                                <span className={`rounded px-2 py-0.5 text-xs ${
                                                    sale.status === "confirmed" ? "bg-green-100 text-green-800" :
                                                    sale.status === "pending" ? "bg-yellow-100 text-yellow-800" :
                                                    "bg-gray-100 text-gray-800"
                                                }`}>
                                                    {sale.status === "confirmed" ? "확정" : sale.status === "pending" ? "대기" : sale.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                    {salesData.length === 0 && (
                                        <tr>
                                            <td colSpan={7} className="px-3 py-8 text-center text-text-subtle">
                                                데이터가 없습니다.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {activeReport === "purchase-statement" && (
                        <div>
                            <h3 className="text-lg font-medium mb-4">매입명세서</h3>

                            {/* 요약 */}
                            <div className="mb-4 grid grid-cols-4 gap-4">
                                <div className="rounded border p-3">
                                    <div className="text-sm text-text-subtle">전표수</div>
                                    <div className="text-xl font-bold">{purchaseStats.count}건</div>
                                </div>
                                <div className="rounded border p-3">
                                    <div className="text-sm text-text-subtle">공급가액</div>
                                    <div className="text-xl font-bold">{purchaseStats.totalSupply.toLocaleString()}원</div>
                                </div>
                                <div className="rounded border p-3">
                                    <div className="text-sm text-text-subtle">부가세</div>
                                    <div className="text-xl font-bold">{purchaseStats.totalTax.toLocaleString()}원</div>
                                </div>
                                <div className="rounded border p-3">
                                    <div className="text-sm text-text-subtle">합계</div>
                                    <div className="text-xl font-bold text-brand">{purchaseStats.totalAmount.toLocaleString()}원</div>
                                </div>
                            </div>

                            {/* 테이블 */}
                            <table className="w-full border-collapse text-sm">
                                <thead>
                                    <tr className="border-b bg-surface">
                                        <th className="px-3 py-2 text-left">전표번호</th>
                                        <th className="px-3 py-2 text-left">일자</th>
                                        <th className="px-3 py-2 text-left">거래처</th>
                                        <th className="px-3 py-2 text-right">공급가액</th>
                                        <th className="px-3 py-2 text-right">부가세</th>
                                        <th className="px-3 py-2 text-right">합계</th>
                                        <th className="px-3 py-2 text-center">상태</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {purchaseData.map((purchase) => (
                                        <tr key={purchase.id} className="border-b hover:bg-surface-secondary">
                                            <td className="px-3 py-2">{purchase.purchase_number}</td>
                                            <td className="px-3 py-2">{purchase.purchase_date}</td>
                                            <td className="px-3 py-2">{purchase.supplier?.name}</td>
                                            <td className="px-3 py-2 text-right">{Number(purchase.supply_amount || 0).toLocaleString()}</td>
                                            <td className="px-3 py-2 text-right">{Number(purchase.tax_amount || 0).toLocaleString()}</td>
                                            <td className="px-3 py-2 text-right font-medium">{Number(purchase.total_amount || 0).toLocaleString()}</td>
                                            <td className="px-3 py-2 text-center">
                                                <span className={`rounded px-2 py-0.5 text-xs ${
                                                    purchase.status === "confirmed" ? "bg-green-100 text-green-800" :
                                                    purchase.status === "pending" ? "bg-yellow-100 text-yellow-800" :
                                                    "bg-gray-100 text-gray-800"
                                                }`}>
                                                    {purchase.status === "confirmed" ? "확정" : purchase.status === "pending" ? "대기" : purchase.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                    {purchaseData.length === 0 && (
                                        <tr>
                                            <td colSpan={7} className="px-3 py-8 text-center text-text-subtle">
                                                데이터가 없습니다.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {activeReport === "customer-sales" && (
                        <div>
                            <h3 className="text-lg font-medium mb-4">거래처별 매출현황</h3>

                            <table className="w-full border-collapse text-sm">
                                <thead>
                                    <tr className="border-b bg-surface">
                                        <th className="px-3 py-2 text-left">거래처명</th>
                                        <th className="px-3 py-2 text-right">매출건수</th>
                                        <th className="px-3 py-2 text-right">공급가액</th>
                                        <th className="px-3 py-2 text-right">부가세</th>
                                        <th className="px-3 py-2 text-right">합계</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {customers.map((customer) => {
                                        const customerSales = salesData.filter((s) => s.customer_id === customer.id);
                                        const stats = calculateStats(customerSales);
                                        if (stats.count === 0) return null;
                                        return (
                                            <tr key={customer.id} className="border-b hover:bg-surface-secondary">
                                                <td className="px-3 py-2">{customer.name}</td>
                                                <td className="px-3 py-2 text-right">{stats.count}건</td>
                                                <td className="px-3 py-2 text-right">{stats.totalSupply.toLocaleString()}</td>
                                                <td className="px-3 py-2 text-right">{stats.totalTax.toLocaleString()}</td>
                                                <td className="px-3 py-2 text-right font-medium">{stats.totalAmount.toLocaleString()}</td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {activeReport === "daily-report" && (
                        <div>
                            <h3 className="text-lg font-medium mb-4">일계표</h3>

                            <div className="grid grid-cols-2 gap-6">
                                {/* 매출 */}
                                <div className="rounded border p-4">
                                    <h4 className="font-medium mb-3 text-blue-600">매출</h4>
                                    <div className="space-y-2">
                                        <div className="flex justify-between">
                                            <span className="text-text-subtle">전표수</span>
                                            <span>{salesStats.count}건</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-text-subtle">공급가액</span>
                                            <span>{salesStats.totalSupply.toLocaleString()}원</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-text-subtle">부가세</span>
                                            <span>{salesStats.totalTax.toLocaleString()}원</span>
                                        </div>
                                        <div className="flex justify-between border-t pt-2 font-bold">
                                            <span>합계</span>
                                            <span className="text-blue-600">{salesStats.totalAmount.toLocaleString()}원</span>
                                        </div>
                                    </div>
                                </div>

                                {/* 매입 */}
                                <div className="rounded border p-4">
                                    <h4 className="font-medium mb-3 text-red-600">매입</h4>
                                    <div className="space-y-2">
                                        <div className="flex justify-between">
                                            <span className="text-text-subtle">전표수</span>
                                            <span>{purchaseStats.count}건</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-text-subtle">공급가액</span>
                                            <span>{purchaseStats.totalSupply.toLocaleString()}원</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-text-subtle">부가세</span>
                                            <span>{purchaseStats.totalTax.toLocaleString()}원</span>
                                        </div>
                                        <div className="flex justify-between border-t pt-2 font-bold">
                                            <span>합계</span>
                                            <span className="text-red-600">{purchaseStats.totalAmount.toLocaleString()}원</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* 손익 */}
                            <div className="mt-6 rounded border-2 border-brand p-4">
                                <div className="flex justify-between text-lg font-bold">
                                    <span>손익</span>
                                    <span className={salesStats.totalAmount - purchaseStats.totalAmount >= 0 ? "text-blue-600" : "text-red-600"}>
                                        {(salesStats.totalAmount - purchaseStats.totalAmount).toLocaleString()}원
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeReport === "profit-loss" && (
                        <div>
                            <h3 className="text-lg font-medium mb-4">손익현황</h3>

                            <div className="space-y-4">
                                <div className="rounded border p-4">
                                    <div className="flex justify-between border-b pb-3 mb-3">
                                        <span className="font-medium">총 매출</span>
                                        <span className="text-blue-600 font-bold">{salesStats.totalAmount.toLocaleString()}원</span>
                                    </div>
                                    <div className="flex justify-between border-b pb-3 mb-3">
                                        <span className="font-medium">총 매입</span>
                                        <span className="text-red-600 font-bold">{purchaseStats.totalAmount.toLocaleString()}원</span>
                                    </div>
                                    <div className="flex justify-between text-xl font-bold">
                                        <span>순이익</span>
                                        <span className={salesStats.totalAmount - purchaseStats.totalAmount >= 0 ? "text-green-600" : "text-red-600"}>
                                            {(salesStats.totalAmount - purchaseStats.totalAmount).toLocaleString()}원
                                        </span>
                                    </div>
                                </div>

                                <div className="rounded bg-surface-secondary p-4">
                                    <div className="text-sm text-text-subtle mb-2">이익률</div>
                                    <div className="text-2xl font-bold">
                                        {salesStats.totalAmount > 0
                                            ? (((salesStats.totalAmount - purchaseStats.totalAmount) / salesStats.totalAmount) * 100).toFixed(1)
                                            : 0}%
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
