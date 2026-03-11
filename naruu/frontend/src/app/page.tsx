"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";

export default function Home() {
  const router = useRouter();
  const token = useAuthStore((s) => s.accessToken);

  useEffect(() => {
    if (token) {
      router.replace("/dashboard");
    } else {
      router.replace("/auth/login");
    }
  }, [token, router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-pulse text-naruu-600 text-xl font-semibold">
        NARUU 로딩 중...
      </div>
    </div>
  );
}
