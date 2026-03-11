"use client";

import React from "react";
import Link from "next/link";
import { Phone, Mail, MapPin, ArrowRight } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-[#0B1120] text-slate-400">
      {/* CTA Band */}
      <div className="border-b border-white/[0.06]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
            <div>
              <h3 className="font-heading text-xl sm:text-2xl font-bold text-white tracking-tight">
                지금 바로 AI 견적을 받아보세요
              </h3>
              <p className="mt-2 text-sm text-slate-500">
                30초 만에 정확한 분전반 견적을 확인할 수 있습니다.
              </p>
            </div>
            <Link
              href="/estimate"
              className="group inline-flex items-center gap-2.5 px-7 py-3.5 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-500 transition-all duration-200 text-sm shrink-0 active:scale-[0.98]"
            >
              무료 견적 시작
              <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>
        </div>
      </div>

      {/* Main Footer */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14 sm:py-16">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">
          {/* Company Info */}
          <div className="sm:col-span-2 lg:col-span-1">
            <div className="mb-4">
              <span className="font-heading text-lg font-bold text-white tracking-tight">
                한국산업 E&S
              </span>
              <p className="text-[10px] text-slate-600 tracking-[0.12em] uppercase mt-0.5">
                HKKOR
              </p>
            </div>
            <p className="text-sm text-slate-500 leading-relaxed">
              분전반 및 기성함 전문 제조기업.
              <br />
              AI 기반 견적 시스템으로
              <br />
              빠르고 정확한 서비스를 제공합니다.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-xs font-semibold text-slate-300 tracking-[0.15em] uppercase mb-5">
              제품
            </h4>
            <ul className="space-y-3">
              {[
                { label: "철 기성함", href: "/products/steel-enclosure" },
                { label: "스테인리스 기성함", href: "/products/stainless-enclosure" },
                { label: "계량기함", href: "/products/meter-box" },
                { label: "기성 분전반", href: "/products/distribution-panel" },
                { label: "전기차 분전반", href: "/products/ev-panel" },
                { label: "태양광", href: "/products/solar-panel" },
              ].map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-500 hover:text-white transition-colors duration-200"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company Links */}
          <div>
            <h4 className="text-xs font-semibold text-slate-300 tracking-[0.15em] uppercase mb-5">
              회사
            </h4>
            <ul className="space-y-3">
              {[
                { label: "회사소개", href: "/about" },
                { label: "인사말", href: "/about/greeting" },
                { label: "전국지사", href: "/about/branches" },
                { label: "인증서", href: "/about/certificates" },
                { label: "공지사항", href: "/support/notice" },
                { label: "견적 문의", href: "/support/contact" },
              ].map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-500 hover:text-white transition-colors duration-200"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="text-xs font-semibold text-slate-300 tracking-[0.15em] uppercase mb-5">
              연락처
            </h4>
            <ul className="space-y-4">
              <li className="flex items-start gap-3">
                <Phone className="w-4 h-4 text-slate-600 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm text-white font-medium">053-792-1410</p>
                  <p className="text-xs text-slate-600 mt-0.5">평일 09:00 - 18:00</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <Mail className="w-4 h-4 text-slate-600 mt-0.5 shrink-0" />
                <p className="text-sm text-slate-500">info@hkkor.com</p>
              </li>
              <li className="flex items-start gap-3">
                <MapPin className="w-4 h-4 text-slate-600 mt-0.5 shrink-0" />
                <p className="text-sm text-slate-500 leading-relaxed">
                  대구 북구 검단공단로21길
                  <br />
                  54-22
                </p>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-white/[0.06]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <p className="text-xs text-slate-600">
              &copy; {new Date().getFullYear()} ㈜한국산업이앤에스 | 대표이사: 이광원 | 사업자등록번호: 502-86-34015
            </p>
            <div className="flex items-center gap-6">
              <Link
                href="/terms"
                className="text-xs text-slate-600 hover:text-slate-400 transition-colors duration-200"
              >
                이용약관
              </Link>
              <Link
                href="/privacy"
                className="text-xs text-slate-600 hover:text-slate-400 transition-colors duration-200"
              >
                개인정보처리방침
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
