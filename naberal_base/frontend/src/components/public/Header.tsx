"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X, ChevronDown, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  {
    label: "회사소개",
    href: "/about",
    children: [
      { label: "회사개요", href: "/about" },
      { label: "인사말", href: "/about/greeting" },
      { label: "조직도", href: "/about/organization" },
      { label: "전국지사", href: "/about/branches" },
      { label: "인증서", href: "/about/certificates" },
      { label: "오시는 길", href: "/about/location" },
    ],
  },
  {
    label: "제품소개",
    href: "/products",
    children: [
      { label: "철 기성함", href: "/products/steel-enclosure" },
      { label: "스테인리스 기성함", href: "/products/stainless-enclosure" },
      { label: "계량기함", href: "/products/meter-box" },
      { label: "기성 분전반", href: "/products/distribution-panel" },
      { label: "전기차 분전반", href: "/products/ev-panel" },
      { label: "태양광", href: "/products/solar-panel" },
    ],
  },
  {
    label: "고객지원",
    href: "/support",
    children: [
      { label: "공지사항", href: "/support/notice" },
      { label: "FAQ", href: "/support/faq" },
      { label: "문의하기", href: "/support/contact" },
    ],
  },
];

export function Header() {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
    setActiveDropdown(null);
  }, [pathname]);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [mobileOpen]);

  return (
    <>
      {/* 상단 레드 악센트 라인 */}
      <div className="fixed top-0 left-0 right-0 z-[60] h-[3px] bg-gradient-to-r from-red-600 via-red-500 to-red-600" />

      <header
        className={cn(
          "fixed top-[3px] left-0 right-0 z-50 transition-all duration-300 bg-white",
          scrolled
            ? "shadow-[0_2px_20px_-4px_rgba(0,0,0,0.1)]"
            : "shadow-[0_1px_0_0_rgba(0,0,0,0.06)]"
        )}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20 lg:h-24">
            {/* Logo */}
            <Link href="/home" className="flex items-center gap-4 group">
              {/* HK 로고 마크 */}
              <div className="flex items-center justify-center w-12 h-12 bg-[#0F172A] rounded-lg">
                <span className="font-heading text-[18px] font-extrabold text-white tracking-tight">HK</span>
              </div>
              <div className="flex flex-col">
                <span className="font-heading text-[24px] font-bold leading-tight tracking-tight text-gray-900">
                  한국산업 E&S
                </span>
                <span className="text-[11px] font-medium leading-tight tracking-[0.15em] uppercase text-gray-400">
                  HANKOOK INDUSTRY E&S
                </span>
              </div>
            </Link>

            {/* Desktop Nav */}
            <nav className="hidden lg:flex items-center gap-0.5">
              {NAV_ITEMS.map((item) => (
                <div
                  key={item.href}
                  className="relative group"
                  onMouseEnter={() => setActiveDropdown(item.href)}
                  onMouseLeave={() => setActiveDropdown(null)}
                >
                  <Link
                    href={item.href}
                    className={cn(
                      "relative flex items-center gap-1.5 px-6 py-3 text-[20px] font-semibold transition-all duration-200",
                      "text-gray-700 hover:text-gray-900",
                      pathname.startsWith(item.href) && "text-red-600"
                    )}
                  >
                    {item.label}
                    {item.children && (
                      <ChevronDown className="w-3.5 h-3.5 opacity-40 transition-transform duration-200 group-hover:rotate-180" />
                    )}
                    {/* 활성 언더라인 */}
                    {pathname.startsWith(item.href) && (
                      <span className="absolute bottom-0 left-6 right-6 h-[2px] bg-red-600 rounded-full" />
                    )}
                  </Link>

                  {/* Dropdown */}
                  {item.children && activeDropdown === item.href && (
                    <div className="absolute top-full left-0 pt-2 min-w-[240px]">
                      <div className="bg-[#1E293B] rounded-xl shadow-xl shadow-black/20 overflow-hidden py-2">
                        {item.children.map((child) => (
                          <Link
                            key={child.href}
                            href={child.href}
                            className={cn(
                              "block px-6 py-3.5 text-[16px] transition-colors duration-150",
                              pathname === child.href
                                ? "text-white bg-white/10 font-semibold"
                                : "text-slate-300 hover:text-white hover:bg-white/[0.06]"
                            )}
                          >
                            {child.label}
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </nav>

            {/* CTA + Mobile Toggle */}
            <div className="flex items-center gap-3">
              <Link
                href="/estimate"
                className="hidden sm:inline-flex items-center gap-2.5 px-7 py-3 rounded-lg text-[16px] font-bold transition-all duration-200 bg-red-600 text-white hover:bg-red-500 active:scale-[0.98]"
              >
                견적의뢰
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>

              <button
                onClick={() => setMobileOpen(!mobileOpen)}
                className="lg:hidden flex items-center justify-center w-10 h-10 rounded-lg text-gray-700 hover:bg-gray-100 transition-all"
              >
                {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        <div className={cn(
          "lg:hidden fixed inset-0 top-[83px] lg:top-[99px] z-40 transition-all duration-300",
          mobileOpen ? "opacity-100 visible" : "opacity-0 invisible pointer-events-none"
        )}>
          <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <div className={cn(
            "relative bg-white border-t border-gray-100 max-h-[calc(100vh-99px)] overflow-y-auto",
            "transition-transform duration-300",
            mobileOpen ? "translate-y-0" : "-translate-y-4"
          )}>
            <div className="p-4 space-y-1">
              {NAV_ITEMS.map((item) => (
                <div key={item.href}>
                  <Link
                    href={item.href}
                    className={cn(
                      "block px-4 py-3 text-base font-semibold rounded-lg hover:bg-gray-50",
                      pathname.startsWith(item.href) ? "text-red-600" : "text-gray-800"
                    )}
                  >
                    {item.label}
                  </Link>
                  {item.children && (
                    <div className="ml-4 space-y-0.5">
                      {item.children.map((child) => (
                        <Link
                          key={child.href}
                          href={child.href}
                          className={cn(
                            "block px-4 py-2 text-sm rounded-lg transition-colors",
                            pathname === child.href
                              ? "text-red-600 bg-red-50 font-medium"
                              : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                          )}
                        >
                          {child.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              <div className="pt-4 border-t border-gray-100">
                <Link
                  href="/estimate"
                  className="flex items-center justify-center gap-2 w-full px-5 py-3 rounded-xl text-base font-semibold bg-red-600 text-white"
                >
                  견적의뢰
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </header>
    </>
  );
}
