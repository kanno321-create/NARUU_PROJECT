
import React from "react";
import { Button } from "@/components/ui/button";
import { FileText, Download, Send } from "lucide-react";

import { EstimateResponse, LineItemResponse, fetchAPI } from "@/lib/api";
import { getFileUrl } from "@/config/api";

interface QuoteItem {
    name: string;
    spec: string;
    unit: string;
    quantity: number;
    unitPrice: number;
    amount: number;
}

interface QuotePreviewProps {
    data: any;
    estimateResult?: EstimateResponse | null;
}

export function QuotePreview({ data, estimateResult }: QuotePreviewProps) {
    // Convert backend LineItemResponse to QuoteItem for display
    const getItemsFromBackend = (): QuoteItem[] => {
        if (!estimateResult?.panels || estimateResult.panels.length === 0) {
            return [];
        }

        // Get items from the first panel (분전반1)
        const panel = estimateResult.panels[0];
        if (!panel.items || panel.items.length === 0) {
            return [];
        }

        return panel.items.map((item: LineItemResponse) => ({
            name: item.name,
            spec: item.spec,
            unit: item.unit,
            quantity: item.quantity,
            unitPrice: item.unit_price,
            amount: item.supply_price
        }));
    };

    // Get items: prefer backend data, fallback to empty if not available
    const items = getItemsFromBackend();
    const hasBackendData = items.length > 0;

    // Use the real total price from API
    const totalAmount = estimateResult?.total_price || 0;
    const totalWithVat = estimateResult?.total_price_with_vat || Math.round(totalAmount * 1.1);

    // Get enclosure size from pipeline results if available
    const enclosureSize = estimateResult?.pipeline_results?.stage_1_enclosure?.enclosure_size;
    const enclosureSizeStr = enclosureSize ? `${enclosureSize[0]}×${enclosureSize[1]}×${enclosureSize[2]}` : "";

    return (
        <div className="flex h-full flex-col">
            {/* Header */}
            <div className="mb-4 flex items-center justify-between rounded-md bg-surface-secondary px-5 py-4">
                <div>
                    <div className="text-lg font-semibold text-text-strong">견적서</div>
                    {enclosureSizeStr && (
                        <div className="text-sm text-text-subtle">외함 사이즈: {enclosureSizeStr}</div>
                    )}
                </div>
                <div className="text-right">
                    <div className="text-lg font-bold text-brand">
                        공급가: {totalAmount.toLocaleString()}원
                    </div>
                    <div className="text-sm text-text-subtle">
                        부가세 포함: {totalWithVat.toLocaleString()}원
                    </div>
                </div>
            </div>

            {/* Table */}
            <div className="flex-1 overflow-hidden rounded-md border border-border bg-white">
                <div className="h-full overflow-y-auto">
                    {hasBackendData ? (
                        <table className="w-full border-collapse text-sm">
                            <thead className="bg-surface-tertiary sticky top-0 z-10">
                                <tr>
                                    <th className="border-b px-4 py-3 text-left font-medium text-text-subtle">품목</th>
                                    <th className="border-b px-4 py-3 text-left font-medium text-text-subtle">규격</th>
                                    <th className="border-b px-4 py-3 text-center font-medium text-text-subtle">단위</th>
                                    <th className="border-b px-4 py-3 text-center font-medium text-text-subtle">수량</th>
                                    <th className="border-b px-4 py-3 text-right font-medium text-text-subtle">단가</th>
                                    <th className="border-b px-4 py-3 text-right font-medium text-text-subtle">공급가액</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item, idx) => (
                                    <tr key={idx} className="border-b last:border-0 hover:bg-surface-secondary/50">
                                        <td className="px-4 py-3 font-medium">{item.name}</td>
                                        <td className="px-4 py-3 text-text-subtle">{item.spec}</td>
                                        <td className="px-4 py-3 text-center">{item.unit}</td>
                                        <td className="px-4 py-3 text-center">{item.quantity}</td>
                                        <td className="px-4 py-3 text-right">{item.unitPrice.toLocaleString()}</td>
                                        <td className="px-4 py-3 text-right font-medium">{item.amount.toLocaleString()}</td>
                                    </tr>
                                ))}
                                {/* 소계 행 */}
                                <tr className="bg-surface-tertiary font-semibold">
                                    <td colSpan={5} className="px-4 py-3 text-right">소계</td>
                                    <td className="px-4 py-3 text-right">{totalAmount.toLocaleString()}원</td>
                                </tr>
                                {/* 부가세 포함 행 */}
                                <tr className="bg-brand/10 font-bold text-brand">
                                    <td colSpan={5} className="px-4 py-3 text-right">합계 (VAT 포함)</td>
                                    <td className="px-4 py-3 text-right">{totalWithVat.toLocaleString()}원</td>
                                </tr>
                            </tbody>
                        </table>
                    ) : (
                        <div className="flex h-full items-center justify-center text-text-subtle">
                            <div className="text-center">
                                <p className="text-lg">견적 데이터를 불러오는 중...</p>
                                <p className="text-sm mt-2">백엔드에서 상세 품목 정보를 가져오지 못했습니다.</p>
                                {estimateResult && (
                                    <p className="text-xs mt-4 text-text-subtle">
                                        총액: {estimateResult.total_price?.toLocaleString() || 0}원
                                    </p>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Validation Status */}
            {estimateResult?.validation_checks && (
                <div className="mt-4 rounded-md border border-border bg-surface-secondary p-3">
                    <div className="text-sm font-medium mb-2">검증 결과</div>
                    <div className="grid grid-cols-3 gap-2 text-xs">
                        {Object.entries(estimateResult.validation_checks).map(([key, value]) => (
                            <div key={key} className="flex items-center gap-1">
                                <span className={value === "passed" ? "text-green-600" : value === "failed" ? "text-red-600" : "text-gray-400"}>
                                    {value === "passed" ? "✓" : value === "failed" ? "✗" : "○"}
                                </span>
                                <span className="text-text-subtle">{key.replace("CHK_", "")}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Actions */}
            <div className="mt-4 flex gap-2">
                {estimateResult?.documents?.pdf_url ? (
                    <a
                        href={getFileUrl(estimateResult.documents.pdf_url)}
                        download
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 border rounded-md hover:bg-surface-secondary text-sm"
                    >
                        <Download className="h-4 w-4" /> PDF 다운로드
                    </a>
                ) : (
                    <Button variant="outline" className="flex-1 gap-2" disabled>
                        <Download className="h-4 w-4" /> PDF 다운로드
                    </Button>
                )}
                {estimateResult?.documents?.excel_url ? (
                    <a
                        href={getFileUrl(estimateResult.documents.excel_url)}
                        download
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 border rounded-md hover:bg-surface-secondary text-sm"
                    >
                        <FileText className="h-4 w-4" /> Excel 다운로드
                    </a>
                ) : (
                    <Button variant="outline" className="flex-1 gap-2" disabled>
                        <FileText className="h-4 w-4" /> Excel 다운로드
                    </Button>
                )}
                <Button
                    className="flex-1 gap-2 bg-brand hover:bg-brand-strong"
                    onClick={async () => {
                        const email = prompt("견적서를 전송할 이메일 주소를 입력하세요:");
                        if (!email || !email.includes("@")) {
                            if (email) alert("올바른 이메일 주소를 입력해주세요.");
                            return;
                        }

                        try {
                            const panelName = estimateResult?.panels?.[0]?.panel_name || "분전반";
                            const emailBody = `
<h2>견적서 안내</h2>
<p>안녕하세요,</p>
<p>요청하신 견적서를 송부드립니다.</p>
<h3>■ 견적 정보</h3>
<ul>
    <li>품목: ${panelName}</li>
    <li>공급가: ${totalAmount.toLocaleString()}원</li>
    <li>부가세 포함: ${totalWithVat.toLocaleString()}원</li>
</ul>
${estimateResult?.documents?.pdf_url ? `<p><a href="${getFileUrl(estimateResult.documents.pdf_url)}">PDF 다운로드</a></p>` : ''}
${estimateResult?.documents?.excel_url ? `<p><a href="${getFileUrl(estimateResult.documents.excel_url)}">Excel 다운로드</a></p>` : ''}
<p>감사합니다.</p>
                            `.trim();

                            await fetchAPI("/v1/email/send", {
                                method: "POST",
                                body: JSON.stringify({
                                    recipients: [{ email: email, name: "" }],
                                    subject: `견적서 - ${panelName}`,
                                    body: emailBody,
                                    estimate_id: estimateResult?.id || estimateResult?.estimate_id || null,
                                }),
                            });
                            alert(`견적서가 ${email}로 전송되었습니다.`);
                        } catch (error) {
                            console.error("이메일 전송 오류:", error);
                            // 백엔드 API가 없는 경우 mailto: 링크로 대체
                            const subject = encodeURIComponent(`견적서 - ${estimateResult?.panels?.[0]?.panel_name || "분전반"}`);
                            const body = encodeURIComponent(
                                `안녕하세요,\n\n` +
                                `견적서를 송부드립니다.\n\n` +
                                `■ 견적 정보\n` +
                                `- 품목: ${estimateResult?.panels?.[0]?.panel_name || "분전반"}\n` +
                                `- 공급가: ${totalAmount.toLocaleString()}원\n` +
                                `- 부가세 포함: ${totalWithVat.toLocaleString()}원\n\n` +
                                `감사합니다.`
                            );
                            window.open(`mailto:${email}?subject=${subject}&body=${body}`, "_blank");
                            alert("이메일 앱이 열렸습니다. 직접 전송해주세요.");
                        }
                    }}
                >
                    <Send className="h-4 w-4" /> 견적서 전송
                </Button>
            </div>
        </div>
    );
}
