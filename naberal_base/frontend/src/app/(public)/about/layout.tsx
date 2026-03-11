import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "회사소개 - ㈜한국산업 이앤에스",
  description:
    "분전반·기성함 전문 제조기업. IEC 61439, KS C 4510 준수. 대구 북구 본사.",
  openGraph: {
    title: "회사소개 - 한국산업 이앤에스",
    description: "분전반·기성함 전문 제조기업 한국산업 이앤에스.",
    url: "https://hkkor.com/about",
  },
};

export default function AboutLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
