"use client";

import React from "react";
import { Plus, Trash2, ArrowLeft, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import type { WizardState, BreakerBrand, BreakerGrade } from "./types";
import {
  AMPERE_OPTIONS,
  ACCESSORY_TYPES,
  DEFAULT_BRANCH_BREAKER,
} from "./types";
import type { BreakerInput, AccessoryInput } from "@/lib/api";

interface Step2Props {
  state: WizardState;
  onUpdate: (partial: Partial<WizardState>) => void;
  onNext: () => void;
  onBack: () => void;
}

const BRAND_OPTIONS: { value: BreakerBrand; label: string; desc: string }[] = [
  { value: "상도", label: "상도", desc: "우수한 품질, 저렴한 가격" },
  { value: "LS", label: "LS산전", desc: "우수한 품질, 다양한 스펙" },
];

const GRADE_OPTIONS: { value: BreakerGrade; label: string; desc: string }[] = [
  { value: "경제형", label: "경제형", desc: "저렴한 가격" },
  { value: "표준형", label: "표준형", desc: "고급 사양" },
];

export function Step2Config({ state, onUpdate, onNext, onBack }: Step2Props) {
  /* -- 메인 차단기 업데이트 -- */
  const updateMain = (field: keyof BreakerInput, value: any) => {
    onUpdate({
      mainBreaker: { ...state.mainBreaker, [field]: value },
    });
  };

  /* -- 분기 차단기 업데이트 -- */
  const updateBranch = (
    index: number,
    field: keyof BreakerInput,
    value: any
  ) => {
    const updated = [...state.branchBreakers];
    updated[index] = { ...updated[index], [field]: value };
    onUpdate({ branchBreakers: updated });
  };

  const addBranch = () => {
    onUpdate({
      branchBreakers: [
        ...state.branchBreakers,
        { ...DEFAULT_BRANCH_BREAKER },
      ],
    });
  };

  const removeBranch = (index: number) => {
    if (state.branchBreakers.length <= 1) return;
    onUpdate({
      branchBreakers: state.branchBreakers.filter((_, i) => i !== index),
    });
  };

  /* -- 부속자재 -- */
  const addAccessory = () => {
    onUpdate({
      accessories: [
        ...state.accessories,
        { type: "magnet" as const, model: "MC-22", quantity: 1 },
      ],
    });
  };

  const updateAccessory = (
    index: number,
    field: keyof AccessoryInput,
    value: any
  ) => {
    const updated = [...state.accessories];
    updated[index] = { ...updated[index], [field]: value };
    onUpdate({ accessories: updated });
  };

  const removeAccessory = (index: number) => {
    onUpdate({
      accessories: state.accessories.filter((_, i) => i !== index),
    });
  };

  return (
    <div className="space-y-10">
      {/* -- 브랜드 선택 -- */}
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-1">차단기 브랜드</h3>
        <p className="text-sm text-slate-500 mb-4">차단기 제조사를 선택해 주세요.</p>
        <div className="grid grid-cols-2 gap-3 max-w-md">
          {BRAND_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => onUpdate({ breakerBrand: opt.value })}
              className={cn(
                "flex flex-col items-center gap-1 p-4 rounded-xl border-2 transition-all text-center",
                state.breakerBrand === opt.value
                  ? "border-blue-600 bg-blue-50 ring-2 ring-blue-100"
                  : "border-slate-100 bg-white hover:border-slate-200 hover:bg-slate-50"
              )}
            >
              <span className={cn(
                "text-base font-bold",
                state.breakerBrand === opt.value ? "text-blue-700" : "text-slate-700"
              )}>
                {opt.label}
              </span>
              <span className="text-xs text-slate-400">{opt.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* -- 등급 선택 -- */}
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-1">차단기 등급</h3>
        <p className="text-sm text-slate-500 mb-4">표준형 또는 경제형을 선택해 주세요.</p>
        <div className="grid grid-cols-2 gap-3 max-w-md">
          {GRADE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => onUpdate({ breakerGrade: opt.value })}
              className={cn(
                "flex flex-col items-center gap-1 p-4 rounded-xl border-2 transition-all text-center",
                state.breakerGrade === opt.value
                  ? "border-blue-600 bg-blue-50 ring-2 ring-blue-100"
                  : "border-slate-100 bg-white hover:border-slate-200 hover:bg-slate-50"
              )}
            >
              <span className={cn(
                "text-base font-bold",
                state.breakerGrade === opt.value ? "text-blue-700" : "text-slate-700"
              )}>
                {opt.label}
              </span>
              <span className="text-xs text-slate-400">{opt.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* -- 메인 차단기 -- */}
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-1">
          <Zap className="inline w-5 h-5 mr-1 text-blue-600" />
          메인 차단기
        </h3>
        <p className="text-sm text-slate-500 mb-5">
          분전반의 주 차단기를 설정합니다.
        </p>
        <div className="bg-blue-50 rounded-xl p-5 border border-blue-100">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* 종류 */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                종류
              </label>
              <select
                value={state.mainBreaker.breaker_type}
                onChange={(e) => updateMain("breaker_type", e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg border border-blue-200 bg-white text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none"
              >
                <option value="MCCB">MCCB (배선용)</option>
                <option value="ELB">ELB (누전차단기)</option>
              </select>
            </div>
            {/* 극수 */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                극수
              </label>
              <select
                value={state.mainBreaker.poles}
                onChange={(e) =>
                  updateMain("poles", parseInt(e.target.value))
                }
                className="w-full px-3 py-2.5 rounded-lg border border-blue-200 bg-white text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none"
              >
                <option value={2}>2P</option>
                <option value={3}>3P</option>
                <option value={4}>4P</option>
              </select>
            </div>
            {/* 용량 */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                용량 (A)
              </label>
              <select
                value={state.mainBreaker.ampere}
                onChange={(e) =>
                  updateMain("ampere", parseInt(e.target.value))
                }
                className="w-full px-3 py-2.5 rounded-lg border border-blue-200 bg-white text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none"
              >
                {AMPERE_OPTIONS.filter((a) => a >= 50).map((a) => (
                  <option key={a} value={a}>
                    {a}A
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* -- 분기 차단기 -- */}
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-1">
          분기 차단기
        </h3>
        <p className="text-sm text-slate-500 mb-4">
          분기 회로별 차단기를 구성합니다. ({state.branchBreakers.length}개)
        </p>
        <button
          onClick={addBranch}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 transition-colors mb-3"
        >
          <Plus className="w-4 h-4" />
          분기 추가
        </button>

        <div className="space-y-3">
          {state.branchBreakers.map((breaker, i) => (
            <div
              key={i}
              className="bg-white rounded-xl p-4 border border-slate-100 hover:border-slate-200 transition-colors"
            >
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xs font-bold text-slate-400 bg-slate-50 px-2 py-0.5 rounded">
                  #{i + 1}
                </span>
                {state.branchBreakers.length > 1 && (
                  <button
                    onClick={() => removeBranch(i)}
                    className="ml-auto text-slate-300 hover:text-red-500 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {/* 종류 */}
                <div>
                  <label className="block text-xs text-slate-500 mb-1">
                    종류
                  </label>
                  <select
                    value={breaker.breaker_type}
                    onChange={(e) =>
                      updateBranch(i, "breaker_type", e.target.value)
                    }
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:border-blue-500 outline-none"
                  >
                    <option value="MCCB">MCCB</option>
                    <option value="ELB">ELB</option>
                  </select>
                </div>
                {/* 극수 */}
                <div>
                  <label className="block text-xs text-slate-500 mb-1">
                    극수
                  </label>
                  <select
                    value={breaker.poles}
                    onChange={(e) =>
                      updateBranch(i, "poles", parseInt(e.target.value))
                    }
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:border-blue-500 outline-none"
                  >
                    <option value={2}>2P</option>
                    <option value={3}>3P</option>
                    <option value={4}>4P</option>
                  </select>
                </div>
                {/* 용량 */}
                <div>
                  <label className="block text-xs text-slate-500 mb-1">
                    용량
                  </label>
                  <select
                    value={breaker.ampere}
                    onChange={(e) =>
                      updateBranch(i, "ampere", parseInt(e.target.value))
                    }
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:border-blue-500 outline-none"
                  >
                    {AMPERE_OPTIONS.map((a) => (
                      <option key={a} value={a}>
                        {a}A
                      </option>
                    ))}
                  </select>
                </div>
                {/* 수량 */}
                <div>
                  <label className="block text-xs text-slate-500 mb-1">
                    수량
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={20}
                    value={breaker.quantity}
                    onChange={(e) =>
                      updateBranch(
                        i,
                        "quantity",
                        Math.max(1, parseInt(e.target.value) || 1)
                      )
                    }
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:border-blue-500 outline-none"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* -- 부속자재 (선택) -- */}
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-1">
          부속자재 <span className="text-sm font-normal text-slate-400">(선택)</span>
        </h3>
        <p className="text-sm text-slate-500 mb-4">
          마그네트, 타이머 등 추가 부속자재를 선택합니다.
        </p>
        <button
          onClick={addAccessory}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 transition-colors mb-3"
        >
          <Plus className="w-4 h-4" />
          부속 추가
        </button>

        {state.accessories.length === 0 ? (
          <div className="text-center py-8 bg-slate-50 rounded-xl border border-dashed border-slate-200">
            <p className="text-sm text-slate-400">
              부속자재가 없습니다. 필요 시 추가해 주세요.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {state.accessories.map((acc, i) => (
              <div
                key={i}
                className="bg-white rounded-xl p-4 border border-slate-100 hover:border-slate-200 transition-colors"
              >
                <div className="grid grid-cols-3 sm:grid-cols-4 gap-3 items-end">
                  <div>
                    <label className="block text-xs text-slate-500 mb-1">
                      종류
                    </label>
                    <select
                      value={acc.type}
                      onChange={(e) =>
                        updateAccessory(i, "type", e.target.value)
                      }
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:border-blue-500 outline-none"
                    >
                      {ACCESSORY_TYPES.map((t) => (
                        <option key={t.value} value={t.value}>
                          {t.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500 mb-1">
                      모델
                    </label>
                    <input
                      type="text"
                      value={acc.model}
                      onChange={(e) =>
                        updateAccessory(i, "model", e.target.value)
                      }
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:border-blue-500 outline-none"
                      placeholder="모델명"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500 mb-1">
                      수량
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={20}
                      value={acc.quantity}
                      onChange={(e) =>
                        updateAccessory(
                          i,
                          "quantity",
                          Math.max(1, parseInt(e.target.value) || 1)
                        )
                      }
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:border-blue-500 outline-none"
                    />
                  </div>
                  <div className="flex justify-end">
                    <button
                      onClick={() => removeAccessory(i)}
                      className="p-2 text-slate-300 hover:text-red-500 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* -- 네비게이션 -- */}
      <div className="flex justify-between pt-4">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold text-slate-600 border border-slate-200 hover:bg-slate-50 transition-all"
        >
          <ArrowLeft className="w-4 h-4" />
          이전
        </button>
        <button
          onClick={onNext}
          className="px-8 py-3 rounded-xl text-base font-bold bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-500 hover:to-blue-600 hover:shadow-lg active:scale-[0.98] transition-all"
        >
          견적 요청하기
        </button>
      </div>
    </div>
  );
}
