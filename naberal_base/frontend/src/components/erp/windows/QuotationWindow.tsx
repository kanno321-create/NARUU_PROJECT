"use client";

import React, { useState } from "react";

interface Quotation {
  id: string;
  issueNo: number;        // 발행번호
  issueDate: string;      // 발행일
  customerName: string;   // 명칭(거래처)
  email: string;          // 이메일
  projectName: string;    // 건명
  totalAmount: number;    // 합계
  voucherIssued: boolean; // 전표발행여부
  emailSentStatus: string;    // 메일전송상태(견적서)
  emailReadStatus: boolean;   // 메일수신확인
  deliverySentStatus: string; // 메일전송상태(납품서)
  deliveryReadStatus: boolean; // 메일수신확인
}

// 이지판매재고관리 원본 데이터 100% 복제 (2025-12-05 스크린샷 기준)
const ORIGINAL_QUOTATIONS: Quotation[] = [
  { id: "1", issueNo: 1, issueDate: "2025-12-01", customerName: "테스트사업장", email: "test@test.com", projectName: "테스트 견적", totalAmount: 1500000, voucherIssued: true, emailSentStatus: "전송완료", emailReadStatus: true, deliverySentStatus: "미전송", deliveryReadStatus: false },
  { id: "2", issueNo: 2, issueDate: "2025-12-03", customerName: "이지사업장", email: "easy@panme.com", projectName: "장비 납품 견적", totalAmount: 3200000, voucherIssued: false, emailSentStatus: "전송완료", emailReadStatus: false, deliverySentStatus: "미전송", deliveryReadStatus: false },
  { id: "3", issueNo: 3, issueDate: "2025-12-05", customerName: "재고사업장", email: "stock@test.com", projectName: "부품 견적", totalAmount: 890000, voucherIssued: false, emailSentStatus: "미전송", emailReadStatus: false, deliverySentStatus: "미전송", deliveryReadStatus: false },
];

const emptyQuotation: Quotation = {
  id: "",
  issueNo: 0,
  issueDate: "",
  customerName: "",
  email: "",
  projectName: "",
  totalAmount: 0,
  voucherIssued: false,
  emailSentStatus: "미전송",
  emailReadStatus: false,
  deliverySentStatus: "미전송",
  deliveryReadStatus: false,
};

export function QuotationWindow() {
  const [quotations, setQuotations] = useState<Quotation[]>(ORIGINAL_QUOTATIONS);
  const [selectedRow, setSelectedRow] = useState<number | null>(null);

  // 필터
  const [startDate, setStartDate] = useState("2024-12-01");
  const [endDate, setEndDate] = useState("2025-12-05");
  const [searchCustomer, setSearchCustomer] = useState("");

  // 모달 상태
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit">("add");
  const [editForm, setEditForm] = useState<Quotation>(emptyQuotation);

  // 필터링된 견적서 목록
  const filteredQuotations = quotations.filter((q) => {
    const matchCustomer = !searchCustomer || q.customerName.includes(searchCustomer);
    const matchDate = q.issueDate >= startDate && q.issueDate <= endDate;
    return matchCustomer && matchDate;
  });

  // 등록
  const handleAdd = () => {
    const nextNo = Math.max(...quotations.map((q) => q.issueNo), 0) + 1;
    const today = new Date().toISOString().split("T")[0];
    setEditForm({ ...emptyQuotation, id: String(Date.now()), issueNo: nextNo, issueDate: today });
    setModalMode("add");
    setShowModal(true);
  };

  // 수정
  const handleEdit = () => {
    if (selectedRow === null) {
      alert("수정할 견적서를 선택하세요.");
      return;
    }
    const quotation = filteredQuotations[selectedRow];
    setEditForm({ ...quotation });
    setModalMode("edit");
    setShowModal(true);
  };

  // 삭제
  const handleDelete = () => {
    if (selectedRow === null) {
      alert("삭제할 견적서를 선택하세요.");
      return;
    }
    if (confirm("선택한 견적서를 삭제하시겠습니까?")) {
      const quotation = filteredQuotations[selectedRow];
      setQuotations(quotations.filter((q) => q.id !== quotation.id));
      setSelectedRow(null);
    }
  };

  // 새로고침
  const handleRefresh = () => {
    setQuotations([...ORIGINAL_QUOTATIONS]);
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

  // 검색
  const handleSearch = () => {
    // 실시간 필터링이므로 별도 처리 불필요
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

    if (modalMode === "add") {
      setQuotations([...quotations, editForm]);
    } else {
      setQuotations(
        quotations.map((q) => (q.id === editForm.id ? editForm : q))
      );
    }
    setShowModal(false);
    setSelectedRow(null);
  };

  const handleCancel = () => {
    setShowModal(false);
  };

  // 행 더블클릭으로 수정
  const handleRowDoubleClick = (index: number) => {
    setSelectedRow(index);
    const quotation = filteredQuotations[index];
    setEditForm({ ...quotation });
    setModalMode("edit");
    setShowModal(true);
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 - 이지판매재고관리 스타일 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">견적서관리-이지판매상회</span>
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

      {/* 검색 영역 - 이지판매재고관리 스타일 */}
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
          <button
            onClick={handleSearch}
            className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
          >
            검 색(F)
          </button>
        </div>
      </div>

      {/* 포인트 정보 - 이지판매재고관리 스타일 */}
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
        <div className="w-48 border-r border-gray-400 px-2 py-1 text-center font-medium">견적서</div>
        <div className="w-48 px-2 py-1 text-center font-medium">납품서</div>
      </div>

      {/* 그리드 - 이지판매재고관리 컬럼 100% */}
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
              <th className="w-24 border border-gray-400 px-2 py-1 text-center font-normal">메일전송상태</th>
              <th className="w-20 border border-gray-400 px-2 py-1 text-center font-normal">메일수신확인</th>
            </tr>
          </thead>
          <tbody>
            {filteredQuotations.map((quotation, index) => (
              <tr
                key={quotation.id}
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
                <td className="border border-gray-300 px-2 py-1 text-center">
                  {quotation.issueNo}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  {quotation.issueDate}
                </td>
                <td className="border border-gray-300 px-2 py-1">
                  {quotation.customerName}
                </td>
                <td className="border border-gray-300 px-2 py-1">
                  {quotation.email}
                </td>
                <td className="border border-gray-300 px-2 py-1">
                  {quotation.projectName}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {quotation.totalAmount.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <input type="checkbox" checked={quotation.voucherIssued} readOnly />
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  quotation.emailSentStatus === "전송완료" && selectedRow !== index ? "text-blue-600" : ""
                }`}>
                  {quotation.emailSentStatus}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <input type="checkbox" checked={quotation.emailReadStatus} readOnly />
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  quotation.deliverySentStatus === "전송완료" && selectedRow !== index ? "text-blue-600" : ""
                }`}>
                  {quotation.deliverySentStatus}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <input type="checkbox" checked={quotation.deliveryReadStatus} readOnly />
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
          <span>전체 {quotations.length} 건</span>
          <span>|</span>
          <span>조회 {filteredQuotations.length} 건</span>
          <span>|</span>
          <span className="text-blue-600">
            합계: {filteredQuotations.reduce((sum, q) => sum + q.totalAmount, 0).toLocaleString()}원
          </span>
        </div>
      </div>

      {/* 견적서 등록/수정 모달 - 이지판매재고관리 100% 복제 */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-[500px] rounded bg-gray-200 shadow-lg">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between border-b border-gray-400 bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">
                {modalMode === "add" ? "견적서 등록" : "견적서 수정"}
              </span>
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
                <legend className="px-2 text-sm text-blue-700">견적서 정보</legend>
                <div className="grid grid-cols-[100px_1fr] gap-2 text-sm">
                  <label className="py-1 text-right">발행번호:</label>
                  <input
                    type="text"
                    value={editForm.issueNo}
                    readOnly
                    className="w-20 border border-gray-400 bg-gray-100 px-2 py-1"
                  />

                  <label className="py-1 text-right">발행일:</label>
                  <input
                    type="date"
                    value={editForm.issueDate}
                    onChange={(e) => setEditForm({ ...editForm, issueDate: e.target.value })}
                    className="w-40 border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">거래처명:</label>
                  <div className="flex items-center gap-1">
                    <input
                      type="text"
                      value={editForm.customerName}
                      onChange={(e) => setEditForm({ ...editForm, customerName: e.target.value })}
                      className="flex-1 border border-gray-400 px-2 py-1"
                    />
                    <button className="rounded border border-gray-400 bg-gray-200 px-2 py-1 hover:bg-gray-300">
                      ...
                    </button>
                  </div>

                  <label className="py-1 text-right">이메일:</label>
                  <input
                    type="email"
                    value={editForm.email}
                    onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                    className="w-full border border-gray-400 px-2 py-1"
                    placeholder="example@email.com"
                  />

                  <label className="py-1 text-right">건명:</label>
                  <input
                    type="text"
                    value={editForm.projectName}
                    onChange={(e) => setEditForm({ ...editForm, projectName: e.target.value })}
                    className="w-full border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">합계금액:</label>
                  <input
                    type="number"
                    value={editForm.totalAmount}
                    onChange={(e) => setEditForm({ ...editForm, totalAmount: Number(e.target.value) })}
                    className="w-40 border border-gray-400 px-2 py-1 text-right"
                  />
                </div>
              </fieldset>

              <fieldset className="mt-3 rounded border border-gray-400 p-3">
                <legend className="px-2 text-sm text-blue-700">전송 상태</legend>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={editForm.voucherIssued}
                      onChange={(e) => setEditForm({ ...editForm, voucherIssued: e.target.checked })}
                    />
                    <label>전표발행 완료</label>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={editForm.emailReadStatus}
                      onChange={(e) => setEditForm({ ...editForm, emailReadStatus: e.target.checked })}
                    />
                    <label>메일 수신 확인</label>
                  </div>
                </div>
              </fieldset>

              <p className="mt-3 text-sm text-gray-600">
                {modalMode === "add" ? "새로운 견적서를 등록합니다." : "선택한 견적서를 수정합니다."}
              </p>
            </div>

            {/* 모달 푸터 - 이지판매재고관리 스타일 */}
            <div className="flex justify-end gap-2 border-t border-gray-400 bg-gray-200 px-4 py-3">
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
    </div>
  );
}
