"use client";

import React, { useState, useEffect, useRef } from "react";
import { useWindowContextOptional } from "../ERPContext";

interface Customer {
  id: string;
  code: string;
  name: string;
  phone: string;
}

// SMS API 인터페이스 (실제 API 키 연동 시 즉시 사용 가능하도록)
interface SmsApiRequest {
  sender: string;
  recipients: string[];
  message: string;
  type: "SMS" | "LMS";
  scheduled?: { date: string; time: string };
}

interface SmsHistoryItem extends SmsApiRequest {
  sentAt: string;
  status: "queued" | "sent" | "failed";
}

async function sendSms(request: SmsApiRequest): Promise<{ success: boolean; message: string }> {
  // TODO[KIS-SMS]: API 키 연동 후 실제 전송
  // 현재는 localStorage에 이력 저장
  const history: SmsHistoryItem[] = JSON.parse(localStorage.getItem("sms-history") || "[]");
  history.unshift({ ...request, sentAt: new Date().toISOString(), status: "queued" });
  localStorage.setItem("sms-history", JSON.stringify(history));
  return { success: true, message: `${request.recipients.length}건 전송 대기` };
}

function getSmsPoint(): number {
  const pointStr = localStorage.getItem("sms-point");
  return pointStr ? parseInt(pointStr, 10) : 160;
}

// 이지판매재고관리 원본 데이터 100% 복제 (2025-12-05 스크린샷 기준)
const ORIGINAL_CUSTOMERS: Customer[] = [
  { id: "1", code: "m001", name: "테스트사업장", phone: "010-1234-5678" },
  { id: "2", code: "m002", name: "이지사업장", phone: "010-2345-6789" },
  { id: "3", code: "m003", name: "재고사업장", phone: "010-3456-7890" },
];

export function SmsWindow() {
  const windowContext = useWindowContextOptional();
  const [activeTab, setActiveTab] = useState<"SMS" | "LMS">("SMS");
  const [message, setMessage] = useState("");
  const [senderNumber, setSenderNumber] = useState("01044389180");
  const [autoLms, setAutoLms] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCustomers, setSelectedCustomers] = useState<string[]>([]);
  const [recipients, setRecipients] = useState<string[]>([]);
  const [newRecipient, setNewRecipient] = useState("");
  const [scheduleEnabled, setScheduleEnabled] = useState(false);
  const [scheduleDate, setScheduleDate] = useState(new Date().toISOString().split("T")[0]);
  const [scheduleTime, setScheduleTime] = useState("17:58");
  const [customers, setCustomers] = useState<Customer[]>(ORIGINAL_CUSTOMERS);
  const [point, setPoint] = useState(160);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [smsHistory, setSmsHistory] = useState<SmsHistoryItem[]>([]);

  useEffect(() => {
    // 거래처 데이터 로드 시도
    try {
      const stored = localStorage.getItem("erp-customers");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setCustomers(parsed);
        }
      }
    } catch {
      // 로드 실패 시 기본 데이터 사용
    }
    setPoint(getSmsPoint());
  }, []);

  const filteredCustomers = customers.filter(
    (c) => c.name.includes(searchQuery) || c.code.includes(searchQuery) || c.phone.includes(searchQuery)
  );

  const maxBytes = activeTab === "SMS" ? 90 : 2000;
  const currentBytes = new TextEncoder().encode(message).length;

  const handleAddAll = () => {
    const phones = filteredCustomers.map((c) => c.phone);
    setRecipients([...new Set([...recipients, ...phones])]);
  };

  const handleAddSelected = () => {
    const phones = filteredCustomers
      .filter((c) => selectedCustomers.includes(c.id))
      .map((c) => c.phone);
    setRecipients([...new Set([...recipients, ...phones])]);
  };

  const handleAddRecipient = () => {
    if (newRecipient && !recipients.includes(newRecipient)) {
      setRecipients([...recipients, newRecipient]);
      setNewRecipient("");
    }
  };

  const handleClearAll = () => {
    setRecipients([]);
  };

  const handleSend = async () => {
    if (recipients.length === 0) {
      alert("수신번호를 추가하세요.");
      return;
    }
    if (!message) {
      alert("메시지를 입력하세요.");
      return;
    }

    const msgType: "SMS" | "LMS" = autoLms && currentBytes > 90 ? "LMS" : activeTab;

    const request: SmsApiRequest = {
      sender: senderNumber,
      recipients: [...recipients],
      message,
      type: msgType,
    };

    if (scheduleEnabled) {
      request.scheduled = { date: scheduleDate, time: scheduleTime };
    }

    const result = await sendSms(request);
    if (result.success) {
      alert(`${result.message}\n${scheduleEnabled ? `예약: ${scheduleDate} ${scheduleTime}` : "즉시 전송"}`);
    }
  };

  const handleScheduleSend = async () => {
    if (!scheduleEnabled) {
      alert("예약전송을 활성화해주세요.");
      return;
    }
    if (recipients.length === 0) {
      alert("수신번호를 추가하세요.");
      return;
    }
    if (!message) {
      alert("메시지를 입력하세요.");
      return;
    }

    const msgType: "SMS" | "LMS" = autoLms && currentBytes > 90 ? "LMS" : activeTab;

    const request: SmsApiRequest = {
      sender: senderNumber,
      recipients: [...recipients],
      message,
      type: msgType,
      scheduled: { date: scheduleDate, time: scheduleTime },
    };

    const result = await sendSms(request);
    if (result.success) {
      alert(`예약 전송 등록 완료\n예약 시각: ${scheduleDate} ${scheduleTime}\n${result.message}`);
    }
  };

  const handleCheckPoint = () => {
    const currentPoint = getSmsPoint();
    setPoint(currentPoint);
    alert(`현재 잔여 포인트: ${currentPoint}P\n\nSMS 1건: 20P\nLMS 1건: 50P`);
  };

  const handleViewHistory = () => {
    const history: SmsHistoryItem[] = JSON.parse(localStorage.getItem("sms-history") || "[]");
    setSmsHistory(history);
    setShowHistoryModal(true);
  };

  const handleRefreshPoint = () => {
    const currentPoint = getSmsPoint();
    setPoint(currentPoint);
  };

  const handleClose = () => {
    windowContext?.closeThisWindow();
  };

  const handleCancel = () => {
    setMessage("");
    setRecipients([]);
    setSelectedCustomers([]);
  };

  return (
    <div className="relative flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">문자 발송</span>
      </div>

      <div className="flex flex-1 overflow-hidden p-4">
        {/* 좌측: 메시지 입력 */}
        <div className="w-80 pr-4">
          {/* 탭 */}
          <div className="mb-2 flex border-b">
            <button
              onClick={() => setActiveTab("SMS")}
              className={`px-4 py-1 text-sm ${activeTab === "SMS" ? "border-b-2 border-blue-600 font-medium" : ""}`}
            >
              SMS
            </button>
            <button
              onClick={() => setActiveTab("LMS")}
              className={`px-4 py-1 text-sm ${activeTab === "LMS" ? "border-b-2 border-blue-600 font-medium" : ""}`}
            >
              LMS
            </button>
          </div>

          {/* 폰 미리보기 */}
          <div className="mb-2 rounded-lg border-2 border-gray-400 bg-white p-4">
            <div className="mb-2 flex items-center justify-between text-xs text-gray-500">
              <span>Tall</span>
              <div className="flex gap-1">
                <span>📶</span>
                <span>🔋</span>
              </div>
            </div>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="h-24 w-full resize-none border border-gray-300 p-2 text-sm"
              placeholder="문자 내용을 입력하세요"
              maxLength={maxBytes * 2}
            />
            <div className="text-right text-xs text-gray-500">
              {currentBytes} / {maxBytes} 바이트
            </div>
          </div>

          {/* 두 번째 입력창 (LMS용) */}
          {activeTab === "LMS" && (
            <div className="mb-2 rounded-lg border-2 border-gray-400 bg-white p-4">
              <textarea
                className="h-24 w-full resize-none border border-gray-300 p-2 text-sm"
                placeholder="추가 내용"
              />
              <div className="text-right text-xs text-gray-500">0 / 90 바이트</div>
            </div>
          )}

          {/* 자동 LMS 전환 */}
          <label className="mb-3 flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={autoLms}
              onChange={(e) => setAutoLms(e.target.checked)}
            />
            90바이트 초과시 자동 LMS전환
          </label>

          {/* 발신번호 */}
          <div className="mb-3 flex items-center gap-2">
            <span className="text-sm">발신번호:</span>
            <select
              value={senderNumber}
              onChange={(e) => setSenderNumber(e.target.value)}
              className="flex-1 rounded border border-gray-400 px-2 py-1 text-sm"
            >
              <option value="01044389180">01044389180</option>
            </select>
            <button className="rounded border border-gray-400 bg-gray-100 px-2 py-1 text-sm hover:bg-gray-200">
              발신번호 등록
            </button>
          </div>

          {/* 전송/취소 버튼 */}
          <div className="flex gap-2">
            <button
              onClick={handleSend}
              className="flex-1 rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
            >
              전송
            </button>
            <button
              onClick={handleCancel}
              className="flex-1 rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
            >
              취소
            </button>
          </div>

          {scheduleEnabled && (
            <button
              onClick={handleScheduleSend}
              className="mt-2 w-full rounded border border-blue-400 bg-blue-50 px-4 py-1.5 text-sm text-blue-700 hover:bg-blue-100"
            >
              예약전송
            </button>
          )}

          <div className="mt-2 text-xs text-green-600">loading ok</div>
        </div>

        {/* 우측: 결제정보 & 수신번호 */}
        <div className="flex-1 border-l pl-4">
          {/* 문자 결제정보 */}
          <fieldset className="mb-4 rounded border border-gray-400 p-3">
            <legend className="px-2 text-sm text-blue-700">문자 결제정보</legend>
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <span>사용자 아이디:</span>
                <span className="font-medium text-blue-600">easypanme</span>
              </div>
              <button
                onClick={() => alert("포인트 충전 페이지로 이동합니다.\n(외부 결제 연동 준비 중)")}
                className="rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
              >
                포인트 충전
              </button>
              <button
                onClick={handleViewHistory}
                className="rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
              >
                문자 사용내역 조회
              </button>
            </div>
            <div className="mt-2 flex items-center gap-2 text-sm">
              <span>충전된 포인트:</span>
              <span className="font-medium text-blue-600">{point}</span>
              <button
                onClick={handleRefreshPoint}
                className="rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
              >
                새로고침
              </button>
              <button
                onClick={handleCheckPoint}
                className="rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
              >
                잔여포인트 조회
              </button>
            </div>
          </fieldset>

          {/* 수신번호 추가 */}
          <fieldset className="mb-4 rounded border border-gray-400 p-3">
            <legend className="px-2 text-sm text-blue-700">수신번호 추가</legend>

            {/* 거래처 검색 */}
            <div className="mb-2 flex items-center gap-2">
              <span className="text-sm">거래처 검색</span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-32 rounded border border-gray-400 px-2 py-1 text-sm"
                placeholder="검색어"
              />
              <button
                onClick={() => {/* searchQuery already triggers filter */}}
                className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
              >
                검 색(F)
              </button>
              <button
                onClick={() => setSearchQuery("")}
                className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
              >
                전체보기
              </button>
            </div>

            {/* 거래처 그리드 */}
            <div className="mb-2 h-32 overflow-auto border border-gray-400">
              <table className="w-full border-collapse text-xs">
                <thead className="sticky top-0 bg-[#E8E4D9]">
                  <tr>
                    <th className="border-b border-gray-300 px-2 py-1">거래처코드</th>
                    <th className="border-b border-gray-300 px-2 py-1">거래처명</th>
                    <th className="border-b border-gray-300 px-2 py-1">핸드폰</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCustomers.map((c) => (
                    <tr
                      key={c.id}
                      className={`cursor-pointer ${selectedCustomers.includes(c.id) ? "bg-[#316AC5] text-white" : "hover:bg-gray-100"}`}
                      onClick={() => {
                        if (selectedCustomers.includes(c.id)) {
                          setSelectedCustomers(selectedCustomers.filter((id) => id !== c.id));
                        } else {
                          setSelectedCustomers([...selectedCustomers, c.id]);
                        }
                      }}
                    >
                      <td className="border-b border-gray-200 px-2 py-1">{c.code}</td>
                      <td className="border-b border-gray-200 px-2 py-1">{c.name}</td>
                      <td className="border-b border-gray-200 px-2 py-1">{c.phone}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mb-2 flex gap-2">
              <button
                onClick={handleAddAll}
                className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-xs hover:bg-gray-200"
              >
                전체추가
              </button>
              <button
                onClick={handleAddSelected}
                className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-xs hover:bg-gray-200"
              >
                선택추가
              </button>
            </div>

            {/* 수신번호 직접 추가 */}
            <div className="mb-2 flex items-center gap-2">
              <span className="text-sm">수신번호 추가</span>
              <input
                type="text"
                value={newRecipient}
                onChange={(e) => setNewRecipient(e.target.value)}
                className="w-32 rounded border border-gray-400 px-2 py-1 text-sm"
                placeholder="010-0000-0000"
                onKeyDown={(e) => { if (e.key === "Enter") handleAddRecipient(); }}
              />
              <button
                onClick={handleAddRecipient}
                className="rounded border border-gray-400 bg-gray-200 px-2 py-1 text-sm hover:bg-gray-300"
              >
                &gt;&gt;
              </button>
            </div>

            {/* 수신번호 리스트 */}
            <div className="flex items-start gap-2">
              <span className="text-sm">수신번호 리스트</span>
              <div className="h-16 w-32 overflow-auto border border-gray-400 bg-white p-1">
                {recipients.map((r, i) => (
                  <div key={i} className="text-xs">{r}</div>
                ))}
              </div>
              <span className="text-sm">{recipients.length}명</span>
              <button
                onClick={handleClearAll}
                className="rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
              >
                모두삭제
              </button>
            </div>
          </fieldset>

          {/* 예약전송 */}
          <fieldset className="rounded border border-gray-400 p-3">
            <legend className="px-2 text-sm text-blue-700">예약전송</legend>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={scheduleEnabled}
                  onChange={(e) => setScheduleEnabled(e.target.checked)}
                />
                예약전송
              </label>
              <input
                type="date"
                value={scheduleDate}
                onChange={(e) => setScheduleDate(e.target.value)}
                disabled={!scheduleEnabled}
                className="rounded border border-gray-400 px-2 py-1 text-sm disabled:bg-gray-100"
              />
              <input
                type="time"
                value={scheduleTime}
                onChange={(e) => setScheduleTime(e.target.value)}
                disabled={!scheduleEnabled}
                className="rounded border border-gray-400 px-2 py-1 text-sm disabled:bg-gray-100"
              />
            </div>
          </fieldset>

          <div className="mt-3 text-sm text-red-600">
            * 문자작성시 #을 넣으시면 해당위치에 거래처명이 입력되어 전송됩니다.
          </div>
        </div>
      </div>

      {/* 닫기 버튼 */}
      <div className="flex justify-end border-t bg-gray-200 px-4 py-2">
        <button
          onClick={handleClose}
          className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
        >
          닫기
        </button>
      </div>

      {/* 전송내역 조회 모달 */}
      {showHistoryModal && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-[500px] max-h-[400px] rounded-lg border bg-white shadow-xl">
            <div className="flex items-center justify-between border-b bg-blue-600 px-4 py-2">
              <span className="text-sm font-medium text-white">문자 전송내역</span>
              <button onClick={() => setShowHistoryModal(false)} className="text-white hover:text-gray-200">X</button>
            </div>
            <div className="max-h-[300px] overflow-auto p-4">
              {smsHistory.length === 0 ? (
                <p className="text-center text-sm text-gray-500">전송 내역이 없습니다.</p>
              ) : (
                <table className="w-full border-collapse text-xs">
                  <thead className="sticky top-0 bg-gray-100">
                    <tr>
                      <th className="border px-2 py-1">전송일시</th>
                      <th className="border px-2 py-1">유형</th>
                      <th className="border px-2 py-1">수신자수</th>
                      <th className="border px-2 py-1">상태</th>
                      <th className="border px-2 py-1">메시지</th>
                    </tr>
                  </thead>
                  <tbody>
                    {smsHistory.map((h, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="border px-2 py-1">{new Date(h.sentAt).toLocaleString("ko-KR")}</td>
                        <td className="border px-2 py-1 text-center">{h.type}</td>
                        <td className="border px-2 py-1 text-center">{h.recipients.length}</td>
                        <td className="border px-2 py-1 text-center">
                          <span className={h.status === "queued" ? "text-orange-600" : h.status === "sent" ? "text-green-600" : "text-red-600"}>
                            {h.status === "queued" ? "대기" : h.status === "sent" ? "전송" : "실패"}
                          </span>
                        </td>
                        <td className="border px-2 py-1 truncate max-w-[120px]">{h.message}</td>
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
