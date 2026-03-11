"""
Create catalog_items table directly using asyncpg
Bypasses Alembic complexity
"""
import os
import asyncio
import asyncpg

# Load environment
with open('.env.test.local', encoding='utf-8') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

# Parse DATABASE_URL
db_url = os.environ['DATABASE_URL']
# postgresql+asyncpg://user:pass@host:port/dbname
db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')

async def main():
    print('Connecting to database...')
    conn = await asyncpg.connect(db_url)

    try:
        # Create table
        print('Creating catalog_items table...')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS public.catalog_items (
                id SERIAL PRIMARY KEY,
                sku VARCHAR(100) NOT NULL UNIQUE,
                category VARCHAR(50) NOT NULL,
                kind VARCHAR(50) NOT NULL,
                brand VARCHAR(100) NOT NULL,
                series VARCHAR(100),
                model VARCHAR(100) NOT NULL,
                specs JSONB NOT NULL DEFAULT '{}',
                width_mm INTEGER,
                height_mm INTEGER,
                depth_mm INTEGER,
                price INTEGER NOT NULL,
                search_keywords TEXT[] NOT NULL DEFAULT '{}',
                source_line INTEGER,
                notes TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        ''')
        print('  Table created!')

        # Create indexes
        print('Creating indexes...')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_catalog_items_category ON public.catalog_items(category)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_catalog_items_kind ON public.catalog_items(kind)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_catalog_items_brand ON public.catalog_items(brand)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_catalog_items_model ON public.catalog_items(model)')
        await conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_catalog_items_sku ON public.catalog_items(sku)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_catalog_items_search_keywords ON public.catalog_items USING gin(search_keywords)')
        print('  Indexes created!')

        # Create trigger function
        print('Creating updated_at trigger...')
        await conn.execute('''
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = now();
                RETURN NEW;
            END;
            $$ language 'plpgsql'
        ''')

        await conn.execute('''
            DROP TRIGGER IF EXISTS update_catalog_items_updated_at ON public.catalog_items
        ''')

        await conn.execute('''
            CREATE TRIGGER update_catalog_items_updated_at
            BEFORE UPDATE ON public.catalog_items
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
        ''')
        print('  Trigger created!')

        # Insert sample data
        print('Inserting sample data...')
        await conn.execute('''
            INSERT INTO public.catalog_items (sku, category, kind, brand, series, model, specs, width_mm, height_mm, depth_mm, price, search_keywords)
            VALUES
                ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9, $10, $11, $12),
                ($13, $14, $15, $16, $17, $18, $19::jsonb, $20, $21, $22, $23, $24),
                ($25, $26, $27, $28, $29, $30, $31::jsonb, $32, $33, $34, $35, $36)
            ON CONFLICT (sku) DO NOTHING
        ''',
            'SBS-54-100A', 'breaker', 'MCCB', '상도차단기', '표준형', 'SBS-54',
            '{"poles": 4, "current_a": 100, "frame_af": 50, "breaking_capacity_ka": 25.0}',
            100, 130, 60, 28500,
            ['SBS-54', '4P', '100A', '50AF', 'MCCB', '표준형', '상도차단기'],

            'SBE-102-60A', 'breaker', 'MCCB', '상도차단기', '경제형', 'SBE-102',
            '{"poles": 2, "current_a": 60, "frame_af": 100, "breaking_capacity_ka": 14.0}',
            50, 130, 60, 12500,
            ['SBE-102', '2P', '60A', '100AF', 'MCCB', '경제형', '상도차단기'],

            'HB-600800200', 'enclosure', 'enclosure', '한국산업', None, 'HB-600*800*200',
            '{"type": "옥내노출", "material": "STEEL 1.6T"}',
            600, 800, 200, 180000,
            ['HB-600*800*200', '600x800x200', '옥내노출', 'STEEL 1.6T', '한국산업']
        )
        print('  Sample data inserted!')

        # Verify
        count = await conn.fetchval('SELECT COUNT(*) FROM public.catalog_items')
        print(f'\nSuccess! catalog_items table has {count} rows')

        # Show samples
        rows = await conn.fetch('SELECT sku, category, model, price FROM public.catalog_items LIMIT 3')
        print('\nSample data:')
        for row in rows:
            print(f'  {row["sku"]}: {row["model"]} ({row["category"]}) - {row["price"]:,}원')

    finally:
        await conn.close()
        print('\nConnection closed.')

if __name__ == '__main__':
    asyncio.run(main())
