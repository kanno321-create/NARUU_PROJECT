"use client";

import React from "react";
import Link from "next/link";
import {
  Building2,
  Users,
  Award,
  MapPin,
  Calendar,
  Target,
  Zap,
  ArrowRight,
} from "lucide-react";

const HISTORY = [
  { year: "2014", event: "㈜한국산업이앤에스 설립 (7월)" },
  { year: "2018", event: "스마트 팩토리 도입" },
  { year: "2023", event: "AI 견적 시스템 (KIS) 런칭" },
  { year: "2024", event: "LEAN ERP 시스템 도입" },
];

const ABOUT_LINKS = [
  { icon: Users, label: "인사말", href: "/about/greeting", desc: "대표이사 인사말" },
  { icon: Building2, label: "조직도", href: "/about/organization", desc: "효율적인 조직 구조" },
  { icon: MapPin, label: "전국지사", href: "/about/branches", desc: "전국 서비스 네트워크" },
  { icon: Award, label: "인증서", href: "/about/certificates", desc: "품질 인증 현황" },
  { icon: MapPin, label: "오시는 길", href: "/about/location", desc: "본사 위치 안내" },
];

export default function AboutPage() {
  return (
    <div className="pt-[99px]">
      {/* Hero */}
      <section className="bg-[#0B1120] py-16 sm:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold text-blue-400 tracking-[0.15em] uppercase">
              About Us
            </p>
            <h1 className="mt-4 font-heading text-3xl sm:text-4xl lg:text-5xl font-bold text-white tracking-tight">
              회사개요
            </h1>
            <p className="mt-5 text-lg text-slate-400 leading-relaxed">
              20년 전통의 분전반 및 기성함 전문 제조기업,
              AI 기술로 전기설비 산업의 미래를 열어갑니다.
            </p>
          </div>
        </div>
      </section>

      {/* 기업 정보 */}
      <section className="py-20 sm:py-28 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
            <div>
              <h2 className="font-heading text-2xl sm:text-3xl font-bold text-gray-900 mb-6">
                전기설비의 미래를 선도하는 기업
              </h2>
              <p className="text-slate-500 leading-relaxed mb-6">
                ㈜한국산업이앤에스는 분전반, 기성함, 계량기함 등 전기설비 제품을
                전문으로 제조하는 기업입니다. IEC 61439, KS C 4510 등 국제·국내 표준을
                철저히 준수하며, AI 기반 견적 시스템을 통해 고객에게 빠르고 정확한
                서비스를 제공합니다.
              </p>
              <p className="text-slate-500 leading-relaxed mb-8">
                대구 북구에 위치한 본사 공장에서 최신 설비와 숙련된 기술진이
                고품질 제품을 생산하고 있으며, 전국 지사 네트워크를 통해
                신속한 납품과 A/S를 보장합니다.
              </p>
              <div className="grid grid-cols-2 gap-6">
                {[
                  { icon: Calendar, label: "설립", value: "2014년 7월" },
                  { icon: Target, label: "업종", value: "전기설비 제조" },
                  { icon: Building2, label: "본사", value: "대구 북구" },
                  { icon: Zap, label: "특화", value: "AI 견적 시스템" },
                ].map((item) => (
                  <div key={item.label} className="flex items-start gap-3">
                    <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-50 text-blue-600 shrink-0">
                      <item.icon className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 uppercase tracking-wider">{item.label}</p>
                      <p className="text-sm font-semibold text-slate-900">{item.value}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 연혁 */}
            <div>
              <h3 className="text-xl font-bold text-slate-900 mb-8">주요 연혁</h3>
              <div className="space-y-6">
                {HISTORY.map((item, i) => (
                  <div key={item.year} className="flex items-start gap-4">
                    <div className="flex flex-col items-center">
                      <div className="w-3 h-3 rounded-full bg-blue-600 ring-4 ring-blue-100" />
                      {i < HISTORY.length - 1 && (
                        <div className="w-px h-8 bg-blue-100 mt-1" />
                      )}
                    </div>
                    <div className="-mt-1">
                      <span className="text-sm font-bold text-blue-600">{item.year}</span>
                      <p className="text-sm text-slate-600 mt-0.5">{item.event}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 하위 페이지 링크 */}
      <section className="py-20 sm:py-28 bg-[#FAFAFA]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="font-heading text-2xl font-bold text-gray-900 mb-10 text-center">
            더 알아보기
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {ABOUT_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="group bg-white rounded-2xl p-7 border border-gray-100 hover:border-gray-200 shadow-sm hover:shadow-md transition-all duration-300"
              >
                <div className="flex items-center justify-center w-11 h-11 rounded-xl bg-gray-900 text-white mb-5 group-hover:scale-105 transition-transform duration-200">
                  <link.icon className="w-5 h-5" />
                </div>
                <h3 className="font-heading text-lg font-bold text-gray-900 mb-1">{link.label}</h3>
                <p className="text-sm text-gray-500 mb-4">{link.desc}</p>
                <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-gray-400 group-hover:text-blue-600 group-hover:gap-2.5 transition-all duration-200">
                  바로가기 <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
