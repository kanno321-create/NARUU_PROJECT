"use client";

import { ClientLayout } from "@/components/layout/ClientLayout";

export default function InternalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div style={{ backgroundColor: 'var(--color-bg)' }} className="bg-surface-secondary">
      <ClientLayout>{children}</ClientLayout>
    </div>
  );
}
