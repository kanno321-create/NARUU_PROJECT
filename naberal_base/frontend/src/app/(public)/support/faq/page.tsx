"use client";

import React, { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

const FAQ_DATA = [
  {
    category: "견적",
    items: [
      {
        q: "AI 견적은 어떻게 받나요?",
        a: "홈페이지 상단의 'AI 견적' 버튼을 클릭하면 3단계 견적 위저드가 시작됩니다. 분전반 종류 선택 → 차단기 구성 → 견적 확인까지 30초 만에 완료됩니다.",
      },
      {
        q: "AI 견적의 정확도는 어떤가요?",
        a: "KIS FIX-4 알고리즘은 실제 시장 단가를 기반으로 산출하며, 전문가 검수를 거친 가격 데이터를 사용합니다. 최종 견적은 담당자 확인 후 발송됩니다.",
      },
      {
        q: "견적서 PDF를 다운로드할 수 있나요?",
        a: "네, AI 견적 결과 페이지에서 BOM 테이블과 함께 PDF 형식의 견적서를 즉시 다운로드할 수 있습니다.",
      },
    ],
  },
  {
    category: "제품",
    items: [
      {
        q: "기성함과 분전반의 차이점은 무엇인가요?",
        a: "기성함은 차단기 없이 외함(박스)만을 의미하며, 분전반은 외함 안에 차단기와 부속자재가 설치된 완제품입니다.",
      },
      {
        q: "맞춤 제작도 가능한가요?",
        a: "네, 표준 규격 외에 맞춤 크기·사양의 기성함과 분전반도 제작 가능합니다. 문의하기를 통해 요청해 주세요.",
      },
      {
        q: "어떤 차단기를 사용하나요?",
        a: "LS전선(LSIS), ABB 등 국내외 주요 브랜드의 MCCB, ELB를 사용합니다. AI 견적 시 최적 차단기를 자동 추천합니다.",
      },
    ],
  },
  {
    category: "주문/납품",
    items: [
      {
        q: "납기는 얼마나 걸리나요?",
        a: "기성품은 재고 확인 후 1~3일 내 출고 가능합니다. 맞춤 제작 제품은 사양에 따라 1~2주 소요됩니다.",
      },
      {
        q: "전국 배송이 가능한가요?",
        a: "네, 전국 지사 네트워크를 통해 전국 어디든 배송이 가능합니다. 수도권은 당일/익일 배송도 가능합니다.",
      },
      {
        q: "A/S는 어떻게 받나요?",
        a: "053-792-1410으로 전화하시거나, 문의하기 페이지에서 A/S 요청을 남겨주시면 빠르게 처리해 드립니다.",
      },
    ],
  },
];

export default function FAQPage() {
  const [openIndex, setOpenIndex] = useState<string | null>(null);

  const toggleFaq = (key: string) => {
    setOpenIndex(openIndex === key ? null : key);
  };

  return (
    <div className="pt-[99px]">
      <section className="bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 py-16 sm:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <span className="text-sm font-semibold text-blue-400 tracking-wider uppercase">
            FAQ
          </span>
          <h1 className="mt-3 text-3xl sm:text-4xl font-bold text-white tracking-tight">
            자주 묻는 질문
          </h1>
        </div>
      </section>

      <section className="py-16 sm:py-24 bg-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          {FAQ_DATA.map((section) => (
            <div key={section.category}>
              <h2 className="text-lg font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100">
                {section.category}
              </h2>
              <div className="space-y-2">
                {section.items.map((item, i) => {
                  const key = `${section.category}-${i}`;
                  const isOpen = openIndex === key;
                  return (
                    <div
                      key={key}
                      className="border border-slate-100 rounded-xl overflow-hidden"
                    >
                      <button
                        onClick={() => toggleFaq(key)}
                        className="w-full flex items-center justify-between gap-4 px-6 py-4 text-left hover:bg-slate-50 transition-colors"
                      >
                        <span className="text-sm font-semibold text-slate-900">
                          {item.q}
                        </span>
                        <ChevronDown
                          className={cn(
                            "w-4 h-4 text-slate-400 shrink-0 transition-transform",
                            isOpen && "rotate-180"
                          )}
                        />
                      </button>
                      {isOpen && (
                        <div className="px-6 pb-4">
                          <p className="text-sm text-slate-500 leading-relaxed">
                            {item.a}
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
