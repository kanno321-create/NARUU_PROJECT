"use client";

import React, { useState } from "react";

interface TaxInvoiceSummaryItem {
  id: string;
  partnerCode: string;
  partnerName: string;
  businessNo: string;
  representative: string;
  address: string;
  businessType: string;
  businessItem: string;
  salesSupply: number;
  salesTax: number;
  salesTotal: number;
  salesCount: number;
  purchaseSupply: number;
  purchaseTax: number;
  purchaseTotal: number;
  purchaseCount: number;
}

// 이지판매재고관리 원본 데이터 복제
const ORIGINAL_DATA: TaxInvoiceSummaryItem[] = [
  {
    id: "1",
    partnerCode: "C001",
    partnerName: "테스트전자",
    businessNo: "123-45-67890",
    representative: "김대표",
    address: "서울시 강남구 테헤란로 123",
    businessType: "제조업",
    businessItem: "전자부품",
    salesSupply: 25000000,
    salesTax: 2500000,
    salesTotal: 27500000,
    salesCount: 5,
    purchaseSupply: 0,
    purchaseTax: 0,
    purchaseTotal: 0,
    purchaseCount: 0,
  },
  {
    id: "2",
    partnerCode: "C002",
    partnerName: "제고상사",
    businessNo: "234-56-78901",
    representative: "이사장",
    address: "서울시 서초구 서초대로 456",
    businessType: "도소매업",
    businessItem: "전자제품",
    salesSupply: 18000000,
    salesTax: 1800000,
    salesTotal: 19800000,
    salesCount: 3,
    purchaseSupply: 0,
    purchaseTax: 0,
    purchaseTotal: 0,
    purchaseCount: 0,
  },
  {
    id: "3",
    partnerCode: "S001",
    partnerName: "공급업체A",
    businessNo: "111-22-33333",
    representative: "박공급",
    address: "경기도 성남시 분당구 판교로 789",
    businessType: "제조업",
    businessItem: "반도체부품",
    salesSupply: 0,
    salesTax: 0,
    salesTotal: 0,
    salesCount: 0,
    purchaseSupply: 32000000,
    purchaseTax: 3200000,
    purchaseTotal: 35200000,
    purchaseCount: 8,
  },
  {
    id: "4",
    partnerCode: "S002",
    partnerName: "공급업체B",
    businessNo: "222-33-44444",
    representative: "최공급",
    address: "인천시 연수구 송도대로 321",
    businessType: "도소매업",
    businessItem: "케이블",
    salesSupply: 0,
    salesTax: 0,
    salesTotal: 0,
    salesCount: 0,
    purchaseSupply: 15000000,
    purchaseTax: 1500000,
    purchaseTotal: 16500000,
    purchaseCount: 4,
  },
  {
    id: "5",
    partnerCode: "C003",
    partnerName: "신규산업",
    businessNo: "345-67-89012",
    representative: "정신규",
    address: "대전시 유성구 테크노로 654",
    businessType: "제조업",
    businessItem: "산업용품",
    salesSupply: 12000000,
    salesTax: 1200000,
    salesTotal: 13200000,
    salesCount: 2,
    purchaseSupply: 5000000,
    purchaseTax: 500000,
    purchaseTotal: 5500000,
    purchaseCount: 1,
  },
];

export function TaxInvoiceSummary() {
  const [year, setYear] = useState("2024");
  const [quarter, setQuarter] = useState("4");
  const [typeFilter, setTypeFilter] = useState("전체");
  const [partnerFilter, setPartnerFilter] = useState("");
  const [data] = useState<TaxInvoiceSummaryItem[]>(ORIGINAL_DATA);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredData = data.filter(
    (item) =>
      (partnerFilter === "" || item.partnerName.includes(partnerFilter)) &&
      (typeFilter === "전체" ||
        (typeFilter === "매출" && item.salesTotal > 0) ||
        (typeFilter === "매입" && item.purchaseTotal > 0))
  );

  // 총계 계산
  const totals = filteredData.reduce(
    (acc, item) => ({
      salesSupply: acc.salesSupply + item.salesSupply,
      salesTax: acc.salesTax + item.salesTax,
      salesTotal: acc.salesTotal + item.salesTotal,
      salesCount: acc.salesCount + item.salesCount,
      purchaseSupply: acc.purchaseSupply + item.purchaseSupply,
      purchaseTax: acc.purchaseTax + item.purchaseTax,
      purchaseTotal: acc.purchaseTotal + item.purchaseTotal,
      purchaseCount: acc.purchaseCount + item.purchaseCount,
    }),
    {
      salesSupply: 0, salesTax: 0, salesTotal: 0, salesCount: 0,
      purchaseSupply: 0, purchaseTax: 0, purchaseTotal: 0, purchaseCount: 0
    }
  );

  // 거래처 수 집계
  const salesPartners = filteredData.filter(d => d.salesTotal > 0).length;
  const purchasePartners = filteredData.filter(d => d.purchaseTotal > 0).length;

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">세금계산서합계표</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📊</span> 합계표출력
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 엑셀변환
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🖨️</span> 인쇄
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-blue-100 px-2 py-0.5 text-xs hover:bg-blue-200">
          <span>📤</span> 국세청 전자제출
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
          <span className="text-xs">분기:</span>
          <select
            value={quarter}
            onChange={(e) => setQuarter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="1">1분기 (1~3월)</option>
            <option value="2">2분기 (4~6월)</option>
            <option value="3">3분기 (7~9월)</option>
            <option value="4">4분기 (10~12월)</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">구분:</span>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          >
            <option value="전체">전체</option>
            <option value="매출">매출</option>
            <option value="매입">매입</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">거래처:</span>
          <input
            type="text"
            value={partnerFilter}
            onChange={(e) => setPartnerFilter(e.target.value)}
            placeholder="거래처명"
            className="rounded border border-gray-400 px-2 py-1 text-xs w-32"
          />
        </div>
        <button className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200">
          검 색(F)
        </button>
      </div>

      {/* 요약 정보 */}
      <div className="grid grid-cols-2 gap-4 border-b bg-yellow-50 px-3 py-2">
        {/* 매출 합계 */}
        <div className="bg-white p-3 rounded border">
          <div className="text-sm font-medium text-blue-700 border-b pb-1 mb-2">▶ 매출처별 세금계산서 합계</div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div>
              <div className="text-gray-500">거래처수</div>
              <div className="font-bold">{salesPartners}개</div>
            </div>
            <div>
              <div className="text-gray-500">매수</div>
              <div className="font-bold">{totals.salesCount}매</div>
            </div>
            <div>
              <div className="text-gray-500">공급가액</div>
              <div className="font-bold text-blue-600">{totals.salesSupply.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-gray-500">세액</div>
              <div className="font-bold text-red-600">{totals.salesTax.toLocaleString()}</div>
            </div>
            <div className="col-span-2">
              <div className="text-gray-500">합계금액</div>
              <div className="font-bold text-lg">{totals.salesTotal.toLocaleString()}</div>
            </div>
          </div>
        </div>

        {/* 매입 합계 */}
        <div className="bg-white p-3 rounded border">
          <div className="text-sm font-medium text-red-700 border-b pb-1 mb-2">▶ 매입처별 세금계산서 합계</div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div>
              <div className="text-gray-500">거래처수</div>
              <div className="font-bold">{purchasePartners}개</div>
            </div>
            <div>
              <div className="text-gray-500">매수</div>
              <div className="font-bold">{totals.purchaseCount}매</div>
            </div>
            <div>
              <div className="text-gray-500">공급가액</div>
              <div className="font-bold text-blue-600">{totals.purchaseSupply.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-gray-500">세액</div>
              <div className="font-bold text-red-600">{totals.purchaseTax.toLocaleString()}</div>
            </div>
            <div className="col-span-2">
              <div className="text-gray-500">합계금액</div>
              <div className="font-bold text-lg">{totals.purchaseTotal.toLocaleString()}</div>
            </div>
          </div>
        </div>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>거래처코드</th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>거래처명</th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>사업자번호</th>
              <th className="border border-gray-400 px-2 py-1" rowSpan={2}>대표자</th>
              <th className="border border-gray-400 px-2 py-1 bg-blue-100" colSpan={4}>매 출</th>
              <th className="border border-gray-400 px-2 py-1 bg-red-100" colSpan={4}>매 입</th>
            </tr>
            <tr>
              <th className="border border-gray-400 px-2 py-1 bg-blue-50 w-16">매수</th>
              <th className="border border-gray-400 px-2 py-1 bg-blue-50 w-24">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 bg-blue-50 w-20">세액</th>
              <th className="border border-gray-400 px-2 py-1 bg-blue-50 w-24">합계</th>
              <th className="border border-gray-400 px-2 py-1 bg-red-50 w-16">매수</th>
              <th className="border border-gray-400 px-2 py-1 bg-red-50 w-24">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 bg-red-50 w-20">세액</th>
              <th className="border border-gray-400 px-2 py-1 bg-red-50 w-24">합계</th>
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
                <td className="border border-gray-300 px-2 py-1">{item.partnerCode}</td>
                <td className="border border-gray-300 px-2 py-1 font-medium">{item.partnerName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.businessNo}</td>
                <td className="border border-gray-300 px-2 py-1">{item.representative}</td>
                {/* 매출 */}
                <td className="border border-gray-300 px-2 py-1 text-center bg-blue-50/50">
                  {item.salesCount > 0 ? item.salesCount : "-"}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right bg-blue-50/50 ${
                  selectedId === item.id ? "" : "text-blue-600"
                }`}>
                  {item.salesSupply > 0 ? item.salesSupply.toLocaleString() : "-"}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right bg-blue-50/50 ${
                  selectedId === item.id ? "" : "text-red-600"
                }`}>
                  {item.salesTax > 0 ? item.salesTax.toLocaleString() : "-"}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium bg-blue-50/50">
                  {item.salesTotal > 0 ? item.salesTotal.toLocaleString() : "-"}
                </td>
                {/* 매입 */}
                <td className="border border-gray-300 px-2 py-1 text-center bg-red-50/50">
                  {item.purchaseCount > 0 ? item.purchaseCount : "-"}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right bg-red-50/50 ${
                  selectedId === item.id ? "" : "text-blue-600"
                }`}>
                  {item.purchaseSupply > 0 ? item.purchaseSupply.toLocaleString() : "-"}
                </td>
                <td className={`border border-gray-300 px-2 py-1 text-right bg-red-50/50 ${
                  selectedId === item.id ? "" : "text-red-600"
                }`}>
                  {item.purchaseTax > 0 ? item.purchaseTax.toLocaleString() : "-"}
                </td>
                <td className="border border-gray-300 px-2 py-1 text-right font-medium bg-red-50/50">
                  {item.purchaseTotal > 0 ? item.purchaseTotal.toLocaleString() : "-"}
                </td>
              </tr>
            ))}
            {/* 합계 행 */}
            <tr className="bg-gray-200 font-medium">
              <td className="border border-gray-400 px-2 py-1" colSpan={4}>
                (합계: {filteredData.length}개 거래처)
              </td>
              <td className="border border-gray-400 px-2 py-1 text-center bg-blue-100">
                {totals.salesCount}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600 bg-blue-100">
                {totals.salesSupply.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600 bg-blue-100">
                {totals.salesTax.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right bg-blue-100">
                {totals.salesTotal.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-center bg-red-100">
                {totals.purchaseCount}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-blue-600 bg-red-100">
                {totals.purchaseSupply.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right text-red-600 bg-red-100">
                {totals.purchaseTax.toLocaleString()}
              </td>
              <td className="border border-gray-400 px-2 py-1 text-right bg-red-100">
                {totals.purchaseTotal.toLocaleString()}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        {year}년 {quarter}분기 | 총 {filteredData.length}개 거래처 | 매출처: {salesPartners}개 | 매입처: {purchasePartners}개 | loading ok
      </div>
    </div>
  );
}
