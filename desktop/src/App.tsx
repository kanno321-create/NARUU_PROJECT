import { Routes, Route, Navigate } from 'react-router-dom';
import { useAppStore } from '@/lib/store';
import Layout from '@/components/Layout';
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import Customers from '@/pages/Customers';
import Partners from '@/pages/Partners';
import Products from '@/pages/Products';
import Bookings from '@/pages/Bookings';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAppStore();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/customers" element={<Customers />} />
        <Route path="/partners" element={<Partners />} />
        <Route path="/products" element={<Products />} />
        <Route path="/bookings" element={<Bookings />} />
        <Route path="/sales" element={<div className="text-gray-500">営業管理 - Coming Soon</div>} />
        <Route path="/schedules" element={<div className="text-gray-500">スケジュール - Coming Soon</div>} />
        <Route path="/venues" element={<div className="text-gray-500">場所DB - Coming Soon</div>} />
        <Route path="/accounting" element={<div className="text-gray-500">会計 - Coming Soon</div>} />
        <Route path="/marketing" element={<div className="text-gray-500">マーケティング - Coming Soon</div>} />
        <Route path="/line" element={<div className="text-gray-500">LINE - Coming Soon</div>} />
        <Route path="/settings" element={<div className="text-gray-500">設定 - Coming Soon</div>} />
      </Route>
    </Routes>
  );
}
