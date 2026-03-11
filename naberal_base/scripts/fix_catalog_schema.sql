-- Fix catalog_items schema: Add missing 'price' column
-- Run this on Supabase SQL Editor

-- Check current schema
-- SELECT column_name, data_type FROM information_schema.columns 
-- WHERE table_schema = 'shared' AND table_name = 'catalog_items';

-- Add price column if not exists
ALTER TABLE shared.catalog_items 
ADD COLUMN IF NOT EXISTS price INTEGER NOT NULL DEFAULT 0;

-- Verify
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'shared' AND table_name = 'catalog_items'
ORDER BY ordinal_position;
