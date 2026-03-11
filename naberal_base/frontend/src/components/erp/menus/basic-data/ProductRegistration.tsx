"use client";

import React, { useState } from "react";
import { useERPData, Product as APIProduct } from "@/contexts/ERPDataContext";

interface Product {
  id: string;
  code: string;
  name: string;
  spec: string;
  detailSpec: string;
  unit: string;
  safetyStock: number;
  purchasePrice: number;
  wholesalePrice: number;
  retailPrice: number;
  category: string;
  themeCategory: string;
  memo: string;
}

// API 데이터를 로컬 Product 타입으로 변환
const apiToLocalProduct = (api: APIProduct): Product => ({
  id: api.id,
  code: api.code,
  name: api.name,
  spec: api.specification || "",
  detailSpec: "",
  unit: api.unit || "EA",
  safetyStock: api.min_stock || 0,
  purchasePrice: api.purchase_price || 0,
  wholesalePrice: api.selling_price || 0,
  retailPrice: api.selling_price || 0,
  category: api.category || "",
  themeCategory: "",
  memo: api.memo || "",
});

// 로컬 Product를 API 형식으로 변환
const localToApiProduct = (local: Product): Omit<APIProduct, "id" | "created_at" | "updated_at"> => ({
  code: local.code,
  name: local.name,
  specification: local.spec || undefined,
  unit: local.unit || undefined,
  purchase_price: local.purchasePrice || undefined,
  selling_price: local.retailPrice || undefined,
  min_stock: local.safetyStock || undefined,
  category: local.category || undefined,
  memo: local.memo || undefined,
  is_active: true,
});

type ModalTab = "기본정보입력" | "상세정보입력" | "메모";

export function ProductRegistration() {
  // ERPDataContext에서 데이터 및 함수 가져오기
  const {
    products: apiProducts,
    productsLoading,
    fetchProducts,
    addProduct: apiAddProduct,
    updateProduct: apiUpdateProduct,
    deleteProduct: apiDeleteProduct,
  } = useERPData();

  // 로컬 상태
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalTab, setModalTab] = useState<ModalTab>("기본정보입력");
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [isNewProduct, setIsNewProduct] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // API 데이터를 로컬 형식으로 변환
  const products = apiProducts.map(apiToLocalProduct);

  const filteredProducts = products.filter(
    (p) => p.name.includes(searchQuery) || p.code.includes(searchQuery)
  );

  const handleAdd = () => {
    setIsNewProduct(true);
    setEditingProduct({
      id: Date.now().toString(),
      code: `s${String(products.length + 1).padStart(4, "0")}`,
      name: "", spec: "", detailSpec: "", unit: "EA",
      safetyStock: 0, purchasePrice: 0, wholesalePrice: 0, retailPrice: 0,
      category: "", themeCategory: "", memo: ""
    });
    setModalTab("기본정보입력");
    setIsModalOpen(true);
  };

  const handleEdit = () => {
    const product = products.find((p) => p.id === selectedId);
    if (product) {
      setIsNewProduct(false);
      setEditingProduct({ ...product });
      setModalTab("기본정보입력");
      setIsModalOpen(true);
    }
  };

  const handleDelete = async () => {
    if (selectedId && confirm("선택한 상품을 삭제하시겠습니까?")) {
      setIsSaving(true);
      try {
        const success = await apiDeleteProduct(selectedId);
        if (success) {
          setSelectedId(null);
          alert("삭제되었습니다.");
        } else {
          alert("삭제에 실패했습니다.");
        }
      } catch (error) {
        console.error("상품 삭제 오류:", error);
        alert("삭제 중 오류가 발생했습니다.");
      } finally {
        setIsSaving(false);
      }
    }
  };

  const handleSave = async () => {
    if (!editingProduct) return;
    if (!editingProduct.name) {
      alert("상품명을 입력하세요.");
      return;
    }

    setIsSaving(true);
    try {
      const apiData = localToApiProduct(editingProduct);

      if (isNewProduct) {
        const result = await apiAddProduct(apiData);
        if (result) {
          alert("상품이 등록되었습니다.");
          setIsModalOpen(false);
          setEditingProduct(null);
        } else {
          alert("상품 등록에 실패했습니다.");
        }
      } else {
        const result = await apiUpdateProduct(editingProduct.id, apiData);
        if (result) {
          alert("상품이 수정되었습니다.");
          setIsModalOpen(false);
          setEditingProduct(null);
        } else {
          alert("상품 수정에 실패했습니다.");
        }
      }
    } catch (error) {
      console.error("상품 저장 오류:", error);
      alert("저장 중 오류가 발생했습니다.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveAndAdd = async () => {
    if (!editingProduct) return;
    if (!editingProduct.name) {
      alert("상품명을 입력하세요.");
      return;
    }

    setIsSaving(true);
    try {
      const apiData = localToApiProduct(editingProduct);
      const result = await apiAddProduct(apiData);
      if (result) {
        // 저장 성공 후 새 상품 추가 모드로 전환
        setEditingProduct({
          id: Date.now().toString(),
          code: `s${String(products.length + 2).padStart(4, "0")}`,
          name: "", spec: "", detailSpec: "", unit: "EA",
          safetyStock: 0, purchasePrice: 0, wholesalePrice: 0, retailPrice: 0,
          category: "", themeCategory: "", memo: ""
        });
        setModalTab("기본정보입력");
      } else {
        alert("상품 등록에 실패했습니다.");
      }
    } catch (error) {
      console.error("상품 저장 오류:", error);
      alert("저장 중 오류가 발생했습니다.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleRefresh = async () => {
    await fetchProducts();
  };

  const formatNumber = (n: number) => n.toLocaleString();

  const modalTabs: ModalTab[] = ["기본정보입력", "상세정보입력", "메모"];

  return (
    <div className="flex h-full flex-col bg-gray-50">
      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-100 px-2 py-1">
        <button onClick={handleAdd} className="flex items-center gap-1 rounded border border-gray-300 bg-white px-3 py-1 text-sm hover:bg-gray-50">
          <span className="text-green-600">⊕</span> 추가
        </button>
        <button onClick={handleEdit} disabled={!selectedId} className="flex items-center gap-1 rounded border border-gray-300 bg-white px-3 py-1 text-sm hover:bg-gray-50 disabled:opacity-50">
          <span className="text-blue-600">✓</span> 수정
        </button>
        <button onClick={handleDelete} disabled={!selectedId || isSaving} className="flex items-center gap-1 rounded border border-gray-300 bg-white px-3 py-1 text-sm hover:bg-gray-50 disabled:opacity-50">
          <span className="text-red-600">✕</span> 삭제
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-300 bg-white px-3 py-1 text-sm hover:bg-gray-50">
          🔗 구성상품
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-300 bg-white px-3 py-1 text-sm hover:bg-gray-50">
          <span>A</span> 미리보기
        </button>
        <button onClick={handleRefresh} disabled={productsLoading} className="flex items-center gap-1 rounded border border-gray-300 bg-white px-3 py-1 text-sm hover:bg-gray-50 disabled:opacity-50">
          🔄 {productsLoading ? "로딩중..." : "새로고침"}
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-300 bg-white px-3 py-1 text-sm hover:bg-gray-50">
          📋 표시항목 ▼
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-300 bg-white px-3 py-1 text-sm hover:bg-gray-50">
          📊 엑셀입력
        </button>
      </div>

      {/* 검색 */}
      <div className="flex items-center gap-2 border-b bg-white px-3 py-2">
        <span className="text-sm">상품명:</span>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-40 rounded border border-gray-300 px-2 py-1 text-sm"
        />
        <button className="rounded border border-gray-300 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
          검 색(F)
        </button>
        <button onClick={() => setSearchQuery("")} className="rounded border border-gray-300 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
          전체보기
        </button>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-300 px-2 py-1 text-left">코드</th>
              <th className="border border-gray-300 px-2 py-1 text-left">품목명</th>
              <th className="border border-gray-300 px-2 py-1 text-left">규격</th>
              <th className="border border-gray-300 px-2 py-1 text-left">상세규격</th>
              <th className="border border-gray-300 px-2 py-1 text-left">재고단위</th>
              <th className="border border-gray-300 px-2 py-1 text-right">적정재고</th>
              <th className="border border-gray-300 px-2 py-1 text-right">입고가</th>
              <th className="border border-gray-300 px-2 py-1 text-right">도매가</th>
              <th className="border border-gray-300 px-2 py-1 text-right">소매가</th>
              <th className="border border-gray-300 px-2 py-1 text-left">상품분류</th>
              <th className="border border-gray-300 px-2 py-1 text-left">메모</th>
            </tr>
          </thead>
          <tbody>
            {filteredProducts.map((p) => (
              <tr
                key={p.id}
                className={`cursor-pointer ${selectedId === p.id ? "bg-[#316AC5] text-white" : "hover:bg-gray-100"}`}
                onClick={() => setSelectedId(p.id)}
                onDoubleClick={handleEdit}
              >
                <td className="border border-gray-200 px-2 py-1">{p.code}</td>
                <td className="border border-gray-200 px-2 py-1">{p.name}</td>
                <td className="border border-gray-200 px-2 py-1">{p.spec}</td>
                <td className="border border-gray-200 px-2 py-1">{p.detailSpec}</td>
                <td className="border border-gray-200 px-2 py-1">{p.unit}</td>
                <td className="border border-gray-200 px-2 py-1 text-right">{formatNumber(p.safetyStock)}</td>
                <td className="border border-gray-200 px-2 py-1 text-right">{formatNumber(p.purchasePrice)}</td>
                <td className="border border-gray-200 px-2 py-1 text-right">{formatNumber(p.wholesalePrice)}</td>
                <td className="border border-gray-200 px-2 py-1 text-right">{formatNumber(p.retailPrice)}</td>
                <td className="border border-gray-200 px-2 py-1">{p.category}</td>
                <td className="border border-gray-200 px-2 py-1">{p.memo}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 상태바 */}
      <div className="flex justify-end border-t bg-gray-100 px-3 py-1 text-xs text-gray-600">
        전체 {products.length} 항목 | {filteredProducts.length} 항목표시
      </div>

      {/* 모달 */}
      {isModalOpen && editingProduct && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="w-[450px] rounded border border-gray-400 bg-[#F0EDE4] shadow-lg">
            <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">상품정보등록</span>
              <button onClick={() => setIsModalOpen(false)} className="text-white hover:text-gray-200">✕</button>
            </div>

            {/* 탭 */}
            <div className="flex border-b bg-[#E8E4D9]">
              {modalTabs.map((tab) => (
                <button
                  key={tab}
                  onClick={() => setModalTab(tab)}
                  className={`px-3 py-1.5 text-xs ${modalTab === tab ? "bg-[#F0EDE4] font-medium" : "hover:bg-gray-200"}`}
                >
                  {tab}
                </button>
              ))}
            </div>

            <div className="p-4">
              {modalTab === "기본정보입력" && (
                <>
                  <fieldset className="mb-3 rounded border border-gray-400 p-3">
                    <legend className="px-2 text-xs text-blue-700">기본정보</legend>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <label className="w-16 text-right text-xs">상품코드:</label>
                        <input type="text" value={editingProduct.code} readOnly className="w-24 rounded border border-gray-300 bg-gray-100 px-2 py-1 text-xs" />
                      </div>
                      <div className="flex items-center gap-2">
                        <label className="w-16 text-right text-xs">상품명:</label>
                        <input type="text" value={editingProduct.name} onChange={(e) => setEditingProduct({ ...editingProduct, name: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                      </div>
                      <div className="flex items-center gap-2">
                        <label className="w-16 text-right text-xs">규격:</label>
                        <input type="text" value={editingProduct.spec} onChange={(e) => setEditingProduct({ ...editingProduct, spec: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                      </div>
                      <div className="flex items-center gap-2">
                        <label className="w-16 text-right text-xs">상세규격:</label>
                        <input type="text" value={editingProduct.detailSpec} onChange={(e) => setEditingProduct({ ...editingProduct, detailSpec: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                      </div>
                      <div className="flex items-center gap-2">
                        <label className="w-16 text-right text-xs">재고단위:</label>
                        <select value={editingProduct.unit} onChange={(e) => setEditingProduct({ ...editingProduct, unit: e.target.value })} className="w-20 rounded border border-gray-300 px-2 py-1 text-xs">
                          <option value="EA">EA</option>
                          <option value="box">box</option>
                          <option value="set">set</option>
                          <option value="kg">kg</option>
                          <option value="m">m</option>
                        </select>
                        <button className="rounded border border-gray-300 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">...</button>
                      </div>
                    </div>
                  </fieldset>
                  <fieldset className="rounded border border-gray-400 p-3">
                    <legend className="px-2 text-xs text-blue-700">분류정보</legend>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <label className="w-16 text-right text-xs">상품분류:</label>
                        <input type="text" value={editingProduct.category} onChange={(e) => setEditingProduct({ ...editingProduct, category: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                        <button className="rounded border border-gray-300 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">...</button>
                      </div>
                      <div className="flex items-center gap-2">
                        <label className="w-16 text-right text-xs">테마분류:</label>
                        <input type="text" value={editingProduct.themeCategory} onChange={(e) => setEditingProduct({ ...editingProduct, themeCategory: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                      </div>
                    </div>
                  </fieldset>
                </>
              )}

              {modalTab === "상세정보입력" && (
                <fieldset className="rounded border border-gray-400 p-3">
                  <legend className="px-2 text-xs text-blue-700">가격정보</legend>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <label className="w-16 text-right text-xs">적정재고:</label>
                      <input type="number" value={editingProduct.safetyStock} onChange={(e) => setEditingProduct({ ...editingProduct, safetyStock: Number(e.target.value) })} className="w-32 rounded border border-gray-300 px-2 py-1 text-xs text-right" />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-16 text-right text-xs">입고가:</label>
                      <input type="number" value={editingProduct.purchasePrice} onChange={(e) => setEditingProduct({ ...editingProduct, purchasePrice: Number(e.target.value) })} className="w-32 rounded border border-gray-300 px-2 py-1 text-xs text-right" />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-16 text-right text-xs">도매가:</label>
                      <input type="number" value={editingProduct.wholesalePrice} onChange={(e) => setEditingProduct({ ...editingProduct, wholesalePrice: Number(e.target.value) })} className="w-32 rounded border border-gray-300 px-2 py-1 text-xs text-right" />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-16 text-right text-xs">소매가:</label>
                      <input type="number" value={editingProduct.retailPrice} onChange={(e) => setEditingProduct({ ...editingProduct, retailPrice: Number(e.target.value) })} className="w-32 rounded border border-gray-300 px-2 py-1 text-xs text-right" />
                    </div>
                  </div>
                </fieldset>
              )}

              {modalTab === "메모" && (
                <fieldset className="rounded border border-gray-400 p-3">
                  <legend className="px-2 text-xs text-blue-700">메모</legend>
                  <textarea
                    value={editingProduct.memo}
                    onChange={(e) => setEditingProduct({ ...editingProduct, memo: e.target.value })}
                    className="h-32 w-full rounded border border-gray-300 p-2 text-xs"
                    placeholder="메모를 입력하세요."
                  />
                </fieldset>
              )}

              <div className="mt-3 text-xs text-blue-600">
                새로운 상품의 정보를 등록합니다.
              </div>
            </div>

            <div className="flex justify-end gap-2 border-t bg-[#E8E4D9] px-4 py-2">
              <button className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-xs hover:bg-gray-200">규격추가</button>
              <button onClick={handleSaveAndAdd} disabled={isSaving} className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-xs hover:bg-gray-200 disabled:opacity-50">
                {isSaving ? "저장중..." : "저장후추가"}
              </button>
              <button onClick={handleSave} disabled={isSaving} className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-xs hover:bg-gray-200 disabled:opacity-50">
                {isSaving ? "저장중..." : "저장"}
              </button>
              <button onClick={() => setIsModalOpen(false)} disabled={isSaving} className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-xs hover:bg-gray-200 disabled:opacity-50">취소</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
