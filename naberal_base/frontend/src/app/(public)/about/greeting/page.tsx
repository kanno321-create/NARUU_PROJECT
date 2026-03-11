"use client";

import React from "react";
import { Quote } from "lucide-react";

export default function GreetingPage() {
  return (
    <div className="pt-[99px]">
      <section className="bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 py-16 sm:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <span className="text-sm font-semibold text-blue-400 tracking-wider uppercase">
            CEO Greeting
          </span>
          <h1 className="mt-3 text-3xl sm:text-4xl font-bold text-white tracking-tight">
            인사말
          </h1>
        </div>
      </section>

      <section className="py-16 sm:py-24 bg-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="relative">
            <Quote className="w-12 h-12 text-blue-100 mb-6" />
            <div className="space-y-6 text-slate-600 leading-relaxed">
              <p>
                안녕하십니까, ㈜한국산업이앤에스 대표이사입니다.
              </p>
              <p>
                저희 회사는 2014년 설립 이래 분전반, 기성함, 계량기함 등
                전기설비 분야에서 최고 품질의 제품을 공급해 왔습니다.
                IEC 61439, KS C 4510 등 국제·국내 표준을 철저히 준수하며,
                고객의 신뢰에 보답하기 위해 끊임없이 노력하고 있습니다.
              </p>
              <p>
                최근에는 AI 기반 견적 시스템(KIS)을 도입하여, 복잡한 분전반
                견적을 30초 만에 완성하는 혁신적인 서비스를 시작했습니다.
                전통적인 제조 기술과 첨단 IT 기술의 융합을 통해
                전기설비 산업의 새로운 패러다임을 제시하겠습니다.
              </p>
              <p>
                앞으로도 고객 여러분의 성원에 힘입어, 더 좋은 제품,
                더 나은 서비스로 보답하겠습니다.
              </p>
              <p className="text-slate-400 text-sm">감사합니다.</p>
            </div>

            <div className="mt-12 pt-8 border-t border-slate-100">
              <p className="text-lg font-bold text-slate-900">
                ㈜한국산업이앤에스
              </p>
              <p className="text-slate-500">대표이사 이광원</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
