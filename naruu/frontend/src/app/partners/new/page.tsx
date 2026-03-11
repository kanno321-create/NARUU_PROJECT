"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { Partner, PartnerType } from "@/lib/types";

export default function NewPartnerPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    name_ko: "",
    name_ja: "",
    type: "hospital" as PartnerType,
    address: "",
    contact_person: "",
    phone: "",
    commission_rate: "",
    contract_start: "",
    contract_end: "",
  });

  function update(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name_ko.trim()) {
      alert("업체명(한국어)을 입력하세요.");
      return;
    }

    const rate = form.commission_rate ? parseFloat(form.commission_rate) : undefined;
    if (rate !== undefined && rate > 30) {
      alert("커미션율은 30%를 초과할 수 없습니다 (의원급 상한).");
      return;
    }

    setSaving(true);
    try {
      const body: Record<string, unknown> = {
        name_ko: form.name_ko,
        type: form.type,
      };
      if (form.name_ja) body.name_ja = form.name_ja;
      if (form.address) body.address = form.address;
      if (form.contact_person) body.contact_person = form.contact_person;
      if (form.phone) body.phone = form.phone;
      if (rate !== undefined) body.commission_rate = rate;
      if (form.contract_start) body.contract_start = form.contract_start;
      if (form.contract_end) body.contract_end = form.contract_end;

      const created = await api.post<Partner>("/partners", body);
      router.push(`/partners/${created.id}`);
    } catch (e) {
      alert("등록 실패: " + (e instanceof Error ? e.message : "알 수 없는 오류"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell>
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.push("/partners")} className="text-gray-400 hover:text-gray-600">
          ← 목록
        </button>
        <h2 className="text-2xl font-bold text-gray-800">제휴처 등록</h2>
      </div>

      <form onSubmit={handleSubmit} className="max-w-2xl space-y-6">
        <div className="bg-white rounded-xl p-6 shadow-sm space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">업체명 (한국어) *</label>
              <input
                type="text"
                value={form.name_ko}
                onChange={(e) => update("name_ko", e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">업체명 (일본어)</label>
              <input
                type="text"
                value={form.name_ja}
                onChange={(e) => update("name_ja", e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">유형 *</label>
              <select
                value={form.type}
                onChange={(e) => update("type", e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
              >
                <option value="hospital">병원</option>
                <option value="clinic">클리닉</option>
                <option value="restaurant">레스토랑</option>
                <option value="hotel">호텔</option>
                <option value="shop">샵</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">커미션율 (%, 최대 30)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="30"
                value={form.commission_rate}
                onChange={(e) => update("commission_rate", e.target.value)}
                placeholder="예: 15.0"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">주소</label>
            <input
              type="text"
              value={form.address}
              onChange={(e) => update("address", e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">담당자</label>
              <input
                type="text"
                value={form.contact_person}
                onChange={(e) => update("contact_person", e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">연락처</label>
              <input
                type="text"
                value={form.phone}
                onChange={(e) => update("phone", e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">계약 시작일</label>
              <input
                type="date"
                value={form.contract_start}
                onChange={(e) => update("contract_start", e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">계약 종료일</label>
              <input
                type="date"
                value={form.contract_end}
                onChange={(e) => update("contract_end", e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
              />
            </div>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 disabled:opacity-50 transition font-medium text-sm"
          >
            {saving ? "등록 중..." : "제휴처 등록"}
          </button>
          <button
            type="button"
            onClick={() => router.push("/partners")}
            className="px-6 py-2.5 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition text-sm"
          >
            취소
          </button>
        </div>
      </form>
    </AppShell>
  );
}
