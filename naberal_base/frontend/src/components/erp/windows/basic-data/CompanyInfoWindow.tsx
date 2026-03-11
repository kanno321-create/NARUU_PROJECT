"use client";

import React, { useState, useRef, useEffect } from "react";
import { Save, Building2, Upload, Search } from "lucide-react";
import { useToast } from "@/components/ui/Toast";
import { useERPData } from "@/contexts/ERPDataContext";

interface CompanyInfo {
    companyName: string;
    ceoName: string;
    businessNumber: string;
    businessType: string;
    businessCategory: string;
    zipCode: string;
    address: string;
    addressDetail: string;
    tel: string;
    fax: string;
    email: string;
    website: string;
    logo: string;
}

export function CompanyInfoWindow() {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const { showToast } = useToast();
    const { companyInfo: ctxCompanyInfo, updateCompanyInfo, saveCompanyInfo } = useERPData();

    const [info, setInfo] = useState<CompanyInfo>(() => {
        // 컨텍스트에 값이 있으면 우선 사용, 없으면 기본값
        if (ctxCompanyInfo.companyName) {
            return ctxCompanyInfo;
        }
        const saved = localStorage.getItem("companyInfo");
        if (saved) {
            try {
                return JSON.parse(saved) as CompanyInfo;
            } catch {
                // fall through to defaults
            }
        }
        return {
            companyName: "", ceoName: "", businessNumber: "", businessType: "",
            businessCategory: "", zipCode: "", address: "", addressDetail: "",
            tel: "", fax: "", email: "", website: "", logo: "",
        };
    });

    // 컨텍스트 변경 시 로컬 상태 동기화
    useEffect(() => {
        if (ctxCompanyInfo.companyName) {
            setInfo(ctxCompanyInfo);
        }
    }, [ctxCompanyInfo]);

    const handleChange = (field: keyof CompanyInfo, value: string) => {
        setInfo({ ...info, [field]: value });
    };

    const handleSave = async () => {
        updateCompanyInfo(info);
        const saved = await saveCompanyInfo(info);
        window.dispatchEvent(new CustomEvent("kis-erp-settings-updated"));
        showToast(saved ? "데이터베이스에 저장되었습니다." : "로컬에만 저장되었습니다. (서버 연결 확인 필요)", saved ? "success" : "warning");
    };

    const handleLogoUpload = () => {
        fileInputRef.current?.click();
    };

    const compressImage = (
        file: File,
        maxWidth: number,
        maxHeight: number,
        quality: number,
    ): Promise<string> => {
        return new Promise((resolve, reject) => {
            const img = new Image();
            const objectUrl = URL.createObjectURL(file);
            img.onload = () => {
                URL.revokeObjectURL(objectUrl);
                let { width, height } = img;
                if (width > maxWidth || height > maxHeight) {
                    const ratio = Math.min(maxWidth / width, maxHeight / height);
                    width = Math.round(width * ratio);
                    height = Math.round(height * ratio);
                }
                const canvas = document.createElement("canvas");
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext("2d");
                if (!ctx) {
                    reject(new Error("Canvas context not available"));
                    return;
                }
                ctx.drawImage(img, 0, 0, width, height);
                const compressed = canvas.toDataURL("image/jpeg", quality);
                resolve(compressed);
            };
            img.onerror = () => {
                URL.revokeObjectURL(objectUrl);
                reject(new Error("이미지를 불러올 수 없습니다."));
            };
            img.src = objectUrl;
        });
    };

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const validTypes = ["image/png", "image/jpeg", "image/jpg"];
        if (!validTypes.includes(file.type)) {
            showToast("PNG 또는 JPG 파일만 업로드 가능합니다.", "warning");
            return;
        }

        if (file.size > 2 * 1024 * 1024) {
            showToast("파일 크기는 2MB 이하만 가능합니다.", "warning");
            return;
        }

        const MAX_LOGO_BYTES = 500 * 1024;

        if (file.size > MAX_LOGO_BYTES) {
            try {
                const compressed = await compressImage(file, 200, 200, 0.8);
                setInfo((prev) => ({ ...prev, logo: compressed }));
            } catch (err) {
                showToast(
                    err instanceof Error
                        ? err.message
                        : "로고 압축에 실패했습니다.",
                    "error",
                );
            }
        } else {
            const reader = new FileReader();
            reader.onload = (event) => {
                const base64 = event.target?.result as string;
                setInfo((prev) => ({ ...prev, logo: base64 }));
            };
            reader.readAsDataURL(file);
        }

        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    const fallbackManualAddress = () => {
        const manualZip = prompt("Daum 주소검색에 연결할 수 없습니다. 수동으로 입력해주세요.\n\n우편번호:");
        if (manualZip === null) return;
        const manualAddr = prompt("주소를 입력하세요:");
        if (manualAddr === null) return;
        setInfo((prev) => ({
            ...prev,
            zipCode: manualZip.trim(),
            address: manualAddr.trim(),
        }));
    };

    const handleAddressSearch = () => {
        const openPostcode = () => {
            try {
                const daum = window.daum;
                if (!daum) return;
                new daum.Postcode({
                    oncomplete: (data: DaumPostcodeResult) => {
                        const fullAddress =
                            data.userSelectedType === "R"
                                ? data.roadAddress
                                : data.jibunAddress;
                        setInfo((prev) => ({
                            ...prev,
                            zipCode: data.zonecode,
                            address: fullAddress,
                        }));
                    },
                }).open();
            } catch {
                fallbackManualAddress();
            }
        };

        if (window.daum?.Postcode) {
            openPostcode();
        } else {
            const script = document.createElement("script");
            script.src =
                "https://t1.daumcdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js";
            script.onload = () => openPostcode();
            script.onerror = () => fallbackManualAddress();
            document.head.appendChild(script);
        }
    };

    return (
        <div className="flex h-full flex-col">
            {/* 툴바 */}
            <div className="flex items-center gap-2 border-b bg-surface px-4 py-2">
                <button
                    onClick={handleSave}
                    className="flex items-center gap-1 rounded bg-brand px-3 py-1.5 text-sm text-white hover:bg-brand-dark"
                >
                    <Save className="h-4 w-4" />
                    저장
                </button>
            </div>

            {/* 폼 */}
            <div className="flex-1 overflow-auto p-4">
                <div className="mx-auto max-w-3xl space-y-6">
                    {/* 회사 로고 */}
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/png,image/jpeg,image/jpg"
                        onChange={handleFileChange}
                        className="hidden"
                    />
                    <div className="flex items-center gap-4 rounded-lg border bg-surface-secondary p-4">
                        <div className="flex h-20 w-20 items-center justify-center overflow-hidden rounded-lg border-2 border-dashed">
                            {info.logo ? (
                                <img
                                    src={info.logo}
                                    alt="회사 로고"
                                    className="h-full w-full object-contain"
                                />
                            ) : (
                                <Building2 className="h-10 w-10 text-text-subtle" />
                            )}
                        </div>
                        <div>
                            <p className="font-medium">회사 로고</p>
                            <p className="text-sm text-text-subtle">권장: 200x200px, PNG/JPG (최대 2MB, 500KB 초과 시 자동 압축)</p>
                            <div className="mt-2 flex gap-2">
                                <button
                                    onClick={handleLogoUpload}
                                    className="flex items-center gap-1 rounded border px-3 py-1 text-sm hover:bg-surface"
                                >
                                    <Upload className="h-3 w-3" />
                                    로고 업로드
                                </button>
                                {info.logo && (
                                    <button
                                        onClick={() => setInfo((prev) => ({ ...prev, logo: "" }))}
                                        className="rounded border px-3 py-1 text-sm text-red-500 hover:bg-red-50"
                                    >
                                        삭제
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* 기본 정보 */}
                    <div className="rounded-lg border p-4">
                        <h3 className="mb-4 font-medium">기본 정보</h3>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="mb-1 block text-sm font-medium">회사명 *</label>
                                <input
                                    type="text"
                                    value={info.companyName}
                                    onChange={(e) => handleChange("companyName", e.target.value)}
                                    className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:outline-none"
                                />
                            </div>
                            <div>
                                <label className="mb-1 block text-sm font-medium">대표자명 *</label>
                                <input
                                    type="text"
                                    value={info.ceoName}
                                    onChange={(e) => handleChange("ceoName", e.target.value)}
                                    className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:outline-none"
                                />
                            </div>
                            <div>
                                <label className="mb-1 block text-sm font-medium">사업자등록번호 *</label>
                                <input
                                    type="text"
                                    value={info.businessNumber}
                                    onChange={(e) => handleChange("businessNumber", e.target.value)}
                                    className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:outline-none"
                                    placeholder="000-00-00000"
                                />
                            </div>
                            <div>
                                <label className="mb-1 block text-sm font-medium">업태</label>
                                <input
                                    type="text"
                                    value={info.businessType}
                                    onChange={(e) => handleChange("businessType", e.target.value)}
                                    className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:outline-none"
                                />
                            </div>
                            <div className="col-span-2">
                                <label className="mb-1 block text-sm font-medium">종목</label>
                                <input
                                    type="text"
                                    value={info.businessCategory}
                                    onChange={(e) => handleChange("businessCategory", e.target.value)}
                                    className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:outline-none"
                                />
                            </div>
                        </div>
                    </div>

                    {/* 주소 정보 */}
                    <div className="rounded-lg border p-4">
                        <h3 className="mb-4 font-medium">주소 정보</h3>
                        <div className="grid grid-cols-4 gap-4">
                            <div>
                                <label className="mb-1 block text-sm font-medium">우편번호</label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={info.zipCode}
                                        onChange={(e) => handleChange("zipCode", e.target.value)}
                                        className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:outline-none"
                                    />
                                    <button
                                        onClick={handleAddressSearch}
                                        className="flex items-center gap-1 whitespace-nowrap rounded border px-3 py-2 text-sm hover:bg-surface"
                                    >
                                        <Search className="h-3 w-3" />
                                        주소 검색
                                    </button>
                                </div>
                            </div>
                            <div className="col-span-3">
                                <label className="mb-1 block text-sm font-medium">주소</label>
                                <input
                                    type="text"
                                    value={info.address}
                                    onChange={(e) => handleChange("address", e.target.value)}
                                    className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:outline-none"
                                />
                            </div>
                            <div className="col-span-4">
                                <label className="mb-1 block text-sm font-medium">상세주소</label>
                                <input
                                    type="text"
                                    value={info.addressDetail}
                                    onChange={(e) => handleChange("addressDetail", e.target.value)}
                                    className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:outline-none"
                                />
                            </div>
                        </div>
                    </div>

                    {/* 연락처 정보 */}
                    <div className="rounded-lg border p-4">
                        <h3 className="mb-4 font-medium">연락처 정보</h3>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="mb-1 block text-sm font-medium">대표전화</label>
                                <input
                                    type="text"
                                    value={info.tel}
                                    onChange={(e) => handleChange("tel", e.target.value)}
                                    className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:outline-none"
                                />
                            </div>
                            <div>
                                <label className="mb-1 block text-sm font-medium">팩스</label>
                                <input
                                    type="text"
                                    value={info.fax}
                                    onChange={(e) => handleChange("fax", e.target.value)}
                                    className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:outline-none"
                                />
                            </div>
                            <div>
                                <label className="mb-1 block text-sm font-medium">이메일</label>
                                <input
                                    type="email"
                                    value={info.email}
                                    onChange={(e) => handleChange("email", e.target.value)}
                                    className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:outline-none"
                                />
                            </div>
                            <div>
                                <label className="mb-1 block text-sm font-medium">홈페이지</label>
                                <input
                                    type="text"
                                    value={info.website}
                                    onChange={(e) => handleChange("website", e.target.value)}
                                    className="w-full rounded border px-3 py-2 text-sm focus:border-brand focus:outline-none"
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
