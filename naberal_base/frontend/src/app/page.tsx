"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

// 루트 경로는 공개 랜딩페이지로 이동
export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/home");
  }, [router]);

  return null;
}
