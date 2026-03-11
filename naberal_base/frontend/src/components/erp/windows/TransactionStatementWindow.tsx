"use client";

import React, { useState } from "react";

// =============================================
// 거래명세서관리 - 이지판매재고관리 100% 복제
// NABERAL Modern Design (white bg, rounded-lg, shadow-sm, blue-600)
// =============================================

interface TransactionStatement {
  id: string;
  issueNumber: string;   // 발행번호
  issueDate: string;     // 발행일
  customerName: string;  // 거래처명
  totalAmount: number;   // 합계
  sendStatus: string;    // 전송상태
  customerStatus: string; // 거래처상태
  errorMessage: string;  // 오류메세지
}

interface Customer {
  code: string;
  name: string;
  representative: string;
  phone: string;
  fax: string;
  email: string;
  address: string;
  businessType: string;
  businessItem: string;
  registrationNo: string;
}

interface StatementItem {
  id: string;
  no: number;
  productName: string;
  spec: string;
  unit: string;
  quantity: number;
  unitPrice: number;
  supplyAmount: number;
  taxAmount: number;
  memo: string;
}

// 거래처 원본 데이터 (이지판매재고관리 기준)
const CUSTOMERS: Customer[] = [
  {
    code: "m001",
    name: "테스트사업장",
    representative: "김사장",
    phone: "02-456-7890",
    fax: "02-456-7891",
    email: "test@test.com",
    address: "서울시 강남구 테헤란로 123",
    businessType: "제조업",
    businessItem: "전자부품",
    registrationNo: "123-45-67890"
  },
  {
    code: "m003",
    name: "재고사업장",
    representative: "최사장",
    phone: "051-754-9652",
    fax: "051-754-9653",
    email: "stock@stock.com",
    address: "부산시 해운대구 센텀로 456",
    businessType: "도소매",
    businessItem: "사무용품",
    registrationNo: "234-56-78901"
  },
  {
    code: "m004",
    name: "나베랄상회",
    representative: "박대표",
    phone: "032-123-4567",
    fax: "032-123-4568",
    email: "naberal@naberal.com",
    address: "인천시 남동구 논현로 789",
    businessType: "서비스",
    businessItem: "소프트웨어",
    registrationNo: "345-67-89012"
  },
];

// 상품 원본 데이터
const PRODUCTS = [
  { code: "P001", name: "노트북", spec: "15인치 i7", unit: "EA", price: 1500000 },
  { code: "P002", name: "모니터", spec: "27인치 QHD", unit: "EA", price: 350000 },
  { code: "P003", name: "키보드", spec: "기계식", unit: "EA", price: 120000 },
  { code: "P004", name: "마우스", spec: "무선", unit: "EA", price: 45000 },
  { code: "P005", name: "복사용지", spec: "A4 500매", unit: "BOX", price: 25000 },
];

// 거래명세서 샘플 데이터
const SAMPLE_STATEMENTS: TransactionStatement[] = [
  { id: "1", issueNumber: "TS-2025-0001", issueDate: "2025-12-01", customerName: "테스트사업장", totalAmount: 3300000, sendStatus: "전송완료", customerStatus: "정상", errorMessage: "" },
  { id: "2", issueNumber: "TS-2025-0002", issueDate: "2025-12-03", customerName: "재고사업장", totalAmount: 1650000, sendStatus: "미전송", customerStatus: "정상", errorMessage: "" },
  { id: "3", issueNumber: "TS-2025-0003", issueDate: "2025-12-05", customerName: "나베랄상회", totalAmount: 825000, sendStatus: "전송실패", customerStatus: "오류", errorMessage: "이메일 주소 오류" },
];

function formatDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}년 ${m}월 ${d}일`;
}

function formatDateShort(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function formatNumber(num: number): string {
  return num.toLocaleString("ko-KR");
}

export function TransactionStatementWindow() {
  const today = new Date();

  // 검색 조건 상태
  const [searchStartDate, setSearchStartDate] = useState(formatDateShort(today));
  const [searchEndDate, setSearchEndDate] = useState(formatDateShort(today));
  const [searchCustomer, setSearchCustomer] = useState("");

  // 거래명세서 목록
  const [statements, setStatements] = useState<TransactionStatement[]>(SAMPLE_STATEMENTS);
  const [selectedRow, setSelectedRow] = useState<number | null>(null);

  // 포인트 정보
  const [pointInfo] = useState({ webId: "easypanme", points: 160 });

  // 모달 상태들
  const [showFormModal, setShowFormModal] = useState(false);
  const [showCustomerModal, setShowCustomerModal] = useState(false);
  const [showProductModal, setShowProductModal] = useState(false);
  const [showMemoModal, setShowMemoModal] = useState(false);
  const [formMode, setFormMode] = useState<"add" | "edit">("add");

  // 거래명세서 작성 폼 상태
  const [formDate, setFormDate] = useState(formatDate(today));
  const [taxType, setTaxType] = useState<"별도" | "포함">("별도");
  const [taxRate, setTaxRate] = useState(10);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [statementItems, setStatementItems] = useState<StatementItem[]>([]);
  const [selectedItemRow, setSelectedItemRow] = useState<number | null>(null);
  const [prevBalance, setPrevBalance] = useState(0);
  const [depositAmount, setDepositAmount] = useState(0);
  const [memoText, setMemoText] = useState("");

  // 검색어 상태
  const [customerSearchQuery, setCustomerSearchQuery] = useState("");
  const [productSearchQuery, setProductSearchQuery] = useState("");

  // 상품 추가 폼 상태
  const [addProductName, setAddProductName] = useState("");
  const [addProductSpec, setAddProductSpec] = useState("");
  const [addProductUnit, setAddProductUnit] = useState("EA");
  const [addProductQty, setAddProductQty] = useState(1);
  const [addProductPrice, setAddProductPrice] = useState(0);
  const [addProductMemo, setAddProductMemo] = useState("");

  // 필터링된 거래처
  const filteredCustomers = CUSTOMERS.filter(
    (c) =>
      c.name.includes(customerSearchQuery) ||
      c.code.includes(customerSearchQuery)
  );

  // 필터링된 상품
  const filteredProducts = PRODUCTS.filter(
    (p) =>
      p.name.includes(productSearchQuery) ||
      p.code.includes(productSearchQuery)
  );

  // 금액 계산
  const supplyTotal = statementItems.reduce((sum, item) => sum + item.supplyAmount, 0);
  const taxTotal = statementItems.reduce((sum, item) => sum + item.taxAmount, 0);
  const grandTotal = supplyTotal + taxTotal;
  const totalBalance = prevBalance - depositAmount + grandTotal;

  // 검색
  const handleSearch = () => {
    // 검색 로직은 API 연동 시 구현
  };

  // 최근 한달 검색
  const handleLastMonthSearch = () => {
    const lastMonth = new Date(today);
    lastMonth.setMonth(lastMonth.getMonth() - 1);
    setSearchStartDate(formatDateShort(lastMonth));
    setSearchEndDate(formatDateShort(today));
  };

  // 등록 모달 열기
  const handleOpenAddModal = () => {
    setFormMode("add");
    setFormDate(formatDate(today));
    setSelectedCustomer(null);
    setStatementItems([]);
    setPrevBalance(0);
    setDepositAmount(0);
    setMemoText("");
    setShowFormModal(true);
  };

  // 수정 모달 열기
  const handleOpenEditModal = () => {
    if (selectedRow === null) {
      alert("수정할 거래명세서를 선택하세요.");
      return;
    }
    setFormMode("edit");
    const stmt = statements[selectedRow];
    const customer = CUSTOMERS.find(c => c.name === stmt.customerName);
    if (customer) {
      setSelectedCustomer(customer);
    }
    // 실제로는 상세 데이터를 API에서 로드
    setStatementItems([
      { id: "1", no: 1, productName: "노트북", spec: "15인치 i7", unit: "EA", quantity: 2, unitPrice: 1500000, supplyAmount: 3000000, taxAmount: 300000, memo: "" }
    ]);
    setShowFormModal(true);
  };

  // 삭제
  const handleDelete = () => {
    if (selectedRow === null) {
      alert("삭제할 거래명세서를 선택하세요.");
      return;
    }
    if (confirm("선택한 거래명세서를 삭제하시겠습니까?")) {
      setStatements(statements.filter((_, idx) => idx !== selectedRow));
      setSelectedRow(null);
    }
  };

  // 거래처 선택
  const handleSelectCustomer = (customer: Customer) => {
    setSelectedCustomer(customer);
    setShowCustomerModal(false);
  };

  // 상품 추가
  const handleAddProduct = () => {
    if (!addProductName) {
      alert("상품명을 입력하세요.");
      return;
    }
    if (addProductQty <= 0) {
      alert("수량을 입력하세요.");
      return;
    }

    const supplyAmount = addProductQty * addProductPrice;
    const taxAmount = taxType === "별도" ? Math.round(supplyAmount * taxRate / 100) : 0;

    const newItem: StatementItem = {
      id: String(Date.now()),
      no: statementItems.length + 1,
      productName: addProductName,
      spec: addProductSpec,
      unit: addProductUnit,
      quantity: addProductQty,
      unitPrice: addProductPrice,
      supplyAmount: supplyAmount,
      taxAmount: taxAmount,
      memo: addProductMemo,
    };
    setStatementItems([...statementItems, newItem]);

    // 초기화
    setAddProductName("");
    setAddProductSpec("");
    setAddProductUnit("EA");
    setAddProductQty(1);
    setAddProductPrice(0);
    setAddProductMemo("");
    setShowProductModal(false);
  };

  // 상품 선택 (카탈로그에서)
  const handleSelectProduct = (product: typeof PRODUCTS[0]) => {
    setAddProductName(product.name);
    setAddProductSpec(product.spec);
    setAddProductUnit(product.unit);
    setAddProductPrice(product.price);
  };

  // 상품 삭제
  const handleDeleteProduct = () => {
    if (selectedItemRow === null) {
      alert("삭제할 상품을 선택하세요.");
      return;
    }
    const newItems = statementItems.filter((_, idx) => idx !== selectedItemRow);
    // 번호 재정렬
    const renumbered = newItems.map((item, idx) => ({ ...item, no: idx + 1 }));
    setStatementItems(renumbered);
    setSelectedItemRow(null);
  };

  // 저장
  const handleSave = () => {
    if (!selectedCustomer) {
      alert("거래처를 선택하세요.");
      return;
    }
    if (statementItems.length === 0) {
      alert("상품을 추가하세요.");
      return;
    }

    if (formMode === "add") {
      const newStatement: TransactionStatement = {
        id: String(Date.now()),
        issueNumber: `TS-2025-${String(statements.length + 1).padStart(4, "0")}`,
        issueDate: formatDateShort(today),
        customerName: selectedCustomer.name,
        totalAmount: grandTotal,
        sendStatus: "미전송",
        customerStatus: "정상",
        errorMessage: "",
      };
      setStatements([...statements, newStatement]);
    } else {
      // 수정 로직
      if (selectedRow !== null) {
        const updated = [...statements];
        updated[selectedRow] = {
          ...updated[selectedRow],
          customerName: selectedCustomer.name,
          totalAmount: grandTotal,
        };
        setStatements(updated);
      }
    }

    alert("저장되었습니다.");
    setShowFormModal(false);
  };

  // 저장 후 추가
  const handleSaveAndAdd = () => {
    if (!selectedCustomer) {
      alert("거래처를 선택하세요.");
      return;
    }
    if (statementItems.length === 0) {
      alert("상품을 추가하세요.");
      return;
    }

    const newStatement: TransactionStatement = {
      id: String(Date.now()),
      issueNumber: `TS-2025-${String(statements.length + 1).padStart(4, "0")}`,
      issueDate: formatDateShort(today),
      customerName: selectedCustomer.name,
      totalAmount: grandTotal,
      sendStatus: "미전송",
      customerStatus: "정상",
      errorMessage: "",
    };
    setStatements([...statements, newStatement]);

    // 폼 초기화
    setSelectedCustomer(null);
    setStatementItems([]);
    setPrevBalance(0);
    setDepositAmount(0);
    setMemoText("");

    alert("저장되었습니다. 새 거래명세서를 입력하세요.");
  };

  // 새로고침
  const handleRefresh = () => {
    setStatements([...SAMPLE_STATEMENTS]);
    setSelectedRow(null);
  };

  return (
    <div className="flex h-full flex-col bg-white">
      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b border-gray-200 bg-gray-50 px-4 py-2">
        <button
          onClick={handleOpenAddModal}
          className="flex items-center gap-1 rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
        >
          <span>+</span> 등록
        </button>
        <button
          onClick={handleOpenEditModal}
          className="flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          <span className="text-blue-600">&#10003;</span> 수정
        </button>
        <button
          onClick={handleDelete}
          className="flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          <span className="text-red-500">&#10005;</span> 삭제
        </button>
        <div className="mx-1 h-6 w-px bg-gray-300" />
        <button
          onClick={handleRefresh}
          className="flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          <span className="text-blue-600">&#8635;</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50">
          <span>&#9776;</span> 표시항목
        </button>
        <button className="flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50">
          <span>A</span> 미리보기
        </button>
        <button className="flex items-center gap-1 rounded-md bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700">
          거래명세서 전송
        </button>
      </div>

      {/* 검색 영역 */}
      <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-4 py-3">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">검색기간:</span>
            <input
              type="date"
              value={searchStartDate}
              onChange={(e) => setSearchStartDate(e.target.value)}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
            />
            <span className="text-gray-400">~</span>
            <input
              type="date"
              value={searchEndDate}
              onChange={(e) => setSearchEndDate(e.target.value)}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
            />
            <button
              onClick={handleLastMonthSearch}
              className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
            >
              최근한달검색(F2)
            </button>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">거래처:</span>
            <input
              type="text"
              value={searchCustomer}
              onChange={(e) => setSearchCustomer(e.target.value)}
              className="w-40 rounded-md border border-gray-300 px-3 py-1.5 text-sm"
            />
            <button className="rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm hover:bg-gray-50">
              ...
            </button>
            <button
              onClick={handleSearch}
              className="rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
            >
              검 색(F)
            </button>
          </div>
        </div>

        {/* 포인트 정보 */}
        <div className="rounded-lg border border-gray-200 bg-white px-4 py-2">
          <div className="text-xs text-gray-500">&#9632;포인트 정보</div>
          <div className="mt-1 flex items-center gap-4 text-sm">
            <div>
              <span className="text-gray-600">웹아이디: </span>
              <span className="font-medium text-gray-800">{pointInfo.webId}</span>
            </div>
            <div>
              <span className="text-gray-600">충전된 포인트: </span>
              <span className="font-bold text-blue-600">{pointInfo.points}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-gray-100">
            <tr>
              <th className="border-b border-gray-300 px-3 py-2 text-center font-medium text-gray-700">
                <input type="checkbox" />
              </th>
              <th className="border-b border-gray-300 px-3 py-2 text-left font-medium text-gray-700">발행번호</th>
              <th className="border-b border-gray-300 px-3 py-2 text-left font-medium text-gray-700">발행일</th>
              <th className="border-b border-gray-300 px-3 py-2 text-left font-medium text-gray-700">거래처명</th>
              <th className="border-b border-gray-300 px-3 py-2 text-right font-medium text-gray-700">합계</th>
              <th className="border-b border-gray-300 px-3 py-2 text-center font-medium text-gray-700">전송상태</th>
              <th className="border-b border-gray-300 px-3 py-2 text-center font-medium text-gray-700">거래처상태</th>
              <th className="border-b border-gray-300 px-3 py-2 text-left font-medium text-gray-700">오류메세지</th>
            </tr>
          </thead>
          <tbody>
            {statements.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-3 py-8 text-center text-gray-400">
                  거래명세서가 없습니다
                </td>
              </tr>
            ) : (
              statements.map((stmt, index) => (
                <tr
                  key={stmt.id}
                  onClick={() => setSelectedRow(index)}
                  onDoubleClick={handleOpenEditModal}
                  className={`cursor-pointer ${
                    selectedRow === index
                      ? "bg-blue-600 text-white"
                      : "hover:bg-gray-50"
                  }`}
                >
                  <td className="border-b border-gray-200 px-3 py-2 text-center">
                    <input type="checkbox" />
                  </td>
                  <td className="border-b border-gray-200 px-3 py-2">{stmt.issueNumber}</td>
                  <td className="border-b border-gray-200 px-3 py-2">{stmt.issueDate}</td>
                  <td className="border-b border-gray-200 px-3 py-2">{stmt.customerName}</td>
                  <td className="border-b border-gray-200 px-3 py-2 text-right">
                    {formatNumber(stmt.totalAmount)}
                  </td>
                  <td className="border-b border-gray-200 px-3 py-2 text-center">
                    <span className={`rounded-full px-2 py-0.5 text-xs ${
                      stmt.sendStatus === "전송완료" ? "bg-green-100 text-green-700" :
                      stmt.sendStatus === "전송실패" ? "bg-red-100 text-red-700" :
                      "bg-gray-100 text-gray-700"
                    }`}>
                      {stmt.sendStatus}
                    </span>
                  </td>
                  <td className="border-b border-gray-200 px-3 py-2 text-center">
                    <span className={`rounded-full px-2 py-0.5 text-xs ${
                      stmt.customerStatus === "정상" ? "bg-blue-100 text-blue-700" :
                      "bg-red-100 text-red-700"
                    }`}>
                      {stmt.customerStatus}
                    </span>
                  </td>
                  <td className="border-b border-gray-200 px-3 py-2 text-red-500">
                    {stmt.errorMessage}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="flex items-center justify-end border-t border-gray-200 bg-gray-50 px-4 py-2 text-sm text-gray-600">
        <span>전체 {statements.length} 건</span>
      </div>

      {/* ========== 거래명세서 작성 모달 ========== */}
      {showFormModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="max-h-[90vh] w-[900px] overflow-auto rounded-lg bg-white shadow-xl">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
              <span className="text-lg font-medium text-gray-800">거래명세서 작성</span>
              <button
                onClick={() => setShowFormModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                &#10005;
              </button>
            </div>

            <div className="p-4">
              {/* ■기본정보 섹션 */}
              <div className="mb-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">&#9632;기본정보</span>
                  <div className="flex gap-2">
                    <button className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm hover:bg-gray-50">
                      출력하기
                    </button>
                    <button className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm hover:bg-gray-50">
                      전장출력
                    </button>
                    <button
                      onClick={() => setShowMemoModal(true)}
                      className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm hover:bg-gray-50"
                    >
                      메모사항
                    </button>
                  </div>
                </div>
                <div className="mt-2 flex items-center gap-8 rounded-lg border border-gray-200 bg-gray-50 p-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">작성일자:</span>
                    <input
                      type="text"
                      value={formDate}
                      readOnly
                      className="w-40 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">부가세율:</span>
                    <select
                      value={taxType}
                      onChange={(e) => setTaxType(e.target.value as "별도" | "포함")}
                      className="rounded-md border border-gray-300 px-3 py-2 text-sm"
                    >
                      <option value="별도">부가세별도</option>
                      <option value="포함">부가세포함</option>
                    </select>
                    <input
                      type="number"
                      value={taxRate}
                      onChange={(e) => setTaxRate(Number(e.target.value))}
                      className="w-16 rounded-md border border-gray-300 px-2 py-2 text-right text-sm"
                    />
                    <span className="text-sm text-gray-600">%</span>
                  </div>
                </div>
              </div>

              {/* ■공급받는자 섹션 */}
              <div className="mb-4">
                <span className="text-sm font-medium text-gray-700">&#9632;공급받는자</span>
                <div className="mt-2 rounded-lg border border-gray-200 bg-gray-50 p-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-center gap-2">
                      <span className="w-24 text-right text-sm text-gray-600">상호(법인명):</span>
                      <input
                        type="text"
                        value={selectedCustomer?.name || ""}
                        readOnly
                        className="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
                      />
                      <button
                        onClick={() => setShowCustomerModal(true)}
                        className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm hover:bg-gray-50"
                      >
                        ...
                      </button>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-24 text-right text-sm text-gray-600">전화번호:</span>
                      <input
                        type="text"
                        value={selectedCustomer?.phone || ""}
                        readOnly
                        className="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-24 text-right text-sm text-gray-600">성명(대표자):</span>
                      <input
                        type="text"
                        value={selectedCustomer?.representative || ""}
                        readOnly
                        className="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-24 text-right text-sm text-gray-600">등록번호:</span>
                      <input
                        type="text"
                        value={selectedCustomer?.registrationNo || ""}
                        readOnly
                        className="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
                      />
                    </div>
                    <div className="col-span-2 flex items-center gap-2">
                      <span className="w-24 text-right text-sm text-gray-600">주소:</span>
                      <input
                        type="text"
                        value={selectedCustomer?.address || ""}
                        readOnly
                        className="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
                      />
                      <button className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm hover:bg-gray-50">
                        ...
                      </button>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-24 text-right text-sm text-gray-600">업태:</span>
                      <input
                        type="text"
                        value={selectedCustomer?.businessType || ""}
                        readOnly
                        className="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-24 text-right text-sm text-gray-600">종목:</span>
                      <input
                        type="text"
                        value={selectedCustomer?.businessItem || ""}
                        readOnly
                        className="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-24 text-right text-sm text-gray-600">E-MAIL:</span>
                      <input
                        type="text"
                        value={selectedCustomer?.email || ""}
                        readOnly
                        className="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-24 text-right text-sm text-gray-600">팩스번호:</span>
                      <input
                        type="text"
                        value={selectedCustomer?.fax || ""}
                        readOnly
                        className="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* ■상품추가 섹션 */}
              <div className="mb-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">
                    &#9632;상품추가 ({statementItems.length}품목)
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setShowProductModal(true)}
                      className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
                    >
                      추가
                    </button>
                    <button className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm hover:bg-gray-50">
                      수정
                    </button>
                    <button
                      onClick={handleDeleteProduct}
                      className="rounded-md border border-red-300 bg-white px-3 py-1.5 text-sm text-red-500 hover:bg-red-50"
                    >
                      삭제
                    </button>
                  </div>
                </div>
                <div className="mt-2 max-h-40 overflow-auto rounded-lg border border-gray-200">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-gray-100">
                      <tr>
                        <th className="border-b border-gray-300 px-2 py-2 text-center font-medium text-gray-700">번호</th>
                        <th className="border-b border-gray-300 px-2 py-2 text-left font-medium text-gray-700">상품명</th>
                        <th className="border-b border-gray-300 px-2 py-2 text-left font-medium text-gray-700">규격</th>
                        <th className="border-b border-gray-300 px-2 py-2 text-center font-medium text-gray-700">단위</th>
                        <th className="border-b border-gray-300 px-2 py-2 text-right font-medium text-gray-700">수량</th>
                        <th className="border-b border-gray-300 px-2 py-2 text-right font-medium text-gray-700">단가</th>
                        <th className="border-b border-gray-300 px-2 py-2 text-right font-medium text-gray-700">공급가액</th>
                        <th className="border-b border-gray-300 px-2 py-2 text-right font-medium text-gray-700">부가세액</th>
                        <th className="border-b border-gray-300 px-2 py-2 text-left font-medium text-gray-700">메모</th>
                      </tr>
                    </thead>
                    <tbody>
                      {statementItems.length === 0 ? (
                        <tr>
                          <td colSpan={9} className="px-3 py-4 text-center text-gray-400">
                            상품을 추가하세요
                          </td>
                        </tr>
                      ) : (
                        statementItems.map((item, index) => (
                          <tr
                            key={item.id}
                            onClick={() => setSelectedItemRow(index)}
                            className={`cursor-pointer ${
                              selectedItemRow === index
                                ? "bg-blue-600 text-white"
                                : "hover:bg-gray-50"
                            }`}
                          >
                            <td className="border-b border-gray-200 px-2 py-2 text-center">{item.no}</td>
                            <td className="border-b border-gray-200 px-2 py-2">{item.productName}</td>
                            <td className="border-b border-gray-200 px-2 py-2">{item.spec}</td>
                            <td className="border-b border-gray-200 px-2 py-2 text-center">{item.unit}</td>
                            <td className="border-b border-gray-200 px-2 py-2 text-right">{item.quantity}</td>
                            <td className="border-b border-gray-200 px-2 py-2 text-right">{formatNumber(item.unitPrice)}</td>
                            <td className="border-b border-gray-200 px-2 py-2 text-right">{formatNumber(item.supplyAmount)}</td>
                            <td className="border-b border-gray-200 px-2 py-2 text-right">{formatNumber(item.taxAmount)}</td>
                            <td className="border-b border-gray-200 px-2 py-2">{item.memo}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* ■금액정보 섹션 */}
              <div className="mb-4">
                <span className="text-sm font-medium text-gray-700">&#9632;금액정보</span>
                <div className="mt-2 rounded-lg border border-gray-200 bg-gray-50 p-4">
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">공급가액:</span>
                      <span className="font-medium text-gray-800">{formatNumber(supplyTotal)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">세액:</span>
                      <span className="font-medium text-gray-800">{formatNumber(taxTotal)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">합계금액:</span>
                      <span className="text-lg font-bold text-blue-600">{formatNumber(grandTotal)}</span>
                    </div>
                  </div>
                  <div className="mt-4 grid grid-cols-3 gap-4 border-t border-gray-300 pt-4 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600">전미수잔액:</span>
                      <input
                        type="number"
                        value={prevBalance}
                        onChange={(e) => setPrevBalance(Number(e.target.value))}
                        className="w-28 rounded-md border border-gray-300 px-2 py-1 text-right text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600">입금액:</span>
                      <input
                        type="number"
                        value={depositAmount}
                        onChange={(e) => setDepositAmount(Number(e.target.value))}
                        className="w-28 rounded-md border border-gray-300 px-2 py-1 text-right text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600">총미수잔액:</span>
                      <input
                        type="number"
                        value={totalBalance}
                        readOnly
                        className="w-28 rounded-md border border-gray-300 bg-gray-100 px-2 py-1 text-right text-sm"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* 모달 푸터 */}
            <div className="flex justify-end gap-2 border-t border-gray-200 bg-gray-50 px-4 py-3">
              <button
                onClick={handleSaveAndAdd}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                저장후추가
              </button>
              <button
                onClick={handleSave}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                저 장
              </button>
              <button
                onClick={() => setShowFormModal(false)}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                취 소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========== 거래처 선택 모달 ========== */}
      {showCustomerModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50">
          <div className="w-[550px] rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
              <span className="text-lg font-medium text-gray-800">거래처 선택</span>
              <button
                onClick={() => setShowCustomerModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                &#10005;
              </button>
            </div>

            <div className="border-b border-gray-200 bg-gray-50 px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">검색어</span>
                <input
                  type="text"
                  value={customerSearchQuery}
                  onChange={(e) => setCustomerSearchQuery(e.target.value)}
                  className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
                  placeholder="코드 또는 거래처명..."
                />
                <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
                  검 색
                </button>
                <button
                  onClick={() => setCustomerSearchQuery("")}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  전체검색
                </button>
              </div>
            </div>

            <div className="max-h-60 overflow-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-gray-100">
                  <tr>
                    <th className="border-b border-gray-300 px-3 py-2 text-left font-medium text-gray-700">코드</th>
                    <th className="border-b border-gray-300 px-3 py-2 text-left font-medium text-gray-700">거래처명</th>
                    <th className="border-b border-gray-300 px-3 py-2 text-left font-medium text-gray-700">전화번호</th>
                    <th className="border-b border-gray-300 px-3 py-2 text-left font-medium text-gray-700">대표자명</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCustomers.map((customer) => (
                    <tr
                      key={customer.code}
                      onDoubleClick={() => handleSelectCustomer(customer)}
                      className="cursor-pointer hover:bg-blue-50"
                    >
                      <td className="border-b border-gray-200 px-3 py-2">{customer.code}</td>
                      <td className="border-b border-gray-200 px-3 py-2">{customer.name}</td>
                      <td className="border-b border-gray-200 px-3 py-2">{customer.phone}</td>
                      <td className="border-b border-gray-200 px-3 py-2">{customer.representative}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex items-center justify-between border-t border-gray-200 bg-gray-50 px-4 py-3">
              <button className="text-sm text-blue-600 hover:underline">관련항목&gt;&gt;</button>
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600">총 {filteredCustomers.length}개 검색됨</span>
                <button
                  onClick={() => setShowCustomerModal(false)}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  확 인
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========== 상품 추가 모달 ========== */}
      {showProductModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50">
          <div className="w-[500px] rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
              <span className="text-lg font-medium text-gray-800">상품 추가</span>
              <button
                onClick={() => setShowProductModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                &#10005;
              </button>
            </div>

            {/* 상품 검색/선택 */}
            <div className="border-b border-gray-200 bg-gray-50 px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">상품검색</span>
                <input
                  type="text"
                  value={productSearchQuery}
                  onChange={(e) => setProductSearchQuery(e.target.value)}
                  className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
                  placeholder="상품코드 또는 상품명..."
                />
              </div>
              {productSearchQuery && (
                <div className="mt-2 max-h-32 overflow-auto rounded-md border border-gray-300 bg-white">
                  {filteredProducts.map((product) => (
                    <div
                      key={product.code}
                      onClick={() => {
                        handleSelectProduct(product);
                        setProductSearchQuery("");
                      }}
                      className="cursor-pointer border-b border-gray-100 px-3 py-2 text-sm hover:bg-blue-50"
                    >
                      [{product.code}] {product.name} - {product.spec} ({formatNumber(product.price)}원)
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="p-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="mb-1 block text-sm text-gray-600">상품명:</label>
                  <input
                    type="text"
                    value={addProductName}
                    onChange={(e) => setAddProductName(e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-600">규격:</label>
                  <input
                    type="text"
                    value={addProductSpec}
                    onChange={(e) => setAddProductSpec(e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-600">단위:</label>
                  <input
                    type="text"
                    value={addProductUnit}
                    onChange={(e) => setAddProductUnit(e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-600">수량:</label>
                  <input
                    type="number"
                    value={addProductQty}
                    onChange={(e) => setAddProductQty(Number(e.target.value))}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-right text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-600">단가:</label>
                  <input
                    type="number"
                    value={addProductPrice}
                    onChange={(e) => setAddProductPrice(Number(e.target.value))}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-right text-sm"
                  />
                </div>
                <div className="col-span-2">
                  <label className="mb-1 block text-sm text-gray-600">메모:</label>
                  <input
                    type="text"
                    value={addProductMemo}
                    onChange={(e) => setAddProductMemo(e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>
              {/* 계산된 금액 표시 */}
              <div className="mt-4 rounded-md bg-blue-50 p-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">공급가액:</span>
                  <span className="font-medium">{formatNumber(addProductQty * addProductPrice)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">부가세액:</span>
                  <span className="font-medium">
                    {formatNumber(taxType === "별도" ? Math.round(addProductQty * addProductPrice * taxRate / 100) : 0)}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 border-t border-gray-200 bg-gray-50 px-4 py-3">
              <button
                onClick={handleAddProduct}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                추가
              </button>
              <button
                onClick={() => setShowProductModal(false)}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========== 메모 모달 ========== */}
      {showMemoModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50">
          <div className="w-[400px] rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
              <span className="text-lg font-medium text-gray-800">메모사항</span>
              <button
                onClick={() => setShowMemoModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                &#10005;
              </button>
            </div>
            <div className="p-4">
              <textarea
                value={memoText}
                onChange={(e) => setMemoText(e.target.value)}
                className="h-40 w-full resize-none rounded-md border border-gray-300 p-3 text-sm"
                placeholder="메모를 입력하세요..."
              />
            </div>
            <div className="flex justify-end gap-2 border-t border-gray-200 bg-gray-50 px-4 py-3">
              <button
                onClick={() => setShowMemoModal(false)}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                확 인
              </button>
              <button
                onClick={() => {
                  setMemoText("");
                  setShowMemoModal(false);
                }}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
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
