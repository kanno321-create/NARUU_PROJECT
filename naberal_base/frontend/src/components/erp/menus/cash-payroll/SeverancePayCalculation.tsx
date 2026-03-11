"use client";

import React, { useState } from "react";

interface SeverancePayItem {
  id: string;
  employeeNo: string;
  name: string;
  department: string;
  joinDate: string;
  resignDate: string;
  workYears: number;
  workMonths: number;
  workDays: number;
  avgSalary3Months: number;
  severancePay: number;
  annualLeaveBalance: number;
  annualLeavePay: number;
  totalPayment: number;
  status: string;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: SeverancePayItem[] = [
  {
    id: "1",
    employeeNo: "EMP010",
    name: "홍길동",
    department: "영업부",
    joinDate: "2020-03-15",
    resignDate: "2025-12-31",
    workYears: 5,
    workMonths: 9,
    workDays: 16,
    avgSalary3Months: 4200000,
    severancePay: 24150000,
    annualLeaveBalance: 8,
    annualLeavePay: 1120000,
    totalPayment: 25270000,
    status: "계산완료",
  },
  {
    id: "2",
    employeeNo: "EMP015",
    name: "이순신",
    department: "생산부",
    joinDate: "2022-06-01",
    resignDate: "2025-11-30",
    workYears: 3,
    workMonths: 5,
    workDays: 29,
    avgSalary3Months: 3500000,
    severancePay: 12250000,
    annualLeaveBalance: 5,
    annualLeavePay: 583300,
    totalPayment: 12833300,
    status: "지급완료",
  },
  {
    id: "3",
    employeeNo: "EMP020",
    name: "장보고",
    department: "관리부",
    joinDate: "2023-01-02",
    resignDate: "2025-10-15",
    workYears: 2,
    workMonths: 9,
    workDays: 13,
    avgSalary3Months: 3000000,
    severancePay: 8250000,
    annualLeaveBalance: 3,
    annualLeavePay: 300000,
    totalPayment: 8550000,
    status: "지급완료",
  },
];

export function SeverancePayCalculation() {
  const [year, setYear] = useState("2025");
  const [statusFilter, setStatusFilter] = useState("전체");
  const [data, setData] = useState<SeverancePayItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState<SeverancePayItem | null>(null);

  const filteredData = data.filter(
    (item) =>
      item.resignDate.startsWith(year) &&
      (statusFilter === "전체" || item.status === statusFilter)
  );

  // 총계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      severancePay: acc.severancePay + item.severancePay,
      annualLeavePay: acc.annualLeavePay + item.annualLeavePay,
      totalPayment: acc.totalPayment + item.totalPayment,
    }),
    { severancePay: 0, annualLeavePay: 0, totalPayment: 0 }
  );

  const handleNew = () => {
    setEditItem({
      id: String(Date.now()),
      employeeNo: "",
      name: "",
      department: "",
      joinDate: "",
      resignDate: new Date().toISOString().split("T")[0],
      workYears: 0,
      workMonths: 0,
      workDays: 0,
      avgSalary3Months: 0,
      severancePay: 0,
      annualLeaveBalance: 0,
      annualLeavePay: 0,
      totalPayment: 0,
      status: "계산중",
    });
    setShowModal(true);
  };

  const calculateSeverance = () => {
    if (editItem && editItem.joinDate && editItem.resignDate) {
      const join = new Date(editItem.joinDate);
      const resign = new Date(editItem.resignDate);
      const diffTime = resign.getTime() - join.getTime();
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

      const years = Math.floor(diffDays / 365);
      const months = Math.floor((diffDays % 365) / 30);
      const days = diffDays % 30;

      // 퇴직금 = (평균임금 × 30일 × 근속연수)
      const totalMonths = years * 12 + months + days / 30;
      const severancePay = Math.round((editItem.avgSalary3Months / 30) * 30 * (totalMonths / 12));

      // 연차수당 = (평균임금 / 30) × 잔여연차일수
      const annualLeavePay = Math.round((editItem.avgSalary3Months / 30) * editItem.annualLeaveBalance);

      setEditItem({
        ...editItem,
        workYears: years,
        workMonths: months,
        workDays: days,
        severancePay,
        annualLeavePay,
        totalPayment: severancePay + annualLeavePay,
        status: "계산완료",
      });
    }
  };

  const handleSave = () => {
    if (editItem) {
      const exists = data.find((d) => d.id === editItem.id);
      if (exists) {
        setData(data.map((d) => (d.id === editItem.id ? editItem : d)));
      } else {
        setData([...data, editItem]);
      }
      setShowModal(false);
      setEditItem(null);
    }
  };

  const handleEdit = () => {
    const item = data.find((d) => d.id === selectedId);
    if (item) {
      setEditItem({ ...item });
      setShowModal(true);
    }
  };

  const handlePayment = () => {
    if (selectedId) {
      setData(data.map((d) =>
        d.id === selectedId ? { ...d, status: "지급완료" } : d
      ));
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">퇴직금계산</span>
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
          <span>➕</span> 신규계산
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
          <span>✏️</span> 수정
        </button>
        <button
          onClick={handlePayment}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
          <span>💰</span> 지급처리
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 엑셀변환
        </button>
      </div>

      {/* 검색 조건 */}
      <div className="flex items-center gap-4 border-b bg-white px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="text-xs">퇴직연도:</span>
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
          <span className="text-xs">상태:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="계산중">계산중</option>
            <option value="계산완료">계산완료</option>
            <option value="지급완료">지급완료</option>
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
              <th className="border border-gray-400 px-2 py-1 w-24">입사일</th>
              <th className="border border-gray-400 px-2 py-1 w-24">퇴직일</th>
              <th className="border border-gray-400 px-2 py-1 w-24">근속기간</th>
              <th className="border border-gray-400 px-2 py-1 w-28">3개월평균임금</th>
              <th className="border border-gray-400 px-2 py-1 w-28">퇴직금</th>
              <th className="border border-gray-400 px-2 py-1 w-16">연차잔여</th>
              <th className="border border-gray-400 px-2 py-1 w-24">연차수당</th>
              <th className="border border-gray-400 px-2 py-1 w-28">총지급액</th>
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
                    : item.status === "지급완료"
                    ? "bg-green-50 hover:bg-green-100"
                    : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
                onDoubleClick={handleEdit}
              >
                <td className="border border-gray-300 px-2 py-1">{item.employeeNo}</td>
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.name}</td>
                <td className="border border-gray-300 px-2 py-1">{item.department}</td>
                <td className="border border-gray-300 px-2 py-1">{item.joinDate}</td>
                <td className="border border-gray-300 px-2 py-1">{item.resignDate}</td>
                <td className="border border-gray-300 px-2 py-1">
                  {item.workYears}년 {item.workMonths}개월 {item.workDays}일
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.avgSalary3Months.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right text-blue-600 font-medium">
                  {item.severancePay.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-center">
                  {item.annualLeaveBalance}일
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right">
                  {item.annualLeavePay.toLocaleString()}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-bold text-green-600">
                  {item.totalPayment.toLocaleString()}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-center ${
                  item.status === "지급완료" ? "text-green-600" : item.status === "계산완료" ? "text-blue-600" : "text-orange-600"
                }`}>
                  {item.status}
                </td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={7}>
                (합계: {filteredData.length}건)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600">
                {totals.severancePay.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1"></td>
              <td className="border border-gray-400 px-2 py-1 text-right">
                {totals.annualLeavePay.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-green-600">
                {totals.totalPayment.toLocaleString()}
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

      {/* 계산 모달 */}
      {showModal && editItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-[500px] bg-white shadow-lg">
            <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">퇴직금 계산</span>
              <button onClick={() => setShowModal(false)} className="text-white hover:text-gray-200">✕</button>
            </div>
            <div className="p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs mb-1">사번 *</label>
                  <input
                    type="text"
                    value={editItem.employeeNo}
                    onChange={(e) => setEditItem({ ...editItem, employeeNo: e.target.value })}
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
                  <label className="block text-xs mb-1">부서</label>
                  <input
                    type="text"
                    value={editItem.department}
                    onChange={(e) => setEditItem({ ...editItem, department: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">입사일 *</label>
                  <input
                    type="date"
                    value={editItem.joinDate}
                    onChange={(e) => setEditItem({ ...editItem, joinDate: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">퇴직일 *</label>
                  <input
                    type="date"
                    value={editItem.resignDate}
                    onChange={(e) => setEditItem({ ...editItem, resignDate: e.target.value })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">3개월 평균임금 *</label>
                  <input
                    type="number"
                    value={editItem.avgSalary3Months}
                    onChange={(e) => setEditItem({ ...editItem, avgSalary3Months: Number(e.target.value) })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1">잔여 연차일수</label>
                  <input
                    type="number"
                    value={editItem.annualLeaveBalance}
                    onChange={(e) => setEditItem({ ...editItem, annualLeaveBalance: Number(e.target.value) })}
                    className="w-full rounded border border-gray-400 px-2 py-1 text-xs"
                  />
                </div>
                <div>
                  <button
                    onClick={calculateSeverance}
                    className="w-full mt-4 rounded bg-orange-500 px-4 py-1 text-xs text-white hover:bg-orange-600"
                  >
                    퇴직금 계산
                  </button>
                </div>
              </div>

              {editItem.severancePay > 0 && (
                <div className="bg-green-50 p-3 rounded mt-3">
                  <div className="text-xs font-medium mb-2">▶ 계산 결과</div>
                  <div className="grid grid-cols-2 gap-1 text-xs">
                    <div>근속기간:</div>
                    <div className="text-right">{editItem.workYears}년 {editItem.workMonths}개월 {editItem.workDays}일</div>
                    <div>퇴직금:</div>
                    <div className="text-right text-blue-600 font-medium">{editItem.severancePay.toLocaleString()}원</div>
                    <div>연차수당:</div>
                    <div className="text-right">{editItem.annualLeavePay.toLocaleString()}원</div>
                    <div className="font-bold">총 지급액:</div>
                    <div className="text-right font-bold text-green-600">{editItem.totalPayment.toLocaleString()}원</div>
                  </div>
                </div>
              )}
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
