"use client";

import React, { useState } from "react";

interface Product {
  id: string;
  code: string;          // 코드
  productName: string;   // 품목명
  spec: string;          // 규격
  detailSpec: string;    // 상세규격
  stockUnit: string;     // 재고단위
  properStock: number;   // 적정재고
  purchasePrice: number; // 입가
  wholesalePrice: number; // 도매가
  retailPrice: number;   // 소매가
  category: string;      // 상품분류
  memo: string;          // 메모
}

// 이지판매재고관리 원본 데이터 100% 복제 (2025-12-05 스크린샷 기준)
const ORIGINAL_PRODUCTS: Product[] = [
  { id: "1", code: "s0001", productName: "핸드폰케이스", spec: "10×10", detailSpec: "100×100", stockUnit: "EA", properStock: 100, purchasePrice: 10000, wholesalePrice: 11000, retailPrice: 12000, category: "테스트", memo: "" },
  { id: "2", code: "s0002", productName: "노트북케이스", spec: "20×25", detailSpec: "200×300", stockUnit: "box", properStock: 2000, purchasePrice: 15000, wholesalePrice: 17000, retailPrice: 20000, category: "", memo: "" },
  { id: "3", code: "s0003", productName: "키보드케이스", spec: "300×400", detailSpec: "350×450", stockUnit: "set", properStock: 150, purchasePrice: 4500, wholesalePrice: 5000, retailPrice: 7000, category: "", memo: "" },
];

// 상품분류 목록
const PRODUCT_CATEGORIES = [
  "테스트",
  "전자제품",
  "컴퓨터부품",
  "악세서리",
  "생활용품",
  "기타",
];

// 재고단위 목록
const STOCK_UNITS = ["EA", "box", "set", "개", "세트", "케이스", "팩", "KG", "M"];

const emptyProduct: Product = {
  id: "",
  code: "",
  productName: "",
  spec: "",
  detailSpec: "",
  stockUnit: "EA",
  properStock: 0,
  purchasePrice: 0,
  wholesalePrice: 0,
  retailPrice: 0,
  category: "",
  memo: "",
};

export function ProductInfoWindow() {
  const [products, setProducts] = useState<Product[]>(ORIGINAL_PRODUCTS);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRow, setSelectedRow] = useState<number | null>(null);

  // 모달 상태
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit">("add");
  const [editForm, setEditForm] = useState<Product>(emptyProduct);

  // 구성상품 모달 상태
  const [showCompositeModal, setShowCompositeModal] = useState(false);

  const filteredProducts = products.filter(
    (p) =>
      p.productName.includes(searchQuery) ||
      p.code.includes(searchQuery) ||
      p.spec.includes(searchQuery)
  );

  // 툴바 버튼 핸들러
  const handleAdd = () => {
    const nextCode = `s${String(products.length + 1).padStart(4, "0")}`;
    setEditForm({ ...emptyProduct, id: String(Date.now()), code: nextCode });
    setModalMode("add");
    setShowModal(true);
  };

  const handleEdit = () => {
    if (selectedRow === null) {
      alert("수정할 상품을 선택하세요.");
      return;
    }
    const product = filteredProducts[selectedRow];
    setEditForm({ ...product });
    setModalMode("edit");
    setShowModal(true);
  };

  const handleDelete = () => {
    if (selectedRow === null) {
      alert("삭제할 상품을 선택하세요.");
      return;
    }
    if (confirm("선택한 상품을 삭제하시겠습니까?")) {
      const product = filteredProducts[selectedRow];
      setProducts(products.filter((p) => p.id !== product.id));
      setSelectedRow(null);
    }
  };

  const handleComposite = () => {
    if (selectedRow === null) {
      alert("구성상품을 설정할 상품을 선택하세요.");
      return;
    }
    setShowCompositeModal(true);
  };

  const handleRefresh = () => {
    setProducts([...ORIGINAL_PRODUCTS]);
    setSelectedRow(null);
    setSearchQuery("");
  };

  const handleSearch = () => {
    // 검색은 실시간으로 되므로 별도 처리 불필요
  };

  const handleViewAll = () => {
    setSearchQuery("");
  };

  // 모달 저장
  const handleSave = () => {
    if (!editForm.productName) {
      alert("품목명을 입력하세요.");
      return;
    }
    if (!editForm.code) {
      alert("코드를 입력하세요.");
      return;
    }

    if (modalMode === "add") {
      setProducts([...products, editForm]);
    } else {
      setProducts(
        products.map((p) => (p.id === editForm.id ? editForm : p))
      );
    }
    setShowModal(false);
    setSelectedRow(null);
  };

  // 저장 후 추가
  const handleSaveAndAdd = () => {
    if (!editForm.productName) {
      alert("품목명을 입력하세요.");
      return;
    }
    if (!editForm.code) {
      alert("코드를 입력하세요.");
      return;
    }

    if (modalMode === "add") {
      setProducts([...products, editForm]);
    } else {
      setProducts(
        products.map((p) => (p.id === editForm.id ? editForm : p))
      );
    }
    // 새 항목으로 초기화
    const nextCode = `s${String(products.length + 2).padStart(4, "0")}`;
    setEditForm({ ...emptyProduct, id: String(Date.now()), code: nextCode });
    setModalMode("add");
  };

  const handleCancel = () => {
    setShowModal(false);
  };

  // 행 더블클릭으로 수정
  const handleRowDoubleClick = (index: number) => {
    setSelectedRow(index);
    const product = filteredProducts[index];
    setEditForm({ ...product });
    setModalMode("edit");
    setShowModal(true);
  };

  // 금액 포맷
  const formatNumber = (num: number) => {
    return num.toLocaleString();
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
          onClick={handleComposite}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-orange-600">🔗</span> 구성상품
        </button>
        <div className="mx-1 h-6 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
          <span>A</span> 미리보기
        </button>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-blue-600">↻</span> 새로고침
        </button>
        <div className="mx-1 h-6 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
          <span>▤</span> 표시항목
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
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
          className="w-48 rounded border border-gray-400 px-2 py-1 text-sm"
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
              <th className="border border-gray-400 px-2 py-1 text-center font-normal w-8">
                <input type="checkbox" />
              </th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal w-20">코드</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">품목명</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal w-24">규격</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal w-24">상세규격</th>
              <th className="border border-gray-400 px-2 py-1 text-center font-normal w-20">재고단위</th>
              <th className="border border-gray-400 px-2 py-1 text-right font-normal w-20">적정재고</th>
              <th className="border border-gray-400 px-2 py-1 text-right font-normal w-24">입가</th>
              <th className="border border-gray-400 px-2 py-1 text-right font-normal w-24">도매가</th>
              <th className="border border-gray-400 px-2 py-1 text-right font-normal w-24">소매가</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal w-24">상품분류</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">메모</th>
            </tr>
          </thead>
          <tbody>
            {filteredProducts.map((product, index) => (
              <tr
                key={product.id}
                className={`cursor-pointer ${
                  selectedRow === index ? "bg-[#316AC5] text-white" : "bg-white hover:bg-gray-100"
                }`}
                onClick={() => setSelectedRow(index)}
                onDoubleClick={() => handleRowDoubleClick(index)}
              >
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <input type="checkbox" />
                </td>
                <td className="border border-gray-300 px-2 py-1">{product.code}</td>
                <td className="border border-gray-300 px-2 py-1">{product.productName}</td>
                <td className="border border-gray-300 px-2 py-1">{product.spec}</td>
                <td className="border border-gray-300 px-2 py-1">{product.detailSpec}</td>
                <td className="border border-gray-300 px-2 py-1 text-center">{product.stockUnit}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">{formatNumber(product.properStock)}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">{formatNumber(product.purchasePrice)}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">{formatNumber(product.wholesalePrice)}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">{formatNumber(product.retailPrice)}</td>
                <td className="border border-gray-300 px-2 py-1">{product.category}</td>
                <td className="border border-gray-300 px-2 py-1">{product.memo}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="flex items-center justify-end border-t bg-gray-100 px-4 py-1 text-sm text-gray-600">
        <span>전체 {products.length} 항목</span>
        <span className="mx-4">|</span>
        <span>{filteredProducts.length} 항목표시</span>
      </div>

      {/* 상품 등록 모달 - 이지판매재고관리 100% 복제 */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-[550px] rounded bg-gray-200 shadow-lg">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between border-b border-gray-400 bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">상품 정보입력</span>
              <button
                onClick={handleCancel}
                className="text-white hover:text-gray-200"
              >
                ✕
              </button>
            </div>

            {/* 모달 내용 */}
            <div className="bg-[#F0EDE4] p-4">
              <fieldset className="rounded border border-gray-400 p-3">
                <legend className="px-2 text-sm text-blue-700">상품정보</legend>
                <div className="grid grid-cols-[80px_1fr_80px_1fr] gap-2 text-sm">
                  <label className="py-1 text-right">코드:</label>
                  <input
                    type="text"
                    value={editForm.code}
                    onChange={(e) => setEditForm({ ...editForm, code: e.target.value })}
                    className="w-24 border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">품목명:</label>
                  <input
                    type="text"
                    value={editForm.productName}
                    onChange={(e) => setEditForm({ ...editForm, productName: e.target.value })}
                    className="w-full border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">규격:</label>
                  <input
                    type="text"
                    value={editForm.spec}
                    onChange={(e) => setEditForm({ ...editForm, spec: e.target.value })}
                    className="w-32 border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">상세규격:</label>
                  <input
                    type="text"
                    value={editForm.detailSpec}
                    onChange={(e) => setEditForm({ ...editForm, detailSpec: e.target.value })}
                    className="w-32 border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">재고단위:</label>
                  <select
                    value={editForm.stockUnit}
                    onChange={(e) => setEditForm({ ...editForm, stockUnit: e.target.value })}
                    className="w-24 border border-gray-400 px-2 py-1"
                  >
                    {STOCK_UNITS.map((unit) => (
                      <option key={unit} value={unit}>{unit}</option>
                    ))}
                  </select>

                  <label className="py-1 text-right">적정재고:</label>
                  <input
                    type="number"
                    value={editForm.properStock}
                    onChange={(e) => setEditForm({ ...editForm, properStock: Number(e.target.value) })}
                    className="w-24 border border-gray-400 px-2 py-1 text-right"
                  />
                </div>
              </fieldset>

              <fieldset className="mt-3 rounded border border-gray-400 p-3">
                <legend className="px-2 text-sm text-blue-700">가격정보</legend>
                <div className="grid grid-cols-[80px_1fr_80px_1fr] gap-2 text-sm">
                  <label className="py-1 text-right">입가:</label>
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      value={editForm.purchasePrice}
                      onChange={(e) => setEditForm({ ...editForm, purchasePrice: Number(e.target.value) })}
                      className="w-28 border border-gray-400 px-2 py-1 text-right"
                    />
                    <span>원</span>
                  </div>

                  <label className="py-1 text-right">도매가:</label>
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      value={editForm.wholesalePrice}
                      onChange={(e) => setEditForm({ ...editForm, wholesalePrice: Number(e.target.value) })}
                      className="w-28 border border-gray-400 px-2 py-1 text-right"
                    />
                    <span>원</span>
                  </div>

                  <label className="py-1 text-right">소매가:</label>
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      value={editForm.retailPrice}
                      onChange={(e) => setEditForm({ ...editForm, retailPrice: Number(e.target.value) })}
                      className="w-28 border border-gray-400 px-2 py-1 text-right"
                    />
                    <span>원</span>
                  </div>

                  <label className="py-1 text-right">상품분류:</label>
                  <select
                    value={editForm.category}
                    onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                    className="w-32 border border-gray-400 px-2 py-1"
                  >
                    <option value="">선택</option>
                    {PRODUCT_CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
              </fieldset>

              <fieldset className="mt-3 rounded border border-gray-400 p-3">
                <legend className="px-2 text-sm text-blue-700">메모</legend>
                <textarea
                  value={editForm.memo}
                  onChange={(e) => setEditForm({ ...editForm, memo: e.target.value })}
                  className="h-16 w-full border border-gray-400 px-2 py-1 text-sm"
                  placeholder="상품에 대한 메모를 입력하세요"
                />
              </fieldset>

              <p className="mt-3 text-sm text-gray-600">
                새로운 상품의 정보를 등록합니다.
              </p>
            </div>

            {/* 모달 푸터 - 이지판매재고관리 스타일 */}
            <div className="flex justify-end gap-2 border-t border-gray-400 bg-gray-200 px-4 py-3">
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
                저 장
              </button>
              <button
                onClick={handleCancel}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
              >
                취 소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 구성상품 모달 */}
      {showCompositeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-[600px] rounded bg-gray-200 shadow-lg">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between border-b border-gray-400 bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">구성상품 설정</span>
              <button
                onClick={() => setShowCompositeModal(false)}
                className="text-white hover:text-gray-200"
              >
                ✕
              </button>
            </div>

            {/* 모달 내용 */}
            <div className="bg-[#F0EDE4] p-4">
              <div className="mb-3 text-sm">
                <span className="font-medium">선택된 상품:</span>{" "}
                {selectedRow !== null && filteredProducts[selectedRow]?.productName}
              </div>

              <fieldset className="rounded border border-gray-400 p-3">
                <legend className="px-2 text-sm text-blue-700">구성상품 목록</legend>
                <div className="h-48 overflow-auto bg-white">
                  <table className="w-full border-collapse text-sm">
                    <thead className="sticky top-0 bg-[#E8E4D9]">
                      <tr>
                        <th className="border border-gray-300 px-2 py-1 font-normal">코드</th>
                        <th className="border border-gray-300 px-2 py-1 font-normal">품목명</th>
                        <th className="border border-gray-300 px-2 py-1 font-normal">수량</th>
                        <th className="border border-gray-300 px-2 py-1 font-normal">삭제</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td colSpan={4} className="border border-gray-300 px-2 py-4 text-center text-gray-400">
                          구성상품이 없습니다. 아래에서 추가하세요.
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </fieldset>

              <fieldset className="mt-3 rounded border border-gray-400 p-3">
                <legend className="px-2 text-sm text-blue-700">구성상품 추가</legend>
                <div className="flex items-center gap-2 text-sm">
                  <label>상품:</label>
                  <select className="w-48 border border-gray-400 px-2 py-1">
                    <option value="">선택</option>
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>{p.productName}</option>
                    ))}
                  </select>
                  <label>수량:</label>
                  <input type="number" defaultValue={1} className="w-16 border border-gray-400 px-2 py-1 text-right" />
                  <button className="rounded border border-gray-400 bg-gray-100 px-3 py-1 hover:bg-gray-200">
                    추가
                  </button>
                </div>
              </fieldset>

              <p className="mt-3 text-sm text-gray-600">
                하나의 상품을 판매할 때 여러 상품이 함께 출고되도록 구성합니다.
              </p>
            </div>

            {/* 모달 푸터 */}
            <div className="flex justify-end gap-2 border-t border-gray-400 bg-gray-200 px-4 py-3">
              <button
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
              >
                저 장
              </button>
              <button
                onClick={() => setShowCompositeModal(false)}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
              >
                취 소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
