"use client";

import React from "react";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowRight,
  CheckCircle2,
  Box,
  Cpu,
  Sun,
  Gauge,
  Shield,
  Zap,
  Clock,
  FileText,
  BarChart3,
  Phone,
  ChevronRight,
  Building2,
  Award,
  Truck,
} from "lucide-react";

/* ──────────────────────────────────────────────
   데이터
   ────────────────────────────────────────────── */
const PRODUCTS = [
  { icon: Box, title: "철 기성함", desc: "내구성이 뛰어난 철제 기성함. 다양한 규격 보유.", href: "/products/steel-enclosure", img: "/images/about/intro1.webp" },
  { icon: Shield, title: "스테인리스 기성함", desc: "부식에 강한 스테인리스 재질. 옥외 설치에 최적.", href: "/products/stainless-enclosure", img: "/images/products/stainless1.jpg" },
  { icon: Gauge, title: "계량기함", desc: "한전 규격 준수 계량기함. 정확한 계량 보장.", href: "/products/meter-box", img: "/images/products/sec2_img1.webp" },
  { icon: Cpu, title: "기성 분전반", desc: "IEC/KS 표준 기성 분전반. 즉시 납품 가능.", href: "/products/distribution-panel", img: "/images/about/intro2.webp" },
  { icon: Zap, title: "전기차 분전반", desc: "EV 충전 인프라 전용 분전반. 고용량 대응.", href: "/products/ev-panel", img: "/images/products/sec2_img2.webp" },
  { icon: Sun, title: "태양광 분전반", desc: "신재생에너지 연계 분전반. 인버터 연동 설계.", href: "/products/solar-panel", img: "/images/products/sec2_img4.webp" },
];

const STRENGTHS = [
  { icon: Cpu, title: "AI 견적 엔진", desc: "KIS FIX-4 알고리즘이 차단기, 외함, 부속자재를 자동 산출합니다.", light: "bg-blue-50 text-blue-600 border-blue-100" },
  { icon: Clock, title: "30초 견적", desc: "복잡한 분전반 견적을 30초 만에 완성합니다.", light: "bg-emerald-50 text-emerald-600 border-emerald-100" },
  { icon: FileText, title: "견적서 자동생성", desc: "BOM, 가격표, 표지까지 전문 견적서를 즉시 제공합니다.", light: "bg-violet-50 text-violet-600 border-violet-100" },
  { icon: BarChart3, title: "실시간 단가", desc: "최신 시장 단가를 반영한 정확한 가격을 보장합니다.", light: "bg-amber-50 text-amber-600 border-amber-100" },
];

const STATS = [
  { value: "11+", suffix: "년", label: "업력" },
  { value: "5,000+", suffix: "건", label: "납품 실적" },
  { value: "30", suffix: "초", label: "AI 견적 속도" },
  { value: "100", suffix: "%", label: "IEC/KS 준수" },
];

const CERTIFICATIONS = [
  { icon: Award, text: "IEC 61439 인증" },
  { icon: Shield, text: "KS C 4510 준수" },
  { icon: CheckCircle2, text: "ISO 9001 품질경영" },
  { icon: Truck, text: "전국 지사 네트워크" },
];

export default function HomePage() {
  return (
    <>
      {/* ══════════════════════════════════════
          HERO — 실사 배경 + 오버레이 + 오른쪽 비주얼
          ══════════════════════════════════════ */}
      <section className="relative min-h-screen flex items-center overflow-hidden pt-[99px]">
        {/* 실사 배경 이미지 */}
        <Image
          src="/images/hero/mv1.webp"
          alt="전기차 충전 인프라"
          fill
          className="object-cover"
          priority
        />
        {/* 다크 오버레이 */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#0B1120]/95 via-[#0B1120]/85 to-[#0B1120]/60" />
        {/* 하단 페이드 */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[#0B1120] to-transparent" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-28 w-full">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            {/* 왼쪽: 메인 콘텐츠 (7칸) */}
            <div className="lg:col-span-7">
              <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full border border-white/10 bg-white/[0.04] mb-8">
                <div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)] animate-pulse" />
                <span className="text-[13px] font-medium text-slate-400 tracking-wide">
                  AI 견적 시스템 가동중
                </span>
              </div>

              <h1 className="font-heading text-[2.5rem] sm:text-[3.5rem] lg:text-[4rem] font-extrabold text-white leading-[1.08] tracking-tight">
                분전반 견적,
                <br />
                <span className="relative inline-block">
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-sky-300 to-cyan-300">
                    AI가 30초 만에
                  </span>
                  <span className="absolute -bottom-2 left-0 w-full h-[3px] bg-gradient-to-r from-blue-500 via-sky-400 to-transparent rounded-full" />
                </span>
              </h1>

              <p className="mt-8 text-lg sm:text-xl text-slate-300 leading-relaxed max-w-lg">
                한국산업이앤에스의 AI 견적 엔진이 차단기 선정부터
                외함 크기 산출, BOM 생성까지 자동으로 처리합니다.
              </p>

              <div className="mt-10 flex flex-col sm:flex-row gap-4">
                <Link
                  href="/estimate"
                  className="group inline-flex items-center justify-center gap-3 px-8 py-4 rounded-xl text-[15px] font-bold bg-red-600 text-white hover:bg-red-500 transition-all duration-200 shadow-[0_4px_15px_rgba(220,38,38,0.3)] hover:shadow-[0_8px_30px_rgba(220,38,38,0.5),0_0_60px_rgba(220,38,38,0.15)] hover:-translate-y-0.5 active:scale-[0.98]"
                >
                  무료 AI 견적 받기
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </Link>
                <Link
                  href="/products"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl text-[15px] font-semibold text-white/90 border border-white/20 hover:border-white/40 hover:bg-white/[0.06] transition-all duration-200 active:scale-[0.98]"
                >
                  제품 둘러보기
                </Link>
              </div>

              <div className="mt-12 flex flex-wrap gap-6">
                {["IEC 61439", "KS C 4510", "ISO 9001"].map((cert) => (
                  <div key={cert} className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-blue-400/70" />
                    <span className="text-xs font-medium text-slate-400">{cert}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* 오른쪽: AI 엔진 비주얼 (5칸) */}
            <div className="lg:col-span-5 hidden lg:block relative">
              <div className="absolute -top-10 -right-10 w-[300px] h-[300px] border border-white/[0.04] rounded-full" />

              <div className="relative bg-gradient-to-br from-white/[0.08] to-white/[0.03] backdrop-blur-md border border-white/[0.1] rounded-2xl overflow-hidden shadow-[0_8px_40px_rgba(0,0,0,0.4),0_0_80px_rgba(59,130,246,0.06)]">
                <div className="flex items-center gap-2 px-6 py-4 border-b border-white/[0.06] bg-white/[0.02]">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
                  <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                  <span className="ml-3 text-[12px] text-slate-500 font-medium">KIS FIX-4 Engine v2.0</span>
                </div>

                <div className="p-6 space-y-0">
                  {[
                    { label: "프로젝트", val: "OO빌딩 신축공사", status: "진행중", sc: "bg-emerald-400 text-emerald-900" },
                    { label: "차단기 선정", val: "MCCB 3P 225AF", status: "완료", sc: "bg-blue-400 text-blue-900" },
                    { label: "외함 산출", val: "H1400 x W800 x D250", status: "완료", sc: "bg-blue-400 text-blue-900" },
                    { label: "BOM 생성", val: "32개 품목", status: "완료", sc: "bg-blue-400 text-blue-900" },
                    { label: "견적 금액", val: "\\3,280,000", status: "확정", sc: "bg-amber-400 text-amber-900" },
                  ].map((row, i) => (
                    <div key={row.label} className={`flex items-center justify-between py-4 ${i < 4 ? "border-b border-white/[0.05]" : ""}`}>
                      <div>
                        <p className="text-[11px] text-slate-500 mb-0.5">{row.label}</p>
                        <p className="text-[14px] font-semibold text-white font-heading">{row.val}</p>
                      </div>
                      <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full ${row.sc}`}>{row.status}</span>
                    </div>
                  ))}
                </div>

                <div className="px-6 pb-5">
                  <div className="flex items-center justify-between text-[11px] text-slate-500 mb-2">
                    <span>AI 검증 진행률</span>
                    <span className="text-emerald-400 font-bold">6/6 통과</span>
                  </div>
                  <div className="h-2 bg-white/[0.06] rounded-full overflow-hidden">
                    <div className="h-full w-full bg-gradient-to-r from-blue-500 via-cyan-400 to-emerald-400 rounded-full" />
                  </div>
                </div>
              </div>

              <div className="absolute -left-8 bottom-16 bg-white rounded-xl px-5 py-4 shadow-[0_8px_30px_rgba(0,0,0,0.15),0_2px_8px_rgba(0,0,0,0.08)] border border-gray-100 hover:-translate-y-0.5 transition-transform duration-300">
                <p className="text-[10px] text-gray-400 font-medium mb-1">처리시간</p>
                <div className="flex items-baseline gap-1">
                  <span className="font-heading text-2xl font-extrabold text-gray-900">30</span>
                  <span className="text-sm font-bold text-red-500">초</span>
                </div>
              </div>

              <div className="absolute -right-4 -top-4 bg-white rounded-xl px-5 py-4 shadow-[0_8px_30px_rgba(0,0,0,0.15),0_2px_8px_rgba(0,0,0,0.08)] border border-gray-100 hover:-translate-y-0.5 transition-transform duration-300">
                <p className="text-[10px] text-gray-400 font-medium mb-1">금일 견적</p>
                <div className="flex items-baseline gap-1">
                  <span className="font-heading text-2xl font-extrabold text-gray-900">127</span>
                  <span className="text-sm font-bold text-emerald-500">건</span>
                </div>
              </div>
            </div>
          </div>

          {/* 하단 신뢰 수치 */}
          <div className="mt-20 grid grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12 border-t border-white/[0.06] pt-10">
            {STATS.map((stat) => (
              <div key={stat.label}>
                <div className="flex items-baseline gap-1">
                  <span className="font-heading text-4xl sm:text-5xl font-extrabold text-white tracking-tight">{stat.value}</span>
                  <span className="text-lg font-bold text-red-400/80">{stat.suffix}</span>
                </div>
                <p className="mt-2 text-sm text-slate-500 font-medium">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════
          COMPANY BRIEF — 실제 제품 사진 + 소개
          ══════════════════════════════════════ */}
      <section className="py-24 sm:py-32 bg-white relative overflow-hidden">
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-50/50 rounded-full blur-[100px]" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-red-50/30 rounded-full blur-[120px]" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            {/* 왼쪽: 텍스트 */}
            <div>
              <p className="text-sm font-bold text-red-600 tracking-[0.15em] uppercase mb-4">About HKKOR</p>
              <h2 className="font-heading text-3xl sm:text-4xl lg:text-[2.75rem] font-bold text-gray-900 tracking-tight leading-tight mb-6">
                제품에 특화된 생산 운영이
                <br />
                <span className="text-red-600">최고의 제품</span>을 만듭니다.
              </h2>
              <p className="text-gray-500 leading-relaxed text-lg mb-8">
                ㈜한국산업이앤에스는 20년간 분전반 및 기성함을 전문 제조해 온
                기업입니다. 최신 AI 견적 시스템과 숙련된 기술진이 빠르고
                정확한 서비스를 제공합니다.
              </p>

              <div className="grid grid-cols-2 gap-4">
                {[
                  { icon: Building2, label: "본사", value: "대구 북구" },
                  { icon: Award, label: "설립", value: "2014년" },
                  { icon: Truck, label: "납품", value: "전국 즉시배송" },
                  { icon: Cpu, label: "특화", value: "AI 견적 시스템" },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-3 bg-gray-50 rounded-xl px-4 py-3.5 border border-gray-100 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-300">
                    <div className="w-9 h-9 rounded-lg bg-white flex items-center justify-center border border-gray-100 shadow-sm shrink-0">
                      <item.icon className="w-4 h-4 text-gray-600" />
                    </div>
                    <div>
                      <p className="text-[10px] text-gray-400 font-medium uppercase tracking-wider">{item.label}</p>
                      <p className="text-sm font-bold text-gray-900">{item.value}</p>
                    </div>
                  </div>
                ))}
              </div>

              <Link href="/about" className="group inline-flex items-center gap-2 mt-8 text-sm font-bold text-red-600 hover:text-red-500 transition-colors">
                회사소개 더보기
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>

            {/* 오른쪽: 제품 사진 그리드 (2x2) */}
            <div className="grid grid-cols-2 gap-4">
              {[
                { src: "/images/about/intro1.webp", title: "기성함", desc: "철 / SUS 기성함 전 규격", href: "/products/steel-enclosure" },
                { src: "/images/about/intro2.webp", title: "분전반", desc: "기성 / EV / 태양광 분전반", href: "/products/distribution-panel" },
                { src: "/images/products/sec2_img1.webp", title: "계량기함", desc: "한전 규격 단상/삼상", href: "/products/meter-box" },
                { src: "/images/products/stainless1.jpg", title: "SUS 기성함", desc: "부식방지 스테인리스", href: "/products/stainless-enclosure" },
              ].map((item) => (
                <Link key={item.title} href={item.href} className="group relative rounded-2xl overflow-hidden aspect-square bg-gray-100 shadow-lg hover:shadow-2xl hover:-translate-y-1 transition-all duration-500 cursor-pointer">
                  <Image
                    src={item.src}
                    alt={item.title}
                    fill
                    className="object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent" />
                  <div className="absolute bottom-0 left-0 right-0 p-5">
                    <h3 className="font-heading text-lg font-bold text-white mb-0.5">{item.title}</h3>
                    <p className="text-sm text-white/70">{item.desc}</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════
          WHY CHOOSE US
          ══════════════════════════════════════ */}
      <section className="py-24 sm:py-32 bg-[#FAFAFA] shadow-[inset_0_2px_4px_rgba(0,0,0,0.02)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <p className="text-sm font-bold text-red-600 tracking-[0.15em] uppercase mb-4">Why Choose Us</p>
            <h2 className="font-heading text-3xl sm:text-4xl font-bold text-gray-900 tracking-tight">왜 한국산업인가</h2>
            <p className="mt-5 text-lg text-gray-500">20년 제조 노하우와 AI 기술을 결합한 차세대 견적 시스템</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {STRENGTHS.map((item, i) => (
              <div key={item.title} className="group bg-white rounded-2xl p-8 border border-gray-100 shadow-[0_1px_3px_rgba(0,0,0,0.04),0_4px_12px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.08),0_2px_8px_rgba(0,0,0,0.04)] hover:-translate-y-1.5 hover:border-gray-200 transition-all duration-400 relative overflow-hidden">
                <span className="absolute top-4 right-5 font-heading text-[4rem] font-extrabold text-gray-50 leading-none select-none">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div className={`relative inline-flex items-center justify-center w-12 h-12 rounded-xl border ${item.light} mb-6 group-hover:scale-110 transition-transform duration-300`}>
                  <item.icon className="w-5 h-5" />
                </div>
                <h3 className="relative font-heading text-xl font-bold text-gray-900 mb-3">{item.title}</h3>
                <p className="relative text-[15px] text-gray-500 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════
          PROCESS — 3단계
          ══════════════════════════════════════ */}
      <section className="py-24 sm:py-32 bg-gradient-to-b from-blue-50/60 via-white to-white relative overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-blue-100/30 rounded-full blur-[120px]" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <p className="text-sm font-bold text-blue-600 tracking-[0.15em] uppercase mb-4">How It Works</p>
            <h2 className="font-heading text-3xl sm:text-4xl font-bold text-gray-900 tracking-tight">3단계로 끝나는 AI 견적</h2>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {[
              { step: "01", title: "용도 선택", desc: "분전반 종류, 설치 위치, 재질을 카드 UI로 직관적으로 선택합니다.", color: "border-t-blue-600", bg: "bg-blue-600" },
              { step: "02", title: "차단기 구성", desc: "메인 차단기와 분기 차단기를 구성합니다. AI가 최적 사양을 추천합니다.", color: "border-t-cyan-500", bg: "bg-cyan-500" },
              { step: "03", title: "견적 확인", desc: "실시간 견적 결과를 확인합니다. BOM 테이블과 주문 문의까지 한번에.", color: "border-t-emerald-500", bg: "bg-emerald-500" },
            ].map((item) => (
              <div key={item.step} className={`bg-white rounded-2xl p-8 border border-gray-100 border-t-4 ${item.color} shadow-[0_2px_8px_rgba(0,0,0,0.04),0_8px_24px_rgba(0,0,0,0.03)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.1),0_4px_12px_rgba(0,0,0,0.05)] hover:-translate-y-1.5 transition-all duration-400`}>
                <div className="flex items-center gap-4 mb-5">
                  <div className={`w-10 h-10 rounded-full ${item.bg} text-white flex items-center justify-center text-sm font-bold font-heading`}>
                    {item.step}
                  </div>
                  <h3 className="font-heading text-xl font-bold text-gray-900">{item.title}</h3>
                </div>
                <p className="text-[15px] text-gray-500 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>

          <div className="mt-14 text-center">
            <Link href="/estimate" className="group inline-flex items-center gap-2.5 px-9 py-4 rounded-xl text-[15px] font-bold bg-blue-600 text-white hover:bg-blue-500 transition-all duration-200 hover:shadow-lg active:scale-[0.98]">
              지금 견적 시작하기
              <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════
          PRODUCTS — 실제 제품 사진 카드
          ══════════════════════════════════════ */}
      <section className="py-24 sm:py-32 bg-[#0F172A] relative overflow-hidden shadow-[inset_0_4px_12px_rgba(0,0,0,0.3)]">
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, rgba(255,255,255,0.15) 1px, transparent 0)`,
          backgroundSize: "32px 32px",
        }} />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6 mb-16">
            <div>
              <p className="text-sm font-bold text-red-400 tracking-[0.15em] uppercase mb-4">Products</p>
              <h2 className="font-heading text-3xl sm:text-4xl font-bold text-white tracking-tight">제품 라인업</h2>
              <p className="mt-4 text-slate-400 max-w-lg">분전반부터 기성함까지, IEC/KS 표준을 준수하는 전기설비의 모든 것</p>
            </div>
            <Link href="/products" className="group inline-flex items-center gap-2 text-sm font-bold text-red-400 hover:text-red-300 transition-colors shrink-0">
              전체 제품 보기 <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {PRODUCTS.map((product) => (
              <Link
                key={product.href}
                href={product.href}
                className="group relative bg-white/[0.04] rounded-2xl overflow-hidden border border-white/[0.06] hover:border-white/[0.15] shadow-[0_4px_20px_rgba(0,0,0,0.2)] hover:shadow-[0_8px_40px_rgba(0,0,0,0.35),0_0_20px_rgba(59,130,246,0.08)] hover:-translate-y-2 transition-all duration-400"
              >
                {/* 제품 이미지 */}
                <div className="relative h-48 bg-white/[0.02] overflow-hidden border-b border-white/[0.04]">
                  <Image
                    src={product.img}
                    alt={product.title}
                    fill
                    className="object-contain p-4 group-hover:scale-105 transition-transform duration-500"
                  />
                </div>
                <div className="p-6">
                  <h3 className="font-heading text-lg font-bold text-white mb-2 group-hover:text-red-300 transition-colors duration-200">
                    {product.title}
                  </h3>
                  <p className="text-sm text-slate-400 leading-relaxed mb-4">{product.desc}</p>
                  <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 group-hover:text-red-400 group-hover:gap-2.5 transition-all duration-200">
                    자세히 보기 <ChevronRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════
          TRUST — 밝은 배경 + 인증
          ══════════════════════════════════════ */}
      <section className="py-24 sm:py-32 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <p className="text-sm font-bold text-[#C8A96E] tracking-[0.15em] uppercase mb-4">Trust & Quality</p>
              <h2 className="font-heading text-3xl sm:text-4xl lg:text-[2.75rem] font-bold text-gray-900 mb-6 tracking-tight leading-tight">
                최고의 신뢰가
                <br />
                모든일에 있어 가장 중요하다.
              </h2>
              <p className="text-lg text-gray-500 leading-relaxed mb-10">
                한국산업이앤에스는 IEC 61439, KS C 4510 표준을 준수하는
                분전반 및 기성함 전문 제조기업입니다.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {CERTIFICATIONS.map((item) => (
                  <div key={item.text} className="flex items-center gap-3 bg-gray-50 rounded-xl px-5 py-4 border border-gray-100 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-300">
                    <item.icon className="w-5 h-5 text-[#C8A96E] shrink-0" />
                    <span className="text-sm font-semibold text-gray-700">{item.text}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-5">
              {STATS.map((stat) => (
                <div key={stat.label} className="bg-gradient-to-br from-white to-gray-50 rounded-2xl p-8 border border-gray-100 text-center shadow-[0_2px_8px_rgba(0,0,0,0.04),0_8px_24px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.08)] hover:-translate-y-1 transition-all duration-300">
                  <div className="flex items-baseline justify-center gap-1">
                    <span className="font-heading text-4xl sm:text-5xl font-extrabold text-gray-900 tracking-tight">{stat.value}</span>
                    <span className="text-lg font-bold text-[#C8A96E]">{stat.suffix}</span>
                  </div>
                  <p className="mt-2 text-sm text-gray-500 font-medium">{stat.label}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════
          CTA — 레드 그라데이션
          ══════════════════════════════════════ */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-red-700 via-red-600 to-red-700" />
        <div className="absolute inset-0 bg-gradient-to-b from-black/10 via-transparent to-black/15" />
        <div className="absolute inset-0 opacity-10" style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, rgba(255,255,255,0.2) 1px, transparent 0)`,
          backgroundSize: "24px 24px",
        }} />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-24">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-10">
            <div className="text-center lg:text-left">
              <h2 className="font-heading text-3xl sm:text-4xl font-bold text-white tracking-tight">견적이 필요하신가요?</h2>
              <p className="mt-3 text-red-100/80 text-[15px]">AI 견적은 무료입니다. 지금 바로 시작하세요.</p>
            </div>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link href="/estimate" className="group inline-flex items-center justify-center gap-2.5 px-8 py-4 rounded-xl text-[15px] font-bold bg-white text-red-700 hover:bg-red-50 transition-all duration-200 shadow-[0_4px_20px_rgba(0,0,0,0.2),0_8px_30px_rgba(0,0,0,0.1)] hover:shadow-[0_8px_40px_rgba(0,0,0,0.3)] active:scale-[0.98]">
                무료 AI 견적
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </Link>
              <a href="tel:053-792-1410" className="inline-flex items-center justify-center gap-2.5 px-8 py-4 rounded-xl text-[15px] font-semibold text-white border-2 border-white/30 hover:border-white/50 hover:bg-white/10 transition-all duration-200 active:scale-[0.98]">
                <Phone className="w-4 h-4" />
                053-792-1410
              </a>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
