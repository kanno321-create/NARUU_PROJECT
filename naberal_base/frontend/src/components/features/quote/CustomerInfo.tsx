"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import { api, ERPCustomer } from "@/lib/api";

interface CustomerInfoProps {
    data: any;
    onChange: (data: any) => void;
}

interface CustomerOption {
    id: string;
    name: string;
    contact: string;
    email: string;
    address: string;
}

export function CustomerInfo({ data, onChange }: CustomerInfoProps) {
    const [isOpen, setIsOpen] = useState(true);
    const [customers, setCustomers] = useState<CustomerOption[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");

    // 고객 목록 로드 (API 연동)
    const loadCustomers = useCallback(async (search?: string) => {
        setIsLoading(true);
        try {
            const response = await api.erp.customers.list({
                search: search || undefined,
                is_active: true,
                limit: 50,
            });

            const mappedCustomers: CustomerOption[] = response.items.map((c: ERPCustomer) => ({
                id: c.id,
                name: c.name,
                contact: c.phone || "",
                email: c.email || "",
                address: c.address || "",
            }));

            setCustomers(mappedCustomers);
        } catch (error) {
            // API 실패 시 빈 배열 유지 (조용히 실패)
            setCustomers([]);
        } finally {
            setIsLoading(false);
        }
    }, []);

    // 컴포넌트 마운트 시 고객 목록 로드
    useEffect(() => {
        loadCustomers();
    }, [loadCustomers]);

    // 검색어 변경 시 디바운스로 API 호출
    useEffect(() => {
        const timer = setTimeout(() => {
            if (searchTerm.length >= 1) {
                loadCustomers(searchTerm);
            } else {
                loadCustomers();
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [searchTerm, loadCustomers]);

    const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setSearchTerm(value);

        // 자동완성 매칭 확인 (정확한 이름 매칭)
        const match = customers.find((c) => c.name === value);

        if (match) {
            // 매칭된 고객 정보 전체 자동완성
            onChange({
                ...data,
                customerId: match.id,
                companyName: match.name,
                contact: match.contact,
                email: match.email,
                address: match.address,
            });
        } else {
            // 매칭 없으면 업체명만 업데이트
            onChange({ ...data, companyName: value, customerId: null });
        }
    };

    return (
        <Card className="mb-4">
            <CardHeader
                className="cursor-pointer flex-row items-center justify-between bg-surface-tertiary py-3"
                onClick={() => setIsOpen(!isOpen)}
            >
                <CardTitle className="text-sm font-semibold">고객정보</CardTitle>
                <div className="flex items-center gap-2">
                    {isLoading && <Loader2 className="h-3 w-3 animate-spin text-text-subtle" />}
                    {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </div>
            </CardHeader>
            {isOpen && (
                <CardContent className="pt-4">
                    <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-text-subtle">업체명</label>
                            <Input
                                placeholder="업체명을 입력하세요"
                                value={data.companyName || ""}
                                onChange={handleNameChange}
                                list="customer-list"
                            />
                            <datalist id="customer-list">
                                {customers.map((c) => (
                                    <option key={c.id} value={c.name} />
                                ))}
                            </datalist>
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-text-subtle">연락처</label>
                            <Input
                                placeholder="연락처를 입력하세요"
                                value={data.contact || ""}
                                onChange={(e) => onChange({ ...data, contact: e.target.value })}
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-text-subtle">이메일</label>
                            <Input
                                placeholder="이메일을 입력하세요"
                                value={data.email || ""}
                                onChange={(e) => onChange({ ...data, email: e.target.value })}
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-text-subtle">주소</label>
                            <Input
                                placeholder="주소를 입력하세요"
                                value={data.address || ""}
                                onChange={(e) => onChange({ ...data, address: e.target.value })}
                            />
                        </div>
                    </div>
                </CardContent>
            )}
        </Card>
    );
}
