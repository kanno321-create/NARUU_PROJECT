import { useTranslation } from 'react-i18next';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAppStore } from '@/lib/store';
import { cn } from '@/lib/utils';

const navItems = [
  { key: 'dashboard', icon: '📊', path: '/' },
  { key: 'customers', icon: '👥', path: '/customers' },
  { key: 'partners', icon: '🏢', path: '/partners' },
  { key: 'products', icon: '🎌', path: '/products' },
  { key: 'bookings', icon: '📅', path: '/bookings' },
  { key: 'sales', icon: '💰', path: '/sales' },
  { key: 'schedules', icon: '🗓️', path: '/schedules' },
  { key: 'venues', icon: '📍', path: '/venues' },
  { key: 'accounting', icon: '💳', path: '/accounting' },
  { key: 'marketing', icon: '📣', path: '/marketing' },
  { key: 'line', icon: '💬', path: '/line' },
  { key: 'settings', icon: '⚙️', path: '/settings' },
];

export default function Sidebar() {
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, sidebarCollapsed, toggleSidebar } = useAppStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleLang = () => {
    const newLang = i18n.language === 'ja' ? 'ko' : 'ja';
    i18n.changeLanguage(newLang);
    localStorage.setItem('naruu_lang', newLang);
  };

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-full bg-white border-r border-gray-200 flex flex-col transition-all duration-200',
        sidebarCollapsed ? 'w-16' : 'w-60',
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center justify-between">
          {!sidebarCollapsed && (
            <div>
              <h1 className="text-xl font-bold text-naruu-700">{t('app.name')}</h1>
              <p className="text-[10px] text-gray-400 mt-0.5">{t('app.tagline')}</p>
            </div>
          )}
          <button
            onClick={toggleSidebar}
            className="p-1.5 rounded hover:bg-gray-100 text-gray-400 text-xs"
          >
            {sidebarCollapsed ? '▶' : '◀'}
          </button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-2 px-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path ||
            (item.path !== '/' && location.pathname.startsWith(item.path));

          return (
            <button
              key={item.key}
              onClick={() => navigate(item.path)}
              className={cn(
                'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors mb-0.5',
                isActive
                  ? 'bg-naruu-50 text-naruu-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
              )}
            >
              <span className="text-base">{item.icon}</span>
              {!sidebarCollapsed && <span>{t(`nav.${item.key}`)}</span>}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-gray-100 space-y-2">
        {/* Language toggle */}
        <button
          onClick={toggleLang}
          className="w-full flex items-center gap-2 px-3 py-1.5 rounded text-xs text-gray-500 hover:bg-gray-50"
        >
          <span>🌐</span>
          {!sidebarCollapsed && (
            <span>{i18n.language === 'ja' ? '日本語 → 한국어' : '한국어 → 日本語'}</span>
          )}
        </button>

        {/* User info + logout */}
        {user && (
          <div className="flex items-center justify-between">
            {!sidebarCollapsed && (
              <div className="text-xs">
                <p className="font-medium text-gray-700">{user.name}</p>
                <p className="text-gray-400">{user.role}</p>
              </div>
            )}
            <button
              onClick={handleLogout}
              className="p-1.5 rounded hover:bg-red-50 text-red-400 text-xs"
              title={t('common.logout')}
            >
              🚪
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
