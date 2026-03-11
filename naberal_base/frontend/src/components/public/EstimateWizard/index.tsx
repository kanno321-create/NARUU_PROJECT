"use client";

import React, { useState, useCallback } from "react";
import { StepIndicator } from "./StepIndicator";
import { Step1Usage } from "./Step1Usage";
import { Step2Config } from "./Step2Config";
import { Step3Result } from "./Step3Result";
import { INITIAL_WIZARD_STATE } from "./types";
import type { WizardState } from "./types";
/* ──────────────────────────────────────────────
   공개 견적 API 타입
   ────────────────────────────────────────────── */
interface PublicBreakerSpec {
  type: string;
  poles: number;
  current: number;
  frame: number;
}

interface PublicEstimateRequest {
  panel_usage: string;
  install_location: string;
  enclosure_material: string;
  breaker_brand: string;
  breaker_grade: string;
  main_breaker: PublicBreakerSpec;
  branch_breakers: PublicBreakerSpec[];
  accessories: { type: string; quantity: number }[];
  customer_name: string;
  project_name: string;
  contact_phone: string;
}

interface PublicEstimateResponse {
  estimate_id: string;
  success: boolean;
  total_amount: number | null;
  line_items: any[];
  validation_checks: any;
  created_at: string;
  message: string;
}

/* ──────────────────────────────────────────────
   공개 견적 API 호출 (인증 불필요)
   ────────────────────────────────────────────── */
const API_BASE =
  typeof window !== "undefined" && !(window as any).electronAPI
    ? "/api"
    : process.env.NEXT_PUBLIC_API_URL ||
      "https://naberalproject-production.up.railway.app";

async function submitEstimate(
  request: PublicEstimateRequest
): Promise<PublicEstimateResponse> {
  const res = await fetch(`${API_BASE}/v1/public/estimates`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = err.detail;
    const msg = typeof detail === "string" ? detail : detail?.message;
    throw new Error(msg || `서버 오류 (${res.status})`);
  }

  return res.json();
}

/* ──────────────────────────────────────────────
   위저드 → 공개 API 요청 변환
   ────────────────────────────────────────────── */
function buildEstimateRequest(state: WizardState): PublicEstimateRequest {
  return {
    panel_usage: state.panelUsage || "일반",
    install_location: state.installLocation || "옥내노출",
    enclosure_material: state.enclosureMaterial || "STEEL 1.6T",
    breaker_brand: state.breakerBrand || "상도",
    breaker_grade: state.breakerGrade || "경제형",
    main_breaker: {
      type: state.mainBreaker.breaker_type || "MCCB",
      poles: state.mainBreaker.poles,
      current: state.mainBreaker.ampere,
      frame: state.mainBreaker.ampere, // frame = ampere (백엔드에서 자동 결정)
    },
    branch_breakers: state.branchBreakers.map((b) => ({
      type: b.breaker_type || "ELB",
      poles: b.poles,
      current: b.ampere,
      frame: b.ampere,
    })),
    accessories: state.accessories.map((a) => ({
      type: a.type,
      quantity: a.quantity,
    })),
    customer_name: state.customerName || "웹사이트 고객",
    project_name: state.projectName || "온라인 견적",
    contact_phone: state.contactPhone || "",
  };
}

/* ──────────────────────────────────────────────
   메인 위저드 컴포넌트
   ────────────────────────────────────────────── */
export function EstimateWizard() {
  const [state, setState] = useState<WizardState>({ ...INITIAL_WIZARD_STATE });
  const [result, setResult] = useState<PublicEstimateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onUpdate = useCallback((partial: Partial<WizardState>) => {
    setState((prev) => ({ ...prev, ...partial }));
  }, []);

  const goToStep = useCallback((step: 1 | 2 | 3) => {
    setState((prev) => ({ ...prev, step }));
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  const handleSubmit = useCallback(async () => {
    goToStep(3);
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const request = buildEstimateRequest(state);
      const response = await submitEstimate(request);
      setResult(response);
    } catch (err: any) {
      setError(err.message || "견적 요청 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }, [state, goToStep]);

  return (
    <div className="max-w-4xl mx-auto">
      {/* Step Indicator */}
      <div className="mb-10">
        <StepIndicator currentStep={state.step} />
      </div>

      {/* Step Content */}
      {state.step === 1 && (
        <Step1Usage
          state={state}
          onUpdate={onUpdate}
          onNext={() => goToStep(2)}
        />
      )}
      {state.step === 2 && (
        <Step2Config
          state={state}
          onUpdate={onUpdate}
          onNext={handleSubmit}
          onBack={() => goToStep(1)}
        />
      )}
      {state.step === 3 && (
        <Step3Result
          state={state}
          result={result}
          loading={loading}
          error={error}
          onBack={() => goToStep(2)}
          onRetry={handleSubmit}
        />
      )}
    </div>
  );
}
