"use client";

import React, { useState, useCallback } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Loader2,
  FileText,
  MessageSquare,
  Download,
  RefreshCw,
  AlertTriangle,
  Info,
  FileSpreadsheet,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { WizardState } from "./types";

interface PublicEstimateResult {
  estimate_id: string;
  success: boolean;
  total_amount: number | null;
  line_items: any[];
  validation_checks: any;
  created_at: string;
  message: string;
}

interface Step3Props {
  state: WizardState;
  result: PublicEstimateResult | null;
  loading: boolean;
  error: string | null;
  onBack: () => void;
  onRetry: () => void;
}

/* ── 헬퍼: BOM 항목에서 필드 추출 ── */
function getItemName(item: any): string {
  return item.name || item.item_name || item.description || "-";
}
function getItemSpec(item: any): string {
  return item.spec || item.specification || item.model || "-";
}
function getItemQty(item: any): number {
  return item.quantity || 1;
}
function getItemUnit(item: any): string {
  return item.unit || "EA";
}
function getItemUnitPrice(item: any): number {
  return item.unit_price || item.unitPrice || 0;
}
function getItemAmount(item: any): number {
  return item.supply_price || item.amount || item.total_price || item.subtotal || 0;
}

/* ── PDF 다운로드 ── */
async function downloadPdf(
  result: PublicEstimateResult,
  state: WizardState,
  formatPrice: (n: number) => string
) {
  const { default: jsPDF } = await import("jspdf");
  await import("jspdf-autotable");

  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const pageWidth = doc.internal.pageSize.getWidth();

  // 한글 폰트가 없으므로 기본 폰트로 영문+숫자만 정확히 표시
  // 실제 배포 시 한글 폰트 embed 필요
  doc.setFontSize(18);
  doc.text("HKKOR AI Estimate", pageWidth / 2, 25, { align: "center" });

  doc.setFontSize(10);
  doc.text(`Estimate ID: ${result.estimate_id}`, 15, 40);
  doc.text(`Date: ${new Date(result.created_at).toLocaleDateString("ko-KR")}`, 15, 46);
  doc.text(`Customer: ${state.customerName || "N/A"}`, 15, 52);
  doc.text(`Project: ${state.projectName || "N/A"}`, 15, 58);

  const totalAmount = result.total_amount || 0;
  const vatAmount = Math.round(totalAmount * 0.1);
  doc.setFontSize(12);
  doc.text(`Total: ${formatPrice(totalAmount)} KRW`, 15, 68);
  doc.text(`VAT(10%): ${formatPrice(vatAmount)} KRW`, 15, 74);
  doc.text(`Grand Total: ${formatPrice(totalAmount + vatAmount)} KRW`, 15, 80);

  // BOM 테이블
  if (result.line_items && result.line_items.length > 0) {
    const tableData = result.line_items.map((item: any, idx: number) => [
      idx + 1,
      getItemName(item),
      getItemSpec(item),
      getItemQty(item),
      getItemUnit(item),
      getItemUnitPrice(item) > 0 ? formatPrice(getItemUnitPrice(item)) : "-",
      getItemAmount(item) > 0 ? formatPrice(getItemAmount(item)) : "-",
    ]);

    (doc as any).autoTable({
      startY: 90,
      head: [["#", "Item", "Spec", "Qty", "Unit", "Unit Price", "Amount"]],
      body: tableData,
      styles: { fontSize: 8, cellPadding: 2 },
      headStyles: { fillColor: [30, 41, 59] },
      theme: "grid",
    });
  }

  // 베타 안내
  const finalY = (doc as any).lastAutoTable?.finalY || 90;
  doc.setFontSize(8);
  doc.setTextColor(120, 120, 120);
  doc.text(
    "* This is an AI-generated beta estimate. Actual prices may differ. Contact us for accurate pricing.",
    15,
    finalY + 15
  );

  doc.save(`HKKOR_Estimate_${result.estimate_id}.pdf`);
}

/* ── Excel 다운로드 ── */
async function downloadExcel(
  result: PublicEstimateResult,
  state: WizardState,
  formatPrice: (n: number) => string
) {
  const XLSX = await import("xlsx");

  const totalAmount = result.total_amount || 0;
  const vatAmount = Math.round(totalAmount * 0.1);

  // 헤더 정보
  const headerRows = [
    ["한국산업이앤에스 AI 견적서"],
    [],
    ["견적 ID", result.estimate_id],
    ["일자", new Date(result.created_at).toLocaleDateString("ko-KR")],
    ["고객명", state.customerName || "-"],
    ["프로젝트", state.projectName || "-"],
    [],
  ];

  // BOM 데이터
  const bomHeader = ["No", "품목", "규격", "수량", "단위", "단가", "금액"];
  const bomData = (result.line_items || []).map((item: any, idx: number) => [
    idx + 1,
    getItemName(item),
    getItemSpec(item),
    getItemQty(item),
    getItemUnit(item),
    getItemUnitPrice(item) || "",
    getItemAmount(item) || "",
  ]);

  // 합계
  const summaryRows = [
    [],
    ["", "", "", "", "", "공급가액", totalAmount],
    ["", "", "", "", "", "부가세(10%)", vatAmount],
    ["", "", "", "", "", "합계", totalAmount + vatAmount],
    [],
    [
      "* 본 견적은 AI 자동 견적 베타 버전으로, 실제 견적과 차이가 있을 수 있습니다.",
    ],
  ];

  const wsData = [...headerRows, bomHeader, ...bomData, ...summaryRows];
  const ws = XLSX.utils.aoa_to_sheet(wsData);

  // 열 너비 설정
  ws["!cols"] = [
    { wch: 5 },
    { wch: 25 },
    { wch: 20 },
    { wch: 6 },
    { wch: 5 },
    { wch: 15 },
    { wch: 15 },
  ];

  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "견적서");
  XLSX.writeFile(wb, `HKKOR_견적서_${result.estimate_id}.xlsx`);
}

export function Step3Result({
  state,
  result,
  loading,
  error,
  onBack,
  onRetry,
}: Step3Props) {
  const [showInquiry, setShowInquiry] = useState(false);
  const [inquirySubmitted, setInquirySubmitted] = useState(false);

  const formatPrice = useCallback(
    (n: number) => new Intl.NumberFormat("ko-KR").format(Math.round(n)),
    []
  );

  /* ── 로딩 상태 ── */
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="relative">
          <div className="w-20 h-20 rounded-full bg-blue-50 flex items-center justify-center">
            <Loader2 className="w-10 h-10 text-blue-600 animate-spin" />
          </div>
        </div>
        <h3 className="mt-6 text-xl font-bold text-slate-900">
          AI가 견적을 산출하고 있습니다
        </h3>
        <p className="mt-2 text-sm text-slate-500 text-center max-w-md">
          차단기 선정, 외함 크기 산출, BOM 생성, 6단계 검증을 수행 중입니다.
          <br />
          잠시만 기다려 주세요...
        </p>
      </div>
    );
  }

  /* ── 에러 상태 ── */
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mb-4">
          <AlertTriangle className="w-8 h-8 text-red-500" />
        </div>
        <h3 className="text-xl font-bold text-slate-900 mb-2">
          견적 산출 중 오류가 발생했습니다
        </h3>
        <p className="text-sm text-slate-500 text-center max-w-md mb-6">
          {error}
        </p>
        <div className="flex gap-3">
          <button
            onClick={onBack}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-slate-600 border border-slate-200 hover:bg-slate-50 transition-all"
          >
            <ArrowLeft className="w-4 h-4" />
            구성 수정
          </button>
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold bg-blue-600 text-white hover:bg-blue-700 transition-all"
          >
            <RefreshCw className="w-4 h-4" />
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  /* ── 결과 없음 ── */
  if (!result) return null;

  const totalAmount = result.total_amount || 0;
  const vatAmount = Math.round(totalAmount * 0.1);

  const validationChecks = result.validation_checks || {};
  const stagesCompleted = validationChecks.stages_completed || 0;
  const totalStages = validationChecks.total_stages || 8;

  return (
    <div className="space-y-8">
      {/* ── 베타 안내 배너 ── */}
      <div className="flex items-start gap-3 px-5 py-4 rounded-xl bg-blue-50 border border-blue-100">
        <Info className="w-5 h-5 text-blue-500 mt-0.5 shrink-0" />
        <div>
          <p className="text-sm font-semibold text-blue-800">
            AI 자동 견적 베타 버전 안내
          </p>
          <p className="text-sm text-blue-600 mt-0.5">
            본 견적은 AI가 자동으로 산출한 참고용 견적입니다. 실제 견적과 차이가
            있을 수 있으며, 정확한 견적은{" "}
            <Link
              href="/support/contact"
              className="font-semibold underline underline-offset-2"
            >
              문의
            </Link>{" "}
            부탁드립니다.
          </p>
        </div>
      </div>

      {/* ── 상단 요약 ── */}
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-8 text-center">
        <div
          className={cn(
            "inline-flex items-center gap-2 px-4 py-1.5 rounded-full mb-4 text-sm font-medium",
            result.success
              ? "bg-emerald-500/10 text-emerald-400"
              : "bg-amber-500/10 text-amber-400"
          )}
        >
          {result.success ? (
            <CheckCircle2 className="w-4 h-4" />
          ) : (
            <AlertTriangle className="w-4 h-4" />
          )}
          {result.success
            ? `AI 검증 통과 (${stagesCompleted}/${totalStages})`
            : result.message || "일부 검증 주의"}
        </div>

        <p className="text-slate-400 text-sm mb-2">AI 견적 총액</p>
        <p className="text-4xl sm:text-5xl font-extrabold text-white">
          {totalAmount > 0 ? formatPrice(totalAmount) : "산출 중"}
          <span className="text-xl text-slate-400 ml-1">원</span>
        </p>
        {totalAmount > 0 && (
          <p className="mt-2 text-slate-400 text-sm">
            VAT 포함: {formatPrice(totalAmount + vatAmount)}원
          </p>
        )}
        <p className="mt-1 text-xs text-slate-500">
          견적 ID: {result.estimate_id}
        </p>
      </div>

      {/* ── BOM 테이블 ── */}
      {result.line_items && result.line_items.length > 0 && (
        <div>
          <h3 className="text-lg font-bold text-slate-900 mb-4">
            <FileText className="inline w-5 h-5 mr-1 text-blue-600" />
            견적 상세 (BOM)
          </h3>
          <div className="bg-white rounded-xl border border-slate-100 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50/50">
                    <th className="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase">
                      품목
                    </th>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase">
                      규격
                    </th>
                    <th className="px-5 py-3 text-right text-xs font-semibold text-slate-500 uppercase">
                      수량
                    </th>
                    <th className="px-5 py-3 text-right text-xs font-semibold text-slate-500 uppercase">
                      단가
                    </th>
                    <th className="px-5 py-3 text-right text-xs font-semibold text-slate-500 uppercase">
                      금액
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {result.line_items.map((item: any, idx: number) => (
                    <tr
                      key={idx}
                      className="border-b border-slate-50 last:border-0 hover:bg-slate-50/50"
                    >
                      <td className="px-5 py-3 font-medium text-slate-700">
                        {getItemName(item)}
                      </td>
                      <td className="px-5 py-3 text-slate-500">
                        {getItemSpec(item)}
                      </td>
                      <td className="px-5 py-3 text-right text-slate-600">
                        {getItemQty(item)}
                        <span className="text-slate-400 ml-0.5 text-xs">
                          {getItemUnit(item)}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-right text-slate-600">
                        {getItemUnitPrice(item) > 0
                          ? formatPrice(getItemUnitPrice(item))
                          : "-"}
                      </td>
                      <td className="px-5 py-3 text-right font-semibold text-slate-900">
                        {getItemAmount(item) > 0
                          ? formatPrice(getItemAmount(item))
                          : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
                {/* 합계 행 */}
                <tfoot>
                  <tr className="border-t-2 border-slate-200 bg-slate-50/80">
                    <td
                      colSpan={4}
                      className="px-5 py-3 text-right text-sm font-semibold text-slate-600"
                    >
                      공급가액
                    </td>
                    <td className="px-5 py-3 text-right text-sm font-bold text-slate-900">
                      {formatPrice(totalAmount)}원
                    </td>
                  </tr>
                  <tr className="bg-slate-50/80">
                    <td
                      colSpan={4}
                      className="px-5 py-2 text-right text-sm text-slate-500"
                    >
                      부가세 (10%)
                    </td>
                    <td className="px-5 py-2 text-right text-sm text-slate-600">
                      {formatPrice(vatAmount)}원
                    </td>
                  </tr>
                  <tr className="bg-blue-50/50">
                    <td
                      colSpan={4}
                      className="px-5 py-3 text-right text-base font-bold text-slate-900"
                    >
                      합계 (VAT 포함)
                    </td>
                    <td className="px-5 py-3 text-right text-base font-extrabold text-blue-700">
                      {formatPrice(totalAmount + vatAmount)}원
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ── 검증 결과 요약 ── */}
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-4">AI 검증 결과</h3>
        <div className="flex items-center gap-4 p-4 rounded-xl bg-slate-50 border border-slate-100">
          <div
            className={cn(
              "w-12 h-12 rounded-full flex items-center justify-center text-white font-bold",
              result.success ? "bg-emerald-500" : "bg-amber-500"
            )}
          >
            {stagesCompleted}/{totalStages}
          </div>
          <div>
            <p className="font-semibold text-slate-900">
              {result.success ? "모든 검증 통과" : "일부 검증 미완료"}
            </p>
            <p className="text-sm text-slate-500">
              {stagesCompleted}개 단계 완료 / 총 {totalStages}개 단계
            </p>
          </div>
        </div>
      </div>

      {/* ── 다운로드 + 액션 버튼 ── */}
      <div className="bg-slate-50 rounded-2xl p-6 border border-slate-100">
        <div className="flex flex-col gap-4">
          {/* 다운로드 버튼 */}
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={() => downloadPdf(result, state, formatPrice)}
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-red-600 text-white hover:bg-red-500 transition-all shadow-sm"
            >
              <Download className="w-4 h-4" />
              PDF 다운로드
            </button>
            <button
              onClick={() => downloadExcel(result, state, formatPrice)}
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-emerald-600 text-white hover:bg-emerald-500 transition-all shadow-sm"
            >
              <FileSpreadsheet className="w-4 h-4" />
              Excel 다운로드
            </button>
          </div>

          {/* 액션 버튼 */}
          <div className="flex flex-col sm:flex-row gap-3 pt-3 border-t border-slate-200">
            <button
              onClick={() => setShowInquiry(!showInquiry)}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-bold bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-500 hover:to-blue-600 transition-all"
            >
              <MessageSquare className="w-4 h-4" />
              주문/문의하기
            </button>
            <button
              onClick={onBack}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold text-slate-600 border border-slate-200 hover:bg-white transition-all"
            >
              <RefreshCw className="w-4 h-4" />
              구성 수정
            </button>
          </div>
        </div>
      </div>

      {/* ── 문의 폼 ── */}
      {showInquiry && !inquirySubmitted && (
        <div className="bg-white rounded-2xl p-6 border border-blue-100 space-y-4">
          <h3 className="text-lg font-bold text-slate-900">주문/견적 문의</h3>
          <p className="text-sm text-slate-500">
            견적 ID ({result.estimate_id})를 참조하여 담당자가 연락드립니다.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">
                이름/회사명 *
              </label>
              <input
                type="text"
                value={state.customerName}
                readOnly
                className="w-full px-4 py-2.5 rounded-lg border border-slate-200 bg-slate-50 text-sm"
                placeholder="입력해 주세요"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">
                연락처 *
              </label>
              <input
                type="tel"
                value={state.contactPhone}
                readOnly
                className="w-full px-4 py-2.5 rounded-lg border border-slate-200 bg-slate-50 text-sm"
                placeholder="010-0000-0000"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">
              추가 요청사항
            </label>
            <textarea
              rows={3}
              className="w-full px-4 py-2.5 rounded-lg border border-slate-200 text-sm focus:border-blue-500 outline-none resize-none"
              placeholder="납기, 수량, 특이사항 등을 입력해 주세요."
            />
          </div>
          <button
            onClick={() => setInquirySubmitted(true)}
            className="px-6 py-3 rounded-xl text-sm font-bold bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-500 hover:to-blue-600 transition-all"
          >
            문의 보내기
          </button>
        </div>
      )}

      {inquirySubmitted && (
        <div className="bg-emerald-50 rounded-2xl p-8 border border-emerald-100 text-center">
          <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-slate-900 mb-1">
            문의가 접수되었습니다
          </h3>
          <p className="text-sm text-slate-500">
            담당자가 빠른 시일 내에 연락드리겠습니다.
          </p>
          <Link
            href="/home"
            className="inline-block mt-4 text-sm font-medium text-blue-600 hover:underline"
          >
            홈으로 돌아가기
          </Link>
        </div>
      )}
    </div>
  );
}
