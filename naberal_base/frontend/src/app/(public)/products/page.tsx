"use client";

import React from "react";
import Link from "next/link";
import Image from "next/image";
import { ArrowRight } from "lucide-react";

const PRODUCTS = [
  {
    title: "철 기성함",
    desc: "HDS(옥내노출), HT(옥외노출), HB(콘트롤박스), HS(매입함) 4종. 다양한 규격 즉시 납품.",
    href: "/products/steel-enclosure",
    img: "/images/products/steel1.jpg",
    specs: ["SPC 1.0t~1.6t", "4종 타입", "옥내/옥외"],
    price: "21,000원~",
  },
  {
    title: "스테인리스 기성함",
    desc: "SHDS(옥내노출), SS(매입함커버), SC(옥외노출) 3종. 내부식성 우수.",
    href: "/products/stainless-enclosure",
    img: "/images/products/stainless1.jpg",
    specs: ["SUS 201", "3종 타입", "옥외/옥내"],
    price: "23,000원~",
  },
  {
    title: "계량기함",
    desc: "CT-1, CT-2, 단상/삼상, 자립형, 전기차 전용 등 다양한 타입 보유.",
    href: "/products/meter-box",
    img: "/images/products/meter1.jpg",
    specs: ["STS 201", "한전 규격", "옥외 방수"],
    price: "85,000원~",
  },
  {
    title: "기성 분전반",
    desc: "NO.1~NO.5 표준 모델. IEC 61439, KS C 4510 준수. 노출함/매입함 선택.",
    href: "/products/distribution-panel",
    img: "/images/products/panel1.jpg",
    specs: ["IEC 61439", "KS 표준", "즉시 납품"],
    price: "200,000원~",
  },
  {
    title: "전기차 분전반",
    desc: "급속(100KW/200KW) 및 완속(7KW) 충전기 대응. CT 계량기 일체형.",
    href: "/products/ev-panel",
    img: "/images/products/ev1.jpg",
    specs: ["급속/완속", "EV 전용", "누전차단"],
    price: "45,000원~",
  },
  {
    title: "태양광 분전반",
    desc: "30~50KW, 100KW 2가지 타입. 인버터 연동 설계. 상도/대륙/LS 브랜드.",
    href: "/products/solar-panel",
    img: "/images/products/solar2.jpg",
    specs: ["인버터 연동", "신재생에너지", "계통연계"],
    price: "480,000원~",
  },
];

export default function ProductsPage() {
  return (
    <div className="pt-[99px]">
      {/* Hero */}
      <section className="bg-[#0B1120] py-16 sm:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-sm font-bold text-red-400 tracking-[0.15em] uppercase">Products</p>
          <h1 className="mt-4 font-heading text-3xl sm:text-4xl lg:text-5xl font-bold text-white tracking-tight">
            제품소개
          </h1>
          <p className="mt-5 text-lg text-slate-400 max-w-xl">
            분전반부터 기성함까지, IEC/KS 표준을 준수하는 전기설비 전 제품군
          </p>
        </div>
      </section>

      {/* 제품 그리드 */}
      <section className="py-20 sm:py-28 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {PRODUCTS.map((product) => (
              <Link
                key={product.href}
                href={product.href}
                className="group bg-white rounded-2xl border border-gray-100 hover:border-gray-200 shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden"
              >
                {/* 제품 이미지 */}
                <div className="relative h-56 bg-gray-50 overflow-hidden">
                  <Image
                    src={product.img}
                    alt={product.title}
                    fill
                    className="object-contain p-6 group-hover:scale-105 transition-transform duration-500"
                  />
                </div>

                <div className="p-6">
                  <h3 className="font-heading text-xl font-bold text-gray-900 mb-2 group-hover:text-red-600 transition-colors">
                    {product.title}
                  </h3>
                  <p className="text-sm text-gray-500 leading-relaxed mb-4">{product.desc}</p>

                  {/* 스펙 태그 */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {product.specs.map((spec) => (
                      <span key={spec} className="text-xs font-medium text-blue-600 bg-blue-50 px-2.5 py-1 rounded-md">
                        {spec}
                      </span>
                    ))}
                  </div>

                  {/* 가격 + 링크 */}
                  <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                    <span className="text-lg font-bold text-red-600 font-heading">{product.price}</span>
                    <span className="inline-flex items-center gap-1 text-sm font-semibold text-gray-400 group-hover:text-red-600 group-hover:gap-2 transition-all">
                      상세보기 <ArrowRight className="w-4 h-4" />
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
