"use client";

import React, { useState, useCallback } from "react";
import { fetchAPI } from "@/lib/api";

interface VendorLedgerItem {
  id: string;
  date: string;
  slipNo: string;
  transType: string;
  productName: string;
  spec: string;
  qty: number;
  unitPrice: number;
  supplyAmount: number;
  tax: number;
  totalAmount: number;
  balance: number;
  memo: string;
}

export function PurchaseVendorLedger() {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [vendorSearch, setVendorSearch] = useState("");
  const [selectedVendor, setSelectedVendor] = useState("");
  const [data, setData] = useState<VendorLedgerItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [previousBalance, setPreviousBalance] = useState(0);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (startDate) params.append("start_date", startDate);
      if (endDate) params.append("end_date", endDate);

      const endpoint = `/v1/erp/ledger/purchase-vendor${params.toString() ? `?${params}` : ""}`;
      const json = await fetchAPI<any>(endpoint);

      const items: VendorLedgerItem[] = (json.items || []).map((item: VendorLedgerItem) => ({
        id: String(item.id),
        date: item.date || "",
        slipNo: item.slipNo || "",
        transType: item.transType || "",
        productName: item.productName || "",
        spec: item.spec || "",
        qty: item.qty || 0,
        unitPrice: item.unitPrice || 0,
        supplyAmount: item.supplyAmount || 0,
        tax: item.tax || 0,
        totalAmount: item.totalAmount || 0,
        balance: item.balance || 0,
        memo: item.memo || "",
      }));

      setData(items);
      setPreviousBalance(json.previousBalance || 0);
      setSelectedVendor(vendorSearch || "전체");
      setLoaded(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : "데이터 로딩 실패";
      setError(message);
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, vendorSearch]);

  // 누계 계산
  const totals = data.reduce(
    (acc, item) => ({
      supplyAmount: acc.supplyAmount + item.supplyAmount,
      tax: acc.tax + item.tax,
    }),
    { supplyAmount: 0, tax: 0 }
  );

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">매입처원장</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
          onClick={fetchData}
        >
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📊</span> 보고서출력
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 엑셀변환
        </button>
      </div>

      {/* 안내 메시지 */}
      <div className="bg-blue-50 px-3 py-1 text-xs text-blue-700">
        • 매입처원장: 선택한 거래처의 매입/지급 내역을 시간순으로 표시합니다.
      </div>

      {/* 검색 조건 */}
      <div className="flex items-center gap-4 border-b bg-white px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="text-xs">기간선택:</span>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          />
          <span className="text-xs">~</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="rounded border border-gray-400 px-2 py-1 text-xs"
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs">거래처:</span>
          <input
            type="text"
            value={vendorSearch}
            onChange={(e) => setVendorSearch(e.target.value)}
            className="w-32 rounded border border-gray-400 px-2 py-1 text-xs"
          />
          <button className="rounded border border-gray-400 bg-gray-100 px-2 py-1 text-xs hover:bg-gray-200">
            ...
          </button>
        </div>
        <button
          className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200"
          onClick={fetchData}
        >
          검 색(F)
        </button>
      </div>

      {/* 선택된 거래처 정보 */}
      {loaded && (
        <div className="border-b bg-yellow-50 px-3 py-1">
          <span className="text-xs font-medium">선택 거래처: {selectedVendor}</span>
          <span className="ml-4 text-xs">전기이월: {previousBalance.toLocaleString()}원</span>
          <span className="ml-4 text-xs">
            현잔액: {data.length > 0 ? data[data.length - 1].balance.toLocaleString() : "0"}원
          </span>
        </div>
      )}

      {/* 에러 표시 */}
      {error && (
        <div className="bg-red-50 px-3 py-1 text-xs text-red-700">
          {error}
        </div>
      )}

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-24">일자</th>
              <th className="border border-gray-400 px-2 py-1 w-28">전표번호</th>
              <th className="border border-gray-400 px-2 py-1 w-16">거래유형</th>
              <th className="border border-gray-400 px-2 py-1 w-24">상품명</th>
              <th className="border border-gray-400 px-2 py-1 w-16">규격</th>
              <th className="border border-gray-400 px-2 py-1 w-14">수량</th>
              <th className="border border-gray-400 px-2 py-1 w-20">단가</th>
              <th className="border border-gray-400 px-2 py-1 w-24">공급가액</th>
              <th className="border border-gray-400 px-2 py-1 w-20">세액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">금액</th>
              <th className="border border-gray-400 px-2 py-1 w-24">잔액</th>
              <th className="border border-gray-400 px-2 py-1">비고</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={12} className="border border-gray-300 px-2 py-4 text-center text-gray-500">
                  데이터 로딩 중...
                </td>
              </tr>
            ) : !loaded ? (
              <tr>
                <td colSpan={12} className="border border-gray-300 px-2 py-4 text-center text-gray-500">
                  기간을 선택하고 검색 버튼을 클릭하세요.
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={12} className="border border-gray-300 px-2 py-4 text-center text-gray-500">
                  조회 결과가 없습니다.
                </td>
              </tr>
            ) : (
              <>
                {data.map((item) => (
                  <tr
                    key={item.id}
                    className={`cursor-pointer ${
                      selectedId === item.id
                        ? "bg-[#316AC5] text-white"
                        : item.transType === "지급"
                        ? "bg-green-50 hover:bg-green-100"
                        : "hover:bg-gray-100"
                    }`}
                    onClick={() => setSelectedId(item.id)}
                  >
                    <td className="border border-gray-300 px-2 py-1">{item.date}</td>
                    <td className="border border-gray-300 px-2 py-1">{item.slipNo}</td>
                    <td className="border border-gray-300 px-2 py-1">{item.transType}</td>
                    <td className="border border-gray-300 px-2 py-1">{item.productName}</td>
                    <td className="border border-gray-300 px-2 py-1">{item.spec}</td>
                    <td className="border border-gray-300 px-2 py-1 text-right">
                      {item.qty || ""}
                    </td>
                    <td className="border border-gray-300 px-2 py-1 text-right">
                      {item.unitPrice ? item.unitPrice.toLocaleString() : ""}
                    </td>
                    <td className="border border-gray-300 px-2 py-1 text-right">
                      {item.supplyAmount ? item.supplyAmount.toLocaleString() : ""}
                    </td>
                    <td className="border border-gray-300 px-2 py-1 text-right">
                      {item.tax ? item.tax.toLocaleString() : ""}
                    </td>
                    <td className={`border border-gray-300 px-2 py-1 text-right ${
                      item.totalAmount < 0 ? "text-red-600" : ""
                    }`}>
                      {item.totalAmount.toLocaleString()}
                    </td>
                    <td className="border border-gray-300 px-2 py-1 text-right">
                      {item.balance.toLocaleString()}
                    </td>
                    <td className="border border-gray-300 px-2 py-1">{item.memo}</td>
                  </tr>
                ))}
                {/* 누계 행 */}
                <tr className="bg-gray-200 font-medium">
                  <td className="border border-gray-400 px-2 py-1" colSpan={7}>
                    (누계)
                  </td>
                  <td className="border border-gray-400 px-2 py-1 text-right">
                    {totals.supplyAmount.toLocaleString()}
                  </td>
                  <td className="border border-gray-400 px-2 py-1 text-right">
                    {totals.tax.toLocaleString()}
                  </td>
                  <td className="border border-gray-400 px-2 py-1"></td>
                  <td className="border border-gray-400 px-2 py-1 text-right">
                    {data.length > 0 ? data[data.length - 1].balance.toLocaleString() : "0"}
                  </td>
                  <td className="border border-gray-400 px-2 py-1"></td>
                </tr>
              </>
            )}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="border-t bg-gray-100 px-3 py-1 text-xs text-green-600">
        총 {data.length}건 | {loading ? "loading..." : loaded ? "loading ok" : "대기중"}
      </div>
    </div>
  );
}
