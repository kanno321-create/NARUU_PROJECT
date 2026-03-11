"use client";

import React, { useState, useEffect } from "react";
import { useWindowContextOptional } from "../ERPContext";
import { api, ERPPayroll, ERPPayrollItem, ERPPayrollCreate } from "@/lib/api";

interface Employee {
  id: string;
  employeeNo: string;
  name: string;
  department?: string;
  position: string;
  isPaid: boolean;
  isSent: boolean;
}

interface PayrollRecord {
  id: string;
  employeeId: string;
  workDays: number;
  overtimeHours: number;
  nightHours: number;
  holidayHours: number;
  baseSalary: number;
  positionPay: number;
  overtimePay: number;
  nightPay: number;
  holidayPay: number;
  otherPay: number;
  taxableTotal: number;
  paymentTotal: number;
  incomeTax: number;
  localTax: number;
  healthIns: number;
  longTermCare: number;
  pension: number;
  employmentIns: number;
  industrialIns: number;
  otherDeduction: number;
  deductionTotal: number;
  netPay: number;
}

interface InsuranceRates {
  healthInsRate: number;      // 건강보험 3.545%
  longTermCareRate: number;   // 장기요양 12.81% of 건강보험
  pensionRate: number;        // 국민연금 4.5%
  employmentInsRate: number;  // 고용보험 0.8%
}

const DEFAULT_INSURANCE_RATES: InsuranceRates = {
  healthInsRate: 3.545,
  longTermCareRate: 12.81,
  pensionRate: 4.5,
  employmentInsRate: 0.8,
};

// 간이세액표 근사치 (월급여 기준)
function calculateIncomeTax(taxableTotal: number): number {
  if (taxableTotal <= 1060000) return 0;
  if (taxableTotal <= 1500000) return Math.round(taxableTotal * 0.006);
  if (taxableTotal <= 2000000) return Math.round(taxableTotal * 0.015);
  if (taxableTotal <= 2500000) return Math.round(taxableTotal * 0.02);
  if (taxableTotal <= 3000000) return Math.round(taxableTotal * 0.03);
  if (taxableTotal <= 4000000) return Math.round(taxableTotal * 0.04);
  if (taxableTotal <= 5000000) return Math.round(taxableTotal * 0.05);
  if (taxableTotal <= 7000000) return Math.round(taxableTotal * 0.06);
  if (taxableTotal <= 10000000) return Math.round(taxableTotal * 0.08);
  return Math.round(taxableTotal * 0.1);
}

function calculatePayroll(
  baseSalary: number,
  positionPay: number,
  overtimeHours: number,
  nightHours: number,
  holidayHours: number,
  otherPay: number,
  rates: InsuranceRates
): Omit<PayrollRecord, "id" | "employeeId" | "workDays"> {
  const hourlyRate = baseSalary / 209;
  const overtimePay = Math.round(hourlyRate * 1.5 * overtimeHours);
  const nightPay = Math.round(hourlyRate * 0.5 * nightHours);
  const holidayPay = Math.round(hourlyRate * 1.5 * holidayHours);
  const taxableTotal = baseSalary + positionPay + overtimePay + nightPay + holidayPay + otherPay;
  const paymentTotal = taxableTotal;

  const healthIns = Math.round(taxableTotal * rates.healthInsRate / 100);
  const longTermCare = Math.round(healthIns * rates.longTermCareRate / 100);
  const pension = Math.round(taxableTotal * rates.pensionRate / 100);
  const employmentIns = Math.round(taxableTotal * rates.employmentInsRate / 100);
  const industrialIns = 0;
  const incomeTax = calculateIncomeTax(taxableTotal);
  const localTax = Math.round(incomeTax * 0.1);
  const otherDeduction = 0;
  const deductionTotal = incomeTax + localTax + healthIns + longTermCare + pension + employmentIns + industrialIns + otherDeduction;
  const netPay = taxableTotal - deductionTotal;

  return {
    overtimeHours, nightHours, holidayHours,
    baseSalary, positionPay, overtimePay, nightPay, holidayPay, otherPay,
    taxableTotal, paymentTotal,
    incomeTax, localTax, healthIns, longTermCare, pension, employmentIns, industrialIns, otherDeduction,
    deductionTotal, netPay,
  };
}

// 기본 빈 배열 (API에서 로드)
const INITIAL_EMPLOYEES: Employee[] = [];
const INITIAL_PAYROLLS: PayrollRecord[] = [];

export function PayrollWindow() {
  const windowContext = useWindowContextOptional();
  const [employees, setEmployees] = useState<Employee[]>(INITIAL_EMPLOYEES);
  const [payrolls, setPayrolls] = useState<PayrollRecord[]>(INITIAL_PAYROLLS);
  const [apiPayrollId, setApiPayrollId] = useState<string | null>(null);
  const [loadingApi, setLoadingApi] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState<string | null>(null);
  const [searchFilter, setSearchFilter] = useState("");
  const [insuranceRates, setInsuranceRates] = useState<InsuranceRates>(DEFAULT_INSURANCE_RATES);

  // 필터
  const [yearMonth, setYearMonth] = useState("2025-12");
  const [paymentDate, setPaymentDate] = useState("2025-12-01");
  const [paymentInfo, setPaymentInfo] = useState("");

  // 메일 관련
  const [mailSubject, setMailSubject] = useState("");
  const [mailBody, setMailBody] = useState("");
  const [note, setNote] = useState("");
  const [printNote, setPrintNote] = useState(false);

  // 모달 상태
  const [showBasicInfoModal, setShowBasicInfoModal] = useState(false);
  const [showPayrollRegModal, setShowPayrollRegModal] = useState(false);
  const [showMailModal, setShowMailModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  // 기초정보등록 폼
  const [editEmpId, setEditEmpId] = useState<string | null>(null);
  const [editBaseSalary, setEditBaseSalary] = useState(0);
  const [editPositionPay, setEditPositionPay] = useState(0);

  // 급여등록 폼
  const [regWorkDays, setRegWorkDays] = useState(22);
  const [regOvertimeHours, setRegOvertimeHours] = useState(0);
  const [regNightHours, setRegNightHours] = useState(0);
  const [regHolidayHours, setRegHolidayHours] = useState(0);
  const [regOtherPay, setRegOtherPay] = useState(0);

  // 설정 폼
  const [editRates, setEditRates] = useState<InsuranceRates>(DEFAULT_INSURANCE_RATES);

  // API에서 급여 데이터 로드 (primary), localStorage는 캐시
  useEffect(() => {
    const loadData = async () => {
      setLoadingApi(true);
      const [yearStr, monthStr] = yearMonth.split("-");
      const y = parseInt(yearStr);
      const m = parseInt(monthStr);

      try {
        const payrollData = await api.erp.payroll.getByPeriod(y, m);
        setApiPayrollId(payrollData.id);

        // insurance_rates 로드
        if (payrollData.insurance_rates) {
          const rates: InsuranceRates = {
            healthInsRate: payrollData.insurance_rates.healthInsRate ?? DEFAULT_INSURANCE_RATES.healthInsRate,
            longTermCareRate: payrollData.insurance_rates.longTermCareRate ?? DEFAULT_INSURANCE_RATES.longTermCareRate,
            pensionRate: payrollData.insurance_rates.pensionRate ?? DEFAULT_INSURANCE_RATES.pensionRate,
            employmentInsRate: payrollData.insurance_rates.employmentInsRate ?? DEFAULT_INSURANCE_RATES.employmentInsRate,
          };
          setInsuranceRates(rates);
        }

        // items -> employees + payrolls 변환
        const emps: Employee[] = [];
        const pays: PayrollRecord[] = [];
        (payrollData.items || []).forEach((item: ERPPayrollItem, idx: number) => {
          const empId = item.employee_id || String(idx + 1);
          emps.push({
            id: empId,
            employeeNo: String(idx + 1).padStart(2, "0"),
            name: item.employee_name || "",
            position: item.position || "",
            isPaid: payrollData.status === "paid",
            isSent: false,
          });
          pays.push({
            id: String(idx + 1),
            employeeId: empId,
            workDays: 22,
            overtimeHours: 0,
            nightHours: 0,
            holidayHours: 0,
            baseSalary: Number(item.base_salary) || 0,
            positionPay: 0,
            overtimePay: Number(item.overtime_pay) || 0,
            nightPay: 0,
            holidayPay: 0,
            otherPay: Number(item.allowances) || 0,
            taxableTotal: Number(item.total_earnings) || 0,
            paymentTotal: Number(item.total_earnings) || 0,
            incomeTax: Number(item.income_tax) || 0,
            localTax: Number(item.local_income_tax) || 0,
            healthIns: Number(item.health_insurance) || 0,
            longTermCare: Number(item.long_term_care) || 0,
            pension: Number(item.national_pension) || 0,
            employmentIns: Number(item.employment_insurance) || 0,
            industrialIns: 0,
            otherDeduction: Number(item.other_deductions) || 0,
            deductionTotal: Number(item.total_deductions) || 0,
            netPay: Number(item.net_pay) || 0,
          });
        });

        if (emps.length > 0) {
          setEmployees(emps);
          setPayrolls(pays);
          // localStorage 캐시 업데이트
          localStorage.setItem("payroll-data", JSON.stringify({ employees: emps, payrolls: pays }));
        }
      } catch {
        // API 실패 시 localStorage fallback
        setApiPayrollId(null);
        try {
          const savedPayrolls = localStorage.getItem("payroll-data");
          if (savedPayrolls) {
            const parsed = JSON.parse(savedPayrolls);
            if (parsed.employees) setEmployees(parsed.employees);
            if (parsed.payrolls) setPayrolls(parsed.payrolls);
          }
          const savedRates = localStorage.getItem("payroll-insurance-rates");
          if (savedRates) {
            setInsuranceRates(JSON.parse(savedRates));
          }
        } catch { /* ignore */ }
      } finally {
        setLoadingApi(false);
      }
    };

    loadData();
  }, [yearMonth]);

  const savePayrollData = (emps: Employee[], pays: PayrollRecord[]) => {
    // localStorage 캐시 저장
    localStorage.setItem("payroll-data", JSON.stringify({ employees: emps, payrolls: pays }));
  };

  // API로 급여대장 저장/업데이트
  const savePayrollToApi = async (emps: Employee[], pays: PayrollRecord[]) => {
    const [yearStr, monthStr] = yearMonth.split("-");
    const y = parseInt(yearStr);
    const m = parseInt(monthStr);

    const items: ERPPayrollItem[] = pays.map((p, idx) => {
      const emp = emps.find(e => e.id === p.employeeId);
      return {
        employee_id: p.employeeId,
        employee_name: emp?.name || "",
        department: undefined,
        position: emp?.position || undefined,
        base_salary: p.baseSalary,
        overtime_pay: p.overtimePay,
        bonus: 0,
        allowances: p.otherPay,
        total_earnings: p.taxableTotal,
        income_tax: p.incomeTax,
        local_income_tax: p.localTax,
        national_pension: p.pension,
        health_insurance: p.healthIns,
        employment_insurance: p.employmentIns,
        long_term_care: p.longTermCare,
        other_deductions: p.otherDeduction,
        total_deductions: p.deductionTotal,
        net_pay: p.netPay,
      };
    });

    const totalEarnings = pays.reduce((s, p) => s + p.taxableTotal, 0);
    const totalDeductions = pays.reduce((s, p) => s + p.deductionTotal, 0);
    const totalNetPay = pays.reduce((s, p) => s + p.netPay, 0);

    const payrollData: ERPPayrollCreate = {
      year: y,
      month: m,
      pay_date: paymentDate,
      items,
      total_earnings: totalEarnings,
      total_deductions: totalDeductions,
      total_net_pay: totalNetPay,
      insurance_rates: insuranceRates as unknown as Record<string, number>,
    };

    try {
      if (apiPayrollId) {
        const updated = await api.erp.payroll.update(apiPayrollId, payrollData);
        setApiPayrollId(updated.id);
      } else {
        const created = await api.erp.payroll.create(payrollData);
        setApiPayrollId(created.id);
      }
    } catch (err) {
      console.error("API 저장 실패:", err);
      throw err;
    }
  };

  // 검색 필터
  const filteredEmployees = employees.filter((emp) =>
    !searchFilter || emp.name.includes(searchFilter) || emp.employeeNo.includes(searchFilter)
  );

  const selectedPayroll = selectedEmployee
    ? payrolls.find((p) => p.employeeId === selectedEmployee)
    : null;

  const totals = payrolls.reduce(
    (acc, p) => ({
      workDays: acc.workDays + p.workDays,
      overtimeHours: acc.overtimeHours + p.overtimeHours,
      nightHours: acc.nightHours + p.nightHours,
      holidayHours: acc.holidayHours + p.holidayHours,
      baseSalary: acc.baseSalary + p.baseSalary,
      positionPay: acc.positionPay + p.positionPay,
      overtimePay: acc.overtimePay + p.overtimePay,
      nightPay: acc.nightPay + p.nightPay,
      holidayPay: acc.holidayPay + p.holidayPay,
      otherPay: acc.otherPay + p.otherPay,
      taxableTotal: acc.taxableTotal + p.taxableTotal,
      paymentTotal: acc.paymentTotal + p.paymentTotal,
      incomeTax: acc.incomeTax + p.incomeTax,
      localTax: acc.localTax + p.localTax,
      healthIns: acc.healthIns + p.healthIns,
      longTermCare: acc.longTermCare + p.longTermCare,
      pension: acc.pension + p.pension,
      employmentIns: acc.employmentIns + p.employmentIns,
      industrialIns: acc.industrialIns + p.industrialIns,
      otherDeduction: acc.otherDeduction + p.otherDeduction,
      deductionTotal: acc.deductionTotal + p.deductionTotal,
      netPay: acc.netPay + p.netPay,
    }),
    {
      workDays: 0, overtimeHours: 0, nightHours: 0, holidayHours: 0,
      baseSalary: 0, positionPay: 0, overtimePay: 0, nightPay: 0, holidayPay: 0, otherPay: 0,
      taxableTotal: 0, paymentTotal: 0,
      incomeTax: 0, localTax: 0, healthIns: 0, longTermCare: 0, pension: 0, employmentIns: 0, industrialIns: 0, otherDeduction: 0,
      deductionTotal: 0, netPay: 0,
    }
  );

  // --- 버튼 핸들러들 ---

  // 기초정보등록
  const handleBasicInfo = () => {
    setShowBasicInfoModal(true);
  };

  const handleSaveBasicInfo = () => {
    if (!editEmpId) return;
    const payroll = payrolls.find((p) => p.employeeId === editEmpId);
    if (payroll) {
      const updated = calculatePayroll(
        editBaseSalary, editPositionPay,
        payroll.overtimeHours, payroll.nightHours, payroll.holidayHours,
        payroll.otherPay, insuranceRates
      );
      const newPayrolls = payrolls.map((p) =>
        p.employeeId === editEmpId
          ? { ...p, ...updated, workDays: p.workDays }
          : p
      );
      setPayrolls(newPayrolls);
      savePayrollData(employees, newPayrolls);
    }
    // 기초정보 저장
    const settings = JSON.parse(localStorage.getItem("payroll-settings") || "{}");
    settings[editEmpId] = { baseSalary: editBaseSalary, positionPay: editPositionPay };
    localStorage.setItem("payroll-settings", JSON.stringify(settings));
    setShowBasicInfoModal(false);
  };

  // 급여등록
  const handlePayrollReg = () => {
    if (!selectedEmployee) {
      alert("사원을 선택하세요.");
      return;
    }
    const payroll = payrolls.find((p) => p.employeeId === selectedEmployee);
    if (payroll) {
      setRegWorkDays(payroll.workDays);
      setRegOvertimeHours(payroll.overtimeHours);
      setRegNightHours(payroll.nightHours);
      setRegHolidayHours(payroll.holidayHours);
      setRegOtherPay(payroll.otherPay);
    }
    setShowPayrollRegModal(true);
  };

  const handleSavePayrollReg = () => {
    if (!selectedEmployee) return;
    const payroll = payrolls.find((p) => p.employeeId === selectedEmployee);
    if (!payroll) return;

    const updated = calculatePayroll(
      payroll.baseSalary, payroll.positionPay,
      regOvertimeHours, regNightHours, regHolidayHours,
      regOtherPay, insuranceRates
    );
    const newPayrolls = payrolls.map((p) =>
      p.employeeId === selectedEmployee
        ? { ...p, ...updated, workDays: regWorkDays }
        : p
    );
    setPayrolls(newPayrolls);
    savePayrollData(employees, newPayrolls);
    setShowPayrollRegModal(false);
  };

  // 실시간 계산 미리보기
  const getRegPreview = () => {
    if (!selectedEmployee) return null;
    const payroll = payrolls.find((p) => p.employeeId === selectedEmployee);
    if (!payroll) return null;
    return calculatePayroll(
      payroll.baseSalary, payroll.positionPay,
      regOvertimeHours, regNightHours, regHolidayHours,
      regOtherPay, insuranceRates
    );
  };

  // 지급처리
  const handlePayProcess = () => {
    if (!selectedEmployee) {
      alert("사원을 선택하세요.");
      return;
    }
    const newEmployees = employees.map((emp) =>
      emp.id === selectedEmployee ? { ...emp, isPaid: true } : emp
    );
    setEmployees(newEmployees);
    savePayrollData(newEmployees, payrolls);
    alert(`${employees.find((e) => e.id === selectedEmployee)?.name}님 급여 지급 처리 완료\n지급일: ${paymentDate}`);
  };

  // 지급취소
  const handlePayCancel = () => {
    if (!selectedEmployee) {
      alert("사원을 선택하세요.");
      return;
    }
    const newEmployees = employees.map((emp) =>
      emp.id === selectedEmployee ? { ...emp, isPaid: false } : emp
    );
    setEmployees(newEmployees);
    savePayrollData(newEmployees, payrolls);
    alert(`${employees.find((e) => e.id === selectedEmployee)?.name}님 지급 취소 완료`);
  };

  // 출력하기
  const handlePrint = () => {
    const emp = selectedEmployee ? employees.find((e) => e.id === selectedEmployee) : null;
    const payroll = selectedEmployee ? payrolls.find((p) => p.employeeId === selectedEmployee) : null;

    if (!emp || !payroll) {
      alert("출력할 사원을 선택하세요.");
      return;
    }

    const printContent = `
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>급여명세서</title>
<style>
  body { font-family: 'Malgun Gothic', sans-serif; padding: 20px; font-size: 12px; }
  h2 { text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }
  table { width: 100%; border-collapse: collapse; margin: 10px 0; }
  th, td { border: 1px solid #333; padding: 6px 8px; text-align: right; }
  th { background: #f0f0f0; text-align: center; }
  .label { text-align: left; font-weight: bold; }
  .header-info { display: flex; justify-content: space-between; margin: 10px 0; }
  .total { font-weight: bold; color: #1a56db; }
  @media print { body { margin: 0; } }
</style></head><body>
<h2>급 여 명 세 서</h2>
<div class="header-info">
  <div>사원번호: ${emp.employeeNo} / 성명: ${emp.name} / 직급: ${emp.position}</div>
  <div>지급년월: ${yearMonth} / 지급일: ${paymentDate}</div>
</div>
<table>
  <tr><th colspan="2">지급내역</th><th colspan="2">공제내역</th></tr>
  <tr><td class="label">기본급</td><td>${payroll.baseSalary.toLocaleString()}</td><td class="label">소득세</td><td>${payroll.incomeTax.toLocaleString()}</td></tr>
  <tr><td class="label">직책수당</td><td>${payroll.positionPay.toLocaleString()}</td><td class="label">지방소득세</td><td>${payroll.localTax.toLocaleString()}</td></tr>
  <tr><td class="label">연장수당</td><td>${payroll.overtimePay.toLocaleString()}</td><td class="label">건강보험</td><td>${payroll.healthIns.toLocaleString()}</td></tr>
  <tr><td class="label">야근수당</td><td>${payroll.nightPay.toLocaleString()}</td><td class="label">장기요양</td><td>${payroll.longTermCare.toLocaleString()}</td></tr>
  <tr><td class="label">휴일수당</td><td>${payroll.holidayPay.toLocaleString()}</td><td class="label">국민연금</td><td>${payroll.pension.toLocaleString()}</td></tr>
  <tr><td class="label">기타지급</td><td>${payroll.otherPay.toLocaleString()}</td><td class="label">고용보험</td><td>${payroll.employmentIns.toLocaleString()}</td></tr>
  <tr><th class="label">지급합계</th><th class="total">${payroll.taxableTotal.toLocaleString()}</th><th class="label">공제합계</th><th class="total">${payroll.deductionTotal.toLocaleString()}</th></tr>
</table>
<table><tr><th class="label" style="text-align:center">차감지급액</th><td class="total" style="font-size:16px;text-align:center">${payroll.netPay.toLocaleString()} 원</td></tr></table>
${printNote && note ? `<div style="margin-top:10px;border:1px solid #ccc;padding:8px"><strong>비고:</strong> ${note}</div>` : ""}
</body></html>`;

    const printWindow = window.open("", "_blank");
    if (printWindow) {
      printWindow.document.write(printContent);
      printWindow.document.close();
      printWindow.print();
    }
  };

  // 메일전송
  const handleMailSend = () => {
    setShowMailModal(true);
  };

  const handleConfirmMailSend = () => {
    if (!mailSubject) {
      alert("메일 제목을 입력하세요.");
      return;
    }
    const mailHistory = JSON.parse(localStorage.getItem("payroll-mail-history") || "[]");
    const selectedEmps = selectedEmployee
      ? employees.filter((e) => e.id === selectedEmployee)
      : employees;
    mailHistory.unshift({
      subject: mailSubject,
      body: mailBody,
      recipients: selectedEmps.map((e) => e.name),
      sentAt: new Date().toISOString(),
    });
    localStorage.setItem("payroll-mail-history", JSON.stringify(mailHistory));
    const newEmployees = employees.map((emp) => {
      if (!selectedEmployee || emp.id === selectedEmployee) {
        return { ...emp, isSent: true };
      }
      return emp;
    });
    setEmployees(newEmployees);
    savePayrollData(newEmployees, payrolls);
    alert(`${selectedEmps.length}명에게 급여명세서 메일 전송이 등록되었습니다.`);
    setShowMailModal(false);
  };

  // 환경설정
  const handleSettings = () => {
    setEditRates({ ...insuranceRates });
    setShowSettingsModal(true);
  };

  const handleSaveSettings = async () => {
    setInsuranceRates(editRates);
    localStorage.setItem("payroll-insurance-rates", JSON.stringify(editRates));
    // API에도 insurance_rates 반영하여 저장
    if (apiPayrollId) {
      try {
        await savePayrollToApi(employees, payrolls);
      } catch (err) {
        alert("API 저장에 실패했습니다. localStorage에는 저장되었습니다.");
        setShowSettingsModal(false);
        return;
      }
    }
    setShowSettingsModal(false);
    alert("4대보험율이 저장되었습니다.");
  };

  // 검색
  const handleSearch = () => {
    // searchFilter state가 이미 필터링을 처리함
  };

  // 입출금전표생성
  const handleCreateVoucher = () => {
    const paidEmployees = employees.filter((e) => e.isPaid);
    if (paidEmployees.length === 0) {
      alert("지급 처리된 사원이 없습니다.");
      return;
    }
    const paidPayrolls = payrolls.filter((p) => paidEmployees.some((e) => e.id === p.employeeId));
    const totalNetPay = paidPayrolls.reduce((sum, p) => sum + p.netPay, 0);
    const totalDeduction = paidPayrolls.reduce((sum, p) => sum + p.deductionTotal, 0);
    const totalTaxable = paidPayrolls.reduce((sum, p) => sum + p.taxableTotal, 0);

    const now = new Date();
    const voucherDate = paymentDate || now.toISOString().slice(0, 10);
    const voucherId = `PV-${yearMonth.replace('-', '')}-${Date.now()}`;

    // 전표 명세: 사원별 지급/공제 내역
    const details = paidEmployees.map((emp) => {
      const pr = payrolls.find((p) => p.employeeId === emp.id);
      return {
        employeeId: emp.id,
        employeeNo: emp.employeeNo,
        employeeName: emp.name,
        department: emp.department,
        position: emp.position,
        netPay: pr?.netPay || 0,
        deductionTotal: pr?.deductionTotal || 0,
        taxableTotal: pr?.taxableTotal || 0,
      };
    });

    const voucher = {
      id: voucherId,
      type: 'payroll',
      date: voucherDate,
      yearMonth,
      createdAt: now.toISOString(),
      summary: `${yearMonth} 급여 지급 전표 (${paidEmployees.length}명)`,
      slips: [
        {
          type: '출금',
          accountTitle: '급여',
          description: `${yearMonth} 급여 지급 (${paidEmployees.length}명)`,
          amount: totalNetPay,
        },
        {
          type: '출금',
          accountTitle: '예수금 (4대보험/세금)',
          description: `${yearMonth} 4대보험/세금 공제분 납부`,
          amount: totalDeduction,
        },
        {
          type: '대변',
          accountTitle: '보통예금',
          description: `${yearMonth} 급여 총지급액`,
          amount: totalTaxable,
        },
      ],
      details,
      totals: {
        netPay: totalNetPay,
        deduction: totalDeduction,
        gross: totalTaxable,
      },
    };

    // localStorage에 전표 저장
    const existingVouchers = JSON.parse(localStorage.getItem("payroll-vouchers") || "[]");
    existingVouchers.push(voucher);
    localStorage.setItem("payroll-vouchers", JSON.stringify(existingVouchers));

    alert(
      `입출금전표가 생성되었습니다.\n\n` +
      `전표번호: ${voucherId}\n` +
      `전표일자: ${voucherDate}\n` +
      `────────────────\n` +
      `[출금] 급여 지급: ${totalNetPay.toLocaleString()}원\n` +
      `[출금] 4대보험/세금: ${totalDeduction.toLocaleString()}원\n` +
      `[대변] 보통예금: ${totalTaxable.toLocaleString()}원\n` +
      `────────────────\n` +
      `대상 인원: ${paidEmployees.length}명`
    );
  };

  const handleRefresh = () => {
    // API에서 재로드 트리거 (yearMonth 변경 시 useEffect가 재실행)
    const current = yearMonth;
    setYearMonth("");
    setTimeout(() => setYearMonth(current), 50);
    setSelectedEmployee(null);
  };

  const handleSave = async () => {
    savePayrollData(employees, payrolls);
    try {
      await savePayrollToApi(employees, payrolls);
      alert("저장되었습니다.");
    } catch (err) {
      alert("API 저장에 실패했습니다. localStorage에는 저장되었습니다.");
    }
  };

  return (
    <div className="relative flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">급여대장-이지판매상회</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button
          onClick={handleBasicInfo}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-blue-600">👤</span> 기초정보등록
        </button>
        <button
          onClick={handlePayrollReg}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-green-600">💰</span> 급여등록
        </button>
        <button
          onClick={handlePayProcess}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-blue-600">✓</span> 지급처리
        </button>
        <button
          onClick={handlePayCancel}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-red-600">✕</span> 지급취소
        </button>
        <div className="mx-1 h-6 w-px bg-gray-400" />
        <button
          onClick={handlePrint}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span>🖨️</span> 출력하기
        </button>
        <button
          onClick={handleMailSend}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-blue-600">✉</span> 메일전송
        </button>
        <button
          onClick={handleSettings}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span>⚙️</span> 환경설정
        </button>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-blue-600">↻</span> 새로고침
        </button>
      </div>

      {/* 검색 영역 */}
      <div className="flex items-center justify-between border-b bg-gray-100 px-4 py-2">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm">기준급여년월:</span>
            <input
              type="month"
              value={yearMonth}
              onChange={(e) => setYearMonth(e.target.value)}
              className="rounded border border-gray-400 px-2 py-1 text-sm"
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm">지급급여정보:</span>
            <input
              type="text"
              value={paymentInfo}
              onChange={(e) => setPaymentInfo(e.target.value)}
              className="w-40 rounded border border-gray-400 px-2 py-1 text-sm"
            />
            <button className="rounded border border-gray-400 bg-gray-200 px-2 py-1 text-sm hover:bg-gray-300">
              ...
            </button>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="사원명/사번"
              className="w-28 rounded border border-gray-400 px-2 py-1 text-sm"
            />
            <button
              onClick={handleSearch}
              className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
            >
              검 색(F)
            </button>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm">지급일자:</span>
            <input
              type="date"
              value={paymentDate}
              onChange={(e) => setPaymentDate(e.target.value)}
              className="rounded border border-gray-400 px-2 py-1 text-sm"
            />
          </div>
          <button
            onClick={handleCreateVoucher}
            className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
          >
            입출금전표생성
          </button>
        </div>
      </div>

      {/* 포인트 정보 */}
      <div className="flex items-center justify-end gap-4 border-b bg-gray-50 px-4 py-2">
        <div className="flex items-center gap-2 text-sm">
          <span className="font-medium">● 포인트 정보</span>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span>접아이디: <span className="text-blue-600">easypanme</span></span>
          <span>충전된 포인트: <span className="text-blue-600 font-medium">160</span></span>
          <button className="text-blue-600 underline hover:text-blue-800">충전하기</button>
        </div>
      </div>

      {/* 메인 컨텐츠 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 직원 목록 (좌측) */}
        <div className="w-64 border-r bg-white">
          <div className="border-b bg-[#E8E4D9] px-2 py-1 text-sm font-medium">직원목록</div>
          <div className="overflow-auto">
            <table className="w-full border-collapse text-xs">
              <thead className="sticky top-0 bg-[#E8E4D9]">
                <tr>
                  <th className="w-6 border-b border-gray-300 px-1 py-1">
                    <input type="checkbox" />
                  </th>
                  <th className="w-14 border-b border-gray-300 px-1 py-1">지급</th>
                  <th className="w-14 border-b border-gray-300 px-1 py-1">전송</th>
                  <th className="w-10 border-b border-gray-300 px-1 py-1">번호</th>
                  <th className="border-b border-gray-300 px-1 py-1">이름</th>
                  <th className="w-12 border-b border-gray-300 px-1 py-1">직급</th>
                </tr>
              </thead>
              <tbody>
                {filteredEmployees.map((emp) => (
                  <tr
                    key={emp.id}
                    className={`cursor-pointer ${
                      selectedEmployee === emp.id
                        ? "bg-[#316AC5] text-white"
                        : "hover:bg-gray-100"
                    }`}
                    onClick={() => setSelectedEmployee(emp.id)}
                  >
                    <td className="border-b border-gray-200 px-1 py-1 text-center">
                      <input type="checkbox" />
                    </td>
                    <td className="border-b border-gray-200 px-1 py-1 text-center">
                      <span className={emp.isPaid ? "text-blue-600" : "text-red-600"}>
                        {emp.isPaid ? "지급" : "미지급"}
                      </span>
                    </td>
                    <td className="border-b border-gray-200 px-1 py-1 text-center">
                      <span className={emp.isSent ? "text-blue-600" : "text-red-600"}>
                        {emp.isSent ? "전송" : "미전송"}
                      </span>
                    </td>
                    <td className="border-b border-gray-200 px-1 py-1 text-center">{emp.employeeNo}</td>
                    <td className="border-b border-gray-200 px-1 py-1">{emp.name}</td>
                    <td className="border-b border-gray-200 px-1 py-1 text-center">{emp.position}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* 급여 상세 (우측) */}
        <div className="flex-1 overflow-auto">
          <div className="flex border-b bg-[#E8E4D9] text-xs">
            <div className="w-40 border-r border-gray-400 px-2 py-1 text-center font-medium">근무내역</div>
            <div className="flex-1 border-r border-gray-400 px-2 py-1 text-center font-medium">지급내역(과세)</div>
            <div className="w-80 px-2 py-1 text-center font-medium">공제내역</div>
          </div>

          <table className="w-full border-collapse text-xs">
            <thead className="bg-[#E8E4D9]">
              <tr>
                <th className="border border-gray-400 px-1 py-1">근무</th>
                <th className="border border-gray-400 px-1 py-1">연장</th>
                <th className="border border-gray-400 px-1 py-1">야간</th>
                <th className="border border-gray-400 px-1 py-1">휴일</th>
                <th className="border border-gray-400 px-1 py-1">기본급</th>
                <th className="border border-gray-400 px-1 py-1">직책</th>
                <th className="border border-gray-400 px-1 py-1">연장</th>
                <th className="border border-gray-400 px-1 py-1">야근</th>
                <th className="border border-gray-400 px-1 py-1">휴일</th>
                <th className="border border-gray-400 px-1 py-1">기타지급</th>
                <th className="border border-gray-400 px-1 py-1">과세총액</th>
                <th className="border border-gray-400 px-1 py-1">소득세</th>
                <th className="border border-gray-400 px-1 py-1">지방소득세</th>
                <th className="border border-gray-400 px-1 py-1">건강보험</th>
                <th className="border border-gray-400 px-1 py-1">장기요양</th>
                <th className="border border-gray-400 px-1 py-1">국민연금</th>
                <th className="border border-gray-400 px-1 py-1">고용보험</th>
                <th className="border border-gray-400 px-1 py-1">기타공제</th>
                <th className="border border-gray-400 px-1 py-1">공제총액</th>
                <th className="border border-gray-400 px-1 py-1">차감지급액</th>
              </tr>
            </thead>
            <tbody>
              {payrolls.map((p) => (
                <tr
                  key={p.id}
                  className={`${
                    selectedEmployee === p.employeeId
                      ? "bg-[#316AC5] text-white"
                      : "hover:bg-gray-100"
                  }`}
                  onClick={() => setSelectedEmployee(p.employeeId)}
                >
                  <td className="border border-gray-300 px-1 py-1 text-right">{p.workDays}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right">{p.overtimeHours}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right">{p.nightHours}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right">{p.holidayHours}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right">{p.baseSalary.toLocaleString()}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right">{p.positionPay.toLocaleString()}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right">{p.overtimePay.toLocaleString()}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right">{p.nightPay.toLocaleString()}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right">{p.holidayPay.toLocaleString()}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right">{p.otherPay.toLocaleString()}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right font-medium">{p.taxableTotal.toLocaleString()}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right">{p.incomeTax.toLocaleString()}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right">{p.localTax.toLocaleString()}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right">{p.healthIns.toLocaleString()}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right">{p.longTermCare.toLocaleString()}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right">{p.pension.toLocaleString()}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right">{p.employmentIns.toLocaleString()}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right">{p.otherDeduction.toLocaleString()}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right font-medium">{p.deductionTotal.toLocaleString()}</td>
                  <td className="border border-gray-300 px-1 py-1 text-right font-medium text-blue-600">{p.netPay.toLocaleString()}</td>
                </tr>
              ))}
              {/* 합계 행 */}
              <tr className="bg-yellow-50 font-medium">
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.workDays}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.overtimeHours}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.nightHours}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.holidayHours}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.baseSalary.toLocaleString()}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.positionPay.toLocaleString()}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.overtimePay.toLocaleString()}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.nightPay.toLocaleString()}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.holidayPay.toLocaleString()}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.otherPay.toLocaleString()}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.taxableTotal.toLocaleString()}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.incomeTax.toLocaleString()}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.localTax.toLocaleString()}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.healthIns.toLocaleString()}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.longTermCare.toLocaleString()}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.pension.toLocaleString()}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.employmentIns.toLocaleString()}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.otherDeduction.toLocaleString()}</td>
                <td className="border border-gray-300 px-1 py-1 text-right">{totals.deductionTotal.toLocaleString()}</td>
                <td className="border border-gray-300 px-1 py-1 text-right text-blue-600">{totals.netPay.toLocaleString()}</td>
              </tr>
            </tbody>
          </table>

          {/* 하단 요약 */}
          <div className="mt-2 space-y-1 px-4 text-xs">
            <div className="flex items-center gap-8">
              <span className="w-20 text-right">회사부담분</span>
              <span className="w-32 text-right">{Math.round((totals.healthIns + totals.pension + totals.employmentIns) * 0.5).toLocaleString()}</span>
            </div>
            <div className="flex items-center gap-8">
              <span className="w-20 text-right">총 납부액</span>
              <span className="w-32 text-right">{totals.deductionTotal.toLocaleString()}</span>
            </div>
            <div className="flex items-center gap-8">
              <span className="w-20 text-right font-medium">금여상출계</span>
              <span className="w-32 text-right font-medium text-blue-600">{totals.netPay.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 메일/비고 섹션 */}
      <div className="border-t bg-gray-50 p-3">
        <div className="flex gap-4">
          <fieldset className="flex-1 rounded border border-gray-400 p-2">
            <legend className="px-2 text-xs text-blue-700">● 메일/비고</legend>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <label className="w-16 text-xs">메일제목:</label>
                <input
                  type="text"
                  value={mailSubject}
                  onChange={(e) => setMailSubject(e.target.value)}
                  className="flex-1 border border-gray-400 px-2 py-1 text-xs"
                />
              </div>
              <div className="flex items-start gap-2">
                <label className="w-16 text-xs">메일본문:</label>
                <textarea
                  value={mailBody}
                  onChange={(e) => setMailBody(e.target.value)}
                  className="h-12 flex-1 resize-none border border-gray-400 p-1 text-xs"
                />
              </div>
              <div className="text-xs text-red-600">
                * 수정시 #을 넣으시면 해당위치에 회사명이 입력되어 전송됩니다.
              </div>
            </div>
          </fieldset>
          <fieldset className="w-80 rounded border border-gray-400 p-2">
            <legend className="px-2 text-xs text-blue-700">비고:</legend>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="h-16 w-full resize-none border border-gray-400 p-1 text-xs"
            />
            <div className="mt-2 flex items-center justify-between">
              <label className="flex items-center gap-1 text-xs">
                <input
                  type="checkbox"
                  checked={printNote}
                  onChange={(e) => setPrintNote(e.target.checked)}
                />
                금여대장 인쇄 시 비고 출력 유무
              </label>
              <button
                onClick={handleSave}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200"
              >
                저 장
              </button>
            </div>
          </fieldset>
        </div>
      </div>

      {/* 하단 상태바 */}
      <div className="flex items-center justify-end border-t bg-gray-100 px-4 py-1 text-sm text-gray-600">
        <span>{filteredEmployees.length}개 항목 선택됨</span>
      </div>

      {/* === 모달들 === */}

      {/* 기초정보등록 모달 */}
      {showBasicInfoModal && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-[450px] rounded-lg border bg-white shadow-xl">
            <div className="flex items-center justify-between border-b bg-blue-600 px-4 py-2">
              <span className="text-sm font-medium text-white">기초정보등록</span>
              <button onClick={() => setShowBasicInfoModal(false)} className="text-white hover:text-gray-200">X</button>
            </div>
            <div className="p-4">
              <div className="mb-4">
                <label className="mb-1 block text-sm font-medium">사원 선택</label>
                <select
                  value={editEmpId || ""}
                  onChange={(e) => {
                    setEditEmpId(e.target.value);
                    const payroll = payrolls.find((p) => p.employeeId === e.target.value);
                    if (payroll) {
                      setEditBaseSalary(payroll.baseSalary);
                      setEditPositionPay(payroll.positionPay);
                    }
                  }}
                  className="w-full rounded border px-3 py-2 text-sm"
                >
                  <option value="">사원 선택</option>
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.employeeNo} - {emp.name} ({emp.position})
                    </option>
                  ))}
                </select>
              </div>
              {editEmpId && (
                <>
                  <div className="mb-3">
                    <label className="mb-1 block text-sm">기본급</label>
                    <input
                      type="number"
                      value={editBaseSalary}
                      onChange={(e) => setEditBaseSalary(parseInt(e.target.value) || 0)}
                      className="w-full rounded border px-3 py-2 text-sm text-right"
                    />
                  </div>
                  <div className="mb-3">
                    <label className="mb-1 block text-sm">직책수당</label>
                    <input
                      type="number"
                      value={editPositionPay}
                      onChange={(e) => setEditPositionPay(parseInt(e.target.value) || 0)}
                      className="w-full rounded border px-3 py-2 text-sm text-right"
                    />
                  </div>
                </>
              )}
            </div>
            <div className="flex justify-end gap-2 border-t px-4 py-3">
              <button
                onClick={handleSaveBasicInfo}
                disabled={!editEmpId}
                className="rounded bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
              >
                저장
              </button>
              <button
                onClick={() => setShowBasicInfoModal(false)}
                className="rounded border px-4 py-1.5 text-sm hover:bg-gray-100"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 급여등록 모달 */}
      {showPayrollRegModal && selectedEmployee && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-[500px] rounded-lg border bg-white shadow-xl">
            <div className="flex items-center justify-between border-b bg-green-600 px-4 py-2">
              <span className="text-sm font-medium text-white">
                급여등록 - {employees.find((e) => e.id === selectedEmployee)?.name}
              </span>
              <button onClick={() => setShowPayrollRegModal(false)} className="text-white hover:text-gray-200">X</button>
            </div>
            <div className="p-4">
              <div className="mb-4 grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-sm">근무일수</label>
                  <input
                    type="number"
                    value={regWorkDays}
                    onChange={(e) => setRegWorkDays(parseInt(e.target.value) || 0)}
                    className="w-full rounded border px-3 py-2 text-sm text-right"
                    min="0" max="31"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm">연장시간</label>
                  <input
                    type="number"
                    value={regOvertimeHours}
                    onChange={(e) => setRegOvertimeHours(parseInt(e.target.value) || 0)}
                    className="w-full rounded border px-3 py-2 text-sm text-right"
                    min="0"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm">야간시간</label>
                  <input
                    type="number"
                    value={regNightHours}
                    onChange={(e) => setRegNightHours(parseInt(e.target.value) || 0)}
                    className="w-full rounded border px-3 py-2 text-sm text-right"
                    min="0"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm">휴일시간</label>
                  <input
                    type="number"
                    value={regHolidayHours}
                    onChange={(e) => setRegHolidayHours(parseInt(e.target.value) || 0)}
                    className="w-full rounded border px-3 py-2 text-sm text-right"
                    min="0"
                  />
                </div>
                <div className="col-span-2">
                  <label className="mb-1 block text-sm">기타지급</label>
                  <input
                    type="number"
                    value={regOtherPay}
                    onChange={(e) => setRegOtherPay(parseInt(e.target.value) || 0)}
                    className="w-full rounded border px-3 py-2 text-sm text-right"
                    min="0"
                  />
                </div>
              </div>
              {/* 실시간 계산 미리보기 */}
              {(() => {
                const preview = getRegPreview();
                if (!preview) return null;
                return (
                  <div className="rounded border bg-gray-50 p-3 text-xs">
                    <p className="mb-2 font-medium">자동 계산 미리보기</p>
                    <div className="grid grid-cols-2 gap-1">
                      <span>연장수당:</span><span className="text-right">{preview.overtimePay.toLocaleString()}</span>
                      <span>야근수당:</span><span className="text-right">{preview.nightPay.toLocaleString()}</span>
                      <span>휴일수당:</span><span className="text-right">{preview.holidayPay.toLocaleString()}</span>
                      <span className="font-medium">과세총액:</span><span className="text-right font-medium">{preview.taxableTotal.toLocaleString()}</span>
                      <span>공제총액:</span><span className="text-right">{preview.deductionTotal.toLocaleString()}</span>
                      <span className="font-medium text-blue-600">차감지급액:</span>
                      <span className="text-right font-medium text-blue-600">{preview.netPay.toLocaleString()}</span>
                    </div>
                  </div>
                );
              })()}
            </div>
            <div className="flex justify-end gap-2 border-t px-4 py-3">
              <button
                onClick={handleSavePayrollReg}
                className="rounded bg-green-600 px-4 py-1.5 text-sm text-white hover:bg-green-700"
              >
                저장
              </button>
              <button
                onClick={() => setShowPayrollRegModal(false)}
                className="rounded border px-4 py-1.5 text-sm hover:bg-gray-100"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 메일전송 모달 */}
      {showMailModal && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-[400px] rounded-lg border bg-white shadow-xl">
            <div className="flex items-center justify-between border-b bg-blue-600 px-4 py-2">
              <span className="text-sm font-medium text-white">급여명세서 메일전송</span>
              <button onClick={() => setShowMailModal(false)} className="text-white hover:text-gray-200">X</button>
            </div>
            <div className="p-4 space-y-3">
              <div>
                <label className="mb-1 block text-sm">메일 제목</label>
                <input
                  type="text"
                  value={mailSubject}
                  onChange={(e) => setMailSubject(e.target.value)}
                  placeholder={`${yearMonth} 급여명세서`}
                  className="w-full rounded border px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm">메일 본문</label>
                <textarea
                  value={mailBody}
                  onChange={(e) => setMailBody(e.target.value)}
                  placeholder="급여명세서를 첨부하여 보내드립니다."
                  className="h-24 w-full resize-none rounded border px-3 py-2 text-sm"
                />
              </div>
              <p className="text-xs text-gray-500">
                {selectedEmployee
                  ? `대상: ${employees.find((e) => e.id === selectedEmployee)?.name}`
                  : `대상: 전체 ${employees.length}명`}
              </p>
            </div>
            <div className="flex justify-end gap-2 border-t px-4 py-3">
              <button
                onClick={handleConfirmMailSend}
                className="rounded bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700"
              >
                전송
              </button>
              <button
                onClick={() => setShowMailModal(false)}
                className="rounded border px-4 py-1.5 text-sm hover:bg-gray-100"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 환경설정 모달 */}
      {showSettingsModal && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-[400px] rounded-lg border bg-white shadow-xl">
            <div className="flex items-center justify-between border-b bg-gray-600 px-4 py-2">
              <span className="text-sm font-medium text-white">4대보험율 설정</span>
              <button onClick={() => setShowSettingsModal(false)} className="text-white hover:text-gray-200">X</button>
            </div>
            <div className="p-4 space-y-3">
              <div>
                <label className="mb-1 block text-sm">건강보험율 (%)</label>
                <input
                  type="number"
                  value={editRates.healthInsRate}
                  onChange={(e) => setEditRates({ ...editRates, healthInsRate: parseFloat(e.target.value) || 0 })}
                  step="0.001"
                  className="w-full rounded border px-3 py-2 text-sm text-right"
                />
                <p className="text-xs text-gray-500 mt-1">기본: 3.545%</p>
              </div>
              <div>
                <label className="mb-1 block text-sm">장기요양보험율 (건강보험의 %)</label>
                <input
                  type="number"
                  value={editRates.longTermCareRate}
                  onChange={(e) => setEditRates({ ...editRates, longTermCareRate: parseFloat(e.target.value) || 0 })}
                  step="0.01"
                  className="w-full rounded border px-3 py-2 text-sm text-right"
                />
                <p className="text-xs text-gray-500 mt-1">기본: 12.81%</p>
              </div>
              <div>
                <label className="mb-1 block text-sm">국민연금율 (%)</label>
                <input
                  type="number"
                  value={editRates.pensionRate}
                  onChange={(e) => setEditRates({ ...editRates, pensionRate: parseFloat(e.target.value) || 0 })}
                  step="0.1"
                  className="w-full rounded border px-3 py-2 text-sm text-right"
                />
                <p className="text-xs text-gray-500 mt-1">기본: 4.5%</p>
              </div>
              <div>
                <label className="mb-1 block text-sm">고용보험율 (%)</label>
                <input
                  type="number"
                  value={editRates.employmentInsRate}
                  onChange={(e) => setEditRates({ ...editRates, employmentInsRate: parseFloat(e.target.value) || 0 })}
                  step="0.1"
                  className="w-full rounded border px-3 py-2 text-sm text-right"
                />
                <p className="text-xs text-gray-500 mt-1">기본: 0.8%</p>
              </div>
            </div>
            <div className="flex justify-end gap-2 border-t px-4 py-3">
              <button
                onClick={handleSaveSettings}
                className="rounded bg-gray-600 px-4 py-1.5 text-sm text-white hover:bg-gray-700"
              >
                저장
              </button>
              <button
                onClick={() => setShowSettingsModal(false)}
                className="rounded border px-4 py-1.5 text-sm hover:bg-gray-100"
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
