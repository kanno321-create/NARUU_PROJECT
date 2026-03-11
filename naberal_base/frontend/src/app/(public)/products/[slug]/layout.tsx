export function generateStaticParams() {
  return [
    { slug: "steel-enclosure" },
    { slug: "stainless-enclosure" },
    { slug: "meter-box" },
    { slug: "distribution-panel" },
    { slug: "ev-panel" },
    { slug: "solar-panel" },
  ];
}

export default function ProductSlugLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
