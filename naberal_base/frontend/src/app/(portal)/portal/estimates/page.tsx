"use client";

import React, { useState } from "react";
import Link from "next/link";

interface EstimateItem {
  id: string;
  date: string;
  projectName: string;
  panelType: string;
  totalAmount: number;
  status: "완료" | "검토중" | "만료";
}

export default function PortalEstimatesPage() {
  const [estimates] = useState<EstimateItem[]>([]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-900">내 견적 목록</h1>
        <Link
          href="/estimate"
          className="px-4 py-2 bg-blue-700 text-white text-sm font-medium rounded-lg hover:bg-blue-800 transition-colors"
        >
          + 새 견적
        </Link>
      </div>

      {estimates.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <div className="text-5xl mb-4">📋</div>
          <h2 className="text-lg font-semibold text-slate-700 mb-2">
            견적 내역이 없습니다
          </h2>
          <p className="text-slate-500 mb-6">
            AI 견적 시스템으로 빠르게 견적을 받아보세요.
          </p>
          <Link
            href="/estimate"
            className="inline-flex items-center px-6 py-3 bg-blue-700 text-white font-medium rounded-lg hover:bg-blue-800 transition-colors"
          >
            AI 견적 시작하기
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-slate-600">날짜</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">프로젝트명</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">분전반 종류</th>
                <th className="text-right px-4 py-3 font-medium text-slate-600">견적금액</th>
                <th className="text-center px-4 py-3 font-medium text-slate-600">상태</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {estimates.map((est) => (
                <tr key={est.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-3 text-slate-600">{est.date}</td>
                  <td className="px-4 py-3 font-medium text-slate-900">{est.projectName}</td>
                  <td className="px-4 py-3 text-slate-600">{est.panelType}</td>
                  <td className="px-4 py-3 text-right font-medium">
                    {est.totalAmount.toLocaleString()}원
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                        est.status === "완료"
                          ? "bg-green-100 text-green-700"
                          : est.status === "검토중"
                          ? "bg-amber-100 text-amber-700"
                          : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {est.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                      상세
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
