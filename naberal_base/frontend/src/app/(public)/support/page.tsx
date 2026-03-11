"use client";

import React from "react";
import Link from "next/link";
import { Bell, HelpCircle, MessageSquare, ArrowRight } from "lucide-react";

const SUPPORT_LINKS = [
  {
    icon: Bell,
    title: "공지사항",
    desc: "회사 소식, 제품 업데이트, 휴무 안내 등을 확인하세요.",
    href: "/support/notice",
    color: "from-blue-500 to-blue-600",
  },
  {
    icon: HelpCircle,
    title: "자주 묻는 질문",
    desc: "견적, 납기, 제품 사양 등 자주 묻는 질문과 답변입니다.",
    href: "/support/faq",
    color: "from-emerald-500 to-emerald-600",
  },
  {
    icon: MessageSquare,
    title: "문의하기",
    desc: "견적 문의, 기술 지원, 기타 문의를 남겨주세요.",
    href: "/support/contact",
    color: "from-violet-500 to-violet-600",
  },
];

export default function SupportPage() {
  return (
    <div className="pt-[99px]">
      <section className="bg-[#0B1120] py-16 sm:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-sm font-semibold text-blue-400 tracking-[0.15em] uppercase">
            Support
          </p>
          <h1 className="mt-4 font-heading text-3xl sm:text-4xl lg:text-5xl font-bold text-white tracking-tight">
            고객지원
          </h1>
          <p className="mt-5 text-lg text-slate-400">
            궁금한 점이 있으시면 언제든 문의해 주세요.
          </p>
        </div>
      </section>

      <section className="py-20 sm:py-28 bg-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 gap-6">
            {SUPPORT_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="group flex items-center gap-6 bg-white rounded-2xl p-8 border border-gray-100 hover:border-gray-200 shadow-sm hover:shadow-md transition-all duration-300"
              >
                <div className="shrink-0 flex items-center justify-center w-12 h-12 rounded-xl bg-gray-900 text-white group-hover:scale-105 transition-transform duration-200">
                  <link.icon className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <h3 className="font-heading text-xl font-bold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors duration-200">
                    {link.title}
                  </h3>
                  <p className="text-sm text-gray-500">{link.desc}</p>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-300 group-hover:text-blue-600 group-hover:translate-x-1 transition-all duration-200 shrink-0" />
              </Link>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
