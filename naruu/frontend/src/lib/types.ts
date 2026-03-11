/** Shared TypeScript types matching backend schemas. */

export interface Customer {
  id: number;
  name_ja: string;
  name_ko: string | null;
  email: string | null;
  phone: string | null;
  line_user_id: string | null;
  nationality: string;
  visa_type: string | null;
  first_visit_date: string | null;
  preferred_language: string;
  notes: string | null;
  tags: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface CustomerListResponse {
  items: Customer[];
  total: number;
  page: number;
  page_size: number;
}

export interface JourneyEvent {
  id: number;
  event_type: "reservation" | "order" | "review" | "line_message";
  title: string;
  description: string | null;
  status: string | null;
  date: string;
}

export interface CustomerDetail extends Customer {
  journey: JourneyEvent[];
  stats: {
    total_orders: number;
    total_revenue: number;
    total_reservations: number;
    total_reviews: number;
    total_messages: number;
  };
}

// --- Package Types ---

export type PackageCategory = "medical" | "tourism" | "combo" | "goods";
export type CurrencyType = "JPY" | "KRW";

export interface Package {
  id: number;
  name_ja: string;
  name_ko: string;
  description_ja: string | null;
  description_ko: string | null;
  category: PackageCategory;
  base_price: number | null;
  currency: CurrencyType;
  duration_days: number | null;
  includes: string[] | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PackageListResponse {
  items: Package[];
  total: number;
  page: number;
  per_page: number;
}

export interface PackageCreate {
  name_ja: string;
  name_ko: string;
  description_ja?: string;
  description_ko?: string;
  category: PackageCategory;
  base_price?: number;
  currency?: CurrencyType;
  duration_days?: number;
  includes?: string[];
  is_active?: boolean;
}

export interface QuoteItem {
  package_id: number;
  quantity: number;
  custom_price?: number;
}

export interface QuoteRequest {
  items: QuoteItem[];
  target_currency: CurrencyType;
  customer_name?: string;
  notes?: string;
  discount_percent?: number;
}

export interface QuoteLineItem {
  package_name_ja: string;
  package_name_ko: string;
  category: PackageCategory;
  quantity: number;
  unit_price: number;
  subtotal: number;
  currency: CurrencyType;
}

export interface QuoteResponse {
  line_items: QuoteLineItem[];
  subtotal: number;
  discount_percent: number;
  discount_amount: number;
  total: number;
  target_currency: CurrencyType;
  exchange_rate: number | null;
  total_converted: number | null;
  converted_currency: CurrencyType | null;
  customer_name: string | null;
  notes: string | null;
  generated_at: string;
}

export interface RecommendResponse {
  recommendation: string;
  suggested_package_ids: number[];
}

// --- Tour Route Types ---

export type RouteStatus = "draft" | "published" | "archived";

export interface Waypoint {
  order: number;
  place_id?: string;
  name_ja: string;
  name_ko: string;
  lat: number;
  lng: number;
  category: string;
  stay_minutes: number;
  notes?: string;
  partner_id?: number;
}

export interface RouteLeg {
  from: string;
  to: string;
  distance_km: number;
  duration_minutes: number;
  polyline: string;
}

export interface RouteData {
  total_distance_km: number;
  total_duration_minutes: number;
  legs: RouteLeg[];
  overview_polyline?: string;
  waypoint_order?: number[];
}

export interface TourRoute {
  id: number;
  name_ja: string;
  name_ko: string;
  description_ja: string | null;
  description_ko: string | null;
  waypoints: Waypoint[] | null;
  route_data: RouteData | null;
  status: RouteStatus;
  total_duration_minutes: number | null;
  total_distance_km: number | null;
  tags: string[] | null;
  is_template: boolean;
  customer_id: number | null;
  package_id: number | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface TourRouteListResponse {
  items: TourRoute[];
  total: number;
  page: number;
  per_page: number;
}

export interface PlaceResult {
  place_id: string;
  name: string;
  address: string;
  lat: number;
  lng: number;
  rating: number | null;
  types: string[];
  photo_reference: string | null;
}

// --- Content Types ---

export type ContentSeries = "DaeguTour" | "JCouple" | "Medical" | "Brochure";
export type ContentStatus = "draft" | "review" | "approved" | "published" | "rejected";
export type ContentPlatform = "youtube" | "instagram" | "tiktok";

export interface Content {
  id: number;
  title: string;
  series: ContentSeries;
  script_ja: string | null;
  script_ko: string | null;
  status: ContentStatus;
  video_url: string | null;
  thumbnail_url: string | null;
  platform: ContentPlatform | null;
  published_at: string | null;
  performance_metrics: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ContentListResponse {
  items: Content[];
  total: number;
  page: number;
  per_page: number;
}

export interface ContentCreate {
  title: string;
  series: ContentSeries;
  script_ja?: string;
  script_ko?: string;
  video_url?: string;
  thumbnail_url?: string;
  platform?: ContentPlatform;
}

export interface ContentStats {
  by_status: Record<string, number>;
  by_series: Record<string, number>;
  total: number;
}

// --- Review Types ---

export type ReviewPlatform = "google" | "instagram" | "line" | "naver" | "tabelog";

export interface Review {
  id: number;
  customer_id: number | null;
  partner_id: number | null;
  platform: ReviewPlatform;
  rating: number | null;
  content_ja: string | null;
  content_ko: string | null;
  sentiment_score: number | null;
  is_published: boolean;
  response_text: string | null;
  responded_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReviewListResponse {
  items: Review[];
  total: number;
  page: number;
  per_page: number;
}

export interface ReviewCreate {
  customer_id?: number;
  partner_id?: number;
  platform: ReviewPlatform;
  rating?: number;
  content_ja?: string;
  content_ko?: string;
}

export interface ReviewStats {
  total: number;
  avg_rating: number | null;
  avg_sentiment: number | null;
  awaiting_response: number;
  by_platform: { platform: string; count: number; avg_sentiment: number | null }[];
  sentiment_distribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
}

// --- Partner Types ---

export type PartnerType = "hospital" | "clinic" | "restaurant" | "hotel" | "shop";

export interface Partner {
  id: number;
  name_ko: string;
  name_ja: string | null;
  type: PartnerType;
  address: string | null;
  contact_person: string | null;
  phone: string | null;
  commission_rate: number | null;
  contract_start: string | null;
  contract_end: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PartnerListResponse {
  items: Partner[];
  total: number;
  page: number;
  per_page: number;
}

export interface PartnerCreate {
  name_ko: string;
  name_ja?: string;
  type: PartnerType;
  address?: string;
  contact_person?: string;
  phone?: string;
  commission_rate?: number;
  contract_start?: string;
  contract_end?: string;
  is_active?: boolean;
}

export interface SettlementItem {
  order_id: number;
  customer_id: number;
  total_amount: number;
  currency: string;
  commission_rate: number;
  commission_amount: number;
  created_at: string;
}

export interface SettlementReport {
  partner_id: number;
  partner_name: string;
  period_start: string;
  period_end: string;
  total_orders: number;
  total_revenue: number;
  total_commission: number;
  items: SettlementItem[];
}

export interface PartnerPerformance {
  partner_id: number;
  total_reservations: number;
  total_reviews: number;
  avg_sentiment: number | null;
  total_revenue: number;
  total_commission: number;
}

export interface PartnerStats {
  total: number;
  active: number;
  inactive: number;
  by_type: Record<string, number>;
  expiring_soon: number;
}

// --- Goods Types ---

export type GoodsCategory = "bag" | "accessory" | "souvenir";

export interface GoodsItem {
  id: number;
  name_ja: string;
  name_ko: string;
  description_ja: string | null;
  description_ko: string | null;
  category: GoodsCategory;
  price: number;
  stock_quantity: number;
  image_urls: string[] | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface GoodsListResponse {
  items: GoodsItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface GoodsCreate {
  name_ja: string;
  name_ko: string;
  description_ja?: string;
  description_ko?: string;
  category: GoodsCategory;
  price: number;
  stock_quantity?: number;
  image_urls?: string[];
  is_active?: boolean;
}

export interface GoodsStats {
  total: number;
  active: number;
  low_stock: number;
  out_of_stock: number;
  by_category: Record<string, number>;
  total_inventory_value: number;
}

// --- Finance/ERP Types ---

export type PaymentStatus = "pending" | "paid" | "refunded" | "cancelled";

export interface OrderItem {
  id: number;
  customer_id: number;
  package_id: number | null;
  reservation_id: number | null;
  total_amount: number;
  currency: string;
  payment_status: PaymentStatus;
  payment_method: string | null;
  commission_rate: number | null;
  commission_amount: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrderListResponse {
  items: OrderItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface ExpenseItem {
  id: number;
  category: string;
  vendor_name: string;
  amount: number;
  currency: string;
  description: string | null;
  receipt_url: string | null;
  approved_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface ExpenseListResponse {
  items: ExpenseItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface PnLReport {
  year: number;
  month: number;
  revenue: { gross: number; commission: number; net: number };
  expenses: number;
  profit: number;
  profit_margin: number;
}

export interface OrderSummary {
  year: number;
  month: number;
  total_revenue: number;
  paid_revenue: number;
  total_orders: number;
  paid_orders: number;
  pending_orders: number;
  total_commission: number;
  net_revenue: number;
}

export interface ExpenseSummary {
  year: number;
  month: number;
  total_expenses: number;
  expense_count: number;
  by_category: { category: string; total: number; count: number }[];
}

// --- Customer Types ---

export interface CustomerCreate {
  name_ja: string;
  name_ko?: string;
  email?: string;
  phone?: string;
  line_user_id?: string;
  nationality?: string;
  visa_type?: string;
  first_visit_date?: string;
  preferred_language?: string;
  notes?: string;
  tags?: string[];
}
