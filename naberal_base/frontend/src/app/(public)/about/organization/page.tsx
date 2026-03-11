"use client";

import React from "react";
import { Users, Wrench, Cpu, Headphones, BarChart3 } from "lucide-react";

const DEPARTMENTS = [
  {
    icon: BarChart3,
    name: "경영지원팀",
    desc: "경영기획, 재무회계, 인사관리",
    color: "from-blue-500 to-blue-600",
  },
  {
    icon: Wrench,
    name: "생산기술팀",
    desc: "분전반·기성함 제조, 품질관리",
    color: "from-emerald-500 to-emerald-600",
  },
  {
    icon: Cpu,
    name: "기술연구팀",
    desc: "AI 견적 엔진 개발, 신제품 연구",
    color: "from-violet-500 to-violet-600",
  },
  {
    icon: Users,
    name: "영업팀",
    desc: "고객관리, 수주, 전국 영업",
    color: "from-amber-500 to-amber-600",
  },
  {
    icon: Headphones,
    name: "고객지원팀",
    desc: "A/S, 기술지원, 고객상담",
    color: "from-rose-500 to-rose-600",
  },
];

export default function OrganizationPage() {
  return (
    <div className="pt-[99px]">
      <section className="bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 py-16 sm:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <span className="text-sm font-semibold text-blue-400 tracking-wider uppercase">
            Organization
          </span>
          <h1 className="mt-3 text-3xl sm:text-4xl font-bold text-white tracking-tight">
            조직도
          </h1>
        </div>
      </section>

      <section className="py-16 sm:py-24 bg-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* CEO */}
          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-blue-700 text-white mb-4">
              <Users className="w-8 h-8" />
            </div>
            <h2 className="text-xl font-bold text-slate-900">대표이사</h2>
            <p className="text-sm text-slate-500">CEO</p>
          </div>

          {/* 연결선 */}
          <div className="flex justify-center mb-8">
            <div className="w-px h-12 bg-slate-200" />
          </div>

          {/* 부서 */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {DEPARTMENTS.map((dept) => (
              <div
                key={dept.name}
                className="bg-slate-50 rounded-2xl p-6 border border-slate-100 hover:border-blue-200 hover:shadow-md transition-all text-center"
              >
                <div
                  className={`inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br ${dept.color} text-white mb-4`}
                >
                  <dept.icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-1">
                  {dept.name}
                </h3>
                <p className="text-sm text-slate-500">{dept.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
