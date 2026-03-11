"use client";

import React from "react";
import { EstimateWizard } from "@/components/public/EstimateWizard";
import { Zap, Shield, Clock } from "lucide-react";

export default function EstimatePage() {
  return (
    <div className="pt-[99px]">
      {/* Hero */}
      <section className="bg-[#0B1120] py-12 sm:py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full border border-white/10 bg-white/[0.04] mb-8">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]" />
            <span className="text-[13px] font-medium text-slate-400 tracking-wide">
              KIS FIX-4 AI Engine
            </span>
          </div>
          <h1 className="font-heading text-3xl sm:text-4xl font-bold text-white tracking-tight mb-5">
            AI 분전반 견적
          </h1>
          <p className="text-slate-400 max-w-xl mx-auto mb-8">
            3단계만 완성하면 AI가 차단기 선정, 외함 크기 산출,
            BOM 생성, 가격 산출까지 자동으로 처리합니다.
          </p>
          <div className="flex justify-center gap-8 text-sm">
            {[
              { icon: Clock, text: "30초 견적" },
              { icon: Zap, text: "AI 자동 산출" },
              { icon: Shield, text: "6단계 검증" },
            ].map((item) => (
              <div
                key={item.text}
                className="flex items-center gap-2 text-slate-500"
              >
                <item.icon className="w-4 h-4 text-slate-600" />
                <span>{item.text}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Wizard */}
      <section className="py-12 sm:py-16 bg-[#FAFAFA]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <EstimateWizard />
        </div>
      </section>
    </div>
  );
}
