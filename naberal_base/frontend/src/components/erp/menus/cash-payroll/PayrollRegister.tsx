"use client";

import React, { useState } from "react";

interface PayrollRegisterItem {
  id: string;
  payMonth: string;
  employeeNo: string;
  name: string;
  department: string;
  workDays: number;
  baseSalary: number;
  overtimePay: number;
  bonusPay: number;
  totalAllowance: number;
  nationalPension: number;
  healthInsurance: number;
  employmentInsurance: number;
  incomeTax: number;
  totalDeduction: number;
  netSalary: number;
  payDate: string;
  payStatus: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: PayrollRegisterItem[] = [
  {
    id: "1",
    payMonth: "2025-12",
    employeeNo: "EMP001",
    name: "김철수",
    department: "영업부",
    workDays: 22,
    baseSalary: 4000000,
    overtimePay: 200000,
    bonusPay: 0,
    totalAllowance: 500000,
    nationalPension: 202500,
    healthInsurance: 157500,
    employmentInsurance: 40500,
    incomeTax: 93500,
    totalDeduction: 494000,
    netSalary: 4006000,
    payDate: "2025-12-25",
    payStatus: "지급완료",
  },
  {
    id: "2",
    payMonth: "2025-12",
    employeeNo: "EMP002",
    name: "이영희",
    department: "관리부",
    workDays: 22,
    baseSalary: 3200000,
    overtimePay: 100000,
    bonusPay: 0,
    totalAllowance: 400000,
    nationalPension: 162000,
    healthInsurance: 126000,
    employmentInsurance: 32400,
    incomeTax: 57200,
    totalDeduction: 377600,
    netSalary: 3222400,
    payDate: "2025-12-25",
    payStatus: "지급완료",
  },
  {
    id: "3",
    payMonth: "2025-12",
    employeeNo: "EMP003",
    name: "박민수",
    department: "생산부",
    workDays: 20,
    baseSalary: 2800000,
    overtimePay: 150000,
    bonusPay: 0,
    totalAllowance: 350000,
    nationalPension: 148500,
    healthInsurance: 115500,
    employmentInsurance: 29700,
    incomeTax: 41800,
    totalDeduction: 335500,
    netSalary: 2964500,
    payDate: "2025-12-25",
    payStatus: "지급완료",
  },
  {
    id: "4",
    payMonth: "2025-11",
    employeeNo: "EMP001",
    name: "김철수",
    department: "영업부",
    workDays: 21,
    baseSalary: 4000000,
    overtimePay: 180000,
    bonusPay: 2000000,
    totalAllowance: 480000,
    nationalPension: 202500,
    healthInsurance: 157500,
    employmentInsurance: 40500,
    incomeTax: 185000,
    totalDeduction: 585500,
    netSalary: 5894500,
    payDate: "2025-11-25",
    payStatus: "지급완료",
  },
];

export function PayrollRegister() {
  const [year, setYear] = useState("2025");
  const [departmentFilter, setDepartmentFilter] = useState("전체");
  const [data] = useState<PayrollRegisterItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const departments = ["전체", ...new Set(data.map((d) => d.department))];

  const filteredData = data.filter(
    (item) =>
      item.payMonth.startsWith(year) &&
      (departmentFilter === "전체" || item.department === departmentFilter)
  );

  // 월별 집계
  const monthSummary = filteredData.reduce((acc, item) => {
    if (!acc[item.payMonth]) {
      acc[item.payMonth] = {
        count: 0,
        totalPayment: 0,
        totalDeduction: 0,
        netSalary: 0,
      };
    }
    acc[item.payMonth].count += 1;
    acc[item.payMonth].totalPayment += item.baseSalary + item.overtimePay + item.bonusPay + item.totalAllowance;
    acc[item.payMonth].totalDeduction += item.totalDeduction;
    acc[item.payMonth].netSalary += item.netSalary;
    return acc;
  }, {} as Record<string, { count: number; totalPayment: number; totalDeduction: number; netSalary: number }>);

  // 총계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      baseSalary: acc.baseSalary + item.baseSalary,
      overtimePay: acc.overtimePay + item.overtimePay,
      bonusPay: acc.bonusPay + item.bonusPay,
      totalAllowance: acc.totalAllowance + item.totalAllowance,
      totalDeduction: acc.totalDeduction + item.totalDeduction,
      netSalary: acc.netSalary + item.netSalary,
    }),
    { baseSalary: 0, overtimePay: 0, bonusPay: 0, totalAllowance: 0, totalDeduction: 0, netSalary: 0 }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">급여대장</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
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
          <span className="text-xs">연도:</span>
          <select
            value={year}
            onChange={(e) => setYear(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="2025">2025년</option>
            <option value="2024">2024년</option>
            <option value="2023">2023년</option>
          </select>
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
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색
        </button>
      </div>

      {/* 월별 요약 */}
      <div className="border-b bg-blue-50 px-3 py-2">
        <div className="text-xs font-medium mb-1">▶ 월별 급여 현황</div>
        <div className="flex gap-3 text-xs">
          {Object.entries(monthSummary).sort().reverse().map(([month, summary]) => (
            <div key={month} className="bg-white px-3 py-1 rounded border">
              <div className="font-medium">{month}</div>
              <div>{summary.count}명</div>
              <div className="text-green-600 font-bold">{summary.netSalary.toLocaleString()}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-20">급여월</th>
              <th className="border border-gray-400 px-2 py-1 w-20">사번</th>
              <th className="border border-gray-400 px-2 py-1 w-20">성명</th>
              <th className="border border-gray-400 px-2 py-1 w-20">부서</th>
              <th className="border border-gray-400 px-2 py-1 w-12">근무일</th>
              <th className="border border-gray-400 px-2 py-1 w-24">기본급</th>
              <th className="border border-gray-400 px-2 py-1 w-20">시간외</th>
              <th className="border border-gray-400 px-2 py-1 w-20">상여</th>
              <th className="border border-gray-400 px-2 py-1 w-20">수당</th>
              <th className="border border-gray-400 px-2 py-1 w-24">공제합계</th>
              <th className="border border-gray-400 px-2 py-1 w-28">실지급액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">지급일</th>
              <th className="border border-gray-400 px-2 py-1 w-20">상태</th>
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
              >
                <td className="border border-gray-300 px-2 py-1">{item.payMonth}</td>
                <td className="border border-gray-300 px-2 py-1">{item.employeeNo}</td>
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.name}</td>
                <td className="border border-gray-300 px-2 py-1">{item.department}</td>
                <td className="border border-gray-300 px-2 py-1 text-center">{item.workDays}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.baseSalary.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.overtimePay.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">
                  {item.bonusPay > 0 ? item.bonusPay.toLocaleString() : ""}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.totalAllowance.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-red-600">
                  {item.totalDeduction.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-bold text-green-600">
                  {item.netSalary.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.payDate}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  item.payStatus === "지급완료" ? "text-green-600" : "text-orange-600"
                }`}>
                  {item.payStatus}
                </td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={5}>
                (합계: {filteredData.length}건)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.baseSalary.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.overtimePay.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.bonusPay.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.totalAllowance.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.totalDeduction.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-green-600">
                {totals.netSalary.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={2}></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {filteredData.length}건 | loading ok
      </div>
    </div>
  );
}
