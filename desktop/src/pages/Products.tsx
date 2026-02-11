import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '@/lib/api';
import { formatJPY, formatKRW } from '@/lib/utils';
import type { Product, ListResponse } from '@/types';

export default function Products() {
  const { t } = useTranslation();
  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: '20' });
      if (search) params.set('search', search);
      const data = await api.get<ListResponse<Product>>(`/v1/products?${params}`);
      setProducts(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to fetch products:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [page]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchProducts();
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">{t('products.title')}</h2>
        <button className="px-4 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 text-sm font-medium transition-colors">
          + {t('products.add')}
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

      {/* Card grid view for products */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">{t('common.loading')}</div>
      ) : products.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-5xl mb-3">🎌</p>
          <p className="text-gray-400">{t('common.noData')}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {products.map((p) => (
            <div
              key={p.id}
              className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow overflow-hidden"
            >
              <div className="p-5">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <span className="text-[10px] font-mono text-gray-400">{p.code}</span>
                    <h3 className="font-semibold text-gray-900 mt-0.5">{p.name_ja}</h3>
                    {p.name_kr && (
                      <p className="text-xs text-gray-500">{p.name_kr}</p>
                    )}
                  </div>
                  <span className="px-2 py-0.5 rounded bg-naruu-50 text-naruu-700 text-[10px] font-medium">
                    {t(`products.types.${p.product_type}` as any)}
                  </span>
                </div>

                {p.description_ja && (
                  <p className="text-xs text-gray-500 mb-3 line-clamp-2">{p.description_ja}</p>
                )}

                <div className="flex items-center gap-4 text-xs text-gray-600 mb-3">
                  <span>📅 {p.duration_days}日{p.duration_nights > 0 ? `${p.duration_nights}泊` : ''}</span>
                  <span>👥 {p.min_participants}~{p.max_participants}名</span>
                </div>

                <div className="flex items-center gap-3 text-sm">
                  {p.base_price_jpy && (
                    <span className="font-semibold text-gray-900">
                      {formatJPY(p.base_price_jpy)}
                    </span>
                  )}
                  {p.base_price_krw && (
                    <span className="text-gray-400 text-xs">
                      ({formatKRW(p.base_price_krw)})
                    </span>
                  )}
                </div>

                {p.itinerary && p.itinerary.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <p className="text-[10px] text-gray-400 mb-1">{t('products.itinerary')}</p>
                    <div className="space-y-1">
                      {p.itinerary.slice(0, 3).map((item, i) => (
                        <p key={i} className="text-xs text-gray-600">
                          Day{item.day}: {item.title}
                        </p>
                      ))}
                      {p.itinerary.length > 3 && (
                        <p className="text-xs text-gray-400">+{p.itinerary.length - 3} more...</p>
                      )}
                    </div>
                  </div>
                )}
              </div>

              <div className="px-5 py-3 bg-gray-50 border-t border-gray-100 flex justify-end">
                <button className="text-naruu-600 hover:text-naruu-800 text-xs font-medium">
                  {t('common.edit')}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
