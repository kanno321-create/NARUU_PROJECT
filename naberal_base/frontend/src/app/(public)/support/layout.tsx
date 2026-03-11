import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "고객지원 - 공지사항·FAQ·문의 | 한국산업 이앤에스",
  description:
    "견적 문의, 기술 지원, A/S 요청. 053-792-1410. 평일 09:00-18:00.",
  openGraph: {
    title: "고객지원 - 한국산업 이앤에스",
    description: "견적 문의, FAQ, 기술지원, A/S 요청.",
    url: "https://hkkor.com/support",
  },
};

export default function SupportLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
