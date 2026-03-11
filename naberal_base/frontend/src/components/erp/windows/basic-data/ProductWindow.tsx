"use client";

import React, { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import { useWindowContextOptional } from "../../ERPContext";
import { useERPData } from "@/contexts/ERPDataContext";

// ProductWithCatalog 타입 (기존 erp-api에서 가져오던 것을 인라인으로 정의)
interface ProductWithCatalog {
  id: string;
  code: string;
  name: string;
  spec: string | null;
  unit: string;
  purchase_price: number;
  selling_price: number;
  safety_stock: number;
  memo: string | null;
  is_active: boolean;
  is_catalog?: boolean;
  category_id?: string | null;
}

// 재고단위 옵션 (이지판매재고관리 스크린샷 기준)
const UNIT_OPTIONS = ["EA", "box", "set", "kg", "g", "L", "ml", "개", "묶음"];

// 적용비율 옵션 (이지판매재고관리 스크린샷 기준)
const PRICE_RATIO_OPTIONS = ["분류별비율", "직접입력", "정가기준", "매입가기준"];

// 현재상태 옵션
const STATUS_OPTIONS = ["일반상품", "판매중지", "품절", "단종"];

interface Product {
  id: string;
  code: string;            // 상품코드
  name: string;            // 상품명
  spec: string;            // 규격
  specDetail: string;      // 상세규격
  unit: string;            // 재고단위
  category: string;        // 상품분류
  theme: string;           // 테마분류
  // 상세정보
  purchasePrice: number;   // 입고가
  wholesalePrice: number;  // 도매가
  retailPrice: number;     // 소매가
  priceRatioType: string;  // 적용비율
  marginRate: number;      // 상품마진율
  optimalStock: number;    // 적정재고
  status: string;          // 현재상태
  // 메모
  memo: string;
}

// API 상품 → 로컬 Product 매핑
function mapApiToLocal(p: ProductWithCatalog): Product {
  return {
    id: p.id,
    code: p.code || '',
    name: p.name,
    spec: p.spec || '',
    specDetail: '',
    unit: p.unit || 'EA',
    category: '',
    theme: '',
    purchasePrice: Number(p.purchase_price) || 0,
    wholesalePrice: Number(p.selling_price) || 0,
    retailPrice: Number(p.selling_price) || 0,
    priceRatioType: '분류별비율',
    marginRate: 0,
    optimalStock: p.safety_stock || 0,
    status: p.is_active ? '일반상품' : '판매중지',
    memo: p.memo || '',
  };
}

const emptyProduct: Product = {
  id: "",
  code: "",
  name: "",
  spec: "",
  specDetail: "",
  unit: "EA",
  category: "",
  theme: "",
  purchasePrice: 0,
  wholesalePrice: 0,
  retailPrice: 0,
  priceRatioType: "분류별비율",
  marginRate: 0,
  optimalStock: 0,
  status: "일반상품",
  memo: "",
};

export function ProductWindow() {
  const windowContext = useWindowContextOptional();
  const { products: ctxProducts, productsLoading, fetchProducts: ctxFetchProducts, addProduct: ctxAddProduct, updateProduct: ctxUpdateProduct, deleteProduct: ctxDeleteProduct, searchProducts: ctxSearchProducts } = useERPData();
  const [products, setProducts] = useState<Product[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRow, setSelectedRow] = useState<number | null>(null);

  // API 검색 결과 (카탈로그 포함)
  const [apiProducts, setApiProducts] = useState<ProductWithCatalog[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchCounts, setSearchCounts] = useState({ erp: 0, catalog: 0 });

  // 모달 상태
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit">("add");
  const [editForm, setEditForm] = useState<Product>(emptyProduct);
  const [activeTab, setActiveTab] = useState(0);
  const [showPreview, setShowPreview] = useState(false);
  const [showColumnToggle, setShowColumnToggle] = useState(false);
  const allColumns = ['코드','품목명','규격','상세규격','재고단위','적정재고','입고가','도매가','소매가','상품분류','메모'];
  const [visibleColumns, setVisibleColumns] = useState<Set<string>>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('erp-columns-product');
      if (saved) { try { return new Set(JSON.parse(saved) as string[]); } catch { /* fall through */ } }
    }
    return new Set(allColumns);
  });

  // DB에서 표시항목(컬럼) 설정 로드 (localStorage는 즉시 캐시, DB가 최종 권한)
  useEffect(() => {
    api.erp.settings.getPreferences().then(res => {
      const cols = res.column_preferences?.product;
      if (Array.isArray(cols) && cols.length > 0) {
        setVisibleColumns(new Set(cols));
        localStorage.setItem('erp-columns-product', JSON.stringify(cols));
      }
    }).catch(() => { /* DB 실패 시 localStorage/기본값 유지 */ });
  }, []);

  // 분류 선택 모달
  const [showCategoryModal, setShowCategoryModal] = useState(false);

  const tabs = ["기본정보입력", "상세정보입력", "메모"];

  // 컨텍스트에서 상품 목록 로드
  const fetchProducts = useCallback(async () => {
    await ctxFetchProducts();
  }, [ctxFetchProducts]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  // 컨텍스트 products → 로컬 products 동기화
  useEffect(() => {
    if (ctxProducts.length > 0) {
      setProducts(ctxProducts.map(p => mapApiToLocal(p as unknown as ProductWithCatalog)));
    }
  }, [ctxProducts]);

  // 컨텍스트 기반 검색 함수 (디바운스 적용)
  const searchProductsLocal = useCallback(async (query: string) => {
    if (!query || query.length < 2) {
      setApiProducts([]);
      setSearchCounts({ erp: 0, catalog: 0 });
      return;
    }

    setIsSearching(true);
    try {
      const results = ctxSearchProducts(query);
      setApiProducts(results as unknown as ProductWithCatalog[]);
      setSearchCounts({ erp: results.length, catalog: 0 });
    } catch (error) {
      console.error("상품 검색 오류:", error);
      setApiProducts([]);
    } finally {
      setIsSearching(false);
    }
  }, [ctxSearchProducts]);

  // 검색어 변경 시 컨텍스트 검색 (디바운스)
  useEffect(() => {
    const timer = setTimeout(() => {
      searchProductsLocal(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, searchProductsLocal]);

  // 로컬 필터링 (API 결과가 없을 때)
  const filteredProducts = searchQuery && apiProducts.length > 0
    ? [] // API 결과가 있으면 로컬 필터링 안함
    : products.filter(
        (p) =>
          p.name.includes(searchQuery) ||
          p.code.includes(searchQuery) ||
          p.category.includes(searchQuery)
      );

  // 표시할 상품 목록 (API 결과 우선)
  const displayProducts = apiProducts.length > 0 ? apiProducts : filteredProducts;

  // 툴바 버튼 핸들러
  const handleAdd = () => {
    const nextCode = `s${String(products.length + 1).padStart(4, "0")}`;
    setEditForm({ ...emptyProduct, id: String(Date.now()), code: nextCode });
    setModalMode("add");
    setActiveTab(0);
    setShowModal(true);
  };

  const handleEdit = () => {
    if (selectedRow === null) {
      alert("수정할 상품을 선택하세요.");
      return;
    }
    const product = displayProducts[selectedRow];
    if ((product as ProductWithCatalog).is_catalog) {
      alert("카탈로그 상품은 수정할 수 없습니다.");
      return;
    }
    setEditForm({ ...product as Product });
    setModalMode("edit");
    setActiveTab(0);
    setShowModal(true);
  };

  const handleDelete = async () => {
    if (selectedRow === null) {
      alert("삭제할 상품을 선택하세요.");
      return;
    }
    const product = displayProducts[selectedRow];
    if ((product as ProductWithCatalog).is_catalog) {
      alert("카탈로그 상품은 삭제할 수 없습니다.");
      return;
    }
    if (!confirm("선택한 상품을 삭제하시겠습니까?")) return;
    const success = await ctxDeleteProduct(product.id);
    if (success) {
      setSelectedRow(null);
    } else {
      alert("상품 삭제에 실패했습니다.");
    }
  };

  const handleRefresh = () => {
    ctxFetchProducts();
    setSelectedRow(null);
    setSearchQuery("");
    setApiProducts([]);
    setSearchCounts({ erp: 0, catalog: 0 });
  };

  const handleSearch = () => {
    ctxFetchProducts();
  };

  const handleViewAll = () => {
    setSearchQuery("");
  };

  // 모달 저장
  const handleSave = async () => {
    if (!editForm.name) {
      alert("상품명을 입력하세요.");
      return;
    }
    if (!editForm.code) {
      alert("상품코드를 입력하세요.");
      return;
    }
    const ctxPayload = {
      code: editForm.code,
      name: editForm.name,
      specification: editForm.spec || undefined,
      unit: editForm.unit,
      purchase_price: editForm.purchasePrice,
      selling_price: editForm.retailPrice,
      min_stock: editForm.optimalStock,
      memo: editForm.memo || undefined,
      is_active: editForm.status !== '판매중지' && editForm.status !== '단종',
    };
    try {
      if (modalMode === "add") {
        const result = await ctxAddProduct(ctxPayload as any);
        if (!result) throw new Error('등록 실패');
      } else {
        const result = await ctxUpdateProduct(editForm.id, ctxPayload as any);
        if (!result) throw new Error('수정 실패');
      }
      setShowModal(false);
      setSelectedRow(null);
    } catch {
      alert("상품 저장에 실패했습니다.");
    }
  };

  const handleSaveAndAdd = async () => {
    if (!editForm.name || !editForm.code) {
      alert("필수 항목을 입력하세요.");
      return;
    }

    // API를 통해 저장
    try {
      const ctxPayload = {
        code: editForm.code,
        name: editForm.name,
        specification: editForm.spec || undefined,
        unit: editForm.unit,
        purchase_price: editForm.purchasePrice,
        selling_price: editForm.retailPrice,
        min_stock: editForm.optimalStock,
        memo: editForm.memo || undefined,
        is_active: editForm.status !== '판매중지' && editForm.status !== '단종',
      };

      if (modalMode === "add") {
        const result = await ctxAddProduct(ctxPayload as any);
        if (!result) throw new Error('등록 실패');
      } else {
        const result = await ctxUpdateProduct(editForm.id, ctxPayload as any);
        if (!result) throw new Error('수정 실패');
      }
    } catch {
      alert("상품 저장에 실패했습니다.");
      return;
    }

    // 새 항목 준비
    const nextCode = `s${String(products.length + 2).padStart(4, "0")}`;
    setEditForm({ ...emptyProduct, id: String(Date.now()), code: nextCode });
    setModalMode("add");
    setActiveTab(0);
  };

  const handleCancel = () => {
    setShowModal(false);
  };

  const handleCloseWindow = () => {
    windowContext?.closeThisWindow();
  };

  const handleExcelImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = async (ev) => {
        try {
          const text = ev.target?.result as string;
          if (!text) { alert('파일 내용을 읽을 수 없습니다.'); return; }

          const lines = text.split(/\r?\n/).filter(line => line.trim());
          if (lines.length < 2) { alert('데이터가 없습니다. (헤더 + 최소 1행 필요)'); return; }

          // 헤더 파싱
          const headers = lines[0].split(',').map(h => h.trim().replace(/^["']|["']$/g, ''));
          const colIdx = (names: string[]) => headers.findIndex(h => names.some(n => h.includes(n)));

          const iCode = colIdx(['상품코드', '코드', 'code']);
          const iName = colIdx(['상품명', '품명', 'name']);
          const iSpec = colIdx(['규격', 'spec']);
          const iUnit = colIdx(['단위', '재고단위', 'unit']);
          const iPurchase = colIdx(['입고가', '매입가', '원가', 'purchase']);
          const iSelling = colIdx(['소매가', '판매가', '소비자가', 'selling', 'retail']);
          const iStock = colIdx(['적정재고', '안전재고', '최소재고', 'stock']);
          const iMemo = colIdx(['메모', '비고', 'memo']);

          if (iCode < 0 || iName < 0) {
            alert('필수 열을 찾을 수 없습니다.\n필수: 상품코드(또는 코드/code), 상품명(또는 품명/name)');
            return;
          }

          let success = 0;
          let fail = 0;

          for (let i = 1; i < lines.length; i++) {
            const cols = lines[i].split(',').map(c => c.trim().replace(/^["']|["']$/g, ''));
            const code = cols[iCode] || '';
            const name = cols[iName] || '';
            if (!code || !name) { fail++; continue; }

            const payload = {
              code,
              name,
              specification: iSpec >= 0 ? (cols[iSpec] || undefined) : undefined,
              unit: iUnit >= 0 ? (cols[iUnit] || 'EA') : 'EA',
              purchase_price: iPurchase >= 0 ? (Number(cols[iPurchase]) || 0) : 0,
              selling_price: iSelling >= 0 ? (Number(cols[iSelling]) || 0) : 0,
              min_stock: iStock >= 0 ? (Number(cols[iStock]) || 0) : 0,
              memo: iMemo >= 0 ? (cols[iMemo] || undefined) : undefined,
              is_active: true,
            };

            try {
              const result = await ctxAddProduct(payload as any);
              if (result) { success++; } else { fail++; }
            } catch {
              fail++;
            }
          }

          alert(`CSV 가져오기 완료\n성공: ${success}건 / 실패: ${fail}건`);
          ctxFetchProducts();
        } catch {
          alert('CSV 파싱 중 오류가 발생했습니다.');
        }
      };
      reader.readAsText(file, 'UTF-8');
    };
    input.click();
  };

  // 규격추가 (이지판매재고관리 기능) - 현재 상품 복사하여 새 규격으로 추가
  const handleAddSpec = () => {
    if (!editForm.name) {
      alert("상품명을 먼저 입력하세요.");
      return;
    }

    const newSpec = prompt("새 규격을 입력하세요:", editForm.spec || "");
    if (newSpec === null) return; // 취소
    if (!newSpec.trim()) {
      alert("규격을 입력해주세요.");
      return;
    }

    // 동일 규격 중복 체크
    const isDuplicate = products.some(
      p => p.name === editForm.name && p.spec === newSpec.trim()
    );
    if (isDuplicate) {
      alert("동일한 상품명과 규격이 이미 존재합니다.");
      return;
    }

    // 새 상품 코드 생성
    const nextCode = `s${String(products.length + 1).padStart(4, "0")}`;

    // 현재 폼 데이터 기반으로 새 규격 상품 추가
    const newProduct: Product = {
      ...editForm,
      id: String(Date.now()),
      code: nextCode,
      spec: newSpec.trim(),
      specDetail: "", // 상세규격은 새로 입력
    };

    setProducts([...products, newProduct]);
    alert(`규격 "${newSpec}" 상품이 추가되었습니다.\n상품코드: ${nextCode}`);
  };

  // 행 더블클릭으로 수정
  const handleRowDoubleClick = (index: number) => {
    setSelectedRow(index);
    const product = displayProducts[index];
    // 카탈로그 상품은 수정 불가
    if ((product as ProductWithCatalog).is_catalog) {
      alert("카탈로그 상품은 수정할 수 없습니다. 조회만 가능합니다.");
      return;
    }
    setEditForm({ ...product as Product });
    setModalMode("edit");
    setActiveTab(0);
    setShowModal(true);
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 툴바 - 이지판매재고관리 스타일 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button
          onClick={handleAdd}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-green-600">⊕</span> 추가
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-blue-600">✎</span> 수정
        </button>
        <button
          onClick={handleDelete}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-red-600">✕</span> 삭제
        </button>
        <div className="mx-1 h-6 w-px bg-gray-400" />
        <button
          onClick={() => {
            if (selectedRow === null) { alert("미리보기할 상품을 선택하세요."); return; }
            setShowPreview(true);
          }}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span>A</span> 미리보기
        </button>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-blue-600">↻</span> 새로고침
        </button>
        <div className="mx-1 h-6 w-px bg-gray-400" />
        <div className="relative">
          <button
            onClick={() => setShowColumnToggle(!showColumnToggle)}
            className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
          >
            <span>▤</span> 표시항목 ▼
          </button>
          {showColumnToggle && (
            <div className="absolute top-full left-0 mt-1 bg-white border border-gray-300 rounded shadow-lg z-50 p-2 w-40 max-h-64 overflow-y-auto">
              {allColumns.map(col => (
                <label key={col} className="flex items-center gap-2 px-2 py-1 text-xs hover:bg-gray-50 cursor-pointer">
                  <input type="checkbox" checked={visibleColumns.has(col)} onChange={e => {
                    const next = new Set(visibleColumns);
                    if (e.target.checked) next.add(col); else next.delete(col);
                    setVisibleColumns(next);
                    const arr = [...next];
                    localStorage.setItem('erp-columns-product', JSON.stringify(arr));
                    api.erp.settings.updatePreferences({ product: arr }).catch(() => {});
                  }} />
                  {col}
                </label>
              ))}
            </div>
          )}
        </div>
        <button
          onClick={handleExcelImport}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-green-700">📊</span> 엑셀입력
        </button>
      </div>

      {/* 검색 영역 */}
      <div className="flex items-center gap-2 border-b bg-gray-100 px-4 py-2">
        <span className="text-sm">상품명:</span>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-40 rounded border border-gray-400 px-2 py-1 text-sm"
        />
        <button
          onClick={handleSearch}
          className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
        >
          검 색(F)
        </button>
        <button
          onClick={handleViewAll}
          className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
        >
          전체보기
        </button>
      </div>

      {/* 그리드 - 이지판매재고관리 컬럼 100% */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 text-center font-normal">
                <input type="checkbox" />
              </th>
              {visibleColumns.has('코드') && <th className="border border-gray-400 px-2 py-1 text-left font-normal">코드</th>}
              {visibleColumns.has('품목명') && <th className="border border-gray-400 px-2 py-1 text-left font-normal">품목명</th>}
              {visibleColumns.has('규격') && <th className="border border-gray-400 px-2 py-1 text-left font-normal">규격</th>}
              {visibleColumns.has('상세규격') && <th className="border border-gray-400 px-2 py-1 text-left font-normal">상세규격</th>}
              {visibleColumns.has('재고단위') && <th className="border border-gray-400 px-2 py-1 text-left font-normal">재고단위</th>}
              {visibleColumns.has('적정재고') && <th className="border border-gray-400 px-2 py-1 text-right font-normal">적정재고</th>}
              {visibleColumns.has('입고가') && <th className="border border-gray-400 px-2 py-1 text-right font-normal">입고가</th>}
              {visibleColumns.has('도매가') && <th className="border border-gray-400 px-2 py-1 text-right font-normal">도매가</th>}
              {visibleColumns.has('소매가') && <th className="border border-gray-400 px-2 py-1 text-right font-normal">소매가</th>}
              {visibleColumns.has('상품분류') && <th className="border border-gray-400 px-2 py-1 text-left font-normal">상품분류</th>}
              {visibleColumns.has('메모') && <th className="border border-gray-400 px-2 py-1 text-left font-normal">메모</th>}
            </tr>
          </thead>
          <tbody>
            {displayProducts.map((product, index) => {
              const isCatalog = (product as ProductWithCatalog).is_catalog;
              return (
                <tr
                  key={product.id}
                  className={`cursor-pointer ${
                    selectedRow === index
                      ? "bg-[#316AC5] text-white"
                      : isCatalog
                      ? "bg-blue-50 hover:bg-blue-100"
                      : "bg-white hover:bg-gray-100"
                  }`}
                  onClick={() => setSelectedRow(index)}
                  onDoubleClick={() => handleRowDoubleClick(index)}
                >
                  <td className="border border-gray-300 px-2 py-1 text-center">
                    {isCatalog ? (
                      <span className="text-blue-600 text-xs">📦</span>
                    ) : (
                      <input type="checkbox" />
                    )}
                  </td>
                  {visibleColumns.has('코드') && <td className="border border-gray-300 px-2 py-1">{product.code}</td>}
                  {visibleColumns.has('품목명') && <td className="border border-gray-300 px-2 py-1">
                    {product.name}
                    {isCatalog && <span className="ml-1 text-xs text-blue-500">[카탈로그]</span>}
                  </td>}
                  {visibleColumns.has('규격') && <td className="border border-gray-300 px-2 py-1">{product.spec || ""}</td>}
                  {visibleColumns.has('상세규격') && <td className="border border-gray-300 px-2 py-1">{(product as Product).specDetail || ""}</td>}
                  {visibleColumns.has('재고단위') && <td className="border border-gray-300 px-2 py-1">{product.unit || ""}</td>}
                  {visibleColumns.has('적정재고') && <td className="border border-gray-300 px-2 py-1 text-right">
                    {((product as Product).optimalStock || 0).toLocaleString()}
                  </td>}
                  {visibleColumns.has('입고가') && <td className="border border-gray-300 px-2 py-1 text-right">
                    {((product as Product).purchasePrice || 0).toLocaleString()}
                  </td>}
                  {visibleColumns.has('도매가') && <td className="border border-gray-300 px-2 py-1 text-right">
                    {((product as Product).wholesalePrice || 0).toLocaleString()}
                  </td>}
                  {visibleColumns.has('소매가') && <td className="border border-gray-300 px-2 py-1 text-right">
                    {((product as Product).retailPrice || 0).toLocaleString()}
                  </td>}
                  {visibleColumns.has('상품분류') && <td className="border border-gray-300 px-2 py-1">{(product as Product).category || ""}</td>}
                  {visibleColumns.has('메모') && <td className="border border-gray-300 px-2 py-1">{(product as Product).memo || ""}</td>}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="flex items-center justify-between border-t bg-gray-100 px-4 py-1 text-sm text-gray-600">
        <div className="flex items-center gap-2">
          {isSearching && <span className="text-blue-600">검색중...</span>}
          {searchQuery.length >= 2 && !isSearching && apiProducts.length > 0 && (
            <span className="text-blue-600">
              검색결과: ERP {searchCounts.erp}개 + 카탈로그 {searchCounts.catalog}개
            </span>
          )}
        </div>
        <div className="flex items-center">
          <span>전체 {products.length} 항목</span>
          <span className="mx-4">|</span>
          <span>{displayProducts.length} 항목표시</span>
        </div>
      </div>

      {/* 상품정보등록 모달 - 이지판매재고관리 100% 복제 */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-[420px] rounded bg-gray-200 shadow-lg">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between border-b border-gray-400 bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">상품정보등록</span>
              <button
                onClick={handleCancel}
                className="text-white hover:text-gray-200"
              >
                ✕
              </button>
            </div>

            {/* 탭 헤더 - 이지판매재고관리 스타일 */}
            <div className="flex border-b border-gray-300 bg-gray-200">
              {tabs.map((tab, index) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(index)}
                  className={`border-r border-gray-300 px-4 py-2 text-sm ${
                    activeTab === index
                      ? "border-t-2 border-t-blue-500 bg-white"
                      : "bg-gray-100 hover:bg-gray-50"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* 탭 내용 */}
            <div className="bg-[#F0EDE4] p-4">
              {/* 기본정보입력 탭 */}
              {activeTab === 0 && (
                <div className="space-y-3">
                  <fieldset className="rounded border border-gray-400 p-3">
                    <legend className="px-2 text-sm text-blue-700">기본정보</legend>
                    <div className="grid grid-cols-[80px_1fr] gap-2 text-sm">
                      <label className="py-1 text-right">상품코드:</label>
                      <input
                        type="text"
                        value={editForm.code}
                        onChange={(e) => setEditForm({ ...editForm, code: e.target.value })}
                        className="w-32 border border-gray-400 px-2 py-1"
                      />

                      <label className="py-1 text-right">상품명:</label>
                      <input
                        type="text"
                        value={editForm.name}
                        onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                        className="w-full border border-gray-400 px-2 py-1"
                      />

                      <label className="py-1 text-right">규격:</label>
                      <input
                        type="text"
                        value={editForm.spec}
                        onChange={(e) => setEditForm({ ...editForm, spec: e.target.value })}
                        className="w-full border border-gray-400 px-2 py-1"
                      />

                      <label className="py-1 text-right">상세규격:</label>
                      <input
                        type="text"
                        value={editForm.specDetail}
                        onChange={(e) => setEditForm({ ...editForm, specDetail: e.target.value })}
                        className="w-full border border-gray-400 px-2 py-1"
                      />

                      <label className="py-1 text-right">재고단위:</label>
                      <div className="flex gap-1">
                        <select
                          value={editForm.unit}
                          onChange={(e) => setEditForm({ ...editForm, unit: e.target.value })}
                          className="w-24 border border-gray-400 px-2 py-1"
                        >
                          {UNIT_OPTIONS.map((unit) => (
                            <option key={unit} value={unit}>{unit}</option>
                          ))}
                        </select>
                        <button className="rounded border border-gray-400 bg-gray-100 px-2 hover:bg-gray-200">
                          ...
                        </button>
                      </div>
                    </div>
                  </fieldset>

                  <fieldset className="rounded border border-gray-400 p-3">
                    <legend className="px-2 text-sm text-blue-700">분류정보</legend>
                    <div className="grid grid-cols-[80px_1fr] gap-2 text-sm">
                      <label className="py-1 text-right">상품분류:</label>
                      <div className="flex gap-1">
                        <input
                          type="text"
                          value={editForm.category}
                          readOnly
                          className="w-40 border border-gray-400 bg-white px-2 py-1"
                        />
                        <button
                          onClick={() => setShowCategoryModal(true)}
                          className="rounded border border-gray-400 bg-gray-100 px-2 hover:bg-gray-200"
                        >
                          ...
                        </button>
                      </div>

                      <label className="py-1 text-right">테마분류:</label>
                      <input
                        type="text"
                        value={editForm.theme}
                        onChange={(e) => setEditForm({ ...editForm, theme: e.target.value })}
                        className="w-40 border border-gray-400 px-2 py-1"
                      />
                    </div>
                  </fieldset>
                  <p className="text-sm text-gray-600">새로운 상품의 정보를 등록합니다.</p>
                </div>
              )}

              {/* 상세정보입력 탭 */}
              {activeTab === 1 && (
                <div className="space-y-3">
                  <fieldset className="rounded border border-gray-400 p-3">
                    <legend className="px-2 text-sm text-blue-700">판매단가정보</legend>
                    <div className="grid grid-cols-[80px_1fr] gap-2 text-sm">
                      <label className="py-1 text-right">입고가:</label>
                      <div className="flex items-center gap-1">
                        <input
                          type="number"
                          value={editForm.purchasePrice}
                          onChange={(e) => setEditForm({ ...editForm, purchasePrice: Number(e.target.value) })}
                          className="w-32 border border-gray-400 px-2 py-1 text-right"
                        />
                        <span>원</span>
                      </div>

                      <label className="py-1 text-right">도매가:</label>
                      <div className="flex items-center gap-1">
                        <input
                          type="number"
                          value={editForm.wholesalePrice}
                          onChange={(e) => setEditForm({ ...editForm, wholesalePrice: Number(e.target.value) })}
                          className="w-32 border border-gray-400 px-2 py-1 text-right"
                        />
                        <span>원</span>
                      </div>

                      <label className="py-1 text-right">소매가:</label>
                      <div className="flex items-center gap-1">
                        <input
                          type="number"
                          value={editForm.retailPrice}
                          onChange={(e) => setEditForm({ ...editForm, retailPrice: Number(e.target.value) })}
                          className="w-32 border border-gray-400 px-2 py-1 text-right"
                        />
                        <span>원</span>
                      </div>

                      <label className="py-1 text-right">적용비율:</label>
                      <select
                        value={editForm.priceRatioType}
                        onChange={(e) => setEditForm({ ...editForm, priceRatioType: e.target.value })}
                        className="w-32 border border-gray-400 px-2 py-1"
                      >
                        {PRICE_RATIO_OPTIONS.map((opt) => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>

                      <label className="py-1 text-right">상품마진율:</label>
                      <div className="flex items-center gap-1">
                        <input
                          type="number"
                          value={editForm.marginRate}
                          onChange={(e) => setEditForm({ ...editForm, marginRate: Number(e.target.value) })}
                          className="w-24 border border-gray-400 px-2 py-1 text-right"
                        />
                        <span>%</span>
                      </div>
                    </div>
                  </fieldset>

                  <fieldset className="rounded border border-gray-400 p-3">
                    <legend className="px-2 text-sm text-blue-700">기타정보</legend>
                    <div className="grid grid-cols-[80px_1fr] gap-2 text-sm">
                      <label className="py-1 text-right">적정재고:</label>
                      <input
                        type="number"
                        value={editForm.optimalStock}
                        onChange={(e) => setEditForm({ ...editForm, optimalStock: Number(e.target.value) })}
                        className="w-24 border border-gray-400 px-2 py-1 text-right"
                      />

                      <label className="py-1 text-right">현재상태:</label>
                      <select
                        value={editForm.status}
                        onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                        className="w-32 border border-gray-400 px-2 py-1"
                      >
                        {STATUS_OPTIONS.map((opt) => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>
                    </div>
                  </fieldset>
                  <p className="text-sm text-gray-600">새로운 상품의 정보를 등록합니다.</p>
                </div>
              )}

              {/* 메모 탭 */}
              {activeTab === 2 && (
                <div className="space-y-3">
                  <fieldset className="rounded border border-gray-400 p-3">
                    <legend className="px-2 text-sm text-blue-700">메모</legend>
                    <textarea
                      value={editForm.memo}
                      onChange={(e) => setEditForm({ ...editForm, memo: e.target.value })}
                      className="h-40 w-full border border-gray-400 px-2 py-1"
                      placeholder="상품에 대한 메모를 입력하세요."
                    />
                  </fieldset>
                  <p className="text-sm text-gray-600">새로운 상품의 정보를 등록합니다.</p>
                </div>
              )}
            </div>

            {/* 모달 푸터 - 이지판매재고관리 스타일 */}
            <div className="flex justify-end gap-2 border-t border-gray-400 bg-gray-200 px-4 py-3">
              <button
                onClick={handleAddSpec}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
              >
                규격추가
              </button>
              <button
                onClick={handleSaveAndAdd}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
              >
                저장후추가
              </button>
              <button
                onClick={handleSave}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
              >
                저장
              </button>
              <button
                onClick={handleCancel}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 미리보기 모달 */}
      {showPreview && selectedRow !== null && (() => {
        const previewProduct = displayProducts[selectedRow] as Product;
        return (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded shadow-lg w-[450px]">
              <div className="flex items-center justify-between px-4 py-2 bg-gray-200 rounded-t">
                <span className="text-sm font-medium">상품 미리보기</span>
                <button onClick={() => setShowPreview(false)} className="text-gray-600 hover:text-gray-800 text-lg">x</button>
              </div>
              <div className="p-4 text-sm space-y-2">
                <div className="flex"><span className="w-24 text-gray-500">상품코드:</span><span>{previewProduct.code}</span></div>
                <div className="flex"><span className="w-24 text-gray-500">상품명:</span><span>{previewProduct.name}</span></div>
                <div className="flex"><span className="w-24 text-gray-500">규격:</span><span>{previewProduct.spec}</span></div>
                <div className="flex"><span className="w-24 text-gray-500">재고단위:</span><span>{previewProduct.unit}</span></div>
                <div className="flex"><span className="w-24 text-gray-500">입고가:</span><span>{(previewProduct.purchasePrice || 0).toLocaleString()}원</span></div>
                <div className="flex"><span className="w-24 text-gray-500">도매가:</span><span>{(previewProduct.wholesalePrice || 0).toLocaleString()}원</span></div>
                <div className="flex"><span className="w-24 text-gray-500">소매가:</span><span>{(previewProduct.retailPrice || 0).toLocaleString()}원</span></div>
                <div className="flex"><span className="w-24 text-gray-500">적정재고:</span><span>{(previewProduct.optimalStock || 0).toLocaleString()}</span></div>
                {previewProduct.memo && <div className="flex"><span className="w-24 text-gray-500">메모:</span><span>{previewProduct.memo}</span></div>}
              </div>
              <div className="flex justify-end px-4 py-3 bg-gray-100 rounded-b">
                <button onClick={() => setShowPreview(false)} className="px-4 py-1.5 bg-gray-200 border border-gray-400 rounded text-sm">닫기</button>
              </div>
            </div>
          </div>
        );
      })()}

      {/* 분류 선택 모달 */}
      {showCategoryModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-[300px] rounded bg-white shadow-lg">
            <div className="flex items-center justify-between border-b bg-gray-200 px-3 py-2">
              <span className="text-sm font-medium">상품분류 선택</span>
              <button onClick={() => setShowCategoryModal(false)} className="hover:text-gray-600">
                ✕
              </button>
            </div>
            <div className="max-h-[300px] overflow-y-auto p-2">
              {["테스트", "전자제품", "악세서리", "생활용품", "의류", "식품"].map((cat) => (
                <div
                  key={cat}
                  onClick={() => {
                    setEditForm({ ...editForm, category: cat });
                    setShowCategoryModal(false);
                  }}
                  className="cursor-pointer rounded px-3 py-2 text-sm hover:bg-blue-100"
                >
                  {cat}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
