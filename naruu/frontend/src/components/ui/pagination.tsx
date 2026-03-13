"use client";

interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  total?: number;
  perPage?: number;
  unit?: string;
}

export default function Pagination({
  page,
  totalPages,
  onPageChange,
  total,
  perPage = 20,
  unit = "건",
}: PaginationProps) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
      {total != null ? (
        <span className="text-xs text-gray-500">
          총 {total}
          {unit} 중 {(page - 1) * perPage + 1}-
          {Math.min(page * perPage, total)}
          {unit}
        </span>
      ) : (
        <span className="text-xs text-gray-500">
          {page} / {totalPages} 페이지
        </span>
      )}
      <div className="flex gap-1">
        <button
          onClick={() => onPageChange(Math.max(1, page - 1))}
          disabled={page <= 1}
          aria-label="이전 페이지"
          className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
        >
          이전
        </button>
        <button
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
          disabled={page >= totalPages}
          aria-label="다음 페이지"
          className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
        >
          다음
        </button>
      </div>
    </div>
  );
}
