-- Create catalog_items table for product catalog management
-- Purpose: Enable real catalog API testing with database
-- Date: 2025-10-18

CREATE TABLE IF NOT EXISTS public.catalog_items (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,  -- 'breaker' or 'enclosure'
    kind VARCHAR(50) NOT NULL,      -- 'MCCB', 'ELB', 'enclosure', etc.

    -- Basic info
    brand VARCHAR(100) NOT NULL,
    series VARCHAR(100),            -- '경제형', '표준형', NULL
    model VARCHAR(100) NOT NULL,

    -- Specifications (JSONB for flexibility)
    specs JSONB NOT NULL DEFAULT '{}',
    -- Breaker specs: poles, current_a, frame_af, breaking_capacity_ka
    -- Enclosure specs: type, material, width_mm, height_mm, depth_mm

    -- Dimensions (for all items)
    width_mm INTEGER,
    height_mm INTEGER,
    depth_mm INTEGER,

    -- Pricing
    price INTEGER NOT NULL,  -- 견적가 (원)

    -- Metadata
    search_keywords TEXT[] NOT NULL DEFAULT '{}',
    source_line INTEGER,
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for fast querying
CREATE INDEX IF NOT EXISTS idx_catalog_items_category ON public.catalog_items(category);
CREATE INDEX IF NOT EXISTS idx_catalog_items_kind ON public.catalog_items(kind);
CREATE INDEX IF NOT EXISTS idx_catalog_items_brand ON public.catalog_items(brand);
CREATE INDEX IF NOT EXISTS idx_catalog_items_model ON public.catalog_items(model);
CREATE UNIQUE INDEX IF NOT EXISTS idx_catalog_items_sku ON public.catalog_items(sku);

-- GIN index for search_keywords array
CREATE INDEX IF NOT EXISTS idx_catalog_items_search_keywords ON public.catalog_items USING gin(search_keywords);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_catalog_items_updated_at ON public.catalog_items;
CREATE TRIGGER update_catalog_items_updated_at
BEFORE UPDATE ON public.catalog_items
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO public.catalog_items (sku, category, kind, brand, series, model, specs, width_mm, height_mm, depth_mm, price, search_keywords)
VALUES
    ('SBS-54-100A', 'breaker', 'MCCB', '상도차단기', '표준형', 'SBS-54',
     '{"poles": 4, "current_a": 100, "frame_af": 50, "breaking_capacity_ka": 25.0}'::jsonb,
     100, 130, 60, 28500,
     ARRAY['SBS-54', '4P', '100A', '50AF', 'MCCB', '표준형', '상도차단기']),

    ('SBE-102-60A', 'breaker', 'MCCB', '상도차단기', '경제형', 'SBE-102',
     '{"poles": 2, "current_a": 60, "frame_af": 100, "breaking_capacity_ka": 14.0}'::jsonb,
     50, 130, 60, 12500,
     ARRAY['SBE-102', '2P', '60A', '100AF', 'MCCB', '경제형', '상도차단기']),

    ('HB-600800200', 'enclosure', 'enclosure', '한국산업', NULL, 'HB-600*800*200',
     '{"type": "옥내노출", "material": "STEEL 1.6T"}'::jsonb,
     600, 800, 200, 180000,
     ARRAY['HB-600*800*200', '600x800x200', '옥내노출', 'STEEL 1.6T', '한국산업'])
ON CONFLICT (sku) DO NOTHING;

-- Verify table creation
SELECT COUNT(*) as total_items FROM public.catalog_items;
