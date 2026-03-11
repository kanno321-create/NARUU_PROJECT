"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { Package, Plus, ChevronRight } from "lucide-react";

interface OrderItem {
  id: string;
  orderNumber: string;
  date: string;
  projectName: string;
  totalAmount: number;
  status: "접수" | "제작중" | "출하준비" | "배송중" | "완료";
}

const STATUS_STEPS = ["접수", "제작중", "출하준비", "배송중", "완료"] as const;

const STATUS_COLORS: Record<string, string> = {
  접수: "bg-blue-100 text-blue-700",
  제작중: "bg-amber-100 text-amber-700",
  출하준비: "bg-purple-100 text-purple-700",
  배송중: "bg-cyan-100 text-cyan-700",
  완료: "bg-green-100 text-green-700",
};

function OrderProgress({ status }: { status: OrderItem["status"] }) {
  const currentIdx = STATUS_STEPS.indexOf(status);
  return (
    <div className="flex items-center gap-1 mt-3">
      {STATUS_STEPS.map((step, i) => (
        <React.Fragment key={step}>
          <div className="flex flex-col items-center">
            <div
              className={`w-3 h-3 rounded-full transition-colors ${
                i <= currentIdx ? "bg-blue-600" : "bg-slate-200"
              }`}
            />
            <span className={`text-[10px] mt-1 ${
              i <= currentIdx ? "text-blue-600 font-medium" : "text-slate-400"
            }`}>
              {step}
            </span>
          </div>
          {i < STATUS_STEPS.length - 1 && (
            <div
              className={`flex-1 h-0.5 mb-4 ${
                i < currentIdx ? "bg-blue-600" : "bg-slate-200"
              }`}
            />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

// 새 주문 요청 모달
function NewOrderModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const [form, setForm] = useState({
    estimateId: "",
    projectName: "",
    deliveryAddress: "",
    deliveryDate: "",
    notes: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    // 주문 API 호출 (향후 구현)
    await new Promise((r) => setTimeout(r, 800));
    setIsSubmitting(false);
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-2xl p-8 max-w-md w-full text-center">
          <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-2">주문 요청 완료</h3>
          <p className="text-sm text-slate-500 mb-6">
            담당자가 확인 후 연락드리겠습니다.
          </p>
          <button
            onClick={() => {
              setSubmitted(false);
              onClose();
            }}
            className="px-6 py-2.5 bg-blue-700 text-white text-sm font-medium rounded-lg hover:bg-blue-800"
          >
            확인
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-bold text-slate-900 mb-4">새 주문 요청</h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              견적번호 (선택)
            </label>
            <input
              type="text"
              value={form.estimateId}
              onChange={(e) => setForm({ ...form, estimateId: e.target.value })}
              className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="EST-XXXXXX (견적 결과에서 확인)"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              프로젝트명 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={form.projectName}
              onChange={(e) => setForm({ ...form, projectName: e.target.value })}
              className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="예: OO아파트 분전반"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              배송지 주소
            </label>
            <input
              type="text"
              value={form.deliveryAddress}
              onChange={(e) => setForm({ ...form, deliveryAddress: e.target.value })}
              className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="배송 받으실 주소"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              희망 납기일
            </label>
            <input
              type="date"
              value={form.deliveryDate}
              onChange={(e) => setForm({ ...form, deliveryDate: e.target.value })}
              className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              요청사항
            </label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              rows={3}
              className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder="추가 요청사항이 있으시면 입력해 주세요"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 border border-slate-200 text-slate-600 text-sm font-medium rounded-lg hover:bg-slate-50"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 py-2.5 bg-blue-700 text-white text-sm font-medium rounded-lg hover:bg-blue-800 disabled:opacity-50"
            >
              {isSubmitting ? "요청 중..." : "주문 요청"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function PortalOrdersPage() {
  const [orders] = useState<OrderItem[]>([]);
  const [showNewOrder, setShowNewOrder] = useState(false);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-900">내 주문 목록</h1>
        <button
          onClick={() => setShowNewOrder(true)}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-700 text-white text-sm font-medium rounded-lg hover:bg-blue-800 transition-colors"
        >
          <Plus className="w-4 h-4" />
          주문 요청
        </button>
      </div>

      {orders.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Package className="w-8 h-8 text-slate-400" />
          </div>
          <h2 className="text-lg font-semibold text-slate-700 mb-2">
            주문 내역이 없습니다
          </h2>
          <p className="text-slate-500 text-sm mb-6">
            견적 완료 후 주문을 요청하시면 이곳에서 진행 상태를 추적하실 수 있습니다.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/estimate"
              className="inline-flex items-center justify-center gap-1.5 px-6 py-3 bg-blue-700 text-white font-medium rounded-lg hover:bg-blue-800 transition-colors"
            >
              AI 견적 시작하기
              <ChevronRight className="w-4 h-4" />
            </Link>
            <button
              onClick={() => setShowNewOrder(true)}
              className="inline-flex items-center justify-center gap-1.5 px-6 py-3 border border-slate-200 text-slate-700 font-medium rounded-lg hover:bg-slate-50 transition-colors"
            >
              <Plus className="w-4 h-4" />
              직접 주문 요청
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((order) => (
            <div
              key={order.id}
              className="bg-white rounded-xl border border-slate-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="text-xs text-slate-400 mb-1">
                    주문번호: {order.orderNumber}
                  </p>
                  <h3 className="font-semibold text-slate-900">
                    {order.projectName}
                  </h3>
                  <p className="text-sm text-slate-500">{order.date}</p>
                </div>
                <div className="text-right">
                  <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[order.status]}`}>
                    {order.status}
                  </span>
                  <p className="text-lg font-bold text-slate-900 mt-1">
                    {order.totalAmount.toLocaleString()}원
                  </p>
                </div>
              </div>
              <OrderProgress status={order.status} />
            </div>
          ))}
        </div>
      )}

      <NewOrderModal
        isOpen={showNewOrder}
        onClose={() => setShowNewOrder(false)}
      />
    </div>
  );
}
