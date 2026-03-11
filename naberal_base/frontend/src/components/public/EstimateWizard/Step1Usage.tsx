"use client";

import React from "react";
import {
  MapPin,
  Shield,
  Box,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { WizardState, InstallLocation } from "./types";

interface Step1Props {
  state: WizardState;
  onUpdate: (partial: Partial<WizardState>) => void;
  onNext: () => void;
}

const LOCATION_OPTIONS: {
  value: InstallLocation;
  label: string;
  desc: string;
}[] = [
  { value: "옥내노출", label: "옥내 노출", desc: "실내 벽면 부착" },
  { value: "옥외노출", label: "옥외 노출", desc: "실외 벽면 부착" },
  { value: "옥내자립", label: "옥내 자립", desc: "실내 바닥 설치" },
  { value: "옥외자립", label: "옥외 자립", desc: "실외 바닥 설치" },
  { value: "매입함", label: "매입함", desc: "벽 매입 설치" },
];

type MaterialType = "STEEL" | "SUS201" | "SUS304";

const STEEL_THICKNESS = [
  { value: "STEEL 1.0T", label: "1.0T", desc: "소형함 전용" },
  { value: "STEEL 1.6T", label: "1.6T", desc: "가장 일반적" },
  { value: "STEEL 2.0T", label: "2.0T", desc: "대형함/고하중" },
];

const SUS201_THICKNESS = [
  { value: "SUS201 1.0T", label: "1.0T", desc: "경제형 소형" },
  { value: "SUS201 1.2T", label: "1.2T", desc: "가장 일반적" },
  { value: "SUS201 1.5T", label: "1.5T", desc: "고하중/대형" },
];

const SUS304_THICKNESS = [
  { value: "SUS304 1.2T", label: "1.2T", desc: "내부식 기본" },
  { value: "SUS304 1.5T", label: "1.5T", desc: "옥외 권장" },
  { value: "SUS304 2.0T", label: "2.0T", desc: "고내식/대형" },
];

function getMaterialType(material: string | null): MaterialType | null {
  if (!material) return null;
  if (material.startsWith("STEEL")) return "STEEL";
  if (material.startsWith("SUS304")) return "SUS304";
  if (material.startsWith("SUS201")) return "SUS201";
  return null;
}

export function Step1Usage({ state, onUpdate, onNext }: Step1Props) {
  const isMaeip = state.installLocation === "매입함";
  const materialType = getMaterialType(state.enclosureMaterial);
  const canProceed = state.installLocation && state.enclosureMaterial;

  const handleLocationChange = (loc: InstallLocation) => {
    if (loc === "매입함" && (materialType === "SUS201" || materialType === "SUS304")) {
      // 매입함 선택 시 SUS면 재질 초기화
      onUpdate({ installLocation: loc, enclosureMaterial: null });
    } else {
      onUpdate({ installLocation: loc });
    }
  };

  const handleMaterialType = (type: MaterialType) => {
    // 재질 타입 변경 시 대표 두께로 자동 선택
    if (type === "STEEL") {
      onUpdate({ enclosureMaterial: "STEEL 1.6T" as any });
    } else if (type === "SUS201") {
      onUpdate({ enclosureMaterial: "SUS201 1.2T" as any });
    } else {
      onUpdate({ enclosureMaterial: "SUS304 1.2T" as any });
    }
  };

  const handleThickness = (value: string) => {
    onUpdate({ enclosureMaterial: value as any });
  };

  const thicknessOptions = materialType === "STEEL" ? STEEL_THICKNESS
    : materialType === "SUS201" ? SUS201_THICKNESS
    : materialType === "SUS304" ? SUS304_THICKNESS
    : [];

  return (
    <div className="space-y-10">
      {/* 설치 위치 */}
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-1">
          <MapPin className="inline w-5 h-5 mr-1 text-blue-600" />
          설치 위치
        </h3>
        <p className="text-sm text-slate-500 mb-5">
          분전반이 설치될 위치를 선택해 주세요.
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {LOCATION_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => handleLocationChange(opt.value)}
              className={cn(
                "flex flex-col items-center gap-1.5 p-4 rounded-xl border-2 transition-all text-center",
                state.installLocation === opt.value
                  ? "border-blue-600 bg-blue-50 ring-2 ring-blue-100"
                  : "border-slate-100 bg-white hover:border-slate-200 hover:bg-slate-50"
              )}
            >
              <span
                className={cn(
                  "text-sm font-semibold",
                  state.installLocation === opt.value
                    ? "text-blue-700"
                    : "text-slate-700"
                )}
              >
                {opt.label}
              </span>
              <span className="text-xs text-slate-400">{opt.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 재질 선택 */}
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-1">
          <Shield className="inline w-5 h-5 mr-1 text-blue-600" />
          외함 재질
        </h3>
        <p className="text-sm text-slate-500 mb-5">
          재질을 선택한 후 두께를 선택해 주세요.
          {isMaeip && (
            <span className="text-red-500 font-medium ml-1">
              (매입함은 STEEL만 가능)
            </span>
          )}
        </p>

        {/* 재질 타입: STEEL / SUS 201 / SUS 304 */}
        <div className="grid grid-cols-3 gap-3 max-w-xl mb-4">
          <button
            onClick={() => handleMaterialType("STEEL")}
            className={cn(
              "flex flex-col items-center gap-1.5 p-5 rounded-xl border-2 transition-all text-center",
              materialType === "STEEL"
                ? "border-blue-600 bg-blue-50 ring-2 ring-blue-100"
                : "border-slate-100 bg-white hover:border-slate-200 hover:bg-slate-50"
            )}
          >
            <Box className={cn("w-6 h-6", materialType === "STEEL" ? "text-blue-600" : "text-slate-400")} />
            <span className={cn("text-base font-bold", materialType === "STEEL" ? "text-blue-700" : "text-slate-700")}>
              STEEL
            </span>
            <span className="text-xs text-slate-400">철판 (분체도장)</span>
          </button>
          <button
            onClick={() => !isMaeip && handleMaterialType("SUS201")}
            disabled={isMaeip}
            className={cn(
              "flex flex-col items-center gap-1.5 p-5 rounded-xl border-2 transition-all text-center",
              isMaeip
                ? "border-slate-100 bg-slate-50 opacity-40 cursor-not-allowed"
                : materialType === "SUS201"
                  ? "border-blue-600 bg-blue-50 ring-2 ring-blue-100"
                  : "border-slate-100 bg-white hover:border-slate-200 hover:bg-slate-50"
            )}
          >
            <Box className={cn("w-6 h-6", materialType === "SUS201" ? "text-blue-600" : "text-slate-400")} />
            <span className={cn("text-base font-bold", materialType === "SUS201" ? "text-blue-700" : "text-slate-700")}>
              SUS 201
            </span>
            <span className="text-xs text-slate-400">경제형 스테인리스</span>
          </button>
          <button
            onClick={() => !isMaeip && handleMaterialType("SUS304")}
            disabled={isMaeip}
            className={cn(
              "flex flex-col items-center gap-1.5 p-5 rounded-xl border-2 transition-all text-center",
              isMaeip
                ? "border-slate-100 bg-slate-50 opacity-40 cursor-not-allowed"
                : materialType === "SUS304"
                  ? "border-blue-600 bg-blue-50 ring-2 ring-blue-100"
                  : "border-slate-100 bg-white hover:border-slate-200 hover:bg-slate-50"
            )}
          >
            <Box className={cn("w-6 h-6", materialType === "SUS304" ? "text-blue-600" : "text-slate-400")} />
            <span className={cn("text-base font-bold", materialType === "SUS304" ? "text-blue-700" : "text-slate-700")}>
              SUS 304
            </span>
            <span className="text-xs text-slate-400">내부식 고급</span>
          </button>
        </div>

        {/* 두께 선택 */}
        {materialType && (
          <div>
            <p className="text-xs font-semibold text-slate-500 mb-2">두께 선택</p>
            <div className="flex flex-wrap gap-2">
              {thicknessOptions.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => handleThickness(opt.value)}
                  className={cn(
                    "px-4 py-2.5 rounded-lg border-2 text-sm font-semibold transition-all",
                    state.enclosureMaterial === opt.value
                      ? "border-blue-600 bg-blue-50 text-blue-700"
                      : "border-slate-100 bg-white text-slate-600 hover:border-slate-200"
                  )}
                >
                  {opt.label}
                  <span className="ml-1.5 text-xs font-normal text-slate-400">{opt.desc}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 다음 버튼 */}
      <div className="flex justify-end pt-4">
        <button
          onClick={onNext}
          disabled={!canProceed}
          className={cn(
            "px-8 py-3 rounded-xl text-base font-bold transition-all",
            canProceed
              ? "bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-500 hover:to-blue-600 hover:shadow-lg active:scale-[0.98]"
              : "bg-slate-100 text-slate-400 cursor-not-allowed"
          )}
        >
          다음: 차단기 구성
        </button>
      </div>
    </div>
  );
}
