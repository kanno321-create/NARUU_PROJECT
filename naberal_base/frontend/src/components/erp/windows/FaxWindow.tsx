"use client";

import React, { useState, useEffect, useRef } from "react";
import { useWindowContextOptional } from "../ERPContext";

interface Customer {
  id: string;
  code: string;
  name: string;
  phone: string;
  manager: string;
  fax: string;
}

interface FaxRecipient {
  id: string;
  faxNumber: string;
  hasError: boolean;
}

interface FaxHistoryItem {
  faxNumbers: string[];
  fileName: string;
  sentAt: string;
  status: "queued" | "sent" | "failed";
}

async function sendFax(faxNumbers: string[], fileName: string): Promise<{ success: boolean; message: string }> {
  // TODO[KIS-FAX]: API 키 연동 후 실제 전송
  const history: FaxHistoryItem[] = JSON.parse(localStorage.getItem("fax-history") || "[]");
  history.unshift({
    faxNumbers,
    fileName,
    sentAt: new Date().toISOString(),
    status: "queued",
  });
  localStorage.setItem("fax-history", JSON.stringify(history));
  return { success: true, message: `${faxNumbers.length}건 팩스 전송 대기` };
}

function getFaxPoint(): number {
  const pointStr = localStorage.getItem("fax-point");
  return pointStr ? parseInt(pointStr, 10) : 160;
}

// 이지판매재고관리 원본 데이터 100% 복제 (2025-12-05 스크린샷 기준)
const ORIGINAL_CUSTOMERS: Customer[] = [
  { id: "1", code: "m001", name: "테스트사업장", phone: "02-456-7890", manager: "김사장", fax: "02-145-6851" },
  { id: "2", code: "m002", name: "이지사업장", phone: "032-452-1230", manager: "김사장", fax: "032-111-1111" },
  { id: "3", code: "m003", name: "재고사업장", phone: "051-754-9652", manager: "최사장", fax: "051-754-9630" },
];

export function FaxWindow() {
  const windowContext = useWindowContextOptional();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCustomer, setSelectedCustomer] = useState<string | null>(null);
  const [filePath, setFilePath] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [recipients, setRecipients] = useState<FaxRecipient[]>([]);
  const [newFaxNumber, setNewFaxNumber] = useState("");
  const [customers, setCustomers] = useState<Customer[]>(ORIGINAL_CUSTOMERS);
  const [point, setPoint] = useState(160);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [faxHistory, setFaxHistory] = useState<FaxHistoryItem[]>([]);
  const [showPreviewModal, setShowPreviewModal] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("erp-customers");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setCustomers(parsed.map((c: any) => ({
            ...c,
            manager: c.manager || "",
            fax: c.fax || "",
          })));
        }
      }
    } catch {
      // 로드 실패 시 기본 데이터 사용
    }
    setPoint(getFaxPoint());
  }, []);

  const filteredCustomers = customers.filter(
    (c) =>
      c.name.includes(searchQuery) ||
      c.code.includes(searchQuery) ||
      c.phone.includes(searchQuery) ||
      c.fax.includes(searchQuery)
  );

  const handleDoubleClick = (customer: Customer) => {
    if (!recipients.find((r) => r.faxNumber === customer.fax)) {
      setRecipients([
        ...recipients,
        { id: Date.now().toString(), faxNumber: customer.fax, hasError: false },
      ]);
    }
  };

  const handleAddFax = () => {
    if (newFaxNumber && !recipients.find((r) => r.faxNumber === newFaxNumber)) {
      const hasError = !/^\d{2,3}-\d{3,4}-\d{4}$/.test(newFaxNumber);
      setRecipients([
        ...recipients,
        { id: Date.now().toString(), faxNumber: newFaxNumber, hasError },
      ]);
      setNewFaxNumber("");
    }
  };

  const handleRemoveFax = () => {
    if (selectedCustomer) {
      setRecipients(recipients.filter((r) => r.id !== selectedCustomer));
      setSelectedCustomer(null);
    }
  };

  const handleClearAll = () => {
    setRecipients([]);
  };

  const handleFileBrowse = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setFilePath(file.name);
    }
  };

  const handlePreview = () => {
    if (!selectedFile && !filePath) {
      alert("첨부파일을 선택하세요.");
      return;
    }
    setShowPreviewModal(true);
  };

  const handleCharge = () => {
    alert("포인트 충전 페이지로 이동합니다.\n(외부 결제 연동 준비 중)");
  };

  const handleViewHistory = () => {
    const history: FaxHistoryItem[] = JSON.parse(localStorage.getItem("fax-history") || "[]");
    setFaxHistory(history);
    setShowHistoryModal(true);
  };

  const handleRefresh = () => {
    setPoint(getFaxPoint());
    const history: FaxHistoryItem[] = JSON.parse(localStorage.getItem("fax-history") || "[]");
    // 전송 상태 업데이트 (시뮬레이션)
    const updated = history.map((h) => {
      if (h.status === "queued") {
        const sentTime = new Date(h.sentAt).getTime();
        const now = Date.now();
        if (now - sentTime > 30000) {
          return { ...h, status: "sent" as const };
        }
      }
      return h;
    });
    localStorage.setItem("fax-history", JSON.stringify(updated));
  };

  const handleSend = async () => {
    const validRecipients = recipients.filter((r) => !r.hasError);
    if (validRecipients.length === 0) {
      alert("수신 팩스 번호를 추가하세요.");
      return;
    }
    if (!filePath) {
      alert("첨부파일을 선택하세요.");
      return;
    }
    const result = await sendFax(
      validRecipients.map((r) => r.faxNumber),
      filePath
    );
    if (result.success) {
      alert(result.message);
    }
  };

  const handleClose = () => {
    windowContext?.closeThisWindow();
  };

  const errorRecipients = recipients.filter((r) => r.hasError);

  return (
    <div className="relative flex h-full flex-col bg-gray-100">
      {/* hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.png,.tif,.tiff"
        onChange={handleFileChange}
      />

      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">팩스 전송</span>
      </div>

      <div className="flex-1 overflow-auto p-4">
        {/* 결제정보 */}
        <fieldset className="mb-4 rounded border border-gray-400 p-3">
          <legend className="px-2 text-sm text-blue-700">결제정보</legend>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <span>사용자 아이디:</span>
              <input
                type="text"
                value="easypanme"
                readOnly
                className="w-28 rounded border border-gray-400 bg-white px-2 py-1 text-sm"
              />
            </div>
            <button
              onClick={handleCharge}
              className="rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
            >
              충전하기
            </button>
            <button
              onClick={handleViewHistory}
              className="rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
            >
              포인트 사용내역 조회
            </button>
          </div>
          <div className="mt-2 flex items-center gap-2 text-sm">
            <span>충전된 포인트:</span>
            <input
              type="text"
              value={point.toString()}
              readOnly
              className="w-20 rounded border border-gray-400 bg-white px-2 py-1 text-sm text-right"
            />
            <button
              onClick={handleRefresh}
              className="rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
            >
              새로고침
            </button>
          </div>
        </fieldset>

        {/* 첨부파일 위치 */}
        <fieldset className="mb-4 rounded border border-gray-400 p-3">
          <legend className="px-2 text-sm text-blue-700">
            첨부파일 위치 (파일명이 한글일 경우 전송이 안될 수 있습니다.)
          </legend>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
              className="flex-1 rounded border border-gray-400 px-2 py-1 text-sm"
              placeholder="파일 경로"
            />
            <button
              onClick={handleFileBrowse}
              className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
            >
              파일찾기
            </button>
            <button
              onClick={handlePreview}
              className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
            >
              미리보기
            </button>
          </div>
        </fieldset>

        {/* 거래처 검색 */}
        <fieldset className="mb-4 rounded border border-gray-400 p-3">
          <legend className="px-2 text-sm text-blue-700">
            거래처 검색 (거래처 더블클릭시 수신팩스에 추가 됩니다.)
          </legend>
          <div className="mb-2 flex items-center gap-2">
            <span className="text-sm">검색어 :</span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-32 rounded border border-gray-400 px-2 py-1 text-sm"
            />
            <button
              onClick={() => {/* searchQuery already triggers filter via filteredCustomers */}}
              className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
            >
              검 색
            </button>
            <button
              onClick={() => setSearchQuery("")}
              className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
            >
              전체보기
            </button>
          </div>

          {/* 거래처 그리드 */}
          <div className="h-32 overflow-auto border border-gray-400">
            <table className="w-full border-collapse text-xs">
              <thead className="sticky top-0 bg-[#E8E4D9]">
                <tr>
                  <th className="border-b border-r border-gray-300 px-2 py-1">거래처코드</th>
                  <th className="border-b border-r border-gray-300 px-2 py-1">거래처명</th>
                  <th className="border-b border-r border-gray-300 px-2 py-1">전화번호</th>
                  <th className="border-b border-r border-gray-300 px-2 py-1">이름</th>
                  <th className="border-b border-gray-300 px-2 py-1">팩스번호</th>
                </tr>
              </thead>
              <tbody>
                {filteredCustomers.map((c) => (
                  <tr
                    key={c.id}
                    className="cursor-pointer hover:bg-gray-100"
                    onDoubleClick={() => handleDoubleClick(c)}
                  >
                    <td className="border-b border-r border-gray-200 px-2 py-1">{c.code}</td>
                    <td className="border-b border-r border-gray-200 px-2 py-1">{c.name}</td>
                    <td className="border-b border-r border-gray-200 px-2 py-1">{c.phone}</td>
                    <td className="border-b border-r border-gray-200 px-2 py-1">{c.manager}</td>
                    <td className="border-b border-gray-200 px-2 py-1">{c.fax}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </fieldset>

        {/* 수신정보 */}
        <fieldset className="rounded border border-gray-400 p-3">
          <legend className="px-2 text-sm text-blue-700">수신정보</legend>
          <div className="flex gap-4">
            {/* 수신 팩스 */}
            <div className="flex-1">
              <div className="mb-1 flex items-center gap-2">
                <span className="text-sm">수신 팩스 :</span>
                <input
                  type="text"
                  value={newFaxNumber}
                  onChange={(e) => setNewFaxNumber(e.target.value)}
                  className="w-32 rounded border border-gray-400 px-2 py-1 text-sm"
                  placeholder="02-000-0000"
                  onKeyDown={(e) => { if (e.key === "Enter") handleAddFax(); }}
                />
                <button
                  onClick={handleAddFax}
                  className="rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
                >
                  추가
                </button>
                <button
                  onClick={handleRemoveFax}
                  className="rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
                >
                  삭제
                </button>
              </div>
              <div className="h-24 overflow-auto border border-gray-400 bg-white p-1">
                {recipients
                  .filter((r) => !r.hasError)
                  .map((r) => (
                    <div
                      key={r.id}
                      className={`cursor-pointer px-1 text-xs ${
                        selectedCustomer === r.id ? "bg-[#316AC5] text-white" : ""
                      }`}
                      onClick={() => setSelectedCustomer(r.id)}
                    >
                      {r.faxNumber}
                    </div>
                  ))}
              </div>
            </div>

            {/* 번호 오류 체크 */}
            <div className="flex-1">
              <div className="mb-1 flex items-center justify-between">
                <span className="text-sm">번호 오류 체크 :</span>
                <button
                  onClick={handleClearAll}
                  className="rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
                >
                  전체삭제
                </button>
              </div>
              <div className="h-24 overflow-auto border border-gray-400 bg-white p-1">
                {errorRecipients.map((r) => (
                  <div key={r.id} className="px-1 text-xs text-red-600">
                    {r.faxNumber} (오류)
                  </div>
                ))}
              </div>
            </div>
          </div>
        </fieldset>
      </div>

      {/* 하단 버튼 */}
      <div className="flex justify-end gap-2 border-t bg-gray-200 px-4 py-2">
        <button
          onClick={handleSend}
          className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
        >
          팩스 전송
        </button>
        <button
          onClick={handleClose}
          className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
        >
          닫기
        </button>
      </div>

      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">loading ok</div>

      {/* 미리보기 모달 */}
      {showPreviewModal && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-[400px] rounded-lg border bg-white shadow-xl">
            <div className="flex items-center justify-between border-b bg-blue-600 px-4 py-2">
              <span className="text-sm font-medium text-white">파일 미리보기</span>
              <button onClick={() => setShowPreviewModal(false)} className="text-white hover:text-gray-200">X</button>
            </div>
            <div className="p-4">
              <div className="mb-3 rounded border bg-gray-50 p-3">
                <p className="text-sm"><strong>파일명:</strong> {filePath}</p>
                {selectedFile && (
                  <>
                    <p className="text-sm"><strong>크기:</strong> {(selectedFile.size / 1024).toFixed(1)} KB</p>
                    <p className="text-sm"><strong>유형:</strong> {selectedFile.type || "알 수 없음"}</p>
                    <p className="text-sm"><strong>수정일:</strong> {new Date(selectedFile.lastModified).toLocaleString("ko-KR")}</p>
                  </>
                )}
              </div>
              {selectedFile && selectedFile.type.startsWith("image/") && (
                <div className="rounded border p-2">
                  <img
                    src={URL.createObjectURL(selectedFile)}
                    alt="미리보기"
                    className="max-h-48 w-full object-contain"
                  />
                </div>
              )}
            </div>
            <div className="flex justify-end border-t px-4 py-2">
              <button
                onClick={() => setShowPreviewModal(false)}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-sm hover:bg-gray-200"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 전송내역 모달 */}
      {showHistoryModal && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-[500px] max-h-[400px] rounded-lg border bg-white shadow-xl">
            <div className="flex items-center justify-between border-b bg-blue-600 px-4 py-2">
              <span className="text-sm font-medium text-white">팩스 전송내역</span>
              <button onClick={() => setShowHistoryModal(false)} className="text-white hover:text-gray-200">X</button>
            </div>
            <div className="max-h-[300px] overflow-auto p-4">
              {faxHistory.length === 0 ? (
                <p className="text-center text-sm text-gray-500">전송 내역이 없습니다.</p>
              ) : (
                <table className="w-full border-collapse text-xs">
                  <thead className="sticky top-0 bg-gray-100">
                    <tr>
                      <th className="border px-2 py-1">전송일시</th>
                      <th className="border px-2 py-1">수신번호</th>
                      <th className="border px-2 py-1">파일</th>
                      <th className="border px-2 py-1">상태</th>
                    </tr>
                  </thead>
                  <tbody>
                    {faxHistory.map((h, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="border px-2 py-1">{new Date(h.sentAt).toLocaleString("ko-KR")}</td>
                        <td className="border px-2 py-1">{h.faxNumbers.join(", ")}</td>
                        <td className="border px-2 py-1 truncate max-w-[100px]">{h.fileName}</td>
                        <td className="border px-2 py-1 text-center">
                          <span className={h.status === "queued" ? "text-orange-600" : h.status === "sent" ? "text-green-600" : "text-red-600"}>
                            {h.status === "queued" ? "대기" : h.status === "sent" ? "전송" : "실패"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            <div className="flex justify-end border-t px-4 py-2">
              <button
                onClick={() => setShowHistoryModal(false)}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-sm hover:bg-gray-200"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
