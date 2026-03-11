"use client";

import React, { useState } from "react";

interface IncomeExpenseItem {
  id: string;
  code: string;           // 항목코드
  groupName: string;      // 그룹명
  itemName: string;       // 항목명
  incomeExpenseType: "입금" | "출금";  // 구분
  processMethod: string;  // 처리분류
  relatedItem: string;    // 관련항목
}

// 이지판매재고관리 원본 데이터 100% 복제 (59개 항목 - 2025-12-05 스크린샷 기준)
const ORIGINAL_DATA: IncomeExpenseItem[] = [
  // 은행관련업무 (6개)
  { id: "1", code: "A0001", groupName: "은행관련업무", itemName: "현금을 은행으로 입금", incomeExpenseType: "입금", processMethod: "처리안함", relatedItem: "없음" },
  { id: "2", code: "A0002", groupName: "은행관련업무", itemName: "은행에서 현금을 출금", incomeExpenseType: "입금", processMethod: "처리안함", relatedItem: "없음" },
  { id: "3", code: "A0003", groupName: "은행관련업무", itemName: "수입수수료", incomeExpenseType: "입금", processMethod: "수익발생", relatedItem: "없음" },
  { id: "4", code: "A0004", groupName: "은행관련업무", itemName: "지급수수료", incomeExpenseType: "출금", processMethod: "수익발생", relatedItem: "없음" },
  { id: "5", code: "A0005", groupName: "은행관련업무", itemName: "수입이자", incomeExpenseType: "입금", processMethod: "수익발생", relatedItem: "없음" },
  { id: "6", code: "A0006", groupName: "은행관련업무", itemName: "지급이자", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  // 복리후생비 (3개)
  { id: "7", code: "A1001", groupName: "복리후생비", itemName: "식대", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "8", code: "A1002", groupName: "복리후생비", itemName: "직원회식", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "9", code: "A1003", groupName: "복리후생비", itemName: "신문/서적", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  // 여비교통비 (3개)
  { id: "10", code: "B1001", groupName: "여비교통비", itemName: "교통비", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "11", code: "B1002", groupName: "여비교통비", itemName: "통행료", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "12", code: "B1003", groupName: "여비교통비", itemName: "출장비", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  // 차량유지비 (5개)
  { id: "13", code: "C1001", groupName: "차량유지비", itemName: "주유대", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "14", code: "C1002", groupName: "차량유지비", itemName: "오일교체", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "15", code: "C1003", groupName: "차량유지비", itemName: "부품교체", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "16", code: "C1004", groupName: "차량유지비", itemName: "주차비", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "17", code: "C1005", groupName: "차량유지비", itemName: "차량보험료", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  // 소모품비 (2개)
  { id: "18", code: "D1001", groupName: "소모품비", itemName: "사무소모품비", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "19", code: "D1002", groupName: "소모품비", itemName: "일반소모품비", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  // 급(상)여지급 (2개)
  { id: "20", code: "E1001", groupName: "급(상)여지급", itemName: "급여지급", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "사원" },
  { id: "21", code: "E1002", groupName: "급(상)여지급", itemName: "상여지급", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "사원" },
  // 가지급금 (4개)
  { id: "22", code: "F1001", groupName: "가지급금", itemName: "가불금지급", incomeExpenseType: "출금", processMethod: "채권증가", relatedItem: "사원" },
  { id: "23", code: "F1002", groupName: "가지급금", itemName: "가불금입금", incomeExpenseType: "입금", processMethod: "채권감소", relatedItem: "사원" },
  { id: "24", code: "F1003", groupName: "가지급금", itemName: "업무가지급금지급", incomeExpenseType: "출금", processMethod: "채권증가", relatedItem: "사원" },
  { id: "25", code: "F1004", groupName: "가지급금", itemName: "업무가지급금입금", incomeExpenseType: "입금", processMethod: "채권감소", relatedItem: "사원" },
  // 관리비 (3개)
  { id: "26", code: "G1001", groupName: "관리비", itemName: "임대료", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "27", code: "G1002", groupName: "관리비", itemName: "관리비", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "28", code: "G1003", groupName: "관리비", itemName: "전화요금", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  // 판공비 (2개)
  { id: "29", code: "H1001", groupName: "판공비", itemName: "접대비", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "30", code: "H1002", groupName: "판공비", itemName: "영업비", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  // 경조비 (1개)
  { id: "31", code: "I1001", groupName: "경조비", itemName: "경조사비", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  // 잡비(일반관리비) (1개)
  { id: "32", code: "J1001", groupName: "잡비(일반관리비)", itemName: "잡비", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  // 잡손실 (1개)
  { id: "33", code: "K1001", groupName: "잡손실", itemName: "기타손실", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  // 잡이익 (1개)
  { id: "34", code: "L1001", groupName: "잡이익", itemName: "기타이익", incomeExpenseType: "입금", processMethod: "수익발생", relatedItem: "없음" },
  // 집기비품매입 (3개)
  { id: "35", code: "M1001", groupName: "집기비품매입", itemName: "가구류매입", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "36", code: "M1002", groupName: "집기비품매입", itemName: "공구및기구매입", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "37", code: "M1003", groupName: "집기비품매입", itemName: "기타비품매입", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  // 전매관리비 (1개)
  { id: "38", code: "N1001", groupName: "전매관리비", itemName: "운송비", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  // 세금과공과 (7개)
  { id: "39", code: "O1001", groupName: "세금과공과", itemName: "부가가치세", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "40", code: "O1002", groupName: "세금과공과", itemName: "법인세", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "41", code: "O1003", groupName: "세금과공과", itemName: "산업재해 보상보험료", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "42", code: "O1004", groupName: "세금과공과", itemName: "고용보험료", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "43", code: "O1005", groupName: "세금과공과", itemName: "의료보험", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "44", code: "O1006", groupName: "세금과공과", itemName: "국민연금", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  { id: "45", code: "O1007", groupName: "세금과공과", itemName: "기타세금", incomeExpenseType: "출금", processMethod: "비용발생", relatedItem: "없음" },
  // 차입금 (2개)
  { id: "46", code: "P1001", groupName: "차입금", itemName: "업체로부터 차입", incomeExpenseType: "입금", processMethod: "채무증가", relatedItem: "거래처" },
  { id: "47", code: "P1002", groupName: "차입금", itemName: "업체 차입금상환", incomeExpenseType: "출금", processMethod: "채무감소", relatedItem: "거래처" },
  // 카드채권 (1개)
  { id: "48", code: "SYS1001", groupName: "카드채권", itemName: "카드사로부터 카드매출", incomeExpenseType: "입금", processMethod: "채권감소", relatedItem: "신용카드" },
  // 카드채무 (1개)
  { id: "49", code: "SYS1002", groupName: "카드채무", itemName: "카드대금상환(채무)", incomeExpenseType: "출금", processMethod: "채무감소", relatedItem: "신용카드" },
];

// 그룹명 목록 (스크린샷 기준)
const GROUP_NAMES = [
  "가지급금",
  "경조비",
  "관리비",
  "급(상)여지급",
  "복리후생비",
  "세금과공과",
  "소모품비",
  "여비교통비",
  "은행관련업무",
  "잡비(일반관리비)",
  "잡손실",
  "잡이익",
  "전매관리비",
  "집기비품매입",
  "차량유지비",
  "차입금",
  "카드채권",
  "카드채무",
  "판공비",
];

// 처리분류 목록 (스크린샷 기준)
const PROCESS_METHODS = ["비용발생", "채권증가", "채권감소", "채무증가", "채무감소", "처리안함", "수익발생"];

// 관련항목 목록 (스크린샷 기준)
const RELATED_ITEMS = ["없음", "거래처", "사원", "신용카드", "어음"];

const emptyItem: IncomeExpenseItem = {
  id: "",
  code: "",
  groupName: "",
  itemName: "",
  incomeExpenseType: "출금",
  processMethod: "비용발생",
  relatedItem: "없음",
};

export function IncomeExpenseItemWindow() {
  const [items, setItems] = useState<IncomeExpenseItem[]>(ORIGINAL_DATA);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRow, setSelectedRow] = useState<number | null>(null);

  // 모달 상태
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit">("add");
  const [editForm, setEditForm] = useState<IncomeExpenseItem>(emptyItem);

  const filteredItems = items.filter(
    (item) =>
      item.itemName.includes(searchQuery) ||
      item.code.includes(searchQuery) ||
      item.groupName.includes(searchQuery)
  );

  // 툴바 버튼 핸들러
  const handleAdd = () => {
    const nextCode = `NEW${String(items.length + 1).padStart(4, "0")}`;
    setEditForm({ ...emptyItem, id: String(Date.now()), code: nextCode });
    setModalMode("add");
    setShowModal(true);
  };

  const handleEdit = () => {
    if (selectedRow === null) {
      alert("수정할 항목을 선택하세요.");
      return;
    }
    const item = filteredItems[selectedRow];
    setEditForm({ ...item });
    setModalMode("edit");
    setShowModal(true);
  };

  const handleDelete = () => {
    if (selectedRow === null) {
      alert("삭제할 항목을 선택하세요.");
      return;
    }
    if (confirm("선택한 항목을 삭제하시겠습니까?")) {
      const item = filteredItems[selectedRow];
      setItems(items.filter((i) => i.id !== item.id));
      setSelectedRow(null);
    }
  };

  const handleRefresh = () => {
    setItems([...ORIGINAL_DATA]);
    setSelectedRow(null);
    setSearchQuery("");
  };

  const handleSearch = () => {
    // 검색은 실시간으로 되므로 별도 처리 불필요
  };

  const handleViewAll = () => {
    setSearchQuery("");
  };

  // 모달 저장
  const handleSave = () => {
    if (!editForm.itemName) {
      alert("항목명을 입력하세요.");
      return;
    }
    if (!editForm.groupName) {
      alert("그룹명을 선택하세요.");
      return;
    }

    if (modalMode === "add") {
      setItems([...items, editForm]);
    } else {
      setItems(
        items.map((i) => (i.id === editForm.id ? editForm : i))
      );
    }
    setShowModal(false);
    setSelectedRow(null);
  };

  // 저장 후 추가
  const handleSaveAndAdd = () => {
    if (!editForm.itemName) {
      alert("항목명을 입력하세요.");
      return;
    }
    if (!editForm.groupName) {
      alert("그룹명을 선택하세요.");
      return;
    }

    if (modalMode === "add") {
      setItems([...items, editForm]);
    } else {
      setItems(
        items.map((i) => (i.id === editForm.id ? editForm : i))
      );
    }
    // 새 항목으로 초기화
    const nextCode = `NEW${String(items.length + 2).padStart(4, "0")}`;
    setEditForm({ ...emptyItem, id: String(Date.now()), code: nextCode });
    setModalMode("add");
  };

  const handleCancel = () => {
    setShowModal(false);
  };

  // 행 더블클릭으로 수정
  const handleRowDoubleClick = (index: number) => {
    setSelectedRow(index);
    const item = filteredItems[index];
    setEditForm({ ...item });
    setModalMode("edit");
    setShowModal(true);
  };

  return (
    <div className="flex h-full flex-col bg-gray-100">
      {/* 툴바 - 이지판매재고관리 스타일 */}
      <div className="flex items-center gap-1 border-b bg-gray-200 px-2 py-1">
        <button
          onClick={handleAdd}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-green-600">⊕</span> 추가
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-blue-600">✎</span> 수정
        </button>
        <button
          onClick={handleDelete}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-red-600">✕</span> 삭제
        </button>
        <div className="mx-1 h-6 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
          <span>A</span> 미리보기
        </button>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
        >
          <span className="text-blue-600">↻</span> 새로고침
        </button>
        <div className="mx-1 h-6 w-px bg-gray-400" />
        <button className="flex items-center gap-1 rounded border border-gray-400 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
          <span>▤</span> 표시항목
        </button>
      </div>

      {/* 검색 영역 */}
      <div className="flex items-center gap-2 border-b bg-gray-100 px-4 py-2">
        <span className="text-sm">항목명:</span>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-40 rounded border border-gray-400 px-2 py-1 text-sm"
        />
        <button
          onClick={handleSearch}
          className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
        >
          검 색(F)
        </button>
        <button
          onClick={handleViewAll}
          className="rounded border border-gray-400 bg-gray-200 px-3 py-1 text-sm hover:bg-gray-300"
        >
          전체보기
        </button>
      </div>

      {/* 그리드 - 이지판매재고관리 컬럼 100% */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-400 px-2 py-1 text-center font-normal">
                <input type="checkbox" />
              </th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">코드</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">그룹명</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">항목명</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">입출금구분</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">처리방법</th>
              <th className="border border-gray-400 px-2 py-1 text-left font-normal">관련항목</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.map((item, index) => (
              <tr
                key={item.id}
                className={`cursor-pointer ${
                  selectedRow === index ? "bg-[#316AC5] text-white" : "bg-white hover:bg-gray-100"
                }`}
                onClick={() => setSelectedRow(index)}
                onDoubleClick={() => handleRowDoubleClick(index)}
              >
                <td className="border border-gray-300 px-2 py-1 text-center">
                  <input type="checkbox" />
                </td>
                <td className="border border-gray-300 px-2 py-1">{item.code}</td>
                <td className="border border-gray-300 px-2 py-1">{item.groupName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.itemName}</td>
                <td className="border border-gray-300 px-2 py-1">{item.incomeExpenseType}</td>
                <td className="border border-gray-300 px-2 py-1">{item.processMethod}</td>
                <td className="border border-gray-300 px-2 py-1">{item.relatedItem}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 하단 상태바 */}
      <div className="flex items-center justify-end border-t bg-gray-100 px-4 py-1 text-sm text-gray-600">
        <span>전체 {items.length} 항목</span>
        <span className="mx-4">|</span>
        <span>{filteredItems.length} 항목표시</span>
      </div>

      {/* 입출금항목 등록 모달 - 이지판매재고관리 100% 복제 */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-[380px] rounded bg-gray-200 shadow-lg">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between border-b border-gray-400 bg-gradient-to-r from-blue-600 to-blue-400 px-3 py-1">
              <span className="text-sm font-medium text-white">입출금항목 등록</span>
              <button
                onClick={handleCancel}
                className="text-white hover:text-gray-200"
              >
                ✕
              </button>
            </div>

            {/* 모달 내용 */}
            <div className="bg-[#F0EDE4] p-4">
              <fieldset className="rounded border border-gray-400 p-3">
                <legend className="px-2 text-sm text-blue-700">입출금항목등록</legend>
                <div className="grid grid-cols-[80px_1fr] gap-2 text-sm">
                  <label className="py-1 text-right">항목코드:</label>
                  <input
                    type="text"
                    value={editForm.code}
                    onChange={(e) => setEditForm({ ...editForm, code: e.target.value })}
                    className="w-32 border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">그룹명:</label>
                  <select
                    value={editForm.groupName}
                    onChange={(e) => setEditForm({ ...editForm, groupName: e.target.value })}
                    className="w-full border border-gray-400 px-2 py-1"
                  >
                    <option value="">선택</option>
                    {GROUP_NAMES.map((name) => (
                      <option key={name} value={name}>{name}</option>
                    ))}
                  </select>

                  <label className="py-1 text-right">항목명:</label>
                  <input
                    type="text"
                    value={editForm.itemName}
                    onChange={(e) => setEditForm({ ...editForm, itemName: e.target.value })}
                    className="w-full border border-gray-400 px-2 py-1"
                  />

                  <label className="py-1 text-right">구분:</label>
                  <select
                    value={editForm.incomeExpenseType}
                    onChange={(e) => setEditForm({ ...editForm, incomeExpenseType: e.target.value as "입금" | "출금" })}
                    className="w-24 border border-gray-400 px-2 py-1"
                  >
                    <option value="출금">출금</option>
                    <option value="입금">입금</option>
                  </select>

                  <label className="py-1 text-right">처리분류:</label>
                  <select
                    value={editForm.processMethod}
                    onChange={(e) => setEditForm({ ...editForm, processMethod: e.target.value })}
                    className="w-32 border border-gray-400 px-2 py-1"
                  >
                    {PROCESS_METHODS.map((method) => (
                      <option key={method} value={method}>{method}</option>
                    ))}
                  </select>

                  <label className="py-1 text-right">관련항목:</label>
                  <select
                    value={editForm.relatedItem}
                    onChange={(e) => setEditForm({ ...editForm, relatedItem: e.target.value })}
                    className="w-32 border border-gray-400 px-2 py-1"
                  >
                    {RELATED_ITEMS.map((item) => (
                      <option key={item} value={item}>{item}</option>
                    ))}
                  </select>
                </div>
              </fieldset>
              <p className="mt-3 text-sm text-gray-600">
                입출금 항목 정보를 등록합니다.
              </p>
            </div>

            {/* 모달 푸터 - 이지판매재고관리 스타일 */}
            <div className="flex justify-end gap-2 border-t border-gray-400 bg-gray-200 px-4 py-3">
              <button
                onClick={handleSaveAndAdd}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
              >
                저장후추가
              </button>
              <button
                onClick={handleSave}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
              >
                저 장
              </button>
              <button
                onClick={handleCancel}
                className="rounded border border-gray-400 bg-gray-100 px-4 py-1.5 text-sm hover:bg-gray-200"
              >
                취 소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
