"use client";

import React from "react";
import { useAuth } from "@/contexts/AuthContext";

export default function PortalProfilePage() {
  const { user } = useAuth();

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900 mb-6">내 정보</h1>

      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-slate-500 mb-1">
              이름
            </label>
            <p className="text-slate-900 font-medium">
              {user?.full_name || "-"}
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-500 mb-1">
              이메일
            </label>
            <p className="text-slate-900">{user?.email || "-"}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-500 mb-1">
              역할
            </label>
            <p className="text-slate-900">{user?.role || "-"}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-500 mb-1">
              가입일
            </label>
            <p className="text-slate-900">
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString("ko-KR")
                : "-"}
            </p>
          </div>
        </div>

        <hr className="my-6 border-slate-200" />

        <div>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">연락처</h2>
          <p className="text-sm text-slate-500">
            연락처 정보 변경은 고객지원으로 문의해 주세요.
          </p>
          <div className="mt-3 flex items-center gap-2 text-sm">
            <span className="text-slate-600">전화:</span>
            <a href="tel:053-792-1410" className="text-blue-600 hover:underline">
              053-792-1410
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
