"""
Phase I-3.5: Seed kis_beta schema from SSOT (Zero-Mock)

SB-01: search_path="kis_beta,public"
SB-03: Spec → Supabase 순서 마이그레이션
SB-05: Real DB only, skip if unavailable

Loads catalog data from knowledge_consolidation/output/*.json (SSOT)
Inserts 100+ breakers, 100+ enclosures for integration test success paths
"""
import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from datetime import datetime

# Load .env.test.local
load_dotenv(".env.test.local", override=True)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
SSOT_DIR = PROJECT_ROOT / "knowledge_consolidation" / "output"
EVIDENCE_DIR = PROJECT_ROOT / "out" / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# SSOT Sources
BREAKERS_JSON = SSOT_DIR / "breakers.json"
ENCLOSURES_JSON = SSOT_DIR / "enclosures.json"
STANDARDS_JSON = SSOT_DIR / "standards.json"

# Evidence Output
SEED_LOG = EVIDENCE_DIR / "db_seed_log.txt"


async def create_tables(conn):
    """Create kis_beta tables if not exist"""

    # breakers table (already exists, verify)
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS kis_beta.breakers (
            id SERIAL PRIMARY KEY,
            sku VARCHAR(100) UNIQUE NOT NULL,
            brand VARCHAR(50),
            series VARCHAR(50),
            model VARCHAR(100),
            poles INTEGER,
            frame_af INTEGER,
            current_at INTEGER,
            breaker_type VARCHAR(50),
            price DECIMAL(10,2),
            width_mm INTEGER,
            height_mm INTEGER,
            depth_mm INTEGER,
            heat_w DECIMAL(8,2),
            slot_need INTEGER,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))

    # enclosures table (new)
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS kis_beta.enclosures (
            id SERIAL PRIMARY KEY,
            code VARCHAR(100) UNIQUE NOT NULL,
            model VARCHAR(100),
            ip_rating VARCHAR(10),
            frame_family VARCHAR(50),
            width_mm INTEGER NOT NULL,
            height_mm INTEGER NOT NULL,
            depth_mm INTEGER NOT NULL,
            slots_total INTEGER,
            heat_limit_w DECIMAL(10,2),
            material VARCHAR(50),
            thickness_mm DECIMAL(5,2),
            install_location VARCHAR(50),
            price DECIMAL(10,2),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))

    print("[OK] Tables created/verified")


async def seed_breakers(conn, log_file):
    """Seed breakers from SSOT breakers.json"""

    with open(BREAKERS_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data['catalog']['items']

    # Take first 120 items (diverse sample)
    items_to_seed = items[:120]

    inserted = 0
    updated = 0
    failed = 0
    sample_ids = []

    for item in items_to_seed:
        try:
            # Extract fields (match DB schema)
            sku = f"{item['model']}-{item.get('ampere', [20])[0] if item.get('ampere') else 20}A"
            brand = item.get('brand', 'Unknown')
            series = item.get('series', '')
            model = item['model']
            poles = item.get('poles', 2)
            frame_af = item.get('frame_AF', 50)
            current_at = item.get('ampere', [20])[0] if item.get('ampere') else 20
            breaker_type = item.get('category', 'MCCB')
            price = item.get('price', 10000)

            # Dimensions (W×H×D from size_mm)
            size_mm = item.get('size_mm', [50, 130, 60])
            width_mm = size_mm[0] if len(size_mm) > 0 else 50
            height_mm = size_mm[1] if len(size_mm) > 1 else 130
            depth_mm = size_mm[2] if len(size_mm) > 2 else 60

            # Heat/Slot (default estimates)
            heat_w = current_at * 0.5  # Rough estimate
            slot_need = 1 if poles <= 2 else 2

            # Upsert
            result = await conn.execute(text("""
                INSERT INTO kis_beta.breakers
                (sku, brand, series, model, poles, frame_af, current_at, breaker_type, price,
                 width_mm, height_mm, depth_mm, heat_w, slot_need)
                VALUES
                (:sku, :brand, :series, :model, :poles, :frame_af, :current_at, :breaker_type, :price,
                 :width_mm, :height_mm, :depth_mm, :heat_w, :slot_need)
                ON CONFLICT (sku) DO UPDATE SET
                    price = EXCLUDED.price,
                    width_mm = EXCLUDED.width_mm,
                    height_mm = EXCLUDED.height_mm,
                    depth_mm = EXCLUDED.depth_mm
                RETURNING id
            """), {
                'sku': sku, 'brand': brand, 'series': series, 'model': model,
                'poles': poles, 'frame_af': frame_af, 'current_at': current_at,
                'breaker_type': breaker_type, 'price': price,
                'width_mm': width_mm, 'height_mm': height_mm, 'depth_mm': depth_mm,
                'heat_w': heat_w, 'slot_need': slot_need
            })

            breaker_id = result.scalar()
            inserted += 1

            if len(sample_ids) < 10:
                sample_ids.append((breaker_id, sku))

        except Exception as e:
            failed += 1
            log_file.write(f"[FAIL] Breaker {item.get('model')}: {str(e)}\n")

    log_file.write(f"\n[Breakers Seed]\n")
    log_file.write(f"  Inserted: {inserted}\n")
    log_file.write(f"  Failed: {failed}\n")
    log_file.write(f"  Sample IDs (first 10):\n")
    for bid, sku in sample_ids:
        log_file.write(f"    - ID={bid}: {sku}\n")

    print(f"[OK] Breakers: {inserted} inserted, {failed} failed")
    return inserted


async def seed_enclosures(conn, log_file):
    """Seed enclosures from SSOT enclosures.json"""

    with open(ENCLOSURES_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data['hds_catalog']['standard']['items']

    # Take first 120 items
    items_to_seed = items[:120]

    inserted = 0
    failed = 0
    sample_ids = []

    for item in items_to_seed:
        try:
            code = item['model']
            model = item['model']
            ip_rating = item.get('grade', 'IP54')  # Default IP54
            frame_family = f"{item.get('material', 'steel')}_{item.get('thickness_mm', 1.6)}T"

            # Dimensions
            size_mm = item['size_mm']
            width_mm = size_mm[0]
            height_mm = size_mm[1]
            depth_mm = size_mm[2]

            # Slots/Heat (estimates based on size)
            slots_total = max(4, int(width_mm / 100))  # Rough estimate
            heat_limit_w = width_mm * height_mm * 0.01  # Rough estimate

            material = item.get('material', 'steel')
            thickness_mm = item.get('thickness_mm', 1.6)
            install_location = item.get('install_location', 'indoor')
            price = item.get('price', 20000)

            # Upsert
            result = await conn.execute(text("""
                INSERT INTO kis_beta.enclosures
                (code, model, ip_rating, frame_family, width_mm, height_mm, depth_mm,
                 slots_total, heat_limit_w, material, thickness_mm, install_location, price)
                VALUES
                (:code, :model, :ip_rating, :frame_family, :width_mm, :height_mm, :depth_mm,
                 :slots_total, :heat_limit_w, :material, :thickness_mm, :install_location, :price)
                ON CONFLICT (code) DO UPDATE SET
                    price = EXCLUDED.price,
                    slots_total = EXCLUDED.slots_total
                RETURNING id
            """), {
                'code': code, 'model': model, 'ip_rating': ip_rating, 'frame_family': frame_family,
                'width_mm': width_mm, 'height_mm': height_mm, 'depth_mm': depth_mm,
                'slots_total': slots_total, 'heat_limit_w': heat_limit_w,
                'material': material, 'thickness_mm': thickness_mm,
                'install_location': install_location, 'price': price
            })

            enc_id = result.scalar()
            inserted += 1

            if len(sample_ids) < 10:
                sample_ids.append((enc_id, code))

        except Exception as e:
            failed += 1
            log_file.write(f"[FAIL] Enclosure {item.get('model')}: {str(e)}\n")

    log_file.write(f"\n[Enclosures Seed]\n")
    log_file.write(f"  Inserted: {inserted}\n")
    log_file.write(f"  Failed: {failed}\n")
    log_file.write(f"  Sample IDs (first 10):\n")
    for eid, code in sample_ids:
        log_file.write(f"    - ID={eid}: {code}\n")

    print(f"[OK] Enclosures: {inserted} inserted, {failed} failed")
    return inserted


async def main():
    """Main seed execution"""

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("[FAIL] DATABASE_URL not configured (SB-05)")
        with open(SEED_LOG, 'w') as f:
            f.write("[SKIP] DATABASE_URL unavailable\n")
            f.write(f"Reason: SB-05 Zero-Mock requires real DB\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        return

    # Convert to asyncpg
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(database_url, echo=False)

    with open(SEED_LOG, 'w', encoding='utf-8') as log_file:
        log_file.write(f"[Phase I-3.5] Seed kis_beta from SSOT\n")
        log_file.write(f"Timestamp: {datetime.now().isoformat()}\n")
        log_file.write(f"SSOT Dir: {SSOT_DIR}\n\n")

        async with engine.begin() as conn:
            # SB-01: Set search_path
            await conn.execute(text("SET search_path TO kis_beta, public"))

            # Create tables
            await create_tables(conn)

            # Seed breakers
            breakers_count = await seed_breakers(conn, log_file)

            # Seed enclosures
            enclosures_count = await seed_enclosures(conn, log_file)

            # Summary
            log_file.write(f"\n[SUMMARY]\n")
            log_file.write(f"  Total Breakers: {breakers_count}\n")
            log_file.write(f"  Total Enclosures: {enclosures_count}\n")
            log_file.write(f"  Status: COMPLETE\n")

        await engine.dispose()

        print(f"\n[DONE] Seed complete")
        print(f"  Breakers: {breakers_count}")
        print(f"  Enclosures: {enclosures_count}")
        print(f"  Log: {SEED_LOG}")


if __name__ == "__main__":
    asyncio.run(main())
