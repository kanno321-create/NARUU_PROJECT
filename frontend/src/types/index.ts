// Customer types
export interface Customer {
  id: string;
  code: string;
  name_ja: string;
  name_kr?: string;
  name_en?: string;
  gender?: string;
  birth_date?: string;
  nationality?: string;
  email?: string;
  phone?: string;
  line_user_id?: string;
  instagram_handle?: string;
  language_preference: string;
  medical_interests: string[];
  beauty_interests: string[];
  tourism_interests: string[];
  dietary_restrictions: string[];
  allergies?: string;
  customer_source?: string;
  vip_level: string;
  total_bookings?: number;
  total_spent_jpy?: number;
  is_active: boolean;
  memo?: string;
  created_at: string;
  updated_at: string;
}

// Partner types
export interface Partner {
  id: string;
  code: string;
  name_ja: string;
  name_kr?: string;
  name_en?: string;
  category: string;
  sub_category?: string;
  contact_person?: string;
  phone?: string;
  email?: string;
  address_kr?: string;
  address_ja?: string;
  commission_rate: number;
  contract_start?: string;
  contract_end?: string;
  services: ServiceItem[];
  is_active: boolean;
  memo?: string;
  created_at: string;
  updated_at: string;
}

export interface ServiceItem {
  name: string;
  price_krw?: number;
  price_jpy?: number;
  description?: string;
}

// Product types
export interface Product {
  id: string;
  code: string;
  name_ja: string;
  name_kr?: string;
  name_en?: string;
  product_type: string;
  category?: string;
  description_ja?: string;
  description_kr?: string;
  duration_days: number;
  duration_nights: number;
  min_participants: number;
  max_participants: number;
  base_price_jpy?: number;
  base_price_krw?: number;
  itinerary: ItineraryItem[];
  included_services: string[];
  excluded_services: string[];
  partner_ids: string[];
  meeting_point?: string;
  meeting_time?: string;
  is_active: boolean;
  memo?: string;
  created_at: string;
  updated_at: string;
}

export interface ItineraryItem {
  day: number;
  time?: string;
  title: string;
  description?: string;
  partner_id?: string;
  location?: string;
}

// Booking types
export interface Booking {
  id: string;
  booking_no: string;
  customer_id?: string;
  product_id?: string;
  status: string;
  tour_date?: string;
  tour_end_date?: string;
  num_adults: number;
  num_children: number;
  total_price_jpy?: number;
  total_price_krw?: number;
  exchange_rate?: number;
  payment_method?: string;
  payment_status: string;
  assigned_guide_id?: string;
  special_requests?: string;
  internal_memo?: string;
  created_at: string;
  updated_at: string;
}

// List response
export interface ListResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// Auth types
export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}
