"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";

const PORTAL_NAV = [
  { href: "/portal/estimates", label: "내 견적", icon: "📋" },
  { href: "/portal/orders", label: "내 주문", icon: "📦" },
  { href: "/portal/chat", label: "AI 상담", icon: "🤖" },
  { href: "/portal/contact", label: "직원 상담", icon: "💬" },
  { href: "/portal/profile", label: "내 정보", icon: "👤" },
];

function PortalGuard({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login?redirect=/portal/estimates");
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-500">로딩 중...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return <>{children}</>;
}

function PortalShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-6">
              <Link href="/home" className="text-xl font-bold text-blue-800">
                한국산업 E&S
              </Link>
              <span className="text-sm text-slate-400 hidden sm:inline">|</span>
              <span className="text-sm text-slate-600 hidden sm:inline">고객 포털</span>
            </div>

            <div className="flex items-center gap-4">
              <span className="text-sm text-slate-600 hidden sm:inline">
                {user?.full_name || user?.email}
              </span>
              <button
                onClick={() => logout()}
                className="text-sm text-slate-500 hover:text-slate-700 transition-colors"
              >
                로그아웃
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col sm:flex-row gap-6">
          {/* Side Nav */}
          <nav className="sm:w-48 flex-shrink-0">
            <ul className="flex sm:flex-col gap-1 overflow-x-auto sm:overflow-visible">
              {PORTAL_NAV.map((item) => {
                const active = pathname.startsWith(item.href);
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                        active
                          ? "bg-blue-50 text-blue-700"
                          : "text-slate-600 hover:bg-slate-100"
                      }`}
                    >
                      <span>{item.icon}</span>
                      {item.label}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* Content */}
          <main className="flex-1 min-w-0">{children}</main>
        </div>
      </div>
    </div>
  );
}

export default function PortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <PortalGuard>
        <PortalShell>{children}</PortalShell>
      </PortalGuard>
    </AuthProvider>
  );
}
