"use client";

import React, { useState } from "react";
import { Search } from "lucide-react";

interface ProductInventoryCarryoverWindowProps {
    onClose: () => void;
}

interface ProductInventoryCarryover {
    id: string;
    productCode: string;
    productName: string;
    spec: string;
    detailSpec: string;
    carryoverDate: string;
    carryoverQty: number;
    carryoverPrice: number;
}

// 이지판매재고관리 원본 데이터 100% 복제 (2025-12-05 스크린샷 기준)
const ORIGINAL_DATA: ProductInventoryCarryover[] = [
    { id: "1", productCode: "s0001", productName: "핸드폰케이스", spec: "10*10", detailSpec: "100*100", carryoverDate: "2025-12-05", carryoverQty: 100, carryoverPrice: 10000 },
    { id: "2", productCode: "s0002", productName: "노트북케이스", spec: "20*25", detailSpec: "200*300", carryoverDate: "2025-12-05", carryoverQty: 150, carryoverPrice: 15000 },
    { id: "3", productCode: "s0003", productName: "키보드케이스", spec: "300*400", detailSpec: "350*450", carryoverDate: "2025-12-05", carryoverQty: 200, carryoverPrice: 4500 },
];

export default function ProductInventoryCarryoverWindow({ onClose }: ProductInventoryCarryoverWindowProps) {
    const [data] = useState<ProductInventoryCarryover[]>(ORIGINAL_DATA);
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedDate, setSelectedDate] = useState("2025년 12월 05일");

    const filteredData = data.filter(
        (item) =>
            item.productName.includes(searchQuery) ||
            item.productCode.includes(searchQuery)
    );

    return (
        <div className="flex h-full flex-col bg-[#d4d0c8]">
            {/* 검색 영역 */}
            <div className="flex items-center gap-4 border-b bg-[#d4d0c8] px-4 py-2">
                <div className="flex items-center gap-2">
                    <label className="text-sm">상품명:</label>
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-40 border border-gray-400 px-2 py-1 text-sm"
                    />
                    <button className="border border-gray-400 bg-[#d4d0c8] px-3 py-1 text-sm hover:bg-gray-300">
                        검 색(F)
                    </button>
                </div>
                <div className="ml-auto flex items-center gap-2">
                    <select
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                        className="border border-gray-400 px-2 py-1 text-sm"
                    >
                        <option>2025년 12월 05일</option>
                    </select>
                    <button className="border border-gray-400 bg-[#d4d0c8] px-3 py-1 text-sm hover:bg-gray-300">
                        날짜전체입력
                    </button>
                </div>
            </div>

            {/* 테이블 */}
            <div className="flex-1 overflow-auto">
                <table className="w-full border-collapse text-sm">
                    <thead className="sticky top-0 bg-[#c0c0c0]">
                        <tr>
                            <th className="border border-gray-400 px-3 py-1.5 text-left font-normal">상품코드</th>
                            <th className="border border-gray-400 px-3 py-1.5 text-left font-normal">상품명</th>
                            <th className="border border-gray-400 px-3 py-1.5 text-left font-normal">규격</th>
                            <th className="border border-gray-400 px-3 py-1.5 text-left font-normal">상세규격</th>
                            <th className="border border-gray-400 px-3 py-1.5 text-left font-normal">이월일자</th>
                            <th className="border border-gray-400 px-3 py-1.5 text-right font-normal">이월수량</th>
                            <th className="border border-gray-400 px-3 py-1.5 text-right font-normal">이월단가</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredData.map((item) => (
                            <tr key={item.id} className="hover:bg-[#316ac5] hover:text-white">
                                <td className="border border-gray-300 px-3 py-1">{item.productCode}</td>
                                <td className="border border-gray-300 px-3 py-1">{item.productName}</td>
                                <td className="border border-gray-300 px-3 py-1">{item.spec}</td>
                                <td className="border border-gray-300 px-3 py-1">{item.detailSpec}</td>
                                <td className="border border-gray-300 px-3 py-1">{item.carryoverDate}</td>
                                <td className="border border-gray-300 px-3 py-1 text-right text-blue-600">{item.carryoverQty}</td>
                                <td className="border border-gray-300 px-3 py-1 text-right text-blue-600">{item.carryoverPrice.toLocaleString()}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
