import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '@/lib/api';
import { formatJPY, formatDate } from '@/lib/utils';
import type { Booking, ListResponse } from '@/types';

const STATUS_STYLES: Record<string, string> = {
  inquiry: 'bg-blue-100 text-blue-700',
  confirmed: 'bg-green-100 text-green-700',
  in_progress: 'bg-amber-100 text-amber-700',
  completed: 'bg-gray-100 text-gray-700',
  cancelled: 'bg-red-100 text-red-700',
  no_show: 'bg-red-50 text-red-500',
};

const PAYMENT_STYLES: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700',
  partial: 'bg-orange-100 text-orange-700',
  paid: 'bg-green-100 text-green-700',
  refunded: 'bg-gray-100 text-gray-600',
};

export default function Bookings() {
  const { t } = useTranslation();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchBookings = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: '20' });
      if (statusFilter) params.set('status', statusFilter);
      const data = await api.get<ListResponse<Booking>>(`/v1/bookings?${params}`);
      setBookings(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to fetch bookings:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookings();
  }, [page, statusFilter]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">{t('bookings.title')}</h2>
        <button className="px-4 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 text-sm font-medium transition-colors">
          + {t('bookings.add')}
        </button>
      </div>

      {/* Status filter tabs */}
      <div className="flex gap-2 mb-4">
        {['', 'inquiry', 'confirmed', 'in_progress', 'completed', 'cancelled'].map((s) => (
          <button
            key={s}
            onClick={() => { setStatusFilter(s); setPage(1); }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              statusFilter === s
                ? 'bg-naruu-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {s === '' ? '全件' : t(`bookings.statuses.${s}` as any)}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('bookings.bookingNo')}</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('bookings.tourDate')}</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">人数</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">金額</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('bookings.status')}</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('bookings.payment')}</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('common.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center text-gray-400">
                  {t('common.loading')}
                </td>
              </tr>
            ) : bookings.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center text-gray-400">
                  {t('common.noData')}
                </td>
              </tr>
            ) : (
              bookings.map((b) => (
                <tr key={b.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs font-medium text-gray-900">{b.booking_no}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {b.tour_date ? formatDate(b.tour_date) : '-'}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    大人{b.num_adults}{b.num_children > 0 ? ` 子供${b.num_children}` : ''}
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {b.total_price_jpy ? formatJPY(b.total_price_jpy) : '-'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_STYLES[b.status] || ''}`}>
                      {t(`bookings.statuses.${b.status}` as any)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${PAYMENT_STYLES[b.payment_status] || ''}`}>
                      {b.payment_status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button className="text-naruu-600 hover:text-naruu-800 text-xs font-medium">
                      {t('common.edit')}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {total > 20 && (
          <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between text-xs text-gray-500">
            <span>{t('common.total')}: {total}</span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="px-3 py-1 border rounded disabled:opacity-30"
              >
                ←
              </button>
              <span className="px-3 py-1">{page}</span>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page * 20 >= total}
                className="px-3 py-1 border rounded disabled:opacity-30"
              >
                →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
