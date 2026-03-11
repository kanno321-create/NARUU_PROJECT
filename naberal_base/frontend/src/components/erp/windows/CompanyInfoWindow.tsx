"use client";

import React, { useState, useEffect } from "react";
import { Save, Building2, Upload } from "lucide-react";

interface CompanyInfo {
    companyName: string;
    businessNumber: string;
    representative: string;
    businessType: string;
    businessCategory: string;
    address: string;
    phone: string;
    fax: string;
    email: string;
    website: string;
    bankName: string;
    accountNumber: string;
    accountHolder: string;
    logo: string;
    stamp: string;
}

export function CompanyInfoWindow() {
    const [info, setInfo] = useState<CompanyInfo>({
        companyName: "(주)한국산업",
        businessNumber: "123-45-67890",
        representative: "홍길동",
        businessType: "제조업",
        businessCategory: "전기기기",
        address: "서울시 강남구 테헤란로 123",
        phone: "02-1234-5678",
        fax: "02-1234-5679",
        email: "info@hankook.co.kr",
        website: "www.hankook.co.kr",
        bankName: "국민은행",
        accountNumber: "123-456-789012",
        accountHolder: "㈜한국산업",
        logo: "",
        stamp: "",
    });
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

    // 로컬스토리지에서 불러오기
    useEffect(() => {
        const saved = localStorage.getItem("erp_company_info");
        if (saved) {
            try {
                setInfo(JSON.parse(saved));
            } catch (e) {
                console.error("회사정보 불러오기 실패:", e);
            }
        }
    }, []);

    // 저장
    const handleSave = async () => {
        setSaving(true);
        try {
            localStorage.setItem("erp_company_info", JSON.stringify(info));
            setMessage({ type: "success", text: "자사정보가 저장되었습니다." });
            setTimeout(() => setMessage(null), 3000);
        } catch (error) {
            setMessage({ type: "error", text: "저장에 실패했습니다." });
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="flex h-full flex-col">
            {/* 툴바 */}
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark disabled:opacity-50"
                >
                    <Save className="h-4 w-4" />
                    {saving ? "저장 중..." : "저장"}
                </button>

                {message && (
                    <span className={`ml-4 text-sm ${message.type === "success" ? "text-green-600" : "text-red-600"}`}>
                        {message.text}
                    </span>
                )}
            </div>

            {/* 내용 */}
            <div className="flex-1 overflow-auto p-4">
                <div className="mx-auto max-w-3xl space-y-6">
                    {/* 기본 정보 */}
                    <div className="rounded border p-4">
                        <h3 className="flex items-center gap-2 text-lg font-medium mb-4">
                            <Building2 className="h-5 w-5" />
                            기본 정보
                        </h3>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">회사명 *</label>
                                <input
                                    type="text"
                                    value={info.companyName}
                                    onChange={(e) => setInfo({ ...info, companyName: e.target.value })}
                                    className="w-full rounded border px-3 py-2 text-sm"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">사업자등록번호 *</label>
                                <input
                                    type="text"
                                    value={info.businessNumber}
                                    onChange={(e) => setInfo({ ...info, businessNumber: e.target.value })}
                                    className="w-full rounded border px-3 py-2 text-sm"
                                    placeholder="000-00-00000"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">대표자 *</label>
                                <input
                                    type="text"
                                    value={info.representative}
                                    onChange={(e) => setInfo({ ...info, representative: e.target.value })}
                                    className="w-full rounded border px-3 py-2 text-sm"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">업태</label>
                                <input
                                    type="text"
                                    value={info.businessType}
                                    onChange={(e) => setInfo({ ...info, businessType: e.target.value })}
                                    className="w-full rounded border px-3 py-2 text-sm"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">업종</label>
                                <input
                                    type="text"
                                    value={info.businessCategory}
                                    onChange={(e) => setInfo({ ...info, businessCategory: e.target.value })}
                                    className="w-full rounded border px-3 py-2 text-sm"
                                />
                            </div>
                            <div className="col-span-2">
                                <label className="block text-sm font-medium mb-1">사업장 주소</label>
                                <input
                                    type="text"
                                    value={info.address}
                                    onChange={(e) => setInfo({ ...info, address: e.target.value })}
                                    className="w-full rounded border px-3 py-2 text-sm"
                                />
                            </div>
                        </div>
                    </div>

                    {/* 연락처 정보 */}
                    <div className="rounded border p-4">
                        <h3 className="text-lg font-medium mb-4">연락처 정보</h3>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">전화번호</label>
                                <input
                                    type="text"
                                    value={info.phone}
                                    onChange={(e) => setInfo({ ...info, phone: e.target.value })}
                                    className="w-full rounded border px-3 py-2 text-sm"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">팩스번호</label>
                                <input
                                    type="text"
                                    value={info.fax}
                                    onChange={(e) => setInfo({ ...info, fax: e.target.value })}
                                    className="w-full rounded border px-3 py-2 text-sm"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">이메일</label>
                                <input
                                    type="email"
                                    value={info.email}
                                    onChange={(e) => setInfo({ ...info, email: e.target.value })}
                                    className="w-full rounded border px-3 py-2 text-sm"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">웹사이트</label>
                                <input
                                    type="text"
                                    value={info.website}
                                    onChange={(e) => setInfo({ ...info, website: e.target.value })}
                                    className="w-full rounded border px-3 py-2 text-sm"
                                />
                            </div>
                        </div>
                    </div>

                    {/* 계좌 정보 */}
                    <div className="rounded border p-4">
                        <h3 className="text-lg font-medium mb-4">계좌 정보</h3>

                        <div className="grid grid-cols-3 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">은행명</label>
                                <input
                                    type="text"
                                    value={info.bankName}
                                    onChange={(e) => setInfo({ ...info, bankName: e.target.value })}
                                    className="w-full rounded border px-3 py-2 text-sm"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">계좌번호</label>
                                <input
                                    type="text"
                                    value={info.accountNumber}
                                    onChange={(e) => setInfo({ ...info, accountNumber: e.target.value })}
                                    className="w-full rounded border px-3 py-2 text-sm"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">예금주</label>
                                <input
                                    type="text"
                                    value={info.accountHolder}
                                    onChange={(e) => setInfo({ ...info, accountHolder: e.target.value })}
                                    className="w-full rounded border px-3 py-2 text-sm"
                                />
                            </div>
                        </div>
                    </div>

                    {/* 인감/로고 */}
                    <div className="rounded border p-4">
                        <h3 className="text-lg font-medium mb-4">인감 / 로고</h3>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">회사 로고</label>
                                <div className="flex items-center gap-2">
                                    <div className="flex h-24 w-24 items-center justify-center rounded border bg-surface-secondary">
                                        {info.logo ? (
                                            <img src={info.logo} alt="로고" className="h-full w-full object-contain" />
                                        ) : (
                                            <span className="text-xs text-text-subtle">로고 없음</span>
                                        )}
                                    </div>
                                    <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary">
                                        <Upload className="h-4 w-4" />
                                        업로드
                                    </button>
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">인감</label>
                                <div className="flex items-center gap-2">
                                    <div className="flex h-24 w-24 items-center justify-center rounded border bg-surface-secondary">
                                        {info.stamp ? (
                                            <img src={info.stamp} alt="인감" className="h-full w-full object-contain" />
                                        ) : (
                                            <span className="text-xs text-text-subtle">인감 없음</span>
                                        )}
                                    </div>
                                    <button className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-surface-secondary">
                                        <Upload className="h-4 w-4" />
                                        업로드
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
