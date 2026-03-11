"use client";

import React, { useState } from "react";

interface PayrollStatementItem {
  id: string;
  payMonth: string;
  employeeNo: string;
  name: string;
  department: string;
  position: string;
  baseSalary: number;
  overtimePay: number;
  mealAllowance: number;
  transportAllowance: number;
  otherAllowance: number;
  totalPayment: number;
  nationalPension: number;
  healthInsurance: number;
  employmentInsurance: number;
  incomeTax: number;
  localTax: number;
  totalDeduction: number;
  netSalary: number;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: PayrollStatementItem[] = [
  {
    id: "1",
    payMonth: "2025-12",
    employeeNo: "EMP001",
    name: "김철수",
    department: "영업부",
    position: "과장",
    baseSalary: 4000000,
    overtimePay: 200000,
    mealAllowance: 200000,
    transportAllowance: 100000,
    otherAllowance: 0,
    totalPayment: 4500000,
    nationalPension: 202500,
    healthInsurance: 157500,
    employmentInsurance: 40500,
    incomeTax: 85000,
    localTax: 8500,
    totalDeduction: 494000,
    netSalary: 4006000,
  },
  {
    id: "2",
    payMonth: "2025-12",
    employeeNo: "EMP002",
    name: "이영희",
    department: "관리부",
    position: "대리",
    baseSalary: 3200000,
    overtimePay: 100000,
    mealAllowance: 200000,
    transportAllowance: 100000,
    otherAllowance: 0,
    totalPayment: 3600000,
    nationalPension: 162000,
    healthInsurance: 126000,
    employmentInsurance: 32400,
    incomeTax: 52000,
    localTax: 5200,
    totalDeduction: 377600,
    netSalary: 3222400,
  },
  {
    id: "3",
    payMonth: "2025-12",
    employeeNo: "EMP003",
    name: "박민수",
    department: "생산부",
    position: "사원",
    baseSalary: 2800000,
    overtimePay: 150000,
    mealAllowance: 200000,
    transportAllowance: 100000,
    otherAllowance: 50000,
    totalPayment: 3300000,
    nationalPension: 148500,
    healthInsurance: 115500,
    employmentInsurance: 29700,
    incomeTax: 38000,
    localTax: 3800,
    totalDeduction: 335500,
    netSalary: 2964500,
  },
  {
    id: "4",
    payMonth: "2025-12",
    employeeNo: "EMP004",
    name: "정수진",
    department: "영업부",
    position: "부장",
    baseSalary: 5500000,
    overtimePay: 300000,
    mealAllowance: 200000,
    transportAllowance: 100000,
    otherAllowance: 200000,
    totalPayment: 6300000,
    nationalPension: 283500,
    healthInsurance: 220500,
    employmentInsurance: 56700,
    incomeTax: 180000,
    localTax: 18000,
    totalDeduction: 758700,
    netSalary: 5541300,
  },
];

export function PayrollStatement() {
  const [payMonth, setPayMonth] = useState("2025-12");
  const [departmentFilter, setDepartmentFilter] = useState("전체");
  const [employeeSearch, setEmployeeSearch] = useState("");
  const [data] = useState<PayrollStatementItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [detailItem, setDetailItem] = useState<PayrollStatementItem | null>(null);

  const departments = ["전체", ...new Set(data.map((d) => d.department))];

  const filteredData = data.filter(
    (item) =>
      item.payMonth === payMonth &&
      (departmentFilter === "전체" || item.department === departmentFilter) &&
      (employeeSearch === "" || item.name.includes(employeeSearch) || item.employeeNo.includes(employeeSearch))
  );

  // 총계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      totalPayment: acc.totalPayment + item.totalPayment,
      totalDeduction: acc.totalDeduction + item.totalDeduction,
      netSalary: acc.netSalary + item.netSalary,
    }),
    { totalPayment: 0, totalDeduction: 0, netSalary: 0 }
  );

  const handleShowDetail = (item: PayrollStatementItem) => {
    setDetailItem(item);
    setShowDetailModal(true);
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">급여명세서</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📊</span> 명세서출력
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 엑셀변환
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📧</span> 이메일발송
        </button>
      </div>

      {/* 검색 조건 */}
      <div className="flex items-center gap-4 border-b bg-white px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="text-xs">급여월:</span>
          <input
            type="month"
            value={payMonth}
            onChange={(e) => setPayMonth(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          />
        </div>
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
          <span className="text-xs">직원검색:</span>
          <input
            type="text"
            value={employeeSearch}
            onChange={(e) => setEmployeeSearch(e.target.value)}
            placeholder="사번/성명"
            className="w-24 rounded border border-gray-400 px-2 py-1 text-xs"
          />
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
              <th className="border border-gray-400 px-2 py-1 w-24">기본급</th>
              <th className="border border-gray-400 px-2 py-1 w-24">제수당</th>
              <th className="border border-gray-400 px-2 py-1 w-28 bg-blue-50">총지급액</th>
              <th className="border border-gray-400 px-2 py-1 w-28 bg-red-50">총공제액</th>
              <th className="border border-gray-400 px-2 py-1 w-28 bg-green-50">실지급액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">상세</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => {
              const allowances = item.overtimePay + item.mealAllowance + item.transportAllowance + item.otherAllowance;
              return (
                <tr
                  key={item.id}
                  className={`cursor-pointer ${
                    selectedId === item.id
                      ? "bg-[#316AC5] text-white"
                      : "hover:bg-gray-100"
                  }`}
                  onClick={() => setSelectedId(item.id)}
                >
                  <td className="border border-gray-300 px-2 py-1">{item.employeeNo}</td>
                  <td className="border border-gray-300 px-2 py-1 font-medium">{item.name}</td>
                  <td className="border border-gray-300 px-2 py-1">{item.department}</td>
                  <td className="border border-gray-300 px-2 py-1">{item.position}</td>
                  <td className="border border-gray-300 px-2 py-1 text-right">
                    {item.baseSalary.toLocaleString()}
                  </td>
                  <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">
                    {allowances.toLocaleString()}
                  </td>
                  <td className="border border-gray-300 px-2 py-1 text-right font-medium">
                    {item.totalPayment.toLocaleString()}
                  </td>
                  <td className="border border-gray-300 px-2 py-1 text-right text-red-600">
                    {item.totalDeduction.toLocaleString()}
                  </td>
                  <td className="border border-gray-300 px-2 py-1 text-right font-bold text-green-600">
                    {item.netSalary.toLocaleString()}
                  </td>
                  <td className="border border-gray-300 px-2 py-1 text-center">
                    <button
                      onClick={(e) => { e.stopPropagation(); handleShowDetail(item); }}
                      className="rounded bg-blue-500 px-2 py-0.5 text-white hover:bg-blue-600"
                    >
                      상세
                    </button>
                  </td>
                </tr>
              );
            })}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={6}>
                (합계: {filteredData.length}명)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.totalPayment.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.totalDeduction.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-green-600">
                {totals.netSalary.toLocaleString()}
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

      {/* 상세 모달 */}
      {showDetailModal && detailItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-[500px] bg-white shadow-lg">
            <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">급여명세서 - {detailItem.name}</span>
              <button onClick={() => setShowDetailModal(false)} className="text-white hover:text-gray-200">✕</button>
            </div>
            <div className="p-4">
              {/* 기본 정보 */}
              <div className="mb-4 border-b pb-3">
                <div className="grid grid-cols-4 gap-2 text-xs">
                  <div><span className="text-gray-500">사번:</span> {detailItem.employeeNo}</div>
                  <div><span className="text-gray-500">성명:</span> {detailItem.name}</div>
                  <div><span className="text-gray-500">부서:</span> {detailItem.department}</div>
                  <div><span className="text-gray-500">직급:</span> {detailItem.position}</div>
                </div>
              </div>

              {/* 지급 내역 */}
              <div className="mb-4">
                <div className="text-xs font-medium text-blue-700 mb-2">▶ 지급 내역</div>
                <table className="w-full text-xs border-collapse">
                  <tbody>
                    <tr className="bg-blue-50">
                      <td className="border px-2 py-1">기본급</td>
                      <td className="border px-2 py-1 text-right">{detailItem.baseSalary.toLocaleString()}</td>
                      <td className="border px-2 py-1">시간외수당</td>
                      <td className="border px-2 py-1 text-right">{detailItem.overtimePay.toLocaleString()}</td>
                    </tr>
                    <tr className="bg-blue-50">
                      <td className="border px-2 py-1">식대</td>
                      <td className="border px-2 py-1 text-right">{detailItem.mealAllowance.toLocaleString()}</td>
                      <td className="border px-2 py-1">교통비</td>
                      <td className="border px-2 py-1 text-right">{detailItem.transportAllowance.toLocaleString()}</td>
                    </tr>
                    <tr className="bg-blue-50">
                      <td className="border px-2 py-1">기타수당</td>
                      <td className="border px-2 py-1 text-right">{detailItem.otherAllowance.toLocaleString()}</td>
                      <td className="border px-2 py-1 font-medium">총 지급액</td>
                      <td className="border px-2 py-1 text-right font-bold text-blue-600">{detailItem.totalPayment.toLocaleString()}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* 공제 내역 */}
              <div className="mb-4">
                <div className="text-xs font-medium text-red-700 mb-2">▶ 공제 내역</div>
                <table className="w-full text-xs border-collapse">
                  <tbody>
                    <tr className="bg-red-50">
                      <td className="border px-2 py-1">국민연금</td>
                      <td className="border px-2 py-1 text-right">{detailItem.nationalPension.toLocaleString()}</td>
                      <td className="border px-2 py-1">건강보험</td>
                      <td className="border px-2 py-1 text-right">{detailItem.healthInsurance.toLocaleString()}</td>
                    </tr>
                    <tr className="bg-red-50">
                      <td className="border px-2 py-1">고용보험</td>
                      <td className="border px-2 py-1 text-right">{detailItem.employmentInsurance.toLocaleString()}</td>
                      <td className="border px-2 py-1">소득세</td>
                      <td className="border px-2 py-1 text-right">{detailItem.incomeTax.toLocaleString()}</td>
                    </tr>
                    <tr className="bg-red-50">
                      <td className="border px-2 py-1">지방소득세</td>
                      <td className="border px-2 py-1 text-right">{detailItem.localTax.toLocaleString()}</td>
                      <td className="border px-2 py-1 font-medium">총 공제액</td>
                      <td className="border px-2 py-1 text-right font-bold text-red-600">{detailItem.totalDeduction.toLocaleString()}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* 실지급액 */}
              <div className="bg-green-100 p-3 rounded text-center">
                <span className="text-sm font-medium">실 지급액: </span>
                <span className="text-lg font-bold text-green-700">{detailItem.netSalary.toLocaleString()}원</span>
              </div>
            </div>
            <div className="flex justify-end gap-2 border-t bg-gray-100 px-4 py-2">
              <button className="rounded border border-gray-400 bg-blue-500 px-4 py-1 text-xs text-white hover:bg-blue-600">
                인쇄
              </button>
              <button
                onClick={() => setShowDetailModal(false)}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
