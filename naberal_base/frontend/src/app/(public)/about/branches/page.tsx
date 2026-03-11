"use client";

import React from "react";
import { MapPin, Phone } from "lucide-react";

const BRANCHES = [
  { region: "대구", name: "본사/공장", address: "대구 북구 검단공단로21길 54-22", tel: "053-792-1410" },
  { region: "서울", name: "서울지사", address: "서울특별시", tel: "02-000-0000" },
  { region: "인천", name: "인천지사", address: "인천광역시", tel: "032-000-0000" },
  { region: "부산", name: "부산지사", address: "부산광역시", tel: "051-000-0000" },
  { region: "광주", name: "광주지사", address: "광주광역시", tel: "062-000-0000" },
  { region: "대전", name: "대전지사", address: "대전광역시", tel: "042-000-0000" },
  { region: "경기", name: "경기지사", address: "경기도", tel: "031-000-0000" },
  { region: "강원", name: "강원지사", address: "강원특별자치도", tel: "033-000-0000" },
];

export default function BranchesPage() {
  return (
    <div className="pt-[99px]">
      <section className="bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 py-16 sm:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <span className="text-sm font-semibold text-blue-400 tracking-wider uppercase">
            Branches
          </span>
          <h1 className="mt-3 text-3xl sm:text-4xl font-bold text-white tracking-tight">
            전국지사
          </h1>
          <p className="mt-4 text-lg text-slate-300">
            전국 어디서나 신속한 납품과 A/S를 제공합니다.
          </p>
        </div>
      </section>

      <section className="py-16 sm:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {BRANCHES.map((branch) => (
              <div
                key={branch.region}
                className={`rounded-2xl p-6 border transition-all ${
                  branch.region === "대구"
                    ? "bg-blue-50 border-blue-200 ring-2 ring-blue-100"
                    : "bg-white border-slate-100 hover:border-blue-200 hover:shadow-md"
                }`}
              >
                <div className="flex items-center gap-2 mb-3">
                  <MapPin className={`w-5 h-5 ${branch.region === "대구" ? "text-blue-600" : "text-slate-400"}`} />
                  <span className="text-xs font-semibold text-blue-600 tracking-wider uppercase">
                    {branch.region}
                  </span>
                  {branch.region === "대구" && (
                    <span className="text-[10px] font-bold text-blue-600 bg-blue-100 px-2 py-0.5 rounded-full">
                      본사
                    </span>
                  )}
                </div>
                <h3 className="text-base font-bold text-slate-900 mb-2">
                  {branch.name}
                </h3>
                <p className="text-sm text-slate-500 mb-3 leading-relaxed">
                  {branch.address}
                </p>
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Phone className="w-3.5 h-3.5 text-blue-500" />
                  {branch.tel}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
