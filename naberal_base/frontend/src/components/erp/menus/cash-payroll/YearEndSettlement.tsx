"use client";

import React, { useState } from "react";

interface YearEndSettlementItem {
  id: string;
  employeeCode: string;
  employeeName: string;
  department: string;
  position: string;
  joinDate: string;
  // 소득 내역
  totalSalary: number;
  bonus: number;
  otherIncome: number;
  totalIncome: number;
  // 비과세 소득
  mealAllowance: number;
  transportAllowance: number;
  childcareAllowance: number;
  totalNonTaxable: number;
  // 소득공제
  nationalPension: number;
  healthInsurance: number;
  employmentInsurance: number;
  housingFund: number;
  creditCardDeduction: number;
  medicalExpense: number;
  educationExpense: number;
  donationDeduction: number;
  totalDeduction: number;
  // 세액계산
  taxableIncome: number;
  calculatedTax: number;
  taxCredit: number;
  finalTax: number;
  paidTax: number;
  settlementAmount: number;
  settlementType: string;
  status: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: YearEndSettlementItem[] = [
  {
    id: "1",
    employeeCode: "EMP001",
    employeeName: "김영희",
    department: "영업부",
    position: "과장",
    joinDate: "2020-03-15",
    totalSalary: 48000000,
    bonus: 8000000,
    otherIncome: 500000,
    totalIncome: 56500000,
    mealAllowance: 1200000,
    transportAllowance: 1200000,
    childcareAllowance: 1200000,
    totalNonTaxable: 3600000,
    nationalPension: 2160000,
    healthInsurance: 1700000,
    employmentInsurance: 432000,
    housingFund: 0,
    creditCardDeduction: 3500000,
    medicalExpense: 850000,
    educationExpense: 2400000,
    donationDeduction: 500000,
    totalDeduction: 11542000,
    taxableIncome: 41358000,
    calculatedTax: 4520000,
    taxCredit: 680000,
    finalTax: 3840000,
    paidTax: 4200000,
    settlementAmount: 360000,
    settlementType: "환급",
    status: "완료",
  },
  {
    id: "2",
    employeeCode: "EMP002",
    employeeName: "이철수",
    department: "개발부",
    position: "대리",
    joinDate: "2021-07-01",
    totalSalary: 42000000,
    bonus: 6000000,
    otherIncome: 300000,
    totalIncome: 48300000,
    mealAllowance: 1200000,
    transportAllowance: 1200000,
    childcareAllowance: 0,
    totalNonTaxable: 2400000,
    nationalPension: 1890000,
    healthInsurance: 1488000,
    employmentInsurance: 378000,
    housingFund: 2400000,
    creditCardDeduction: 2800000,
    medicalExpense: 450000,
    educationExpense: 0,
    donationDeduction: 200000,
    totalDeduction: 9606000,
    taxableIncome: 36294000,
    calculatedTax: 3650000,
    taxCredit: 520000,
    finalTax: 3130000,
    paidTax: 2950000,
    settlementAmount: 180000,
    settlementType: "추가납부",
    status: "완료",
  },
  {
    id: "3",
    employeeCode: "EMP003",
    employeeName: "박지민",
    department: "총무부",
    position: "사원",
    joinDate: "2023-01-02",
    totalSalary: 36000000,
    bonus: 4000000,
    otherIncome: 200000,
    totalIncome: 40200000,
    mealAllowance: 1200000,
    transportAllowance: 1200000,
    childcareAllowance: 1200000,
    totalNonTaxable: 3600000,
    nationalPension: 1620000,
    healthInsurance: 1276000,
    employmentInsurance: 324000,
    housingFund: 0,
    creditCardDeduction: 2200000,
    medicalExpense: 320000,
    educationExpense: 1800000,
    donationDeduction: 100000,
    totalDeduction: 7640000,
    taxableIncome: 28960000,
    calculatedTax: 2450000,
    taxCredit: 380000,
    finalTax: 2070000,
    paidTax: 2100000,
    settlementAmount: 30000,
    settlementType: "환급",
    status: "진행중",
  },
  {
    id: "4",
    employeeCode: "EMP004",
    employeeName: "최민수",
    department: "영업부",
    position: "부장",
    joinDate: "2018-05-20",
    totalSalary: 60000000,
    bonus: 12000000,
    otherIncome: 800000,
    totalIncome: 72800000,
    mealAllowance: 1200000,
    transportAllowance: 1200000,
    childcareAllowance: 0,
    totalNonTaxable: 2400000,
    nationalPension: 2700000,
    healthInsurance: 2126000,
    employmentInsurance: 540000,
    housingFund: 3600000,
    creditCardDeduction: 4500000,
    medicalExpense: 1200000,
    educationExpense: 3600000,
    donationDeduction: 1000000,
    totalDeduction: 19266000,
    taxableIncome: 51134000,
    calculatedTax: 6850000,
    taxCredit: 850000,
    finalTax: 6000000,
    paidTax: 5800000,
    settlementAmount: 200000,
    settlementType: "추가납부",
    status: "미제출",
  },
  {
    id: "5",
    employeeCode: "EMP005",
    employeeName: "정수현",
    department: "개발부",
    position: "과장",
    joinDate: "2019-09-10",
    totalSalary: 52000000,
    bonus: 10000000,
    otherIncome: 600000,
    totalIncome: 62600000,
    mealAllowance: 1200000,
    transportAllowance: 1200000,
    childcareAllowance: 2400000,
    totalNonTaxable: 4800000,
    nationalPension: 2340000,
    healthInsurance: 1843000,
    employmentInsurance: 468000,
    housingFund: 1200000,
    creditCardDeduction: 3800000,
    medicalExpense: 950000,
    educationExpense: 4200000,
    donationDeduction: 600000,
    totalDeduction: 15401000,
    taxableIncome: 42399000,
    calculatedTax: 4680000,
    taxCredit: 720000,
    finalTax: 3960000,
    paidTax: 4100000,
    settlementAmount: 140000,
    settlementType: "환급",
    status: "완료",
  },
];

interface DeductionDetailModalProps {
  item: YearEndSettlementItem;
  onClose: () => void;
}

function DeductionDetailModal({ item, onClose }: DeductionDetailModalProps) {
  const [activeTab, setActiveTab] = useState<"income" | "deduction" | "tax">("income");

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded shadow-lg w-[900px] max-h-[90vh] overflow-hidden flex flex-col">
        {/* 모달 헤더 */}
        <div className="flex items-center justify-between bg-gradient-to-r from-blue-600 to-blue-400 px-4 py-2">
          <span className="text-white font-medium">
            연말정산 상세 - {item.employeeName} ({item.employeeCode})
          </span>
          <button
            onClick={onClose}
            className="text-white hover:text-gray-200 text-xl font-bold"
          >
            ×
          </button>
        </div>

        {/* 탭 */}
        <div className="flex border-b bg-gray-100">
          <button
            onClick={() => setActiveTab("income")}
            className={`px-4 py-2 text-sm ${
              activeTab === "income"
                ? "bg-white border-t-2 border-blue-500 font-medium"
                : "hover:bg-gray-200"
            }`}
          >
            소득내역
          </button>
          <button
            onClick={() => setActiveTab("deduction")}
            className={`px-4 py-2 text-sm ${
              activeTab === "deduction"
                ? "bg-white border-t-2 border-blue-500 font-medium"
                : "hover:bg-gray-200"
            }`}
          >
            공제내역
          </button>
          <button
            onClick={() => setActiveTab("tax")}
            className={`px-4 py-2 text-sm ${
              activeTab === "tax"
                ? "bg-white border-t-2 border-blue-500 font-medium"
                : "hover:bg-gray-200"
            }`}
          >
            세액계산
          </button>
        </div>

        {/* 모달 내용 */}
        <div className="flex-1 overflow-auto p-4">
          {/* 기본 정보 */}
          <div className="mb-4 p-3 bg-gray-50 rounded border">
            <div className="grid grid-cols-5 gap-4 text-sm">
              <div>
                <span className="text-gray-500">사원코드:</span>
                <span className="ml-2 font-medium">{item.employeeCode}</span>
              </div>
              <div>
                <span className="text-gray-500">성명:</span>
                <span className="ml-2 font-medium">{item.employeeName}</span>
              </div>
              <div>
                <span className="text-gray-500">부서:</span>
                <span className="ml-2">{item.department}</span>
              </div>
              <div>
                <span className="text-gray-500">직급:</span>
                <span className="ml-2">{item.position}</span>
              </div>
              <div>
                <span className="text-gray-500">입사일:</span>
                <span className="ml-2">{item.joinDate}</span>
              </div>
            </div>
          </div>

          {activeTab === "income" && (
            <div className="space-y-4">
              {/* 총급여 내역 */}
              <div className="border rounded">
                <div className="bg-blue-50 px-3 py-2 font-medium text-sm border-b">
                  총급여 내역
                </div>
                <table className="w-full text-sm">
                  <tbody>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50 w-40">급여총액</td>
                      <td className="px-3 py-2 text-right text-blue-600 font-medium">
                        {item.totalSalary.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50">상여금</td>
                      <td className="px-3 py-2 text-right text-blue-600">
                        {item.bonus.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50">기타소득</td>
                      <td className="px-3 py-2 text-right text-blue-600">
                        {item.otherIncome.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className="bg-yellow-50">
                      <td className="px-3 py-2 font-medium">총소득</td>
                      <td className="px-3 py-2 text-right text-blue-600 font-bold">
                        {item.totalIncome.toLocaleString()}원
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* 비과세 소득 */}
              <div className="border rounded">
                <div className="bg-green-50 px-3 py-2 font-medium text-sm border-b">
                  비과세 소득
                </div>
                <table className="w-full text-sm">
                  <tbody>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50 w-40">식대</td>
                      <td className="px-3 py-2 text-right text-green-600">
                        {item.mealAllowance.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50">교통비</td>
                      <td className="px-3 py-2 text-right text-green-600">
                        {item.transportAllowance.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50">육아수당</td>
                      <td className="px-3 py-2 text-right text-green-600">
                        {item.childcareAllowance.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className="bg-green-50">
                      <td className="px-3 py-2 font-medium">비과세 합계</td>
                      <td className="px-3 py-2 text-right text-green-600 font-bold">
                        {item.totalNonTaxable.toLocaleString()}원
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === "deduction" && (
            <div className="space-y-4">
              {/* 소득공제 */}
              <div className="border rounded">
                <div className="bg-purple-50 px-3 py-2 font-medium text-sm border-b">
                  근로소득공제 (4대보험)
                </div>
                <table className="w-full text-sm">
                  <tbody>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50 w-40">국민연금</td>
                      <td className="px-3 py-2 text-right text-red-600">
                        {item.nationalPension.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50">건강보험</td>
                      <td className="px-3 py-2 text-right text-red-600">
                        {item.healthInsurance.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50">고용보험</td>
                      <td className="px-3 py-2 text-right text-red-600">
                        {item.employmentInsurance.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50">주택청약</td>
                      <td className="px-3 py-2 text-right text-red-600">
                        {item.housingFund.toLocaleString()}원
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* 특별공제 */}
              <div className="border rounded">
                <div className="bg-orange-50 px-3 py-2 font-medium text-sm border-b">
                  특별소득공제
                </div>
                <table className="w-full text-sm">
                  <tbody>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50 w-40">신용카드공제</td>
                      <td className="px-3 py-2 text-right text-red-600">
                        {item.creditCardDeduction.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50">의료비공제</td>
                      <td className="px-3 py-2 text-right text-red-600">
                        {item.medicalExpense.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50">교육비공제</td>
                      <td className="px-3 py-2 text-right text-red-600">
                        {item.educationExpense.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50">기부금공제</td>
                      <td className="px-3 py-2 text-right text-red-600">
                        {item.donationDeduction.toLocaleString()}원
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* 공제 합계 */}
              <div className="border rounded bg-gray-100">
                <div className="px-3 py-3 flex justify-between items-center">
                  <span className="font-medium">총 공제금액</span>
                  <span className="text-red-600 font-bold text-lg">
                    {item.totalDeduction.toLocaleString()}원
                  </span>
                </div>
              </div>
            </div>
          )}

          {activeTab === "tax" && (
            <div className="space-y-4">
              {/* 과세표준 계산 */}
              <div className="border rounded">
                <div className="bg-blue-50 px-3 py-2 font-medium text-sm border-b">
                  과세표준 계산
                </div>
                <table className="w-full text-sm">
                  <tbody>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50 w-48">총소득</td>
                      <td className="px-3 py-2 text-right">
                        {item.totalIncome.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50">(-) 비과세소득</td>
                      <td className="px-3 py-2 text-right text-green-600">
                        {item.totalNonTaxable.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50">(-) 소득공제</td>
                      <td className="px-3 py-2 text-right text-red-600">
                        {item.totalDeduction.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className="bg-yellow-50">
                      <td className="px-3 py-2 font-medium">(=) 과세표준</td>
                      <td className="px-3 py-2 text-right font-bold">
                        {item.taxableIncome.toLocaleString()}원
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* 산출세액 */}
              <div className="border rounded">
                <div className="bg-red-50 px-3 py-2 font-medium text-sm border-b">
                  세액 계산
                </div>
                <table className="w-full text-sm">
                  <tbody>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50 w-48">산출세액</td>
                      <td className="px-3 py-2 text-right">
                        {item.calculatedTax.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50">(-) 세액공제</td>
                      <td className="px-3 py-2 text-right text-green-600">
                        {item.taxCredit.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className="bg-red-50">
                      <td className="px-3 py-2 font-medium">(=) 결정세액</td>
                      <td className="px-3 py-2 text-right font-bold text-red-600">
                        {item.finalTax.toLocaleString()}원
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* 정산결과 */}
              <div className="border rounded">
                <div className="bg-purple-50 px-3 py-2 font-medium text-sm border-b">
                  정산 결과
                </div>
                <table className="w-full text-sm">
                  <tbody>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50 w-48">결정세액</td>
                      <td className="px-3 py-2 text-right text-red-600">
                        {item.finalTax.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="px-3 py-2 bg-gray-50">(-) 기납부세액</td>
                      <td className="px-3 py-2 text-right text-blue-600">
                        {item.paidTax.toLocaleString()}원
                      </td>
                    </tr>
                    <tr className={`${item.settlementType === "환급" ? "bg-green-100" : "bg-red-100"}`}>
                      <td className="px-3 py-2 font-medium">(=) 정산금액</td>
                      <td className="px-3 py-2 text-right">
                        <span className={`font-bold text-lg ${
                          item.settlementType === "환급" ? "text-green-600" : "text-red-600"
                        }`}>
                          {item.settlementType === "환급" ? "+" : "-"}
                          {item.settlementAmount.toLocaleString()}원
                        </span>
                        <span className={`ml-2 px-2 py-0.5 rounded text-sm ${
                          item.settlementType === "환급"
                            ? "bg-green-200 text-green-800"
                            : "bg-red-200 text-red-800"
                        }`}>
                          {item.settlementType}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* 모달 푸터 */}
        <div className="flex justify-end gap-2 px-4 py-3 border-t bg-gray-50">
          <button className="px-4 py-1.5 text-sm border border-gray-400 rounded hover:bg-gray-100">
            인쇄
          </button>
          <button className="px-4 py-1.5 text-sm border border-gray-400 rounded hover:bg-gray-100">
            PDF 저장
          </button>
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}

export function YearEndSettlement() {
  const [year, setYear] = useState("2024");
  const [departmentFilter, setDepartmentFilter] = useState("전체");
  const [statusFilter, setStatusFilter] = useState("전체");
  const [data] = useState<YearEndSettlementItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detailItem, setDetailItem] = useState<YearEndSettlementItem | null>(null);

  const departments = ["전체", ...new Set(data.map((d) => d.department))];

  const filteredData = data.filter(
    (item) =>
      (departmentFilter === "전체" || item.department === departmentFilter) &&
      (statusFilter === "전체" || item.status === statusFilter)
  );

  // 정산유형별 집계
  const settlementSummary = filteredData.reduce(
    (acc, item) => {
      if (item.settlementType === "환급") {
        acc.refundCount += 1;
        acc.refundAmount += item.settlementAmount;
      } else {
        acc.additionalCount += 1;
        acc.additionalAmount += item.settlementAmount;
      }
      acc.totalIncome += item.totalIncome;
      acc.totalDeduction += item.totalDeduction;
      acc.totalFinalTax += item.finalTax;
      return acc;
    },
    { refundCount: 0, refundAmount: 0, additionalCount: 0, additionalAmount: 0, totalIncome: 0, totalDeduction: 0, totalFinalTax: 0 }
  );

  // 상태별 집계
  const statusSummary = filteredData.reduce((acc, item) => {
    acc[item.status] = (acc[item.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const handleDetailClick = (item: YearEndSettlementItem) => {
    setDetailItem(item);
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">연말정산</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📥</span> 자료수집
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🧮</span> 일괄계산
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📊</span> 보고서출력
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 엑셀변환
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📤</span> 전자신고
        </button>
      </div>

      {/* 검색 조건 */}
      <div className="flex items-center gap-4 border-b bg-white px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="text-xs">귀속년도:</span>
          <select
            value={year}
            onChange={(e) => setYear(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="2024">2024년</option>
            <option value="2023">2023년</option>
            <option value="2022">2022년</option>
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
        <div className="flex items-center gap-2">
          <span className="text-xs">진행상태:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="미제출">미제출</option>
            <option value="진행중">진행중</option>
            <option value="완료">완료</option>
          </select>
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색(F)
        </button>
      </div>

      {/* 요약 정보 */}
      <div className="grid grid-cols-4 gap-2 border-b bg-yellow-50 px-3 py-2">
        <div className="bg-white px-3 py-2 rounded border text-center">
          <div className="text-xs text-gray-600">총 대상인원</div>
          <div className="text-lg font-bold">{filteredData.length}명</div>
          <div className="text-xs text-gray-500">
            완료: {statusSummary["완료"] || 0} / 진행중: {statusSummary["진행중"] || 0} / 미제출: {statusSummary["미제출"] || 0}
          </div>
        </div>
        <div className="bg-white px-3 py-2 rounded border text-center">
          <div className="text-xs text-gray-600">총소득</div>
          <div className="text-lg font-bold text-blue-600">
            {settlementSummary.totalIncome.toLocaleString()}원
          </div>
        </div>
        <div className="bg-white px-3 py-2 rounded border text-center">
          <div className="text-xs text-gray-600">환급 대상</div>
          <div className="text-lg font-bold text-green-600">
            {settlementSummary.refundCount}명 / {settlementSummary.refundAmount.toLocaleString()}원
          </div>
        </div>
        <div className="bg-white px-3 py-2 rounded border text-center">
          <div className="text-xs text-gray-600">추가납부 대상</div>
          <div className="text-lg font-bold text-red-600">
            {settlementSummary.additionalCount}명 / {settlementSummary.additionalAmount.toLocaleString()}원
          </div>
        </div>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-20">사원코드</th>
              <th className="border border-gray-400 px-2 py-1 w-20">성명</th>
              <th className="border border-gray-400 px-2 py-1 w-16">부서</th>
              <th className="border border-gray-400 px-2 py-1 w-16">직급</th>
              <th className="border border-gray-400 px-2 py-1 w-28">총소득</th>
              <th className="border border-gray-400 px-2 py-1 w-24">비과세</th>
              <th className="border border-gray-400 px-2 py-1 w-24">소득공제</th>
              <th className="border border-gray-400 px-2 py-1 w-24">과세표준</th>
              <th className="border border-gray-400 px-2 py-1 w-24">결정세액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">기납부세액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">정산금액</th>
              <th className="border border-gray-400 px-2 py-1 w-16">정산유형</th>
              <th className="border border-gray-400 px-2 py-1 w-16">상태</th>
              <th className="border border-gray-400 px-2 py-1 w-16">상세</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr
                key={item.id}
                className={`cursor-pointer ${
                  selectedId === item.id
                    ? "bg-[#316AC5] text-white"
                    : item.settlementType === "환급"
                    ? "bg-green-50 hover:bg-green-100"
                    : "bg-red-50 hover:bg-red-100"
                }`}
                onClick={() => setSelectedId(item.id)}
                onDoubleClick={() => handleDetailClick(item)}
              >
                <td className="border border-gray-300 px-2 py-1">{item.employeeCode}</td>
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.employeeName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.department}</td>
                <td className="border border-gray-300 px-2 py-1">{item.position}</td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">
                  {item.totalIncome.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-green-600">
                  {item.totalNonTaxable.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-red-600">
                  {item.totalDeduction.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.taxableIncome.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-red-600">
                  {item.finalTax.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600">
                  {item.paidTax.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right font-medium ${
                  selectedId === item.id
                    ? ""
                    : item.settlementType === "환급"
                    ? "text-green-600"
                    : "text-red-600"
                }`}>
                  {item.settlementType === "환급" ? "+" : "-"}
                  {item.settlementAmount.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  selectedId === item.id
                    ? ""
                    : item.settlementType === "환급"
                    ? "text-green-600"
                    : "text-red-600"
                }`}>
                  {item.settlementType}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  selectedId === item.id
                    ? ""
                    : item.status === "완료"
                    ? "text-blue-600"
                    : item.status === "진행중"
                    ? "text-orange-600"
                    : "text-gray-600"
                }`}>
                  {item.status}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDetailClick(item);
                    }}
                    className={`px-2 py-0.5 rounded text-xs ${
                      selectedId === item.id
                        ? "bg-white text-blue-600"
                        : "bg-blue-500 text-white hover:bg-blue-600"
                    }`}
                  >
                    상세
                  </button>
                </td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={4}>
                (합계: {filteredData.length}명)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {settlementSummary.totalIncome.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-green-600">
                {filteredData.reduce((sum, item) => sum + item.totalNonTaxable, 0).toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {settlementSummary.totalDeduction.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {filteredData.reduce((sum, item) => sum + item.taxableIncome, 0).toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {settlementSummary.totalFinalTax.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {filteredData.reduce((sum, item) => sum + item.paidTax, 0).toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                환급: +{settlementSummary.refundAmount.toLocaleString()} /
                추납: -{settlementSummary.additionalAmount.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={3}></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 하단 정보 */}
      <div className="flex items-center gap-6 border-t bg-purple-50 px-3 py-2 text-xs">
        <span className="font-medium">연말정산 요약:</span>
        <span className="text-green-600">
          환급: {settlementSummary.refundCount}명 (+{settlementSummary.refundAmount.toLocaleString()}원)
        </span>
        <span className="text-red-600">
          추가납부: {settlementSummary.additionalCount}명 (-{settlementSummary.additionalAmount.toLocaleString()}원)
        </span>
        <span className={`font-bold ${
          settlementSummary.refundAmount > settlementSummary.additionalAmount ? "text-green-600" : "text-red-600"
        }`}>
          순정산: {settlementSummary.refundAmount > settlementSummary.additionalAmount ? "+" : "-"}
          {Math.abs(settlementSummary.refundAmount - settlementSummary.additionalAmount).toLocaleString()}원
        </span>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        {year}년 귀속 연말정산 | 총 {filteredData.length}건 | loading ok
      </div>

      {/* 상세 모달 */}
      {detailItem && (
        <DeductionDetailModal
          item={detailItem}
          onClose={() => setDetailItem(null)}
        />
      )}
    </div>
  );
}
