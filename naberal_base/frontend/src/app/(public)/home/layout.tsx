import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "㈜한국산업 이앤에스 - 분전반·기성함 전문기업 | AI 견적",
  description:
    "20년 전통의 분전반·기성함 전문 제조기업. AI 견적 시스템으로 30초 만에 정확한 분전반 견적을 받아보세요. IEC 61439, KS C 4510 표준 준수.",
  keywords:
    "분전반, 기성함, 전기설비, AI 견적, 전기차 분전반, 태양광 분전반, 계량기함, 한국산업",
  openGraph: {
    title: "㈜한국산업 이앤에스 - AI 분전반 견적",
    description:
      "분전반·기성함 전문 제조기업. AI 기반 실시간 견적 시스템.",
    url: "https://hkkor.com",
    siteName: "한국산업 이앤에스",
    locale: "ko_KR",
    type: "website",
  },
};

export default function HomeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
