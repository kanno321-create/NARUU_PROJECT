"use client";

import React from "react";
import { MapPin, Phone, Mail, Clock, Car, Train } from "lucide-react";

export default function LocationPage() {
  return (
    <div className="pt-[99px]">
      <section className="bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 py-16 sm:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <span className="text-sm font-semibold text-blue-400 tracking-wider uppercase">
            Location
          </span>
          <h1 className="mt-3 text-3xl sm:text-4xl font-bold text-white tracking-tight">
            오시는 길
          </h1>
        </div>
      </section>

      <section className="py-16 sm:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            {/* 지도 영역 */}
            <div className="bg-slate-100 rounded-2xl overflow-hidden aspect-[4/3] flex items-center justify-center">
              <iframe
                src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3231.5!2d128.55!3d35.92!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2z64yA6rWsIOu2geq1rCDqsoDri6jqs7Xri6jroZwyMeq4uCA1NC0yMg!5e0!3m2!1sko!2skr!4v1"
                className="w-full h-full border-0"
                allowFullScreen
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
                title="한국산업이앤에스 본사 위치"
              />
            </div>

            {/* 정보 */}
            <div className="space-y-8">
              <div>
                <h2 className="text-2xl font-bold text-slate-900 mb-2">
                  ㈜한국산업이앤에스 본사
                </h2>
                <p className="text-slate-500">
                  대구 북구 검단공단로21길 54-22
                </p>
              </div>

              <div className="space-y-5">
                {[
                  { icon: Phone, label: "전화", value: "053-792-1410(1415)" },
                  { icon: Mail, label: "이메일", value: "info@hkkor.com" },
                  { icon: Clock, label: "업무시간", value: "평일 09:00 - 18:00 (토·일·공휴일 휴무)" },
                ].map((item) => (
                  <div key={item.label} className="flex items-start gap-4">
                    <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-50 text-blue-600 shrink-0">
                      <item.icon className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 uppercase tracking-wider">{item.label}</p>
                      <p className="text-sm font-medium text-slate-900">{item.value}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="pt-6 border-t border-slate-100">
                <h3 className="text-base font-bold text-slate-900 mb-4">교통 안내</h3>
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <Car className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-slate-900">자가용</p>
                      <p className="text-sm text-slate-500">검단IC에서 5분 거리, 검단공단 내 위치</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <Train className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-slate-900">대중교통</p>
                      <p className="text-sm text-slate-500">대구 북구 버스 이용, 검단공단 정류장 하차</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
