"use client";

import React, { useRef } from "react";
import { X, Printer } from "lucide-react";

interface Column {
  key: string;
  label: string;
  width?: string;
  align?: "left" | "center" | "right";
  format?: (value: any) => string;
}

interface PrintPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  date?: string;
  columns: Column[];
  data: any[];
  // 헤더 정보 (거래처 등)
  headerInfo?: {
    label: string;
    value: string;
  }[];
  // 합계 정보
  summary?: {
    label: string;
    value: string | number;
  }[];
  // 비고
  note?: string;
}

export function PrintPreviewModal({
  isOpen,
  onClose,
  title,
  subtitle,
  date,
  columns,
  data,
  headerInfo,
  summary,
  note,
}: PrintPreviewModalProps) {
  const printRef = useRef<HTMLDivElement>(null);

  if (!isOpen) return null;

  const handlePrint = () => {
    const printContent = printRef.current;
    if (!printContent) return;

    const printWindow = window.open("", "_blank");
    if (!printWindow) return;

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>${title}</title>
          <style>
            @page {
              size: A4 landscape;
              margin: 10mm;
            }
            body {
              font-family: 'Malgun Gothic', '맑은 고딕', sans-serif;
              font-size: 11px;
              margin: 0;
              padding: 0;
            }
            .print-container {
              width: 100%;
              max-width: 297mm;
              padding: 10mm;
              box-sizing: border-box;
            }
            .header {
              text-align: center;
              margin-bottom: 15px;
              border-bottom: 2px solid #000;
              padding-bottom: 10px;
            }
            .header h1 {
              font-size: 18px;
              margin: 0 0 5px 0;
            }
            .header .subtitle {
              font-size: 12px;
              color: #666;
            }
            .header .date {
              font-size: 11px;
              color: #333;
              margin-top: 5px;
            }
            .header-info {
              display: flex;
              flex-wrap: wrap;
              gap: 20px;
              margin-bottom: 10px;
              padding: 8px;
              background: #f5f5f5;
              border: 1px solid #ddd;
            }
            .header-info-item {
              display: flex;
              gap: 5px;
            }
            .header-info-label {
              font-weight: bold;
              color: #333;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin-bottom: 10px;
            }
            th, td {
              border: 1px solid #000;
              padding: 4px 6px;
              font-size: 10px;
            }
            th {
              background: #e0e0e0;
              font-weight: bold;
              text-align: center;
            }
            td.text-right {
              text-align: right;
            }
            td.text-center {
              text-align: center;
            }
            .summary {
              display: flex;
              justify-content: flex-end;
              gap: 30px;
              margin-top: 10px;
              padding: 10px;
              background: #f9f9f9;
              border: 1px solid #ddd;
            }
            .summary-item {
              display: flex;
              gap: 10px;
              font-weight: bold;
            }
            .note {
              margin-top: 10px;
              padding: 8px;
              background: #fff;
              border: 1px solid #ddd;
            }
            .note-label {
              font-weight: bold;
              margin-bottom: 5px;
            }
            .footer {
              margin-top: 20px;
              text-align: center;
              font-size: 10px;
              color: #666;
              border-top: 1px solid #ddd;
              padding-top: 10px;
            }
            @media print {
              body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            }
          </style>
        </head>
        <body>
          ${printContent.innerHTML}
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
      printWindow.close();
    }, 250);
  };

  const formatValue = (column: Column, value: any): string => {
    if (column.format) return column.format(value);
    if (value === null || value === undefined) return "";
    if (typeof value === "number") return value.toLocaleString();
    return String(value);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-[95vw] max-w-[1200px] h-[90vh] flex flex-col">
        {/* 모달 헤더 */}
        <div className="flex items-center justify-between px-4 py-3 bg-gray-100 border-b rounded-t-lg">
          <span className="text-sm font-medium">인쇄 미리보기</span>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="flex items-center gap-1 px-4 py-1.5 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
            >
              <Printer className="h-4 w-4" />
              인쇄
            </button>
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-200 rounded"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* 미리보기 영역 (A4 가로) */}
        <div className="flex-1 overflow-auto bg-gray-300 p-4">
          <div
            ref={printRef}
            className="bg-white mx-auto shadow-lg"
            style={{
              width: "297mm",
              minHeight: "210mm",
              padding: "10mm",
              boxSizing: "border-box",
            }}
          >
            <div className="print-container">
              {/* 헤더 */}
              <div className="header" style={{ textAlign: "center", marginBottom: "15px", borderBottom: "2px solid #000", paddingBottom: "10px" }}>
                <h1 style={{ fontSize: "18px", margin: "0 0 5px 0" }}>{title}</h1>
                {subtitle && <div className="subtitle" style={{ fontSize: "12px", color: "#666" }}>{subtitle}</div>}
                {date && <div className="date" style={{ fontSize: "11px", color: "#333", marginTop: "5px" }}>일자: {date}</div>}
              </div>

              {/* 헤더 정보 */}
              {headerInfo && headerInfo.length > 0 && (
                <div
                  className="header-info"
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "20px",
                    marginBottom: "10px",
                    padding: "8px",
                    background: "#f5f5f5",
                    border: "1px solid #ddd",
                  }}
                >
                  {headerInfo.map((info, idx) => (
                    <div key={idx} className="header-info-item" style={{ display: "flex", gap: "5px" }}>
                      <span className="header-info-label" style={{ fontWeight: "bold", color: "#333" }}>{info.label}:</span>
                      <span>{info.value}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* 테이블 */}
              <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: "10px" }}>
                <thead>
                  <tr>
                    <th style={{ border: "1px solid #000", padding: "4px 6px", fontSize: "10px", background: "#e0e0e0", fontWeight: "bold", textAlign: "center", width: "40px" }}>No</th>
                    {columns.map((col) => (
                      <th
                        key={col.key}
                        style={{
                          border: "1px solid #000",
                          padding: "4px 6px",
                          fontSize: "10px",
                          background: "#e0e0e0",
                          fontWeight: "bold",
                          textAlign: "center",
                          width: col.width,
                        }}
                      >
                        {col.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.map((row, idx) => (
                    <tr key={idx}>
                      <td style={{ border: "1px solid #000", padding: "4px 6px", fontSize: "10px", textAlign: "center" }}>{idx + 1}</td>
                      {columns.map((col) => (
                        <td
                          key={col.key}
                          style={{
                            border: "1px solid #000",
                            padding: "4px 6px",
                            fontSize: "10px",
                            textAlign: col.align || "left",
                          }}
                        >
                          {formatValue(col, row[col.key])}
                        </td>
                      ))}
                    </tr>
                  ))}
                  {/* 빈 행 채우기 (최소 10행) */}
                  {Array.from({ length: Math.max(0, 10 - data.length) }).map((_, idx) => (
                    <tr key={`empty-${idx}`}>
                      <td style={{ border: "1px solid #000", padding: "4px 6px", fontSize: "10px", textAlign: "center" }}>&nbsp;</td>
                      {columns.map((col, colIdx) => (
                        <td
                          key={colIdx}
                          style={{ border: "1px solid #000", padding: "4px 6px", fontSize: "10px" }}
                        >
                          &nbsp;
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* 합계 정보 */}
              {summary && summary.length > 0 && (
                <div
                  className="summary"
                  style={{
                    display: "flex",
                    justifyContent: "flex-end",
                    gap: "30px",
                    marginTop: "10px",
                    padding: "10px",
                    background: "#f9f9f9",
                    border: "1px solid #ddd",
                  }}
                >
                  {summary.map((item, idx) => (
                    <div key={idx} className="summary-item" style={{ display: "flex", gap: "10px", fontWeight: "bold" }}>
                      <span>{item.label}:</span>
                      <span>{typeof item.value === "number" ? item.value.toLocaleString() : item.value}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* 비고 */}
              {note && (
                <div className="note" style={{ marginTop: "10px", padding: "8px", background: "#fff", border: "1px solid #ddd" }}>
                  <div className="note-label" style={{ fontWeight: "bold", marginBottom: "5px" }}>비고:</div>
                  <div>{note}</div>
                </div>
              )}

              {/* 푸터 */}
              <div className="footer" style={{ marginTop: "20px", textAlign: "center", fontSize: "10px", color: "#666", borderTop: "1px solid #ddd", paddingTop: "10px" }}>
                이지판매재고관리 - 출력일시: {new Date().toLocaleString("ko-KR")}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
