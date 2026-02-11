import { useTranslation } from 'react-i18next';
import { useAppStore } from '@/lib/store';

export default function Dashboard() {
  const { t } = useTranslation();
  const { user } = useAppStore();

  const stats = [
    { label: t('dashboard.todayBookings'), value: '0', icon: '📅', color: 'bg-blue-50 text-blue-600' },
    { label: t('dashboard.monthlyRevenue'), value: '¥0', icon: '💰', color: 'bg-green-50 text-green-600' },
    { label: t('dashboard.newInquiries'), value: '0', icon: '💬', color: 'bg-amber-50 text-amber-600' },
    { label: t('dashboard.activeCustomers'), value: '0', icon: '👥', color: 'bg-purple-50 text-purple-600' },
  ];

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{t('dashboard.title')}</h2>
          {user && (
            <p className="text-sm text-gray-500 mt-1">
              ようこそ、{user.name}さん
            </p>
          )}
        </div>
        <div className="text-sm text-gray-400">
          {new Date().toLocaleDateString('ja-JP', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            weekday: 'long',
          })}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-500">{stat.label}</span>
              <span className={`text-lg w-9 h-9 flex items-center justify-center rounded-lg ${stat.color}`}>
                {stat.icon}
              </span>
            </div>
            <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Bookings */}
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <h3 className="text-base font-semibold text-gray-900 mb-4">
            {t('dashboard.recentBookings')}
          </h3>
          <div className="text-center py-8">
            <p className="text-4xl mb-2">📅</p>
            <p className="text-gray-400 text-sm">{t('common.noData')}</p>
          </div>
        </div>

        {/* LINE Messages */}
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <h3 className="text-base font-semibold text-gray-900 mb-4">
            {t('dashboard.lineMessages')}
          </h3>
          <div className="text-center py-8">
            <p className="text-4xl mb-2">💬</p>
            <p className="text-gray-400 text-sm">{t('common.noData')}</p>
          </div>
        </div>

        {/* Sales Pipeline */}
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm lg:col-span-2">
          <h3 className="text-base font-semibold text-gray-900 mb-4">
            {t('dashboard.salesPipeline')}
          </h3>
          <div className="flex gap-3">
            {['問い合わせ', '相談中', '提案', '交渉', '成約'].map((stage, i) => (
              <div
                key={stage}
                className="flex-1 bg-gray-50 rounded-lg p-4 text-center border border-gray-100"
              >
                <p className="text-xs text-gray-500 mb-1">{stage}</p>
                <p className="text-2xl font-bold text-gray-300">0</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
