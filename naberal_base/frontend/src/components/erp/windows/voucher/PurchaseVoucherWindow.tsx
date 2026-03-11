"use client";

import React, { useState, useCallback, useEffect, useMemo } from "react";
import {
    X,
    Loader2,
} from "lucide-react";
import { ERPProduct, api, ERPPurchaseCreate } from "@/lib/api";
import { useERPData } from "@/contexts/ERPDataContext";
import type { Product as ContextProduct } from "@/contexts/ERPDataContext";

// ==================== Types ====================
interface PurchaseItem {
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

interface SupplierInfo {
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
    lastPurchase: number; // 최종매입
    lastPrice: number; // 최종단가
    optimalStock: number; // 적정재고
}

// 상품 추가 시 전달할 데이터
interface ProductAddData {
    product: ProductInfo;
    quantity: number;
    unitPrice: number;
    memo: string;
}

interface PaymentInfo {
    type: "cash" | "bank" | "bill" | "card";
    amount: number;
    details: Record<string, string | number>;
}

// ==================== Data Loading ====================
// 거래처, 상품, 은행계좌 데이터는 ERPDataContext 및 API에서 로드됨

// ==================== Sub Components ====================

// 거래처(공급자) 검색 팝업
function SupplierSearchPopup({
    isOpen,
    onClose,
    onSelect,
    searchTerm,
}: {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (supplier: SupplierInfo) => void;
    searchTerm: string;
}) {
    const [localSearch, setLocalSearch] = useState(searchTerm);
    const { customers: contextCustomers, searchCustomers } = useERPData();

    // Context 고객 데이터를 SupplierInfo로 변환하여 필터링
    const filtered: SupplierInfo[] = React.useMemo(() => {
        const source = localSearch.length >= 1
            ? searchCustomers(localSearch)
            : contextCustomers;
        return source.map(c => ({
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
                <div className="flex items-center justify-between border-b bg-orange-600 px-4 py-2 text-white">
                    <span className="font-medium">거래처 검색</span>
                    <button onClick={onClose} className="hover:bg-orange-700 rounded p-1">
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
                            className="flex-1 rounded border px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
                            autoFocus
                        />
                        <button className="rounded bg-orange-600 px-4 py-2 text-sm text-white hover:bg-orange-700">
                            검색
                        </button>
                    </div>
                    {/* 고정 높이로 팝업 크기 변동 방지 */}
                    <div className="h-[300px] overflow-auto border rounded">
                        <table className="w-full text-sm">
                            <thead className="bg-gray-100 sticky top-0">
                                <tr>
                                    <th className="px-3 py-2 text-left">코드</th>
                                    <th className="px-3 py-2 text-left">거래처명</th>
                                    <th className="px-3 py-2 text-left">담당자</th>
                                    <th className="px-3 py-2 text-right">미지급금</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filtered.map((supplier) => (
                                    <tr
                                        key={supplier.code}
                                        className="border-t hover:bg-orange-50 cursor-pointer"
                                        onClick={() => {
                                            onSelect(supplier);
                                            onClose();
                                        }}
                                    >
                                        <td className="px-3 py-2">{supplier.code}</td>
                                        <td className="px-3 py-2 font-medium">{supplier.name}</td>
                                        <td className="px-3 py-2">{supplier.manager}</td>
                                        <td className="px-3 py-2 text-right text-red-600">
                                            {supplier.payable.toLocaleString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}

// 상품 검색 및 추가 팝업 (2단계: 검색 → 수량/금액/메모 입력) - 실제 API 연결
function ProductSearchPopup({
    isOpen,
    onClose,
    onSelect,
}: {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (data: ProductAddData) => void;
}) {
    const [search, setSearch] = useState("");
    const { products: contextProducts, searchProducts, productsLoading: loading, productsError: error } = useERPData();
    const [selectedProduct, setSelectedProduct] = useState<ProductInfo | null>(null);
    const [quantity, setQuantity] = useState(1);
    const [unitPrice, setUnitPrice] = useState(0);
    const [memo, setMemo] = useState("");

    // Context에서 상품 필터링 (ERPProduct 호환 형태로 변환)
    const products: ERPProduct[] = React.useMemo(() => {
        const source = search.length >= 1
            ? searchProducts(search)
            : contextProducts;
        return source.filter(p => p.is_active !== false).map((p: ContextProduct) => ({
            id: p.id,
            code: p.code,
            name: p.name,
            spec: p.specification || null,
            unit: p.unit || 'EA',
            category_id: p.category || null,
            purchase_price: Number(p.purchase_price) || 0,
            selling_price: Number(p.selling_price) || 0,
            safety_stock: p.stock_quantity || p.min_stock || 0,
            memo: p.memo || null,
            is_active: p.is_active,
            created_at: p.created_at,
            updated_at: p.updated_at || null,
        } as ERPProduct));
    }, [search, contextProducts, searchProducts]);

    // ERPProduct → ProductInfo 변환
    const convertToProductInfo = (p: ERPProduct): ProductInfo => ({
        code: p.code,
        name: p.name,
        stock: p.safety_stock,
        lastPurchase: 0,
        lastPrice: Number(p.purchase_price), // 매입전표는 purchase_price 사용
        optimalStock: p.safety_stock,
    });

    // 상품 선택 시 초기값 설정
    const handleProductClick = (erpProduct: ERPProduct) => {
        const product = convertToProductInfo(erpProduct);
        setSelectedProduct(product);
        setQuantity(1);
        setUnitPrice(product.lastPrice);
        setMemo("");
    };

    // 추가 버튼 클릭
    const handleAdd = () => {
        if (!selectedProduct) return;
        onSelect({
            product: selectedProduct,
            quantity,
            unitPrice,
            memo,
        });
        // 초기화
        setSelectedProduct(null);
        setQuantity(1);
        setUnitPrice(0);
        setMemo("");
        setSearch("");
        onClose();
    };

    // 팝업 닫을 때 초기화
    const handleClose = () => {
        setSelectedProduct(null);
        setQuantity(1);
        setUnitPrice(0);
        setMemo("");
        setSearch("");
        onClose();
    };

    // 공급가액 계산
    const supplyAmount = quantity * unitPrice;

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
            <div className="w-[650px] rounded-lg border bg-white shadow-xl">
                <div className="flex items-center justify-between border-b bg-green-600 px-4 py-2 text-white">
                    <span className="font-medium">상품 추가</span>
                    <button onClick={handleClose} className="hover:bg-green-700 rounded p-1">
                        <X className="h-4 w-4" />
                    </button>
                </div>
                <div className="p-4">
                    {/* 검색 영역 */}
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

                    {/* 상품 목록 */}
                    <div className="h-[200px] overflow-auto border rounded mb-4">
                        {loading ? (
                            <div className="flex h-full items-center justify-center">
                                <Loader2 className="h-6 w-6 animate-spin text-green-600" />
                                <span className="ml-2 text-sm text-gray-500">로딩 중...</span>
                            </div>
                        ) : error ? (
                            <div className="flex h-full items-center justify-center text-red-500 text-sm">
                                {error}
                            </div>
                        ) : products.length === 0 ? (
                            <div className="flex h-full items-center justify-center text-gray-500 text-sm">
                                {search ? "검색 결과가 없습니다." : "등록된 상품이 없습니다."}
                            </div>
                        ) : (
                            <table className="w-full text-sm">
                                <thead className="bg-gray-100 sticky top-0">
                                    <tr>
                                        <th className="px-3 py-2 text-left">코드</th>
                                        <th className="px-3 py-2 text-left">상품명</th>
                                        <th className="px-3 py-2 text-right">현재재고</th>
                                        <th className="px-3 py-2 text-right">매입단가</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {products.map((product) => (
                                        <tr
                                            key={product.id}
                                            className={`border-t cursor-pointer ${
                                                selectedProduct?.code === product.code
                                                    ? "bg-green-100"
                                                    : "hover:bg-green-50"
                                            }`}
                                            onClick={() => handleProductClick(product)}
                                        >
                                            <td className="px-3 py-2">{product.code}</td>
                                            <td className="px-3 py-2 font-medium">{product.name}</td>
                                            <td className="px-3 py-2 text-right">
                                                <span className={product.safety_stock < 10 ? "text-red-600" : ""}>
                                                    {product.safety_stock}
                                                </span>
                                            </td>
                                            <td className="px-3 py-2 text-right">
                                                {Number(product.purchase_price).toLocaleString()}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>

                    {/* 선택된 상품 정보 및 입력 영역 */}
                    {selectedProduct && (
                        <div className="border rounded p-3 bg-green-50">
                            <div className="mb-3 flex items-center justify-between">
                                <span className="font-medium text-green-800">
                                    선택: {selectedProduct.name}
                                </span>
                                <span className="text-sm text-gray-600">
                                    현재재고: <span className={selectedProduct.stock < selectedProduct.optimalStock ? "text-red-600 font-medium" : "font-medium"}>{selectedProduct.stock}</span>개
                                    {selectedProduct.stock < selectedProduct.optimalStock && " (부족)"}
                                </span>
                            </div>
                            <div className="grid grid-cols-4 gap-3">
                                <div>
                                    <label className="block text-xs font-medium mb-1">수량</label>
                                    <input
                                        type="number"
                                        value={quantity}
                                        onChange={(e) => setQuantity(Number(e.target.value))}
                                        min={1}
                                        className="w-full rounded border px-2 py-1.5 text-sm text-right focus:border-green-500 focus:outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium mb-1">단가</label>
                                    <input
                                        type="number"
                                        value={unitPrice}
                                        onChange={(e) => setUnitPrice(Number(e.target.value))}
                                        className="w-full rounded border px-2 py-1.5 text-sm text-right focus:border-green-500 focus:outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium mb-1">공급가액</label>
                                    <div className="w-full rounded border bg-gray-100 px-2 py-1.5 text-sm text-right">
                                        {supplyAmount.toLocaleString()}
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-xs font-medium mb-1">메모</label>
                                    <input
                                        type="text"
                                        value={memo}
                                        onChange={(e) => setMemo(e.target.value)}
                                        placeholder="메모 입력..."
                                        className="w-full rounded border px-2 py-1.5 text-sm focus:border-green-500 focus:outline-none"
                                    />
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 버튼 영역 */}
                    <div className="flex justify-end gap-2 mt-4">
                        <button
                            onClick={handleAdd}
                            disabled={!selectedProduct}
                            className={`rounded px-4 py-2 text-sm text-white ${
                                selectedProduct
                                    ? "bg-green-600 hover:bg-green-700"
                                    : "bg-gray-400 cursor-not-allowed"
                            }`}
                        >
                            추가
                        </button>
                        <button
                            onClick={handleClose}
                            className="rounded border bg-gray-200 px-4 py-2 text-sm hover:bg-gray-300"
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
}: {
    isOpen: boolean;
    onClose: () => void;
    onSave: (payment: PaymentInfo) => void;
}) {
    const [gubun, setGubun] = useState("현금출금");
    const [amount, setAmount] = useState(0);
    const cashBalance = 50000;

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
            <div className="w-[350px] rounded-lg border bg-white shadow-xl">
                <div className="flex items-center justify-between border-b bg-amber-500 px-4 py-2 text-white">
                    <span className="font-medium">현금 결제</span>
                    <button onClick={onClose} className="hover:bg-amber-600 rounded p-1">
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
                            <option>현금출금</option>
                            <option>현금입금</option>
                        </select>
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
                        <label className="text-sm">현금보유:</label>
                        <span className="col-span-2 text-sm text-right">{cashBalance.toLocaleString()}</span>
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
}: {
    isOpen: boolean;
    onClose: () => void;
    onSave: (payment: PaymentInfo) => void;
}) {
    const { bankAccounts } = useERPData();
    const bankAccountList = useMemo(() => bankAccounts.map(b => ({
        code: b.id || '',
        name: b.bank_name,
        accountNo: b.account_number || '',
        balance: b.balance || 0,
    })), [bankAccounts]);
    const [gubun, setGubun] = useState("은행으로 출금");
    const [fromAccount, setFromAccount] = useState("");
    const [toAccount, setToAccount] = useState("");
    const [amount, setAmount] = useState(0);
    const [fee, setFee] = useState(0);
    const [selectedBank, setSelectedBank] = useState<{ code: string; name: string; accountNo: string; balance: number } | null>(null);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
            <div className="w-[400px] rounded-lg border bg-white shadow-xl">
                <div className="flex items-center justify-between border-b bg-blue-500 px-4 py-2 text-white">
                    <span className="font-medium">계좌 결제</span>
                    <button onClick={onClose} className="hover:bg-blue-600 rounded p-1">
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
                        <input
                            type="number"
                            value={amount}
                            onChange={(e) => setAmount(Number(e.target.value))}
                            className="col-span-2 rounded border px-2 py-1.5 text-sm text-right"
                        />
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
    const [gubun, setGubun] = useState("어음발행");
    const [billNo, setBillNo] = useState("");
    const [amount, setAmount] = useState(0);
    const [dueDate, setDueDate] = useState(new Date().toISOString().split("T")[0]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
            <div className="w-[350px] rounded-lg border bg-white shadow-xl">
                <div className="flex items-center justify-between border-b bg-purple-500 px-4 py-2 text-white">
                    <span className="font-medium">어음 결제</span>
                    <button onClick={onClose} className="hover:bg-purple-600 rounded p-1">
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
                            <option>어음발행</option>
                            <option>어음수취</option>
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
    const [gubun, setGubun] = useState("카드출금");
    const [cardType, setCardType] = useState("");
    const [amount, setAmount] = useState(0);
    const [approvalNo, setApprovalNo] = useState("");
    const [memberName, setMemberName] = useState("");
    const [paymentDate, setPaymentDate] = useState(new Date().toISOString().split("T")[0]);
    const [installment, setInstallment] = useState(1);
    const [feeRate, setFeeRate] = useState(0);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
            <div className="w-[400px] rounded-lg border bg-white shadow-xl">
                <div className="flex items-center justify-between border-b bg-rose-500 px-4 py-2 text-white">
                    <span className="font-medium">카드 결제</span>
                    <button onClick={onClose} className="hover:bg-rose-600 rounded p-1">
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
                            <option>카드출금</option>
                            <option>카드입금</option>
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

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
            <div className="w-[450px] rounded-lg border bg-white shadow-xl">
                <div className="flex items-center justify-between border-b bg-orange-500 px-4 py-2 text-white">
                    <span className="font-medium">메모사항</span>
                    <button onClick={onClose} className="hover:bg-orange-600 rounded p-1">
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

// ==================== Main Component ====================
export function PurchaseVoucherWindow() {
    const { products: contextProducts } = useERPData();
    // 기본 정보
    const [purchaseDate, setPurchaseDate] = useState(new Date().toISOString().split("T")[0]);
    const [selectedSupplier, setSelectedSupplier] = useState<SupplierInfo | null>(null);
    const [supplierSearch, setSupplierSearch] = useState("");
    const [manager, setManager] = useState("");
    const [vatType, setVatType] = useState("부가세별도");
    const [vatRate, setVatRate] = useState(10);

    // 상품 목록
    const [items, setItems] = useState<PurchaseItem[]>([]);
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
    const [showSupplierSearch, setShowSupplierSearch] = useState(false);
    const [showProductSearch, setShowProductSearch] = useState(false);
    const [showCashPayment, setShowCashPayment] = useState(false);
    const [showBankPayment, setShowBankPayment] = useState(false);
    const [showBillPayment, setShowBillPayment] = useState(false);
    const [showCardPayment, setShowCardPayment] = useState(false);
    const [showMemo, setShowMemo] = useState(false);
    const [editingItemId, setEditingItemId] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);

    // 계산
    const supplyAmount = items.reduce((sum, item) => sum + item.supplyAmount, 0);
    const taxAmount = items.reduce((sum, item) => sum + item.vatAmount, 0);
    const totalPurchaseAmount = supplyAmount + taxAmount - discountAmount + expenses;
    const totalPayment = payments.reduce((sum, p) => sum + p.amount, 0);
    const unpaidAmount = totalPurchaseAmount - totalPayment;

    // 거래처 선택 시 자동 입력
    const handleSupplierSelect = useCallback((supplier: SupplierInfo) => {
        setSelectedSupplier(supplier);
        setSupplierSearch(supplier.name);
        setManager(supplier.manager);
        setVatType(supplier.vatType);
        setVatRate(supplier.vatRate);
    }, []);

    // 상품 추가
    const handleAddProduct = useCallback((data: ProductAddData) => {
        const { product, quantity, unitPrice, memo } = data;
        const supplyAmount = quantity * unitPrice;
        const newItem: PurchaseItem = {
            id: String(Date.now()),
            gubun: "구매",
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
        setItems([...items, newItem]);
        setSelectedProduct(product);
    }, [items, vatRate]);

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
    const handleItemChange = useCallback((id: string, field: keyof PurchaseItem, value: string | number) => {
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

    // 결제 추가
    const handleAddPayment = useCallback((payment: PaymentInfo) => {
        setPayments([...payments, payment]);
    }, [payments]);

    // 저장
    const handleSave = useCallback(async () => {
        if (isSaving) return;
        setIsSaving(true);
        if (!selectedSupplier) {
            alert("거래처를 선택해주세요.");
            setIsSaving(false);
            return;
        }
        if (items.length === 0) {
            alert("상품을 추가해주세요.");
            setIsSaving(false);
            return;
        }

        try {
            const purchaseData: ERPPurchaseCreate = {
                purchase_date: purchaseDate || new Date().toISOString().split("T")[0],
                supplier_id: selectedSupplier.code,
                status: "confirmed",
                memo: memo || undefined,
                items: items.map((item) => ({
                    product_name: item.productName,
                    spec: item.spec || undefined,
                    unit: item.unit || "EA",
                    quantity: item.quantity || 1,
                    unit_price: item.unitPrice || 0,
                    supply_amount: item.supplyAmount || 0,
                    tax_amount: item.vatAmount || 0,
                    total_amount: (item.supplyAmount || 0) + (item.vatAmount || 0),
                    memo: item.memo || undefined,
                })),
            };

            const result = await api.erp.purchases.create(purchaseData);
            alert(`저장되었습니다. 전표번호: ${result.purchase_number || result.id || ""}`);

            // 폼 초기화
            setItems([]);
            setMemo("");
        } catch (error) {
            alert(`저장 실패: ${error}`);
        } finally {
            setIsSaving(false);
        }
    }, [isSaving, selectedSupplier, items, purchaseDate, memo]);

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

    // 전자세금계산서
    const handleTaxInvoice = useCallback(async () => {
        if (!selectedSupplier) {
            alert("거래처를 선택해주세요.");
            return;
        }
        await handleSave();
        alert("전자세금계산서 화면으로 이동합니다.");
    }, [selectedSupplier, handleSave]);

    // 상품 행 더블클릭 수정
    const handleRowDoubleClick = useCallback((id: string) => {
        setEditingItemId(id);
    }, []);

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
                    <label className="mb-1 block text-xs font-medium">매입일자:</label>
                    <input
                        type="date"
                        value={purchaseDate}
                        onChange={(e) => setPurchaseDate(e.target.value)}
                        className="w-full rounded border px-2 py-1.5 text-sm"
                    />
                </div>
                <div>
                    <label className="mb-1 block text-xs font-medium">매입대상거래처(O):</label>
                    <div className="flex gap-1">
                        <input
                            type="text"
                            value={supplierSearch}
                            onChange={(e) => setSupplierSearch(e.target.value)}
                            className="flex-1 rounded border px-2 py-1.5 text-sm"
                            placeholder="거래처 검색..."
                        />
                        <button
                            onClick={() => setShowSupplierSearch(true)}
                            className="rounded border bg-gray-100 px-2 py-1 text-sm hover:bg-gray-200"
                        >
                            ...
                        </button>
                    </div>
                </div>
                <div>
                    <label className="mb-1 block text-xs font-medium">매입담당사원(U):</label>
                    <input
                        type="text"
                        value={manager}
                        onChange={(e) => setManager(e.target.value)}
                        className="w-full rounded border px-2 py-1.5 text-sm"
                    />
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

            {/* 구매 상품 섹션 */}
            <div className="flex-1 overflow-hidden p-2">
                <div className="flex h-full flex-col rounded border bg-white">
                    <div className="flex items-center justify-between border-b bg-[#fff4e8] px-3 py-1.5">
                        <span className="text-sm font-medium">■ 구매하는 상품 ( {items.length} 품목)</span>
                        <div className="flex gap-1">
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
                        <table className="w-full text-xs">
                            <thead className="sticky top-0 bg-[#f5f5f5]">
                                <tr className="border-b">
                                    <th className="w-16 border-r px-2 py-1.5 text-center">구분</th>
                                    <th className="w-40 border-r px-2 py-1.5 text-left">상품명</th>
                                    <th className="w-24 border-r px-2 py-1.5 text-left">규격</th>
                                    <th className="w-24 border-r px-2 py-1.5 text-left">상세규격</th>
                                    <th className="w-16 border-r px-2 py-1.5 text-center">단위</th>
                                    <th className="w-16 border-r px-2 py-1.5 text-right">수량</th>
                                    <th className="w-24 border-r px-2 py-1.5 text-right">단가</th>
                                    <th className="w-28 border-r px-2 py-1.5 text-right">공급가액</th>
                                    <th className="w-32 border-r px-2 py-1.5 text-left">메모</th>
                                    <th className="w-24 px-2 py-1.5 text-right">부가세액</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item) => (
                                    <tr
                                        key={item.id}
                                        className={`border-b cursor-pointer hover:bg-orange-50 ${selectedItemId === item.id ? "bg-orange-100" : ""}`}
                                        onClick={() => {
                                            setSelectedItemId(item.id);
                                            const ctxProduct = contextProducts.find((p) => p.name === item.productName);
                                            if (ctxProduct) {
                                                setSelectedProduct({
                                                    code: ctxProduct.code,
                                                    name: ctxProduct.name,
                                                    stock: ctxProduct.stock_quantity || ctxProduct.min_stock || 0,
                                                    lastPurchase: 0,
                                                    lastPrice: Number(ctxProduct.purchase_price) || 0,
                                                    optimalStock: ctxProduct.min_stock || 0,
                                                });
                                            }
                                        }}
                                        onDoubleClick={() => handleRowDoubleClick(item.id)}
                                    >
                                        <td className="border-r px-2 py-1 text-center">
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
                                        <td className="border-r px-2 py-1">{item.productName}</td>
                                        <td className="border-r px-2 py-1">{item.spec}</td>
                                        <td className="border-r px-2 py-1">{item.detailSpec}</td>
                                        <td className="border-r px-2 py-1 text-center">{item.unit}</td>
                                        <td className="border-r px-2 py-1 text-right">
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
                                        <td className="border-r px-2 py-1 text-right">
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
                                        <td className="border-r px-2 py-1 text-right">{item.supplyAmount.toLocaleString()}</td>
                                        <td className="border-r px-2 py-1">{item.memo}</td>
                                        <td className="px-2 py-1 text-right">{item.vatAmount.toLocaleString()}</td>
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
                            <div className="flex justify-between">
                                <span className="font-medium">매입액:</span>
                                <span className="font-medium">{totalPurchaseAmount.toLocaleString()}</span>
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
                    <div className="h-[72px] rounded border bg-white p-2 transition-all duration-200 ease-in-out">
                        <div className="mb-1 text-xs font-medium">■ 선택된 업체: <span className="font-normal text-orange-600 transition-all duration-200">{selectedSupplier?.name || "(선택 없음)"}</span></div>
                        <div className="grid grid-cols-3 gap-x-4 gap-y-1 text-xs">
                            <div className="flex justify-between">
                                <span>미수금액:</span>
                                <span className="transition-all duration-200">{selectedSupplier?.receivable.toLocaleString() || 0}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>팩스번호:</span>
                                <span className="transition-all duration-200">{selectedSupplier?.fax || "-"}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>미지급액:</span>
                                <span className="text-red-600 transition-all duration-200">{selectedSupplier?.payable.toLocaleString() || 0}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>전화번호:</span>
                                <span className="transition-all duration-200">{selectedSupplier?.phone || "-"}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>신용한도:</span>
                                <span className="transition-all duration-200">{selectedSupplier?.creditLimit.toLocaleString() || 0}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>최종거래:</span>
                                <span className="transition-all duration-200">{selectedSupplier?.lastTransaction || "-"}</span>
                            </div>
                        </div>
                    </div>
                    <div className="h-[72px] rounded border bg-white p-2 transition-all duration-200 ease-in-out">
                        <div className="mb-1 text-xs font-medium">■ 선택된 상품: <span className="font-normal text-green-600 transition-all duration-200">{selectedProduct?.name || "(선택 없음)"}</span></div>
                        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                            <div className="flex justify-between">
                                <span>보유재고:</span>
                                <span className="transition-all duration-200">{selectedProduct?.stock || 0}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>최종단가:</span>
                                <span className="transition-all duration-200">{selectedProduct?.lastPrice.toLocaleString() || 0}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>최종매입:</span>
                                <span className="transition-all duration-200">{selectedProduct?.lastPurchase || 0}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>적정재고:</span>
                                <span className="transition-all duration-200">{selectedProduct?.optimalStock || 0}</span>
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
                            onClick={handleSave}
                            disabled={isSaving}
                            className="rounded border bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
                        >
                            저 장
                        </button>
                        <button className="rounded border bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300">
                            취 소
                        </button>
                    </div>
                </div>
            </div>

            {/* 팝업들 */}
            <SupplierSearchPopup
                isOpen={showSupplierSearch}
                onClose={() => setShowSupplierSearch(false)}
                onSelect={handleSupplierSelect}
                searchTerm={supplierSearch}
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
            />
            <BankPaymentPopup
                isOpen={showBankPayment}
                onClose={() => setShowBankPayment(false)}
                onSave={handleAddPayment}
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
        </div>
    );
}
