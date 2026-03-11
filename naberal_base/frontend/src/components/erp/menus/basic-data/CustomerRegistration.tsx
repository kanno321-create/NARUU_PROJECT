"use client";

import React, { useState, useEffect, useCallback } from "react";
import { DraggableModal } from "../../common/DraggableModal";
import { useERPData, Customer as APICustomer } from "@/contexts/ERPDataContext";

// Daum 우편번호 타입은 src/types/daum.d.ts 글로벌 선언 사용

interface Customer {
  id: string;
  code: string;
  name: string;
  type: string;
  phone: string;
  mobile: string;
  fax: string;
  email: string;
  homepage: string;
  zipcode: string;
  address1: string;
  address2: string;
  businessName: string;
  representative: string;
  businessNumber: string;
  businessType: string;
  businessCategory: string;
  manager: string;
  isActive: boolean;
  memo: string;
}

// API 데이터를 로컬 Customer 타입으로 변환
const apiToLocalCustomer = (api: APICustomer): Customer => ({
  id: api.id,
  code: api.code,
  name: api.name,
  type: api.customer_type,
  phone: api.phone || "",
  mobile: "", // API에 없는 필드
  fax: api.fax || "",
  email: api.email || "",
  homepage: "",
  zipcode: "",
  address1: api.address || "",
  address2: "",
  businessName: api.name,
  representative: api.ceo_name || "",
  businessNumber: api.business_number || "",
  businessType: "",
  businessCategory: "",
  manager: api.contact_person || "",
  isActive: api.is_active,
  memo: api.memo || "",
});

// 로컬 Customer를 API 형식으로 변환
const localToApiCustomer = (local: Customer): Omit<APICustomer, "id" | "created_at" | "updated_at"> => ({
  code: local.code,
  name: local.name,
  customer_type: local.type as "매출처" | "매입처" | "매입매출처",
  phone: local.phone || undefined,
  fax: local.fax || undefined,
  email: local.email || undefined,
  address: local.address1 || undefined,
  ceo_name: local.representative || undefined,
  business_number: local.businessNumber || undefined,
  contact_person: local.manager || undefined,
  memo: local.memo || undefined,
  is_active: local.isActive,
});

type ModalTab = "기본정보입력" | "연락처" | "업체정보" | "사업자정보입력" | "메모";

export function CustomerRegistration() {
  // ERPDataContext에서 데이터 및 함수 가져오기
  const {
    customers: apiCustomers,
    customersLoading,
    fetchCustomers,
    addCustomer: apiAddCustomer,
    updateCustomer: apiUpdateCustomer,
    deleteCustomer: apiDeleteCustomer,
  } = useERPData();

  // 로컬 상태
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalTab, setModalTab] = useState<ModalTab>("기본정보입력");
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  const [isNewCustomer, setIsNewCustomer] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // API 데이터를 로컬 형식으로 변환
  const customers = apiCustomers.map(apiToLocalCustomer);

  // 다음 우편번호 API 스크립트 로드
  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://t1.daumcdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js";
    script.async = true;
    script.onerror = () => {
      const manualAddress = prompt(
        "주소 검색 서비스에 연결할 수 없습니다.\n주소를 직접 입력해주세요:"
      );
      if (manualAddress) {
        setEditingCustomer((prev) =>
          prev ? { ...prev, address1: manualAddress } : prev
        );
      }
    };
    document.head.appendChild(script);
    return () => {
      document.head.removeChild(script);
    };
  }, []);

  // 주소 검색 함수
  const handleAddressSearch = () => {
    if (!window.daum?.Postcode) {
      const manualAddress = prompt(
        "주소 검색 서비스를 사용할 수 없습니다.\n주소를 직접 입력해주세요:"
      );
      if (manualAddress && editingCustomer) {
        setEditingCustomer((prev) =>
          prev ? { ...prev, address1: manualAddress } : prev
        );
      }
      return;
    }
    new window.daum.Postcode({
      oncomplete: (data: DaumPostcodeResult) => {
        if (editingCustomer) {
          setEditingCustomer({
            ...editingCustomer,
            zipcode: data.zonecode,
            address1: data.roadAddress || data.jibunAddress,
          });
        }
      },
    }).open();
  };

  const filteredCustomers = customers.filter(
    (c) => c.name.includes(searchQuery) || c.code.includes(searchQuery)
  );

  const handleAdd = () => {
    setIsNewCustomer(true);
    setEditingCustomer({
      id: Date.now().toString(),
      code: `m${String(customers.length + 1).padStart(3, "0")}`,
      name: "", type: "매출처", phone: "", mobile: "", fax: "",
      email: "", homepage: "", zipcode: "", address1: "", address2: "",
      businessName: "", representative: "", businessNumber: "",
      businessType: "", businessCategory: "", manager: "", isActive: true, memo: ""
    });
    setModalTab("기본정보입력");
    setIsModalOpen(true);
  };

  const handleEdit = () => {
    const customer = customers.find((c) => c.id === selectedId);
    if (customer) {
      setIsNewCustomer(false);
      setEditingCustomer({ ...customer });
      setModalTab("기본정보입력");
      setIsModalOpen(true);
    }
  };

  const handleDelete = async () => {
    if (selectedId && confirm("선택한 거래처를 삭제하시겠습니까?")) {
      const success = await apiDeleteCustomer(selectedId);
      if (success) {
        setSelectedId(null);
        alert("삭제되었습니다.");
      } else {
        alert("삭제에 실패했습니다.");
      }
    }
  };

  const handleSave = async () => {
    if (!editingCustomer) return;
    if (!editingCustomer.name) {
      alert("업체명을 입력하세요.");
      return;
    }

    setIsSaving(true);
    try {
      if (isNewCustomer) {
        const result = await apiAddCustomer(localToApiCustomer(editingCustomer));
        if (result) {
          alert("저장되었습니다.");
          setIsModalOpen(false);
          setEditingCustomer(null);
        } else {
          alert("저장에 실패했습니다.");
        }
      } else {
        const result = await apiUpdateCustomer(editingCustomer.id, localToApiCustomer(editingCustomer));
        if (result) {
          alert("수정되었습니다.");
          setIsModalOpen(false);
          setEditingCustomer(null);
        } else {
          alert("수정에 실패했습니다.");
        }
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveAndAdd = async () => {
    await handleSave();
    if (!isSaving) {
      setTimeout(() => handleAdd(), 100);
    }
  };

  // 새로고침 핸들러
  const handleRefresh = async () => {
    await fetchCustomers();
  };

  const modalTabs: ModalTab[] = ["기본정보입력", "연락처", "업체정보", "사업자정보입력", "메모"];

  return (
    <div className="flex h-full flex-col bg-gray-50">
      {/* 툴바 */}
      <div className="flex items-center gap-1 border-b bg-gray-100 px-2 py-1">
        <button onClick={handleAdd} className="flex items-center gap-1 rounded border border-gray-300 bg-white px-3 py-1 text-sm hover:bg-gray-50">
          <span className="text-green-600">⊕</span> 추가
        </button>
        <button onClick={handleEdit} disabled={!selectedId} className="flex items-center gap-1 rounded border border-gray-300 bg-white px-3 py-1 text-sm hover:bg-gray-50 disabled:opacity-50">
          <span className="text-blue-600">✓</span> 수정
        </button>
        <button onClick={handleDelete} disabled={!selectedId} className="flex items-center gap-1 rounded border border-gray-300 bg-white px-3 py-1 text-sm hover:bg-gray-50 disabled:opacity-50">
          <span className="text-red-600">✕</span> 삭제
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-300 bg-white px-3 py-1 text-sm hover:bg-gray-50">
          <span>A</span> 미리보기
        </button>
        <button
          onClick={handleRefresh}
          disabled={customersLoading}
          className="flex items-center gap-1 rounded border border-gray-300 bg-white px-3 py-1 text-sm hover:bg-gray-50 disabled:opacity-50"
        >
          🔄 {customersLoading ? "로딩중..." : "새로고침"}
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-300 bg-white px-3 py-1 text-sm hover:bg-gray-50">
          📋 표시항목 ▼
        </button>
        <button className="flex items-center gap-1 rounded border border-gray-300 bg-white px-3 py-1 text-sm hover:bg-gray-50">
          📊 엑셀입력
        </button>
      </div>

      {/* 검색 */}
      <div className="flex items-center gap-2 border-b bg-white px-3 py-2">
        <span className="text-sm">거래처명:</span>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-40 rounded border border-gray-300 px-2 py-1 text-sm"
        />
        <button className="rounded border border-gray-300 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
          검 색(F)
        </button>
        <button onClick={() => setSearchQuery("")} className="rounded border border-gray-300 bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200">
          전체보기
        </button>
      </div>

      {/* 그리드 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 bg-[#E8E4D9]">
            <tr>
              <th className="border border-gray-300 px-2 py-1 text-left">코드</th>
              <th className="border border-gray-300 px-2 py-1 text-left">거래처명</th>
              <th className="border border-gray-300 px-2 py-1 text-left">거래처구분</th>
              <th className="border border-gray-300 px-2 py-1 text-left">전화번호</th>
              <th className="border border-gray-300 px-2 py-1 text-left">핸드폰번호</th>
              <th className="border border-gray-300 px-2 py-1 text-left">팩스번호</th>
              <th className="border border-gray-300 px-2 py-1 text-left">E메일주소</th>
              <th className="border border-gray-300 px-2 py-1 text-left">우편번호</th>
              <th className="border border-gray-300 px-2 py-1 text-left">주소1</th>
              <th className="border border-gray-300 px-2 py-1 text-left">상호(사업장명)</th>
              <th className="border border-gray-300 px-2 py-1 text-left">성명(대표자)</th>
              <th className="border border-gray-300 px-2 py-1 text-left">사업자등록번호</th>
              <th className="border border-gray-300 px-2 py-1 text-left">업태</th>
              <th className="border border-gray-300 px-2 py-1 text-left">종목</th>
              <th className="border border-gray-300 px-2 py-1 text-left">담당사원</th>
              <th className="border border-gray-300 px-2 py-1 text-left">사용여부</th>
            </tr>
          </thead>
          <tbody>
            {filteredCustomers.map((c) => (
              <tr
                key={c.id}
                className={`cursor-pointer ${selectedId === c.id ? "bg-[#316AC5] text-white" : "hover:bg-gray-100"}`}
                onClick={() => setSelectedId(c.id)}
                onDoubleClick={handleEdit}
              >
                <td className="border border-gray-200 px-2 py-1">{c.code}</td>
                <td className="border border-gray-200 px-2 py-1">{c.name}</td>
                <td className="border border-gray-200 px-2 py-1">{c.type}</td>
                <td className="border border-gray-200 px-2 py-1">{c.phone}</td>
                <td className="border border-gray-200 px-2 py-1">{c.mobile}</td>
                <td className="border border-gray-200 px-2 py-1">{c.fax}</td>
                <td className="border border-gray-200 px-2 py-1">{c.email}</td>
                <td className="border border-gray-200 px-2 py-1">{c.zipcode}</td>
                <td className="border border-gray-200 px-2 py-1">{c.address1}</td>
                <td className="border border-gray-200 px-2 py-1">{c.businessName}</td>
                <td className="border border-gray-200 px-2 py-1">{c.representative}</td>
                <td className="border border-gray-200 px-2 py-1">{c.businessNumber}</td>
                <td className="border border-gray-200 px-2 py-1">{c.businessType}</td>
                <td className="border border-gray-200 px-2 py-1">{c.businessCategory}</td>
                <td className="border border-gray-200 px-2 py-1">{c.manager}</td>
                <td className="border border-gray-200 px-2 py-1">{c.isActive ? "사용" : "미사용"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 상태바 */}
      <div className="flex justify-end border-t bg-gray-100 px-3 py-1 text-xs text-gray-600">
        전체 {customers.length} 항목 | {filteredCustomers.length} 항목표시
      </div>

      {/* 드래그 가능한 모달 - 메인창 밖으로 이동 가능 */}
      {editingCustomer && (
        <DraggableModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          title="거래처정보등록"
          width="500px"
          showOverlay={false}
        >
          <div className="bg-[#F0EDE4]">
            {/* 탭 */}
            <div className="flex border-b bg-[#E8E4D9]">
              {modalTabs.map((tab) => (
                <button
                  key={tab}
                  onClick={() => setModalTab(tab)}
                  className={`px-3 py-1.5 text-xs ${modalTab === tab ? "bg-[#F0EDE4] font-medium" : "hover:bg-gray-200"}`}
                >
                  {tab}
                </button>
              ))}
            </div>

            <div className="p-4">
              {modalTab === "기본정보입력" && (
                <fieldset className="rounded border border-gray-400 p-3">
                  <legend className="px-2 text-xs text-blue-700">기본정보</legend>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-right text-xs">코드:</label>
                      <input type="text" value={editingCustomer.code} readOnly className="w-32 rounded border border-gray-300 bg-gray-100 px-2 py-1 text-xs" />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-right text-xs">업체명:</label>
                      <input type="text" value={editingCustomer.name} onChange={(e) => setEditingCustomer({ ...editingCustomer, name: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-right text-xs">거래처구분:</label>
                      <select value={editingCustomer.type} onChange={(e) => setEditingCustomer({ ...editingCustomer, type: e.target.value })} className="w-32 rounded border border-gray-300 px-2 py-1 text-xs">
                        <option value="매출처">매출처</option>
                        <option value="매입처">매입처</option>
                        <option value="매입매출처">매입매출처</option>
                      </select>
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-right text-xs">사용:</label>
                      <select value={editingCustomer.isActive ? "사용" : "미사용"} onChange={(e) => setEditingCustomer({ ...editingCustomer, isActive: e.target.value === "사용" })} className="w-32 rounded border border-gray-300 px-2 py-1 text-xs">
                        <option value="사용">사용</option>
                        <option value="미사용">미사용</option>
                      </select>
                    </div>
                  </div>
                </fieldset>
              )}

              {modalTab === "연락처" && (
                <fieldset className="rounded border border-gray-400 p-3">
                  <legend className="px-2 text-xs text-blue-700">연락처정보</legend>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-right text-xs">전화번호:</label>
                      <input type="text" value={editingCustomer.phone} onChange={(e) => setEditingCustomer({ ...editingCustomer, phone: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-right text-xs">핸드폰:</label>
                      <input type="text" value={editingCustomer.mobile} onChange={(e) => setEditingCustomer({ ...editingCustomer, mobile: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-right text-xs">팩스번호:</label>
                      <input type="text" value={editingCustomer.fax} onChange={(e) => setEditingCustomer({ ...editingCustomer, fax: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-right text-xs">E메일:</label>
                      <input type="text" value={editingCustomer.email} onChange={(e) => setEditingCustomer({ ...editingCustomer, email: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-right text-xs">홈페이지:</label>
                      <input type="text" value={editingCustomer.homepage} onChange={(e) => setEditingCustomer({ ...editingCustomer, homepage: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                    </div>
                  </div>
                </fieldset>
              )}

              {modalTab === "업체정보" && (
                <fieldset className="rounded border border-gray-400 p-3">
                  <legend className="px-2 text-xs text-blue-700">업체정보</legend>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-right text-xs">우편번호:</label>
                      <input type="text" value={editingCustomer.zipcode} onChange={(e) => setEditingCustomer({ ...editingCustomer, zipcode: e.target.value })} className="w-24 rounded border border-gray-300 px-2 py-1 text-xs" readOnly />
                      <button
                        onClick={handleAddressSearch}
                        className="rounded border border-gray-300 bg-blue-500 text-white px-2 py-0.5 text-xs hover:bg-blue-600"
                      >
                        주소찾기
                      </button>
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-right text-xs">주소1:</label>
                      <input type="text" value={editingCustomer.address1} onChange={(e) => setEditingCustomer({ ...editingCustomer, address1: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-right text-xs">주소2:</label>
                      <input type="text" value={editingCustomer.address2} onChange={(e) => setEditingCustomer({ ...editingCustomer, address2: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-20 text-right text-xs">담당사원:</label>
                      <input type="text" value={editingCustomer.manager} onChange={(e) => setEditingCustomer({ ...editingCustomer, manager: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                    </div>
                  </div>
                </fieldset>
              )}

              {modalTab === "사업자정보입력" && (
                <fieldset className="rounded border border-gray-400 p-3">
                  <legend className="px-2 text-xs text-blue-700">사업자정보</legend>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <label className="w-24 text-right text-xs">상호(사업장명):</label>
                      <input type="text" value={editingCustomer.businessName} onChange={(e) => setEditingCustomer({ ...editingCustomer, businessName: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-24 text-right text-xs">성명(대표자):</label>
                      <input type="text" value={editingCustomer.representative} onChange={(e) => setEditingCustomer({ ...editingCustomer, representative: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-24 text-right text-xs">사업자등록번호:</label>
                      <input type="text" value={editingCustomer.businessNumber} onChange={(e) => setEditingCustomer({ ...editingCustomer, businessNumber: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-24 text-right text-xs">업태:</label>
                      <input type="text" value={editingCustomer.businessType} onChange={(e) => setEditingCustomer({ ...editingCustomer, businessType: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="w-24 text-right text-xs">종목:</label>
                      <input type="text" value={editingCustomer.businessCategory} onChange={(e) => setEditingCustomer({ ...editingCustomer, businessCategory: e.target.value })} className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs" />
                    </div>
                  </div>
                </fieldset>
              )}

              {modalTab === "메모" && (
                <fieldset className="rounded border border-gray-400 p-3">
                  <legend className="px-2 text-xs text-blue-700">메모</legend>
                  <textarea
                    value={editingCustomer.memo}
                    onChange={(e) => setEditingCustomer({ ...editingCustomer, memo: e.target.value })}
                    className="h-32 w-full rounded border border-gray-300 p-2 text-xs"
                    placeholder="메모를 입력하세요."
                  />
                </fieldset>
              )}

              <div className="mt-3 text-xs text-blue-600">
                새로운 거래처의 정보를 등록합니다.
              </div>
            </div>

            <div className="flex justify-end gap-2 border-t bg-[#E8E4D9] px-4 py-2">
              <button onClick={handleSaveAndAdd} className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-xs hover:bg-gray-200">저장후추가</button>
              <button onClick={handleSave} className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-xs hover:bg-gray-200">저장</button>
              <button onClick={() => setIsModalOpen(false)} className="rounded border border-gray-400 bg-gray-100 px-3 py-1 text-xs hover:bg-gray-200">취소</button>
            </div>
          </div>
        </DraggableModal>
      )}
    </div>
  );
}
