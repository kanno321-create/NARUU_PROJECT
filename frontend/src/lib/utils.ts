import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number, currency: 'JPY' | 'KRW' = 'JPY'): string {
  return new Intl.NumberFormat(currency === 'JPY' ? 'ja-JP' : 'ko-KR', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatDate(date: string | Date, locale: string = 'ja'): string {
  return new Intl.DateTimeFormat(locale === 'ja' ? 'ja-JP' : 'ko-KR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(new Date(date));
}
