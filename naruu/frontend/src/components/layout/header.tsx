"use client";

import { useAuthStore } from "@/stores/auth-store";
import { useRouter } from "next/navigation";

export default function Header() {
  const { user, logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/auth/login");
  };

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div />
      <div className="flex items-center gap-4">
        {user && (
          <span className="text-sm text-gray-600">
            {user.name_ko}{" "}
            <span className="text-xs text-gray-400">({user.role})</span>
          </span>
        )}
        <button
          onClick={handleLogout}
          className="text-sm text-gray-500 hover:text-red-600 transition"
        >
          로그아웃
        </button>
      </div>
    </header>
  );
}
