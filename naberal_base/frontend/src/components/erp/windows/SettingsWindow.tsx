"use client";

import React, { useState } from "react";

type SettingsTab = "기본설정" | "양식지" | "문자자동전송" | "프린트설정" | "기타" | "급여";

export function SettingsWindow() {
  const [activeTab, setActiveTab] = useState<SettingsTab>("기본설정");

  // 기본설정 states
  const [costMethod, setCostMethod] = useState("선입선출법");
  const [saveMessage, setSaveMessage] = useState("메세지 표시하지 않음");
  const [quantityDigits, setQuantityDigits] = useState("0");
  const [quantityMethod, setQuantityMethod] = useState("지정자리이하올림");
  const [amountDigits, setAmountDigits] = useState("0");
  const [amountMethod, setAmountMethod] = useState("지정자리이하올림");
  const [stockAlert, setStockAlert] = useState(false);
  const [limitAlert, setLimitAlert] = useState(false);
  const [dataPath, setDataPath] = useState("C:\\Weasypanme2015_standard\\WData");
  const [calcCostOnSale, setCalcCostOnSale] = useState(true);
  const [defaultVat, setDefaultVat] = useState("부가세별도");
  const [includeTaxInProfit, setIncludeTaxInProfit] = useState(true);
  const [autoBackup, setAutoBackup] = useState(true);
  const [exitConfirm, setExitConfirm] = useState(true);

  // 양식지 states
  const [formType, setFormType] = useState("기본양식");
  const [showLogo, setShowLogo] = useState(true);
  const [logoPath, setLogoPath] = useState("");

  // 문자자동전송 states
  const [autoSmsOnSale, setAutoSmsOnSale] = useState(false);
  const [autoSmsOnPurchase, setAutoSmsOnPurchase] = useState(false);
  const [smsTemplate, setSmsTemplate] = useState("");

  // 프린트설정 states
  const [defaultPrinter, setDefaultPrinter] = useState("기본 프린터");
  const [printCopies, setPrintCopies] = useState("1");
  const [showPreview, setShowPreview] = useState(true);

  // 기타 states
  const [autoUpdate, setAutoUpdate] = useState(true);
  const [startWithWindows, setStartWithWindows] = useState(false);

  // 급여 states
  const [payDay, setPayDay] = useState("25");
  const [includeWeekend, setIncludeWeekend] = useState(false);

  const handleSave = () => {
    alert("설정이 저장되었습니다.");
  };

  const tabs: SettingsTab[] = ["기본설정", "양식지", "문자자동전송", "프린트설정", "기타", "급여"];

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">환경설정</span>
      </div>

      {/* 탭 */}
      <div className="flex border-b bg-[#F0EDE4]">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm ${
              activeTab === tab
                ? "border-b-2 border-blue-600 bg-white font-medium"
                : "hover:bg-gray-200"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* 탭 컨텐츠 */}
      <div className="flex-1 overflow-auto p-4">
        {activeTab === "기본설정" && (
          <div className="space-y-4">
            {/* 기본환경설정 */}
            <fieldset className="rounded border border-gray-400 p-3">
              <legend className="px-2 text-sm text-blue-700">기본환경설정</legend>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="w-40 text-sm">원가 계산 방법:</span>
                  <select
                    value={costMethod}
                    onChange={(e) => setCostMethod(e.target.value)}
                    className="w-48 rounded border border-gray-400 px-2 py-1 text-sm"
                  >
                    <option value="선입선출법">선입선출법</option>
                    <option value="후입선출법">후입선출법</option>
                    <option value="이동평균법">이동평균법</option>
                    <option value="총평균법">총평균법</option>
                  </select>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-40 text-sm">저장하지 않을 경우<br/>메세지 표시:</span>
                  <select
                    value={saveMessage}
                    onChange={(e) => setSaveMessage(e.target.value)}
                    className="w-48 rounded border border-gray-400 px-2 py-1 text-sm"
                  >
                    <option value="메세지 표시하지 않음">메세지 표시하지 않음</option>
                    <option value="메세지 표시">메세지 표시</option>
                  </select>
                </div>
              </div>
            </fieldset>

            {/* 소수처리방법설정 */}
            <fieldset className="rounded border border-gray-400 p-3">
              <legend className="px-2 text-sm text-blue-700">소수처리방법설정</legend>
              <div className="mb-2 flex items-center gap-8 text-sm">
                <span className="w-20"></span>
                <span className="w-16">자리수</span>
                <span>자리수 이하 처리방법</span>
              </div>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="w-20 text-sm">수량:</span>
                  <select
                    value={quantityDigits}
                    onChange={(e) => setQuantityDigits(e.target.value)}
                    className="w-16 rounded border border-gray-400 px-2 py-1 text-sm"
                  >
                    <option value="0">0</option>
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                  </select>
                  <select
                    value={quantityMethod}
                    onChange={(e) => setQuantityMethod(e.target.value)}
                    className="w-40 rounded border border-gray-400 px-2 py-1 text-sm"
                  >
                    <option value="지정자리이하올림">지정자리이하올림</option>
                    <option value="지정자리이하버림">지정자리이하버림</option>
                    <option value="지정자리이하반올림">지정자리이하반올림</option>
                  </select>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-20 text-sm">금액:</span>
                  <select
                    value={amountDigits}
                    onChange={(e) => setAmountDigits(e.target.value)}
                    className="w-16 rounded border border-gray-400 px-2 py-1 text-sm"
                  >
                    <option value="0">0</option>
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                  </select>
                  <select
                    value={amountMethod}
                    onChange={(e) => setAmountMethod(e.target.value)}
                    className="w-40 rounded border border-gray-400 px-2 py-1 text-sm"
                  >
                    <option value="지정자리이하올림">지정자리이하올림</option>
                    <option value="지정자리이하버림">지정자리이하버림</option>
                    <option value="지정자리이하반올림">지정자리이하반올림</option>
                  </select>
                </div>
              </div>
            </fieldset>

            {/* 자동 알림 기능 */}
            <fieldset className="rounded border border-gray-400 p-3">
              <legend className="px-2 text-sm text-blue-700">자동 알림 기능</legend>
              <div className="flex gap-8">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={stockAlert}
                    onChange={(e) => setStockAlert(e.target.checked)}
                  />
                  재고 부족시 알림
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={limitAlert}
                    onChange={(e) => setLimitAlert(e.target.checked)}
                  />
                  한도액 초과시 알림
                </label>
              </div>
            </fieldset>

            {/* 사업장 선택 */}
            <fieldset className="rounded border border-gray-400 p-3">
              <legend className="px-2 text-sm text-blue-700">사업장 선택</legend>
              <div className="flex items-center gap-2">
                <span className="text-sm">경로:</span>
                <input
                  type="text"
                  value={dataPath}
                  onChange={(e) => setDataPath(e.target.value)}
                  className="flex-1 rounded border border-gray-400 px-2 py-1 text-sm"
                />
                <button className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
                  검색
                </button>
              </div>
            </fieldset>

            {/* 원가계산 옵션 */}
            <div className="rounded border border-blue-400 bg-blue-50 p-3">
              <label className="flex items-center gap-2 text-sm font-medium">
                <input
                  type="radio"
                  checked={calcCostOnSale}
                  onChange={() => setCalcCostOnSale(true)}
                />
                매출전표작성시 원가계산
              </label>
              <div className="ml-6 mt-1 text-xs text-blue-700">
                • 매출전표 작성시 속도가 느릴경우 체크를 해제하시면 속도가 빨라집니다.<br/>
                • 체크해제시 원가관련 보고서를 확인하기 전에 원가재계산을 실행해주시면 됩니다.
              </div>
            </div>

            {/* 부가세처리 */}
            <div className="flex items-center gap-2">
              <span className="text-sm">매출매입처리시 기본 부가세처리:</span>
              <select
                value={defaultVat}
                onChange={(e) => setDefaultVat(e.target.value)}
                className="w-32 rounded border border-gray-400 px-2 py-1 text-sm"
              >
                <option value="부가세별도">부가세별도</option>
                <option value="부가세포함">부가세포함</option>
              </select>
            </div>

            {/* 추가 옵션 */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={includeTaxInProfit}
                  onChange={(e) => setIncludeTaxInProfit(e.target.checked)}
                />
                매입/매출이익 계산시 세액 포함
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={autoBackup}
                  onChange={(e) => setAutoBackup(e.target.checked)}
                />
                프로그램 종료시 자동으로 백업하기
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={exitConfirm}
                  onChange={(e) => setExitConfirm(e.target.checked)}
                />
                프로그램 종료시 확인창 표시
              </label>
            </div>
          </div>
        )}

        {activeTab === "양식지" && (
          <div className="space-y-4">
            <fieldset className="rounded border border-gray-400 p-3">
              <legend className="px-2 text-sm text-blue-700">양식지 설정</legend>
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="w-24 text-sm">양식 종류:</span>
                  <select
                    value={formType}
                    onChange={(e) => setFormType(e.target.value)}
                    className="w-48 rounded border border-gray-400 px-2 py-1 text-sm"
                  >
                    <option value="기본양식">기본양식</option>
                    <option value="간편양식">간편양식</option>
                    <option value="세금계산서양식">세금계산서양식</option>
                  </select>
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={showLogo}
                    onChange={(e) => setShowLogo(e.target.checked)}
                  />
                  로고 표시
                </label>
                <div className="flex items-center gap-2">
                  <span className="w-24 text-sm">로고 경로:</span>
                  <input
                    type="text"
                    value={logoPath}
                    onChange={(e) => setLogoPath(e.target.value)}
                    className="flex-1 rounded border border-gray-400 px-2 py-1 text-sm"
                    disabled={!showLogo}
                  />
                  <button
                    className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
                    disabled={!showLogo}
                  >
                    찾기
                  </button>
                </div>
              </div>
            </fieldset>
          </div>
        )}

        {activeTab === "문자자동전송" && (
          <div className="space-y-4">
            <fieldset className="rounded border border-gray-400 p-3">
              <legend className="px-2 text-sm text-blue-700">자동 문자 발송 설정</legend>
              <div className="space-y-3">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={autoSmsOnSale}
                    onChange={(e) => setAutoSmsOnSale(e.target.checked)}
                  />
                  매출전표 작성시 자동 문자발송
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={autoSmsOnPurchase}
                    onChange={(e) => setAutoSmsOnPurchase(e.target.checked)}
                  />
                  매입전표 작성시 자동 문자발송
                </label>
                <div>
                  <span className="text-sm">문자 템플릿:</span>
                  <textarea
                    value={smsTemplate}
                    onChange={(e) => setSmsTemplate(e.target.value)}
                    className="mt-1 h-24 w-full rounded border border-gray-400 p-2 text-sm"
                    placeholder="[거래처명]님, 거래내역이 등록되었습니다."
                  />
                  <div className="mt-1 text-xs text-gray-500">
                    사용 가능 변수: [거래처명], [금액], [날짜], [담당자]
                  </div>
                </div>
              </div>
            </fieldset>
          </div>
        )}

        {activeTab === "프린트설정" && (
          <div className="space-y-4">
            <fieldset className="rounded border border-gray-400 p-3">
              <legend className="px-2 text-sm text-blue-700">프린터 설정</legend>
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="w-24 text-sm">기본 프린터:</span>
                  <select
                    value={defaultPrinter}
                    onChange={(e) => setDefaultPrinter(e.target.value)}
                    className="w-48 rounded border border-gray-400 px-2 py-1 text-sm"
                  >
                    <option value="기본 프린터">기본 프린터</option>
                    <option value="PDF 프린터">PDF 프린터</option>
                  </select>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-24 text-sm">인쇄 매수:</span>
                  <select
                    value={printCopies}
                    onChange={(e) => setPrintCopies(e.target.value)}
                    className="w-20 rounded border border-gray-400 px-2 py-1 text-sm"
                  >
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                  </select>
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={showPreview}
                    onChange={(e) => setShowPreview(e.target.checked)}
                  />
                  인쇄 전 미리보기 표시
                </label>
              </div>
            </fieldset>
          </div>
        )}

        {activeTab === "기타" && (
          <div className="space-y-4">
            <fieldset className="rounded border border-gray-400 p-3">
              <legend className="px-2 text-sm text-blue-700">기타 설정</legend>
              <div className="space-y-3">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={autoUpdate}
                    onChange={(e) => setAutoUpdate(e.target.checked)}
                  />
                  자동 업데이트 확인
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={startWithWindows}
                    onChange={(e) => setStartWithWindows(e.target.checked)}
                  />
                  윈도우 시작시 자동 실행
                </label>
              </div>
            </fieldset>
          </div>
        )}

        {activeTab === "급여" && (
          <div className="space-y-4">
            <fieldset className="rounded border border-gray-400 p-3">
              <legend className="px-2 text-sm text-blue-700">급여 설정</legend>
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="w-24 text-sm">급여일:</span>
                  <select
                    value={payDay}
                    onChange={(e) => setPayDay(e.target.value)}
                    className="w-20 rounded border border-gray-400 px-2 py-1 text-sm"
                  >
                    {Array.from({ length: 31 }, (_, i) => (
                      <option key={i + 1} value={String(i + 1)}>
                        {i + 1}일
                      </option>
                    ))}
                  </select>
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={includeWeekend}
                    onChange={(e) => setIncludeWeekend(e.target.checked)}
                  />
                  주말 포함 근무일수 계산
                </label>
              </div>
            </fieldset>
          </div>
        )}
      </div>

      {/* 하단 버튼 */}
      <div className="flex justify-end gap-2 border-t bg-gray-200 px-4 py-2">
        <button
          onClick={handleSave}
          className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
        >
          저 장
        </button>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200">
          취 소
        </button>
      </div>
    </div>
  );
}
