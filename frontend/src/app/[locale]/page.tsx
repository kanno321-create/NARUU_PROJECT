'use client';

import { useTranslations } from 'next-intl';

export default function DashboardPage() {
  const t = useTranslations('dashboard');
  const nav = useTranslations('nav');
  const common = useTranslations('common');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-64 bg-white border-r border-gray-200 p-6">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-naruu-700">{common('appName')}</h1>
          <p className="text-xs text-gray-500 mt-1">{common('tagline')}</p>
        </div>
        <nav className="space-y-1">
          {[
            { key: 'dashboard', icon: '📊', href: '/' },
            { key: 'customers', icon: '👥', href: '/customers' },
            { key: 'partners', icon: '🏢', href: '/partners' },
            { key: 'products', icon: '🎌', href: '/products' },
            { key: 'bookings', icon: '📅', href: '/bookings' },
            { key: 'sales', icon: '💰', href: '/sales' },
            { key: 'schedules', icon: '🗓️', href: '/schedules' },
            { key: 'venues', icon: '📍', href: '/venues' },
            { key: 'accounting', icon: '💳', href: '/accounting' },
            { key: 'marketing', icon: '📣', href: '/marketing' },
            { key: 'line', icon: '💬', href: '/line' },
            { key: 'settings', icon: '⚙️', href: '/settings' },
          ].map((item) => (
            <a
              key={item.key}
              href={item.href}
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-700 hover:bg-naruu-50 hover:text-naruu-700 transition-colors"
            >
              <span>{item.icon}</span>
              <span>{nav(item.key as any)}</span>
            </a>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="ml-64 p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('title')}</h2>

        {/* Stats cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[
            { label: t('todayBookings'), value: '0', icon: '📅', color: 'bg-blue-50 text-blue-700' },
            { label: t('monthlyRevenue'), value: '¥0', icon: '💰', color: 'bg-green-50 text-green-700' },
            { label: t('newInquiries'), value: '0', icon: '💬', color: 'bg-yellow-50 text-yellow-700' },
            { label: t('activeCustomers'), value: '0', icon: '👥', color: 'bg-purple-50 text-purple-700' },
          ].map((stat) => (
            <div key={stat.label} className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-500">{stat.label}</span>
                <span className={`text-xl px-2 py-1 rounded-lg ${stat.color}`}>{stat.icon}</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Placeholder sections */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">最近の予約 / 최근 예약</h3>
            <p className="text-gray-500 text-sm">{common('noData')}</p>
          </div>
          <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">LINE メッセージ / LINE 메시지</h3>
            <p className="text-gray-500 text-sm">{common('noData')}</p>
          </div>
        </div>
      </main>
    </div>
  );
}
