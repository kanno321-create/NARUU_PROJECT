'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { ERPCustomer, api } from '@/lib/api';
import { useWindowContextOptional } from '../../ERPContext';
import { useERPData } from "@/contexts/ERPDataContext";

// 거래처 데이터 인터페이스 - 이지판매재고관리 필드 100% 복제
interface Customer {
  id: string;
  code: string;
  name: string;
  customerType: string; // 거래처구분: 매출처, 매입처, 매입매출처
  useYn: string; // 사용여부: 사용, 미사용
  // 연락처 탭
  tel: string;
  mobile: string;
  fax: string;
  homepage: string;
  email: string;
  zipCode: string;
  address1: string;
  address2: string;
  // 업체정보 탭
  businessName: string; // 사업장명
  ceoName: string; // 성명(대표)
  businessNumber: string; // 사업자번호
  businessType: string; // 업태
  businessItem: string; // 종목
  // 사업자정보입력 탭
  manager: string; // 담당자
  bankAccount: string; // 거래처계좌
  bankName: string; // 은행명
  depositor: string; // 예금주
  creditLimit: number; // 신용한도액
  salesFee: number; // 판매수수료
  salesPriceType: string; // 매출시 단가
  purchasePriceType: string; // 매입시 단가
  // 메모 탭
  memo: string;
}

interface CustomerWindowProps {
  onClose?: () => void;
}

// 컬럼 정의
interface ColumnDef {
  key: keyof Customer;
  label: string;
  width: number;
  minWidth: number;
}

// ERPCustomer → local Customer 변환
function mapApiToLocal(c: ERPCustomer): Customer {
  return {
    id: c.id,
    code: c.code,
    name: c.name,
    customerType: c.customer_type || '매출처',
    useYn: c.is_active ? '사용' : '미사용',
    tel: c.phone || '',
    mobile: '',
    fax: c.fax || '',
    homepage: '',
    email: c.email || '',
    zipCode: '',
    address1: c.address || '',
    address2: '',
    businessName: c.name,
    ceoName: c.ceo_name || '',
    businessNumber: c.business_number || '',
    businessType: '',
    businessItem: '',
    manager: c.contact_person || '',
    bankAccount: '',
    bankName: '',
    depositor: '',
    creditLimit: c.credit_limit || 0,
    salesFee: 0,
    salesPriceType: '최종단가',
    purchasePriceType: '최종단가',
    memo: c.memo || '',
  };
}

// 드롭다운 옵션들 - 이지판매재고관리 원본 복제
const CUSTOMER_TYPE_OPTIONS = ['매출처', '매입처', '매입매출처'];
const USE_OPTIONS = ['사용', '미사용'];
const PRICE_TYPE_OPTIONS = ['최종단가', '도매가', '소매가', '입고가'];

// 컬럼 정의 - 초기 폭 설정
const INITIAL_COLUMNS: ColumnDef[] = [
  { key: 'code', label: '코드', width: 60, minWidth: 40 },
  { key: 'name', label: '거래처명', width: 100, minWidth: 60 },
  { key: 'customerType', label: '거래처구분', width: 80, minWidth: 60 },
  { key: 'tel', label: '전화번호', width: 100, minWidth: 60 },
  { key: 'mobile', label: '핸드폰번호', width: 110, minWidth: 60 },
  { key: 'fax', label: '팩스번호', width: 100, minWidth: 60 },
  { key: 'email', label: 'E메일주소', width: 130, minWidth: 60 },
  { key: 'homepage', label: '홈페이지주소', width: 110, minWidth: 60 },
  { key: 'zipCode', label: '우편번호', width: 70, minWidth: 50 },
  { key: 'address1', label: '주소1', width: 200, minWidth: 80 },
  { key: 'businessName', label: '상호(사업장명)', width: 100, minWidth: 60 },
  { key: 'ceoName', label: '성명(대표자)', width: 80, minWidth: 60 },
  { key: 'businessNumber', label: '사업자등록번호', width: 110, minWidth: 80 },
  { key: 'businessType', label: '업태', width: 60, minWidth: 40 },
  { key: 'businessItem', label: '종목', width: 60, minWidth: 40 },
  { key: 'manager', label: '담당사원', width: 70, minWidth: 50 },
  { key: 'useYn', label: '사용여부', width: 60, minWidth: 50 },
];

// 기본 표시 컬럼 (핸드폰번호, 홈페이지, 상호, 사업자번호, 업태, 종목 제외)
const DEFAULT_VISIBLE_KEYS: string[] = INITIAL_COLUMNS
  .map(c => c.key)
  .filter(k => !['mobile', 'homepage', 'businessName', 'businessNumber', 'businessType', 'businessItem'].includes(k));

export function CustomerWindow({ onClose }: CustomerWindowProps) {
  const windowContext = useWindowContextOptional();
  const { customers, customersLoading, fetchCustomers: ctxFetchCustomers, addCustomer: ctxAddCustomer, updateCustomer: ctxUpdateCustomer, deleteCustomer: ctxDeleteCustomer } = useERPData();
  const [searchTerm, setSearchTerm] = useState('');
  const [items, setItems] = useState<Customer[]>([]);
  const [selectedItem, setSelectedItem] = useState<Customer | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editMode, setEditMode] = useState<'add' | 'edit'>('add');
  const [activeTab, setActiveTab] = useState(0);
  const [showPreview, setShowPreview] = useState(false);
  const [showColumnToggle, setShowColumnToggle] = useState(false);
  const [visibleColumns, setVisibleColumns] = useState<Set<string>>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('erp-columns-customer');
      if (saved) { try { return new Set(JSON.parse(saved) as string[]); } catch { /* fall through */ } }
    }
    return new Set(DEFAULT_VISIBLE_KEYS);
  });

  // 컬럼 리사이즈 상태
  const [columns, setColumns] = useState<ColumnDef[]>(INITIAL_COLUMNS);
  const [resizingCol, setResizingCol] = useState<number | null>(null);
  const resizeStartX = useRef<number>(0);
  const resizeStartWidth = useRef<number>(0);

  // DB에서 표시항목(컬럼) 설정 로드 (localStorage는 즉시 캐시, DB가 최종 권한)
  useEffect(() => {
    api.erp.settings.getPreferences().then(res => {
      const cols = res.column_preferences?.customer;
      if (Array.isArray(cols) && cols.length > 0) {
        setVisibleColumns(new Set(cols));
        localStorage.setItem('erp-columns-customer', JSON.stringify(cols));
      }
    }).catch(() => { /* DB 실패 시 localStorage/기본값 유지 */ });
  }, []);

  // 컨텍스트에서 거래처 데이터 로드
  const fetchCustomers = useCallback(async () => {
    await ctxFetchCustomers();
  }, [ctxFetchCustomers]);

  useEffect(() => {
    fetchCustomers();
  }, [fetchCustomers]);

  // 컨텍스트 customers → 로컬 items 동기화
  useEffect(() => {
    if (customers.length > 0) {
      setItems(customers.map(c => mapApiToLocal(c as unknown as ERPCustomer)));
    }
  }, [customers]);

  // 모달 폼 상태 - 이지판매재고관리 필드 100% 복제
  const [formData, setFormData] = useState<Omit<Customer, 'id'>>({
    code: '',
    name: '',
    customerType: '매출처',
    useYn: '사용',
    tel: '',
    mobile: '',
    fax: '',
    homepage: '',
    email: '',
    zipCode: '',
    address1: '',
    address2: '',
    businessName: '',
    ceoName: '',
    businessNumber: '',
    businessType: '',
    businessItem: '',
    manager: '',
    bankAccount: '',
    bankName: '',
    depositor: '',
    creditLimit: 0,
    salesFee: 0,
    salesPriceType: '최종단가',
    purchasePriceType: '최종단가',
    memo: ''
  });

  const tabs = ['기본정보입력', '연락처', '업체정보', '사업자정보입력', '메모'];

  const filteredItems = items.filter(item =>
    item.name.includes(searchTerm) || item.code.includes(searchTerm)
  );

  // 컬럼 리사이즈 핸들러
  const handleResizeStart = useCallback((e: React.MouseEvent, colIndex: number) => {
    e.preventDefault();
    e.stopPropagation();
    setResizingCol(colIndex);
    resizeStartX.current = e.clientX;
    resizeStartWidth.current = columns[colIndex].width;

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const diff = moveEvent.clientX - resizeStartX.current;
      const newWidth = Math.max(columns[colIndex].minWidth, resizeStartWidth.current + diff);
      setColumns(prev => prev.map((col, idx) =>
        idx === colIndex ? { ...col, width: newWidth } : col
      ));
    };

    const handleMouseUp = () => {
      setResizingCol(null);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [columns]);

  const handleSearch = () => {
    ctxFetchCustomers();
  };

  const handleShowAll = () => {
    setSearchTerm('');
  };

  const handleAdd = () => {
    setEditMode('add');
    setActiveTab(0);
    setFormData({
      code: `m${String(items.length + 1).padStart(3, '0')}`,
      name: '',
      customerType: '매출처',
      useYn: '사용',
      tel: '',
      mobile: '',
      fax: '',
      homepage: '',
      email: '',
      zipCode: '',
      address1: '',
      address2: '',
      businessName: '',
      ceoName: '',
      businessNumber: '',
      businessType: '',
      businessItem: '',
      manager: '',
      bankAccount: '',
      bankName: '',
      depositor: '',
      creditLimit: 0,
      salesFee: 0,
      salesPriceType: '최종단가',
      purchasePriceType: '최종단가',
      memo: ''
    });
    setShowModal(true);
  };

  const handleEdit = () => {
    if (!selectedItem) return;
    setEditMode('edit');
    setActiveTab(0);
    setFormData({
      code: selectedItem.code,
      name: selectedItem.name,
      customerType: selectedItem.customerType,
      useYn: selectedItem.useYn,
      tel: selectedItem.tel,
      mobile: selectedItem.mobile,
      fax: selectedItem.fax,
      homepage: selectedItem.homepage,
      email: selectedItem.email,
      zipCode: selectedItem.zipCode,
      address1: selectedItem.address1,
      address2: selectedItem.address2,
      businessName: selectedItem.businessName,
      ceoName: selectedItem.ceoName,
      businessNumber: selectedItem.businessNumber,
      businessType: selectedItem.businessType,
      businessItem: selectedItem.businessItem,
      manager: selectedItem.manager,
      bankAccount: selectedItem.bankAccount,
      bankName: selectedItem.bankName,
      depositor: selectedItem.depositor,
      creditLimit: selectedItem.creditLimit,
      salesFee: selectedItem.salesFee,
      salesPriceType: selectedItem.salesPriceType,
      purchasePriceType: selectedItem.purchasePriceType,
      memo: selectedItem.memo
    });
    setShowModal(true);
  };

  const handleDelete = async () => {
    if (!selectedItem) return;
    if (!confirm('선택한 거래처를 삭제하시겠습니까?')) return;
    const success = await ctxDeleteCustomer(selectedItem.id);
    if (success) {
      setSelectedItem(null);
    } else {
      alert('거래처 삭제에 실패했습니다.');
    }
  };

  const handleRefresh = () => {
    ctxFetchCustomers();
    setSelectedItem(null);
    setSearchTerm('');
  };

  const handleSave = async () => {
    const ctxPayload = {
      code: formData.code,
      name: formData.name,
      customer_type: formData.customerType as any,
      is_active: formData.useYn === '사용',
      phone: formData.tel || undefined,
      fax: formData.fax || undefined,
      email: formData.email || undefined,
      address: formData.address1 || undefined,
      ceo_name: formData.ceoName || undefined,
      business_number: formData.businessNumber || undefined,
      contact_person: formData.manager || undefined,
      credit_limit: String(formData.creditLimit),
      memo: formData.memo || undefined,
    };
    try {
      if (editMode === 'add') {
        const result = await ctxAddCustomer(ctxPayload as any);
        if (!result) throw new Error('등록 실패');
      } else if (selectedItem) {
        const result = await ctxUpdateCustomer(selectedItem.id, ctxPayload as any);
        if (!result) throw new Error('수정 실패');
      }
      setShowModal(false);
    } catch {
      alert('거래처 저장에 실패했습니다.');
    }
  };

  const handleSaveAndAdd = async () => {
    await handleSave();
    handleAdd();
  };

  const handleCancel = () => {
    setShowModal(false);
  };

  const handleCloseWindow = () => {
    windowContext?.closeThisWindow();
    onClose?.();
  };

  const handleExcelImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      if (!file.name.endsWith('.csv')) {
        alert('CSV 파일만 지원됩니다. (.csv)\n엑셀 파일은 CSV로 저장 후 업로드하세요.');
        return;
      }

      try {
        const text = await file.text();
        const lines = text.split('\n').map(line => line.trim()).filter(line => line.length > 0);
        if (lines.length < 2) {
          alert('데이터가 없습니다. 헤더 행 + 1개 이상의 데이터 행이 필요합니다.');
          return;
        }

        const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
        const dataLines = lines.slice(1);

        // 필수 컬럼 확인: 코드, 거래처명(업체명)
        const codeIdx = headers.findIndex(h => h === '코드' || h === 'code');
        const nameIdx = headers.findIndex(h => h === '거래처명' || h === '업체명' || h === 'name');
        if (codeIdx === -1 || nameIdx === -1) {
          alert('필수 컬럼이 없습니다.\n필수: "코드", "거래처명"(또는 "업체명")\n선택: "전화번호", "팩스번호", "이메일", "주소", "대표자", "사업자번호", "메모"');
          return;
        }

        // 선택 컬럼 인덱스
        const telIdx = headers.findIndex(h => h === '전화번호' || h === 'tel' || h === 'phone');
        const faxIdx = headers.findIndex(h => h === '팩스번호' || h === 'fax');
        const emailIdx = headers.findIndex(h => h === '이메일' || h === 'email');
        const addressIdx = headers.findIndex(h => h === '주소' || h === 'address');
        const ceoIdx = headers.findIndex(h => h === '대표자' || h === 'ceo' || h === '성명');
        const bnIdx = headers.findIndex(h => h === '사업자번호' || h === 'business_number');
        const memoIdx = headers.findIndex(h => h === '메모' || h === 'memo');

        const getVal = (cols: string[], idx: number) => idx >= 0 && idx < cols.length ? cols[idx].replace(/^"|"$/g, '').trim() : '';

        let successCount = 0;
        let failCount = 0;

        for (let i = 0; i < dataLines.length; i++) {
          const cols = dataLines[i].split(',').map(c => c.trim());
          const code = getVal(cols, codeIdx);
          const name = getVal(cols, nameIdx);
          if (!code || !name) { failCount++; continue; }

          try {
            const result = await ctxAddCustomer({
              code,
              name,
              customer_type: '매출처' as any,
              is_active: true,
              phone: getVal(cols, telIdx) || undefined,
              fax: getVal(cols, faxIdx) || undefined,
              email: getVal(cols, emailIdx) || undefined,
              address: getVal(cols, addressIdx) || undefined,
              ceo_name: getVal(cols, ceoIdx) || undefined,
              business_number: getVal(cols, bnIdx) || undefined,
              memo: getVal(cols, memoIdx) || undefined,
            } as any);
            if (result) { successCount++; } else { failCount++; }
          } catch {
            failCount++;
          }
        }

        alert(`CSV 가져오기 완료\n성공: ${successCount}건 / 실패: ${failCount}건 (전체 ${dataLines.length}건)`);
        ctxFetchCustomers();
      } catch (err) {
        alert(`파일 읽기 오류: ${err}`);
      }
    };
    input.click();
  };

  const [showPostcode, setShowPostcode] = useState(false);
  const [postcodeReady, setPostcodeReady] = useState(false);
  const postcodeContainerRef = useRef<HTMLDivElement>(null);

  // showPostcode + postcodeReady 둘 다 true일 때 embed 실행
  useEffect(() => {
    if (!showPostcode || !postcodeReady) return;
    const container = postcodeContainerRef.current;
    if (!container || !window.daum?.Postcode) return;
    container.innerHTML = '';
    new window.daum.Postcode({
      oncomplete: (data: DaumPostcodeResult) => {
        const fullAddress = data.roadAddress || data.jibunAddress;
        const extraAddress = data.buildingName ? ` (${data.buildingName})` : '';
        setFormData(prev => ({
          ...prev,
          zipCode: data.zonecode,
          address1: fullAddress + extraAddress,
        }));
        setShowPostcode(false);
        setPostcodeReady(false);
      },
      onclose: () => {
        setShowPostcode(false);
        setPostcodeReady(false);
      },
      width: '100%',
      height: '100%',
    }).embed(container);
  }, [showPostcode, postcodeReady]);

  const handleAddressSearch = () => {
    // 이미 로드된 경우 바로 열기
    if (window.daum?.Postcode) {
      setShowPostcode(true);
      setPostcodeReady(true);
      return;
    }

    // 다음 우편번호 API 동적 로드
    setShowPostcode(true); // 오버레이 먼저 표시
    const script = document.createElement('script');
    script.src = 'https://t1.daumcdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js';

    // 10초 타임아웃
    const timeout = setTimeout(() => {
      setShowPostcode(false);
      const manualAddress = prompt('주소 검색 서비스 연결 시간이 초과되었습니다.\n주소를 직접 입력해주세요:');
      if (manualAddress) {
        setFormData(prev => ({ ...prev, address1: manualAddress }));
      }
    }, 10000);

    script.onload = () => {
      clearTimeout(timeout);
      setPostcodeReady(true);
    };
    script.onerror = () => {
      clearTimeout(timeout);
      setShowPostcode(false);
      const manualAddress = prompt('주소 검색 서비스에 연결할 수 없습니다.\n주소를 직접 입력해주세요:');
      if (manualAddress) {
        setFormData(prev => ({ ...prev, address1: manualAddress }));
      }
    };
    document.body.appendChild(script);
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* 상단 툴바 - 이지판매재고관리 레이아웃 복제 */}
      <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-b from-gray-100 to-gray-200 border-b">
        <button
          onClick={handleAdd}
          className="flex items-center gap-1 px-3 py-1.5 bg-white border border-gray-300 rounded text-sm hover:bg-gray-50"
        >
          <span className="w-5 h-5 flex items-center justify-center rounded-full bg-green-500 text-white text-xs">+</span>
          추가
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-1 px-3 py-1.5 bg-white border border-gray-300 rounded text-sm hover:bg-gray-50"
          disabled={!selectedItem}
        >
          <span className="w-5 h-5 flex items-center justify-center rounded-full bg-blue-500 text-white text-xs">✓</span>
          수정
        </button>
        <button
          onClick={handleDelete}
          className="flex items-center gap-1 px-3 py-1.5 bg-white border border-gray-300 rounded text-sm hover:bg-gray-50"
          disabled={!selectedItem}
        >
          <span className="w-5 h-5 flex items-center justify-center rounded-full bg-red-500 text-white text-xs">×</span>
          삭제
        </button>
        <button
          onClick={() => { if (selectedItem) setShowPreview(true); }}
          className="flex items-center gap-1 px-3 py-1.5 bg-white border border-gray-300 rounded text-sm hover:bg-gray-50"
          disabled={!selectedItem}
        >
          <span className="w-5 h-5 flex items-center justify-center text-gray-600">A</span>
          미리보기
        </button>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-1 px-3 py-1.5 bg-white border border-gray-300 rounded text-sm hover:bg-gray-50"
        >
          <span className="w-5 h-5 flex items-center justify-center text-gray-500">↻</span>
          새로고침
        </button>
        <div className="relative">
          <button
            onClick={() => setShowColumnToggle(!showColumnToggle)}
            className="flex items-center gap-1 px-3 py-1.5 bg-white border border-gray-300 rounded text-sm hover:bg-gray-50"
          >
            표시항목 ▼
          </button>
          {showColumnToggle && (
            <div className="absolute top-full left-0 mt-1 bg-white border border-gray-300 rounded shadow-lg z-50 p-2 w-48 max-h-64 overflow-y-auto">
              {INITIAL_COLUMNS.map(col => (
                <label key={col.key} className="flex items-center gap-2 px-2 py-1 text-xs hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={visibleColumns.has(col.key)}
                    onChange={(e) => {
                      const next = new Set(visibleColumns);
                      if (e.target.checked) next.add(col.key); else next.delete(col.key);
                      setVisibleColumns(next);
                      const arr = [...next];
                      localStorage.setItem('erp-columns-customer', JSON.stringify(arr));
                      api.erp.settings.updatePreferences({ customer: arr }).catch(() => {});
                    }}
                  />
                  {col.label}
                </label>
              ))}
            </div>
          )}
        </div>
        <button
          onClick={handleExcelImport}
          className="flex items-center gap-1 px-3 py-1.5 bg-white border border-gray-300 rounded text-sm hover:bg-gray-50"
        >
          엑셀입력
        </button>
      </div>

      {/* 검색 영역 */}
      <div className="flex items-center gap-3 px-4 py-2 bg-gray-100 border-b">
        <label className="text-sm font-medium text-gray-700">거래처명:</label>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-48 px-3 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleSearch}
          className="px-4 py-1.5 bg-gray-100 border border-gray-300 rounded text-sm hover:bg-gray-200"
        >
          검 색(F)
        </button>
        <button
          onClick={handleShowAll}
          className="px-4 py-1.5 bg-gray-100 border border-gray-300 rounded text-sm hover:bg-gray-200"
        >
          전체보기
        </button>
      </div>

      {/* 데이터 그리드 - 리사이즈 가능한 컬럼 */}
      <div className="flex-1 overflow-auto">
        {(() => { const displayColumns = columns.filter(c => visibleColumns.has(c.key)); return (
        <table className="border-collapse text-xs" style={{ tableLayout: 'fixed', width: displayColumns.reduce((sum, col) => sum + col.width, 0) }}>
          <thead className="bg-blue-100 sticky top-0">
            <tr>
              {displayColumns.map((col, idx) => (
                <th
                  key={col.key}
                  className="border border-gray-300 px-2 py-1.5 text-left font-medium text-gray-700 relative select-none"
                  style={{ width: col.width, minWidth: col.minWidth }}
                >
                  <div className="overflow-hidden whitespace-nowrap text-ellipsis" title={col.label}>
                    {col.label}
                  </div>
                  {/* 리사이즈 핸들 */}
                  <div
                    className="absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-blue-400 active:bg-blue-500"
                    onMouseDown={(e) => handleResizeStart(e, idx)}
                    style={{
                      backgroundColor: resizingCol === idx ? '#3b82f6' : 'transparent',
                    }}
                  />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredItems.map((item, index) => (
              <tr
                key={item.id}
                className={`${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'} hover:bg-blue-50 cursor-pointer ${selectedItem?.id === item.id ? 'bg-blue-100' : ''}`}
                onClick={() => setSelectedItem(item)}
                onDoubleClick={handleEdit}
              >
                {displayColumns.map((col) => (
                  <td
                    key={col.key}
                    className="border border-gray-300 px-2 py-1 overflow-hidden whitespace-nowrap text-ellipsis"
                    style={{ width: col.width, maxWidth: col.width }}
                    title={String(item[col.key] || '')}
                  >
                    {String(item[col.key] || '')}
                  </td>
                ))}
              </tr>
            ))}
            {/* 빈 행들 추가 - 이지판매재고관리 스타일 */}
            {Array.from({ length: Math.max(0, 15 - filteredItems.length) }).map((_, index) => (
              <tr key={`empty-${index}`} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                {displayColumns.map((col, colIndex) => (
                  <td
                    key={colIndex}
                    className="border border-gray-300 px-2 py-1"
                    style={{ width: col.width }}
                  >
                    &nbsp;
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        ); })()}
      </div>

      {/* 하단 상태바 */}
      <div className="px-4 py-1 bg-gray-100 border-t text-xs text-gray-600 flex justify-end">
        <span>전체 {items.length} 항목</span>
        <span className="ml-4">{filteredItems.length} 항목표시</span>
      </div>

      {/* 모달 다이얼로그 - 이지판매재고관리 5탭 구조 100% 복제 */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-200 rounded shadow-lg w-[480px]">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between px-3 py-2 bg-gray-300 rounded-t">
              <span className="text-sm font-medium">거래처정보등록</span>
              <button onClick={handleCancel} className="text-gray-600 hover:text-gray-800 text-lg">×</button>
            </div>

            {/* 탭 헤더 */}
            <div className="flex border-b border-gray-300 bg-gray-200">
              {tabs.map((tab, index) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(index)}
                  className={`px-4 py-2 text-sm border-r border-gray-300 ${
                    activeTab === index
                      ? 'bg-white border-t-2 border-t-blue-500'
                      : 'bg-gray-100 hover:bg-gray-50'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* 모달 바디 - 탭별 내용 (고정 높이) */}
            <div className="p-4 bg-gray-100 h-[320px] overflow-y-auto">
              {/* 기본정보입력 탭 */}
              {activeTab === 0 && (
                <div>
                  <div className="text-sm font-medium text-blue-600 mb-3">기본정보</div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-sm text-right">코드:</label>
                      <input
                        type="text"
                        value={formData.code}
                        onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                        className="w-32 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-sm text-right">업체명:</label>
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-sm text-right">거래처구분:</label>
                      <select
                        value={formData.customerType}
                        onChange={(e) => setFormData({ ...formData, customerType: e.target.value })}
                        className="w-32 px-2 py-1 border border-gray-300 rounded text-sm"
                      >
                        {CUSTOMER_TYPE_OPTIONS.map(opt => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-sm text-right">사용:</label>
                      <select
                        value={formData.useYn}
                        onChange={(e) => setFormData({ ...formData, useYn: e.target.value })}
                        className="w-32 px-2 py-1 border border-gray-300 rounded text-sm"
                      >
                        {USE_OPTIONS.map(opt => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* 연락처 탭 */}
              {activeTab === 1 && (
                <div>
                  <div className="text-sm font-medium text-blue-600 mb-3">연락처</div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-sm text-right">전화번호:</label>
                      <input
                        type="text"
                        value={formData.tel}
                        onChange={(e) => setFormData({ ...formData, tel: e.target.value })}
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-sm text-right">휴대전화:</label>
                      <input
                        type="text"
                        value={formData.mobile}
                        onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-sm text-right">팩스번호:</label>
                      <input
                        type="text"
                        value={formData.fax}
                        onChange={(e) => setFormData({ ...formData, fax: e.target.value })}
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-sm text-right">홈페이지:</label>
                      <input
                        type="text"
                        value={formData.homepage}
                        onChange={(e) => setFormData({ ...formData, homepage: e.target.value })}
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-sm text-right">이메일:</label>
                      <input
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-sm text-right">주소:</label>
                      <input
                        type="text"
                        value={formData.zipCode}
                        onChange={(e) => setFormData({ ...formData, zipCode: e.target.value })}
                        className="w-24 px-2 py-1 border border-gray-300 rounded text-sm"
                        placeholder="우편번호"
                      />
                      <input
                        type="text"
                        value={formData.address1}
                        onChange={(e) => setFormData({ ...formData, address1: e.target.value })}
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                      <button
                        onClick={handleAddressSearch}
                        className="px-2 py-1 bg-gray-100 border border-gray-300 rounded text-sm"
                      >
                        ...
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* 업체정보 탭 */}
              {activeTab === 2 && (
                <div>
                  <div className="text-sm font-medium text-blue-600 mb-3">업체정보</div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <label className="w-24 text-sm text-right">사업장명:</label>
                      <input
                        type="text"
                        value={formData.businessName}
                        onChange={(e) => setFormData({ ...formData, businessName: e.target.value })}
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-24 text-sm text-right">성명(대표):</label>
                      <input
                        type="text"
                        value={formData.ceoName}
                        onChange={(e) => setFormData({ ...formData, ceoName: e.target.value })}
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-24 text-sm text-right">사업자번호:</label>
                      <input
                        type="text"
                        value={formData.businessNumber}
                        onChange={(e) => setFormData({ ...formData, businessNumber: e.target.value })}
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                        placeholder="000-00-00000"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-24 text-sm text-right">업태:</label>
                      <input
                        type="text"
                        value={formData.businessType}
                        onChange={(e) => setFormData({ ...formData, businessType: e.target.value })}
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-24 text-sm text-right">종목:</label>
                      <input
                        type="text"
                        value={formData.businessItem}
                        onChange={(e) => setFormData({ ...formData, businessItem: e.target.value })}
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* 사업자정보입력 탭 */}
              {activeTab === 3 && (
                <div>
                  <div className="text-sm font-medium text-blue-600 mb-3">기타정보</div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <label className="w-24 text-sm text-right">담당자:</label>
                      <select
                        value={formData.manager}
                        onChange={(e) => setFormData({ ...formData, manager: e.target.value })}
                        className="w-40 px-2 py-1 border border-gray-300 rounded text-sm"
                      >
                        <option value=""></option>
                        <option value="김이지">김이지</option>
                        <option value="이판매">이판매</option>
                        <option value="박재고">박재고</option>
                      </select>
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-24 text-sm text-right">거래처계좌:</label>
                      <input
                        type="text"
                        value={formData.bankAccount}
                        onChange={(e) => setFormData({ ...formData, bankAccount: e.target.value })}
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-24 text-sm text-right">은행명:</label>
                      <input
                        type="text"
                        value={formData.bankName}
                        onChange={(e) => setFormData({ ...formData, bankName: e.target.value })}
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-24 text-sm text-right">예금주:</label>
                      <input
                        type="text"
                        value={formData.depositor}
                        onChange={(e) => setFormData({ ...formData, depositor: e.target.value })}
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-24 text-sm text-right">신용한도액:</label>
                      <input
                        type="number"
                        value={formData.creditLimit}
                        onChange={(e) => setFormData({ ...formData, creditLimit: parseInt(e.target.value) || 0 })}
                        className="w-32 px-2 py-1 border border-gray-300 rounded text-sm text-right"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-24 text-sm text-right">판매수수료:</label>
                      <input
                        type="number"
                        value={formData.salesFee}
                        onChange={(e) => setFormData({ ...formData, salesFee: parseFloat(e.target.value) || 0 })}
                        className="w-24 px-2 py-1 border border-gray-300 rounded text-sm text-right"
                      />
                      <span className="text-sm">%</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-24 text-sm text-right">매출시 단가:</label>
                      <select
                        value={formData.salesPriceType}
                        onChange={(e) => setFormData({ ...formData, salesPriceType: e.target.value })}
                        className="w-32 px-2 py-1 border border-gray-300 rounded text-sm"
                      >
                        {PRICE_TYPE_OPTIONS.map(opt => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-24 text-sm text-right">매입시 단가:</label>
                      <select
                        value={formData.purchasePriceType}
                        onChange={(e) => setFormData({ ...formData, purchasePriceType: e.target.value })}
                        className="w-32 px-2 py-1 border border-gray-300 rounded text-sm"
                      >
                        {PRICE_TYPE_OPTIONS.map(opt => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* 메모 탭 */}
              {activeTab === 4 && (
                <div className="h-full">
                  <div className="text-sm font-medium text-blue-600 mb-3">메모</div>
                  <textarea
                    value={formData.memo}
                    onChange={(e) => setFormData({ ...formData, memo: e.target.value })}
                    className="w-full h-[230px] px-2 py-1 border border-gray-300 rounded text-sm resize-none"
                  />
                </div>
              )}
            </div>

            {/* 하단 안내문구 */}
            <div className="px-4 py-1 bg-gray-100 text-xs text-gray-500">
              새로운 거래처의 정보를 등록합니다.
            </div>

            {/* 모달 푸터 */}
            <div className="flex items-center justify-end px-4 py-3 bg-gray-100 rounded-b gap-2">
              <button
                onClick={handleSaveAndAdd}
                className="px-6 py-1.5 bg-gray-200 border border-gray-400 rounded text-sm hover:bg-gray-300"
              >
                저장후추가
              </button>
              <button
                onClick={handleSave}
                className="px-6 py-1.5 bg-gray-200 border border-gray-400 rounded text-sm hover:bg-gray-300"
              >
                저 장
              </button>
              <button
                onClick={handleCancel}
                className="px-6 py-1.5 bg-gray-200 border border-gray-400 rounded text-sm hover:bg-gray-300"
              >
                취 소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 미리보기 모달 */}
      {showPreview && selectedItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded shadow-lg w-[500px] max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between px-4 py-2 bg-gray-200 rounded-t">
              <span className="text-sm font-medium">거래처 미리보기</span>
              <button onClick={() => setShowPreview(false)} className="text-gray-600 hover:text-gray-800 text-lg">×</button>
            </div>
            <div className="p-4 text-sm space-y-2">
              <div className="flex"><span className="w-28 text-gray-500">코드:</span><span>{selectedItem.code}</span></div>
              <div className="flex"><span className="w-28 text-gray-500">거래처명:</span><span>{selectedItem.name}</span></div>
              <div className="flex"><span className="w-28 text-gray-500">거래처구분:</span><span>{selectedItem.customerType}</span></div>
              <div className="flex"><span className="w-28 text-gray-500">사용여부:</span><span>{selectedItem.useYn}</span></div>
              <div className="flex"><span className="w-28 text-gray-500">전화번호:</span><span>{selectedItem.tel}</span></div>
              <div className="flex"><span className="w-28 text-gray-500">이메일:</span><span>{selectedItem.email}</span></div>
              <div className="flex"><span className="w-28 text-gray-500">주소:</span><span>{selectedItem.address1}</span></div>
              <div className="flex"><span className="w-28 text-gray-500">대표자:</span><span>{selectedItem.ceoName}</span></div>
              <div className="flex"><span className="w-28 text-gray-500">사업자번호:</span><span>{selectedItem.businessNumber}</span></div>
              <div className="flex"><span className="w-28 text-gray-500">담당자:</span><span>{selectedItem.manager}</span></div>
              <div className="flex"><span className="w-28 text-gray-500">신용한도액:</span><span>{selectedItem.creditLimit.toLocaleString()}원</span></div>
              {selectedItem.memo && <div className="flex"><span className="w-28 text-gray-500">메모:</span><span>{selectedItem.memo}</span></div>}
            </div>
            <div className="flex justify-end px-4 py-3 bg-gray-100 rounded-b">
              <button onClick={() => setShowPreview(false)} className="px-4 py-1.5 bg-gray-200 border border-gray-400 rounded text-sm">닫기</button>
            </div>
          </div>
        </div>
      )}

      {/* 다음 우편번호 검색 오버레이 */}
      {showPostcode && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-lg shadow-xl w-[500px] h-[600px] flex flex-col">
            <div className="flex items-center justify-between px-4 py-2 border-b bg-gray-100 rounded-t-lg">
              <span className="text-sm font-semibold">주소 검색</span>
              <button
                onClick={() => setShowPostcode(false)}
                className="text-gray-500 hover:text-gray-800 text-lg font-bold px-2"
              >
                X
              </button>
            </div>
            <div ref={postcodeContainerRef} className="flex-1" />
          </div>
        </div>
      )}
    </div>
  );
}
