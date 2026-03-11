-- Insert knowledge data into shared.catalog_items

-- Breakers

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SIB-32', 'Sangdo SIB-32 2P 30AF', '{"model": "SIB-32", "brand": "Sangdo", "poles": 2, "frame_AF": 30, "size_mm": [33, 70, 42]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SIB-32 고감도', 'Sangdo SIB-32 고감도 2P 30AF', '{"model": "SIB-32 \uace0\uac10\ub3c4", "brand": "Sangdo", "poles": 2, "frame_AF": 30, "size_mm": [33, 70, 42]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SBC-52', 'Sangdo SBC-52 2P 50AF', '{"model": "SBC-52", "brand": "Sangdo", "poles": 2, "frame_AF": 50, "size_mm": [50, 96, 60]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SBC-53', 'Sangdo SBC-53 3P 50AF', '{"model": "SBC-53", "brand": "Sangdo", "poles": 3, "frame_AF": 50, "size_mm": [75, 96, 60]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SBS-52', 'Sangdo SBS-52 2P 50AF', '{"model": "SBS-52", "brand": "Sangdo", "poles": 2, "frame_AF": 50, "size_mm": [50, 130, 60]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SBS-53', 'Sangdo SBS-53 3P 50AF', '{"model": "SBS-53", "brand": "Sangdo", "poles": 3, "frame_AF": 50, "size_mm": [75, 96, 60]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SBS-54', 'Sangdo SBS-54 4P 50AF', '{"model": "SBS-54", "brand": "Sangdo", "poles": 4, "frame_AF": 50, "size_mm": [100, 130, 60]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SBE-102', 'Sangdo SBE-102 2P 100AF', '{"model": "SBE-102", "brand": "Sangdo", "poles": 2, "frame_AF": 100, "size_mm": [50, 130, 60]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SBE-103', 'Sangdo SBE-103 3P 100AF', '{"model": "SBE-103", "brand": "Sangdo", "poles": 3, "frame_AF": 100, "size_mm": [75, 130, 60]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SBE-104', 'Sangdo SBE-104 4P 100AF', '{"model": "SBE-104", "brand": "Sangdo", "poles": 4, "frame_AF": 100, "size_mm": [100, 130, 60]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SBS-202', 'Sangdo SBS-202 2P 200AF', '{"model": "SBS-202", "brand": "Sangdo", "poles": 2, "frame_AF": 200, "size_mm": [70, 165, 60]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SBS-203', 'Sangdo SBS-203 3P 200AF', '{"model": "SBS-203", "brand": "Sangdo", "poles": 3, "frame_AF": 200, "size_mm": [105, 165, 60]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SBS-204', 'Sangdo SBS-204 4P 200AF', '{"model": "SBS-204", "brand": "Sangdo", "poles": 4, "frame_AF": 200, "size_mm": [140, 165, 60]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SBS-403', 'Sangdo SBS-403 3P 400AF', '{"model": "SBS-403", "brand": "Sangdo", "poles": 3, "frame_AF": 400, "size_mm": [140, 257, 109]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SBS-404', 'Sangdo SBS-404 4P 400AF', '{"model": "SBS-404", "brand": "Sangdo", "poles": 4, "frame_AF": 400, "size_mm": [187, 257, 109]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SBS-603', 'Sangdo SBS-603 3P 600AF', '{"model": "SBS-603", "brand": "Sangdo", "poles": 3, "frame_AF": 600, "size_mm": [210, 280, 109]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SBS-604', 'Sangdo SBS-604 4P 600AF', '{"model": "SBS-604", "brand": "Sangdo", "poles": 4, "frame_AF": 600, "size_mm": [280, 280, 109]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SBS-803', 'Sangdo SBS-803 3P 800AF', '{"model": "SBS-803", "brand": "Sangdo", "poles": 3, "frame_AF": 800, "size_mm": [210, 280, 109]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SBS-804', 'Sangdo SBS-804 4P 800AF', '{"model": "SBS-804", "brand": "Sangdo", "poles": 4, "frame_AF": 800, "size_mm": [280, 280, 109]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO shared.catalog_items (kind, sku, name, spec, unit_price, currency, is_active, meta)
VALUES ('breaker', 'Sangdo-SBS-103', 'Sangdo SBS-103 3P 125AF', '{"model": "SBS-103", "brand": "Sangdo", "poles": 3, "frame_AF": 125, "size_mm": [90, 155, 60]}'::jsonb, 0.0, 'KRW', true, '{"source": "breakers.json"}'::jsonb)
ON CONFLICT (sku) DO NOTHING;

-- Enclosures

-- Accessories (Magnets)
