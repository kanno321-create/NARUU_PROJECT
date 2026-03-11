"use client";

import React, { useState } from "react";

interface CashItem {
  id: string;
  code: string;
  groupName: string;
  itemName: string;
  inOutType: "입금" | "출금";
  processMethod: string;
  relatedItem: string;
}

// 이지판매재고관리 원본 데이터 100% 복제 (2025-12-05 스크린샷 기준)
const ORIGINAL_ITEMS: CashItem[] = [
  { id: "1", code: "A0001", groupName: "은행관련업무", itemName: "현금을 은행으로 입금", inOutType: "입금", processMethod: "처리안함", relatedItem: "없음" },
  { id: "2", code: "A0002", groupName: "은행관련업무", itemName: "은행에서 현금을 출금", inOutType: "입금", processMethod: "처리안함", relatedItem: "없음" },
  { id: "3", code: "A0003", groupName: "은행관련업무", itemName: "수입수수료", inOutType: "입금", processMethod: "수익발생", relatedItem: "없음" },
  { id: "4", code: "A0004", groupName: "은행관련업무", itemName: "지급수수료", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "5", code: "A0005", groupName: "은행관련업무", itemName: "수입이자", inOutType: "입금", processMethod: "수익발생", relatedItem: "없음" },
  { id: "6", code: "A0006", groupName: "은행관련업무", itemName: "지급이자", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "7", code: "A1001", groupName: "복리후생비", itemName: "식대", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "8", code: "A1002", groupName: "복리후생비", itemName: "직원회식", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "9", code: "A1003", groupName: "복리후생비", itemName: "신문/서적", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "10", code: "B1001", groupName: "여비교통비", itemName: "교통비", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "11", code: "B1002", groupName: "여비교통비", itemName: "통행료", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "12", code: "B1003", groupName: "여비교통비", itemName: "출장비", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "13", code: "C1001", groupName: "차량유지비", itemName: "주유대", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "14", code: "C1002", groupName: "차량유지비", itemName: "오일교체", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "15", code: "C1003", groupName: "차량유지비", itemName: "부품교체", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "16", code: "C1004", groupName: "차량유지비", itemName: "주차비", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "17", code: "C1005", groupName: "차량유지비", itemName: "차량보험료", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "18", code: "D1001", groupName: "소모품비", itemName: "사무소모품비", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "19", code: "D1002", groupName: "소모품비", itemName: "일반소모품비", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "20", code: "E1001", groupName: "급(상)여지급", itemName: "급여지급", inOutType: "출금", processMethod: "비용발생", relatedItem: "사원" },
  { id: "21", code: "E1002", groupName: "급(상)여지급", itemName: "상여지급", inOutType: "출금", processMethod: "비용발생", relatedItem: "사원" },
  { id: "22", code: "F1001", groupName: "가지급금", itemName: "가불금지급", inOutType: "출금", processMethod: "채권증가", relatedItem: "사원" },
  { id: "23", code: "F1002", groupName: "가지급금", itemName: "가불금입금", inOutType: "입금", processMethod: "채권감소", relatedItem: "사원" },
  { id: "24", code: "F1003", groupName: "가지급금", itemName: "업무가지급금지급", inOutType: "출금", processMethod: "채권증가", relatedItem: "사원" },
  { id: "25", code: "F1004", groupName: "가지급금", itemName: "업무가지급금입금", inOutType: "입금", processMethod: "채권감소", relatedItem: "사원" },
  { id: "26", code: "G1001", groupName: "관리비", itemName: "임대료", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "27", code: "G1002", groupName: "관리비", itemName: "관리비", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "28", code: "G1003", groupName: "관리비", itemName: "전화요금", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "29", code: "H1001", groupName: "판공비", itemName: "접대비", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "30", code: "H1002", groupName: "판공비", itemName: "영업비", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "31", code: "I1001", groupName: "경조비", itemName: "경조사비", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "32", code: "J1001", groupName: "잡비(일반관리비)", itemName: "잡비", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "33", code: "K1001", groupName: "잡손실", itemName: "기타손실", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "34", code: "L1001", groupName: "잡이익", itemName: "기타이익", inOutType: "입금", processMethod: "수익발생", relatedItem: "없음" },
  { id: "35", code: "M1001", groupName: "집기비품매입", itemName: "가구류매입", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "36", code: "M1002", groupName: "집기비품매입", itemName: "공구및기구매입", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "37", code: "M1003", groupName: "집기비품매입", itemName: "기타비품매입", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "38", code: "N1001", groupName: "전매관리비", itemName: "운송비", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "39", code: "O1001", groupName: "세금과공과", itemName: "부가가치세", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "40", code: "O1002", groupName: "세금과공과", itemName: "법인세", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "41", code: "O1003", groupName: "세금과공과", itemName: "산업재해 보상보험료", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "42", code: "O1004", groupName: "세금과공과", itemName: "고용보험료", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "43", code: "O1005", groupName: "세금과공과", itemName: "의료보험", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "44", code: "O1006", groupName: "세금과공과", itemName: "국민연금", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "45", code: "O1007", groupName: "세금과공과", itemName: "기타세금", inOutType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "46", code: "P1001", groupName: "차입금", itemName: "업체로부터 차입", inOutType: "입금", processMethod: "채무증가", relatedItem: "거래처" },
  { id: "47", code: "P1002", groupName: "차입금", itemName: "업체 차입금상환", inOutType: "출금", processMethod: "채무감소", relatedItem: "거래처" },
  { id: "48", code: "SYS1001", groupName: "카드채권", itemName: "카드사로부터 카드매출", inOutType: "입금", processMethod: "채권감소", relatedItem: "신용카드" },
  { id: "49", code: "SYS1002", groupName: "카드채무", itemName: "카드대금상환(채무)", inOutType: "출금", processMethod: "채무감소", relatedItem: "신용카드" },
];

const GROUPS = [...new Set(ORIGINAL_ITEMS.map(item => item.groupName))];
const PROCESS_METHODS = ["처리안함", "비용발생", "수익발생", "채권증가", "채권감소", "채무증가", "채무감소"];
const RELATED_ITEMS = ["없음", "사원", "거래처", "신용카드"];

export function CashItemRegistration() {
  const [items, setItems] = useState<CashItem[]>(ORIGINAL_ITEMS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit">("add");

  const [formData, setFormData] = useState<Omit<CashItem, "id">>({
    code: "",
    groupName: "",
    itemName: "",
    inOutType: "출금",
    processMethod: "비용발생",
    relatedItem: "없음",
  });

  const filteredItems = items.filter(
    (item) =>
      item.itemName.includes(searchQuery) ||
      item.code.includes(searchQuery) ||
      item.groupName.includes(searchQuery)
  );

  const handleAdd = () => {
    setModalMode("add");
    const maxCode = Math.max(...items.map(i => parseInt(i.code.slice(1)) || 0));
    setFormData({
      code: `Z${String(maxCode + 1).padStart(4, "0")}`,
      groupName: "",
      itemName: "",
      inOutType: "출금",
      processMethod: "비용발생",
      relatedItem: "없음",
    });
    setIsModalOpen(true);
  };

  const handleEdit = () => {
    if (!selectedId) return;
    const item = items.find((i) => i.id === selectedId);
    if (!item) return;
    setModalMode("edit");
    const { id, ...rest } = item;
    setFormData(rest);
    setIsModalOpen(true);
  };

  const handleDelete = () => {
    if (!selectedId) return;
    if (confirm("선택한 항목을 삭제하시겠습니까?")) {
      setItems(items.filter((i) => i.id !== selectedId));
      setSelectedId(null);
    }
  };

  const handleSave = () => {
    if (!formData.groupName || !formData.itemName) {
      alert("그룹명과 항목명은 필수 입력 항목입니다.");
      return;
    }

    if (modalMode === "add") {
      const newItem: CashItem = {
        id: Date.now().toString(),
        ...formData,
      };
      setItems([...items, newItem]);
    } else {
      setItems(
        items.map((i) => (i.id === selectedId ? { ...i, ...formData } : i))
      );
    }
    setIsModalOpen(false);
  };

  const handleRowDoubleClick = (item: CashItem) => {
    setSelectedId(item.id);
    setModalMode("edit");
    const { id, ...rest } = item;
    setFormData(rest);
    setIsModalOpen(true);
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 타이틀바 */}
      <div className="flex items-center justify-between border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
        <span className="text-sm font-medium text-white">입출금항목등록</span>
      </div>

      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button
          onClick={handleAdd}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
        >
          <span>➕</span> 추가
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
          disabled={!selectedId}
        >
          <span>✏️</span> 수정
        </button>
        <button
          onClick={handleDelete}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200"
          disabled={!selectedId}
        >
          <span>🗑️</span> 삭제
        </button>
        <div className="mx-2 h-4 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔤</span> 미리보기
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>🔄</span> 새로고침
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-2 py-0.5 text-xs hover:bg-gray-200">
          <span>📋</span> 표시항목
        </button>
      </div>

      {/* 검색 바 */}
      <div className="flex items-center gap-2 border-b bg-white px-2 py-1">
        <span className="text-xs">항목명:</span>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-40 rounded border border-gray-400 px-2 py-0.5 text-xs"
        />
        <button className="rounded border border-gray-400 bg-gray-100 px-3 py-0.5 text-xs hover:bg-gray-200">
          검 색(F)
        </button>
        <button
          onClick={() => setSearchQuery("")}
          className="rounded border border-gray-400 bg-gray-100 px-3 py-0.5 text-xs hover:bg-gray-200"
        >
          전체보기
        </button>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 w-20">코드</th>
              <th className="border border-gray-400 px-2 py-1 w-32">그룹명</th>
              <th className="border border-gray-400 px-2 py-1 w-48">항목명</th>
              <th className="border border-gray-400 px-2 py-1 w-20">입출금구분</th>
              <th className="border border-gray-400 px-2 py-1 w-24">처리방법</th>
              <th className="border border-gray-400 px-2 py-1">관련항목</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.map((item) => (
              <tr
                key={item.id}
                className={`cursor-pointer ${
                  selectedId === item.id ? "bg-[#316AC5] text-white" : "hover:bg-gray-100"
                }`}
                onClick={() => setSelectedId(item.id)}
                onDoubleClick={() => handleRowDoubleClick(item)}
              >
                <td className="border border-gray-300 px-2 py-1">{item.code}</td>
                <td className="border border-gray-300 px-2 py-1">{item.groupName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.itemName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.inOutType}</td>
                <td className="border border-gray-300 px-2 py-1">{item.processMethod}</td>
                <td className="border border-gray-300 px-2 py-1">{item.relatedItem}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="flex justify-between border-t bg-gray-100 px-3 py-1 text-xs">
        <span className="text-green-600">loading ok</span>
        <span>전체 {items.length} 항목 &nbsp;&nbsp; {filteredItems.length} 항목표시</span>
      </div>

      {/* 모달 */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-[450px] rounded border border-gray-400 bg-[#F0EDE4] shadow-lg">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between rounded-t border-b bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">
                {modalMode === "add" ? "항목 추가" : "항목 수정"}
              </span>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-white hover:text-gray-200"
              >
                ✕
              </button>
            </div>

            {/* 모달 내용 */}
            <div className="p-4 space-y-3">
              <div className="flex items-center gap-2">
                <label className="w-24 text-right text-xs">코드:</label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  className="w-28 rounded border border-gray-400 px-2 py-1 text-xs"
                />
              </div>
              <div className="flex items-center gap-2">
                <label className="w-24 text-right text-xs">그룹명:</label>
                <select
                  value={formData.groupName}
                  onChange={(e) => setFormData({ ...formData, groupName: e.target.value })}
                  className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                >
                  <option value="">선택</option>
                  {GROUPS.map((g) => (
                    <option key={g} value={g}>{g}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label className="w-24 text-right text-xs">항목명:</label>
                <input
                  type="text"
                  value={formData.itemName}
                  onChange={(e) => setFormData({ ...formData, itemName: e.target.value })}
                  className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                />
              </div>
              <div className="flex items-center gap-2">
                <label className="w-24 text-right text-xs">입출금구분:</label>
                <select
                  value={formData.inOutType}
                  onChange={(e) => setFormData({ ...formData, inOutType: e.target.value as "입금" | "출금" })}
                  className="w-24 rounded border border-gray-400 px-2 py-1 text-xs"
                >
                  <option value="입금">입금</option>
                  <option value="출금">출금</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label className="w-24 text-right text-xs">처리방법:</label>
                <select
                  value={formData.processMethod}
                  onChange={(e) => setFormData({ ...formData, processMethod: e.target.value })}
                  className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                >
                  {PROCESS_METHODS.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label className="w-24 text-right text-xs">관련항목:</label>
                <select
                  value={formData.relatedItem}
                  onChange={(e) => setFormData({ ...formData, relatedItem: e.target.value })}
                  className="flex-1 rounded border border-gray-400 px-2 py-1 text-xs"
                >
                  {RELATED_ITEMS.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* 모달 푸터 */}
            <div className="flex justify-end gap-2 border-t bg-gray-200 px-4 py-2">
              <button
                onClick={handleSave}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1 text-xs hover:bg-gray-200"
              >
                저장
              </button>
              <button
                onClick={() => setIsModalOpen(false)}
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
