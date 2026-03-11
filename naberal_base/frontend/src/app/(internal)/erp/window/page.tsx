"use client";

import React, { useEffect, useState } from "react";
import { ERPDataProvider } from "@/contexts/ERPDataContext";
import { ERPProvider } from "@/components/erp/ERPContext";
import ERPWindowContent from "@/components/erp/ERPWindowContent";

/**
 * ERP 독립 윈도우 페이지
 * Electron에서 새 BrowserWindow로 열릴 때 사용
 * URL: /erp/window/?type=customer&title=거래처등록
 */
export default function ERPWindowPage() {
  const [windowType, setWindowType] = useState<string | null>(null);
  const [windowTitle, setWindowTitle] = useState<string>("ERP");

  useEffect(() => {
    // URL에서 type, title 파라미터 읽기
    const params = new URLSearchParams(window.location.search);
    const type = params.get("type");
    const title = params.get("title");

    if (type) setWindowType(type);
    if (title) {
      setWindowTitle(title);
      document.title = `${title} - KIS ERP`;
    }
  }, []);

  if (!windowType) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-100">
        <p className="text-sm text-gray-500">윈도우 타입이 지정되지 않았습니다.</p>
      </div>
    );
  }

  return (
    <ERPDataProvider>
      <ERPProvider
        openWindow={(type, title) => {
          // 독립 윈도우에서 다른 윈도우를 열 때도 새 OS 창으로 열기
          const IS_ELECTRON = typeof window !== "undefined" && !!(window as any).electronAPI;
          if (IS_ELECTRON && (window as any).electronAPI?.openERPWindow) {
            (window as any).electronAPI.openERPWindow(type, title);
          } else {
            // 웹 환경: 새 탭으로 열기
            window.open(`/erp/window/?type=${encodeURIComponent(type)}&title=${encodeURIComponent(title)}`, "_blank");
          }
        }}
        closeWindow={() => {
          window.close();
        }}
      >
        <div className="flex h-screen flex-col bg-surface overflow-hidden">
          <ERPWindowContent type={windowType} />
        </div>
      </ERPProvider>
    </ERPDataProvider>
  );
}
