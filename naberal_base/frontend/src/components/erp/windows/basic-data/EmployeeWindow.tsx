"use client";

import React, { useState, useEffect } from "react";
import { useERPData } from "@/contexts/ERPDataContext";

// 사용권한 목록 (이지판매재고관리 스크린샷 100% 기준)
const PERMISSION_LIST = [
  { id: "daily", label: "일별종합현황" },
  { id: "total", label: "종합현황" },
  { id: "initial", label: "초기이월정보" },
  { id: "sales_purchase", label: "매입/매출" },
  { id: "collect_pay", label: "수금/지급" },
  { id: "stock", label: "재고" },
  { id: "cash_salary", label: "입출금/급여관리" },
  { id: "business_price", label: "영업/단가관리" },
  { id: "issue", label: "발행관리" },
  { id: "basic", label: "기초자료" },
  { id: "site", label: "사업장관리" },
];

// 부서 목록 (이지판매재고관리 기준)
const DEPARTMENT_LIST = [
  "영업부",
  "관리부",
  "생산부",
  "구매부",
  "총무부",
  "경리부",
  "기획부",
];

// 직책 목록
const POSITION_LIST = [
  "사원",
  "주임",
  "대리",
  "과장",
  "차장",
  "부장",
  "이사",
  "상무",
  "전무",
  "대표이사",
];

// 은행 목록
const BANK_LIST = [
  "국민은행",
  "신한은행",
  "우리은행",
  "하나은행",
  "농협은행",
  "기업은행",
  "SC제일은행",
  "씨티은행",
  "카카오뱅크",
  "케이뱅크",
  "토스뱅크",
];

interface Employee {
  id: string;
  code: string;           // 사원코드
  name: string;           // 사원명
  password: string;       // 비밀번호
  department: string;     // 부서명
  position: string;       // 직책
  // 사용권한
  permissions: string[];
  // 연락처
  tel: string;            // 전화번호
  mobile: string;         // 휴대전화
  zipCode: string;        // 우편번호
  address1: string;       // 주소1
  address2: string;       // 주소2
  email: string;          // 이메일
  // 기타
  ssn: string;            // 주민등록번호
  hireDate: string;       // 입사일
  isResigned: boolean;    // 퇴사여부
  memo: string;           // 메모
  // 급여정보
  baseSalary: number;     // 기본급
  positionAllowance: number; // 직책수당
  incomeTax: number;      // 소득세
  bankAccount: string;    // 계좌정보
  bankName: string;       // 은행명
  // 4대보험 가입여부
  healthInsurance: boolean;  // 건강보험
  nationalPension: boolean;  // 국민연금
  employmentInsurance: boolean; // 고용보험
  industrialInsurance: boolean; // 산재보험
}

// 이지판매재고관리 원본 데이터 100% 복제 (2025-12-05 스크린샷 기준)
const ORIGINAL_EMPLOYEES: Employee[] = [
  {
    id: "1",
    code: "01",
    name: "김이지",
    password: "1234",
    department: "영업부",
    position: "대리",
    permissions: PERMISSION_LIST.map(p => p.id),
    tel: "02-1234-5678",
    mobile: "010-1234-5678",
    zipCode: "12345",
    address1: "서울특별시 강남구",
    address2: "테헤란로 123",
    email: "kim@test.com",
    ssn: "850101-1234567",
    hireDate: "2020-03-01",
    isResigned: false,
    memo: "",
    baseSalary: 3000000,
    positionAllowance: 200000,
    incomeTax: 150000,
    bankAccount: "123-456-789012",
    bankName: "국민은행",
    healthInsurance: true,
    nationalPension: true,
    employmentInsurance: true,
    industrialInsurance: true,
  },
  {
    id: "2",
    code: "02",
    name: "이판매",
    password: "1234",
    department: "영업부",
    position: "사원",
    permissions: PERMISSION_LIST.map(p => p.id),
    tel: "02-2345-6789",
    mobile: "010-2345-6789",
    zipCode: "12346",
    address1: "서울특별시 서초구",
    address2: "서초대로 456",
    email: "lee@test.com",
    ssn: "900202-2345678",
    hireDate: "2021-05-15",
    isResigned: false,
    memo: "",
    baseSalary: 2500000,
    positionAllowance: 0,
    incomeTax: 100000,
    bankAccount: "234-567-890123",
    bankName: "신한은행",
    healthInsurance: true,
    nationalPension: true,
    employmentInsurance: true,
    industrialInsurance: false,
  },
  {
    id: "3",
    code: "03",
    name: "박재고",
    password: "1234",
    department: "관리부",
    position: "사원",
    permissions: PERMISSION_LIST.map(p => p.id),
    tel: "02-3456-7890",
    mobile: "010-3456-7890",
    zipCode: "12347",
    address1: "서울특별시 송파구",
    address2: "올림픽로 789",
    email: "park@test.com",
    ssn: "950303-1456789",
    hireDate: "2022-01-10",
    isResigned: false,
    memo: "",
    baseSalary: 2500000,
    positionAllowance: 0,
    incomeTax: 100000,
    bankAccount: "345-678-901234",
    bankName: "우리은행",
    healthInsurance: true,
    nationalPension: true,
    employmentInsurance: true,
    industrialInsurance: false,
  },
];

const emptyEmployee: Employee = {
  id: "",
  code: "",
  name: "",
  password: "",
  department: "",
  position: "",
  permissions: [],
  tel: "",
  mobile: "",
  zipCode: "",
  address1: "",
  address2: "",
  email: "",
  ssn: "",
  hireDate: "",
  isResigned: false,
  memo: "",
  baseSalary: 0,
  positionAllowance: 0,
  incomeTax: 0,
  bankAccount: "",
  bankName: "",
  healthInsurance: false,
  nationalPension: false,
  employmentInsurance: false,
  industrialInsurance: false,
};

export function EmployeeWindow() {
  const { employees: ctxEmployees, fetchEmployees, addEmployee, updateEmployee, deleteEmployee } = useERPData();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRow, setSelectedRow] = useState<number | null>(null);

  // 컨텍스트에서 직원 데이터 동기화
  useEffect(() => {
    if (ctxEmployees.length > 0) {
      setEmployees(ctxEmployees.map(e => ({
        id: e.id,
        code: e.code,
        name: e.name,
        password: "",
        department: e.department || "",
        position: e.position || "",
        permissions: PERMISSION_LIST.map(p => p.id),
        tel: e.phone || "",
        mobile: "",
        zipCode: "",
        address1: "",
        address2: "",
        email: e.email || "",
        ssn: "",
        hireDate: e.hire_date || "",
        isResigned: !e.is_active,
        memo: "",
        baseSalary: 0,
        positionAllowance: 0,
        incomeTax: 0,
        bankAccount: "",
        bankName: "",
        healthInsurance: false,
        nationalPension: false,
        employmentInsurance: false,
        industrialInsurance: false,
      })));
    }
  }, [ctxEmployees]);

  // 마운트 시 직원 데이터 로드
  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);

  // 모달 상태
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit">("add");
  const [editForm, setEditForm] = useState<Employee>(emptyEmployee);
  const [activeTab, setActiveTab] = useState(0);

  // 부서 선택 모달
  const [showDeptModal, setShowDeptModal] = useState(false);

  const tabs = ["기본정보", "사용권한", "연락처", "기타", "급여정보"];

  const filteredEmployees = employees.filter(
    (e) =>
      e.name.includes(searchQuery) ||
      e.code.includes(searchQuery) ||
      e.department.includes(searchQuery)
  );

  // 툴바 버튼 핸들러
  const handleAdd = () => {
    const nextCode = String(employees.length + 1).padStart(2, "0");
    setEditForm({ ...emptyEmployee, id: String(Date.now()), code: nextCode });
    setModalMode("add");
    setActiveTab(0);
    setShowModal(true);
  };

  const handleEdit = () => {
    if (selectedRow === null) {
      alert("수정할 사원을 선택하세요.");
      return;
    }
    const emp = filteredEmployees[selectedRow];
    setEditForm({ ...emp });
    setModalMode("edit");
    setActiveTab(0);
    setShowModal(true);
  };

  const handleDelete = async () => {
    if (selectedRow === null) {
      alert("삭제할 사원을 선택하세요.");
      return;
    }
    if (confirm("선택한 사원을 삭제하시겠습니까?")) {
      const emp = filteredEmployees[selectedRow];
      await deleteEmployee(emp.id);
      setSelectedRow(null);
    }
  };

  const handleRefresh = () => {
    fetchEmployees();
    setSelectedRow(null);
    setSearchQuery("");
  };

  const handleSearch = () => {
    // 검색은 실시간으로 되므로 별도 처리 불필요
  };

  const handleViewAll = () => {
    setSearchQuery("");
  };

  // 모달 저장 (DB 연동)
  const handleSave = async () => {
    if (!editForm.name) {
      alert("사원명을 입력하세요.");
      return;
    }
    if (editForm.password && editForm.password.length < 8) {
      alert("비밀번호는 8자 이상이어야 합니다.");
      return;
    }

    const payload = {
      name: editForm.name,
      department: editForm.department,
      position: editForm.position,
      tel: editForm.phone,
      email: editForm.email,
    };

    if (modalMode === "add") {
      await addEmployee(payload as any);
    } else {
      await updateEmployee(editForm.id, payload as any);
    }
    setShowModal(false);
    setSelectedRow(null);
  };

  const handleSaveAndAdd = async () => {
    if (!editForm.name) {
      alert("사원명을 입력하세요.");
      return;
    }

    const payload = {
      name: editForm.name,
      department: editForm.department,
      position: editForm.position,
      tel: editForm.phone,
      email: editForm.email,
    };

    if (modalMode === "add") {
      await addEmployee(payload as any);
    } else {
      await updateEmployee(editForm.id, payload as any);
    }

    // 새 항목 준비
    const nextCode = String(employees.length + 2).padStart(2, "0");
    setEditForm({ ...emptyEmployee, id: String(Date.now()), code: nextCode });
    setModalMode("add");
    setActiveTab(0);
  };

  const handleCancel = () => {
    setShowModal(false);
  };

  // 권한 토글
  const togglePermission = (permId: string) => {
    const newPerms = editForm.permissions.includes(permId)
      ? editForm.permissions.filter((p) => p !== permId)
      : [...editForm.permissions, permId];
    setEditForm({ ...editForm, permissions: newPerms });
  };

  // 전체 권한 선택/해제
  const toggleAllPermissions = () => {
    if (editForm.permissions.length === PERMISSION_LIST.length) {
      setEditForm({ ...editForm, permissions: [] });
    } else {
      setEditForm({ ...editForm, permissions: PERMISSION_LIST.map((p) => p.id) });
    }
  };

  // 행 더블클릭으로 수정
  const handleRowDoubleClick = (index: number) => {
    setSelectedRow(index);
    const emp = filteredEmployees[index];
    setEditForm({ ...emp });
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
        <span className="text-sm">사원명:</span>
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
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">코드</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">성명</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">주민등록번호</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">우편번호</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">주소1</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">주소2</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">전화번호</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">휴대전화번호</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">입사일</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">소속부서</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">직책</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">메모</th>
            </tr>
          </thead>
          <tbody>
            {filteredEmployees.map((emp, index) => (
              <tr
                key={emp.id}
                className={`cursor-pointer ${
                  selectedRow === index ? "bg-[#316AC5] text-white" : "bg-white hover:bg-gray-100"
                }`}
                onClick={() => setSelectedRow(index)}
                onDoubleClick={() => handleRowDoubleClick(index)}
              >
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <input type="checkbox" />
                </td>
                <td className="border border-gray-300 px-2 py-1">{emp.code}</td>
                <td className="border border-gray-300 px-2 py-1">{emp.name}</td>
                <td className="border border-gray-300 px-2 py-1">{emp.ssn}</td>
                <td className="border border-gray-300 px-2 py-1">{emp.zipCode}</td>
                <td className="border border-gray-300 px-2 py-1">{emp.address1}</td>
                <td className="border border-gray-300 px-2 py-1">{emp.address2}</td>
                <td className="border border-gray-300 px-2 py-1">{emp.tel}</td>
                <td className="border border-gray-300 px-2 py-1">{emp.mobile}</td>
                <td className="border border-gray-300 px-2 py-1">{emp.hireDate}</td>
                <td className="border border-gray-300 px-2 py-1">{emp.department}</td>
                <td className="border border-gray-300 px-2 py-1">{emp.position}</td>
                <td className="border border-gray-300 px-2 py-1">{emp.memo}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="flex items-center justify-end border-t bg-gray-100 px-4 py-1 text-sm text-gray-600">
        <span>전체 {employees.length} 항목</span>
        <span className="mx-4">|</span>
        <span>{filteredEmployees.length} 항목표시</span>
      </div>

      {/* 사용자(사원) 정보입력 모달 - 이지판매재고관리 100% 복제 */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-[500px] rounded bg-gray-200 shadow-lg">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between border-b border-gray-400 bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">
                사용자(사원) 정보입력
              </span>
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
              {/* 기본정보 탭 */}
              {activeTab === 0 && (
                <div className="space-y-3">
                  <fieldset className="rounded border border-gray-400 p-3">
                    <legend className="px-2 text-sm text-blue-700">기본정보</legend>
                    <div className="grid grid-cols-[100px_1fr] gap-2 text-sm">
                      <label className="py-1 text-right">사원코드:</label>
                      <input
                        type="text"
                        value={editForm.code}
                        onChange={(e) => setEditForm({ ...editForm, code: e.target.value })}
                        className="w-32 border border-gray-400 px-2 py-1"
                      />

                      <label className="py-1 text-right">사원명:</label>
                      <input
                        type="text"
                        value={editForm.name}
                        onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                        className="w-48 border border-gray-400 px-2 py-1"
                      />

                      <label className="py-1 text-right">비밀번호:</label>
                      <input
                        type="password"
                        value={editForm.password}
                        onChange={(e) => setEditForm({ ...editForm, password: e.target.value })}
                        className="w-48 border border-gray-400 px-2 py-1"
                      />

                      <label className="py-1 text-right">부서명:</label>
                      <div className="flex gap-1">
                        <input
                          type="text"
                          value={editForm.department}
                          readOnly
                          className="w-40 border border-gray-400 bg-white px-2 py-1"
                        />
                        <button
                          onClick={() => setShowDeptModal(true)}
                          className="rounded border border-gray-400 bg-gray-100 px-2 hover:bg-gray-200"
                        >
                          ...
                        </button>
                      </div>

                      <label className="py-1 text-right">직책:</label>
                      <select
                        value={editForm.position}
                        onChange={(e) => setEditForm({ ...editForm, position: e.target.value })}
                        className="w-40 border border-gray-400 px-2 py-1"
                      >
                        <option value="">선택</option>
                        {POSITION_LIST.map((pos) => (
                          <option key={pos} value={pos}>{pos}</option>
                        ))}
                      </select>
                    </div>
                  </fieldset>
                  <p className="text-sm text-gray-600">새로운 사용자(사원)의 정보를 등록합니다.</p>
                </div>
              )}

              {/* 사용권한 탭 */}
              {activeTab === 1 && (
                <div className="space-y-3">
                  <fieldset className="rounded border border-gray-400 p-3">
                    <legend className="px-2 text-sm text-blue-700">사용권한</legend>
                    <div className="mb-2 flex gap-2">
                      <button
                        onClick={toggleAllPermissions}
                        className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
                      >
                        {editForm.permissions.length === PERMISSION_LIST.length ? "전체해제" : "전체선택"}
                      </button>
                    </div>
                    <div className="max-h-[200px] space-y-1 overflow-y-auto">
                      {PERMISSION_LIST.map((perm) => (
                        <label key={perm.id} className="flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={editForm.permissions.includes(perm.id)}
                            onChange={() => togglePermission(perm.id)}
                          />
                          {perm.label}
                        </label>
                      ))}
                    </div>
                  </fieldset>
                  <p className="text-sm text-gray-600">새로운 사용자(사원)의 정보를 등록합니다.</p>
                </div>
              )}

              {/* 연락처 탭 */}
              {activeTab === 2 && (
                <div className="space-y-3">
                  <fieldset className="rounded border border-gray-400 p-3">
                    <legend className="px-2 text-sm text-blue-700">연락처</legend>
                    <div className="grid grid-cols-[100px_1fr] gap-2 text-sm">
                      <label className="py-1 text-right">전화번호:</label>
                      <input
                        type="text"
                        value={editForm.tel}
                        onChange={(e) => setEditForm({ ...editForm, tel: e.target.value })}
                        className="w-48 border border-gray-400 px-2 py-1"
                        placeholder="02-0000-0000"
                      />

                      <label className="py-1 text-right">휴대전화:</label>
                      <input
                        type="text"
                        value={editForm.mobile}
                        onChange={(e) => setEditForm({ ...editForm, mobile: e.target.value })}
                        className="w-48 border border-gray-400 px-2 py-1"
                        placeholder="010-0000-0000"
                      />

                      <label className="py-1 text-right">주소:</label>
                      <div className="space-y-1">
                        <div className="flex gap-1">
                          <input
                            type="text"
                            value={editForm.zipCode}
                            onChange={(e) => setEditForm({ ...editForm, zipCode: e.target.value })}
                            className="w-24 border border-gray-400 px-2 py-1"
                            placeholder="우편번호"
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
                                    setEditForm({ ...editForm, zipCode: data.zonecode, address1: fullAddress + extraAddress });
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
                                  setEditForm({ ...editForm, address1: manualAddress });
                                }
                              };
                              document.body.appendChild(script);
                            }}
                            className="rounded border border-gray-400 bg-gray-100 px-2 hover:bg-gray-200"
                          >
                            우편번호찾기
                          </button>
                        </div>
                        <input
                          type="text"
                          value={editForm.address1}
                          onChange={(e) => setEditForm({ ...editForm, address1: e.target.value })}
                          className="w-full border border-gray-400 px-2 py-1"
                          placeholder="주소"
                        />
                        <input
                          type="text"
                          value={editForm.address2}
                          onChange={(e) => setEditForm({ ...editForm, address2: e.target.value })}
                          className="w-full border border-gray-400 px-2 py-1"
                          placeholder="상세주소"
                        />
                      </div>

                      <label className="py-1 text-right">이메일:</label>
                      <input
                        type="email"
                        value={editForm.email}
                        onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                        className="w-64 border border-gray-400 px-2 py-1"
                        placeholder="email@example.com"
                      />
                    </div>
                  </fieldset>
                  <p className="text-sm text-gray-600">새로운 사용자(사원)의 정보를 등록합니다.</p>
                </div>
              )}

              {/* 기타 탭 */}
              {activeTab === 3 && (
                <div className="space-y-3">
                  <fieldset className="rounded border border-gray-400 p-3">
                    <legend className="px-2 text-sm text-blue-700">기타정보</legend>
                    <div className="grid grid-cols-[100px_1fr] gap-2 text-sm">
                      <label className="py-1 text-right">주민등록번호:</label>
                      <input
                        type="text"
                        value={editForm.ssn}
                        onChange={(e) => setEditForm({ ...editForm, ssn: e.target.value })}
                        className="w-48 border border-gray-400 px-2 py-1"
                        placeholder="000000-0000000"
                      />

                      <label className="py-1 text-right">입사일:</label>
                      <input
                        type="date"
                        value={editForm.hireDate}
                        onChange={(e) => setEditForm({ ...editForm, hireDate: e.target.value })}
                        className="w-40 border border-gray-400 px-2 py-1"
                      />

                      <label className="py-1 text-right">퇴사여부:</label>
                      <label className="flex items-center gap-2 py-1">
                        <input
                          type="checkbox"
                          checked={editForm.isResigned}
                          onChange={(e) => setEditForm({ ...editForm, isResigned: e.target.checked })}
                        />
                        퇴사
                      </label>

                      <label className="py-1 text-right">메모:</label>
                      <textarea
                        value={editForm.memo}
                        onChange={(e) => setEditForm({ ...editForm, memo: e.target.value })}
                        className="h-20 w-full border border-gray-400 px-2 py-1"
                      />
                    </div>
                  </fieldset>
                  <p className="text-sm text-gray-600">새로운 사용자(사원)의 정보를 등록합니다.</p>
                </div>
              )}

              {/* 급여정보 탭 */}
              {activeTab === 4 && (
                <div className="space-y-3">
                  <fieldset className="rounded border border-gray-400 p-3">
                    <legend className="px-2 text-sm text-blue-700">급여정보</legend>
                    <div className="grid grid-cols-[100px_1fr] gap-2 text-sm">
                      <label className="py-1 text-right">기본급:</label>
                      <div className="flex items-center gap-1">
                        <input
                          type="number"
                          value={editForm.baseSalary}
                          onChange={(e) => setEditForm({ ...editForm, baseSalary: Number(e.target.value) })}
                          className="w-32 border border-gray-400 px-2 py-1 text-right"
                        />
                        <span>원</span>
                      </div>

                      <label className="py-1 text-right">직책수당:</label>
                      <div className="flex items-center gap-1">
                        <input
                          type="number"
                          value={editForm.positionAllowance}
                          onChange={(e) => setEditForm({ ...editForm, positionAllowance: Number(e.target.value) })}
                          className="w-32 border border-gray-400 px-2 py-1 text-right"
                        />
                        <span>원</span>
                      </div>

                      <label className="py-1 text-right">소득세:</label>
                      <div className="flex items-center gap-1">
                        <input
                          type="number"
                          value={editForm.incomeTax}
                          onChange={(e) => setEditForm({ ...editForm, incomeTax: Number(e.target.value) })}
                          className="w-32 border border-gray-400 px-2 py-1 text-right"
                        />
                        <span>원</span>
                      </div>

                      <label className="py-1 text-right">계좌정보:</label>
                      <input
                        type="text"
                        value={editForm.bankAccount}
                        onChange={(e) => setEditForm({ ...editForm, bankAccount: e.target.value })}
                        className="w-48 border border-gray-400 px-2 py-1"
                        placeholder="000-000-000000"
                      />

                      <label className="py-1 text-right">은행명:</label>
                      <select
                        value={editForm.bankName}
                        onChange={(e) => setEditForm({ ...editForm, bankName: e.target.value })}
                        className="w-40 border border-gray-400 px-2 py-1"
                      >
                        <option value="">선택</option>
                        {BANK_LIST.map((bank) => (
                          <option key={bank} value={bank}>{bank}</option>
                        ))}
                      </select>
                    </div>
                  </fieldset>

                  <fieldset className="rounded border border-gray-400 p-3">
                    <legend className="px-2 text-sm text-blue-700">4대보험 가입여부</legend>
                    <div className="flex flex-wrap gap-4 text-sm">
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={editForm.healthInsurance}
                          onChange={(e) => setEditForm({ ...editForm, healthInsurance: e.target.checked })}
                        />
                        건강보험
                      </label>
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={editForm.nationalPension}
                          onChange={(e) => setEditForm({ ...editForm, nationalPension: e.target.checked })}
                        />
                        국민연금
                      </label>
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={editForm.employmentInsurance}
                          onChange={(e) => setEditForm({ ...editForm, employmentInsurance: e.target.checked })}
                        />
                        고용보험
                      </label>
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={editForm.industrialInsurance}
                          onChange={(e) => setEditForm({ ...editForm, industrialInsurance: e.target.checked })}
                        />
                        산재보험
                      </label>
                    </div>
                  </fieldset>
                  <p className="text-sm text-gray-600">새로운 사용자(사원)의 정보를 등록합니다.</p>
                </div>
              )}
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

      {/* 부서 선택 모달 */}
      {showDeptModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-[300px] rounded bg-white shadow-lg">
            <div className="flex items-center justify-between border-b bg-gray-200 px-3 py-2">
              <span className="text-sm font-medium">부서 선택</span>
              <button onClick={() => setShowDeptModal(false)} className="hover:text-gray-600">
                ✕
              </button>
            </div>
            <div className="max-h-[300px] overflow-y-auto p-2">
              {DEPARTMENT_LIST.map((dept) => (
                <div
                  key={dept}
                  onClick={() => {
                    setEditForm({ ...editForm, department: dept });
                    setShowDeptModal(false);
                  }}
                  className="cursor-pointer rounded px-3 py-2 text-sm hover:bg-blue-100"
                >
                  {dept}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
