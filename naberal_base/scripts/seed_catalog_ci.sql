-- CI Catalog Seed Data (Schema-Correct for Gate 4)
-- Zero-Mock Principle: Real data only
-- Schema: sku, category, kind, brand, series, model, spec (JSONB), price, created_at, updated_at

-- Breakers (15A~1200A complete range)
INSERT INTO shared.catalog_items (sku, category, kind, brand, series, model, spec, price, created_at, updated_at)
VALUES
  -- 상도 경제형 MCCB
  ('SBE-52-15A', 'breaker', 'MCCB', '상도', '경제형', 'SBE-52', '{"poles": 2, "frame_af": 50, "rated_current": 15, "breaking_capacity_ka": 14}'::jsonb, 8500, NOW(), NOW()),
  ('SBE-52-20A', 'breaker', 'MCCB', '상도', '경제형', 'SBE-52', '{"poles": 2, "frame_af": 50, "rated_current": 20, "breaking_capacity_ka": 14}'::jsonb, 8500, NOW(), NOW()),
  ('SBE-52-30A', 'breaker', 'MCCB', '상도', '경제형', 'SBE-52', '{"poles": 2, "frame_af": 50, "rated_current": 30, "breaking_capacity_ka": 14}'::jsonb, 8500, NOW(), NOW()),
  ('SBE-52-40A', 'breaker', 'MCCB', '상도', '경제형', 'SBE-52', '{"poles": 2, "frame_af": 50, "rated_current": 40, "breaking_capacity_ka": 14}'::jsonb, 9500, NOW(), NOW()),
  ('SBE-52-50A', 'breaker', 'MCCB', '상도', '경제형', 'SBE-52', '{"poles": 2, "frame_af": 50, "rated_current": 50, "breaking_capacity_ka": 14}'::jsonb, 9500, NOW(), NOW()),
  ('SBE-102-60A', 'breaker', 'MCCB', '상도', '경제형', 'SBE-102', '{"poles": 2, "frame_af": 100, "rated_current": 60, "breaking_capacity_ka": 14}'::jsonb, 12500, NOW(), NOW()),
  ('SBE-102-75A', 'breaker', 'MCCB', '상도', '경제형', 'SBE-102', '{"poles": 2, "frame_af": 100, "rated_current": 75, "breaking_capacity_ka": 14}'::jsonb, 12500, NOW(), NOW()),
  ('SBE-102-100A', 'breaker', 'MCCB', '상도', '경제형', 'SBE-102', '{"poles": 2, "frame_af": 100, "rated_current": 100, "breaking_capacity_ka": 14}'::jsonb, 13500, NOW(), NOW()),

  -- 상도 표준형 MCCB (경제형 없는 경우)
  ('SBS-203-125A', 'breaker', 'MCCB', '상도', '표준형', 'SBS-203', '{"poles": 3, "frame_af": 200, "rated_current": 125, "breaking_capacity_ka": 25}'::jsonb, 38000, NOW(), NOW()),
  ('SBS-203-150A', 'breaker', 'MCCB', '상도', '표준형', 'SBS-203', '{"poles": 3, "frame_af": 200, "rated_current": 150, "breaking_capacity_ka": 25}'::jsonb, 38000, NOW(), NOW()),
  ('SBS-203-175A', 'breaker', 'MCCB', '상도', '표준형', 'SBS-203', '{"poles": 3, "frame_af": 200, "rated_current": 175, "breaking_capacity_ka": 25}'::jsonb, 40000, NOW(), NOW()),
  ('SBS-203-200A', 'breaker', 'MCCB', '상도', '표준형', 'SBS-203', '{"poles": 3, "frame_af": 200, "rated_current": 200, "breaking_capacity_ka": 25}'::jsonb, 40000, NOW(), NOW()),
  ('SBS-253-225A', 'breaker', 'MCCB', '상도', '표준형', 'SBS-253', '{"poles": 3, "frame_af": 250, "rated_current": 225, "breaking_capacity_ka": 25}'::jsonb, 45000, NOW(), NOW()),
  ('SBS-253-250A', 'breaker', 'MCCB', '상도', '표준형', 'SBS-253', '{"poles": 3, "frame_af": 250, "rated_current": 250, "breaking_capacity_ka": 25}'::jsonb, 45000, NOW(), NOW()),

  -- 대용량 차단기
  ('SBS-403-300A', 'breaker', 'MCCB', '상도', '표준형', 'SBS-403', '{"poles": 3, "frame_af": 400, "rated_current": 300, "breaking_capacity_ka": 35}'::jsonb, 118000, NOW(), NOW()),
  ('SBS-403-350A', 'breaker', 'MCCB', '상도', '표준형', 'SBS-403', '{"poles": 3, "frame_af": 400, "rated_current": 350, "breaking_capacity_ka": 35}'::jsonb, 118000, NOW(), NOW()),
  ('SBS-403-400A', 'breaker', 'MCCB', '상도', '표준형', 'SBS-403', '{"poles": 3, "frame_af": 400, "rated_current": 400, "breaking_capacity_ka": 35}'::jsonb, 125000, NOW(), NOW()),
  ('SBS-603-500A', 'breaker', 'MCCB', '상도', '표준형', 'SBS-603', '{"poles": 3, "frame_af": 600, "rated_current": 500, "breaking_capacity_ka": 50}'::jsonb, 185000, NOW(), NOW()),
  ('SBS-603-600A', 'breaker', 'MCCB', '상도', '표준형', 'SBS-603', '{"poles": 3, "frame_af": 600, "rated_current": 600, "breaking_capacity_ka": 50}'::jsonb, 185000, NOW(), NOW()),
  ('SBS-803-700A', 'breaker', 'MCCB', '상도', '표준형', 'SBS-803', '{"poles": 3, "frame_af": 800, "rated_current": 700, "breaking_capacity_ka": 50}'::jsonb, 225000, NOW(), NOW()),
  ('SBS-803-800A', 'breaker', 'MCCB', '상도', '표준형', 'SBS-803', '{"poles": 3, "frame_af": 800, "rated_current": 800, "breaking_capacity_ka": 50}'::jsonb, 225000, NOW(), NOW()),
  ('SBS-1003-1000A', 'breaker', 'MCCB', '상도', '표준형', 'SBS-1003', '{"poles": 3, "frame_af": 1000, "rated_current": 1000, "breaking_capacity_ka": 65}'::jsonb, 320000, NOW(), NOW()),
  ('SBS-1203-1200A', 'breaker', 'MCCB', '상도', '표준형', 'SBS-1203', '{"poles": 3, "frame_af": 1200, "rated_current": 1200, "breaking_capacity_ka": 65}'::jsonb, 380000, NOW(), NOW())
ON CONFLICT (sku) DO NOTHING;

-- Enclosures (기성함 HDS)
INSERT INTO shared.catalog_items (sku, category, kind, brand, series, model, spec, width_mm, height_mm, depth_mm, price, created_at, updated_at)
VALUES
  ('HDS-600x400x200', 'enclosure', 'PANEL', 'HDS', '옥내노출', 'HDS', '{"material": "STEEL", "thickness": 1.6, "type": "옥내노출"}'::jsonb, 600, 400, 200, 85000, NOW(), NOW()),
  ('HDS-600x800x200', 'enclosure', 'PANEL', 'HDS', '옥내노출', 'HDS', '{"material": "STEEL", "thickness": 1.6, "type": "옥내노출"}'::jsonb, 600, 800, 200, 125000, NOW(), NOW()),
  ('HDS-700x1000x250', 'enclosure', 'PANEL', 'HDS', '옥내노출', 'HDS', '{"material": "STEEL", "thickness": 1.6, "type": "옥내노출"}'::jsonb, 700, 1000, 250, 180000, NOW(), NOW()),
  ('HDS-800x1200x300', 'enclosure', 'PANEL', 'HDS', '옥내자립', 'HDS', '{"material": "STEEL", "thickness": 1.6, "type": "옥내자립"}'::jsonb, 800, 1200, 300, 285000, NOW(), NOW())
ON CONFLICT (sku) DO NOTHING;

-- Accessories (부속자재)
INSERT INTO shared.catalog_items (sku, category, kind, brand, series, model, spec, width_mm, height_mm, depth_mm, price, created_at, updated_at)
VALUES
  ('MC-9', 'accessory', 'MAGNET', '마그네트', 'MC', 'MC-9', '{"rated_current": 9}'::jsonb, 45, 50, 80, 18000, NOW(), NOW()),
  ('MC-22', 'accessory', 'MAGNET', '마그네트', 'MC', 'MC-22', '{"rated_current": 22}'::jsonb, 45, 65, 85, 22000, NOW(), NOW()),
  ('MC-50', 'accessory', 'MAGNET', '마그네트', 'MC', 'MC-50', '{"rated_current": 50}'::jsonb, 60, 82, 95, 35000, NOW(), NOW()),
  ('TIMER-24H', 'accessory', 'TIMER', '타이머', '24H', 'TIMER', '{"type": "24H"}'::jsonb, 23, 75, 100, 26000, NOW(), NOW())
ON CONFLICT (sku) DO NOTHING;
