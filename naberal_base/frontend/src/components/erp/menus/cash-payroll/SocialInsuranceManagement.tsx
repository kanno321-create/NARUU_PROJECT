"use client";

import React, { useState } from "react";

interface SocialInsuranceItem {
  id: string;
  employeeNo: string;
  name: string;
  department: string;
  salary: number;
  nationalPensionRate: number;
  nationalPensionEmployee: number;
  nationalPensionEmployer: number;
  healthInsuranceRate: number;
  healthInsuranceEmployee: number;
  healthInsuranceEmployer: number;
  longTermCareRate: number;
  longTermCareEmployee: number;
  longTermCareEmployer: number;
  employmentInsuranceRate: number;
  employmentInsuranceEmployee: number;
  employmentInsuranceEmployer: number;
  industrialAccidentRate: number;
  industrialAccidentEmployer: number;
  totalEmployee: number;
  totalEmployer: number;
  status: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: SocialInsuranceItem[] = [
  {
    id: "1",
    employeeNo: "EMP001",
    name: "김철수",
    department: "영업부",
    salary: 4500000,
    nationalPensionRate: 4.5,
    nationalPensionEmployee: 202500,
    nationalPensionEmployer: 202500,
    healthInsuranceRate: 3.545,
    healthInsuranceEmployee: 159525,
    healthInsuranceEmployer: 159525,
    longTermCareRate: 0.4591,
    longTermCareEmployee: 20660,
    longTermCareEmployer: 20660,
    employmentInsuranceRate: 0.9,
    employmentInsuranceEmployee: 40500,
    employmentInsuranceEmployer: 40500,
    industrialAccidentRate: 1.0,
    industrialAccidentEmployer: 45000,
    totalEmployee: 423185,
    totalEmployer: 468185,
    status: "적용중",
  },
  {
    id: "2",
    employeeNo: "EMP002",
    name: "이영희",
    department: "관리부",
    salary: 3600000,
    nationalPensionRate: 4.5,
    nationalPensionEmployee: 162000,
    nationalPensionEmployer: 162000,
    healthInsuranceRate: 3.545,
    healthInsuranceEmployee: 127620,
    healthInsuranceEmployer: 127620,
    longTermCareRate: 0.4591,
    longTermCareEmployee: 16528,
    longTermCareEmployer: 16528,
    employmentInsuranceRate: 0.9,
    employmentInsuranceEmployee: 32400,
    employmentInsuranceEmployer: 32400,
    industrialAccidentRate: 1.0,
    industrialAccidentEmployer: 36000,
    totalEmployee: 338548,
    totalEmployer: 374548,
    status: "적용중",
  },
  {
    id: "3",
    employeeNo: "EMP003",
    name: "박민수",
    department: "생산부",
    salary: 3300000,
    nationalPensionRate: 4.5,
    nationalPensionEmployee: 148500,
    nationalPensionEmployer: 148500,
    healthInsuranceRate: 3.545,
    healthInsuranceEmployee: 116985,
    healthInsuranceEmployer: 116985,
    longTermCareRate: 0.4591,
    longTermCareEmployee: 15150,
    longTermCareEmployer: 15150,
    employmentInsuranceRate: 0.9,
    employmentInsuranceEmployee: 29700,
    employmentInsuranceEmployer: 29700,
    industrialAccidentRate: 1.0,
    industrialAccidentEmployer: 33000,
    totalEmployee: 310335,
    totalEmployer: 343335,
    status: "적용중",
  },
  {
    id: "4",
    employeeNo: "EMP004",
    name: "정수진",
    department: "영업부",
    salary: 6300000,
    nationalPensionRate: 4.5,
    nationalPensionEmployee: 283500,
    nationalPensionEmployer: 283500,
    healthInsuranceRate: 3.545,
    healthInsuranceEmployee: 223335,
    healthInsuranceEmployer: 223335,
    longTermCareRate: 0.4591,
    longTermCareEmployee: 28923,
    longTermCareEmployer: 28923,
    employmentInsuranceRate: 0.9,
    employmentInsuranceEmployee: 56700,
    employmentInsuranceEmployer: 56700,
    industrialAccidentRate: 1.0,
    industrialAccidentEmployer: 63000,
    totalEmployee: 592458,
    totalEmployer: 655458,
    status: "적용중",
  },
];

export function SocialInsuranceManagement() {
  const [departmentFilter, setDepartmentFilter] = useState("전체");
  const [data, setData] = useState<SocialInsuranceItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState<SocialInsuranceItem | null>(null);

  const departments = ["전체", ...new Set(data.map((d) => d.department))];

  const filteredData = data.filter(
    (item) => departmentFilter === "전체" || item.department === departmentFilter
  );

  // 총계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      salary: acc.salary + item.salary,
      nationalPensionEmployee: acc.nationalPensionEmployee + item.nationalPensionEmployee,
      nationalPensionEmployer: acc.nationalPensionEmployer + item.nationalPensionEmployer,
      healthInsuranceEmployee: acc.healthInsuranceEmployee + item.healthInsuranceEmployee,
      healthInsuranceEmployer: acc.healthInsuranceEmployer + item.healthInsuranceEmployer,
      employmentInsuranceEmployee: acc.employmentInsuranceEmployee + item.employmentInsuranceEmployee,
      employmentInsuranceEmployer: acc.employmentInsuranceEmployer + item.employmentInsuranceEmployer,
      industrialAccidentEmployer: acc.industrialAccidentEmployer + item.industrialAccidentEmployer,
      totalEmployee: acc.totalEmployee + item.totalEmployee,
      totalEmployer: acc.totalEmployer + item.totalEmployer,
    }),
    {
      salary: 0,
      nationalPensionEmployee: 0,
      nationalPensionEmployer: 0,
      healthInsuranceEmployee: 0,
      healthInsuranceEmployer: 0,
      employmentInsuranceEmployee: 0,
      employmentInsuranceEmployer: 0,
      industrialAccidentEmployer: 0,
      totalEmployee: 0,
      totalEmployer: 0,
    }
  );

  const handleEdit = () => {
    const item = data.find((d) => d.id === selectedId);
    if (item) {
      setEditItem({ ...item });
      setShowModal(true);
    }
  };

  const recalculate = () => {
    if (editItem) {
      const nationalPensionEmployee = Math.round(editItem.salary * editItem.nationalPensionRate / 100);
      const healthInsuranceEmployee = Math.round(editItem.salary * editItem.healthInsuranceRate / 100);
      const longTermCareEmployee = Math.round(editItem.salary * editItem.longTermCareRate / 100);
      const employmentInsuranceEmployee = Math.round(editItem.salary * editItem.employmentInsuranceRate / 100);
      const industrialAccidentEmployer = Math.round(editItem.salary * editItem.industrialAccidentRate / 100);

      const totalEmployee = nationalPensionEmployee + healthInsuranceEmployee + longTermCareEmployee + employmentInsuranceEmployee;
      const totalEmployer = nationalPensionEmployee + healthInsuranceEmployee + longTermCareEmployee + employmentInsuranceEmployee + industrialAccidentEmployer;

      setEditItem({
        ...editItem,
        nationalPensionEmployee,
        nationalPensionEmployer: nationalPensionEmployee,
        healthInsuranceEmployee,
        healthInsuranceEmployer: healthInsuranceEmployee,
        longTermCareEmployee,
        longTermCareEmployer: longTermCareEmployee,
        employmentInsuranceEmployee,
        employmentInsuranceEmployer: employmentInsuranceEmployee,
        industrialAccidentEmployer,
        totalEmployee,
        totalEmployer,
      });
    }
  };

  const handleSave = () => {
    if (editItem) {
      setData(data.map((d) => (d.id === editItem.id ? editItem : d)));
      setShowModal(false);
      setEditItem(null);
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">4대보험관리</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
          <span>✏️</span> 수정
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📊</span> 보고서출력
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
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색
        </button>
        <div className="ml-auto text-xs text-gray-500">
          * 2025년 기준 요율 적용
        </div>
      </div>

      {/* 요율 정보 */}
      <div className="border-b bg-yellow-50 px-3 py-2 text-xs">
        <span className="font-medium">▶ 2025년 4대보험 요율: </span>
        <span className="mx-2">국민연금 9.0%(사업주/근로자 각 4.5%)</span>
        <span className="mx-2">건강보험 7.09%(각 3.545%)</span>
        <span className="mx-2">장기요양 12.95%(건보료의)</span>
        <span className="mx-2">고용보험 1.8%(각 0.9%)</span>
        <span className="mx-2">산재보험 1.0%(사업주)</span>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>사번</th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>성명</th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>부서</th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>보수월액</th>
              <th className="border border-gray-400 px-2 py-1 bg-blue-100" colSpan={2}>국민연금</th>
              <th className="border border-gray-400 px-2 py-1 bg-green-100" colSpan={2}>건강보험</th>
              <th className="border border-gray-400 px-2 py-1 bg-purple-100" colSpan={2}>고용보험</th>
              <th className="border border-gray-400 px-2 py-1 bg-orange-100">산재보험</th>
              <th className="border border-gray-400 px-2 py-1 bg-red-100" colSpan={2}>합계</th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>상태</th>
            </tr>
            <tr>
              <th className="border border-gray-400 px-2 py-1 bg-blue-50 w-20">근로자</th>
              <th className="border border-gray-400 px-2 py-1 bg-blue-50 w-20">사업주</th>
              <th className="border border-gray-400 px-2 py-1 bg-green-50 w-20">근로자</th>
              <th className="border border-gray-400 px-2 py-1 bg-green-50 w-20">사업주</th>
              <th className="border border-gray-400 px-2 py-1 bg-purple-50 w-20">근로자</th>
              <th className="border border-gray-400 px-2 py-1 bg-purple-50 w-20">사업주</th>
              <th className="border border-gray-400 px-2 py-1 bg-orange-50 w-20">사업주</th>
              <th className="border border-gray-400 px-2 py-1 bg-red-50 w-24">근로자</th>
              <th className="border border-gray-400 px-2 py-1 bg-red-50 w-24">사업주</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr
                key={item.id}
                className={`cursor-pointer ${
                  selectedId === item.id
                    ? "bg-[#316AC5] text-white"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
                onDoubleClick={handleEdit}
              >
                <td className="border border-gray-300 px-2 py-1">{item.employeeNo}</td>
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.name}</td>
                <td className="border border-gray-300 px-2 py-1">{item.department}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.salary.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.nationalPensionEmployee.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.nationalPensionEmployer.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.healthInsuranceEmployee.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.healthInsuranceEmployer.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.employmentInsuranceEmployee.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.employmentInsuranceEmployer.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.industrialAccidentEmployer.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium text-red-600">
                  {item.totalEmployee.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium text-blue-600">
                  {item.totalEmployer.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  item.status === "적용중" ? "text-green-600" : "text-gray-500"
                }`}>
                  {item.status}
                </td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={3}>
                (합계: {filteredData.length}명)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.salary.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.nationalPensionEmployee.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.nationalPensionEmployer.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.healthInsuranceEmployee.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.healthInsuranceEmployer.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.employmentInsuranceEmployee.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.employmentInsuranceEmployer.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.industrialAccidentEmployer.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.totalEmployee.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.totalEmployer.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
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
          <div className="w-[500px] bg-white shadow-lg">
            <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">4대보험 정보 수정 - {editItem.name}</span>
              <button onClick={() => setShowModal(false)} className="text-white hover:text-gray-200">✕</button>
            </div>
            <div className="p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs mb-1">사번</label>
                  <input
                    type="text"
                    value={editItem.employeeNo}
                    disabled
                    className="w-full rounded border border-gray-300 bg-gray-100 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">보수월액</label>
                  <input
                    type="number"
                    value={editItem.salary}
                    onChange={(e) => setEditItem({ ...editItem, salary: Number(e.target.value) })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
              </div>

              <div className="text-xs font-medium mt-3">▶ 보험요율 (%)</div>
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div>
                  <label className="block mb-1">국민연금</label>
                  <input
                    type="number"
                    step="0.1"
                    value={editItem.nationalPensionRate}
                    onChange={(e) => setEditItem({ ...editItem, nationalPensionRate: Number(e.target.value) })}
                    className="w-full rounded border border-gray-400 px-2 py-1"
                  />
                </div>
                <div>
                  <label className="block mb-1">건강보험</label>
                  <input
                    type="number"
                    step="0.001"
                    value={editItem.healthInsuranceRate}
                    onChange={(e) => setEditItem({ ...editItem, healthInsuranceRate: Number(e.target.value) })}
                    className="w-full rounded border border-gray-400 px-2 py-1"
                  />
                </div>
                <div>
                  <label className="block mb-1">고용보험</label>
                  <input
                    type="number"
                    step="0.1"
                    value={editItem.employmentInsuranceRate}
                    onChange={(e) => setEditItem({ ...editItem, employmentInsuranceRate: Number(e.target.value) })}
                    className="w-full rounded border border-gray-400 px-2 py-1"
                  />
                </div>
              </div>

              <button
                onClick={recalculate}
                className="w-full rounded bg-orange-500 px-4 py-1 text-xs text-white hover:bg-orange-600"
              >
                보험료 재계산
              </button>

              <div className="bg-gray-50 p-2 rounded text-xs">
                <div className="grid grid-cols-2 gap-1">
                  <div>근로자 부담:</div>
                  <div className="text-right text-red-600 font-medium">{editItem.totalEmployee.toLocaleString()}원</div>
                  <div>사업주 부담:</div>
                  <div className="text-right text-blue-600 font-medium">{editItem.totalEmployer.toLocaleString()}원</div>
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
