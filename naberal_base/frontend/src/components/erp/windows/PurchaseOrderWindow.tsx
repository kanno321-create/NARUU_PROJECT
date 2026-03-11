"use client";

import React, { useState } from "react";

interface PurchaseOrderItem {
  id: string;
  no: number;           // 번호
  type: string;         // 구분
  productName: string;  // 상품명
  spec: string;         // 규격
  unit: string;         // 단위
  quantity: number;     // 수량
  unitPrice: number;    // 단가
  supplyPrice: number;  // 공급가액
  taxAmount: number;    // 부가세액
}

interface PurchaseOrder {
  id: string;
  issueNo: number;        // 발행번호
  issueDate: string;      // 발행일
  customerName: string;   // 명칭(거래처)
  email: string;          // 이메일
  projectName: string;    // 건명
  totalAmount: number;    // 합계
  voucherIssued: boolean; // 전표발행여부
  emailSentStatus: string;    // 메일전송상태
  emailReadStatus: boolean;   // 메일수신확인
  manager: string;        // 담당자
  employee: string;       // 담당사원
  taxType: string;        // 부가세구분
  taxRate: number;        // 부가세율
  supplyPrice: number;    // 공급가액
  taxAmount: number;      // 세액
  discount: number;       // 할인액
  productPrice: number;   // 상품대금
  shippingCost: number;   // 운송비
  deliveryDate: string;   // 납기일자
  validDate: string;      // 유효일자
  otherTerms: string;     // 기타조건
  note: string;           // 비고
  items: PurchaseOrderItem[];
}

// 이지판매재고관리 원본 데이터 100% 복제 (2025-12-05 스크린샷 기준)
const ORIGINAL_ORDERS: PurchaseOrder[] = [
  {
    id: "1", issueNo: 1, issueDate: "2025-12-01", customerName: "테스트사업장", email: "test@test.com",
    projectName: "테스트 발주", totalAmount: 2200000, voucherIssued: true, emailSentStatus: "전송완료", emailReadStatus: true,
    manager: "김이지", employee: "박담당", taxType: "부가세별도", taxRate: 10, supplyPrice: 2000000, taxAmount: 200000,
    discount: 0, productPrice: 2200000, shippingCost: 0, deliveryDate: "2025-12-10", validDate: "2025-12-31",
    otherTerms: "", note: "", items: []
  },
  {
    id: "2", issueNo: 2, issueDate: "2025-12-03", customerName: "이지사업장", email: "easy@panme.com",
    projectName: "부품 발주", totalAmount: 1650000, voucherIssued: false, emailSentStatus: "미전송", emailReadStatus: false,
    manager: "이지팬", employee: "김영업", taxType: "부가세포함", taxRate: 10, supplyPrice: 1500000, taxAmount: 150000,
    discount: 0, productPrice: 1650000, shippingCost: 0, deliveryDate: "2025-12-15", validDate: "2026-01-15",
    otherTerms: "", note: "", items: []
  },
];

const emptyItem: PurchaseOrderItem = {
  id: "", no: 0, type: "", productName: "", spec: "", unit: "EA", quantity: 0, unitPrice: 0, supplyPrice: 0, taxAmount: 0
};

const emptyOrder: PurchaseOrder = {
  id: "", issueNo: 0, issueDate: "", customerName: "", email: "", projectName: "", totalAmount: 0,
  voucherIssued: false, emailSentStatus: "미전송", emailReadStatus: false, manager: "", employee: "",
  taxType: "부가세별도", taxRate: 10, supplyPrice: 0, taxAmount: 0, discount: 0, productPrice: 0,
  shippingCost: 0, deliveryDate: "", validDate: "", otherTerms: "", note: "", items: []
};

export function PurchaseOrderWindow() {
  const [orders, setOrders] = useState<PurchaseOrder[]>(ORIGINAL_ORDERS);
  const [selectedRow, setSelectedRow] = useState<number | null>(null);

  // 필터
  const [startDate, setStartDate] = useState("2025-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [searchCustomer, setSearchCustomer] = useState("");

  // 모달 상태
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit">("add");
  const [editForm, setEditForm] = useState<PurchaseOrder>(emptyOrder);
  const [editItems, setEditItems] = useState<PurchaseOrderItem[]>([]);
  const [selectedItemRow, setSelectedItemRow] = useState<number | null>(null);

  // 필터링된 발주서 목록
  const filteredOrders = orders.filter((o) => {
    const matchCustomer = !searchCustomer || o.customerName.includes(searchCustomer);
    const matchDate = o.issueDate >= startDate && o.issueDate <= endDate;
    return matchCustomer && matchDate;
  });

  // 등록
  const handleAdd = () => {
    const nextNo = Math.max(...orders.map((o) => o.issueNo), 0) + 1;
    const today = new Date().toISOString().split("T")[0];
    setEditForm({ ...emptyOrder, id: String(Date.now()), issueNo: nextNo, issueDate: today, deliveryDate: today, validDate: today });
    setEditItems([]);
    setModalMode("add");
    setShowModal(true);
  };

  // 수정
  const handleEdit = () => {
    if (selectedRow === null) {
      alert("수정할 발주서를 선택하세요.");
      return;
    }
    const order = filteredOrders[selectedRow];
    setEditForm({ ...order });
    setEditItems([...order.items]);
    setModalMode("edit");
    setShowModal(true);
  };

  // 삭제
  const handleDelete = () => {
    if (selectedRow === null) {
      alert("삭제할 발주서를 선택하세요.");
      return;
    }
    if (confirm("선택한 발주서를 삭제하시겠습니까?")) {
      const order = filteredOrders[selectedRow];
      setOrders(orders.filter((o) => o.id !== order.id));
      setSelectedRow(null);
    }
  };

  // 새로고침
  const handleRefresh = () => {
    setOrders([...ORIGINAL_ORDERS]);
    setSelectedRow(null);
    setSearchCustomer("");
  };

  // 최근한달검색
  const handleLastMonth = () => {
    const today = new Date();
    const lastMonth = new Date(today);
    lastMonth.setMonth(lastMonth.getMonth() - 1);
    setStartDate(lastMonth.toISOString().split("T")[0]);
    setEndDate(today.toISOString().split("T")[0]);
  };

  // 상품 추가
  const handleAddItem = () => {
    const nextNo = editItems.length + 1;
    setEditItems([...editItems, { ...emptyItem, id: String(Date.now()), no: nextNo }]);
  };

  // 상품 수정
  const handleEditItem = () => {
    if (selectedItemRow === null) {
      alert("수정할 상품을 선택하세요.");
      return;
    }
  };

  // 상품 삭제
  const handleDeleteItem = () => {
    if (selectedItemRow === null) {
      alert("삭제할 상품을 선택하세요.");
      return;
    }
    setEditItems(editItems.filter((_, i) => i !== selectedItemRow));
    setSelectedItemRow(null);
  };

  // 금액 계산
  const calculateTotals = () => {
    const supplyPrice = editItems.reduce((sum, item) => sum + item.supplyPrice, 0);
    const taxAmount = editForm.taxType === "부가세별도" ? Math.round(supplyPrice * editForm.taxRate / 100) : 0;
    const productPrice = supplyPrice + taxAmount - editForm.discount;
    const totalAmount = productPrice + editForm.shippingCost;
    setEditForm({ ...editForm, supplyPrice, taxAmount, productPrice, totalAmount });
  };

  // 모달 저장
  const handleSave = () => {
    if (!editForm.customerName) {
      alert("거래처명을 입력하세요.");
      return;
    }
    if (!editForm.projectName) {
      alert("건명을 입력하세요.");
      return;
    }

    const orderToSave = { ...editForm, items: editItems };

    if (modalMode === "add") {
      setOrders([...orders, orderToSave]);
    } else {
      setOrders(orders.map((o) => (o.id === editForm.id ? orderToSave : o)));
    }
    setShowModal(false);
    setSelectedRow(null);
  };

  const handleSaveAndAdd = () => {
    handleSave();
    setTimeout(() => handleAdd(), 100);
  };

  const handleCancel = () => {
    setShowModal(false);
  };

  // 행 더블클릭으로 수정
  const handleRowDoubleClick = (index: number) => {
    setSelectedRow(index);
    const order = filteredOrders[index];
    setEditForm({ ...order });
    setEditItems([...order.items]);
    setModalMode("edit");
    setShowModal(true);
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 - 이지판매재고관리 스타일 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">발주서관리-이지판매상회</span>
      </div>

      {/* 툴바 - 이지판매재고관리 스타일 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button
          onClick={handleAdd}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-green-600">⊕</span> 등록
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-blue-600">✓</span> 수정
        </button>
        <button
          onClick={handleDelete}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-red-600">✕</span> 삭제
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
          <span>A</span> 미리보기
        </button>
        <div className="mx-1 h-6 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
          <span className="text-blue-600">✉</span> 메일전송
        </button>
      </div>

      {/* 검색 영역 */}
      <div className="flex items-center justify-between border-b bg-gray-100 px-4 py-2">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm">검색기간:</span>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="rounded border border-gray-400 px-2 py-1 text-sm"
            />
            <span>~</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="rounded border border-gray-400 px-2 py-1 text-sm"
            />
          </div>
          <button
            onClick={handleLastMonth}
            className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
          >
            최근한달검색(F2)
          </button>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm">거래처:</span>
            <input
              type="text"
              value={searchCustomer}
              onChange={(e) => setSearchCustomer(e.target.value)}
              className="w-40 rounded border border-gray-400 px-2 py-1 text-sm"
            />
            <button className="rounded border border-gray-400 bg-gray-200 px-2 py-1 text-sm hover:bg-gray-300">
              ...
            </button>
          </div>
          <button className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300">
            검 색(F)
          </button>
        </div>
      </div>

      {/* 포인트 정보 */}
      <div className="flex items-center justify-end gap-4 border-b bg-gray-50 px-4 py-2">
        <div className="flex items-center gap-2 text-sm">
          <span className="font-medium">● 포인트 정보</span>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span>접아이디: <span className="text-blue-600">easypanme</span></span>
          <span>충전된 포인트: <span className="text-blue-600 font-medium">160</span></span>
          <button className="text-blue-600 underline hover:text-blue-800">충전하기</button>
        </div>
      </div>

      {/* 그리드 헤더 그룹 */}
      <div className="flex border-b bg-[#E8E4D9] text-xs">
        <div className="flex-1 border-r border-gray-400 px-2 py-1 text-center font-medium">거래처</div>
        <div className="w-48 px-2 py-1 text-center font-medium">발주서</div>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="w-10 border border-gray-400 px-2 py-1 text-center font-normal">
                <input type="checkbox" />
              </th>
              <th className="w-20 border border-gray-400 px-2 py-1 text-center font-normal">발행번호</th>
              <th className="w-24 border border-gray-400 px-2 py-1 text-center font-normal">발행일</th>
              <th className="w-32 border border-gray-400 px-2 py-1 text-left font-normal">명칭</th>
              <th className="w-40 border border-gray-400 px-2 py-1 text-left font-normal">이메일</th>
              <th className="w-40 border border-gray-400 px-2 py-1 text-left font-normal">건명</th>
              <th className="w-28 border border-gray-400 px-2 py-1 text-right font-normal">합계</th>
              <th className="w-20 border border-gray-400 px-2 py-1 text-center font-normal">전표발행여부</th>
              <th className="w-24 border border-gray-400 px-2 py-1 text-center font-normal">메일전송상태</th>
              <th className="w-20 border border-gray-400 px-2 py-1 text-center font-normal">메일수신확인</th>
            </tr>
          </thead>
          <tbody>
            {filteredOrders.map((order, index) => (
              <tr
                key={order.id}
                className={`cursor-pointer ${
                  selectedRow === index
                    ? "bg-[#316AC5] text-white"
                    : "bg-white hover:bg-gray-100"
                }`}
                onClick={() => setSelectedRow(index)}
                onDoubleClick={() => handleRowDoubleClick(index)}
              >
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <input type="checkbox" />
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">{order.issueNo}</td>
                <td className="border border-gray-300 px-2 py-1 text-center">{order.issueDate}</td>
                <td className="border border-gray-300 px-2 py-1">{order.customerName}</td>
                <td className="border border-gray-300 px-2 py-1">{order.email}</td>
                <td className="border border-gray-300 px-2 py-1">{order.projectName}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">{order.totalAmount.toLocaleString()}</td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <input type="checkbox" checked={order.voucherIssued} readOnly />
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  order.emailSentStatus === "전송완료" && selectedRow !== index ? "text-blue-600" : ""
                }`}>
                  {order.emailSentStatus}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <input type="checkbox" checked={order.emailReadStatus} readOnly />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="flex items-center justify-between border-t bg-gray-100 px-4 py-1 text-sm text-gray-600">
        <span>{startDate} ~ {endDate}</span>
        <div className="flex items-center gap-4">
          <span>전체 {orders.length} 건</span>
          <span>|</span>
          <span>조회 {filteredOrders.length} 건</span>
          <span>|</span>
          <span className="text-blue-600">
            합계: {filteredOrders.reduce((sum, o) => sum + o.totalAmount, 0).toLocaleString()}원
          </span>
        </div>
      </div>

      {/* 발주서 작성 모달 - 이지판매재고관리 100% 복제 */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-[700px] rounded bg-gray-200 shadow-lg">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between border-b border-gray-400 bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">발주서 작성</span>
              <div className="flex items-center gap-2">
                <button className="rounded border border-white bg-transparent px-2 py-0.5 text-xs text-white hover:bg-blue-500">
                  불러하기
                </button>
                <button className="rounded border border-white bg-transparent px-2 py-0.5 text-xs text-white hover:bg-blue-500">
                  전표작성
                </button>
                <button onClick={handleCancel} className="text-white hover:text-gray-200">
                  ✕
                </button>
              </div>
            </div>

            {/* 모달 내용 */}
            <div className="max-h-[600px] overflow-y-auto bg-[#F0EDE4] p-4">
              {/* 기본정보 */}
              <fieldset className="rounded border border-gray-400 p-3">
                <legend className="px-2 text-sm text-blue-700">● 기본정보</legend>
                <div className="grid grid-cols-4 gap-2 text-sm">
                  <div className="flex items-center gap-1">
                    <label className="w-16 text-right">발주일자:</label>
                    <input
                      type="date"
                      value={editForm.issueDate}
                      onChange={(e) => setEditForm({ ...editForm, issueDate: e.target.value })}
                      className="flex-1 border border-gray-400 px-2 py-1"
                    />
                  </div>
                  <div className="flex items-center gap-1">
                    <label className="w-20 text-right">대상거래처(O):</label>
                    <input
                      type="text"
                      value={editForm.customerName}
                      onChange={(e) => setEditForm({ ...editForm, customerName: e.target.value })}
                      className="flex-1 border border-gray-400 px-2 py-1"
                    />
                    <button className="rounded border border-gray-400 bg-gray-200 px-1 hover:bg-gray-300">...</button>
                  </div>
                  <div className="flex items-center gap-1">
                    <label className="w-16 text-right">담당사원(U):</label>
                    <input
                      type="text"
                      value={editForm.employee}
                      onChange={(e) => setEditForm({ ...editForm, employee: e.target.value })}
                      className="flex-1 border border-gray-400 px-2 py-1"
                    />
                    <button className="rounded border border-gray-400 bg-gray-200 px-1 hover:bg-gray-300">...</button>
                  </div>
                  <div className="flex items-center gap-1">
                    <label className="w-14 text-right">부가세율:</label>
                    <select
                      value={editForm.taxType}
                      onChange={(e) => setEditForm({ ...editForm, taxType: e.target.value })}
                      className="border border-gray-400 px-1 py-1"
                    >
                      <option value="부가세별도">부가세별도</option>
                      <option value="부가세포함">부가세포함</option>
                      <option value="영세율">영세율</option>
                    </select>
                    <input
                      type="number"
                      value={editForm.taxRate}
                      onChange={(e) => setEditForm({ ...editForm, taxRate: Number(e.target.value) })}
                      className="w-12 border border-gray-400 px-1 py-1 text-right"
                    />
                    <span>%</span>
                  </div>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
                  <div className="flex items-center gap-1">
                    <label className="w-16 text-right">건 명:</label>
                    <input
                      type="text"
                      value={editForm.projectName}
                      onChange={(e) => setEditForm({ ...editForm, projectName: e.target.value })}
                      className="flex-1 border border-gray-400 px-2 py-1"
                    />
                  </div>
                  <div className="flex items-center gap-1">
                    <label className="w-12 text-right">담당자:</label>
                    <input
                      type="text"
                      value={editForm.manager}
                      onChange={(e) => setEditForm({ ...editForm, manager: e.target.value })}
                      className="flex-1 border border-gray-400 px-2 py-1"
                    />
                  </div>
                </div>
              </fieldset>

              {/* 상품추가 */}
              <fieldset className="mt-3 rounded border border-gray-400 p-3">
                <legend className="px-2 text-sm text-blue-700">● 상품추가 ({editItems.length}품목)</legend>
                <div className="mb-2 flex justify-end gap-1">
                  <button
                    onClick={handleAddItem}
                    className="rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
                  >
                    추가
                  </button>
                  <button
                    onClick={handleEditItem}
                    className="rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
                  >
                    수정
                  </button>
                  <button
                    onClick={handleDeleteItem}
                    className="rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
                  >
                    삭제
                  </button>
                </div>
                <div className="max-h-32 overflow-auto border border-gray-400">
                  <table className="w-full border-collapse text-xs">
                    <thead className="sticky top-0 bg-[#E8E4D9]">
                      <tr>
                        <th className="border-b border-gray-300 px-1 py-1">번호</th>
                        <th className="border-b border-gray-300 px-1 py-1">구분</th>
                        <th className="border-b border-gray-300 px-1 py-1">상품명</th>
                        <th className="border-b border-gray-300 px-1 py-1">규격</th>
                        <th className="border-b border-gray-300 px-1 py-1">단위</th>
                        <th className="border-b border-gray-300 px-1 py-1">수량</th>
                        <th className="border-b border-gray-300 px-1 py-1">단가</th>
                        <th className="border-b border-gray-300 px-1 py-1">공급가액</th>
                        <th className="border-b border-gray-300 px-1 py-1">부가세액</th>
                      </tr>
                    </thead>
                    <tbody>
                      {editItems.map((item, index) => (
                        <tr
                          key={item.id}
                          className={`cursor-pointer ${selectedItemRow === index ? "bg-[#316AC5] text-white" : "hover:bg-gray-100"}`}
                          onClick={() => setSelectedItemRow(index)}
                        >
                          <td className="border-b border-gray-300 px-1 py-1 text-center">{item.no}</td>
                          <td className="border-b border-gray-300 px-1 py-1">{item.type}</td>
                          <td className="border-b border-gray-300 px-1 py-1">{item.productName}</td>
                          <td className="border-b border-gray-300 px-1 py-1">{item.spec}</td>
                          <td className="border-b border-gray-300 px-1 py-1">{item.unit}</td>
                          <td className="border-b border-gray-300 px-1 py-1 text-right">{item.quantity}</td>
                          <td className="border-b border-gray-300 px-1 py-1 text-right">{item.unitPrice.toLocaleString()}</td>
                          <td className="border-b border-gray-300 px-1 py-1 text-right">{item.supplyPrice.toLocaleString()}</td>
                          <td className="border-b border-gray-300 px-1 py-1 text-right">{item.taxAmount.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </fieldset>

              {/* 금액 정보 */}
              <div className="mt-3 grid grid-cols-3 gap-3">
                <fieldset className="rounded border border-gray-400 p-2">
                  <legend className="px-2 text-xs text-blue-700">● 상품대금관련</legend>
                  <div className="space-y-1 text-xs">
                    <div className="flex justify-between"><span>공급가액:</span><span>{editForm.supplyPrice.toLocaleString()}</span></div>
                    <div className="flex justify-between"><span>세액:</span><span>{editForm.taxAmount.toLocaleString()}</span></div>
                    <div className="flex items-center justify-between">
                      <span>할인액(-):</span>
                      <input
                        type="number"
                        value={editForm.discount}
                        onChange={(e) => setEditForm({ ...editForm, discount: Number(e.target.value) })}
                        className="w-20 border border-gray-400 px-1 py-0.5 text-right"
                      />
                    </div>
                    <div className="flex justify-between font-medium"><span>상품대금:</span><span>{editForm.productPrice.toLocaleString()}</span></div>
                  </div>
                </fieldset>
                <fieldset className="rounded border border-gray-400 p-2">
                  <legend className="px-2 text-xs text-blue-700">● 기타비용</legend>
                  <div className="space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span>운송비:</span>
                      <input
                        type="number"
                        value={editForm.shippingCost}
                        onChange={(e) => setEditForm({ ...editForm, shippingCost: Number(e.target.value) })}
                        className="w-20 border border-gray-400 px-1 py-0.5 text-right"
                      />
                    </div>
                    <div className="flex justify-between font-medium"><span>총금액:</span><span>{editForm.totalAmount.toLocaleString()}</span></div>
                  </div>
                </fieldset>
                <fieldset className="rounded border border-gray-400 p-2">
                  <legend className="px-2 text-xs text-blue-700">● 비고</legend>
                  <textarea
                    value={editForm.note}
                    onChange={(e) => setEditForm({ ...editForm, note: e.target.value })}
                    className="h-16 w-full resize-none border border-gray-400 p-1 text-xs"
                    placeholder="Ctrl+Enter키로 다음라인으로 이동"
                  />
                </fieldset>
              </div>

              {/* 기타 */}
              <fieldset className="mt-3 rounded border border-gray-400 p-2">
                <legend className="px-2 text-xs text-blue-700">● 기타</legend>
                <div className="flex gap-4 text-xs">
                  <div className="flex items-center gap-1">
                    <label>납기일자:</label>
                    <input
                      type="date"
                      value={editForm.deliveryDate}
                      onChange={(e) => setEditForm({ ...editForm, deliveryDate: e.target.value })}
                      className="border border-gray-400 px-1 py-0.5"
                    />
                  </div>
                  <div className="flex items-center gap-1">
                    <label>유효일자:</label>
                    <input
                      type="date"
                      value={editForm.validDate}
                      onChange={(e) => setEditForm({ ...editForm, validDate: e.target.value })}
                      className="border border-gray-400 px-1 py-0.5"
                    />
                  </div>
                  <div className="flex flex-1 items-center gap-1">
                    <label>기타조건:</label>
                    <input
                      type="text"
                      value={editForm.otherTerms}
                      onChange={(e) => setEditForm({ ...editForm, otherTerms: e.target.value })}
                      className="flex-1 border border-gray-400 px-1 py-0.5"
                    />
                  </div>
                </div>
              </fieldset>
            </div>

            {/* 모달 푸터 */}
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
                취소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
