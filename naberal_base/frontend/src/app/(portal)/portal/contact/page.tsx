"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Send, MessageCircle, User, Clock, Phone, Mail } from "lucide-react";

interface ContactMessage {
  id: string;
  role: "customer" | "staff" | "system";
  content: string;
  timestamp: Date;
  senderName?: string;
}

export default function PortalContactPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ContactMessage[]>([
    {
      id: "system-1",
      role: "system",
      content: "담당 직원에게 메시지를 보내실 수 있습니다. 영업시간(평일 09:00~18:00) 내 순차적으로 답변드립니다.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || isSending) return;

    const msg: ContactMessage = {
      id: `msg-${Date.now()}`,
      role: "customer",
      content: text,
      timestamp: new Date(),
      senderName: user?.name || "고객",
    };

    setMessages((prev) => [...prev, msg]);
    setInput("");
    setIsSending(true);

    // 자동 확인 메시지 (실제 구현 시 WebSocket/Polling으로 교체)
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: `ack-${Date.now()}`,
          role: "system",
          content: "메시지가 전송되었습니다. 담당 직원이 확인 후 답변드리겠습니다.",
          timestamp: new Date(),
        },
      ]);
      setIsSending(false);
    }, 500);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-slate-900">직원 상담</h1>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Clock className="w-3.5 h-3.5" />
          평일 09:00 ~ 18:00
        </div>
      </div>

      {/* 직원 연락처 카드 */}
      <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 mb-4">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
            <MessageCircle className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-slate-800">
              한국산업 E&S 고객지원팀
            </p>
            <p className="text-xs text-slate-500 mt-0.5">
              견적 문의, 주문 상담, 기술 지원
            </p>
            <div className="flex flex-wrap gap-3 mt-2">
              <a
                href="tel:053-792-1410"
                className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
              >
                <Phone className="w-3 h-3" />
                053-792-1410
              </a>
              <a
                href="mailto:info@hkkor.com"
                className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
              >
                <Mail className="w-3 h-3" />
                info@hkkor.com
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-y-auto bg-white rounded-xl border border-slate-200 p-4 space-y-3">
        {messages.map((msg) => (
          <div key={msg.id}>
            {msg.role === "system" ? (
              <div className="text-center">
                <span className="inline-block bg-slate-100 text-slate-500 text-xs px-3 py-1.5 rounded-full">
                  {msg.content}
                </span>
              </div>
            ) : (
              <div
                className={`flex gap-3 ${
                  msg.role === "customer" ? "flex-row-reverse" : ""
                }`}
              >
                <div
                  className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    msg.role === "staff"
                      ? "bg-green-100 text-green-600"
                      : "bg-slate-200 text-slate-600"
                  }`}
                >
                  {msg.role === "staff" ? (
                    <MessageCircle className="w-4 h-4" />
                  ) : (
                    <User className="w-4 h-4" />
                  )}
                </div>

                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    msg.role === "staff"
                      ? "bg-green-50 text-slate-800"
                      : "bg-blue-600 text-white"
                  }`}
                >
                  {msg.senderName && (
                    <p
                      className={`text-[10px] font-medium mb-1 ${
                        msg.role === "staff" ? "text-green-600" : "text-blue-200"
                      }`}
                    >
                      {msg.senderName}
                    </p>
                  )}
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                  <p
                    className={`text-[10px] mt-1 ${
                      msg.role === "staff" ? "text-slate-400" : "text-blue-200"
                    }`}
                  >
                    {msg.timestamp.toLocaleTimeString("ko-KR", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* 입력 영역 */}
      <div className="mt-3 flex gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="직원에게 메시지를 보내세요... (Enter로 전송)"
          rows={1}
          className="flex-1 resize-none border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <button
          onClick={sendMessage}
          disabled={!input.trim() || isSending}
          className="px-4 py-3 bg-green-600 text-white rounded-xl hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
