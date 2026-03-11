"use client";

import React from "react";
import { CustomerInfo } from "@/components/features/quote/CustomerInfo";
import { EnclosureInfo } from "@/components/features/quote/EnclosureInfo";
import { MainBreakerInfo } from "@/components/features/quote/MainBreakerInfo";
import { BranchBreakerInfo } from "@/components/features/quote/BranchBreakerInfo";
import { AccessoryInfo } from "@/components/features/quote/AccessoryInfo";
import { MagicPaste } from "@/components/features/quote/MagicPaste";
import { Button } from "@/components/ui/button";
import {
    Save,
    FileText,
    Mail,
    Zap,
    Plus,
    X,
    ChevronRight,
    ChevronDown,
    ArrowRight,
    Sparkles,
    Download,
    Printer,
    MoreHorizontal,
    RefreshCw,
    CheckCircle2,
    AlertCircle,
    ClipboardList,
    Database,
    FileSpreadsheet,
    Loader2,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";

import { QuotePreview } from "@/components/features/quote/QuotePreview";
import { BreakerSettingsDialog } from "@/components/features/quote/BreakerSettingsDialog";
import { api, fetchAPI, mapQuoteDataToEstimateRequest, EstimateResponse } from "@/lib/api";
import { API_BASE_URL, getFileUrl } from "@/config/api";
import { AISupporter } from "@/components/ai-supporter";

export interface QuoteData {
    customer: any;
    enclosure: any;
    mainBreakers: any[];
    branchBreakers: any[];
    accessories: any[];
}

// 탭 인터페이스 정의
interface QuoteTab {
    id: number;
    title: string;
    data: QuoteData;
    estimateResult: EstimateResponse | null;
    showPreview: boolean;
}

// 초기 QuoteData 생성 함수
const createInitialQuoteData = (): QuoteData => ({
    customer: {},
    enclosure: { location: "옥내", type: "기성함", material: "STEEL 1.6T" },
    mainBreakers: [{ type: "MCCB", poles: "4P", capacity: "100A" }],
    branchBreakers: [],
    accessories: [],
});

// 초기 탭 생성 함수
const createNewTab = (id: number, title: string): QuoteTab => ({
    id,
    title,
    data: createInitialQuoteData(),
    estimateResult: null,
    showPreview: false,
});

export default function QuotePage() {
    const router = useRouter();

    // 탭 관리 상태
    const [tabs, setTabs] = React.useState<QuoteTab[]>([
        createNewTab(1, "분전반 1"),
    ]);
    const [activeTabId, setActiveTabId] = React.useState<number>(1);
    const [nextTabId, setNextTabId] = React.useState<number>(2);

    // 현재 활성 탭 가져오기
    const activeTab = tabs.find(tab => tab.id === activeTabId) || tabs[0];

    // 현재 탭의 quoteData를 위한 getter/setter
    const quoteData = activeTab?.data || createInitialQuoteData();
    const setQuoteData = (newData: QuoteData | ((prev: QuoteData) => QuoteData)) => {
        setTabs(prevTabs => prevTabs.map(tab => {
            if (tab.id === activeTabId) {
                const updatedData = typeof newData === 'function' ? newData(tab.data) : newData;
                return { ...tab, data: updatedData };
            }
            return tab;
        }));
    };

    // 현재 탭의 estimateResult getter/setter
    const estimateResult = activeTab?.estimateResult || null;
    const setEstimateResult = (result: EstimateResponse | null) => {
        setTabs(prevTabs => prevTabs.map(tab => {
            if (tab.id === activeTabId) {
                return { ...tab, estimateResult: result };
            }
            return tab;
        }));
    };

    // 현재 탭의 showPreview getter/setter
    const showPreview = activeTab?.showPreview || false;
    const setShowPreview = (show: boolean) => {
        setTabs(prevTabs => prevTabs.map(tab => {
            if (tab.id === activeTabId) {
                return { ...tab, showPreview: show };
            }
            return tab;
        }));
    };

    const [isGenerating, setIsGenerating] = React.useState(false);
    const [showSettings, setShowSettings] = React.useState(false);
    const [isSaving, setIsSaving] = React.useState(false);
    const [showSaveDropdown, setShowSaveDropdown] = React.useState(false);
    const [saveMessage, setSaveMessage] = React.useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const saveDropdownRef = React.useRef<HTMLDivElement>(null);

    const [errorMsg, setErrorMsg] = React.useState<string | null>(null);

    // 저장 드롭다운 외부 클릭 시 닫기
    React.useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (saveDropdownRef.current && !saveDropdownRef.current.contains(e.target as Node)) {
                setShowSaveDropdown(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // 저장 메시지 자동 숨김
    React.useEffect(() => {
        if (saveMessage) {
            const timer = setTimeout(() => setSaveMessage(null), 4000);
            return () => clearTimeout(timer);
        }
    }, [saveMessage]);

    const handleGenerate = async () => {
        setIsGenerating(true);
        setEstimateResult(null);
        setErrorMsg(null);

        // CEO 규칙 (2024-12-03): 메인차단기만 있는 견적 허용
        // 분기차단기가 없어도 견적 생성 가능

        try {
            // 1. Map data to EstimateRequest
            const estimateRequest = mapQuoteDataToEstimateRequest(quoteData);

            // 2. Create Estimate (Single Call)
            const response = await api.estimate.create(estimateRequest);

            setEstimateResult(response);
            setShowPreview(true);
        } catch (error: any) {
            console.error("API Error:", error.message);
            setErrorMsg(error.message || "견적 생성 중 오류가 발생했습니다.");
        } finally {
            setIsGenerating(false);
        }
    };

    const handlePaste = async (text: string) => {
        try {
            // AI API를 Railway 백엔드로 호출하여 텍스트 파싱
            const data = await fetchAPI<{ response?: string; message?: string }>('/v1/ai-manager/chat', {
                method: "POST",
                body: JSON.stringify({
                    message: `다음 텍스트에서 전기 분전반 견적 정보를 추출해주세요. JSON 형식으로만 응답해주세요:
{
  "mainBreakers": [{"type": "MCCB 또는 ELB", "poles": "2P/3P/4P", "capacity": "암페어"}],
  "branchBreakers": [{"type": "MCCB 또는 ELB", "poles": "2P/3P/4P", "capacity": "암페어", "quantity": 수량}],
  "enclosure": {"location": "옥내/옥외", "type": "기성함/주문함"},
  "accessories": []
}

입력 텍스트: ${text}`,
                    model: "claude-sonnet",
                }),
            });

            // AI 응답에서 JSON 추출
            const aiResponse = data.response || data.message || "";
            const jsonMatch = aiResponse.match(/\{[\s\S]*\}/);

            if (jsonMatch) {
                try {
                    const parsed = JSON.parse(jsonMatch[0]);

                    // 분기차단기 추가 (중복 병합 포함)
                    if (parsed.branchBreakers && parsed.branchBreakers.length > 0) {
                        setQuoteData((prev: QuoteData) => {
                            const merged = [...prev.branchBreakers];
                            for (const b of parsed.branchBreakers) {
                                const incoming = {
                                    type: b.type || "MCCB",
                                    poles: b.poles || "2P",
                                    capacity: b.capacity || "20A",
                                    quantity: b.quantity || 1,
                                    brand: b.brand || "",
                                };
                                const existingIdx = merged.findIndex(
                                    (item: any) =>
                                        item.type === incoming.type &&
                                        item.poles === incoming.poles &&
                                        item.capacity === incoming.capacity &&
                                        (item.brand || "") === (incoming.brand || "")
                                );
                                if (existingIdx >= 0) {
                                    merged[existingIdx] = {
                                        ...merged[existingIdx],
                                        quantity: merged[existingIdx].quantity + incoming.quantity,
                                    };
                                } else {
                                    merged.push(incoming);
                                }
                            }
                            return { ...prev, branchBreakers: merged };
                        });
                    }

                    // 메인차단기 업데이트
                    if (parsed.mainBreakers && parsed.mainBreakers.length > 0) {
                        setQuoteData((prev: QuoteData) => ({
                            ...prev,
                            mainBreakers: parsed.mainBreakers.map((m: any) => ({
                                type: m.type || "MCCB",
                                poles: m.poles || "4P",
                                capacity: m.capacity || "100A",
                            })),
                        }));
                    }

                    // 외함 정보 업데이트
                    if (parsed.enclosure) {
                        setQuoteData((prev: QuoteData) => ({
                            ...prev,
                            enclosure: {
                                ...prev.enclosure,
                                location: parsed.enclosure.location || prev.enclosure.location,
                                type: parsed.enclosure.type || prev.enclosure.type,
                            },
                        }));
                    }

                    alert("AI 파싱 완료! 견적 정보가 자동으로 입력되었습니다.");
                } catch (parseError) {
                    console.error("JSON 파싱 오류:", parseError);
                    alert("AI 응답을 파싱하지 못했습니다. 수동으로 입력해주세요.");
                }
            } else {
                // JSON 추출 실패 시 간단한 패턴 매칭 (폴백)
                // 지원 패턴: "ELB 4P 30A 2개", "MCCB 2P 20A 10개",
                //           "E 4P 30A 2개" (E=ELB), "M 2P 20A 10개" (M=MCCB),
                //           "e4P30A2개", "m2p20a10개" 등 한국어 약어
                const patterns = [
                    { regex: /(\d+)\s*분기.*?(\d+)\s*개/gi, handler: (m: RegExpMatchArray) => ({ type: "MCCB", poles: "2P", capacity: `${m[1]}A`, quantity: parseInt(m[2]) }) },
                    { regex: /ELB\s*(\d)P\s*(\d+)A?\s*[x×]?\s*(\d+)\s*개?/gi, handler: (m: RegExpMatchArray) => ({ type: "ELB", poles: `${m[1]}P`, capacity: `${m[2]}A`, quantity: parseInt(m[3]) }) },
                    { regex: /MCCB\s*(\d)P\s*(\d+)A?\s*[x×]?\s*(\d+)\s*개?/gi, handler: (m: RegExpMatchArray) => ({ type: "MCCB", poles: `${m[1]}P`, capacity: `${m[2]}A`, quantity: parseInt(m[3]) }) },
                    // 한국어 약어: "E 4P 30A 2개" → ELB, "M 2P 20A 10개" → MCCB
                    { regex: /(?:^|[\s,])E\s*(\d)P\s*(\d+)A?\s*[x×]?\s*(\d+)\s*개?/gi, handler: (m: RegExpMatchArray) => ({ type: "ELB", poles: `${m[1]}P`, capacity: `${m[2]}A`, quantity: parseInt(m[3]) }) },
                    { regex: /(?:^|[\s,])M\s*(\d)P\s*(\d+)A?\s*[x×]?\s*(\d+)\s*개?/gi, handler: (m: RegExpMatchArray) => ({ type: "MCCB", poles: `${m[1]}P`, capacity: `${m[2]}A`, quantity: parseInt(m[3]) }) },
                    // "누전 2P 30A 4개" → ELB, "배선 3P 50A 2개" → MCCB
                    { regex: /누전\s*(\d)P\s*(\d+)A?\s*[x×]?\s*(\d+)\s*개?/gi, handler: (m: RegExpMatchArray) => ({ type: "ELB", poles: `${m[1]}P`, capacity: `${m[2]}A`, quantity: parseInt(m[3]) }) },
                    { regex: /배선\s*(\d)P\s*(\d+)A?\s*[x×]?\s*(\d+)\s*개?/gi, handler: (m: RegExpMatchArray) => ({ type: "MCCB", poles: `${m[1]}P`, capacity: `${m[2]}A`, quantity: parseInt(m[3]) }) },
                ];

                let foundBreakers: any[] = [];
                for (const pattern of patterns) {
                    let match;
                    while ((match = pattern.regex.exec(text)) !== null) {
                        foundBreakers.push(pattern.handler(match));
                    }
                }

                if (foundBreakers.length > 0) {
                    // 폴백에서도 중복 병합 적용 (brand 포함)
                    setQuoteData((prev: QuoteData) => {
                        const merged = [...prev.branchBreakers];
                        for (const incoming of foundBreakers) {
                            const existingIdx = merged.findIndex(
                                (item: any) =>
                                    item.type === incoming.type &&
                                    item.poles === incoming.poles &&
                                    item.capacity === incoming.capacity &&
                                    (item.brand || "") === (incoming.brand || "")
                            );
                            if (existingIdx >= 0) {
                                merged[existingIdx] = {
                                    ...merged[existingIdx],
                                    quantity: merged[existingIdx].quantity + incoming.quantity,
                                };
                            } else {
                                merged.push(incoming);
                            }
                        }
                        return { ...prev, branchBreakers: merged };
                    });
                    alert(`${foundBreakers.length}개의 차단기 정보를 추출했습니다.`);
                } else {
                    alert("텍스트에서 견적 정보를 추출하지 못했습니다. 직접 입력해주세요.");
                }
            }
        } catch (error) {
            console.error("Magic Paste 오류:", error);
            alert("AI 파싱 중 오류가 발생했습니다. 수동으로 입력해주세요.");
        }
    };

    // Handler: 탭 추가
    const handleAddTab = () => {
        const newTab = createNewTab(nextTabId, `분전반 ${nextTabId}`);
        setTabs(prevTabs => [...prevTabs, newTab]);
        setActiveTabId(nextTabId);
        setNextTabId(prev => prev + 1);
        setErrorMsg(null);
    };

    // Handler: 탭 삭제
    const handleRemoveTab = (tabId: number, e: React.MouseEvent) => {
        e.stopPropagation(); // 탭 클릭 이벤트 전파 방지

        // 최소 1개 탭은 유지
        if (tabs.length <= 1) {
            return;
        }

        const tabIndex = tabs.findIndex(tab => tab.id === tabId);
        const newTabs = tabs.filter(tab => tab.id !== tabId);
        setTabs(newTabs);

        // 삭제된 탭이 활성 탭이면 다른 탭으로 전환
        if (tabId === activeTabId) {
            // 삭제된 탭 위치 기준으로 이전 탭 또는 다음 탭 선택
            const newActiveIndex = Math.max(0, tabIndex - 1);
            setActiveTabId(newTabs[newActiveIndex]?.id || newTabs[0]?.id);
        }
        setErrorMsg(null);
    };

    // Handler: 탭 전환
    const handleTabChange = (tabId: number) => {
        setActiveTabId(tabId);
        setErrorMsg(null);
    };

    // Handler: 탭 이름 변경
    const handleTabRename = (tabId: number, newTitle: string) => {
        setTabs(prevTabs => prevTabs.map(tab => {
            if (tab.id === tabId) {
                return { ...tab, title: newTitle };
            }
            return tab;
        }));
    };

    // Handler: 도면 보기 (drawings 페이지로 이동)
    const handleDrawings = () => {
        router.push("/drawings");
    };

    // Handler: 이메일 전송
    const handleEmail = async () => {
        if (!estimateResult) {
            alert("먼저 견적을 생성해주세요.");
            return;
        }

        const email = prompt("견적서를 전송할 이메일 주소를 입력하세요:");
        if (!email || !email.includes("@")) {
            if (email) alert("올바른 이메일 주소를 입력해주세요.");
            return;
        }

        try {
            const customerName = quoteData.customer || "고객";
            const emailBody = `
<h2>견적서 안내</h2>
<p>안녕하세요,</p>
<p>요청하신 견적서를 송부드립니다.</p>
<h3>■ 견적 정보</h3>
<ul>
    <li>고객명: ${customerName}</li>
    <li>공급가: ${estimateResult.total_price?.toLocaleString() || 0}원</li>
    <li>부가세 포함: ${estimateResult.total_price_with_vat?.toLocaleString() || 0}원</li>
</ul>
${estimateResult.documents?.pdf_url ? `<p><a href="${getFileUrl(estimateResult.documents.pdf_url)}">PDF 다운로드</a></p>` : ''}
${estimateResult.documents?.excel_url ? `<p><a href="${getFileUrl(estimateResult.documents.excel_url)}">Excel 다운로드</a></p>` : ''}
<p>감사합니다.</p>
            `.trim();

            await fetchAPI("/v1/email/send", {
                method: "POST",
                body: JSON.stringify({
                    recipients: [{ email: email, name: customerName }],
                    subject: `견적서 - ${customerName}`,
                    body: emailBody,
                    estimate_id: estimateResult.estimate_id || null,
                    customer: customerName,
                }),
            });
            alert(`견적서가 ${email}로 전송되었습니다.`);
        } catch {
            // 백엔드 API가 없는 경우 mailto: 링크로 대체
            const subject = encodeURIComponent(`견적서 - ${quoteData.customer || "고객"}`);
            const body = encodeURIComponent(
                `안녕하세요,\n\n` +
                `견적서를 송부드립니다.\n\n` +
                `■ 견적 정보\n` +
                `- 고객명: ${quoteData.customer || "-"}\n` +
                `- 공급가: ${estimateResult.total_price?.toLocaleString() || 0}원\n` +
                `- 부가세 포함: ${estimateResult.total_price_with_vat?.toLocaleString() || 0}원\n\n` +
                `감사합니다.`
            );
            window.open(`mailto:${email}?subject=${subject}&body=${body}`, "_blank");
            alert("이메일 앱이 열렸습니다. 직접 전송해주세요.");
        }
    };

    // Handler: 데이터베이스에 견적 저장 + Excel 파일 DB 저장
    const handleSaveToDb = async () => {
        if (!estimateResult) {
            setSaveMessage({ type: 'error', text: '먼저 견적을 생성해주세요.' });
            return;
        }
        setIsSaving(true);
        setShowSaveDropdown(false);

        const quotePayload = {
            estimate_id: estimateResult.estimate_id,
            customer: quoteData.customer,
            enclosure: quoteData.enclosure,
            main_breakers: quoteData.mainBreakers,
            branch_breakers: quoteData.branchBreakers,
            accessories: quoteData.accessories,
            total_price: estimateResult.total_price,
            total_price_with_vat: estimateResult.total_price_with_vat,
            panels: estimateResult.panels || [],
        };

        try {
            const data = await fetchAPI<{ id: string }>("/v1/quotes", {
                method: "POST",
                body: JSON.stringify(quotePayload),
            });

            // Excel/PDF 파일을 DB에 저장
            const estimateId = estimateResult.estimate_id || `EST-${Date.now()}`;
            const customerName = typeof quoteData.customer === 'string'
                ? quoteData.customer
                : quoteData.customer?.name || quoteData.customer?.companyName || '';

            // Excel 파일 저장
            if (estimateResult.documents?.excel_url) {
                try {
                    const excelUrl = getFileUrl(estimateResult.documents.excel_url);
                    const excelRes = await fetch(excelUrl);
                    if (excelRes.ok) {
                        const blob = await excelRes.blob();
                        const formData = new FormData();
                        formData.append("file", blob, `${estimateId}_견적서.xlsx`);
                        formData.append("estimate_id", estimateId);
                        if (customerName) formData.append("customer_name", customerName);
                        if (estimateResult.total_price) formData.append("total_price", String(estimateResult.total_price));
                        await api.erp.estimateFiles.upload(formData);
                    }
                } catch (fileErr) {
                    console.warn("Excel 파일 DB 저장 실패:", fileErr);
                }
            }

            // PDF 파일 저장
            if (estimateResult.documents?.pdf_url) {
                try {
                    const pdfUrl = getFileUrl(estimateResult.documents.pdf_url);
                    const pdfRes = await fetch(pdfUrl);
                    if (pdfRes.ok) {
                        const blob = await pdfRes.blob();
                        const formData = new FormData();
                        formData.append("file", blob, `${estimateId}_견적서.pdf`);
                        formData.append("estimate_id", estimateId);
                        if (customerName) formData.append("customer_name", customerName);
                        if (estimateResult.total_price) formData.append("total_price", String(estimateResult.total_price));
                        await api.erp.estimateFiles.upload(formData);
                    }
                } catch (fileErr) {
                    console.warn("PDF 파일 DB 저장 실패:", fileErr);
                }
            }

            // localStorage 백업 저장
            try {
                const savedQuotes = JSON.parse(localStorage.getItem("savedQuotes") || "[]");
                savedQuotes.push({
                    id: data.id || Date.now(),
                    timestamp: new Date().toISOString(),
                    customer: quoteData.customer,
                    estimateId: estimateResult.estimate_id,
                    totalPrice: estimateResult.total_price,
                    totalPriceWithVat: estimateResult.total_price_with_vat,
                    savedTo: 'database',
                });
                localStorage.setItem("savedQuotes", JSON.stringify(savedQuotes));
            } catch { /* localStorage 백업 실패는 무시 */ }

            setSaveMessage({ type: 'success', text: '견적 데이터 + 파일이 데이터베이스에 저장되었습니다.' });
        } catch (err) {
            console.error("DB Save error:", err);
            // DB 실패 시 localStorage 폴백
            try {
                const savedQuotes = JSON.parse(localStorage.getItem("savedQuotes") || "[]");
                savedQuotes.push({
                    id: Date.now(),
                    timestamp: new Date().toISOString(),
                    customer: quoteData.customer,
                    estimateId: estimateResult.estimate_id,
                    totalPrice: estimateResult.total_price,
                    totalPriceWithVat: estimateResult.total_price_with_vat,
                    savedTo: 'localStorage',
                });
                localStorage.setItem("savedQuotes", JSON.stringify(savedQuotes));
                setSaveMessage({ type: 'success', text: '로컬에 저장되었습니다. (서버 연결 불가)' });
            } catch {
                setSaveMessage({ type: 'error', text: '저장 중 오류가 발생했습니다.' });
            }
        } finally {
            setIsSaving(false);
        }
    };

    // Handler: Excel 다운로드
    const handleDownloadExcel = () => {
        if (!estimateResult) {
            setSaveMessage({ type: 'error', text: '먼저 견적을 생성해주세요.' });
            return;
        }
        setShowSaveDropdown(false);
        if (estimateResult.documents?.excel_url) {
            window.open(getFileUrl(estimateResult.documents.excel_url), "_blank");
        } else {
            setSaveMessage({ type: 'error', text: 'Excel 파일이 아직 준비되지 않았습니다.' });
        }
    };

    // Handler: PDF 다운로드
    const handleDownloadPdf = () => {
        if (!estimateResult) {
            setSaveMessage({ type: 'error', text: '먼저 견적을 생성해주세요.' });
            return;
        }
        setShowSaveDropdown(false);
        if (estimateResult.documents?.pdf_url) {
            window.open(getFileUrl(estimateResult.documents.pdf_url), "_blank");
        } else {
            setSaveMessage({ type: 'error', text: 'PDF 파일이 아직 준비되지 않았습니다.' });
        }
    };

    // 현재 탭 초기화
    const handleReset = () => {
        setQuoteData(createInitialQuoteData());
        setShowPreview(false);
        setEstimateResult(null);
        setErrorMsg(null);
    };

    // 입력된 항목 수 계산
    const itemCount = quoteData.mainBreakers.length + quoteData.branchBreakers.length + quoteData.accessories.length;

    return (
        <div className="flex h-full flex-col bg-bg">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border/40 bg-surface px-6 py-3">
                <div className="flex items-center gap-4">
                    {/* Tabs */}
                    <div className="flex items-center gap-1 overflow-x-auto max-w-[600px]">
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => handleTabChange(tab.id)}
                                className={cn(
                                    "group flex items-center gap-2 rounded-lg px-4 py-2 transition-all",
                                    tab.id === activeTabId
                                        ? "bg-brand/10"
                                        : "hover:bg-surface-secondary"
                                )}
                            >
                                <ClipboardList className={cn(
                                    "h-4 w-4",
                                    tab.id === activeTabId ? "text-brand" : "text-text-subtle"
                                )} />
                                <span className={cn(
                                    "text-sm font-semibold whitespace-nowrap",
                                    tab.id === activeTabId ? "text-brand" : "text-text-subtle"
                                )}>
                                    {tab.title}
                                </span>
                                {tab.estimateResult && (
                                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                                )}
                                {tabs.length > 1 && (
                                    <button
                                        onClick={(e) => handleRemoveTab(tab.id, e)}
                                        className={cn(
                                            "ml-1 rounded p-0.5 transition-colors",
                                            tab.id === activeTabId
                                                ? "text-brand/60 hover:bg-brand/20 hover:text-brand"
                                                : "text-text-subtle/60 opacity-0 group-hover:opacity-100 hover:bg-surface-tertiary hover:text-text"
                                        )}
                                    >
                                        <X className="h-3.5 w-3.5" />
                                    </button>
                                )}
                            </button>
                        ))}
                        <button
                            onClick={handleAddTab}
                            className="flex h-9 w-9 items-center justify-center rounded-lg text-text-subtle transition-colors hover:bg-surface-secondary hover:text-text"
                            title="분전반 추가"
                        >
                            <Plus className="h-4 w-4" />
                        </button>
                    </div>

                    {/* Divider */}
                    <div className="h-6 w-px bg-border/40" />

                    {/* Item Count */}
                    <div className="flex items-center gap-2 text-sm text-text-subtle">
                        <span>입력 항목</span>
                        <span className="rounded-full bg-surface-secondary px-2.5 py-0.5 font-medium text-text">
                            {itemCount}개
                        </span>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {/* MagicPaste */}
                    <MagicPaste onPaste={handlePaste} />

                    {/* Reset Button */}
                    <button
                        onClick={handleReset}
                        className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-text-subtle transition-colors hover:bg-surface-secondary hover:text-text"
                    >
                        <RefreshCw className="h-4 w-4" />
                        초기화
                    </button>
                </div>
            </div>

            <div className="flex flex-1 overflow-hidden">
                {/* Left Panel: Input Forms */}
                <div className="w-[480px] flex-shrink-0 overflow-y-auto border-r border-border/40 bg-surface">
                    <div className="p-5">
                        {/* Section Header */}
                        <div className="mb-5 flex items-center gap-2">
                            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand/10">
                                <FileText className="h-4 w-4 text-brand" />
                            </div>
                            <div>
                                <h2 className="text-base font-semibold text-text-strong">
                                    {activeTab?.title || "분전반"} - 견적 정보
                                </h2>
                                <p className="text-xs text-text-subtle">필요한 정보를 입력해주세요</p>
                            </div>
                        </div>

                        {/* Forms */}
                        <div className="space-y-4">
                            <CustomerInfo
                                data={quoteData.customer}
                                onChange={(d) => setQuoteData({ ...quoteData, customer: d })}
                            />
                            <EnclosureInfo
                                data={quoteData.enclosure}
                                onChange={(d) => setQuoteData({ ...quoteData, enclosure: d })}
                            />
                            <MainBreakerInfo
                                data={quoteData.mainBreakers}
                                onChange={(d) => setQuoteData({ ...quoteData, mainBreakers: d })}
                                onSettingsClick={() => setShowSettings(true)}
                            />
                            <BranchBreakerInfo
                                data={quoteData.branchBreakers}
                                onChange={(d) => setQuoteData({ ...quoteData, branchBreakers: d })}
                            />
                            <AccessoryInfo
                                data={quoteData.accessories}
                                onChange={(d) => setQuoteData({ ...quoteData, accessories: d })}
                            />
                        </div>
                    </div>

                    {/* Generate Button - Sticky at bottom */}
                    <div className="sticky bottom-0 border-t border-border/40 bg-surface p-5">
                        <Button
                            className={cn(
                                "h-12 w-full gap-2 text-base font-semibold transition-all",
                                isGenerating && "opacity-80"
                            )}
                            onClick={handleGenerate}
                            disabled={isGenerating}
                        >
                            {isGenerating ? (
                                <>
                                    <RefreshCw className="h-5 w-5 animate-spin" />
                                    견적 생성 중...
                                </>
                            ) : (
                                <>
                                    <Sparkles className="h-5 w-5" />
                                    AI 견적 생성
                                    <ArrowRight className="h-5 w-5" />
                                </>
                            )}
                        </Button>
                        {errorMsg && (
                            <div className="mt-3 flex items-start gap-2 rounded-lg bg-rose-50 p-3 text-sm text-rose-700 dark:bg-rose-950/30 dark:text-rose-400">
                                <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                                <span>{errorMsg}</span>
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Panel: Preview */}
                <div className="flex flex-1 flex-col overflow-hidden bg-bg">
                    {/* Actions Header */}
                    <div className="flex items-center justify-between border-b border-border/40 bg-surface px-6 py-3">
                        <div className="flex items-center gap-3">
                            <h3 className="text-base font-semibold text-text-strong">견적 결과</h3>
                            {estimateResult && (
                                <span className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400">
                                    <CheckCircle2 className="h-3.5 w-3.5" />
                                    생성 완료
                                </span>
                            )}
                        </div>
                        <div className="flex items-center gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                className="h-9 gap-2"
                                onClick={handleDrawings}
                            >
                                <FileText className="h-4 w-4" />
                                도면
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                className="h-9 gap-2"
                                onClick={handleEmail}
                            >
                                <Mail className="h-4 w-4" />
                                이메일
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                className="h-9 gap-2"
                                onClick={() => {
                                    if (!estimateResult) {
                                        alert("먼저 견적을 생성해주세요.");
                                        return;
                                    }
                                    if (!showPreview) {
                                        alert("미리보기 화면에서 인쇄해주세요.");
                                        setShowPreview(true);
                                        return;
                                    }
                                    window.print();
                                }}
                            >
                                <Printer className="h-4 w-4" />
                                인쇄
                            </Button>
                            <div className="mx-1 h-5 w-px bg-border/40" />
                            {/* 저장 드롭다운 버튼 */}
                            <div className="relative" ref={saveDropdownRef}>
                                <div className="flex">
                                    <Button
                                        size="sm"
                                        className="h-9 gap-2 rounded-r-none"
                                        onClick={handleSaveToDb}
                                        disabled={isSaving}
                                    >
                                        {isSaving ? (
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                        ) : (
                                            <Save className="h-4 w-4" />
                                        )}
                                        저장
                                    </Button>
                                    <Button
                                        size="sm"
                                        className="h-9 px-1.5 rounded-l-none border-l border-white/20"
                                        onClick={() => setShowSaveDropdown(!showSaveDropdown)}
                                        disabled={isSaving}
                                    >
                                        <ChevronDown className="h-3.5 w-3.5" />
                                    </Button>
                                </div>
                                {showSaveDropdown && (
                                    <div className="absolute right-0 top-full z-50 mt-1 w-52 rounded-lg border border-border/40 bg-surface shadow-lg">
                                        <div className="py-1">
                                            <button
                                                onClick={handleSaveToDb}
                                                className="flex w-full items-center gap-2.5 px-3 py-2 text-sm text-text hover:bg-surface-secondary transition"
                                            >
                                                <Database className="h-4 w-4 text-brand" />
                                                데이터베이스 저장
                                            </button>
                                            <button
                                                onClick={handleDownloadExcel}
                                                className="flex w-full items-center gap-2.5 px-3 py-2 text-sm text-text hover:bg-surface-secondary transition"
                                            >
                                                <FileSpreadsheet className="h-4 w-4 text-emerald-600" />
                                                Excel 다운로드
                                            </button>
                                            <button
                                                onClick={handleDownloadPdf}
                                                className="flex w-full items-center gap-2.5 px-3 py-2 text-sm text-text hover:bg-surface-secondary transition"
                                            >
                                                <FileText className="h-4 w-4 text-rose-600" />
                                                PDF 다운로드
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Content */}
                    <div className="flex-1 overflow-auto p-6">
                        {showPreview ? (
                            <QuotePreview data={quoteData} estimateResult={estimateResult} />
                        ) : (
                            <div className="flex h-full items-center justify-center">
                                <div className="text-center">
                                    {/* Animated Generate Button */}
                                    <button
                                        className={cn(
                                            "group relative mx-auto mb-8 flex h-44 w-44 flex-col items-center justify-center rounded-3xl transition-all duration-300",
                                            "bg-gradient-to-br from-brand via-brand to-emerald-500",
                                            "shadow-[0_20px_50px_-15px_rgba(16,163,127,0.5)]",
                                            "hover:shadow-[0_25px_60px_-15px_rgba(16,163,127,0.6)] hover:scale-105",
                                            isGenerating && "opacity-80 pointer-events-none"
                                        )}
                                        onClick={handleGenerate}
                                        disabled={isGenerating}
                                    >
                                        <div className="absolute inset-0 rounded-3xl bg-white/10 opacity-0 transition-opacity group-hover:opacity-100" />
                                        <div className="relative">
                                            {isGenerating ? (
                                                <RefreshCw className="h-10 w-10 animate-spin text-white" />
                                            ) : (
                                                <Sparkles className="h-10 w-10 text-white" />
                                            )}
                                        </div>
                                        <span className="relative mt-3 text-lg font-bold text-white">
                                            {isGenerating ? "분석 중..." : "견적 생성"}
                                        </span>
                                        {!isGenerating && (
                                            <span className="relative mt-1 text-xs text-white/80">
                                                AI Analysis
                                            </span>
                                        )}

                                        {/* Pulse Effect */}
                                        {!isGenerating && (
                                            <div className="absolute inset-0 animate-ping rounded-3xl bg-brand/30" style={{ animationDuration: '2s' }} />
                                        )}
                                    </button>

                                    <div className="space-y-2">
                                        <p className="text-lg font-medium text-text-strong">
                                            견적 정보를 입력하고 생성 버튼을 클릭하세요
                                        </p>
                                        <p className="text-sm text-text-subtle">
                                            AI가 자동으로 최적의 견적서를 생성해 드립니다
                                        </p>
                                    </div>

                                    {/* Quick Tips */}
                                    <div className="mx-auto mt-8 max-w-md rounded-xl border border-border/40 bg-surface p-4">
                                        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-text-subtle">
                                            빠른 입력 팁
                                        </p>
                                        <div className="space-y-2 text-left text-sm text-text-subtle">
                                            <div className="flex items-start gap-2">
                                                <Sparkles className="h-4 w-4 flex-shrink-0 mt-0.5 text-brand" />
                                                <span>매직 붙여넣기로 텍스트에서 자동 추출</span>
                                            </div>
                                            <div className="flex items-start gap-2">
                                                <ChevronRight className="h-4 w-4 flex-shrink-0 mt-0.5 text-text-subtle" />
                                                <span>메인차단기만으로도 견적 생성 가능</span>
                                            </div>
                                            <div className="flex items-start gap-2">
                                                <ChevronRight className="h-4 w-4 flex-shrink-0 mt-0.5 text-text-subtle" />
                                                <span>분기차단기는 여러 종류 추가 가능</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* 저장 알림 토스트 */}
            {saveMessage && (
                <div className={cn(
                    "fixed bottom-6 right-6 z-50 flex items-center gap-2.5 rounded-lg px-4 py-3 shadow-lg transition-all animate-in slide-in-from-bottom-4 fade-in duration-300",
                    saveMessage.type === 'success'
                        ? "bg-emerald-50 border border-emerald-200 text-emerald-800 dark:bg-emerald-950/80 dark:border-emerald-800 dark:text-emerald-300"
                        : "bg-rose-50 border border-rose-200 text-rose-800 dark:bg-rose-950/80 dark:border-rose-800 dark:text-rose-300"
                )}>
                    {saveMessage.type === 'success' ? (
                        <CheckCircle2 className="h-4.5 w-4.5 flex-shrink-0" />
                    ) : (
                        <AlertCircle className="h-4.5 w-4.5 flex-shrink-0" />
                    )}
                    <span className="text-sm font-medium">{saveMessage.text}</span>
                    <button
                        onClick={() => setSaveMessage(null)}
                        className="ml-2 rounded p-0.5 hover:bg-black/5 dark:hover:bg-white/10 transition"
                    >
                        <X className="h-3.5 w-3.5" />
                    </button>
                </div>
            )}

            {/* Settings Dialog */}
            <BreakerSettingsDialog open={showSettings} onOpenChange={setShowSettings} />

            {/* AI 서포터 */}
            <AISupporter
                tabContext="quote"
                onQuoteAction={(action, data) => {
                    // AI가 견적 데이터를 직접 제어할 때 사용
                    console.log("Quote AI Action:", action, data);
                    if (action === "setCustomer" && data.customer) {
                        setQuoteData(prev => ({ ...prev, customer: data.customer }));
                    }
                    if (action === "setEnclosure" && data.enclosure) {
                        setQuoteData(prev => ({ ...prev, enclosure: data.enclosure }));
                    }
                    if (action === "addBranchBreaker" && data.breaker) {
                        setQuoteData(prev => ({
                            ...prev,
                            branchBreakers: [...prev.branchBreakers, data.breaker],
                        }));
                    }
                }}
            />
        </div>
    );
}
