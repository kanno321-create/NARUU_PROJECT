"use client";

import React from "react";
import { Bell, Calendar } from "lucide-react";

const NOTICES = [
  {
    id: 1,
    title: "AI 견적 시스템 (KIS v2.0) 정식 런칭",
    date: "2026-03-01",
    category: "서비스",
    content: "AI 기반 분전반 견적 시스템이 정식 오픈되었습니다. 30초 만에 정확한 견적을 받아보세요.",
  },
  {
    id: 2,
    title: "2026년 설 연휴 휴무 안내",
    date: "2026-01-20",
    category: "안내",
    content: "설 연휴 기간 중 공장 및 사무실이 휴무합니다. 견적 문의는 AI 시스템을 이용해 주세요.",
  },
  {
    id: 3,
    title: "전기차 분전반 신제품 출시",
    date: "2025-12-15",
    category: "제품",
    content: "EV 충전 인프라 전용 고용량 분전반 신제품이 출시되었습니다.",
  },
  {
    id: 4,
    title: "ISO 9001 재인증 완료",
    date: "2025-11-10",
    category: "인증",
    content: "품질경영시스템 ISO 9001 재인증 심사를 통과하였습니다.",
  },
  {
    id: 5,
    title: "홈페이지 리뉴얼 안내",
    date: "2026-03-08",
    category: "안내",
    content: "새로운 디자인과 AI 견적 기능을 탑재한 홈페이지가 오픈되었습니다.",
  },
];

export default function NoticePage() {
  return (
    <div className="pt-[99px]">
      <section className="bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 py-16 sm:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <span className="text-sm font-semibold text-blue-400 tracking-wider uppercase">
            Notice
          </span>
          <h1 className="mt-3 text-3xl sm:text-4xl font-bold text-white tracking-tight">
            공지사항
          </h1>
        </div>
      </section>

      <section className="py-16 sm:py-24 bg-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="space-y-4">
            {NOTICES.sort((a, b) => b.date.localeCompare(a.date)).map((notice) => (
              <div
                key={notice.id}
                className="bg-white rounded-xl p-6 border border-slate-100 hover:border-blue-200 hover:shadow-md transition-all"
              >
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2.5 py-0.5 rounded-full">
                    {notice.category}
                  </span>
                  <div className="flex items-center gap-1 text-xs text-slate-400">
                    <Calendar className="w-3.5 h-3.5" />
                    {notice.date}
                  </div>
                </div>
                <h3 className="text-base font-bold text-slate-900 mb-2">
                  {notice.title}
                </h3>
                <p className="text-sm text-slate-500">{notice.content}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
