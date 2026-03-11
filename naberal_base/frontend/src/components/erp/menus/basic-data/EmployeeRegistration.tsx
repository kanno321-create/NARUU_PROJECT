"use client";

import React, { useState } from "react";

interface Employee {
  id: string;
  code: string;
  name: string;
  residentNo: string;
  zipCode: string;
  address1: string;
  address2: string;
  phone: string;
  mobile: string;
  hireDate: string;
  department: string;
  position: string;
  memo: string;
  // 사용권한
  permissions: {
    sales: boolean;
    purchase: boolean;
    inventory: boolean;
    accounting: boolean;
    admin: boolean;
  };
  // 연락처
  email: string;
  fax: string;
  emergencyContact: string;
  emergencyPhone: string;
  // 기타
  birthDate: string;
  gender: string;
  maritalStatus: string;
  militaryService: string;
  education: string;
  // 급여정보
  bankName: string;
  accountNo: string;
  accountHolder: string;
  baseSalary: number;
  allowance: number;
}

// 이지판매재고관리 원본 데이터 100% 복제
const ORIGINAL_EMPLOYEES: Employee[] = [
  {
    id: "1",
    code: "E001",
    name: "김철수",
    residentNo: "850101-1******",
    zipCode: "06234",
    address1: "서울특별시 강남구",
    address2: "테헤란로 123",
    phone: "02-1234-5678",
    mobile: "010-1234-5678",
    hireDate: "2020-03-01",
    department: "영업부",
    position: "과장",
    memo: "영업1팀 담당",
    permissions: { sales: true, purchase: true, inventory: true, accounting: false, admin: false },
    email: "kim@company.com",
    fax: "02-1234-5679",
    emergencyContact: "김영희",
    emergencyPhone: "010-9876-5432",
    birthDate: "1985-01-01",
    gender: "남",
    maritalStatus: "기혼",
    militaryService: "군필",
    education: "대졸",
    bankName: "국민은행",
    accountNo: "123-456-789012",
    accountHolder: "김철수",
    baseSalary: 3500000,
    allowance: 500000,
  },
  {
    id: "2",
    code: "E002",
    name: "이영희",
    residentNo: "900515-2******",
    zipCode: "06789",
    address1: "서울특별시 서초구",
    address2: "반포대로 456",
    phone: "02-2345-6789",
    mobile: "010-2345-6789",
    hireDate: "2021-06-15",
    department: "경리부",
    position: "대리",
    memo: "회계담당",
    permissions: { sales: false, purchase: false, inventory: false, accounting: true, admin: false },
    email: "lee@company.com",
    fax: "02-2345-6780",
    emergencyContact: "이철호",
    emergencyPhone: "010-8765-4321",
    birthDate: "1990-05-15",
    gender: "여",
    maritalStatus: "미혼",
    militaryService: "해당없음",
    education: "대졸",
    bankName: "신한은행",
    accountNo: "110-123-456789",
    accountHolder: "이영희",
    baseSalary: 3000000,
    allowance: 400000,
  },
  {
    id: "3",
    code: "E003",
    name: "박민수",
    residentNo: "880720-1******",
    zipCode: "04567",
    address1: "서울특별시 마포구",
    address2: "월드컵로 789",
    phone: "02-3456-7890",
    mobile: "010-3456-7890",
    hireDate: "2019-01-02",
    department: "관리부",
    position: "부장",
    memo: "총무담당",
    permissions: { sales: true, purchase: true, inventory: true, accounting: true, admin: true },
    email: "park@company.com",
    fax: "02-3456-7891",
    emergencyContact: "박영수",
    emergencyPhone: "010-7654-3210",
    birthDate: "1988-07-20",
    gender: "남",
    maritalStatus: "기혼",
    militaryService: "군필",
    education: "대졸",
    bankName: "우리은행",
    accountNo: "1002-123-456789",
    accountHolder: "박민수",
    baseSalary: 4500000,
    allowance: 700000,
  },
];

const DEPARTMENTS = ["영업부", "경리부", "관리부", "생산부", "구매부", "물류부", "인사부", "기획부"];
const POSITIONS = ["사원", "주임", "대리", "과장", "차장", "부장", "이사", "상무", "전무", "대표"];

export function EmployeeRegistration() {
  const [employees, setEmployees] = useState<Employee[]>(ORIGINAL_EMPLOYEES);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit">("add");
  const [activeTab, setActiveTab] = useState("basic");

  const [formData, setFormData] = useState<Omit<Employee, "id">>({
    code: "",
    name: "",
    residentNo: "",
    zipCode: "",
    address1: "",
    address2: "",
    phone: "",
    mobile: "",
    hireDate: "",
    department: "",
    position: "",
    memo: "",
    permissions: { sales: false, purchase: false, inventory: false, accounting: false, admin: false },
    email: "",
    fax: "",
    emergencyContact: "",
    emergencyPhone: "",
    birthDate: "",
    gender: "남",
    maritalStatus: "미혼",
    militaryService: "해당없음",
    education: "",
    bankName: "",
    accountNo: "",
    accountHolder: "",
    baseSalary: 0,
    allowance: 0,
  });

  const filteredEmployees = employees.filter(
    (e) =>
      e.name.includes(searchQuery) ||
      e.code.includes(searchQuery) ||
      e.department.includes(searchQuery) ||
      e.position.includes(searchQuery)
  );

  const handleAdd = () => {
    setModalMode("add");
    setFormData({
      code: `E${String(employees.length + 1).padStart(3, "0")}`,
      name: "",
      residentNo: "",
      zipCode: "",
      address1: "",
      address2: "",
      phone: "",
      mobile: "",
      hireDate: new Date().toISOString().split("T")[0],
      department: "",
      position: "",
      memo: "",
      permissions: { sales: false, purchase: false, inventory: false, accounting: false, admin: false },
      email: "",
      fax: "",
      emergencyContact: "",
      emergencyPhone: "",
      birthDate: "",
      gender: "남",
      maritalStatus: "미혼",
      militaryService: "해당없음",
      education: "",
      bankName: "",
      accountNo: "",
      accountHolder: "",
      baseSalary: 0,
      allowance: 0,
    });
    setActiveTab("basic");
    setIsModalOpen(true);
  };

  const handleEdit = () => {
    if (!selectedId) return;
    const employee = employees.find((e) => e.id === selectedId);
    if (!employee) return;
    setModalMode("edit");
    const { id, ...rest } = employee;
    setFormData(rest);
    setActiveTab("basic");
    setIsModalOpen(true);
  };

  const handleDelete = () => {
    if (!selectedId) return;
    if (confirm("선택한 사원을 삭제하시겠습니까?")) {
      setEmployees(employees.filter((e) => e.id !== selectedId));
      setSelectedId(null);
    }
  };

  const handleSave = () => {
    if (!formData.name || !formData.code) {
      alert("코드와 성명은 필수 입력 항목입니다.");
      return;
    }

    if (modalMode === "add") {
      const newEmployee: Employee = {
        id: Date.now().toString(),
        ...formData,
      };
      setEmployees([...employees, newEmployee]);
    } else {
      setEmployees(
        employees.map((e) => (e.id === selectedId ? { ...e, ...formData } : e))
      );
    }
    setIsModalOpen(false);
  };

  const handleRowDoubleClick = (employee: Employee) => {
    setSelectedId(employee.id);
    setModalMode("edit");
    const { id, ...rest } = employee;
    setFormData(rest);
    setActiveTab("basic");
    setIsModalOpen(true);
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">부서별사원등록</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button
          onClick={handleAdd}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
          <span>➕</span> 추가
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
          disabled={!selectedId}
        >
          <span>✏️</span> 수정
        </button>
        <button
          onClick={handleDelete}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
          disabled={!selectedId}
        >
          <span>🗑️</span> 삭제
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <span className="text-xs">검색:</span>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-32 rounded border border-gray-400 px-2 py-0.5 text-xs"
          placeholder="성명/부서/직책"
        />
        <button className="rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          검색
        </button>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto p-2">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1">코드</th>
              <th className="border border-gray-400 px-2 py-1">성명</th>
              <th className="border border-gray-400 px-2 py-1">주민등록번호</th>
              <th className="border border-gray-400 px-2 py-1">우편번호</th>
              <th className="border border-gray-400 px-2 py-1">주소1</th>
              <th className="border border-gray-400 px-2 py-1">주소2</th>
              <th className="border border-gray-400 px-2 py-1">전화번호</th>
              <th className="border border-gray-400 px-2 py-1">휴대전화번호</th>
              <th className="border border-gray-400 px-2 py-1">입사일</th>
              <th className="border border-gray-400 px-2 py-1">소속부서</th>
              <th className="border border-gray-400 px-2 py-1">직책</th>
              <th className="border border-gray-400 px-2 py-1">메모</th>
            </tr>
          </thead>
          <tbody>
            {filteredEmployees.map((emp) => (
              <tr
                key={emp.id}
                className={`cursor-pointer ${
                  selectedId === emp.id ? "bg-[#316AC5] text-white" : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(emp.id)}
                onDoubleClick={() => handleRowDoubleClick(emp)}
              >
                <td className="border border-gray-300 px-2 py-1">{emp.code}</td>
                <td className="border border-gray-300 px-2 py-1">{emp.name}</td>
                <td className="border border-gray-300 px-2 py-1">{emp.residentNo}</td>
                <td className="border border-gray-300 px-2 py-1">{emp.zipCode}</td>
                <td className="border border-gray-300 px-2 py-1">{emp.address1}</td>
                <td className="border border-gray-300 px-2 py-1">{emp.address2}</td>
                <td className="border border-gray-300 px-2 py-1">{emp.phone}</td>
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
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredEmployees.length}명 | loading ok
      </div>

      {/* 모달 */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[700px] rounded border border-gray-400 bg-[#F0EDE4] shadow-lg">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between rounded-t border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">
                {modalMode === "add" ? "사원 추가" : "사원 수정"}
              </span>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-white hover:text-gray-200"
              >
                ✕
              </button>
            </div>

            {/* 탭 */}
            <div className="flex border-b bg-gray-200">
              {[
                { key: "basic", label: "기본정보" },
                { key: "permission", label: "사용권한" },
                { key: "contact", label: "연락처" },
                { key: "etc", label: "기타" },
                { key: "salary", label: "급여정보" },
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`px-4 py-1.5 text-xs ${
                    activeTab === tab.key
                      ? "border-b-2 border-blue-600 bg-white font-medium"
                      : "hover:bg-gray-100"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* 탭 내용 */}
            <div className="p-4">
              {activeTab === "basic" && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">코드:</label>
                    <input
                      type="text"
                      value={formData.code}
                      onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">성명:</label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">주민등록번호:</label>
                    <input
                      type="text"
                      value={formData.residentNo}
                      onChange={(e) => setFormData({ ...formData, residentNo: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                      placeholder="000000-0******"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">입사일:</label>
                    <input
                      type="date"
                      value={formData.hireDate}
                      onChange={(e) => setFormData({ ...formData, hireDate: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">소속부서:</label>
                    <select
                      value={formData.department}
                      onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    >
                      <option value="">선택</option>
                      {DEPARTMENTS.map((d) => (
                        <option key={d} value={d}>{d}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">직책:</label>
                    <select
                      value={formData.position}
                      onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    >
                      <option value="">선택</option>
                      {POSITIONS.map((p) => (
                        <option key={p} value={p}>{p}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">우편번호:</label>
                    <input
                      type="text"
                      value={formData.zipCode}
                      onChange={(e) => setFormData({ ...formData, zipCode: e.target.value })}
                      className="w-24 rounded border border-gray-400 px-2 py-1 text-xs"
                    />
                    <button className="rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
                      검색
                    </button>
                  </div>
                  <div />
                  <div className="col-span-2 flex items-center gap-2">
                    <label className="w-24 text-right text-xs">주소1:</label>
                    <input
                      type="text"
                      value={formData.address1}
                      onChange={(e) => setFormData({ ...formData, address1: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    />
                  </div>
                  <div className="col-span-2 flex items-center gap-2">
                    <label className="w-24 text-right text-xs">주소2:</label>
                    <input
                      type="text"
                      value={formData.address2}
                      onChange={(e) => setFormData({ ...formData, address2: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    />
                  </div>
                  <div className="col-span-2 flex items-center gap-2">
                    <label className="w-24 text-right text-xs">메모:</label>
                    <textarea
                      value={formData.memo}
                      onChange={(e) => setFormData({ ...formData, memo: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                      rows={2}
                    />
                  </div>
                </div>
              )}

              {activeTab === "permission" && (
                <div className="space-y-3">
                  <p className="text-xs text-gray-600">사용 권한을 설정하세요:</p>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { key: "sales", label: "매출관리" },
                      { key: "purchase", label: "매입관리" },
                      { key: "inventory", label: "재고관리" },
                      { key: "accounting", label: "회계관리" },
                      { key: "admin", label: "관리자권한" },
                    ].map((perm) => (
                      <label key={perm.key} className="flex items-center gap-2 text-xs">
                        <input
                          type="checkbox"
                          checked={formData.permissions[perm.key as keyof typeof formData.permissions]}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              permissions: {
                                ...formData.permissions,
                                [perm.key]: e.target.checked,
                              },
                            })
                          }
                        />
                        {perm.label}
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === "contact" && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">전화번호:</label>
                    <input
                      type="text"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">휴대전화:</label>
                    <input
                      type="text"
                      value={formData.mobile}
                      onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">팩스:</label>
                    <input
                      type="text"
                      value={formData.fax}
                      onChange={(e) => setFormData({ ...formData, fax: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">이메일:</label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">비상연락처:</label>
                    <input
                      type="text"
                      value={formData.emergencyContact}
                      onChange={(e) => setFormData({ ...formData, emergencyContact: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                      placeholder="관계(이름)"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">비상연락번호:</label>
                    <input
                      type="text"
                      value={formData.emergencyPhone}
                      onChange={(e) => setFormData({ ...formData, emergencyPhone: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    />
                  </div>
                </div>
              )}

              {activeTab === "etc" && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">생년월일:</label>
                    <input
                      type="date"
                      value={formData.birthDate}
                      onChange={(e) => setFormData({ ...formData, birthDate: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">성별:</label>
                    <select
                      value={formData.gender}
                      onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    >
                      <option value="남">남</option>
                      <option value="여">여</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">결혼여부:</label>
                    <select
                      value={formData.maritalStatus}
                      onChange={(e) => setFormData({ ...formData, maritalStatus: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    >
                      <option value="미혼">미혼</option>
                      <option value="기혼">기혼</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">병역:</label>
                    <select
                      value={formData.militaryService}
                      onChange={(e) => setFormData({ ...formData, militaryService: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    >
                      <option value="해당없음">해당없음</option>
                      <option value="군필">군필</option>
                      <option value="미필">미필</option>
                      <option value="면제">면제</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">최종학력:</label>
                    <select
                      value={formData.education}
                      onChange={(e) => setFormData({ ...formData, education: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    >
                      <option value="">선택</option>
                      <option value="고졸">고졸</option>
                      <option value="전문대졸">전문대졸</option>
                      <option value="대졸">대졸</option>
                      <option value="석사">석사</option>
                      <option value="박사">박사</option>
                    </select>
                  </div>
                </div>
              )}

              {activeTab === "salary" && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">은행명:</label>
                    <select
                      value={formData.bankName}
                      onChange={(e) => setFormData({ ...formData, bankName: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    >
                      <option value="">선택</option>
                      <option value="국민은행">국민은행</option>
                      <option value="신한은행">신한은행</option>
                      <option value="우리은행">우리은행</option>
                      <option value="하나은행">하나은행</option>
                      <option value="기업은행">기업은행</option>
                      <option value="농협은행">농협은행</option>
                      <option value="카카오뱅크">카카오뱅크</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">계좌번호:</label>
                    <input
                      type="text"
                      value={formData.accountNo}
                      onChange={(e) => setFormData({ ...formData, accountNo: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">예금주:</label>
                    <input
                      type="text"
                      value={formData.accountHolder}
                      onChange={(e) => setFormData({ ...formData, accountHolder: e.target.value })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                    />
                  </div>
                  <div />
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">기본급:</label>
                    <input
                      type="number"
                      value={formData.baseSalary}
                      onChange={(e) => setFormData({ ...formData, baseSalary: Number(e.target.value) })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs text-right"
                    />
                    <span className="text-xs">원</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="w-24 text-right text-xs">수당:</label>
                    <input
                      type="number"
                      value={formData.allowance}
                      onChange={(e) => setFormData({ ...formData, allowance: Number(e.target.value) })}
                      className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs text-right"
                    />
                    <span className="text-xs">원</span>
                  </div>
                </div>
              )}
            </div>

            {/* 모달 푸터 */}
            <div className="flex justify-end gap-2 border-t bg-gray-200 px-4 py-2">
              <button
                onClick={handleSave}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200"
              >
                저장
              </button>
              <button
                onClick={() => setIsModalOpen(false)}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200"
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
