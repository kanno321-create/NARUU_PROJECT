"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatResponse {
  reply: string;
  conversation_id: number;
  tokens_used: number;
}

interface ConversationItem {
  id: number;
  context: string;
  preview: string;
  created_at: string;
}

type ChatContext = "chat" | "query" | "content" | "translation";

const CONTEXT_LABELS: Record<ChatContext, string> = {
  chat: "일반 대화",
  query: "데이터 조회",
  content: "콘텐츠 생성",
  translation: "번역",
};

export default function AIPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [context, setContext] = useState<ChatContext>("chat");
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Translation state
  const [translateText, setTranslateText] = useState("");
  const [translateFrom, setTranslateFrom] = useState("ja");
  const [translateTo, setTranslateTo] = useState("ko");
  const [translateResult, setTranslateResult] = useState("");
  const [translating, setTranslating] = useState(false);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const loadConversations = async () => {
    try {
      const data = await api.get<ConversationItem[]>("/ai/conversations");
      setConversations(data);
    } catch {
      // ignore
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const data = await api.post<ChatResponse>("/ai/chat", {
        message: userMsg.content,
        context,
        conversation_id: conversationId,
      });

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply },
      ]);
      setConversationId(data.conversation_id);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "오류가 발생했습니다. 다시 시도해주세요.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleTranslate = async () => {
    if (!translateText.trim() || translating) return;
    setTranslating(true);
    setTranslateResult("");

    try {
      const data = await api.post<{ translated: string }>("/ai/translate", {
        text: translateText,
        source_lang: translateFrom,
        target_lang: translateTo,
      });
      setTranslateResult(data.translated);
    } catch {
      setTranslateResult("번역에 실패했습니다.");
    } finally {
      setTranslating(false);
    }
  };

  const startNewChat = () => {
    setMessages([]);
    setConversationId(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-800">AI 어시스턴트</h2>
        <div className="flex gap-2">
          <button
            onClick={() => {
              setShowHistory(!showHistory);
              if (!showHistory) loadConversations();
            }}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            {showHistory ? "채팅으로" : "대화 기록"}
          </button>
          <button
            onClick={startNewChat}
            className="px-3 py-1.5 text-sm bg-naruu-600 text-white rounded-lg hover:bg-naruu-700"
          >
            새 대화
          </button>
        </div>
      </div>

      {/* Context Tabs */}
      <div className="flex gap-1 mb-4 bg-gray-100 rounded-lg p-1 w-fit" role="tablist" aria-label="AI 모드 선택">
        {(Object.keys(CONTEXT_LABELS) as ChatContext[]).map((ctx) => (
          <button
            key={ctx}
            role="tab"
            aria-selected={context === ctx}
            onClick={() => setContext(ctx)}
            className={`px-3 py-1.5 text-xs rounded-md transition ${
              context === ctx
                ? "bg-white text-naruu-700 font-semibold shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {CONTEXT_LABELS[ctx]}
          </button>
        ))}
      </div>

      {showHistory ? (
        /* Conversation History */
        <div className="bg-white rounded-xl shadow-sm p-4 space-y-2">
          {conversations.length === 0 ? (
            <p className="text-gray-400 text-sm py-4 text-center">
              대화 기록이 없습니다
            </p>
          ) : (
            conversations.map((c) => (
              <div
                key={c.id}
                className="flex items-center justify-between p-3 border border-gray-100 rounded-lg hover:bg-gray-50 cursor-pointer"
                onClick={async () => {
                  // Load existing messages from server
                  try {
                    const detail = await api.get<{
                      id: number;
                      context: string;
                      messages: Message[];
                    }>(`/ai/conversations/${c.id}`);
                    setMessages(
                      detail.messages
                        .filter((m: any) => m.role === "user" || m.role === "assistant")
                        .map((m: any) => ({ role: m.role, content: m.content }))
                    );
                    setConversationId(c.id);
                    setContext((c.context as ChatContext) || "chat");
                  } catch {
                    setConversationId(c.id);
                    setMessages([]);
                  }
                  setShowHistory(false);
                }}
              >
                <div>
                  <span className="text-xs text-gray-400 mr-2">
                    [{CONTEXT_LABELS[c.context as ChatContext] || c.context}]
                  </span>
                  <span className="text-sm text-gray-700">{c.preview || "(empty)"}</span>
                </div>
                <span className="text-xs text-gray-400">
                  {new Date(c.created_at).toLocaleDateString("ko-KR")}
                </span>
              </div>
            ))
          )}
        </div>
      ) : context === "translation" ? (
        /* Translation Mode */
        <div className="bg-white rounded-xl shadow-sm p-6 space-y-4 max-w-2xl">
          <div className="flex gap-3 items-center">
            <select
              value={translateFrom}
              onChange={(e) => setTranslateFrom(e.target.value)}
              aria-label="원본 언어"
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="ja">일본어</option>
              <option value="ko">한국어</option>
              <option value="en">영어</option>
            </select>
            <span className="text-gray-400">→</span>
            <select
              value={translateTo}
              onChange={(e) => setTranslateTo(e.target.value)}
              aria-label="번역 대상 언어"
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="ko">한국어</option>
              <option value="ja">일본어</option>
              <option value="en">영어</option>
            </select>
          </div>
          <textarea
            value={translateText}
            onChange={(e) => setTranslateText(e.target.value)}
            placeholder="번역할 텍스트를 입력하세요..."
            aria-label="번역할 텍스트"
            rows={4}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-naruu-500 outline-none"
          />
          <button
            onClick={handleTranslate}
            disabled={translating || !translateText.trim()}
            className="px-4 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 text-sm disabled:opacity-50"
          >
            {translating ? "번역 중..." : "번역"}
          </button>
          {translateResult && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">번역 결과</p>
              <p className="text-sm text-gray-800 whitespace-pre-wrap">
                {translateResult}
              </p>
            </div>
          )}
        </div>
      ) : (
        /* Chat Mode */
        <div className="bg-white rounded-xl shadow-sm flex flex-col" style={{ height: "calc(100vh - 260px)" }}>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-400 text-sm">
                  {context === "query"
                    ? '"이번 달 매출은?" 같은 질문을 해보세요'
                    : context === "content"
                    ? '"대구 맛집 소개 쇼츠 스크립트 만들어줘" 같이 요청해보세요'
                    : "무엇이든 물어보세요"}
                </p>
              </div>
            )}
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[75%] px-4 py-2.5 rounded-2xl text-sm whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "bg-naruu-600 text-white rounded-br-md"
                      : "bg-gray-100 text-gray-800 rounded-bl-md"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-500 px-4 py-2.5 rounded-2xl rounded-bl-md text-sm">
                  <span className="animate-pulse">응답 생성 중...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-gray-100 p-4">
            <div className="flex gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="메시지를 입력하세요... (Enter 전송, Shift+Enter 줄바꿈)"
                aria-label="AI 채팅 메시지 입력"
                rows={1}
                className="flex-1 px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-naruu-500 outline-none resize-none"
              />
              <button
                onClick={handleSend}
                disabled={loading || !input.trim()}
                className="px-4 py-2.5 bg-naruu-600 text-white rounded-xl hover:bg-naruu-700 transition disabled:opacity-50 text-sm font-medium"
              >
                전송
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
