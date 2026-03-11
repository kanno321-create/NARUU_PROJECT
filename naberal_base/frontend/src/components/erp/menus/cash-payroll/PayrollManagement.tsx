"use client";

import React, { useState } from "react";

interface EmployeeItem {
  id: string;
  employeeNo: string;
  name: string;
  department: string;
  position: string;
  joinDate: string;
  baseSalary: number;
  allowances: number;
  deductions: number;
  netSalary: number;
  bankName: string;
  accountNo: string;
  status: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: EmployeeItem[] = [
  {
    id: "1",
    employeeNo: "EMP001",
    name: "김철수",
    department: "영업부",
    position: "과장",
    joinDate: "2020-03-01",
    baseSalary: 4000000,
    allowances: 500000,
    deductions: 450000,
    netSalary: 4050000,
    bankName: "국민은행",
    accountNo: "123-456-789012",
    status: "재직",
  },
  {
    id: "2",
    employeeNo: "EMP002",
    name: "이영희",
    department: "관리부",
    position: "대리",
    joinDate: "2021-06-15",
    baseSalary: 3200000,
    allowances: 300000,
    deductions: 350000,
    netSalary: 3150000,
    bankName: "신한은행",
    accountNo: "987-654-321098",
    status: "재직",
  },
  {
    id: "3",
    employeeNo: "EMP003",
    name: "박민수",
    department: "생산부",
    position: "사원",
    joinDate: "2023-01-02",
    baseSalary: 2800000,
    allowances: 200000,
    deductions: 280000,
    netSalary: 2720000,
    bankName: "기업은행",
    accountNo: "111-222-333444",
    status: "재직",
  },
  {
    id: "4",
    employeeNo: "EMP004",
    name: "정수진",
    department: "영업부",
    position: "부장",
    joinDate: "2018-09-01",
    baseSalary: 5500000,
    allowances: 800000,
    deductions: 630000,
    netSalary: 5670000,
    bankName: "우리은행",
    accountNo: "555-666-777888",
    status: "재직",
  },
  {
    id: "5",
    employeeNo: "EMP005",
    name: "최동욱",
    department: "생산부",
    position: "대리",
    joinDate: "2022-03-15",
    baseSalary: 3000000,
    allowances: 250000,
    deductions: 310000,
    netSalary: 2940000,
    bankName: "하나은행",
    accountNo: "999-888-777666",
    status: "휴직",
  },
];

export function PayrollManagement() {
  const [departmentFilter, setDepartmentFilter] = useState("전체");
  const [statusFilter, setStatusFilter] = useState("전체");
  const [data, setData] = useState<EmployeeItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState<EmployeeItem | null>(null);
  const [isNew, setIsNew] = useState(false);

  const departments = ["전체", ...new Set(data.map((d) => d.department))];

  const filteredData = data.filter(
    (item) =>
      (departmentFilter === "전체" || item.department === departmentFilter) &&
      (statusFilter === "전체" || item.status === statusFilter)
  );

  // 총계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      baseSalary: acc.baseSalary + item.baseSalary,
      allowances: acc.allowances + item.allowances,
      deductions: acc.deductions + item.deductions,
      netSalary: acc.netSalary + item.netSalary,
    }),
    { baseSalary: 0, allowances: 0, deductions: 0, netSalary: 0 }
  );

  const handleNew = () => {
    setEditItem({
      id: String(Date.now()),
      employeeNo: "",
      name: "",
      department: "",
      position: "",
      joinDate: new Date().toISOString().split("T")[0],
      baseSalary: 0,
      allowances: 0,
      deductions: 0,
      netSalary: 0,
      bankName: "",
      accountNo: "",
      status: "재직",
    });
    setIsNew(true);
    setShowModal(true);
  };

  const handleEdit = () => {
    const item = data.find((d) => d.id === selectedId);
    if (item) {
      setEditItem({ ...item });
      setIsNew(false);
      setShowModal(true);
    }
  };

  const handleSave = () => {
    if (editItem) {
      editItem.netSalary = editItem.baseSalary + editItem.allowances - editItem.deductions;
      if (isNew) {
        setData([...data, editItem]);
      } else {
        setData(data.map((d) => (d.id === editItem.id ? editItem : d)));
      }
      setShowModal(false);
      setEditItem(null);
    }
  };

  const handleDelete = () => {
    if (selectedId && window.confirm("선택한 직원 정보를 삭제하시겠습니까?")) {
      setData(data.filter((d) => d.id !== selectedId));
      setSelectedId(null);
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">급여관리</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button
          onClick={handleNew}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
          <span>➕</span> 신규
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
          <span>✏️</span> 수정
        </button>
        <button
          onClick={handleDelete}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
          <span>🗑️</span> 삭제
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>💰</span> 급여이체
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 엑셀변환
        </button>
      </div>

      {/* 검색 조건 */}
      <div className="flex items-center gap-4 border-b bg-white px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="text-xs">부서:</span>
          <select
            value={departmentFilter}
            onChange={(e) => setDepartmentFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            {departments.map((dept) => (
              <option key={dept} value={dept}>{dept}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">상태:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="재직">재직</option>
            <option value="휴직">휴직</option>
            <option value="퇴직">퇴직</option>
          </select>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색
        </button>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-20">사번</th>
              <th className="border border-gray-400 px-2 py-1 w-20">성명</th>
              <th className="border border-gray-400 px-2 py-1 w-20">부서</th>
              <th className="border border-gray-400 px-2 py-1 w-16">직급</th>
              <th className="border border-gray-400 px-2 py-1 w-24">입사일</th>
              <th className="border border-gray-400 px-2 py-1 w-28">기본급</th>
              <th className="border border-gray-400 px-2 py-1 w-24">수당</th>
              <th className="border border-gray-400 px-2 py-1 w-24">공제</th>
              <th className="border border-gray-400 px-2 py-1 w-28">실지급액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">은행</th>
              <th className="border border-gray-400 px-2 py-1 w-32">계좌번호</th>
              <th className="border border-gray-400 px-2 py-1 w-16">상태</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr
                key={item.id}
                className={`cursor-pointer ${
                  selectedId === item.id
                    ? "bg-[#316AC5] text-white"
                    : item.status !== "재직"
                    ? "bg-gray-100 text-gray-500"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
                onDoubleClick={handleEdit}
              >
                <td className="border border-gray-300 px-2 py-1">{item.employeeNo}</td>
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.name}</td>
                <td className="border border-gray-300 px-2 py-1">{item.department}</td>
                <td className="border border-gray-300 px-2 py-1">{item.position}</td>
                <td className="border border-gray-300 px-2 py-1">{item.joinDate}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.baseSalary.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">
                  {item.allowances.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-red-600">
                  {item.deductions.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium text-green-600">
                  {item.netSalary.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.bankName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.accountNo}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  item.status === "재직" ? "text-green-600" : item.status === "휴직" ? "text-orange-600" : "text-gray-500"
                }`}>
                  {item.status}
                </td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={5}>
                (합계: {filteredData.length}명)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.baseSalary.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.allowances.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.deductions.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-green-600">
                {totals.netSalary.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={3}></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredData.length}건 | loading ok
      </div>

      {/* 수정 모달 */}
      {showModal && editItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-[550px] bg-white shadow-lg">
            <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">{isNew ? "직원 등록" : "직원 수정"}</span>
              <button onClick={() => setShowModal(false)} className="text-white hover:text-gray-200">✕</button>
            </div>
            <div className="p-4 space-y-3">
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs mb-1">사번 *</label>
                  <input
                    type="text"
                    value={editItem.employeeNo}
                    onChange={(e) => setEditItem({ ...editItem, employeeNo: e.target.value })}
                    placeholder="EMP001"
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">성명 *</label>
                  <input
                    type="text"
                    value={editItem.name}
                    onChange={(e) => setEditItem({ ...editItem, name: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">입사일</label>
                  <input
                    type="date"
                    value={editItem.joinDate}
                    onChange={(e) => setEditItem({ ...editItem, joinDate: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">부서</label>
                  <select
                    value={editItem.department}
                    onChange={(e) => setEditItem({ ...editItem, department: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  >
                    <option value="">선택</option>
                    <option value="영업부">영업부</option>
                    <option value="관리부">관리부</option>
                    <option value="생산부">생산부</option>
                    <option value="개발부">개발부</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs mb-1">직급</label>
                  <select
                    value={editItem.position}
                    onChange={(e) => setEditItem({ ...editItem, position: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  >
                    <option value="">선택</option>
                    <option value="사원">사원</option>
                    <option value="대리">대리</option>
                    <option value="과장">과장</option>
                    <option value="부장">부장</option>
                    <option value="이사">이사</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs mb-1">상태</label>
                  <select
                    value={editItem.status}
                    onChange={(e) => setEditItem({ ...editItem, status: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  >
                    <option value="재직">재직</option>
                    <option value="휴직">휴직</option>
                    <option value="퇴직">퇴직</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs mb-1">기본급</label>
                  <input
                    type="number"
                    value={editItem.baseSalary}
                    onChange={(e) => setEditItem({ ...editItem, baseSalary: Number(e.target.value) })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">수당</label>
                  <input
                    type="number"
                    value={editItem.allowances}
                    onChange={(e) => setEditItem({ ...editItem, allowances: Number(e.target.value) })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">공제</label>
                  <input
                    type="number"
                    value={editItem.deductions}
                    onChange={(e) => setEditItem({ ...editItem, deductions: Number(e.target.value) })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">은행</label>
                  <select
                    value={editItem.bankName}
                    onChange={(e) => setEditItem({ ...editItem, bankName: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  >
                    <option value="">선택</option>
                    <option value="국민은행">국민은행</option>
                    <option value="신한은행">신한은행</option>
                    <option value="우리은행">우리은행</option>
                    <option value="하나은행">하나은행</option>
                    <option value="기업은행">기업은행</option>
                  </select>
                </div>
                <div className="col-span-2">
                  <label className="block text-xs mb-1">계좌번호</label>
                  <input
                    type="text"
                    value={editItem.accountNo}
                    onChange={(e) => setEditItem({ ...editItem, accountNo: e.target.value })}
                    placeholder="000-000-000000"
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 border-t bg-gray-100 px-4 py-2">
              <button
                onClick={handleSave}
                className="rounded border border-gray-400 bg-blue-500 px-4 py-1 text-xs text-white hover:bg-blue-600"
              >
                저장
              </button>
              <button
                onClick={() => setShowModal(false)}
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
