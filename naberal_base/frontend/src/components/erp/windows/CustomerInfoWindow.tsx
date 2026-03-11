"use client";

import React, { useState } from "react";

interface Customer {
  id: string;
  code: string;              // 코드
  customerName: string;      // 거래처명
  customerType: string;      // 거래처구분 (매출처, 매입처, 매입매출처)
  phone: string;             // 전화번호
  mobile: string;            // 핸드폰
  fax: string;               // 팩스번호
  email: string;             // E메일주소
  homepage: string;          // 홈페이지
  zipCode: string;           // 우편번호
  address: string;           // 주소
  businessName: string;      // 상호(사업장명)
  businessNumber: string;    // 사업자등록번호
  businessType: string;      // 업태
  businessItem: string;      // 종목
  representative: string;    // 성명(대표자)
  manager: string;           // 담당사원
  useYn: string;             // 사용여부
}

// 이지판매재고관리 원본 데이터 100% 복제 (2025-12-05 스크린샷 기준)
const ORIGINAL_CUSTOMERS: Customer[] = [
  {
    id: "1",
    code: "m001",
    customerName: "테스트사업장",
    customerType: "매출처",
    phone: "02-456-7890",
    mobile: "010-456-7890",
    fax: "02-145-6789",
    email: "12345@naver.com",
    homepage: "",
    zipCode: "140-888",
    address: "서울 용산구 한남대로 12 (한남동)",
    businessName: "테스트사업장",
    businessNumber: "123-45-78901",
    businessType: "서비스",
    businessItem: "서비스",
    representative: "김사장",
    manager: "김이지",
    useYn: "사용",
  },
  {
    id: "2",
    code: "m002",
    customerName: "이지사업장",
    customerType: "매입처",
    phone: "032-452-7890",
    mobile: "010-789-1234",
    fax: "032-111-2222",
    email: "1111@hanmail.net",
    homepage: "",
    zipCode: "422-814",
    address: "경기 부천시 소사구 경인로 4 (소사동)",
    businessName: "이지사업장",
    businessNumber: "325-68-95123",
    businessType: "유통",
    businessItem: "유통",
    representative: "김사장",
    manager: "이판매",
    useYn: "사용",
  },
  {
    id: "3",
    code: "m003",
    customerName: "재고사업장",
    customerType: "매입매출처",
    phone: "051-754-1234",
    mobile: "010-666-7777",
    fax: "051-754-5678",
    email: "sodftma@hanmail.net",
    homepage: "",
    zipCode: "609-851",
    address: "부산 금정구 가마실로 1 (부곡동)",
    businessName: "재고사업장",
    businessNumber: "456-12-34567",
    businessType: "제조",
    businessItem: "제조",
    representative: "최사장",
    manager: "박재고",
    useYn: "사용",
  },
];

// 거래처구분 목록
const CUSTOMER_TYPES = ["매출처", "매입처", "매입매출처"];

// 담당사원 목록
const MANAGERS = ["김이지", "이판매", "박재고", "최영업"];

const emptyCustomer: Customer = {
  id: "",
  code: "",
  customerName: "",
  customerType: "매출처",
  phone: "",
  mobile: "",
  fax: "",
  email: "",
  homepage: "",
  zipCode: "",
  address: "",
  businessName: "",
  businessNumber: "",
  businessType: "",
  businessItem: "",
  representative: "",
  manager: "",
  useYn: "사용",
};

export function CustomerInfoWindow() {
  const [customers, setCustomers] = useState<Customer[]>(ORIGINAL_CUSTOMERS);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRow, setSelectedRow] = useState<number | null>(null);

  // 모달 상태
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit">("add");
  const [editForm, setEditForm] = useState<Customer>(emptyCustomer);

  const filteredCustomers = customers.filter(
    (c) =>
      c.customerName.includes(searchQuery) ||
      c.code.includes(searchQuery) ||
      c.businessNumber.includes(searchQuery)
  );

  // 툴바 버튼 핸들러
  const handleAdd = () => {
    const nextCode = `m${String(customers.length + 1).padStart(3, "0")}`;
    setEditForm({ ...emptyCustomer, id: String(Date.now()), code: nextCode });
    setModalMode("add");
    setShowModal(true);
  };

  const handleEdit = () => {
    if (selectedRow === null) {
      alert("수정할 거래처를 선택하세요.");
      return;
    }
    const customer = filteredCustomers[selectedRow];
    setEditForm({ ...customer });
    setModalMode("edit");
    setShowModal(true);
  };

  const handleDelete = () => {
    if (selectedRow === null) {
      alert("삭제할 거래처를 선택하세요.");
      return;
    }
    if (confirm("선택한 거래처를 삭제하시겠습니까?")) {
      const customer = filteredCustomers[selectedRow];
      setCustomers(customers.filter((c) => c.id !== customer.id));
      setSelectedRow(null);
    }
  };

  const handleRefresh = () => {
    setCustomers([...ORIGINAL_CUSTOMERS]);
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
    if (!editForm.customerName) {
      alert("거래처명을 입력하세요.");
      return;
    }
    if (!editForm.code) {
      alert("코드를 입력하세요.");
      return;
    }

    if (modalMode === "add") {
      setCustomers([...customers, editForm]);
    } else {
      setCustomers(
        customers.map((c) => (c.id === editForm.id ? editForm : c))
      );
    }
    setShowModal(false);
    setSelectedRow(null);
  };

  // 저장 후 추가
  const handleSaveAndAdd = () => {
    if (!editForm.customerName) {
      alert("거래처명을 입력하세요.");
      return;
    }
    if (!editForm.code) {
      alert("코드를 입력하세요.");
      return;
    }

    if (modalMode === "add") {
      setCustomers([...customers, editForm]);
    } else {
      setCustomers(
        customers.map((c) => (c.id === editForm.id ? editForm : c))
      );
    }
    // 새 항목으로 초기화
    const nextCode = `m${String(customers.length + 2).padStart(3, "0")}`;
    setEditForm({ ...emptyCustomer, id: String(Date.now()), code: nextCode });
    setModalMode("add");
  };

  const handleCancel = () => {
    setShowModal(false);
  };

  // 행 더블클릭으로 수정
  const handleRowDoubleClick = (index: number) => {
    setSelectedRow(index);
    const customer = filteredCustomers[index];
    setEditForm({ ...customer });
    setModalMode("edit");
    setShowModal(true);
  };

  // 거래명세서 작성
  const handleCreateStatement = () => {
    if (selectedRow === null) {
      alert("거래처를 선택하세요.");
      return;
    }
    alert("거래명세서 작성 화면으로 이동합니다.");
  };

  // 거래명세서 전송
  const handleSendStatement = () => {
    if (selectedRow === null) {
      alert("거래처를 선택하세요.");
      return;
    }
    alert("거래명세서를 전송합니다.");
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
      <div className="flex items-center justify-between border-b bg-gray-100 px-4 py-2">
        <div className="flex items-center gap-2">
          <span className="text-sm">거래처명:</span>
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

        {/* 우측 버튼들 */}
        <div className="flex items-center gap-2">
          <button className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300">
            자동조절(F3)
          </button>
          <button className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300">
            출력하기
          </button>
          <button
            onClick={handleCreateStatement}
            className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
          >
            거래명세서작성
          </button>
          <button
            onClick={handleSendStatement}
            className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
          >
            거래명세서전송
          </button>
        </div>
      </div>

      {/* 그리드 - 이지판매재고관리 컬럼 100% */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 text-center font-normal w-8">
                <input type="checkbox" />
              </th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal w-16">코드</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal w-28">거래처명</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal w-24">거래처구분</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal w-28">전화번호</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal w-28">핸드폰</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal w-28">팩스번호</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal w-36">E메일주소</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal w-20">우편번호</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">주소</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal w-28">상호(사업장명)</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal w-28">사업자등록번호</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal w-20">업태</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal w-20">종목</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal w-20">성명(대표자)</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal w-20">담당사원</th>
              <th className="border border-gray-400 px-2 py-1 text-center font-normal w-16">사용</th>
            </tr>
          </thead>
          <tbody>
            {filteredCustomers.map((customer, index) => (
              <tr
                key={customer.id}
                className={`cursor-pointer ${
                  selectedRow === index ? "bg-[#316AC5] text-white" : "bg-white hover:bg-gray-100"
                }`}
                onClick={() => setSelectedRow(index)}
                onDoubleClick={() => handleRowDoubleClick(index)}
              >
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <input type="checkbox" />
                </td>
                <td className="border border-gray-300 px-2 py-1">{customer.code}</td>
                <td className="border border-gray-300 px-2 py-1">{customer.customerName}</td>
                <td className="border border-gray-300 px-2 py-1">{customer.customerType}</td>
                <td className="border border-gray-300 px-2 py-1">{customer.phone}</td>
                <td className="border border-gray-300 px-2 py-1">{customer.mobile}</td>
                <td className="border border-gray-300 px-2 py-1">{customer.fax}</td>
                <td className="border border-gray-300 px-2 py-1">{customer.email}</td>
                <td className="border border-gray-300 px-2 py-1">{customer.zipCode}</td>
                <td className="border border-gray-300 px-2 py-1">{customer.address}</td>
                <td className="border border-gray-300 px-2 py-1">{customer.businessName}</td>
                <td className="border border-gray-300 px-2 py-1">{customer.businessNumber}</td>
                <td className="border border-gray-300 px-2 py-1">{customer.businessType}</td>
                <td className="border border-gray-300 px-2 py-1">{customer.businessItem}</td>
                <td className="border border-gray-300 px-2 py-1">{customer.representative}</td>
                <td className="border border-gray-300 px-2 py-1">{customer.manager}</td>
                <td className="border border-gray-300 px-2 py-1 text-center">{customer.useYn}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="flex items-center justify-end border-t bg-gray-100 px-4 py-1 text-sm text-gray-600">
        <span>전체 {customers.length} 항목</span>
        <span className="mx-4">|</span>
        <span>{filteredCustomers.length} 항목표시</span>
      </div>

      {/* 거래처 등록 모달 - 이지판매재고관리 100% 복제 */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-[700px] rounded bg-gray-200 shadow-lg">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between border-b border-gray-400 bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">거래처 정보입력</span>
              <button
                onClick={handleCancel}
                className="text-white hover:text-gray-200"
              >
                ✕
              </button>
            </div>

            {/* 모달 내용 */}
            <div className="bg-[#F0EDE4] p-4 max-h-[70vh] overflow-y-auto">
              <fieldset className="rounded border border-gray-400 p-3">
                <legend className="px-2 text-sm text-blue-700">기본정보</legend>
                <div className="grid grid-cols-[80px_1fr_80px_1fr] gap-2 text-sm">
                  <label className="py-1 text-right">코드:</label>
                  <input
                    type="text"
                    value={editForm.code}
                    onChange={(e) => setEditForm({ ...editForm, code: e.target.value })}
                    className="w-24 border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">거래처명:</label>
                  <input
                    type="text"
                    value={editForm.customerName}
                    onChange={(e) => setEditForm({ ...editForm, customerName: e.target.value })}
                    className="w-full border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">거래처구분:</label>
                  <select
                    value={editForm.customerType}
                    onChange={(e) => setEditForm({ ...editForm, customerType: e.target.value })}
                    className="w-28 border border-gray-400 px-2 py-1"
                  >
                    {CUSTOMER_TYPES.map((type) => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>

                  <label className="py-1 text-right">담당사원:</label>
                  <select
                    value={editForm.manager}
                    onChange={(e) => setEditForm({ ...editForm, manager: e.target.value })}
                    className="w-28 border border-gray-400 px-2 py-1"
                  >
                    <option value="">선택</option>
                    {MANAGERS.map((mgr) => (
                      <option key={mgr} value={mgr}>{mgr}</option>
                    ))}
                  </select>

                  <label className="py-1 text-right">전화번호:</label>
                  <input
                    type="text"
                    value={editForm.phone}
                    onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                    className="w-36 border border-gray-400 px-2 py-1"
                    placeholder="02-1234-5678"
                  />

                  <label className="py-1 text-right">핸드폰:</label>
                  <input
                    type="text"
                    value={editForm.mobile}
                    onChange={(e) => setEditForm({ ...editForm, mobile: e.target.value })}
                    className="w-36 border border-gray-400 px-2 py-1"
                    placeholder="010-1234-5678"
                  />

                  <label className="py-1 text-right">팩스번호:</label>
                  <input
                    type="text"
                    value={editForm.fax}
                    onChange={(e) => setEditForm({ ...editForm, fax: e.target.value })}
                    className="w-36 border border-gray-400 px-2 py-1"
                    placeholder="02-1234-5679"
                  />

                  <label className="py-1 text-right">E메일:</label>
                  <input
                    type="email"
                    value={editForm.email}
                    onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                    className="w-full border border-gray-400 px-2 py-1"
                    placeholder="email@example.com"
                  />

                  <label className="py-1 text-right">홈페이지:</label>
                  <input
                    type="text"
                    value={editForm.homepage}
                    onChange={(e) => setEditForm({ ...editForm, homepage: e.target.value })}
                    className="col-span-3 border border-gray-400 px-2 py-1"
                    placeholder="http://www.example.com"
                  />

                  <label className="py-1 text-right">우편번호:</label>
                  <div className="flex items-center gap-1">
                    <input
                      type="text"
                      value={editForm.zipCode}
                      onChange={(e) => setEditForm({ ...editForm, zipCode: e.target.value })}
                      className="w-24 border border-gray-400 px-2 py-1"
                    />
                    <button
                      type="button"
                      onClick={() => {
                        const script = document.createElement('script');
                        script.src = 'https://t1.daumcdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js';
                        script.onload = () => {
                          new window.daum!.Postcode({
                            oncomplete: (data: DaumPostcodeResult) => {
                              const fullAddress = data.roadAddress || data.jibunAddress;
                              const extraAddress = data.buildingName ? ` (${data.buildingName})` : '';
                              setEditForm({ ...editForm, zipCode: data.zonecode, address: fullAddress + extraAddress });
                            },
                            width: '100%',
                            height: '100%',
                          }).open({
                            left: (window.screen.width / 2) - 250,
                            top: (window.screen.height / 2) - 300,
                          });
                        };
                        script.onerror = () => {
                          const manualAddress = prompt('주소 검색 서비스에 연결할 수 없습니다.\n주소를 직접 입력해주세요:');
                          if (manualAddress) {
                            setEditForm({ ...editForm, address: manualAddress });
                          }
                        };
                        document.body.appendChild(script);
                      }}
                      className="rounded border border-gray-400 bg-gray-100 px-2 py-1 text-xs hover:bg-gray-200"
                    >
                      우편번호찾기
                    </button>
                  </div>

                  <label className="py-1 text-right">주소:</label>
                  <input
                    type="text"
                    value={editForm.address}
                    onChange={(e) => setEditForm({ ...editForm, address: e.target.value })}
                    className="border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">사용여부:</label>
                  <select
                    value={editForm.useYn}
                    onChange={(e) => setEditForm({ ...editForm, useYn: e.target.value })}
                    className="w-20 border border-gray-400 px-2 py-1"
                  >
                    <option value="사용">사용</option>
                    <option value="미사용">미사용</option>
                  </select>
                </div>
              </fieldset>

              <fieldset className="mt-3 rounded border border-gray-400 p-3">
                <legend className="px-2 text-sm text-blue-700">사업자정보</legend>
                <div className="grid grid-cols-[80px_1fr_80px_1fr] gap-2 text-sm">
                  <label className="py-1 text-right">상호:</label>
                  <input
                    type="text"
                    value={editForm.businessName}
                    onChange={(e) => setEditForm({ ...editForm, businessName: e.target.value })}
                    className="w-full border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">사업자번호:</label>
                  <input
                    type="text"
                    value={editForm.businessNumber}
                    onChange={(e) => setEditForm({ ...editForm, businessNumber: e.target.value })}
                    className="w-36 border border-gray-400 px-2 py-1"
                    placeholder="123-45-67890"
                  />

                  <label className="py-1 text-right">대표자:</label>
                  <input
                    type="text"
                    value={editForm.representative}
                    onChange={(e) => setEditForm({ ...editForm, representative: e.target.value })}
                    className="w-24 border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">업태:</label>
                  <input
                    type="text"
                    value={editForm.businessType}
                    onChange={(e) => setEditForm({ ...editForm, businessType: e.target.value })}
                    className="w-28 border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">종목:</label>
                  <input
                    type="text"
                    value={editForm.businessItem}
                    onChange={(e) => setEditForm({ ...editForm, businessItem: e.target.value })}
                    className="w-28 border border-gray-400 px-2 py-1"
                  />
                </div>
              </fieldset>

              <p className="mt-3 text-sm text-gray-600">
                새로운 거래처의 정보를 등록합니다.
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
    </div>
  );
}
