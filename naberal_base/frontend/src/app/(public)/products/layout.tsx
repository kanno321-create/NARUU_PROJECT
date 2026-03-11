import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "제품소개 - 분전반·기성함·계량기함 | 한국산업 이앤에스",
  description:
    "철 기성함, 스테인리스 기성함, 계량기함, 기성 분전반, 전기차 분전반, 태양광 분전반. IEC/KS 표준 준수 전기설비 전 제품군.",
  openGraph: {
    title: "제품소개 - 한국산업 이앤에스",
    description: "분전반부터 기성함까지, IEC/KS 표준 준수 전기설비 전 제품군.",
    url: "https://hkkor.com/products",
  },
};

export default function ProductsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
