"use client";

import React, { useState, useCallback, useEffect, useRef } from "react";
import {
    Calendar,
    Search,
    Plus,
    Edit2,
    Trash2,
    Save,
    X,
    FileText,
    Receipt,
    MessageSquare,
    Banknote,
    Building2,
    CreditCard,
    FileCheck,
    Percent,
    Loader2,
} from "lucide-react";
import { Product } from "@/lib/api/erp-api";
import { api } from "@/lib/api";
import { useERPData } from "@/contexts/ERPDataContext";
import type { Customer as ContextCustomer, Product as ContextProduct } from "@/contexts/ERPDataContext";

// ERPProduct 타입 별칭
type ERPProduct = Product;
import { useERP, useWindowContextOptional } from "@/components/erp/ERPContext";
import TransactionStatementModal from "@/components/erp/windows/documents/TransactionStatementModal";
import TaxInvoiceModal from "@/components/erp/windows/documents/TaxInvoiceModal";

// 사원/상품/은행/카드 데이터는 컴포넌트 내 useEffect에서 API로 로드

// ==================== Types ====================
interface SalesItem {
    id: string;
    gubun: string; // 구분
    productName: string; // 상품명
    spec: string; // 규격
    detailSpec: string; // 상세규격
    unit: string; // 단위
    quantity: number; // 수량
    unitPrice: number; // 단가
    supplyAmount: number; // 공급가액
    memo: string; // 메모
    vatAmount: number; // 부가세액
}

interface CustomerInfo {
    id: string; // 고객 ID (필수)
    code: string;
    name: string;
    manager: string; // 담당사원
    vatType: string; // 부가세별도/포함
    vatRate: number; // 부가세율
    receivable: number; // 미수금액
    payable: number; // 미지급액
    creditLimit: number; // 신용한도
    fax: string;
    phone: string;
    lastTransaction: string;
}

interface ProductInfo {
    code: string;
    name: string;
    stock: number; // 보유재고
    lastSales: number; // 최종매출
    lastPrice: number; // 최종단가
    optimalStock: number; // 적정재고
}

interface PaymentInfo {
    type: "cash" | "bank" | "bill" | "card";
    amount: number;
    details: Record<string, string | number>;
}

// ==================== Data ====================
// 고객 데이터는 ERPDataContext에서 로드됨
// 사원/은행/카드 데이터는 컴포넌트 내 useEffect에서 API로 로드

// ==================== Sub Components ====================

// 고객 검색 팝업
function CustomerSearchPopup({
    isOpen,
    onClose,
    onSelect,
    searchTerm,
}: {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (customer: CustomerInfo) => void;
    searchTerm: string;
}) {
    const [localSearch, setLocalSearch] = useState(searchTerm);
    const { customers: contextCustomers, searchCustomers, customersLoading: loading } = useERPData();

    // Context 고객 데이터를 CustomerInfo로 변환하여 필터링
    const customers: CustomerInfo[] = React.useMemo(() => {
        const source = localSearch.length >= 1
            ? searchCustomers(localSearch)
            : contextCustomers;
        return source.map((c: ContextCustomer) => ({
            id: c.id,
            code: c.code || '',
            name: c.name,
            manager: c.contact_person || '',
            vatType: '부가세별도',
            vatRate: 10,
            receivable: c.current_receivable || 0,
            payable: 0,
            creditLimit: parseFloat(c.credit_limit || '0') || 0,
            fax: c.fax || '',
            phone: c.phone || '',
            lastTransaction: '',
        }));
    }, [localSearch, contextCustomers, searchCustomers]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
            <div className="w-[500px] rounded-lg border bg-white shadow-xl">
                <div className="flex items-center justify-between border-b bg-blue-600 px-4 py-2 text-white">
                    <span className="font-medium">거래처 검색</span>
                    <button onClick={onClose} className="hover:bg-blue-700 rounded p-1">
                        <X className="h-4 w-4" />
                    </button>
                </div>
                <div className="p-4">
                    <div className="mb-3 flex gap-2">
                        <input
                            type="text"
                            value={localSearch}
                            onChange={(e) => setLocalSearch(e.target.value)}
                            placeholder="거래처명 또는 코드 검색..."
                            className="flex-1 rounded border px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                            autoFocus
                        />
                        <button className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
                            검색
                        </button>
                    </div>
                    {/* 고정 높이로 팝업 크기 변동 방지 */}
                    <div className="h-[300px] overflow-auto border rounded">
                        {loading ? (
                            <div className="flex items-center justify-center h-full">
                                <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                                <span className="ml-2 text-gray-500">로딩 중...</span>
                            </div>
                        ) : (
                            <table className="w-full text-sm">
                                <thead className="bg-gray-100 sticky top-0">
                                    <tr>
                                        <th className="px-3 py-2 text-left">코드</th>
                                        <th className="px-3 py-2 text-left">거래처명</th>
                                        <th className="px-3 py-2 text-left">담당자</th>
                                        <th className="px-3 py-2 text-right">미수금</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {customers.length === 0 ? (
                                        <tr>
                                            <td colSpan={4} className="px-3 py-8 text-center text-gray-500">
                                                고객 데이터가 없습니다
                                            </td>
                                        </tr>
                                    ) : (
                                        customers.map((customer) => (
                                            <tr
                                                key={customer.id}
                                                className="border-t hover:bg-blue-50 cursor-pointer"
                                                onClick={() => {
                                                    onSelect(customer);
                                                    onClose();
                                                }}
                                            >
                                                <td className="px-3 py-2">{customer.code}</td>
                                                <td className="px-3 py-2 font-medium">{customer.name}</td>
                                                <td className="px-3 py-2">{customer.manager}</td>
                                                <td className="px-3 py-2 text-right text-red-600">
                                                    {customer.receivable.toLocaleString()}
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

// 상품 추가 데이터 타입
interface ProductAddData {
    product: ProductInfo;
    quantity: number;
    unitPrice: number;
    memo: string;
}

// 대기 상품 타입 (다중 추가용)
interface PendingProduct {
    id: string;
    product: ProductInfo;
    quantity: number;
    unitPrice: number;
    memo: string;
}

// 상품 검색 및 추가 팝업 (다중 상품 추가 지원)
function ProductSearchPopup({
    isOpen,
    onClose,
    onSelect,
}: {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (data: ProductAddData[]) => void;
}) {
    const [search, setSearch] = useState("");
    const { products: contextProducts, searchProducts, productsLoading: loading, productsError: error } = useERPData();
    const [selectedProduct, setSelectedProduct] = useState<ProductInfo | null>(null);
    const [quantity, setQuantity] = useState(1);
    const [unitPrice, setUnitPrice] = useState(0);
    const [memo, setMemo] = useState("");
    const [pendingItems, setPendingItems] = useState<PendingProduct[]>([]);
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const dragOffset = useRef({ x: 0, y: 0 });
    const modalRef = useRef<HTMLDivElement>(null);

    // Context에서 상품 필터링 (ERPProduct 호환 형태로 변환)
    const products: ERPProduct[] = React.useMemo(() => {
        const source = search.length >= 1
            ? searchProducts(search)
            : contextProducts;
        return source.filter(p => p.is_active !== false).map((p: ContextProduct) => ({
            id: p.id,
            code: p.code || null,
            name: p.name,
            spec: p.specification || null,
            unit: p.unit || 'EA',
            category_id: p.category || null,
            purchase_price: String(p.purchase_price || 0),
            selling_price: String(p.selling_price || 0),
            safety_stock: p.stock_quantity || p.min_stock || 0,
            memo: p.memo || null,
            is_active: p.is_active,
            created_at: p.created_at,
            updated_at: p.updated_at || null,
        } as ERPProduct));
    }, [search, contextProducts, searchProducts]);

    // 모달 중앙 위치 설정
    useEffect(() => {
        if (isOpen && modalRef.current) {
            const modalWidth = modalRef.current.offsetWidth;
            const modalHeight = modalRef.current.offsetHeight;
            setPosition({
                x: (window.innerWidth - modalWidth) / 2,
                y: (window.innerHeight - modalHeight) / 2,
            });
        }
    }, [isOpen]);

    // 드래그 핸들러
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (isDragging) {
                setPosition({
                    x: e.clientX - dragOffset.current.x,
                    y: e.clientY - dragOffset.current.y,
                });
            }
        };
        const handleMouseUp = () => setIsDragging(false);

        if (isDragging) {
            document.addEventListener("mousemove", handleMouseMove);
            document.addEventListener("mouseup", handleMouseUp);
        }
        return () => {
            document.removeEventListener("mousemove", handleMouseMove);
            document.removeEventListener("mouseup", handleMouseUp);
        };
    }, [isDragging]);

    const handleMouseDown = (e: React.MouseEvent) => {
        if (modalRef.current) {
            dragOffset.current = {
                x: e.clientX - position.x,
                y: e.clientY - position.y,
            };
            setIsDragging(true);
        }
    };

    // ERPProduct를 ProductInfo로 변환
    const convertToProductInfo = (p: ERPProduct): ProductInfo => ({
        code: p.code || "",
        name: p.name || "",
        stock: p.safety_stock ?? 0, // safety_stock을 현재 재고로 사용
        lastSales: 0,
        lastPrice: Number(p.selling_price) || 0,
        optimalStock: p.safety_stock ?? 0,
    });

    // 상품 선택 시 초기값 설정
    const handleSelectProduct = (p: ERPProduct) => {
        const product = convertToProductInfo(p);
        setSelectedProduct(product);
        setUnitPrice(product.lastPrice);
        setQuantity(1);
        setMemo("");
    };

    // 대기 목록에 추가 버튼 클릭
    const handleAddToPending = () => {
        if (!selectedProduct) return;
        if (quantity <= 0) {
            alert("수량을 입력해주세요.");
            return;
        }
        if (unitPrice <= 0) {
            alert("금액을 입력해주세요.");
            return;
        }
        // 대기 목록에 추가
        setPendingItems([
            ...pendingItems,
            {
                id: `pending-${Date.now()}`,
                product: selectedProduct,
                quantity,
                unitPrice,
                memo,
            },
        ]);
        // 입력 초기화 (계속 추가할 수 있도록)
        setSelectedProduct(null);
        setQuantity(1);
        setUnitPrice(0);
        setMemo("");
    };

    // 대기 목록에서 삭제
    const handleRemoveFromPending = (id: string) => {
        setPendingItems(pendingItems.filter((item) => item.id !== id));
    };

    // 확인 버튼 클릭 - 모든 대기 상품을 배열로 한 번에 전달
    const handleConfirm = () => {
        // 모든 상품을 배열로 수집
        const allProducts: ProductAddData[] = [];

        // 대기 목록 상품들
        for (const item of pendingItems) {
            allProducts.push({
                product: item.product,
                quantity: item.quantity,
                unitPrice: item.unitPrice,
                memo: item.memo,
            });
        }

        // 현재 선택된 상품도 추가
        if (selectedProduct && quantity > 0 && unitPrice > 0) {
            allProducts.push({
                product: selectedProduct,
                quantity,
                unitPrice,
                memo,
            });
        }

        // 추가할 상품이 있으면 한 번에 전달
        if (allProducts.length > 0) {
            onSelect(allProducts);
        }

        // 모두 초기화하고 닫기
        setSelectedProduct(null);
        setQuantity(1);
        setUnitPrice(0);
        setMemo("");
        setSearch("");
        setPendingItems([]);
        onClose();
    };

    // 취소 시 초기화
    const handleClose = () => {
        setSelectedProduct(null);
        setQuantity(1);
        setUnitPrice(0);
        setMemo("");
        setSearch("");
        setPendingItems([]);
        onClose();
    };

    if (!isOpen) return null;

    const supplyAmount = quantity * unitPrice;

    return (
        <div className="fixed inset-0 z-50 bg-black/30">
            <div
                ref={modalRef}
                className="absolute w-[650px] rounded-lg border bg-white shadow-xl"
                style={{
                    left: position.x,
                    top: position.y,
                }}
            >
                <div
                    className="flex cursor-move items-center justify-between border-b bg-green-600 px-4 py-2 text-white select-none"
                    onMouseDown={handleMouseDown}
                >
                    <span className="font-medium">상품 추가 (다중 선택)</span>
                    <button
                        onClick={handleClose}
                        className="hover:bg-green-700 rounded p-1"
                        onMouseDown={(e) => e.stopPropagation()}
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>
                <div className="p-4">
                    {/* 상품 검색 영역 */}
                    <div className="mb-3 flex gap-2">
                        <input
                            type="text"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            placeholder="상품명 또는 코드 검색..."
                            className="flex-1 rounded border px-3 py-2 text-sm focus:border-green-500 focus:outline-none"
                            autoFocus
                        />
                        <button
                            onClick={() => { /* search is reactive via useMemo */ }}
                            className="rounded bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700"
                        >
                            검색
                        </button>
                    </div>

                    {/* 상품 목록 테이블 - 고정 높이 */}
                    <div className="h-[200px] overflow-auto border rounded mb-4">
                        {loading ? (
                            <div className="flex items-center justify-center h-full">
                                <Loader2 className="h-6 w-6 animate-spin text-green-600" />
                                <span className="ml-2 text-sm text-gray-500">로딩 중...</span>
                            </div>
                        ) : error ? (
                            <div className="flex items-center justify-center h-full text-red-500 text-sm">
                                {error}
                            </div>
                        ) : products.length === 0 ? (
                            <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                                {search ? "검색 결과가 없습니다." : "등록된 상품이 없습니다."}
                            </div>
                        ) : (
                            <table className="w-full text-sm">
                                <thead className="bg-gray-100 sticky top-0">
                                    <tr>
                                        <th className="px-3 py-2 text-left">코드</th>
                                        <th className="px-3 py-2 text-left">상품명</th>
                                        <th className="px-3 py-2 text-right">안전재고</th>
                                        <th className="px-3 py-2 text-right">판매단가</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {products.map((p) => (
                                        <tr
                                            key={p.id}
                                            className={`border-t cursor-pointer ${
                                                selectedProduct?.code === p.code
                                                    ? "bg-green-100"
                                                    : "hover:bg-green-50"
                                            }`}
                                            onClick={() => handleSelectProduct(p)}
                                        >
                                            <td className="px-3 py-2">{p.code}</td>
                                            <td className="px-3 py-2 font-medium">{p.name}</td>
                                            <td className="px-3 py-2 text-right text-blue-600 font-medium">
                                                {p.safety_stock}
                                            </td>
                                            <td className="px-3 py-2 text-right">
                                                {Number(p.selling_price).toLocaleString()}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>

                    {/* 선택된 상품 정보 및 입력 영역 */}
                    <div className="border rounded p-3 bg-gray-50">
                        <div className="text-sm font-medium text-green-700 mb-3">
                            ■ 선택된 상품: {selectedProduct ? (
                                <span className="text-black">{selectedProduct.name}</span>
                            ) : (
                                <span className="text-gray-400">(상품을 선택하세요)</span>
                            )}
                        </div>

                        {selectedProduct && (
                            <div className="space-y-3">
                                {/* 재고 정보 */}
                                <div className="flex items-center gap-4 text-sm">
                                    <span className="text-gray-600">안전재고:</span>
                                    <span className="font-medium text-blue-600">{selectedProduct.stock}개</span>
                                    <span className="text-gray-600 ml-4">적정재고:</span>
                                    <span className="font-medium">{selectedProduct.optimalStock}개</span>
                                </div>

                                {/* 입력 필드들 */}
                                <div className="grid grid-cols-3 gap-3">
                                    <div>
                                        <label className="block text-xs text-gray-600 mb-1">수량</label>
                                        <input
                                            type="number"
                                            value={quantity}
                                            onChange={(e) => setQuantity(Number(e.target.value))}
                                            className="w-full rounded border px-3 py-2 text-sm text-right focus:border-green-500 focus:outline-none"
                                            min={1}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs text-gray-600 mb-1">단가</label>
                                        <input
                                            type="number"
                                            value={unitPrice}
                                            onChange={(e) => setUnitPrice(Number(e.target.value))}
                                            className="w-full rounded border px-3 py-2 text-sm text-right focus:border-green-500 focus:outline-none"
                                            min={0}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs text-gray-600 mb-1">공급가액</label>
                                        <div className="w-full rounded border bg-gray-100 px-3 py-2 text-sm text-right font-medium text-blue-600">
                                            {supplyAmount.toLocaleString()}
                                        </div>
                                    </div>
                                </div>

                                {/* 메모 입력 */}
                                <div>
                                    <label className="block text-xs text-gray-600 mb-1">메모 (공급가액 우측에 표시됨)</label>
                                    <input
                                        type="text"
                                        value={memo}
                                        onChange={(e) => setMemo(e.target.value)}
                                        placeholder="메모를 입력하세요..."
                                        className="w-full rounded border px-3 py-2 text-sm focus:border-green-500 focus:outline-none"
                                    />
                                </div>
                            </div>
                        )}
                    </div>

                    {/* 대기 상품 목록 */}
                    {pendingItems.length > 0 && (
                        <div className="border rounded p-3 bg-blue-50 mt-4">
                            <div className="text-sm font-medium text-blue-700 mb-2">
                                ■ 추가 대기 상품 ({pendingItems.length}개)
                            </div>
                            <div className="max-h-[120px] overflow-auto">
                                <table className="w-full text-sm">
                                    <thead className="bg-blue-100 sticky top-0">
                                        <tr>
                                            <th className="px-2 py-1 text-left">상품명</th>
                                            <th className="px-2 py-1 text-right">수량</th>
                                            <th className="px-2 py-1 text-right">단가</th>
                                            <th className="px-2 py-1 text-right">공급가액</th>
                                            <th className="px-2 py-1 text-center w-8"></th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {pendingItems.map((item) => (
                                            <tr key={item.id} className="border-t border-blue-200">
                                                <td className="px-2 py-1">{item.product.name}</td>
                                                <td className="px-2 py-1 text-right">{item.quantity}</td>
                                                <td className="px-2 py-1 text-right">
                                                    {item.unitPrice.toLocaleString()}
                                                </td>
                                                <td className="px-2 py-1 text-right font-medium text-blue-600">
                                                    {(item.quantity * item.unitPrice).toLocaleString()}
                                                </td>
                                                <td className="px-2 py-1 text-center">
                                                    <button
                                                        onClick={() => handleRemoveFromPending(item.id)}
                                                        className="text-red-500 hover:text-red-700"
                                                        title="삭제"
                                                    >
                                                        <X className="h-4 w-4" />
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                            <div className="mt-2 text-right text-sm font-medium text-blue-800">
                                합계: {pendingItems.reduce((sum, item) => sum + item.quantity * item.unitPrice, 0).toLocaleString()}원
                            </div>
                        </div>
                    )}

                    {/* 하단 버튼 */}
                    <div className="flex justify-between items-center mt-4">
                        <div className="text-xs text-gray-500">
                            * 상품을 선택하고 [추가] 버튼으로 대기 목록에 넣은 후 [확인]으로 완료
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={handleAddToPending}
                                disabled={!selectedProduct}
                                className={`rounded px-4 py-2 text-sm text-white ${
                                    selectedProduct
                                        ? "bg-blue-600 hover:bg-blue-700"
                                        : "bg-gray-400 cursor-not-allowed"
                                }`}
                            >
                                + 추가
                            </button>
                            <button
                                onClick={handleConfirm}
                                disabled={pendingItems.length === 0 && !selectedProduct}
                                className={`rounded px-6 py-2 text-sm text-white ${
                                    pendingItems.length > 0 || selectedProduct
                                        ? "bg-green-600 hover:bg-green-700"
                                        : "bg-gray-400 cursor-not-allowed"
                                }`}
                            >
                                확인 {pendingItems.length > 0 && `(${pendingItems.length}개)`}
                            </button>
                            <button
                                onClick={handleClose}
                                className="rounded bg-gray-200 px-6 py-2 text-sm hover:bg-gray-300"
                            >
                                취소
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// 상품 수정 팝업 (더블클릭 시 표시)
function ItemEditPopup({
    isOpen,
    onClose,
    item,
    onSave,
    vatRate,
}: {
    isOpen: boolean;
    onClose: () => void;
    item: SalesItem | null;
    onSave: (item: SalesItem) => void;
    vatRate: number;
}) {
    const [editedItem, setEditedItem] = useState<SalesItem | null>(null);
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const dragOffset = useRef({ x: 0, y: 0 });
    const modalRef = useRef<HTMLDivElement>(null);

    // 아이템이 변경되면 로컬 상태 업데이트
    useEffect(() => {
        if (item) {
            setEditedItem({ ...item });
        }
    }, [item]);

    // 모달 열릴 때 중앙 위치
    useEffect(() => {
        if (isOpen && modalRef.current) {
            const modalWidth = modalRef.current.offsetWidth;
            const modalHeight = modalRef.current.offsetHeight;
            setPosition({
                x: (window.innerWidth - modalWidth) / 2,
                y: (window.innerHeight - modalHeight) / 2,
            });
        }
    }, [isOpen]);

    // 드래그 핸들러
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (isDragging) {
                setPosition({
                    x: e.clientX - dragOffset.current.x,
                    y: e.clientY - dragOffset.current.y,
                });
            }
        };
        const handleMouseUp = () => setIsDragging(false);

        if (isDragging) {
            document.addEventListener("mousemove", handleMouseMove);
            document.addEventListener("mouseup", handleMouseUp);
        }
        return () => {
            document.removeEventListener("mousemove", handleMouseMove);
            document.removeEventListener("mouseup", handleMouseUp);
        };
    }, [isDragging]);

    const handleMouseDown = (e: React.MouseEvent) => {
        if (modalRef.current) {
            dragOffset.current = {
                x: e.clientX - position.x,
                y: e.clientY - position.y,
            };
            setIsDragging(true);
        }
    };

    // 필드 변경 핸들러
    const handleChange = (field: keyof SalesItem, value: string | number) => {
        if (!editedItem) return;
        const updated = { ...editedItem, [field]: value };
        if (field === "quantity" || field === "unitPrice") {
            updated.supplyAmount = updated.quantity * updated.unitPrice;
            updated.vatAmount = Math.round(updated.supplyAmount * (vatRate / 100));
        }
        setEditedItem(updated);
    };

    // 저장 핸들러
    const handleSave = () => {
        if (!editedItem) return;
        onSave(editedItem);
        onClose();
    };

    if (!isOpen || !editedItem) return null;

    return (
        <div className="fixed inset-0 z-50 bg-black/30">
            <div
                ref={modalRef}
                className="absolute w-[500px] rounded-lg border bg-white shadow-xl"
                style={{ left: position.x, top: position.y }}
            >
                <div
                    className="flex cursor-move select-none items-center justify-between border-b bg-teal-600 px-4 py-2 text-white"
                    onMouseDown={handleMouseDown}
                >
                    <span className="font-medium">상품 수정</span>
                    <button
                        onClick={onClose}
                        className="hover:bg-teal-700 rounded p-1"
                        onMouseDown={(e) => e.stopPropagation()}
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>
                <div className="p-4 space-y-4">
                    {/* 상품명 (읽기 전용) */}
                    <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">상품명</label>
                        <div className="rounded border bg-gray-100 px-3 py-2 text-sm font-medium">
                            {editedItem.productName}
                        </div>
                    </div>

                    {/* 구분 */}
                    <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">구분</label>
                        <select
                            value={editedItem.gubun}
                            onChange={(e) => handleChange("gubun", e.target.value)}
                            className="w-full rounded border px-3 py-2 text-sm focus:border-teal-500 focus:outline-none"
                        >
                            <option value="판매">판매</option>
                            <option value="반품">반품</option>
                            <option value="교환">교환</option>
                        </select>
                    </div>

                    {/* 규격 / 상세규격 */}
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">규격</label>
                            <input
                                type="text"
                                value={editedItem.spec}
                                onChange={(e) => handleChange("spec", e.target.value)}
                                className="w-full rounded border px-3 py-2 text-sm focus:border-teal-500 focus:outline-none"
                                placeholder="규격 입력..."
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">상세규격</label>
                            <input
                                type="text"
                                value={editedItem.detailSpec}
                                onChange={(e) => handleChange("detailSpec", e.target.value)}
                                className="w-full rounded border px-3 py-2 text-sm focus:border-teal-500 focus:outline-none"
                                placeholder="상세규격 입력..."
                            />
                        </div>
                    </div>

                    {/* 단위 / 수량 */}
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">단위</label>
                            <select
                                value={editedItem.unit}
                                onChange={(e) => handleChange("unit", e.target.value)}
                                className="w-full rounded border px-3 py-2 text-sm focus:border-teal-500 focus:outline-none"
                            >
                                <option value="EA">EA</option>
                                <option value="SET">SET</option>
                                <option value="BOX">BOX</option>
                                <option value="M">M</option>
                                <option value="KG">KG</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">수량</label>
                            <input
                                type="number"
                                value={editedItem.quantity}
                                onChange={(e) => handleChange("quantity", Number(e.target.value))}
                                className="w-full rounded border px-3 py-2 text-sm text-right focus:border-teal-500 focus:outline-none"
                                min={1}
                            />
                        </div>
                    </div>

                    {/* 단가 / 공급가액 */}
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">단가</label>
                            <input
                                type="number"
                                value={editedItem.unitPrice}
                                onChange={(e) => handleChange("unitPrice", Number(e.target.value))}
                                className="w-full rounded border px-3 py-2 text-sm text-right focus:border-teal-500 focus:outline-none"
                                min={0}
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">공급가액</label>
                            <div className="rounded border bg-gray-100 px-3 py-2 text-sm text-right font-medium text-blue-600">
                                {editedItem.supplyAmount.toLocaleString()}
                            </div>
                        </div>
                    </div>

                    {/* 부가세액 */}
                    <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">부가세액</label>
                        <div className="rounded border bg-gray-100 px-3 py-2 text-sm text-right font-medium">
                            {editedItem.vatAmount.toLocaleString()}
                        </div>
                    </div>

                    {/* 메모 */}
                    <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">메모</label>
                        <input
                            type="text"
                            value={editedItem.memo}
                            onChange={(e) => handleChange("memo", e.target.value)}
                            className="w-full rounded border px-3 py-2 text-sm focus:border-teal-500 focus:outline-none"
                            placeholder="메모 입력..."
                        />
                    </div>

                    {/* 버튼 */}
                    <div className="flex justify-end gap-2 pt-2">
                        <button
                            onClick={handleSave}
                            className="rounded bg-teal-600 px-6 py-2 text-sm text-white hover:bg-teal-700"
                        >
                            저장
                        </button>
                        <button
                            onClick={onClose}
                            className="rounded bg-gray-200 px-6 py-2 text-sm hover:bg-gray-300"
                        >
                            취소
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

// 현금 결제 팝업
function CashPaymentPopup({
    isOpen,
    onClose,
    onSave,
    maxAmount,
}: {
    isOpen: boolean;
    onClose: () => void;
    onSave: (payment: PaymentInfo) => void;
    maxAmount: number;
}) {
    const [gubun, setGubun] = useState("현금입금");
    const [amount, setAmount] = useState(0);
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const dragOffset = useRef({ x: 0, y: 0 });
    const modalRef = useRef<HTMLDivElement>(null);

    // 모달 열릴 때 중앙 위치
    useEffect(() => {
        if (isOpen && modalRef.current) {
            const modalWidth = modalRef.current.offsetWidth;
            const modalHeight = modalRef.current.offsetHeight;
            setPosition({
                x: (window.innerWidth - modalWidth) / 2,
                y: (window.innerHeight - modalHeight) / 2,
            });
        }
    }, [isOpen]);

    // 드래그 핸들러
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (isDragging) {
                setPosition({
                    x: e.clientX - dragOffset.current.x,
                    y: e.clientY - dragOffset.current.y,
                });
            }
        };
        const handleMouseUp = () => setIsDragging(false);

        if (isDragging) {
            document.addEventListener("mousemove", handleMouseMove);
            document.addEventListener("mouseup", handleMouseUp);
        }
        return () => {
            document.removeEventListener("mousemove", handleMouseMove);
            document.removeEventListener("mouseup", handleMouseUp);
        };
    }, [isDragging]);

    const handleMouseDown = (e: React.MouseEvent) => {
        dragOffset.current = {
            x: e.clientX - position.x,
            y: e.clientY - position.y,
        };
        setIsDragging(true);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 bg-black/30">
            <div
                ref={modalRef}
                className="absolute w-[350px] rounded-lg border bg-white shadow-xl"
                style={{ left: position.x, top: position.y }}
            >
                <div
                    className="flex cursor-move items-center justify-between border-b bg-amber-500 px-4 py-2 text-white select-none"
                    onMouseDown={handleMouseDown}
                >
                    <span className="font-medium">현금 결제</span>
                    <button
                        onClick={onClose}
                        className="hover:bg-amber-600 rounded p-1"
                        onMouseDown={(e) => e.stopPropagation()}
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>
                <div className="p-4 space-y-3">
                    <div className="text-sm font-medium text-blue-600">결제정보</div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">구분:</label>
                        <select
                            value={gubun}
                            onChange={(e) => setGubun(e.target.value)}
                            className="col-span-2 rounded border px-2 py-1.5 text-sm"
                        >
                            <option>현금입금</option>
                            <option>현금출금</option>
                        </select>
                    </div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">금액:</label>
                        <div className="col-span-2 flex gap-1">
                            <input
                                type="number"
                                value={amount}
                                onChange={(e) => setAmount(Number(e.target.value))}
                                className="w-[140px] rounded border px-2 py-1.5 text-sm text-right"
                            />
                            <button
                                onClick={() => setAmount(maxAmount)}
                                className="rounded bg-blue-500 px-2 py-1.5 text-xs text-white hover:bg-blue-600 whitespace-nowrap"
                            >
                                전액
                            </button>
                        </div>
                    </div>
                    <div className="flex justify-end gap-2 pt-2 border-t">
                        <button className="text-sm text-blue-600 hover:underline">관련항목&gt;&gt;</button>
                        <button
                            onClick={() => {
                                onSave({ type: "cash", amount, details: { gubun } });
                                onClose();
                            }}
                            className="rounded bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
                        >
                            저 장
                        </button>
                        <button
                            onClick={onClose}
                            className="rounded bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
                        >
                            취 소
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

// 은행 결제 팝업
function BankPaymentPopup({
    isOpen,
    onClose,
    onSave,
    maxAmount,
}: {
    isOpen: boolean;
    onClose: () => void;
    onSave: (payment: PaymentInfo) => void;
    maxAmount: number;
}) {
    const [gubun, setGubun] = useState("은행으로 출금");
    const [fromAccount, setFromAccount] = useState("");
    const [toAccount, setToAccount] = useState("");
    const [amount, setAmount] = useState(0);
    const [fee, setFee] = useState(0);
    const [selectedBank, setSelectedBank] = useState<{ code: string; name: string; accountNo: string; balance: number } | null>(null);
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const dragOffset = useRef({ x: 0, y: 0 });
    const modalRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (isOpen && modalRef.current) {
            const modalWidth = modalRef.current.offsetWidth;
            const modalHeight = modalRef.current.offsetHeight;
            setPosition({
                x: (window.innerWidth - modalWidth) / 2,
                y: (window.innerHeight - modalHeight) / 2,
            });
        }
    }, [isOpen]);

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (isDragging) {
                setPosition({
                    x: e.clientX - dragOffset.current.x,
                    y: e.clientY - dragOffset.current.y,
                });
            }
        };
        const handleMouseUp = () => setIsDragging(false);

        if (isDragging) {
            document.addEventListener("mousemove", handleMouseMove);
            document.addEventListener("mouseup", handleMouseUp);
        }
        return () => {
            document.removeEventListener("mousemove", handleMouseMove);
            document.removeEventListener("mouseup", handleMouseUp);
        };
    }, [isDragging]);

    const handleMouseDown = (e: React.MouseEvent) => {
        dragOffset.current = {
            x: e.clientX - position.x,
            y: e.clientY - position.y,
        };
        setIsDragging(true);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 bg-black/30">
            <div
                ref={modalRef}
                className="absolute w-[400px] rounded-lg border bg-white shadow-xl"
                style={{ left: position.x, top: position.y }}
            >
                <div
                    className="flex cursor-move items-center justify-between border-b bg-blue-500 px-4 py-2 text-white select-none"
                    onMouseDown={handleMouseDown}
                >
                    <span className="font-medium">계좌 결제</span>
                    <button
                        onClick={onClose}
                        className="hover:bg-blue-600 rounded p-1"
                        onMouseDown={(e) => e.stopPropagation()}
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>
                <div className="p-4 space-y-3">
                    <div className="text-sm font-medium text-blue-600">결제정보</div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">구분:</label>
                        <select
                            value={gubun}
                            onChange={(e) => setGubun(e.target.value)}
                            className="col-span-2 rounded border px-2 py-1.5 text-sm"
                        >
                            <option>은행으로 출금</option>
                            <option>은행으로 입금</option>
                        </select>
                    </div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">출금계좌:</label>
                        <input
                            type="text"
                            value={fromAccount}
                            onChange={(e) => setFromAccount(e.target.value)}
                            className="col-span-2 rounded border px-2 py-1.5 text-sm"
                        />
                    </div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">입금계좌:</label>
                        <div className="col-span-2 flex gap-1">
                            <input
                                type="text"
                                value={toAccount}
                                onChange={(e) => setToAccount(e.target.value)}
                                className="flex-1 rounded border px-2 py-1.5 text-sm"
                            />
                            <button className="rounded bg-gray-200 px-2 py-1.5 text-xs hover:bg-gray-300">
                                계좌검색
                            </button>
                        </div>
                    </div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">금액:</label>
                        <div className="col-span-2 flex gap-1">
                            <input
                                type="number"
                                value={amount}
                                onChange={(e) => setAmount(Number(e.target.value))}
                                className="w-[160px] rounded border px-2 py-1.5 text-sm text-right"
                            />
                            <button
                                onClick={() => setAmount(maxAmount)}
                                className="rounded bg-blue-500 px-2 py-1.5 text-xs text-white hover:bg-blue-600 whitespace-nowrap"
                            >
                                전액
                            </button>
                        </div>
                    </div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">수수료:</label>
                        <input
                            type="number"
                            value={fee}
                            onChange={(e) => setFee(Number(e.target.value))}
                            className="col-span-2 rounded border px-2 py-1.5 text-sm text-right"
                        />
                    </div>

                    <div className="text-sm font-medium text-blue-600 pt-2">계좌정보</div>
                    <div className="grid grid-cols-3 gap-2 items-center text-sm">
                        <label>계좌명:</label>
                        <span className="col-span-2">{selectedBank?.name || "-"}</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 items-center text-sm">
                        <label>계좌번호:</label>
                        <span className="col-span-2">{selectedBank?.accountNo || "-"}</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 items-center text-sm">
                        <label>잔 액:</label>
                        <span className="col-span-2">{selectedBank?.balance.toLocaleString() || "-"}</span>
                    </div>

                    <div className="flex justify-end gap-2 pt-2 border-t">
                        <button className="text-sm text-blue-600 hover:underline">관련항목&gt;&gt;</button>
                        <button
                            onClick={() => {
                                onSave({ type: "bank", amount, details: { gubun, fromAccount, toAccount, fee } });
                                onClose();
                            }}
                            className="rounded bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
                        >
                            저 장
                        </button>
                        <button
                            onClick={onClose}
                            className="rounded bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
                        >
                            취 소
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

// 어음 결제 팝업
function BillPaymentPopup({
    isOpen,
    onClose,
    onSave,
}: {
    isOpen: boolean;
    onClose: () => void;
    onSave: (payment: PaymentInfo) => void;
}) {
    const [gubun, setGubun] = useState("어음수취");
    const [billNo, setBillNo] = useState("");
    const [amount, setAmount] = useState(0);
    const [dueDate, setDueDate] = useState(new Date().toISOString().split("T")[0]);
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const dragOffset = useRef({ x: 0, y: 0 });
    const modalRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (isOpen && modalRef.current) {
            const modalWidth = modalRef.current.offsetWidth;
            const modalHeight = modalRef.current.offsetHeight;
            setPosition({
                x: (window.innerWidth - modalWidth) / 2,
                y: (window.innerHeight - modalHeight) / 2,
            });
        }
    }, [isOpen]);

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (isDragging) {
                setPosition({
                    x: e.clientX - dragOffset.current.x,
                    y: e.clientY - dragOffset.current.y,
                });
            }
        };
        const handleMouseUp = () => setIsDragging(false);

        if (isDragging) {
            document.addEventListener("mousemove", handleMouseMove);
            document.addEventListener("mouseup", handleMouseUp);
        }
        return () => {
            document.removeEventListener("mousemove", handleMouseMove);
            document.removeEventListener("mouseup", handleMouseUp);
        };
    }, [isDragging]);

    const handleMouseDown = (e: React.MouseEvent) => {
        dragOffset.current = {
            x: e.clientX - position.x,
            y: e.clientY - position.y,
        };
        setIsDragging(true);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 bg-black/30">
            <div
                ref={modalRef}
                className="absolute w-[350px] rounded-lg border bg-white shadow-xl"
                style={{ left: position.x, top: position.y }}
            >
                <div
                    className="flex cursor-move items-center justify-between border-b bg-purple-500 px-4 py-2 text-white select-none"
                    onMouseDown={handleMouseDown}
                >
                    <span className="font-medium">어음 결제</span>
                    <button
                        onClick={onClose}
                        className="hover:bg-purple-600 rounded p-1"
                        onMouseDown={(e) => e.stopPropagation()}
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>
                <div className="p-4 space-y-3">
                    <div className="text-sm font-medium text-blue-600">결제정보</div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">구분:</label>
                        <select
                            value={gubun}
                            onChange={(e) => setGubun(e.target.value)}
                            className="col-span-2 rounded border px-2 py-1.5 text-sm"
                        >
                            <option>어음수취</option>
                            <option>어음발행</option>
                        </select>
                    </div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">어음번호:</label>
                        <input
                            type="text"
                            value={billNo}
                            onChange={(e) => setBillNo(e.target.value)}
                            className="col-span-2 rounded border px-2 py-1.5 text-sm"
                        />
                    </div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">금액:</label>
                        <input
                            type="number"
                            value={amount}
                            onChange={(e) => setAmount(Number(e.target.value))}
                            className="col-span-2 rounded border px-2 py-1.5 text-sm text-right"
                        />
                    </div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">만기일:</label>
                        <input
                            type="date"
                            value={dueDate}
                            onChange={(e) => setDueDate(e.target.value)}
                            className="col-span-2 rounded border px-2 py-1.5 text-sm"
                        />
                    </div>
                    <div className="flex justify-end gap-2 pt-2 border-t">
                        <button className="text-sm text-blue-600 hover:underline">관련항목&gt;&gt;</button>
                        <button
                            onClick={() => {
                                onSave({ type: "bill", amount, details: { gubun, billNo, dueDate } });
                                onClose();
                            }}
                            className="rounded bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
                        >
                            저 장
                        </button>
                        <button
                            onClick={onClose}
                            className="rounded bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
                        >
                            취 소
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

// 카드 결제 팝업
function CardPaymentPopup({
    isOpen,
    onClose,
    onSave,
}: {
    isOpen: boolean;
    onClose: () => void;
    onSave: (payment: PaymentInfo) => void;
}) {
    const [gubun, setGubun] = useState("카드입금");
    const [cardType, setCardType] = useState("");
    const [amount, setAmount] = useState(0);
    const [approvalNo, setApprovalNo] = useState("");
    const [memberName, setMemberName] = useState("");
    const [paymentDate, setPaymentDate] = useState(new Date().toISOString().split("T")[0]);
    const [installment, setInstallment] = useState(1);
    const [feeRate, setFeeRate] = useState(0);
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const dragOffset = useRef({ x: 0, y: 0 });
    const modalRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (isOpen && modalRef.current) {
            const modalWidth = modalRef.current.offsetWidth;
            const modalHeight = modalRef.current.offsetHeight;
            setPosition({
                x: (window.innerWidth - modalWidth) / 2,
                y: (window.innerHeight - modalHeight) / 2,
            });
        }
    }, [isOpen]);

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (isDragging) {
                setPosition({
                    x: e.clientX - dragOffset.current.x,
                    y: e.clientY - dragOffset.current.y,
                });
            }
        };
        const handleMouseUp = () => setIsDragging(false);

        if (isDragging) {
            document.addEventListener("mousemove", handleMouseMove);
            document.addEventListener("mouseup", handleMouseUp);
        }
        return () => {
            document.removeEventListener("mousemove", handleMouseMove);
            document.removeEventListener("mouseup", handleMouseUp);
        };
    }, [isDragging]);

    const handleMouseDown = (e: React.MouseEvent) => {
        dragOffset.current = {
            x: e.clientX - position.x,
            y: e.clientY - position.y,
        };
        setIsDragging(true);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 bg-black/30">
            <div
                ref={modalRef}
                className="absolute w-[400px] rounded-lg border bg-white shadow-xl"
                style={{ left: position.x, top: position.y }}
            >
                <div
                    className="flex cursor-move items-center justify-between border-b bg-rose-500 px-4 py-2 text-white select-none"
                    onMouseDown={handleMouseDown}
                >
                    <span className="font-medium">카드 결제</span>
                    <button
                        onClick={onClose}
                        className="hover:bg-rose-600 rounded p-1"
                        onMouseDown={(e) => e.stopPropagation()}
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>
                <div className="p-4 space-y-3">
                    <div className="text-sm font-medium text-blue-600">결제정보</div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">구분:</label>
                        <select
                            value={gubun}
                            onChange={(e) => setGubun(e.target.value)}
                            className="col-span-2 rounded border px-2 py-1.5 text-sm"
                        >
                            <option>카드입금</option>
                            <option>카드출금</option>
                        </select>
                    </div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">카드종류:</label>
                        <div className="col-span-2 flex gap-1">
                            <input
                                type="text"
                                value={cardType}
                                onChange={(e) => setCardType(e.target.value)}
                                className="flex-1 rounded border px-2 py-1.5 text-sm"
                            />
                            <button className="rounded bg-gray-200 px-2 py-1.5 text-xs hover:bg-gray-300">
                                카드검색
                            </button>
                        </div>
                    </div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">금액:</label>
                        <input
                            type="number"
                            value={amount}
                            onChange={(e) => setAmount(Number(e.target.value))}
                            className="col-span-2 rounded border px-2 py-1.5 text-sm text-right"
                        />
                    </div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">승인번호:</label>
                        <input
                            type="text"
                            value={approvalNo}
                            onChange={(e) => setApprovalNo(e.target.value)}
                            className="col-span-2 rounded border px-2 py-1.5 text-sm"
                        />
                    </div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">회원명:</label>
                        <input
                            type="text"
                            value={memberName}
                            onChange={(e) => setMemberName(e.target.value)}
                            className="col-span-2 rounded border px-2 py-1.5 text-sm"
                        />
                    </div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">결제일자:</label>
                        <input
                            type="date"
                            value={paymentDate}
                            onChange={(e) => setPaymentDate(e.target.value)}
                            className="col-span-2 rounded border px-2 py-1.5 text-sm"
                        />
                    </div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">할부개월:</label>
                        <select
                            value={installment}
                            onChange={(e) => setInstallment(Number(e.target.value))}
                            className="col-span-2 rounded border px-2 py-1.5 text-sm"
                        >
                            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((m) => (
                                <option key={m} value={m}>
                                    {m} 개월
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="grid grid-cols-3 gap-2 items-center">
                        <label className="text-sm">수수료율:</label>
                        <div className="col-span-2 flex items-center gap-1">
                            <input
                                type="number"
                                value={feeRate}
                                onChange={(e) => setFeeRate(Number(e.target.value))}
                                step="0.1"
                                className="flex-1 rounded border px-2 py-1.5 text-sm text-right"
                            />
                            <span className="text-sm">%</span>
                        </div>
                    </div>
                    <div className="flex justify-end gap-2 pt-2 border-t">
                        <button className="text-sm text-blue-600 hover:underline">관련항목&gt;&gt;</button>
                        <button
                            onClick={() => {
                                onSave({
                                    type: "card",
                                    amount,
                                    details: { gubun, cardType, approvalNo, memberName, paymentDate, installment, feeRate },
                                });
                                onClose();
                            }}
                            className="rounded bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
                        >
                            저 장
                        </button>
                        <button
                            onClick={onClose}
                            className="rounded bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
                        >
                            취 소
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

// 메모 팝업
function MemoPopup({
    isOpen,
    onClose,
    memo,
    onSave,
}: {
    isOpen: boolean;
    onClose: () => void;
    memo: string;
    onSave: (memo: string) => void;
}) {
    const [activeTab, setActiveTab] = useState<"memo" | "transaction">("memo");
    const [localMemo, setLocalMemo] = useState(memo);
    const [transactionMemo, setTransactionMemo] = useState("");

    // 드래그 관련 상태
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const dragOffset = useRef({ x: 0, y: 0 });
    const modalRef = useRef<HTMLDivElement>(null);

    // 모달이 열릴 때 중앙에 위치
    useEffect(() => {
        if (isOpen && modalRef.current) {
            const modalWidth = modalRef.current.offsetWidth;
            const modalHeight = modalRef.current.offsetHeight;
            setPosition({
                x: (window.innerWidth - modalWidth) / 2,
                y: (window.innerHeight - modalHeight) / 2,
            });
        }
    }, [isOpen]);

    // 드래그 핸들러
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (isDragging) {
                setPosition({
                    x: e.clientX - dragOffset.current.x,
                    y: e.clientY - dragOffset.current.y,
                });
            }
        };
        const handleMouseUp = () => setIsDragging(false);
        if (isDragging) {
            document.addEventListener("mousemove", handleMouseMove);
            document.addEventListener("mouseup", handleMouseUp);
        }
        return () => {
            document.removeEventListener("mousemove", handleMouseMove);
            document.removeEventListener("mouseup", handleMouseUp);
        };
    }, [isDragging]);

    const handleMouseDown = (e: React.MouseEvent) => {
        if (modalRef.current) {
            dragOffset.current = {
                x: e.clientX - position.x,
                y: e.clientY - position.y,
            };
            setIsDragging(true);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 bg-black/30">
            <div
                ref={modalRef}
                className="absolute w-[450px] rounded-lg border bg-white shadow-xl"
                style={{ left: position.x, top: position.y }}
            >
                <div
                    className="flex cursor-move select-none items-center justify-between border-b bg-orange-500 px-4 py-2 text-white"
                    onMouseDown={handleMouseDown}
                >
                    <span className="font-medium">메모사항</span>
                    <button onClick={onClose} onMouseDown={(e) => e.stopPropagation()} className="hover:bg-orange-600 rounded p-1">
                        <X className="h-4 w-4" />
                    </button>
                </div>
                <div className="p-4">
                    <div className="flex border-b mb-3">
                        <button
                            className={`px-4 py-2 text-sm ${activeTab === "memo" ? "border-b-2 border-orange-500 text-orange-600 font-medium" : "text-gray-500"}`}
                            onClick={() => setActiveTab("memo")}
                        >
                            메모
                        </button>
                        <button
                            className={`px-4 py-2 text-sm ${activeTab === "transaction" ? "border-b-2 border-orange-500 text-orange-600 font-medium" : "text-gray-500"}`}
                            onClick={() => setActiveTab("transaction")}
                        >
                            거래명세서 한줄메모
                        </button>
                    </div>
                    {activeTab === "memo" ? (
                        <>
                            <p className="text-sm text-gray-600 mb-2">거래에 대한 메모 사항을 입력해주세요.</p>
                            <textarea
                                value={localMemo}
                                onChange={(e) => setLocalMemo(e.target.value)}
                                className="w-full h-32 rounded border px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
                                placeholder="메모 입력..."
                            />
                        </>
                    ) : (
                        <>
                            <p className="text-sm text-gray-600 mb-2">거래명세서에 표시될 한줄 메모입니다.</p>
                            <input
                                type="text"
                                value={transactionMemo}
                                onChange={(e) => setTransactionMemo(e.target.value)}
                                className="w-full rounded border px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
                                placeholder="한줄 메모 입력..."
                            />
                        </>
                    )}
                    <div className="flex justify-end gap-2 mt-4">
                        <button
                            onClick={() => {
                                onSave(localMemo);
                                onClose();
                            }}
                            className="rounded bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
                        >
                            저 장(S)
                        </button>
                        <button
                            onClick={onClose}
                            className="rounded bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
                        >
                            취 소(Esc)
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

// 할인율 적용 팝업
function DiscountRatePopup({
    isOpen,
    onClose,
    onApply,
}: {
    isOpen: boolean;
    onClose: () => void;
    onApply: (rate: number) => void;
}) {
    const [rate, setRate] = useState(0);

    // 드래그 관련 상태
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const dragOffset = useRef({ x: 0, y: 0 });
    const modalRef = useRef<HTMLDivElement>(null);

    // 모달이 열릴 때 중앙에 위치
    useEffect(() => {
        if (isOpen && modalRef.current) {
            const modalWidth = modalRef.current.offsetWidth;
            const modalHeight = modalRef.current.offsetHeight;
            setPosition({
                x: (window.innerWidth - modalWidth) / 2,
                y: (window.innerHeight - modalHeight) / 2,
            });
        }
    }, [isOpen]);

    // 드래그 핸들러
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (isDragging) {
                setPosition({
                    x: e.clientX - dragOffset.current.x,
                    y: e.clientY - dragOffset.current.y,
                });
            }
        };
        const handleMouseUp = () => setIsDragging(false);
        if (isDragging) {
            document.addEventListener("mousemove", handleMouseMove);
            document.addEventListener("mouseup", handleMouseUp);
        }
        return () => {
            document.removeEventListener("mousemove", handleMouseMove);
            document.removeEventListener("mouseup", handleMouseUp);
        };
    }, [isDragging]);

    const handleMouseDown = (e: React.MouseEvent) => {
        if (modalRef.current) {
            dragOffset.current = {
                x: e.clientX - position.x,
                y: e.clientY - position.y,
            };
            setIsDragging(true);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 bg-black/30">
            <div
                ref={modalRef}
                className="absolute w-[300px] rounded-lg border bg-white shadow-xl"
                style={{ left: position.x, top: position.y }}
            >
                <div
                    className="flex cursor-move select-none items-center justify-between border-b bg-indigo-500 px-4 py-2 text-white"
                    onMouseDown={handleMouseDown}
                >
                    <span className="font-medium">할인율 적용</span>
                    <button onClick={onClose} onMouseDown={(e) => e.stopPropagation()} className="hover:bg-indigo-600 rounded p-1">
                        <X className="h-4 w-4" />
                    </button>
                </div>
                <div className="p-4 space-y-3">
                    <div className="flex items-center gap-2">
                        <label className="text-sm">할인율:</label>
                        <input
                            type="number"
                            value={rate}
                            onChange={(e) => setRate(Number(e.target.value))}
                            className="flex-1 rounded border px-2 py-1.5 text-sm text-right"
                            min={0}
                            max={100}
                        />
                        <span className="text-sm">%</span>
                    </div>
                    <div className="flex justify-end gap-2 pt-2">
                        <button
                            onClick={() => {
                                onApply(rate);
                                onClose();
                            }}
                            className="rounded bg-indigo-500 px-4 py-1.5 text-sm text-white hover:bg-indigo-600"
                        >
                            적용
                        </button>
                        <button
                            onClick={onClose}
                            className="rounded bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
                        >
                            취소
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

// ==================== Main Component ====================
export function SalesVoucherWindow() {
    // Context hooks for window management
    const { openWindow } = useERP();
    const windowContext = useWindowContextOptional();
    const { addSale, companyInfo } = useERPData();

    // 사원/은행/카드 데이터 (API 로드)
    const [EMPLOYEE_LIST, setEmployeeList] = useState<{ code: string; name: string; department: string; position: string }[]>([]);
    const [mockBankAccounts, setMockBankAccounts] = useState<{ code: string; name: string; accountNo: string; balance: number }[]>([]);
    const [mockCards, setMockCards] = useState<{ code: string; name: string; feeRate: number }[]>([]);

    useEffect(() => {
        // 직원 목록 로드
        api.erp.employees.list().then((res: any) => {
            const items = Array.isArray(res) ? res : (res?.items || []);
            setEmployeeList(items.map((e: any) => ({
                code: e.code || e.id || "",
                name: e.name || "",
                department: e.department || "",
                position: e.position || "",
            })));
        }).catch(() => setEmployeeList([]));

        // 은행 계좌 목록 로드
        api.erp.bankAccounts.list().then((res: any) => {
            const items = Array.isArray(res) ? res : (res?.items || []);
            setMockBankAccounts(items.map((b: any) => ({
                code: b.code || b.id || "",
                name: b.bank_name || b.name || "",
                accountNo: b.account_number || b.accountNo || "",
                balance: b.balance || 0,
            })));
        }).catch(() => setMockBankAccounts([]));
    }, []);

    // 기본 정보
    const [salesDate, setSalesDate] = useState(new Date().toISOString().split("T")[0]);
    const [selectedCustomer, setSelectedCustomer] = useState<CustomerInfo | null>(null);
    const [customerSearch, setCustomerSearch] = useState("");
    const [manager, setManager] = useState("");
    const [vatType, setVatType] = useState("부가세별도");
    const [vatRate, setVatRate] = useState(10);

    // 상품 목록
    const [items, setItems] = useState<SalesItem[]>([]);
    const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
    const [selectedProduct, setSelectedProduct] = useState<ProductInfo | null>(null);

    // 금액 정보
    const [discountAmount, setDiscountAmount] = useState(0);
    const [expenses, setExpenses] = useState(0);
    const [cardFee, setCardFee] = useState(0);
    const [bankFee, setBankFee] = useState(0);

    // 결제 정보
    const [payments, setPayments] = useState<PaymentInfo[]>([]);

    // 메모
    const [memo, setMemo] = useState("");

    // 팝업 상태
    const [showCustomerSearch, setShowCustomerSearch] = useState(false);
    const [showProductSearch, setShowProductSearch] = useState(false);
    const [showCashPayment, setShowCashPayment] = useState(false);
    const [showBankPayment, setShowBankPayment] = useState(false);
    const [showBillPayment, setShowBillPayment] = useState(false);
    const [showCardPayment, setShowCardPayment] = useState(false);
    const [showMemo, setShowMemo] = useState(false);
    const [showDiscountRate, setShowDiscountRate] = useState(false);
    const [showItemEdit, setShowItemEdit] = useState(false);
    const [editingItemId, setEditingItemId] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);

    // 문서 모달 상태
    const [showTaxInvoiceModal, setShowTaxInvoiceModal] = useState(false);
    const [showTransactionStatementModal, setShowTransactionStatementModal] = useState(false);
    const [transactionStatementMode, setTransactionStatementMode] = useState<"standard" | "full">("standard");

    // 공급자 정보 (회사 정보 - ERPDataContext에서 가져옴)
    const supplierInfo = React.useMemo(() => ({
        businessNumber: companyInfo.businessNumber || "123-45-67890",
        companyName: companyInfo.companyName || "(주)한국산업",
        ceoName: companyInfo.ceoName || "홍길동",
        address: companyInfo.address ? `${companyInfo.address} ${companyInfo.addressDetail || ''}`.trim() : "서울시 강남구 테헤란로 123",
        businessType: companyInfo.businessType || "제조업",
        businessItem: companyInfo.businessCategory || "전기기기",
        phone: companyInfo.tel || "02-1234-5678",
        fax: companyInfo.fax || "02-1234-5679",
    }), [companyInfo]);

    // 계산
    const supplyAmount = items.reduce((sum, item) => sum + item.supplyAmount, 0);
    const taxAmount = items.reduce((sum, item) => sum + item.vatAmount, 0);
    const totalSalesAmount = supplyAmount + taxAmount - discountAmount + expenses;
    const totalPayment = payments.reduce((sum, p) => sum + p.amount, 0);
    const unpaidAmount = totalSalesAmount - totalPayment;

    // 고객 선택 시 자동 입력
    const handleCustomerSelect = useCallback((customer: CustomerInfo) => {
        setSelectedCustomer(customer);
        setCustomerSearch(customer.name);
        setManager(customer.manager);
        setVatType(customer.vatType);
        setVatRate(customer.vatRate);
    }, []);

    // 상품 추가 (팝업에서 수량/금액/메모 포함, 다중 상품 지원)
    const handleAddProduct = useCallback((dataArray: ProductAddData[]) => {
        const now = Date.now();
        const newItems: SalesItem[] = dataArray.map((data, index) => {
            const { product, quantity, unitPrice, memo } = data;
            const supplyAmount = quantity * unitPrice;
            return {
                id: String(now + index), // 고유 ID 보장
                gubun: "판매",
                productName: product.name,
                spec: "",
                detailSpec: "",
                unit: "EA",
                quantity,
                unitPrice,
                supplyAmount,
                memo,
                vatAmount: Math.round(supplyAmount * (vatRate / 100)),
            };
        });
        setItems((prevItems) => [...prevItems, ...newItems]);
        // 마지막 상품을 선택된 상품으로 설정
        if (dataArray.length > 0) {
            setSelectedProduct(dataArray[dataArray.length - 1].product);
        }
    }, [vatRate]);

    // 상품 수정
    const handleEditItem = useCallback((id: string) => {
        setEditingItemId(id);
    }, []);

    // 상품 삭제
    const handleDeleteItem = useCallback((id: string) => {
        setItems(items.filter((item) => item.id !== id));
        if (selectedItemId === id) {
            setSelectedItemId(null);
            setSelectedProduct(null);
        }
    }, [items, selectedItemId]);

    // 상품 항목 변경
    const handleItemChange = useCallback((id: string, field: keyof SalesItem, value: string | number) => {
        setItems(
            items.map((item) => {
                if (item.id === id) {
                    const updated = { ...item, [field]: value };
                    if (field === "quantity" || field === "unitPrice") {
                        updated.supplyAmount = updated.quantity * updated.unitPrice;
                        updated.vatAmount = Math.round(updated.supplyAmount * (vatRate / 100));
                    }
                    return updated;
                }
                return item;
            })
        );
    }, [items, vatRate]);

    // 할인율 적용
    const handleApplyDiscountRate = useCallback((rate: number) => {
        setItems(
            items.map((item) => {
                const discountedPrice = Math.round(item.unitPrice * (1 - rate / 100));
                return {
                    ...item,
                    unitPrice: discountedPrice,
                    supplyAmount: item.quantity * discountedPrice,
                    vatAmount: Math.round(item.quantity * discountedPrice * (vatRate / 100)),
                };
            })
        );
    }, [items, vatRate]);

    // 결제 추가
    const handleAddPayment = useCallback((payment: PaymentInfo) => {
        setPayments([...payments, payment]);
    }, [payments]);

    // 저장 (closeWindow: true면 저장 후 창 닫기, false면 창 유지)
    const handleSave = useCallback(async (closeWindow: boolean = true): Promise<boolean> => {
        if (isSaving) return false;
        setIsSaving(true);
        if (!selectedCustomer) {
            alert("거래처를 선택해주세요.");
            setIsSaving(false);
            return false;
        }
        if (items.length === 0) {
            alert("상품을 추가해주세요.");
            setIsSaving(false);
            return false;
        }

        try {
            // Context의 addSale을 사용하여 매출 등록 (공유 상태 자동 업데이트)
            const salePayload = {
                slip_number: "",
                slip_date: salesDate,
                customer_id: selectedCustomer.id,
                customer_code: selectedCustomer.code,
                customer_name: selectedCustomer.name,
                sale_type: "외상" as const,
                items: items.map(item => ({
                    product_id: "",
                    product_code: "",
                    product_name: item.productName,
                    specification: item.spec,
                    quantity: item.quantity,
                    unit: item.unit,
                    unit_price: Number(item.unitPrice) || 0,
                    supply_amount: item.supplyAmount,
                    tax_amount: item.vatAmount,
                    total_amount: item.supplyAmount + item.vatAmount,
                    memo: item.memo || "",
                })),
                supply_total: supplyAmount,
                tax_total: taxAmount,
                grand_total: totalSalesAmount,
                payment_status: "미수금" as const,
                memo: memo,
                status: "confirmed",
            };

            const result = await addSale(salePayload as any);

            if (!result) {
                alert("저장 실패: 서버 오류가 발생했습니다.");
                return false;
            }

            // 미수금 업데이트 (고객 정보 갱신)
            if (selectedCustomer) {
                const newReceivable = parseFloat(String(selectedCustomer.receivable || 0)) + parseFloat(String(result.grand_total || 0));
                setSelectedCustomer({
                    ...selectedCustomer,
                    receivable: newReceivable,
                });
            }

            alert("저장되었습니다.");
            if (closeWindow) {
                windowContext?.closeThisWindow();
            }
            return true;
        } catch (error) {
            console.error("저장 실패:", error);
            const errorMessage = error instanceof Error ? error.message : JSON.stringify(error);
            alert(`저장 실패: ${errorMessage}`);
            return false;
        } finally {
            setIsSaving(false);
        }
    }, [isSaving, selectedCustomer, items, salesDate, memo, windowContext, addSale, supplyAmount, taxAmount, totalSalesAmount]);

    // 저장 후 추가
    const handleSaveAndAdd = useCallback(async () => {
        await handleSave();
        // Reset form
        setItems([]);
        setPayments([]);
        setDiscountAmount(0);
        setExpenses(0);
        setMemo("");
    }, [handleSave]);

    // 세금계산서 새 창 열기
    const openTaxInvoiceWindow = useCallback(() => {
        const formatNumber = (num: number) => num.toLocaleString();
        const formatDate = (dateStr: string) => {
            const date = new Date(dateStr);
            return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`;
        };

        const newWindow = window.open("", "_blank", "width=900,height=800");
        if (!newWindow) return;

        const salesItems = items.map(item => ({
            productName: item.productName,
            spec: item.spec,
            unit: item.unit,
            quantity: item.quantity,
            unitPrice: item.unitPrice,
            supplyAmount: item.supplyAmount,
            vatAmount: item.vatAmount,
        }));

        newWindow.document.write(`
            <html>
                <head>
                    <title>전자세금계산서</title>
                    <style>
                        @page { size: A4; margin: 10mm; }
                        body { font-family: 'Malgun Gothic', sans-serif; font-size: 10px; padding: 20px; }
                        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
                        th, td { border: 1px solid #1e3a8a; padding: 4px 6px; }
                        .header { background: #dbeafe; color: #1e3a8a; font-weight: bold; text-align: center; font-size: 16px; padding: 10px; }
                        .label { background: #eff6ff; color: #1e3a8a; text-align: center; font-weight: bold; }
                        .right { text-align: right; }
                        .center { text-align: center; }
                        .toolbar { background: #f3f4f6; padding: 10px; margin-bottom: 20px; display: flex; gap: 10px; }
                        .toolbar button { padding: 8px 16px; cursor: pointer; }
                        @media print { .toolbar { display: none; } }
                    </style>
                </head>
                <body>
                    <div class="toolbar">
                        <button onclick="window.print()">인쇄</button>
                        <button onclick="window.close()">닫기</button>
                    </div>
                    <table>
                        <tr><td colspan="8" class="header">세 금 계 산 서 (공급자보관용)</td></tr>
                        <tr>
                            <td class="label">작성일자</td>
                            <td colspan="3">${formatDate(salesDate)}</td>
                            <td class="label">공급가액</td>
                            <td class="right">${formatNumber(supplyAmount)}</td>
                            <td class="label">세액</td>
                            <td class="right">${formatNumber(taxAmount)}</td>
                        </tr>
                        <tr>
                            <td rowspan="3" class="label">공급자</td>
                            <td class="label">상호</td>
                            <td colspan="2">(주)나베랄</td>
                            <td rowspan="3" class="label">공급받는자</td>
                            <td class="label">상호</td>
                            <td colspan="2">${selectedCustomer?.name || ""}</td>
                        </tr>
                        <tr>
                            <td class="label">사업자번호</td>
                            <td colspan="2">123-45-67890</td>
                            <td class="label">사업자번호</td>
                            <td colspan="2"></td>
                        </tr>
                        <tr>
                            <td class="label">주소</td>
                            <td colspan="2">서울특별시</td>
                            <td class="label">주소</td>
                            <td colspan="2"></td>
                        </tr>
                        <tr class="label">
                            <td>월</td><td>일</td><td colspan="2">품목</td><td>수량</td><td>단가</td><td>공급가액</td><td>세액</td>
                        </tr>
                        ${salesItems.map(item => `
                            <tr>
                                <td class="center">${new Date(salesDate).getMonth() + 1}</td>
                                <td class="center">${new Date(salesDate).getDate()}</td>
                                <td colspan="2">${item.productName}</td>
                                <td class="right">${formatNumber(item.quantity)}</td>
                                <td class="right">${formatNumber(item.unitPrice)}</td>
                                <td class="right">${formatNumber(item.supplyAmount)}</td>
                                <td class="right">${formatNumber(item.vatAmount)}</td>
                            </tr>
                        `).join("")}
                        <tr>
                            <td colspan="4" class="label">합계</td>
                            <td colspan="2" class="right">${formatNumber(supplyAmount)}</td>
                            <td colspan="2" class="right">${formatNumber(taxAmount)}</td>
                        </tr>
                        <tr>
                            <td colspan="8" class="center">위 금액을 영수 / 청구 함</td>
                        </tr>
                    </table>
                </body>
            </html>
        `);
        newWindow.document.close();
    }, [items, salesDate, selectedCustomer, supplyAmount, taxAmount]);

    // 거래명세서 새 창 열기
    const openTransactionStatementWindow = useCallback((mode: "standard" | "full") => {
        const formatNumber = (num: number) => num.toLocaleString();
        const formatDate = (dateStr: string) => {
            const date = new Date(dateStr);
            return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`;
        };

        const newWindow = window.open("", "_blank", "width=900,height=800");
        if (!newWindow) return;

        const salesItems = items.map(item => ({
            productName: item.productName,
            spec: item.spec,
            unit: item.unit,
            quantity: item.quantity,
            unitPrice: item.unitPrice,
            supplyAmount: item.supplyAmount,
        }));

        const rowCount = mode === "full" ? 20 : 8;

        const renderStatement = (type: "supplier" | "customer") => {
            const borderColor = type === "supplier" ? "#dc2626" : "#2563eb";
            const bgColor = type === "supplier" ? "#fef2f2" : "#eff6ff";
            const title = type === "supplier" ? "공급자보관용" : "공급받는자보관용";

            return `
                <table style="border: 2px solid ${borderColor}; margin-bottom: 20px;">
                    <tr>
                        <td colspan="2" style="border: 1px solid ${borderColor}; padding: 5px;">
                            <span style="color: ${borderColor};">거래일자</span> ${formatDate(salesDate)}
                        </td>
                        <td colspan="4" style="border: 1px solid ${borderColor}; text-align: center; font-size: 18px; font-weight: bold; color: ${borderColor};">
                            거래명세서<br><span style="font-size: 10px; font-weight: normal;">(${title})</span>
                        </td>
                        <td colspan="2" style="border: 1px solid ${borderColor}; background: ${bgColor}; text-align: center; color: ${borderColor};">인</td>
                    </tr>
                    <tr>
                        <td rowspan="3" style="border: 1px solid ${borderColor}; background: ${bgColor}; text-align: center; color: ${borderColor}; font-weight: bold; width: 30px;">공급자</td>
                        <td style="border: 1px solid ${borderColor}; background: ${bgColor}; color: ${borderColor}; text-align: center;">상호</td>
                        <td colspan="2" style="border: 1px solid ${borderColor};">(주)나베랄</td>
                        <td rowspan="3" style="border: 1px solid ${borderColor}; background: ${bgColor}; text-align: center; color: ${borderColor}; font-weight: bold; width: 30px;">공급받는자</td>
                        <td style="border: 1px solid ${borderColor}; background: ${bgColor}; color: ${borderColor}; text-align: center;">상호</td>
                        <td colspan="2" style="border: 1px solid ${borderColor};">${selectedCustomer?.name || ""}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid ${borderColor}; background: ${bgColor}; color: ${borderColor}; text-align: center;">주소</td>
                        <td colspan="2" style="border: 1px solid ${borderColor};">서울특별시</td>
                        <td style="border: 1px solid ${borderColor}; background: ${bgColor}; color: ${borderColor}; text-align: center;">주소</td>
                        <td colspan="2" style="border: 1px solid ${borderColor};"></td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid ${borderColor}; background: ${bgColor}; color: ${borderColor}; text-align: center;">TEL</td>
                        <td colspan="2" style="border: 1px solid ${borderColor};">02-1234-5678</td>
                        <td style="border: 1px solid ${borderColor}; background: ${bgColor}; color: ${borderColor}; text-align: center;">TEL</td>
                        <td colspan="2" style="border: 1px solid ${borderColor};">${selectedCustomer?.phone || ""}</td>
                    </tr>
                    <tr style="background: ${bgColor}; color: ${borderColor}; text-align: center;">
                        <td style="border: 1px solid ${borderColor};">NO</td>
                        <td style="border: 1px solid ${borderColor};">품목코드</td>
                        <td style="border: 1px solid ${borderColor};">상품명</td>
                        <td style="border: 1px solid ${borderColor};">규격</td>
                        <td style="border: 1px solid ${borderColor};">단위</td>
                        <td style="border: 1px solid ${borderColor};">수량</td>
                        <td style="border: 1px solid ${borderColor};">단가</td>
                        <td style="border: 1px solid ${borderColor};">공급가액</td>
                    </tr>
                    ${Array.from({ length: rowCount }).map((_, idx) => {
                        const item = salesItems[idx];
                        const rowBg = idx % 2 === 1 ? bgColor : "white";
                        return `
                            <tr style="background: ${rowBg};">
                                <td style="border: 1px solid ${borderColor}; text-align: center;">${item ? idx + 1 : ""}</td>
                                <td style="border: 1px solid ${borderColor};"></td>
                                <td style="border: 1px solid ${borderColor};">${item?.productName || ""}</td>
                                <td style="border: 1px solid ${borderColor};">${item?.spec || ""}</td>
                                <td style="border: 1px solid ${borderColor}; text-align: center;">${item?.unit || ""}</td>
                                <td style="border: 1px solid ${borderColor}; text-align: right;">${item ? formatNumber(item.quantity) : ""}</td>
                                <td style="border: 1px solid ${borderColor}; text-align: right;">${item ? formatNumber(item.unitPrice) : ""}</td>
                                <td style="border: 1px solid ${borderColor}; text-align: right;">${item ? formatNumber(item.supplyAmount) : ""}</td>
                            </tr>
                        `;
                    }).join("")}
                    <tr style="background: ${bgColor};">
                        <td colspan="2" style="border: 1px solid ${borderColor}; text-align: center; font-weight: bold; color: ${borderColor};">합계</td>
                        <td style="border: 1px solid ${borderColor}; color: ${borderColor}; text-align: center;">세액</td>
                        <td style="border: 1px solid ${borderColor}; text-align: right; font-weight: bold;">${formatNumber(taxAmount)}</td>
                        <td style="border: 1px solid ${borderColor};"></td>
                        <td style="border: 1px solid ${borderColor}; color: ${borderColor}; text-align: center;">합계금액</td>
                        <td colspan="2" style="border: 1px solid ${borderColor}; text-align: right; font-weight: bold;">${formatNumber(totalSalesAmount)}</td>
                    </tr>
                </table>
            `;
        };

        newWindow.document.write(`
            <html>
                <head>
                    <title>거래명세서${mode === "full" ? "(전장)" : ""}</title>
                    <style>
                        @page { size: A4; margin: 10mm; }
                        body { font-family: 'Malgun Gothic', sans-serif; font-size: 10px; padding: 20px; }
                        table { border-collapse: collapse; width: 100%; }
                        .toolbar { background: #f3f4f6; padding: 10px; margin-bottom: 20px; display: flex; gap: 10px; }
                        .toolbar button { padding: 8px 16px; cursor: pointer; }
                        @media print { .toolbar { display: none; } }
                    </style>
                </head>
                <body>
                    <div class="toolbar">
                        <button onclick="window.print()">인쇄</button>
                        <button onclick="window.close()">닫기</button>
                    </div>
                    ${mode === "full" ? renderStatement("supplier") : renderStatement("supplier") + renderStatement("customer")}
                </body>
            </html>
        `);
        newWindow.document.close();
    }, [items, salesDate, selectedCustomer, taxAmount, totalSalesAmount]);

    // 전자세금계산서
    const handleTaxInvoice = useCallback(async () => {
        if (!selectedCustomer) {
            alert("거래처를 선택해주세요.");
            return;
        }
        if (items.length === 0) {
            alert("상품을 추가해주세요.");
            return;
        }
        const confirmed = window.confirm("입력하신 내용을 저장하고 전자세금계산서를 발행하시겠습니까?");
        if (confirmed) {
            const saved = await handleSave(false); // 창을 닫지 않고 저장
            if (saved) {
                openTaxInvoiceWindow(); // 새 창으로 세금계산서 열기
                windowContext?.closeThisWindow(); // 매출전표창 닫기
            }
        }
    }, [selectedCustomer, items, handleSave, openTaxInvoiceWindow, windowContext]);

    // 거래명세서
    const handleTransactionStatement = useCallback(async () => {
        if (!selectedCustomer) {
            alert("거래처를 선택해주세요.");
            return;
        }
        if (items.length === 0) {
            alert("상품을 추가해주세요.");
            return;
        }
        const confirmed = window.confirm("입력하신 내용을 저장하고 거래명세서를 발행하시겠습니까?");
        if (confirmed) {
            const saved = await handleSave(false); // 창을 닫지 않고 저장
            if (saved) {
                openTransactionStatementWindow("standard"); // 새 창으로 거래명세서 열기
                windowContext?.closeThisWindow(); // 매출전표창 닫기
            }
        }
    }, [selectedCustomer, items, handleSave, openTransactionStatementWindow, windowContext]);

    // 거래명세서(전장)
    const handleTransactionStatementFull = useCallback(async () => {
        if (!selectedCustomer) {
            alert("거래처를 선택해주세요.");
            return;
        }
        if (items.length === 0) {
            alert("상품을 추가해주세요.");
            return;
        }
        const confirmed = window.confirm("입력하신 내용을 저장하고 거래명세서(전장)를 발행하시겠습니까?");
        if (confirmed) {
            const saved = await handleSave(false); // 창을 닫지 않고 저장
            if (saved) {
                openTransactionStatementWindow("full"); // 새 창으로 거래명세서(전장) 열기
                windowContext?.closeThisWindow(); // 매출전표창 닫기
            }
        }
    }, [selectedCustomer, items, handleSave, openTransactionStatementWindow, windowContext]);

    // 상품 행 더블클릭 - 수정 팝업 열기
    const handleRowDoubleClick = useCallback((id: string) => {
        setEditingItemId(id);
        setShowItemEdit(true);
    }, []);

    // 수정된 상품 저장
    const handleSaveEditedItem = useCallback((editedItem: SalesItem) => {
        setItems(items.map(item => item.id === editedItem.id ? editedItem : item));
        setEditingItemId(null);
    }, [items]);

    return (
        <div className="flex h-full flex-col bg-[#f0f0f0]">
            {/* 상단 버튼 영역 */}
            <div className="flex items-center justify-between border-b bg-[#f5f5f5] px-2 py-1">
                <span className="text-sm font-medium">■ 일반</span>
                <div className="flex gap-1">
                    <button
                        onClick={handleTaxInvoice}
                        className="rounded border bg-white px-3 py-1 text-sm hover:bg-gray-100"
                    >
                        전자세금계산서
                    </button>
                    <button
                        onClick={handleTransactionStatement}
                        className="rounded border bg-white px-3 py-1 text-sm hover:bg-gray-100"
                    >
                        거래명세서
                    </button>
                    <button
                        onClick={handleTransactionStatementFull}
                        className="rounded border bg-white px-3 py-1 text-sm hover:bg-gray-100"
                    >
                        거래명세서(전장)
                    </button>
                    <button
                        onClick={() => setShowMemo(true)}
                        className="rounded border bg-orange-400 px-3 py-1 text-sm text-white hover:bg-orange-500"
                    >
                        메모사항
                    </button>
                </div>
            </div>

            {/* 일반 정보 섹션 */}
            <div className="grid grid-cols-4 gap-4 border-b bg-white p-3">
                <div>
                    <label className="mb-1 block text-xs font-medium">매출일자:</label>
                    <input
                        type="date"
                        value={salesDate}
                        onChange={(e) => setSalesDate(e.target.value)}
                        className="w-full rounded border px-2 py-1.5 text-sm"
                    />
                </div>
                <div>
                    <label className="mb-1 block text-xs font-medium">매출대상거래처(O):</label>
                    <div className="flex gap-1">
                        <input
                            type="text"
                            value={customerSearch}
                            onChange={(e) => setCustomerSearch(e.target.value)}
                            className="flex-1 rounded border px-2 py-1.5 text-sm"
                            placeholder="거래처 검색..."
                        />
                        <button
                            onClick={() => setShowCustomerSearch(true)}
                            className="rounded border bg-gray-100 px-2 py-1 text-sm hover:bg-gray-200"
                        >
                            ...
                        </button>
                    </div>
                </div>
                <div>
                    <label className="mb-1 block text-xs font-medium">매출담당사원(U):</label>
                    <select
                        value={manager}
                        onChange={(e) => setManager(e.target.value)}
                        className="w-full rounded border px-2 py-1.5 text-sm"
                    >
                        <option value="">선택</option>
                        {EMPLOYEE_LIST.map((emp) => (
                            <option key={emp.code} value={emp.name}>
                                {emp.name} ({emp.department}/{emp.position})
                            </option>
                        ))}
                    </select>
                </div>
                <div>
                    <label className="mb-1 block text-xs font-medium">부가세율:</label>
                    <div className="flex gap-1">
                        <select
                            value={vatType}
                            onChange={(e) => setVatType(e.target.value)}
                            className="flex-1 rounded border px-2 py-1.5 text-sm"
                        >
                            <option>부가세별도</option>
                            <option>부가세포함</option>
                            <option>영세율</option>
                        </select>
                        <div className="flex items-center gap-1">
                            <input
                                type="number"
                                value={vatRate}
                                onChange={(e) => setVatRate(Number(e.target.value))}
                                className="w-16 rounded border px-2 py-1.5 text-sm text-right"
                            />
                            <span className="text-sm">%</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* 판매 상품 섹션 */}
            <div className="flex-1 overflow-hidden p-2">
                <div className="flex h-full flex-col rounded border bg-white">
                    <div className="flex items-center justify-between border-b bg-[#e8f4e8] px-3 py-1.5">
                        <span className="text-sm font-medium">■ 판매하는 상품 ( {items.length} 품목)</span>
                        <div className="flex gap-1">
                            <button
                                onClick={() => setShowDiscountRate(true)}
                                className="rounded border bg-white px-2 py-1 text-xs hover:bg-gray-100"
                            >
                                할인율 적용
                            </button>
                            <button
                                onClick={() => setShowProductSearch(true)}
                                className="rounded border bg-white px-2 py-1 text-xs hover:bg-gray-100"
                            >
                                추가
                            </button>
                            <button
                                onClick={() => selectedItemId && handleEditItem(selectedItemId)}
                                className="rounded border bg-white px-2 py-1 text-xs hover:bg-gray-100"
                                disabled={!selectedItemId}
                            >
                                수정
                            </button>
                            <button
                                onClick={() => selectedItemId && handleDeleteItem(selectedItemId)}
                                className="rounded border bg-white px-2 py-1 text-xs hover:bg-gray-100"
                                disabled={!selectedItemId}
                            >
                                삭제
                            </button>
                        </div>
                    </div>
                    <div className="flex-1 overflow-auto">
                        <table className="w-full table-fixed text-xs">
                            <thead className="sticky top-0 bg-[#f5f5f5]">
                                <tr className="border-b">
                                    <th className="w-[50px] border-r px-1 py-1.5 text-center">구분</th>
                                    <th className="w-[140px] border-r px-1 py-1.5 text-left">상품명</th>
                                    <th className="w-[80px] border-r px-1 py-1.5 text-left">규격</th>
                                    <th className="w-[80px] border-r px-1 py-1.5 text-left">상세규격</th>
                                    <th className="w-[40px] border-r px-1 py-1.5 text-center">단위</th>
                                    <th className="w-[50px] border-r px-1 py-1.5 text-right">수량</th>
                                    <th className="w-[70px] border-r px-1 py-1.5 text-right">단가</th>
                                    <th className="w-[90px] border-r px-1 py-1.5 text-right">공급가액</th>
                                    <th className="border-r px-1 py-1.5 text-left">메모</th>
                                    <th className="w-[80px] px-1 py-1.5 text-right">부가세액</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item) => (
                                    <tr
                                        key={item.id}
                                        className={`border-b cursor-pointer hover:bg-blue-50 ${selectedItemId === item.id ? "bg-blue-100" : ""}`}
                                        onClick={() => {
                                            setSelectedItemId(item.id);
                                            setSelectedProduct({
                                                code: "",
                                                name: item.productName,
                                                stock: 0,
                                                lastSales: 0,
                                                lastPrice: item.unitPrice,
                                                optimalStock: 0,
                                            });
                                        }}
                                        onDoubleClick={() => handleRowDoubleClick(item.id)}
                                    >
                                        <td className="w-[50px] border-r px-1 py-1 text-center truncate">
                                            {editingItemId === item.id ? (
                                                <input
                                                    type="text"
                                                    value={item.gubun}
                                                    onChange={(e) => handleItemChange(item.id, "gubun", e.target.value)}
                                                    className="w-full rounded border px-1 text-xs"
                                                    onBlur={() => setEditingItemId(null)}
                                                />
                                            ) : (
                                                item.gubun
                                            )}
                                        </td>
                                        <td className="w-[140px] border-r px-1 py-1 truncate" title={item.productName}>{item.productName}</td>
                                        <td className="w-[80px] border-r px-1 py-1 truncate" title={item.spec}>{item.spec}</td>
                                        <td className="w-[80px] border-r px-1 py-1 truncate" title={item.detailSpec}>{item.detailSpec}</td>
                                        <td className="w-[40px] border-r px-1 py-1 text-center">{item.unit}</td>
                                        <td className="w-[50px] border-r px-1 py-1 text-right">
                                            {editingItemId === item.id ? (
                                                <input
                                                    type="number"
                                                    value={item.quantity}
                                                    onChange={(e) => handleItemChange(item.id, "quantity", Number(e.target.value))}
                                                    className="w-full rounded border px-1 text-xs text-right"
                                                    onBlur={() => setEditingItemId(null)}
                                                />
                                            ) : (
                                                item.quantity
                                            )}
                                        </td>
                                        <td className="w-[70px] border-r px-1 py-1 text-right">
                                            {editingItemId === item.id ? (
                                                <input
                                                    type="number"
                                                    value={item.unitPrice}
                                                    onChange={(e) => handleItemChange(item.id, "unitPrice", Number(e.target.value))}
                                                    className="w-full rounded border px-1 text-xs text-right"
                                                    onBlur={() => setEditingItemId(null)}
                                                />
                                            ) : (
                                                item.unitPrice.toLocaleString()
                                            )}
                                        </td>
                                        <td className="w-[90px] border-r px-1 py-1 text-right">{item.supplyAmount.toLocaleString()}</td>
                                        <td className="border-r px-1 py-1 truncate" title={item.memo}>{item.memo}</td>
                                        <td className="w-[80px] px-1 py-1 text-right">{item.vatAmount.toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* 하단 정보 영역 - 고정 높이로 창 크기 변동 방지 */}
            <div className="h-[280px] flex-shrink-0 border-t bg-[#f5f5f5] p-2">
                <div className="grid grid-cols-3 gap-4">
                    {/* 상품대금 */}
                    <div className="rounded border bg-white p-2">
                        <div className="mb-2 text-xs font-medium">■ 상품대금</div>
                        <div className="space-y-1 text-xs">
                            <div className="flex justify-between">
                                <span className="text-blue-600">공급가액:</span>
                                <span className="text-blue-600">{supplyAmount.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-blue-600">세액:</span>
                                <span className="text-blue-600">{taxAmount.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span>할인액(-):</span>
                                <input
                                    type="number"
                                    value={discountAmount}
                                    onChange={(e) => setDiscountAmount(Number(e.target.value))}
                                    className="w-24 rounded border px-2 py-0.5 text-right text-xs"
                                />
                            </div>
                            <div className="flex justify-between border-t pt-1">
                                <span className="font-medium">상품대금:</span>
                                <span className="font-medium">{(supplyAmount + taxAmount - discountAmount).toLocaleString()}</span>
                            </div>
                        </div>
                    </div>

                    {/* 기타비용 */}
                    <div className="rounded border bg-white p-2">
                        <div className="mb-2 text-xs font-medium">■ 기타비용</div>
                        <div className="space-y-1 text-xs">
                            <div className="flex justify-between items-center">
                                <span>제비용(+):</span>
                                <input
                                    type="number"
                                    value={expenses}
                                    onChange={(e) => setExpenses(Number(e.target.value))}
                                    className="w-24 rounded border px-2 py-0.5 text-right text-xs"
                                />
                            </div>
                            <div className="flex justify-between items-center">
                                <span>카드수수료(+):</span>
                                <input
                                    type="number"
                                    value={cardFee}
                                    onChange={(e) => setCardFee(Number(e.target.value))}
                                    className="w-24 rounded border px-2 py-0.5 text-right text-xs"
                                />
                            </div>
                            <div className="flex justify-between items-center">
                                <span>은행수수료:</span>
                                <input
                                    type="number"
                                    value={bankFee}
                                    onChange={(e) => setBankFee(Number(e.target.value))}
                                    className="w-24 rounded border px-2 py-0.5 text-right text-xs"
                                />
                            </div>
                        </div>
                    </div>

                    {/* 대금결제 */}
                    <div className="rounded border bg-white p-2">
                        <div className="mb-2 flex items-center justify-between">
                            <span className="text-xs font-medium">■ 대금결제</span>
                            <div className="flex gap-1">
                                <button
                                    onClick={() => setShowCashPayment(true)}
                                    className="rounded border bg-amber-100 px-2 py-0.5 text-xs hover:bg-amber-200"
                                >
                                    현금
                                </button>
                                <button
                                    onClick={() => setShowBankPayment(true)}
                                    className="rounded border bg-blue-100 px-2 py-0.5 text-xs hover:bg-blue-200"
                                >
                                    은행
                                </button>
                                <button
                                    onClick={() => setShowBillPayment(true)}
                                    className="rounded border bg-purple-100 px-2 py-0.5 text-xs hover:bg-purple-200"
                                >
                                    어음
                                </button>
                                <button
                                    onClick={() => setShowCardPayment(true)}
                                    className="rounded border bg-rose-100 px-2 py-0.5 text-xs hover:bg-rose-200"
                                >
                                    카드
                                </button>
                            </div>
                        </div>
                        <div className="space-y-1 text-xs">
                            <div className="flex justify-between">
                                <span>매출액:</span>
                                <span>{totalSalesAmount.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>결제금액:</span>
                                <span className="text-green-600">{totalPayment.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between border-t pt-1">
                                <span className="font-medium">미결제금액:</span>
                                <span className={`font-medium ${unpaidAmount > 0 ? "text-red-600" : ""}`}>
                                    {unpaidAmount.toLocaleString()}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* 선택된 업체/상품 정보 - 고정 높이 + 부드러운 전환 */}
                <div className="mt-2 grid grid-cols-2 gap-4">
                    <div className="h-[96px] rounded border bg-white p-2 transition-all duration-200 ease-in-out">
                        <div className="mb-1 text-xs font-medium">■ 선택된 업체: <span className="font-normal text-blue-600">{selectedCustomer?.name || "(선택 없음)"}</span></div>
                        <div className="grid grid-cols-3 gap-x-4 gap-y-1 text-xs">
                            <div className="flex justify-between">
                                <span className="text-gray-500">미수금액:</span>
                                <span className={`transition-all duration-200 ${selectedCustomer ? "text-red-600" : "text-gray-400"}`}>{selectedCustomer?.receivable.toLocaleString() || "-"}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-500">팩스번호:</span>
                                <span className="transition-all duration-200">{selectedCustomer?.fax || "-"}</span>
                            </div>
                            <div />
                            <div className="flex justify-between">
                                <span className="text-gray-500">미지급액:</span>
                                <span className="transition-all duration-200">{selectedCustomer?.payable.toLocaleString() || "-"}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-500">전화번호:</span>
                                <span className="transition-all duration-200">{selectedCustomer?.phone || "-"}</span>
                            </div>
                            <div />
                            <div className="flex justify-between">
                                <span className="text-gray-500">신용한도:</span>
                                <span className="transition-all duration-200">{selectedCustomer?.creditLimit.toLocaleString() || "-"}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-500">최종거래:</span>
                                <span className="transition-all duration-200">{selectedCustomer?.lastTransaction || "-"}</span>
                            </div>
                        </div>
                    </div>
                    <div className="h-[72px] rounded border bg-white p-2 transition-all duration-200 ease-in-out">
                        <div className="mb-1 text-xs font-medium">■ 선택된 상품: <span className="font-normal text-blue-600">{selectedProduct?.name || "(선택 없음)"}</span></div>
                        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                            <div className="flex justify-between">
                                <span className="text-gray-500">보유재고:</span>
                                <span className="transition-all duration-200">{selectedProduct?.stock ?? "-"}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-500">최종단가:</span>
                                <span className="transition-all duration-200">{selectedProduct?.lastPrice.toLocaleString() ?? "-"}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-500">최종매출:</span>
                                <span className="transition-all duration-200">{selectedProduct?.lastSales ?? "-"}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-500">적정재고:</span>
                                <span className="transition-all duration-200">{selectedProduct?.optimalStock ?? "-"}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* 하단 버튼 */}
                <div className="mt-2 flex items-center justify-between">
                    <button className="text-xs text-blue-600 hover:underline">관련항목&gt;&gt;</button>
                    <div className="flex gap-2">
                        <button
                            onClick={handleSaveAndAdd}
                            className="rounded border bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
                        >
                            저장후추가
                        </button>
                        <button
                            onClick={() => handleSave()}
                            disabled={isSaving}
                            className="rounded border bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
                        >
                            저 장
                        </button>
                        <button
                            onClick={() => windowContext?.closeThisWindow()}
                            className="rounded border bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
                        >
                            취 소
                        </button>
                    </div>
                </div>
            </div>

            {/* 팝업들 */}
            <CustomerSearchPopup
                isOpen={showCustomerSearch}
                onClose={() => setShowCustomerSearch(false)}
                onSelect={handleCustomerSelect}
                searchTerm={customerSearch}
            />
            <ProductSearchPopup
                isOpen={showProductSearch}
                onClose={() => setShowProductSearch(false)}
                onSelect={handleAddProduct}
            />
            <CashPaymentPopup
                isOpen={showCashPayment}
                onClose={() => setShowCashPayment(false)}
                onSave={handleAddPayment}
                maxAmount={unpaidAmount}
            />
            <BankPaymentPopup
                isOpen={showBankPayment}
                onClose={() => setShowBankPayment(false)}
                onSave={handleAddPayment}
                maxAmount={unpaidAmount}
            />
            <BillPaymentPopup
                isOpen={showBillPayment}
                onClose={() => setShowBillPayment(false)}
                onSave={handleAddPayment}
            />
            <CardPaymentPopup
                isOpen={showCardPayment}
                onClose={() => setShowCardPayment(false)}
                onSave={handleAddPayment}
            />
            <MemoPopup
                isOpen={showMemo}
                onClose={() => setShowMemo(false)}
                memo={memo}
                onSave={setMemo}
            />
            <DiscountRatePopup
                isOpen={showDiscountRate}
                onClose={() => setShowDiscountRate(false)}
                onApply={handleApplyDiscountRate}
            />
            <ItemEditPopup
                isOpen={showItemEdit}
                onClose={() => {
                    setShowItemEdit(false);
                    setEditingItemId(null);
                }}
                item={items.find(item => item.id === editingItemId) || null}
                onSave={handleSaveEditedItem}
                vatRate={vatRate}
            />

            {/* 거래명세서 모달 */}
            {selectedCustomer && (
                <TransactionStatementModal
                    isOpen={showTransactionStatementModal}
                    onClose={() => setShowTransactionStatementModal(false)}
                    mode={transactionStatementMode}
                    transactionDate={salesDate}
                    documentNumber={`TS-${Date.now()}`}
                    supplierBusinessNumber={supplierInfo.businessNumber}
                    supplierCompanyName={supplierInfo.companyName}
                    supplierCeoName={supplierInfo.ceoName}
                    supplierAddress={supplierInfo.address}
                    supplierPhone={supplierInfo.phone}
                    supplierFax={supplierInfo.fax}
                    customerBusinessNumber={selectedCustomer.code || ""}
                    customerCompanyName={selectedCustomer.name}
                    customerCeoName=""
                    customerAddress=""
                    customerPhone=""
                    customerFax=""
                    items={items.map(item => ({
                        id: item.id,
                        productName: item.productName,
                        spec: item.spec,
                        unit: item.unit,
                        quantity: item.quantity,
                        unitPrice: item.unitPrice,
                        supplyAmount: item.supplyAmount,
                        vatAmount: item.vatAmount,
                        memo: item.memo,
                    }))}
                    totalSupplyAmount={supplyAmount}
                    totalVatAmount={taxAmount}
                    totalAmount={totalSalesAmount}
                />
            )}

            {/* 전자세금계산서 모달 */}
            {selectedCustomer && (
                <TaxInvoiceModal
                    isOpen={showTaxInvoiceModal}
                    onClose={() => setShowTaxInvoiceModal(false)}
                    transactionDate={salesDate}
                    documentNumber={`TI-${Date.now()}`}
                    supplierBusinessNumber={supplierInfo.businessNumber}
                    supplierCompanyName={supplierInfo.companyName}
                    supplierCeoName={supplierInfo.ceoName}
                    supplierAddress={supplierInfo.address}
                    supplierBusinessType={supplierInfo.businessType}
                    supplierBusinessItem={supplierInfo.businessItem}
                    customerBusinessNumber={selectedCustomer.code || ""}
                    customerCompanyName={selectedCustomer.name}
                    customerCeoName=""
                    customerAddress=""
                    customerBusinessType=""
                    customerBusinessItem=""
                    items={items.map(item => ({
                        id: item.id,
                        productName: item.productName,
                        spec: item.spec,
                        unit: item.unit,
                        quantity: item.quantity,
                        unitPrice: item.unitPrice,
                        supplyAmount: item.supplyAmount,
                        vatAmount: item.vatAmount,
                        memo: item.memo,
                    }))}
                    totalSupplyAmount={supplyAmount}
                    totalVatAmount={taxAmount}
                    totalAmount={totalSalesAmount}
                />
            )}
        </div>
    );
}
