-- NARUU AI Tourism Platform - Initial Schema Migration
-- 12 tables in `naruu` schema
-- Run against any PostgreSQL 14+

-- ============================================================
-- Schema creation
-- ============================================================
CREATE SCHEMA IF NOT EXISTS naruu;

-- ============================================================
-- 1. users (내부 직원)
-- ============================================================
CREATE TABLE IF NOT EXISTS naruu.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'staff'
        CHECK (role IN ('owner', 'manager', 'staff', 'guide')),
    phone VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON naruu.users(email);
CREATE INDEX idx_users_role ON naruu.users(role);

-- ============================================================
-- 2. customers (일본인 고객)
-- ============================================================
CREATE TABLE IF NOT EXISTS naruu.customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,          -- NR-C0001
    name_ja VARCHAR(100) NOT NULL,             -- 日本語名
    name_kr VARCHAR(100),                       -- 한국어명
    name_en VARCHAR(100),                       -- English name
    gender VARCHAR(10),
    birth_date DATE,
    nationality VARCHAR(50) DEFAULT '日本',
    email VARCHAR(255),
    phone VARCHAR(30),
    line_user_id VARCHAR(100),                  -- LINE User ID
    instagram_handle VARCHAR(100),
    language_preference VARCHAR(10) DEFAULT 'ja',
    medical_interests JSONB DEFAULT '[]'::jsonb,
    beauty_interests JSONB DEFAULT '[]'::jsonb,
    tourism_interests JSONB DEFAULT '[]'::jsonb,
    dietary_restrictions JSONB DEFAULT '[]'::jsonb,
    allergies TEXT,
    customer_source VARCHAR(50),                -- line/instagram/website/referral/walk_in
    vip_level VARCHAR(20) DEFAULT 'standard',   -- standard/silver/gold/platinum
    total_bookings INT DEFAULT 0,
    total_spent_jpy NUMERIC(12,0) DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    memo TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_customers_code ON naruu.customers(code);
CREATE INDEX idx_customers_line ON naruu.customers(line_user_id);
CREATE INDEX idx_customers_name_ja ON naruu.customers(name_ja);
CREATE INDEX idx_customers_vip ON naruu.customers(vip_level);
CREATE INDEX idx_customers_active ON naruu.customers(is_active);

-- ============================================================
-- 3. partners (거래처)
-- ============================================================
CREATE TABLE IF NOT EXISTS naruu.partners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,           -- NR-P0001
    name_ja VARCHAR(200) NOT NULL,
    name_kr VARCHAR(200),
    name_en VARCHAR(200),
    category VARCHAR(30) NOT NULL
        CHECK (category IN ('medical', 'beauty', 'restaurant', 'shopping', 'experience', 'tourism', 'accommodation', 'transport')),
    sub_category VARCHAR(50),
    contact_person VARCHAR(100),
    phone VARCHAR(30),
    email VARCHAR(255),
    address_kr TEXT,
    address_ja TEXT,
    commission_rate NUMERIC(5,2) DEFAULT 20.00,
    contract_start DATE,
    contract_end DATE,
    services JSONB DEFAULT '[]'::jsonb,         -- [{name, price_krw, price_jpy, description}]
    rating NUMERIC(3,2),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    memo TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_partners_code ON naruu.partners(code);
CREATE INDEX idx_partners_category ON naruu.partners(category);
CREATE INDEX idx_partners_active ON naruu.partners(is_active);

-- ============================================================
-- 4. tour_products (관광 상품)
-- ============================================================
CREATE TABLE IF NOT EXISTS naruu.tour_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,           -- NR-T0001
    name_ja VARCHAR(200) NOT NULL,
    name_kr VARCHAR(200),
    name_en VARCHAR(200),
    product_type VARCHAR(20) NOT NULL DEFAULT 'package'
        CHECK (product_type IN ('package', 'course', 'single_service')),
    category VARCHAR(30),
    description_ja TEXT,
    description_kr TEXT,
    duration_days INT DEFAULT 1,
    duration_nights INT DEFAULT 0,
    min_participants INT DEFAULT 1,
    max_participants INT DEFAULT 10,
    base_price_jpy NUMERIC(12,0),
    base_price_krw NUMERIC(12,0),
    itinerary JSONB DEFAULT '[]'::jsonb,        -- [{day, time, title, description, partner_id, location}]
    included_services JSONB DEFAULT '[]'::jsonb,
    excluded_services JSONB DEFAULT '[]'::jsonb,
    partner_ids JSONB DEFAULT '[]'::jsonb,       -- linked partner UUIDs
    meeting_point TEXT,
    meeting_time VARCHAR(10),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    memo TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_products_code ON naruu.tour_products(code);
CREATE INDEX idx_products_type ON naruu.tour_products(product_type);
CREATE INDEX idx_products_active ON naruu.tour_products(is_active);

-- ============================================================
-- 5. bookings (예약)
-- ============================================================
CREATE TABLE IF NOT EXISTS naruu.bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_no VARCHAR(20) UNIQUE NOT NULL,     -- NR-B2026-0001
    customer_id UUID REFERENCES naruu.customers(id),
    product_id UUID REFERENCES naruu.tour_products(id),
    status VARCHAR(20) NOT NULL DEFAULT 'inquiry'
        CHECK (status IN ('inquiry', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show')),
    tour_date DATE,
    tour_end_date DATE,
    num_adults INT DEFAULT 1,
    num_children INT DEFAULT 0,
    total_price_jpy NUMERIC(12,0),
    total_price_krw NUMERIC(12,0),
    exchange_rate NUMERIC(10,4),                -- JPY/KRW rate at booking time
    payment_method VARCHAR(20)
        CHECK (payment_method IS NULL OR payment_method IN ('credit_card', 'bank_transfer', 'cash', 'line_pay')),
    payment_status VARCHAR(20) DEFAULT 'pending'
        CHECK (payment_status IN ('pending', 'partial', 'paid', 'refunded')),
    assigned_guide_id UUID REFERENCES naruu.users(id),
    special_requests TEXT,
    internal_memo TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_bookings_no ON naruu.bookings(booking_no);
CREATE INDEX idx_bookings_customer ON naruu.bookings(customer_id);
CREATE INDEX idx_bookings_status ON naruu.bookings(status);
CREATE INDEX idx_bookings_tour_date ON naruu.bookings(tour_date);

-- ============================================================
-- 6. booking_items (예약 상세 항목)
-- ============================================================
CREATE TABLE IF NOT EXISTS naruu.booking_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES naruu.bookings(id) ON DELETE CASCADE,
    partner_id UUID REFERENCES naruu.partners(id),
    service_name VARCHAR(200) NOT NULL,
    service_type VARCHAR(30),
    unit_price_jpy NUMERIC(12,0),
    unit_price_krw NUMERIC(12,0),
    quantity INT DEFAULT 1,
    commission_rate NUMERIC(5,2),
    commission_amount_krw NUMERIC(12,0),
    memo TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_booking_items_booking ON naruu.booking_items(booking_id);
CREATE INDEX idx_booking_items_partner ON naruu.booking_items(partner_id);

-- ============================================================
-- 7. venues (관광지/맛집/체험 DB)
-- ============================================================
CREATE TABLE IF NOT EXISTS naruu.venues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name_ja VARCHAR(200) NOT NULL,
    name_kr VARCHAR(200),
    category VARCHAR(30) NOT NULL
        CHECK (category IN ('tourist_spot', 'restaurant', 'cafe', 'beauty', 'experience', 'shopping', 'unique_space', 'accommodation')),
    sub_category VARCHAR(50),
    address_kr TEXT,
    address_ja TEXT,
    latitude NUMERIC(10,7),
    longitude NUMERIC(10,7),
    phone VARCHAR(30),
    website VARCHAR(500),
    instagram VARCHAR(100),
    opening_hours TEXT,
    price_range VARCHAR(20),
    description_ja TEXT,
    description_kr TEXT,
    tags JSONB DEFAULT '[]'::jsonb,             -- ["instagrammable", "daegu_unique", "budget_friendly"]
    photos JSONB DEFAULT '[]'::jsonb,            -- [{url, caption}]
    rating NUMERIC(3,2),
    review_count INT DEFAULT 0,
    discovered_by UUID REFERENCES naruu.users(id),
    discovered_at DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    memo TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_venues_category ON naruu.venues(category);
CREATE INDEX idx_venues_active ON naruu.venues(is_active);

-- ============================================================
-- 8. sales_leads (영업 파이프라인)
-- ============================================================
CREATE TABLE IF NOT EXISTS naruu.sales_leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES naruu.customers(id),
    source VARCHAR(30) NOT NULL,                -- line/instagram/website/referral/walk_in
    stage VARCHAR(20) NOT NULL DEFAULT 'lead'
        CHECK (stage IN ('lead', 'contacted', 'proposal', 'negotiation', 'won', 'lost')),
    title VARCHAR(200),
    estimated_value_jpy NUMERIC(12,0),
    assigned_to UUID REFERENCES naruu.users(id),
    next_action TEXT,
    next_action_date DATE,
    lost_reason TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_leads_stage ON naruu.sales_leads(stage);
CREATE INDEX idx_leads_customer ON naruu.sales_leads(customer_id);
CREATE INDEX idx_leads_assigned ON naruu.sales_leads(assigned_to);

-- ============================================================
-- 9. line_conversations (LINE 대화 기록)
-- ============================================================
CREATE TABLE IF NOT EXISTS naruu.line_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    line_user_id VARCHAR(100) NOT NULL,
    customer_id UUID REFERENCES naruu.customers(id),
    message_type VARCHAR(20) NOT NULL,           -- text/image/sticker/location/audio/video
    direction VARCHAR(10) NOT NULL,              -- inbound/outbound
    content TEXT,
    ai_response TEXT,
    ai_confidence NUMERIC(3,2),
    intent VARCHAR(50),                          -- inquiry/booking/support/general
    handled_by VARCHAR(10) DEFAULT 'ai',         -- ai/human
    replied_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_line_user ON naruu.line_conversations(line_user_id);
CREATE INDEX idx_line_customer ON naruu.line_conversations(customer_id);
CREATE INDEX idx_line_direction ON naruu.line_conversations(direction);
CREATE INDEX idx_line_created ON naruu.line_conversations(created_at);

-- ============================================================
-- 10. transactions (회계 - 이중통화)
-- ============================================================
CREATE TABLE IF NOT EXISTS naruu.transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_no VARCHAR(30) UNIQUE NOT NULL,
    booking_id UUID REFERENCES naruu.bookings(id),
    partner_id UUID REFERENCES naruu.partners(id),
    transaction_type VARCHAR(20) NOT NULL
        CHECK (transaction_type IN ('income', 'expense', 'commission', 'refund')),
    category VARCHAR(50),
    description TEXT,
    amount_jpy NUMERIC(12,0),
    amount_krw NUMERIC(12,0),
    exchange_rate NUMERIC(10,4),
    payment_date DATE,
    payment_method VARCHAR(20),
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'completed', 'cancelled')),
    receipt_url TEXT,
    created_by UUID REFERENCES naruu.users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tx_type ON naruu.transactions(transaction_type);
CREATE INDEX idx_tx_booking ON naruu.transactions(booking_id);
CREATE INDEX idx_tx_partner ON naruu.transactions(partner_id);
CREATE INDEX idx_tx_date ON naruu.transactions(payment_date);

-- ============================================================
-- 11. campaigns (마케팅 캠페인)
-- ============================================================
CREATE TABLE IF NOT EXISTS naruu.campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    campaign_type VARCHAR(30) NOT NULL
        CHECK (campaign_type IN ('instagram', 'line_broadcast', 'email', 'cross_channel')),
    status VARCHAR(20) DEFAULT 'draft'
        CHECK (status IN ('draft', 'scheduled', 'active', 'completed', 'cancelled')),
    target_audience TEXT,
    content_ja TEXT,
    content_kr TEXT,
    scheduled_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    reach INT DEFAULT 0,
    impressions INT DEFAULT 0,
    clicks INT DEFAULT 0,
    conversions INT DEFAULT 0,
    cost_krw NUMERIC(12,0) DEFAULT 0,
    created_by UUID REFERENCES naruu.users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_campaigns_type ON naruu.campaigns(campaign_type);
CREATE INDEX idx_campaigns_status ON naruu.campaigns(status);

-- ============================================================
-- 12. tour_schedules (투어 일정)
-- ============================================================
CREATE TABLE IF NOT EXISTS naruu.tour_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID REFERENCES naruu.bookings(id),
    guide_id UUID REFERENCES naruu.users(id),
    schedule_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    title VARCHAR(200) NOT NULL,
    location TEXT,
    partner_id UUID REFERENCES naruu.partners(id),
    venue_id UUID REFERENCES naruu.venues(id),
    notes TEXT,
    status VARCHAR(20) DEFAULT 'scheduled'
        CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_schedules_date ON naruu.tour_schedules(schedule_date);
CREATE INDEX idx_schedules_guide ON naruu.tour_schedules(guide_id);
CREATE INDEX idx_schedules_booking ON naruu.tour_schedules(booking_id);

-- ============================================================
-- Initial owner user (password: changeme123!)
-- ============================================================
INSERT INTO naruu.users (email, password_hash, name, role)
VALUES (
    'narumi@naruu.jp',
    -- pbkdf2_hmac sha256 hash of 'changeme123!' with salt 'naruu_salt_2026'
    'pbkdf2:sha256:260000$naruu_salt_2026$placeholder_hash_change_on_first_login',
    'YAMADA NARUMI',
    'owner'
) ON CONFLICT (email) DO NOTHING;
