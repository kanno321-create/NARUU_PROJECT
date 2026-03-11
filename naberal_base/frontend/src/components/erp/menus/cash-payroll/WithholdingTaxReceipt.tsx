"use client";

import React, { useState } from "react";

interface WithholdingTaxItem {
  id: string;
  taxYear: string;
  employeeNo: string;
  name: string;
  residentNo: string;
  department: string;
  totalSalary: number;
  taxableIncome: number;
  incomeTaxWithheld: number;
  localTaxWithheld: number;
  totalTaxWithheld: number;
  issueDate: string;
  issueStatus: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: WithholdingTaxItem[] = [
  {
    id: "1",
    taxYear: "2025",
    employeeNo: "EMP001",
    name: "김철수",
    residentNo: "850101-1******",
    department: "영업부",
    totalSalary: 54000000,
    taxableIncome: 48600000,
    incomeTaxWithheld: 1020000,
    localTaxWithheld: 102000,
    totalTaxWithheld: 1122000,
    issueDate: "",
    issueStatus: "미발급",
  },
  {
    id: "2",
    taxYear: "2025",
    employeeNo: "EMP002",
    name: "이영희",
    residentNo: "900515-2******",
    department: "관리부",
    totalSalary: 43200000,
    taxableIncome: 38880000,
    incomeTaxWithheld: 624000,
    localTaxWithheld: 62400,
    totalTaxWithheld: 686400,
    issueDate: "",
    issueStatus: "미발급",
  },
  {
    id: "3",
    taxYear: "2024",
    employeeNo: "EMP001",
    name: "김철수",
    residentNo: "850101-1******",
    department: "영업부",
    totalSalary: 52000000,
    taxableIncome: 46800000,
    incomeTaxWithheld: 980000,
    localTaxWithheld: 98000,
    totalTaxWithheld: 1078000,
    issueDate: "2025-01-15",
    issueStatus: "발급완료",
  },
  {
    id: "4",
    taxYear: "2024",
    employeeNo: "EMP002",
    name: "이영희",
    residentNo: "900515-2******",
    department: "관리부",
    totalSalary: 41500000,
    taxableIncome: 37350000,
    incomeTaxWithheld: 598000,
    localTaxWithheld: 59800,
    totalTaxWithheld: 657800,
    issueDate: "2025-01-15",
    issueStatus: "발급완료",
  },
  {
    id: "5",
    taxYear: "2024",
    employeeNo: "EMP003",
    name: "박민수",
    residentNo: "950720-1******",
    department: "생산부",
    totalSalary: 36000000,
    taxableIncome: 32400000,
    incomeTaxWithheld: 456000,
    localTaxWithheld: 45600,
    totalTaxWithheld: 501600,
    issueDate: "2025-01-15",
    issueStatus: "발급완료",
  },
];

export function WithholdingTaxReceipt() {
  const [taxYear, setTaxYear] = useState("2025");
  const [statusFilter, setStatusFilter] = useState("전체");
  const [employeeSearch, setEmployeeSearch] = useState("");
  const [data, setData] = useState<WithholdingTaxItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [detailItem, setDetailItem] = useState<WithholdingTaxItem | null>(null);

  const filteredData = data.filter(
    (item) =>
      item.taxYear === taxYear &&
      (statusFilter === "전체" || item.issueStatus === statusFilter) &&
      (employeeSearch === "" || item.name.includes(employeeSearch) || item.employeeNo.includes(employeeSearch))
  );

  // 총계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      totalSalary: acc.totalSalary + item.totalSalary,
      taxableIncome: acc.taxableIncome + item.taxableIncome,
      totalTaxWithheld: acc.totalTaxWithheld + item.totalTaxWithheld,
    }),
    { totalSalary: 0, taxableIncome: 0, totalTaxWithheld: 0 }
  );

  const handleIssue = () => {
    if (selectedId) {
      const today = new Date().toISOString().split("T")[0];
      setData(data.map((d) =>
        d.id === selectedId
          ? { ...d, issueDate: today, issueStatus: "발급완료" }
          : d
      ));
    }
  };

  const handleBulkIssue = () => {
    if (window.confirm("미발급 항목을 모두 발급하시겠습니까?")) {
      const today = new Date().toISOString().split("T")[0];
      setData(data.map((d) =>
        d.taxYear === taxYear && d.issueStatus === "미발급"
          ? { ...d, issueDate: today, issueStatus: "발급완료" }
          : d
      ));
    }
  };

  const handleShowDetail = (item: WithholdingTaxItem) => {
    setDetailItem(item);
    setShowDetailModal(true);
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">원천징수영수증</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button
          onClick={handleIssue}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
          <span>📄</span> 발급
        </button>
        <button
          onClick={handleBulkIssue}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
          <span>📑</span> 일괄발급
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🖨️</span> 인쇄
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 엑셀변환
        </button>
      </div>

      {/* 검색 조건 */}
      <div className="flex items-center gap-4 border-b bg-white px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="text-xs">귀속연도:</span>
          <select
            value={taxYear}
            onChange={(e) => setTaxYear(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="2025">2025년</option>
            <option value="2024">2024년</option>
            <option value="2023">2023년</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">발급상태:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="미발급">미발급</option>
            <option value="발급완료">발급완료</option>
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
              <th className="border border-gray-400 px-2 py-1 w-16">귀속년도</th>
              <th className="border border-gray-400 px-2 py-1 w-20">사번</th>
              <th className="border border-gray-400 px-2 py-1 w-20">성명</th>
              <th className="border border-gray-400 px-2 py-1 w-32">주민등록번호</th>
              <th className="border border-gray-400 px-2 py-1 w-20">부서</th>
              <th className="border border-gray-400 px-2 py-1 w-28">총급여</th>
              <th className="border border-gray-400 px-2 py-1 w-28">과세소득</th>
              <th className="border border-gray-400 px-2 py-1 w-24">소득세</th>
              <th className="border border-gray-400 px-2 py-1 w-24">지방소득세</th>
              <th className="border border-gray-400 px-2 py-1 w-28">원천징수합계</th>
              <th className="border border-gray-400 px-2 py-1 w-24">발급일</th>
              <th className="border border-gray-400 px-2 py-1 w-20">상태</th>
              <th className="border border-gray-400 px-2 py-1 w-20">상세</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr
                key={item.id}
                className={`cursor-pointer ${
                  selectedId === item.id
                    ? "bg-[#316AC5] text-white"
                    : item.issueStatus === "미발급"
                    ? "bg-yellow-50 hover:bg-yellow-100"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
              >
                <td className="border border-gray-300 px-2 py-1 text-center">{item.taxYear}</td>
                <td className="border border-gray-300 px-2 py-1">{item.employeeNo}</td>
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.name}</td>
                <td className="border border-gray-300 px-2 py-1">{item.residentNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.department}</td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.totalSalary.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.taxableIncome.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-red-600">
                  {item.incomeTaxWithheld.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-red-600">
                  {item.localTaxWithheld.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium text-red-600">
                  {item.totalTaxWithheld.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.issueDate || "-"}</td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  item.issueStatus === "발급완료" ? "text-green-600" : "text-orange-600"
                }`}>
                  {item.issueStatus}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <button
                    onClick={(e) => { e.stopPropagation(); handleShowDetail(item); }}
                    className="rounded bg-blue-500 px-2 py-0.5 text-white hover:bg-blue-600"
                  >
                    보기
                  </button>
                </td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={5}>
                (합계: {filteredData.length}건)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.totalSalary.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.taxableIncome.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1" colSpan={2}></td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600">
                {totals.totalTaxWithheld.toLocaleString()}
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

      {/* 상세 모달 */}
      {showDetailModal && detailItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-[450px] bg-white shadow-lg">
            <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">원천징수영수증 - {detailItem.taxYear}년</span>
              <button onClick={() => setShowDetailModal(false)} className="text-white hover:text-gray-200">✕</button>
            </div>
            <div className="p-4">
              <div className="border-b pb-3 mb-3">
                <div className="text-center font-bold text-lg mb-2">원천징수영수증</div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div><span className="text-gray-500">귀속연도:</span> {detailItem.taxYear}년</div>
                  <div><span className="text-gray-500">발급일:</span> {detailItem.issueDate || "-"}</div>
                </div>
              </div>

              <div className="space-y-3 text-xs">
                <div className="bg-gray-50 p-2 rounded">
                  <div className="font-medium mb-1">▶ 근로자 정보</div>
                  <div className="grid grid-cols-2 gap-1">
                    <div>성명: {detailItem.name}</div>
                    <div>주민번호: {detailItem.residentNo}</div>
                    <div>사번: {detailItem.employeeNo}</div>
                    <div>부서: {detailItem.department}</div>
                  </div>
                </div>

                <div className="bg-blue-50 p-2 rounded">
                  <div className="font-medium mb-1">▶ 소득 내역</div>
                  <div className="grid grid-cols-2 gap-1">
                    <div>총급여액:</div>
                    <div className="text-right font-medium">{detailItem.totalSalary.toLocaleString()}원</div>
                    <div>과세소득:</div>
                    <div className="text-right">{detailItem.taxableIncome.toLocaleString()}원</div>
                  </div>
                </div>

                <div className="bg-red-50 p-2 rounded">
                  <div className="font-medium mb-1">▶ 원천징수 세액</div>
                  <div className="grid grid-cols-2 gap-1">
                    <div>소득세:</div>
                    <div className="text-right text-red-600">{detailItem.incomeTaxWithheld.toLocaleString()}원</div>
                    <div>지방소득세:</div>
                    <div className="text-right text-red-600">{detailItem.localTaxWithheld.toLocaleString()}원</div>
                    <div className="font-medium">합계:</div>
                    <div className="text-right font-bold text-red-600">{detailItem.totalTaxWithheld.toLocaleString()}원</div>
                  </div>
                </div>
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
