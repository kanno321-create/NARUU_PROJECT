"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/dashboard", label: "대시보드", icon: "📊" },
  { href: "/customers", label: "고객 관리", icon: "👥" },
  { href: "/reservations", label: "예약/캘린더", icon: "📅" },
  { href: "/packages", label: "패키지", icon: "🎁" },
  { href: "/routes", label: "관광 루트", icon: "🗺️" },
  { href: "/finance", label: "매출/매입", icon: "💰" },
  { href: "/content", label: "콘텐츠", icon: "🎬" },
  { href: "/reviews", label: "리뷰", icon: "⭐" },
  { href: "/partners", label: "제휴 병원", icon: "🏥" },
  { href: "/goods", label: "굿즈", icon: "🛍️" },
  { href: "/ai", label: "AI 채팅", icon: "🤖" },
  { href: "/settings", label: "설정", icon: "⚙️" },
];

interface SidebarProps {
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export default function Sidebar({ mobileOpen, onMobileClose }: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={onMobileClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 flex flex-col transform transition-transform duration-200 ease-in-out md:relative md:translate-x-0 md:z-auto ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="p-6 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-naruu-700">NARUU</h1>
            <p className="text-xs text-gray-400 mt-1">종합 업무관리</p>
          </div>
          <button
            onClick={onMobileClose}
            className="md:hidden p-1 text-gray-400 hover:text-gray-600"
            aria-label="사이드바 닫기"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <nav className="flex-1 py-4" aria-label="메인 네비게이션">
          {navItems.map((item) => {
            const isActive = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onMobileClose}
                className={`flex items-center gap-3 px-6 py-2.5 text-sm transition ${
                  isActive
                    ? "bg-naruu-50 text-naruu-700 font-semibold border-r-2 border-naruu-600"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                }`}
              >
                <span className="text-lg" aria-hidden="true">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
