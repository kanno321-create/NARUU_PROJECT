"use client";

import React from "react";
import { CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface StepIndicatorProps {
  currentStep: 1 | 2 | 3;
}

const STEPS = [
  { num: 1, label: "외함 선택" },
  { num: 2, label: "차단기 구성" },
  { num: 3, label: "견적 확인" },
] as const;

export function StepIndicator({ currentStep }: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-center gap-0">
      {STEPS.map((step, i) => {
        const isCompleted = currentStep > step.num;
        const isActive = currentStep === step.num;

        return (
          <React.Fragment key={step.num}>
            <div className="flex items-center gap-2.5">
              <div
                className={cn(
                  "flex items-center justify-center w-9 h-9 rounded-full text-sm font-bold transition-all",
                  isCompleted && "bg-blue-600 text-white",
                  isActive && "bg-blue-600 text-white ring-4 ring-blue-100",
                  !isCompleted && !isActive && "bg-slate-100 text-slate-400"
                )}
              >
                {isCompleted ? (
                  <CheckCircle2 className="w-5 h-5" />
                ) : (
                  step.num
                )}
              </div>
              <span
                className={cn(
                  "text-sm font-medium hidden sm:block",
                  isActive ? "text-slate-900" : "text-slate-400"
                )}
              >
                {step.label}
              </span>
            </div>

            {i < STEPS.length - 1 && (
              <div
                className={cn(
                  "w-12 sm:w-20 h-px mx-3",
                  currentStep > step.num ? "bg-blue-600" : "bg-slate-200"
                )}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}
