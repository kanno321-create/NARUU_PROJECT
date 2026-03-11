import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NARUU - 나루 종합 업무관리",
  description: "의료관광·관광·굿즈·AI·LINE 통합 관리 시스템",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="bg-gray-50 text-gray-900 min-h-screen">{children}</body>
    </html>
  );
}
