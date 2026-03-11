"use client";

import AppShell from "@/components/layout/app-shell";

export default function SettingsPage() {
  return (
    <AppShell>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">설정</h2>
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <p className="text-gray-500">시스템 설정 (LINE API, Claude API, 알림 등)이 여기에 표시됩니다.</p>
      </div>
    </AppShell>
  );
}
