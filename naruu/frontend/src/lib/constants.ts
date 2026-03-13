/**
 * Shared label/color maps used across multiple pages.
 * Single Source of Truth for all UI constants.
 */

import type {
  PackageCategory,
  ContentStatus,
  ContentSeries,
  ReviewPlatform,
  PartnerType,
  GoodsCategory,
  RouteStatus,
  PaymentStatus,
} from "./types";

// === Dashboard / Reservation Type Labels ===
export const RESERVATION_TYPE_LABELS: Record<string, string> = {
  medical: "의료",
  tourism: "관광",
  restaurant: "식당",
  goods: "굿즈",
};

// === Dashboard / Reservation Status Labels ===
export const RESERVATION_STATUS_LABELS: Record<string, string> = {
  pending: "대기",
  confirmed: "확정",
  completed: "완료",
  cancelled: "취소",
};

// === Package Category ===
export const CATEGORY_LABELS: Record<PackageCategory, string> = {
  medical: "의료",
  tourism: "관광",
  combo: "콤보",
  goods: "굿즈",
};

export const CATEGORY_COLORS: Record<PackageCategory, string> = {
  medical: "bg-rose-100 text-rose-700",
  tourism: "bg-sky-100 text-sky-700",
  combo: "bg-violet-100 text-violet-700",
  goods: "bg-amber-100 text-amber-700",
};

// === Content Status ===
export const CONTENT_STATUS_LABELS: Record<ContentStatus, string> = {
  draft: "초안",
  review: "검토 중",
  approved: "승인됨",
  published: "게시됨",
  rejected: "반려",
};

export const CONTENT_STATUS_COLORS: Record<ContentStatus, string> = {
  draft: "bg-gray-100 text-gray-600",
  review: "bg-amber-100 text-amber-700",
  approved: "bg-green-100 text-green-700",
  published: "bg-blue-100 text-blue-700",
  rejected: "bg-red-100 text-red-600",
};

// === Content Series ===
export const SERIES_LABELS: Record<ContentSeries, string> = {
  DaeguTour: "대구투어",
  JCouple: "J커플",
  Medical: "의료",
  Brochure: "브로슈어",
};

// === Content Platform ===
export const CONTENT_PLATFORM_LABELS: Record<string, string> = {
  youtube: "YouTube",
  instagram: "Instagram",
  tiktok: "TikTok",
};

// === Review Platform ===
export const PLATFORM_LABELS: Record<ReviewPlatform, string> = {
  google: "Google",
  instagram: "Instagram",
  line: "LINE",
  naver: "Naver",
  tabelog: "食べログ",
};

export const PLATFORM_COLORS: Record<ReviewPlatform, string> = {
  google: "bg-blue-100 text-blue-700",
  instagram: "bg-pink-100 text-pink-700",
  line: "bg-green-100 text-green-700",
  naver: "bg-emerald-100 text-emerald-700",
  tabelog: "bg-orange-100 text-orange-700",
};

// === Partner Type ===
export const PARTNER_TYPE_LABELS: Record<PartnerType, string> = {
  hospital: "병원",
  clinic: "클리닉",
  restaurant: "레스토랑",
  hotel: "호텔",
  shop: "샵",
};

export const PARTNER_TYPE_COLORS: Record<PartnerType, string> = {
  hospital: "bg-red-100 text-red-700",
  clinic: "bg-pink-100 text-pink-700",
  restaurant: "bg-orange-100 text-orange-700",
  hotel: "bg-blue-100 text-blue-700",
  shop: "bg-purple-100 text-purple-700",
};

// === Goods Category ===
export const CAT_LABELS: Record<GoodsCategory, string> = {
  bag: "가방",
  accessory: "액세서리",
  souvenir: "기념품",
};

export const CAT_COLORS: Record<GoodsCategory, string> = {
  bag: "bg-indigo-100 text-indigo-700",
  accessory: "bg-pink-100 text-pink-700",
  souvenir: "bg-amber-100 text-amber-700",
};

// === Route Status ===
export const ROUTE_STATUS_LABELS: Record<RouteStatus, string> = {
  draft: "초안",
  published: "공개",
  archived: "보관",
};

export const ROUTE_STATUS_COLORS: Record<RouteStatus, string> = {
  draft: "bg-gray-100 text-gray-600",
  published: "bg-green-100 text-green-700",
  archived: "bg-red-100 text-red-600",
};

// === Waypoint Category (for route detail) ===
export const WAYPOINT_CATEGORY_LABELS: Record<string, string> = {
  tourism: "관광",
  medical: "의료",
  restaurant: "맛집",
  hotel: "숙박",
  shopping: "쇼핑",
};

// === Finance / Payment Status ===
export const PAYMENT_STATUS_LABELS: Record<PaymentStatus, string> = {
  pending: "대기",
  paid: "결제완료",
  refunded: "환불",
  cancelled: "취소",
};

export const PAYMENT_STATUS_COLORS: Record<PaymentStatus, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  paid: "bg-green-100 text-green-700",
  refunded: "bg-blue-100 text-blue-700",
  cancelled: "bg-gray-100 text-gray-500",
};

// === Chart Colors ===
export const PIE_COLORS = ["#3b82f6", "#ef4444", "#f59e0b", "#10b981", "#8b5cf6"];
export const PIE_COLORS_EXTENDED = ["#6366f1", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#ec4899"];
export const SENTIMENT_COLORS = ["#22c55e", "#f59e0b", "#ef4444"];
