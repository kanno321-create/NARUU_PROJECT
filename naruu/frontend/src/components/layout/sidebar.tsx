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

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen flex flex-col">
      <div className="p-6 border-b border-gray-100">
        <h1 className="text-2xl font-bold text-naruu-700">NARUU</h1>
        <p className="text-xs text-gray-400 mt-1">종합 업무관리</p>
      </div>

      <nav className="flex-1 py-4">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-6 py-2.5 text-sm transition ${
                isActive
                  ? "bg-naruu-50 text-naruu-700 font-semibold border-r-2 border-naruu-600"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
