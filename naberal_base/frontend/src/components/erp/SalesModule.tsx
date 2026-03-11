'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  useERPStore,
  useSales,
  useCustomers,
  useTaxInvoices,
  useQuotations,
  useERPLoading,
  useERPError,
} from '@/lib/stores/useERPStore';

// 날짜 프리셋 계산 헬퍼
const getDatePreset = (preset: string): { startDate: string; endDate: string } => {
  const today = new Date();
  const endDate = today.toISOString().split('T')[0];
  let startDate = endDate;

  switch (preset) {
    case 'today':
      startDate = endDate;
      break;
    case 'week':
      const weekAgo = new Date(today);
      weekAgo.setDate(weekAgo.getDate() - 7);
      startDate = weekAgo.toISOString().split('T')[0];
      break;
    case 'month':
      const monthAgo = new Date(today);
      monthAgo.setMonth(monthAgo.getMonth() - 1);
      startDate = monthAgo.toISOString().split('T')[0];
      break;
    case 'quarter':
      const quarterAgo = new Date(today);
      quarterAgo.setMonth(quarterAgo.getMonth() - 3);
      startDate = quarterAgo.toISOString().split('T')[0];
      break;
    case 'year':
      const yearAgo = new Date(today);
      yearAgo.setFullYear(yearAgo.getFullYear() - 1);
      startDate = yearAgo.toISOString().split('T')[0];
      break;
    case 'thisMonth':
      const firstOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
      startDate = firstOfMonth.toISOString().split('T')[0];
      break;
    case 'thisYear':
      startDate = `${today.getFullYear()}-01-01`;
      break;
    default:
      startDate = '';
      break;
  }

  return { startDate, endDate: preset === 'all' ? '' : endDate };
};

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  pending: 'bg-yellow-100 text-yellow-700',
  confirmed: 'bg-blue-100 text-blue-700',
  shipped: 'bg-purple-100 text-purple-700',
  delivered: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
  completed: 'bg-green-100 text-green-700',
};

const STATUS_LABELS: Record<string, string> = {
  draft: '작성중',
  pending: '대기중',
  confirmed: '확정',
  shipped: '출고됨',
  delivered: '배송완료',
  cancelled: '취소',
  completed: '완료',
};

export default function SalesModule() {
  const salesData = useSales();
  const customers = useCustomers();
  const taxInvoicesData = useTaxInvoices();
  const quotationsData = useQuotations();
  const isLoading = useERPLoading();
  const error = useERPError();
  const {
    fetchSales,
    fetchCustomers,
    fetchTaxInvoices,
    fetchQuotations,
    clearError,
  } = useERPStore();

  const [filter, setFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // 날짜 필터 상태
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [datePreset, setDatePreset] = useState<string>('thisMonth');

  // 날짜 프리셋 적용
  const applyDatePreset = useCallback((preset: string) => {
    setDatePreset(preset);
    const { startDate: start, endDate: end } = getDatePreset(preset);
    setStartDate(start);
    setEndDate(end);
  }, []);

  // 초기 데이터 로드
  useEffect(() => {
    applyDatePreset('thisMonth');
  }, [applyDatePreset]);

  // 데이터 로드 (날짜 필터 적용)
  useEffect(() => {
    fetchSales({ start_date: startDate, end_date: endDate });
    fetchCustomers();
    fetchTaxInvoices({ start_date: startDate, end_date: endDate, invoice_type: 'sale' });
    fetchQuotations();
  }, [fetchSales, fetchCustomers, fetchTaxInvoices, fetchQuotations, startDate, endDate]);

  // 연결된 명세서 맵 생성
  const invoiceMap = useMemo(() => {
    const map = new Map<string, { invoiceNumber: string; amount: number }>();
    taxInvoicesData.forEach(inv => {
      if (inv.reference_type === 'sale' && inv.reference_id) {
        map.set(inv.reference_id, {
          invoiceNumber: inv.invoice_number || '-',
          amount: Number(inv.total_amount || 0),
        });
      }
    });
    return map;
  }, [taxInvoicesData]);

  // 연결된 견적서 맵 생성 (현재 DB 스키마에서는 직접 연결 필드 없음)
  const quotationMap = useMemo(() => {
    // 견적서 ID로 견적서 번호 조회용 맵
    const map = new Map<string, { quoteNumber: string }>();
    quotationsData.forEach(q => {
      map.set(q.id, {
        quoteNumber: q.quotation_number || '-',
      });
    });
    return map;
  }, [quotationsData]);

  // 고객명 조회 헬퍼
  const getCustomerName = (customerId: string) => {
    const customer = customers.find(c => c.id === customerId);
    return customer?.name || '알 수 없음';
  };

  // 매출 데이터 가공 (DB 필드명 → 컴포넌트 필드명)
  const sales = salesData.map(s => {
    const invoiceInfo = invoiceMap.get(s.id);
    const quotationInfo = quotationMap.get(s.id);
    return {
      id: s.id,
      orderNumber: s.sale_number || '-',
      customerId: s.customer_id || '',
      customerName: getCustomerName(s.customer_id || ''),
      totalAmount: Number(s.total_amount || 0),
      status: (s.status || 'draft') as string,
      orderDate: s.sale_date || '',
      dueDate: s.sale_date || '',  // sale_date를 기본값으로 사용
      notes: s.memo || '',
      invoiceInfo,
      quotationInfo,
    };
  });

  const filteredSales = sales.filter((sale) => {
    const matchesFilter = filter === 'all' || sale.status === filter;
    const matchesSearch = sale.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sale.orderNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sale.notes.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ko-KR', { style: 'currency', currency: 'KRW' }).format(amount);
  };

  // 요약 통계 계산
  const stats = {
    total: sales.length,
    confirmed: sales.filter(s => s.status === 'confirmed' || s.status === 'completed').length,
    pending: sales.filter(s => s.status === 'pending' || s.status === 'draft').length,
    shipped: sales.filter(s => s.status === 'shipped' || s.status === 'delivered').length,
    totalAmount: sales.filter(s => s.status !== 'cancelled').reduce((sum, s) => sum + s.totalAmount, 0),
  };

  // 로딩 상태
  if (isLoading && salesData.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand"></div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Error Banner */}
      {error && (
        <div className="px-4 py-2 bg-red-50 border-b border-red-200 flex items-center justify-between">
          <span className="text-sm text-red-700">{error}</span>
          <button onClick={clearError} className="text-red-500 hover:text-red-700">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Summary Cards */}
      <div className="p-4 grid grid-cols-5 gap-4 border-b border-gray-200">
        <div className="bg-blue-50 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-blue-600">{stats.total}</p>
          <p className="text-xs text-gray-600">총 매출건</p>
        </div>
        <div className="bg-yellow-50 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-yellow-600">{stats.pending}</p>
          <p className="text-xs text-gray-600">대기중</p>
        </div>
        <div className="bg-green-50 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-green-600">{stats.confirmed}</p>
          <p className="text-xs text-gray-600">확정</p>
        </div>
        <div className="bg-purple-50 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-purple-600">{stats.shipped}</p>
          <p className="text-xs text-gray-600">출고/배송</p>
        </div>
        <div className="bg-emerald-50 rounded-lg p-3 text-center">
          <p className="text-lg font-bold text-emerald-600">{formatCurrency(stats.totalAmount).replace('₩', '')}</p>
          <p className="text-xs text-gray-600">총 매출액</p>
        </div>
      </div>

      {/* Date Filter Bar - 이지판매재고관리 스타일 */}
      <div className="p-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-gray-700">기간:</span>
          <div className="flex gap-1">
            {[
              { key: 'today', label: '일간' },
              { key: 'week', label: '주간' },
              { key: 'month', label: '월간' },
              { key: 'quarter', label: '분기' },
              { key: 'year', label: '년간' },
              { key: 'thisMonth', label: '이번달' },
              { key: 'thisYear', label: '올해' },
              { key: 'all', label: '전체' },
            ].map(({ key, label }) => (
              <button
                key={key}
                onClick={() => applyDatePreset(key)}
                className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                  datePreset === key
                    ? 'bg-brand text-white'
                    : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-100'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2 ml-4">
            <input
              type="date"
              value={startDate}
              onChange={(e) => {
                setStartDate(e.target.value);
                setDatePreset('custom');
              }}
              className="px-2 py-1.5 text-xs border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand"
            />
            <span className="text-gray-500">~</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => {
                setEndDate(e.target.value);
                setDatePreset('custom');
              }}
              className="px-2 py-1.5 text-xs border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand"
            />
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="p-4 border-b border-gray-200 flex items-center gap-4">
        <input
          type="text"
          placeholder="검색 (고객명, 주문번호)"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand"
        />
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand"
        >
          <option value="all">전체 상태</option>
          <option value="draft">작성중</option>
          <option value="pending">대기중</option>
          <option value="confirmed">확정</option>
          <option value="shipped">출고됨</option>
          <option value="delivered">배송완료</option>
          <option value="completed">완료</option>
          <option value="cancelled">취소</option>
        </select>
        <button
          onClick={() => fetchSales({ start_date: startDate, end_date: endDate })}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          disabled={isLoading}
        >
          {isLoading ? '새로고침 중...' : '새로고침'}
        </button>
        <button className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-strong">
          + 새 매출
        </button>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {filteredSales.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-lg font-medium">매출 데이터가 없습니다</p>
            <p className="text-sm mt-1">새 매출을 등록하거나 견적에서 전환하세요</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">주문번호</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">고객</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">금액</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">상태</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">주문일</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">연결견적</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">연결명세서</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">작업</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredSales.map((sale) => (
                <tr key={sale.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-brand">{sale.orderNumber}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{sale.customerName}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right font-mono font-semibold">
                    {formatCurrency(sale.totalAmount)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-center">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${STATUS_COLORS[sale.status] || 'bg-gray-100 text-gray-700'}`}>
                      {STATUS_LABELS[sale.status] || sale.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 text-center">{sale.orderDate}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-center">
                    {sale.quotationInfo ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded-full">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        {sale.quotationInfo.quoteNumber}
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-center">
                    {sale.invoiceInfo ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-purple-50 text-purple-700 rounded-full">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        {sale.invoiceInfo.invoiceNumber}
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-center">
                    <div className="flex items-center justify-center gap-2">
                      <button className="p-1 text-gray-400 hover:text-brand" title="보기">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      </button>
                      <button className="p-1 text-gray-400 hover:text-green-600" title="명세서 발행">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </button>
                      <button className="p-1 text-gray-400 hover:text-blue-600" title="수정">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
        <span className="text-sm text-gray-500">총 {filteredSales.length}건</span>
        <div className="flex items-center gap-2">
          <button className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100">이전</button>
          <span className="px-3 py-1 text-sm bg-brand text-white rounded">1</span>
          <button className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100">다음</button>
        </div>
      </div>
    </div>
  );
}
