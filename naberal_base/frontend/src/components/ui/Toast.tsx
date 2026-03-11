"use client";

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useRef,
} from "react";

// ── Types ──────────────────────────────────────────────────────────
type ToastType = "success" | "error" | "warning" | "info";

interface ToastItem {
  id: number;
  message: string;
  type: ToastType;
  exiting: boolean;
}

interface ToastContextValue {
  showToast: (message: string, type?: ToastType) => void;
}

// ── Context ────────────────────────────────────────────────────────
const ToastContext = createContext<ToastContextValue | null>(null);

// ── Hook ───────────────────────────────────────────────────────────
export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within a <ToastProvider>");
  }
  return ctx;
}

// ── Colour map (Tailwind classes) ──────────────────────────────────
const TYPE_STYLES: Record<ToastType, string> = {
  success:
    "bg-green-600 text-white",
  error:
    "bg-red-600 text-white",
  warning:
    "bg-amber-500 text-white",
  info:
    "bg-blue-600 text-white",
};

const TYPE_ICONS: Record<ToastType, string> = {
  success: "\u2713",   // checkmark
  error: "\u2717",     // cross
  warning: "\u26A0",   // warning sign
  info: "\u2139",      // info
};

// ── Auto-dismiss duration (ms) ─────────────────────────────────────
const DISMISS_MS = 3000;
const FADE_OUT_MS = 300;

// ── Single Toast ───────────────────────────────────────────────────
function ToastMessage({
  item,
  onDismiss,
}: {
  item: ToastItem;
  onDismiss: (id: number) => void;
}) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    timerRef.current = setTimeout(() => onDismiss(item.id), DISMISS_MS);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [item.id, onDismiss]);

  return (
    <div
      className={`
        flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg text-sm font-medium
        transition-all duration-300 ease-out
        ${item.exiting ? "opacity-0 translate-y-2" : "opacity-100 translate-y-0"}
        ${TYPE_STYLES[item.type]}
      `}
      role="alert"
    >
      <span className="text-base leading-none">{TYPE_ICONS[item.type]}</span>
      <span className="flex-1">{item.message}</span>
      <button
        onClick={() => onDismiss(item.id)}
        className="ml-2 opacity-70 hover:opacity-100 transition-opacity text-lg leading-none"
        aria-label="닫기"
      >
        &times;
      </button>
    </div>
  );
}

// ── Provider ───────────────────────────────────────────────────────
let nextId = 0;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: number) => {
    // Begin fade-out
    setToasts((prev) =>
      prev.map((t) => (t.id === id ? { ...t, exiting: true } : t))
    );
    // Remove after animation
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, FADE_OUT_MS);
  }, []);

  const showToast = useCallback(
    (message: string, type: ToastType = "info") => {
      const id = ++nextId;
      setToasts((prev) => [...prev, { id, message, type, exiting: false }]);
    },
    []
  );

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}

      {/* Toast container — bottom-right, above most overlays */}
      <div
        className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none"
        aria-live="polite"
      >
        {toasts.map((t) => (
          <div key={t.id} className="pointer-events-auto">
            <ToastMessage item={t} onDismiss={dismiss} />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
