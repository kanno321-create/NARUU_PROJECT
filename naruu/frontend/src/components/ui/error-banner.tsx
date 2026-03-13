"use client";

interface ErrorBannerProps {
  message: string | null;
}

export default function ErrorBanner({ message }: ErrorBannerProps) {
  if (!message) return null;

  return (
    <div
      role="alert"
      className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm"
    >
      {message}
    </div>
  );
}
