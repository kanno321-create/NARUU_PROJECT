import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useAppStore } from '@/lib/store';

export default function Layout() {
  const { sidebarCollapsed } = useAppStore();

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <main className={`transition-all duration-200 ${sidebarCollapsed ? 'ml-16' : 'ml-60'} p-6`}>
        <Outlet />
      </main>
    </div>
  );
}
