import type { Metadata, Viewport } from "next";
import { Montserrat } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";
import { ThemeProvider } from "@/contexts/ThemeContext";

const montserrat = Montserrat({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-heading",
  display: "swap",
});

export const metadata: Metadata = {
  title: "㈜한국산업 이앤에스 - 분전반·기성함 전문기업",
  description: "분전반, 기성함, 전기설비 전문 제조기업. AI 견적 시스템으로 실시간 견적을 받아보세요.",
  keywords: "분전반, 기성함, 전기설비, 전기차 분전반, 태양광 분전반, 계량기함, AI 견적",
  openGraph: {
    title: "㈜한국산업 이앤에스",
    description: "분전반·기성함 전문 제조기업. AI 기반 실시간 견적 시스템.",
    url: "https://hkkor.com",
    siteName: "한국산업 이앤에스",
    locale: "ko_KR",
    type: "website",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" suppressHydrationWarning className={montserrat.variable}>
      <head>
        <link
          rel="stylesheet"
          as="style"
          crossOrigin="anonymous"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css"
        />
      </head>
      <body className={cn("antialiased font-body")}>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
