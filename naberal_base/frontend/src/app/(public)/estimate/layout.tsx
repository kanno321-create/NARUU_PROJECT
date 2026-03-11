import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI 분전반 견적 - 30초 만에 견적 완성 | 한국산업 이앤에스",
  description:
    "AI가 차단기 선정, 외함 크기 산출, BOM 생성까지 자동 처리합니다. 3단계만 완성하면 정확한 분전반 견적을 받을 수 있습니다.",
  openGraph: {
    title: "AI 분전반 견적 - 한국산업 이앤에스",
    description: "30초 만에 정확한 분전반 견적. AI 기반 자동 산출 시스템.",
    url: "https://hkkor.com/estimate",
  },
};

export default function EstimateLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
