"use client";

import React from "react";
import { Award, ShieldCheck, FileCheck } from "lucide-react";

const CERTIFICATES = [
  {
    icon: Award,
    name: "ISO 9001",
    desc: "품질경영시스템 인증",
    issuer: "한국인증원",
    color: "from-blue-500 to-blue-600",
  },
  {
    icon: ShieldCheck,
    name: "IEC 61439",
    desc: "저압 개폐장치 국제규격 적합",
    issuer: "국제전기기술위원회",
    color: "from-emerald-500 to-emerald-600",
  },
  {
    icon: FileCheck,
    name: "KS C 4510",
    desc: "분전반 한국산업표준 인증",
    issuer: "한국표준협회",
    color: "from-violet-500 to-violet-600",
  },
  {
    icon: Award,
    name: "전기용품 안전인증",
    desc: "전기용품 및 생활용품 안전관리법",
    issuer: "한국전기안전공사",
    color: "from-amber-500 to-amber-600",
  },
  {
    icon: ShieldCheck,
    name: "공장등록증",
    desc: "전기설비 제조 공장 등록",
    issuer: "산업통상자원부",
    color: "from-rose-500 to-rose-600",
  },
  {
    icon: FileCheck,
    name: "기업부설연구소",
    desc: "연구개발 전담부서 인증",
    issuer: "한국산업기술진흥협회",
    color: "from-cyan-500 to-cyan-600",
  },
];

export default function CertificatesPage() {
  return (
    <div className="pt-[99px]">
      <section className="bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 py-16 sm:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <span className="text-sm font-semibold text-blue-400 tracking-wider uppercase">
            Certificates
          </span>
          <h1 className="mt-3 text-3xl sm:text-4xl font-bold text-white tracking-tight">
            인증서
          </h1>
          <p className="mt-4 text-lg text-slate-300">
            국제·국내 표준을 준수하는 인증된 품질
          </p>
        </div>
      </section>

      <section className="py-16 sm:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {CERTIFICATES.map((cert) => (
              <div
                key={cert.name}
                className="bg-white rounded-2xl p-7 border border-slate-100 hover:border-blue-200 hover:shadow-lg transition-all"
              >
                <div
                  className={`inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br ${cert.color} text-white mb-5`}
                >
                  <cert.icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-1">
                  {cert.name}
                </h3>
                <p className="text-sm text-slate-500 mb-3">{cert.desc}</p>
                <p className="text-xs text-slate-400">발급: {cert.issuer}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
