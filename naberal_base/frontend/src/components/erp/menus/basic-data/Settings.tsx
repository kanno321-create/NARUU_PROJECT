"use client";

import React, { useState } from "react";

type TabType = "기본설정" | "양식지" | "문자자동전송" | "프린트설정" | "기타" | "급여";

export function Settings() {
  const [activeTab, setActiveTab] = useState<TabType>("기본설정");

  // 기본설정 상태
  const [costMethod, setCostMethod] = useState("총평균법");
  const [showSaveMessage, setShowSaveMessage] = useState(true);
  const [quantityDigits, setQuantityDigits] = useState("2");
  const [quantityMethod, setQuantityMethod] = useState("반올림");
  const [amountDigits, setAmountDigits] = useState("0");
  const [amountMethod, setAmountMethod] = useState("반올림");
  const [autoAlertStock, setAutoAlertStock] = useState(true);
  const [autoAlertReceivable, setAutoAlertReceivable] = useState(true);
  const [autoAlertPayable, setAutoAlertPayable] = useState(true);
  const [autoAlertBill, setAutoAlertBill] = useState(false);
  const [businessPath, setBusinessPath] = useState("C:\\EasyPanme\\Data\\");

  // 양식지 상태
  const [formType, setFormType] = useState("기본양식");
  const [headerText, setHeaderText] = useState("");
  const [footerText, setFooterText] = useState("");
  const [showLogo, setShowLogo] = useState(true);
  const [logoPath, setLogoPath] = useState("");

  // 문자자동전송 상태
  const [smsEnabled, setSmsEnabled] = useState(false);
  const [smsApiKey, setSmsApiKey] = useState("");
  const [smsSenderId, setSmsSenderId] = useState("");
  const [smsOnSale, setSmsOnSale] = useState(false);
  const [smsOnPurchase, setSmsOnPurchase] = useState(false);
  const [smsOnPayment, setSmsOnPayment] = useState(false);

  // 프린트설정 상태
  const [defaultPrinter, setDefaultPrinter] = useState("기본 프린터");
  const [printPreview, setPrintPreview] = useState(true);
  const [copies, setCopies] = useState("1");
  const [paperSize, setPaperSize] = useState("A4");
  const [orientation, setOrientation] = useState("세로");

  // 기타 상태
  const [autoBackup, setAutoBackup] = useState(true);
  const [backupPath, setBackupPath] = useState("C:\\EasyPanme\\Backup\\");
  const [backupCycle, setBackupCycle] = useState("매일");
  const [autoUpdate, setAutoUpdate] = useState(true);
  const [showStartupTip, setShowStartupTip] = useState(false);
  const [confirmOnExit, setConfirmOnExit] = useState(true);

  // 급여 상태
  const [payDay, setPayDay] = useState("25");
  const [taxMethod, setTaxMethod] = useState("간이세액");
  const [insuranceRate, setInsuranceRate] = useState("3.545");
  const [pensionRate, setPensionRate] = useState("4.5");
  const [healthRate, setHealthRate] = useState("3.545");
  const [employmentRate, setEmploymentRate] = useState("0.9");

  const tabs: TabType[] = ["기본설정", "양식지", "문자자동전송", "프린트설정", "기타", "급여"];

  const handleSave = () => {
    alert("환경설정이 저장되었습니다.");
  };

  const handleCancel = () => {
    if (confirm("변경사항을 취소하시겠습니까?")) {
      // 초기값으로 복원
    }
  };

  const renderBasicSettings = () => (
    <div className="space-y-4">
      {/* 기본환경설정 */}
      <fieldset className="rounded border border-gray-400 p-3">
        <legend className="px-2 text-xs font-medium text-blue-700">기본환경설정</legend>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="w-32 text-xs">원가 계산 방법:</span>
            <select
              value={costMethod}
              onChange={(e) => setCostMethod(e.target.value)}
              className="rounded border border-gray-400 px-2 py-1 text-xs"
            >
              <option value="총평균법">총평균법</option>
              <option value="이동평균법">이동평균법</option>
              <option value="선입선출법">선입선출법</option>
              <option value="후입선출법">후입선출법</option>
            </select>
          </div>
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={showSaveMessage}
              onChange={(e) => setShowSaveMessage(e.target.checked)}
            />
            저장하지 않을 경우 메세지 표시
          </label>
        </div>
      </fieldset>

      {/* 소수처리방법설정 */}
      <fieldset className="rounded border border-gray-400 p-3">
        <legend className="px-2 text-xs font-medium text-blue-700">소수처리방법설정</legend>
        <div className="space-y-2">
          <div className="flex items-center gap-4">
            <span className="w-20 text-xs">수량:</span>
            <select
              value={quantityDigits}
              onChange={(e) => setQuantityDigits(e.target.value)}
              className="w-16 rounded border border-gray-400 px-2 py-1 text-xs"
            >
              <option value="0">0</option>
              <option value="1">1</option>
              <option value="2">2</option>
              <option value="3">3</option>
            </select>
            <span className="text-xs">자리수</span>
            <select
              value={quantityMethod}
              onChange={(e) => setQuantityMethod(e.target.value)}
              className="rounded border border-gray-400 px-2 py-1 text-xs"
            >
              <option value="반올림">반올림</option>
              <option value="올림">올림</option>
              <option value="버림">버림</option>
            </select>
          </div>
          <div className="flex items-center gap-4">
            <span className="w-20 text-xs">금액:</span>
            <select
              value={amountDigits}
              onChange={(e) => setAmountDigits(e.target.value)}
              className="w-16 rounded border border-gray-400 px-2 py-1 text-xs"
            >
              <option value="0">0</option>
              <option value="1">1</option>
              <option value="2">2</option>
              <option value="3">3</option>
            </select>
            <span className="text-xs">자리수</span>
            <select
              value={amountMethod}
              onChange={(e) => setAmountMethod(e.target.value)}
              className="rounded border border-gray-400 px-2 py-1 text-xs"
            >
              <option value="반올림">반올림</option>
              <option value="올림">올림</option>
              <option value="버림">버림</option>
            </select>
          </div>
        </div>
      </fieldset>

      {/* 자동 알림 기능 */}
      <fieldset className="rounded border border-gray-400 p-3">
        <legend className="px-2 text-xs font-medium text-blue-700">자동 알림 기능</legend>
        <div className="grid grid-cols-2 gap-2">
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={autoAlertStock}
              onChange={(e) => setAutoAlertStock(e.target.checked)}
            />
            재고 부족 알림
          </label>
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={autoAlertReceivable}
              onChange={(e) => setAutoAlertReceivable(e.target.checked)}
            />
            미수금 초과 알림
          </label>
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={autoAlertPayable}
              onChange={(e) => setAutoAlertPayable(e.target.checked)}
            />
            미지급금 초과 알림
          </label>
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={autoAlertBill}
              onChange={(e) => setAutoAlertBill(e.target.checked)}
            />
            어음 만기일 알림
          </label>
        </div>
      </fieldset>

      {/* 사업장 경로 */}
      <fieldset className="rounded border border-gray-400 p-3">
        <legend className="px-2 text-xs font-medium text-blue-700">사업장 선택</legend>
        <div className="flex items-center gap-2">
          <span className="text-xs">데이터 경로:</span>
          <input
            type="text"
            value={businessPath}
            onChange={(e) => setBusinessPath(e.target.value)}
            className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
          />
          <button className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-xs hover:bg-gray-200">
            찾기...
          </button>
        </div>
      </fieldset>
    </div>
  );

  const renderFormSettings = () => (
    <div className="space-y-4">
      <fieldset className="rounded border border-gray-400 p-3">
        <legend className="px-2 text-xs font-medium text-blue-700">양식지 설정</legend>
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="w-24 text-xs">양식 종류:</span>
            <select
              value={formType}
              onChange={(e) => setFormType(e.target.value)}
              className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
            >
              <option value="기본양식">기본양식</option>
              <option value="간이양식">간이양식</option>
              <option value="상세양식">상세양식</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-24 text-xs">머리글:</span>
            <input
              type="text"
              value={headerText}
              onChange={(e) => setHeaderText(e.target.value)}
              className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
              placeholder="문서 상단에 표시할 텍스트"
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="w-24 text-xs">꼬리글:</span>
            <input
              type="text"
              value={footerText}
              onChange={(e) => setFooterText(e.target.value)}
              className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
              placeholder="문서 하단에 표시할 텍스트"
            />
          </div>
        </div>
      </fieldset>

      <fieldset className="rounded border border-gray-400 p-3">
        <legend className="px-2 text-xs font-medium text-blue-700">로고 설정</legend>
        <div className="space-y-3">
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={showLogo}
              onChange={(e) => setShowLogo(e.target.checked)}
            />
            로고 표시
          </label>
          <div className="flex items-center gap-2">
            <span className="w-24 text-xs">로고 파일:</span>
            <input
              type="text"
              value={logoPath}
              onChange={(e) => setLogoPath(e.target.value)}
              className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
              disabled={!showLogo}
            />
            <button
              className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-xs hover:bg-gray-200 disabled:opacity-50"
              disabled={!showLogo}
            >
              찾기...
            </button>
          </div>
        </div>
      </fieldset>
    </div>
  );

  const renderSmsSettings = () => (
    <div className="space-y-4">
      <fieldset className="rounded border border-gray-400 p-3">
        <legend className="px-2 text-xs font-medium text-blue-700">문자 서비스 설정</legend>
        <div className="space-y-3">
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={smsEnabled}
              onChange={(e) => setSmsEnabled(e.target.checked)}
            />
            문자 자동전송 사용
          </label>
          <div className="flex items-center gap-2">
            <span className="w-24 text-xs">API Key:</span>
            <input
              type="password"
              value={smsApiKey}
              onChange={(e) => setSmsApiKey(e.target.value)}
              className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
              disabled={!smsEnabled}
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="w-24 text-xs">발신번호:</span>
            <input
              type="text"
              value={smsSenderId}
              onChange={(e) => setSmsSenderId(e.target.value)}
              className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
              placeholder="010-0000-0000"
              disabled={!smsEnabled}
            />
          </div>
        </div>
      </fieldset>

      <fieldset className="rounded border border-gray-400 p-3">
        <legend className="px-2 text-xs font-medium text-blue-700">자동전송 시점</legend>
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={smsOnSale}
              onChange={(e) => setSmsOnSale(e.target.checked)}
              disabled={!smsEnabled}
            />
            매출 등록 시
          </label>
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={smsOnPurchase}
              onChange={(e) => setSmsOnPurchase(e.target.checked)}
              disabled={!smsEnabled}
            />
            매입 등록 시
          </label>
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={smsOnPayment}
              onChange={(e) => setSmsOnPayment(e.target.checked)}
              disabled={!smsEnabled}
            />
            수금/지급 완료 시
          </label>
        </div>
      </fieldset>
    </div>
  );

  const renderPrintSettings = () => (
    <div className="space-y-4">
      <fieldset className="rounded border border-gray-400 p-3">
        <legend className="px-2 text-xs font-medium text-blue-700">프린터 설정</legend>
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="w-24 text-xs">기본 프린터:</span>
            <select
              value={defaultPrinter}
              onChange={(e) => setDefaultPrinter(e.target.value)}
              className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
            >
              <option value="기본 프린터">기본 프린터</option>
              <option value="Microsoft Print to PDF">Microsoft Print to PDF</option>
              <option value="OneNote">OneNote</option>
            </select>
          </div>
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={printPreview}
              onChange={(e) => setPrintPreview(e.target.checked)}
            />
            인쇄 전 미리보기 표시
          </label>
          <div className="flex items-center gap-2">
            <span className="w-24 text-xs">인쇄 매수:</span>
            <input
              type="number"
              value={copies}
              onChange={(e) => setCopies(e.target.value)}
              className="w-20 rounded border border-gray-400 px-2 py-1 text-xs"
              min="1"
              max="99"
            />
            <span className="text-xs">부</span>
          </div>
        </div>
      </fieldset>

      <fieldset className="rounded border border-gray-400 p-3">
        <legend className="px-2 text-xs font-medium text-blue-700">용지 설정</legend>
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="w-24 text-xs">용지 크기:</span>
            <select
              value={paperSize}
              onChange={(e) => setPaperSize(e.target.value)}
              className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
            >
              <option value="A4">A4 (210 x 297 mm)</option>
              <option value="A5">A5 (148 x 210 mm)</option>
              <option value="B5">B5 (182 x 257 mm)</option>
              <option value="Letter">Letter (216 x 279 mm)</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-24 text-xs">인쇄 방향:</span>
            <label className="flex items-center gap-1 text-xs">
              <input
                type="radio"
                name="orientation"
                value="세로"
                checked={orientation === "세로"}
                onChange={(e) => setOrientation(e.target.value)}
              />
              세로
            </label>
            <label className="flex items-center gap-1 text-xs">
              <input
                type="radio"
                name="orientation"
                value="가로"
                checked={orientation === "가로"}
                onChange={(e) => setOrientation(e.target.value)}
              />
              가로
            </label>
          </div>
        </div>
      </fieldset>
    </div>
  );

  const renderOtherSettings = () => (
    <div className="space-y-4">
      <fieldset className="rounded border border-gray-400 p-3">
        <legend className="px-2 text-xs font-medium text-blue-700">백업 설정</legend>
        <div className="space-y-3">
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={autoBackup}
              onChange={(e) => setAutoBackup(e.target.checked)}
            />
            자동 백업 사용
          </label>
          <div className="flex items-center gap-2">
            <span className="w-24 text-xs">백업 경로:</span>
            <input
              type="text"
              value={backupPath}
              onChange={(e) => setBackupPath(e.target.value)}
              className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
              disabled={!autoBackup}
            />
            <button
              className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-xs hover:bg-gray-200 disabled:opacity-50"
              disabled={!autoBackup}
            >
              찾기...
            </button>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-24 text-xs">백업 주기:</span>
            <select
              value={backupCycle}
              onChange={(e) => setBackupCycle(e.target.value)}
              className="rounded border border-gray-400 px-2 py-1 text-xs"
              disabled={!autoBackup}
            >
              <option value="매일">매일</option>
              <option value="매주">매주</option>
              <option value="매월">매월</option>
            </select>
          </div>
        </div>
      </fieldset>

      <fieldset className="rounded border border-gray-400 p-3">
        <legend className="px-2 text-xs font-medium text-blue-700">프로그램 설정</legend>
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={autoUpdate}
              onChange={(e) => setAutoUpdate(e.target.checked)}
            />
            자동 업데이트 확인
          </label>
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={showStartupTip}
              onChange={(e) => setShowStartupTip(e.target.checked)}
            />
            시작 시 오늘의 팁 표시
          </label>
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={confirmOnExit}
              onChange={(e) => setConfirmOnExit(e.target.checked)}
            />
            종료 시 확인 메시지 표시
          </label>
        </div>
      </fieldset>
    </div>
  );

  const renderPayrollSettings = () => (
    <div className="space-y-4">
      <fieldset className="rounded border border-gray-400 p-3">
        <legend className="px-2 text-xs font-medium text-blue-700">급여 기본설정</legend>
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="w-24 text-xs">급여 지급일:</span>
            <select
              value={payDay}
              onChange={(e) => setPayDay(e.target.value)}
              className="w-20 rounded border border-gray-400 px-2 py-1 text-xs"
            >
              {Array.from({ length: 28 }, (_, i) => (
                <option key={i + 1} value={String(i + 1)}>
                  {i + 1}
                </option>
              ))}
            </select>
            <span className="text-xs">일</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-24 text-xs">세금 계산:</span>
            <select
              value={taxMethod}
              onChange={(e) => setTaxMethod(e.target.value)}
              className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
            >
              <option value="간이세액">간이세액표</option>
              <option value="원천징수">원천징수</option>
            </select>
          </div>
        </div>
      </fieldset>

      <fieldset className="rounded border border-gray-400 p-3">
        <legend className="px-2 text-xs font-medium text-blue-700">4대보험 요율 설정</legend>
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="w-32 text-xs">국민연금:</span>
            <input
              type="text"
              value={pensionRate}
              onChange={(e) => setPensionRate(e.target.value)}
              className="w-20 rounded border border-gray-400 px-2 py-1 text-xs text-right"
            />
            <span className="text-xs">%</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-32 text-xs">건강보험:</span>
            <input
              type="text"
              value={healthRate}
              onChange={(e) => setHealthRate(e.target.value)}
              className="w-20 rounded border border-gray-400 px-2 py-1 text-xs text-right"
            />
            <span className="text-xs">%</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-32 text-xs">장기요양보험:</span>
            <input
              type="text"
              value={insuranceRate}
              onChange={(e) => setInsuranceRate(e.target.value)}
              className="w-20 rounded border border-gray-400 px-2 py-1 text-xs text-right"
            />
            <span className="text-xs">%</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-32 text-xs">고용보험:</span>
            <input
              type="text"
              value={employmentRate}
              onChange={(e) => setEmploymentRate(e.target.value)}
              className="w-20 rounded border border-gray-400 px-2 py-1 text-xs text-right"
            />
            <span className="text-xs">%</span>
          </div>
        </div>
        <p className="mt-2 text-xs text-gray-500">
          * 2025년 기준 요율입니다. 변경 시 정확한 요율을 확인하세요.
        </p>
      </fieldset>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case "기본설정":
        return renderBasicSettings();
      case "양식지":
        return renderFormSettings();
      case "문자자동전송":
        return renderSmsSettings();
      case "프린트설정":
        return renderPrintSettings();
      case "기타":
        return renderOtherSettings();
      case "급여":
        return renderPayrollSettings();
      default:
        return null;
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">환경설정</span>
      </div>

      {/* 탭 */}
      <div className="flex border-b bg-gray-200">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-xs font-medium ${
              activeTab === tab
                ? "border-b-2 border-blue-600 bg-white text-blue-600"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* 내용 */}
      <div className="flex-1 overflow-auto p-4">
        {renderTabContent()}
      </div>

      {/* 하단 버튼 */}
      <div className="flex justify-end gap-2 border-t bg-gray-100 px-4 py-2">
        <button
          onClick={handleSave}
          className="rounded border border-gray-400 bg-gray-100 px-6 py-1.5 text-sm hover:bg-gray-200"
        >
          저 장(S)
        </button>
        <button
          onClick={handleCancel}
          className="rounded border border-gray-400 bg-gray-100 px-6 py-1.5 text-sm hover:bg-gray-200"
        >
          취소(Esc)
        </button>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        loading ok
      </div>
    </div>
  );
}
