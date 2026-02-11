import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '@/lib/api';
import type { Partner, ListResponse } from '@/types';

const CATEGORY_ICONS: Record<string, string> = {
  medical: '🏥',
  beauty: '💄',
  restaurant: '🍜',
  shopping: '🛍️',
  experience: '🎨',
  tourism: '🗾',
  accommodation: '🏨',
  transport: '🚌',
};

export default function Partners() {
  const { t } = useTranslation();
  const [partners, setPartners] = useState<Partner[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchPartners = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: '20' });
      if (search) params.set('search', search);
      const data = await api.get<ListResponse<Partner>>(`/v1/partners?${params}`);
      setPartners(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to fetch partners:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPartners();
  }, [page]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchPartners();
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">{t('partners.title')}</h2>
        <button className="px-4 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 text-sm font-medium transition-colors">
          + {t('partners.add')}
        </button>
      </div>

      <form onSubmit={handleSearch} className="mb-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={t('common.search')}
          className="w-full max-w-md px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-naruu-500 focus:border-naruu-500 outline-none text-sm"
        />
      </form>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('partners.category')}</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('customers.nameJa')}</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('partners.contact')}</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('customers.phone')}</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('partners.commission')}</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('partners.services')}</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('common.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr>
                <td colSpan={8} className="px-4 py-12 text-center text-gray-400">
                  {t('common.loading')}
                </td>
              </tr>
            ) : partners.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-12 text-center text-gray-400">
                  {t('common.noData')}
                </td>
              </tr>
            ) : (
              partners.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{p.code}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1 text-xs">
                      {CATEGORY_ICONS[p.category] || '📌'}
                      {t(`partners.categories.${p.category}` as any)}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900">{p.name_ja}</td>
                  <td className="px-4 py-3 text-gray-600">{p.contact_person || '-'}</td>
                  <td className="px-4 py-3 text-gray-600">{p.phone || '-'}</td>
                  <td className="px-4 py-3 text-gray-600">{p.commission_rate}%</td>
                  <td className="px-4 py-3 text-gray-600 text-xs">{p.services?.length || 0}件</td>
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
      </div>
    </div>
  );
}
