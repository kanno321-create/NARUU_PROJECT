"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { Package } from "@/lib/types";
import { CATEGORY_LABELS } from "@/lib/constants";
import LoadingSpinner from "@/components/ui/loading-spinner";
import ErrorBanner from "@/components/ui/error-banner";

export default function PackageDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [pkg, setPkg] = useState<Package | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await api.get<Package>(`/packages/${params.id}`);
        setPkg(data);
      } catch {
        router.push("/packages");
      } finally {
        setLoading(false);
      }
    })();
  }, [params.id, router]);

  const handleDelete = async () => {
    if (!confirm("이 패키지를 비활성화하시겠습니까?")) return;
    try {
      await api.delete(`/packages/${params.id}`);
      router.push("/packages");
    } catch {
      setError("패키지 비활성화에 실패했습니다.");
    }
  };

  if (loading) {
    return (
      <AppShell>
        <LoadingSpinner text="패키지 로딩 중..." />
      </AppShell>
    );
  }

  if (!pkg) return null;

  const formatPrice = (price: number | null, currency: string) => {
    if (price === null) return "-";
    return currency === "JPY" ? `¥${price.toLocaleString()}` : `₩${price.toLocaleString()}`;
  };

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <div>
          <Link href="/packages" className="text-sm text-naruu-600 hover:underline">
            &larr; 패키지 목록
          </Link>
          <h2 className="text-2xl font-bold text-gray-800 mt-1">{pkg.name_ja}</h2>
          <p className="text-gray-500">{pkg.name_ko}</p>
        </div>
        <div className="flex gap-2">
          <Link
            href={`/packages/${pkg.id}/edit`}
            className="px-4 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 transition text-sm font-medium"
          >
            수정
          </Link>
          <button
            onClick={handleDelete}
            className="px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition text-sm font-medium"
          >
            비활성화
          </button>
        </div>
      </div>

      <ErrorBanner message={error} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Info Card */}
        <div className="bg-white rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="font-semibold text-gray-700">기본 정보</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">카테고리</span>
              <span className="font-medium">{CATEGORY_LABELS[pkg.category]}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">가격</span>
              <span className="font-medium font-mono">{formatPrice(pkg.base_price, pkg.currency)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">기간</span>
              <span className="font-medium">{pkg.duration_days ? `${pkg.duration_days}일` : "-"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">상태</span>
              <span className={`font-medium ${pkg.is_active ? "text-green-600" : "text-gray-400"}`}>
                {pkg.is_active ? "활성" : "비활성"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">등록일</span>
              <span>{new Date(pkg.created_at).toLocaleDateString("ko-KR")}</span>
            </div>
          </div>
        </div>

        {/* Includes */}
        <div className="bg-white rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="font-semibold text-gray-700">포함사항</h3>
          {pkg.includes && pkg.includes.length > 0 ? (
            <ul className="space-y-2">
              {pkg.includes.map((item) => (
                <li key={item} className="flex items-center gap-2 text-sm text-gray-600">
                  <span className="w-1.5 h-1.5 bg-naruu-500 rounded-full" />
                  {item}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-400">포함사항이 없습니다</p>
          )}
        </div>

        {/* Description */}
        <div className="bg-white rounded-xl p-6 shadow-sm space-y-4 md:col-span-2">
          <h3 className="font-semibold text-gray-700">설명</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-400 mb-1">일본어</p>
              <p className="text-gray-700 whitespace-pre-wrap">
                {pkg.description_ja || "설명이 없습니다"}
              </p>
            </div>
            <div>
              <p className="text-gray-400 mb-1">한국어</p>
              <p className="text-gray-700 whitespace-pre-wrap">
                {pkg.description_ko || "설명이 없습니다"}
              </p>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
