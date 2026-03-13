#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NABERAL Project - Database Schema Deployment
Deploy schema to new Supabase project (jijifnzcoxglafvjltwn)
"""

import sys
import os

# Set encoding before importing psycopg2
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import psycopg2

# Connection parameters (from environment variables)
DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

if not DB_PASSWORD or not DB_HOST:
    raise RuntimeError("DB_PASSWORD and DB_HOST must be set")

def main():
    """Deploy database schema to NABERAL Supabase project"""

    # Build connection string
    conn_params = {
        'host': DB_HOST,
        'port': DB_PORT,
        'database': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'connect_timeout': 10
    }

    print("=" * 60)
    print("NABERAL Project - Database Schema Deployment")
    print("=" * 60)
    print(f"Target: {DB_HOST}")
    print(f"Database: {DB_NAME}")
    print()

    try:
        # Connect to database
        print("Connecting to Supabase...")
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = False
        cur = conn.cursor()

        # Read schema file
        schema_file = 'supabase/migrations/001_initial_schema.sql'
        print(f"Reading schema from: {schema_file}")

        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # Execute schema
        print("Executing schema migration...")
        cur.execute(schema_sql)
        conn.commit()
        print("✓ Schema executed successfully")

        # Verify tables
        print("\nVerifying created tables...")
        cur.execute("""
            SELECT schemaname, tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)

        tables = cur.fetchall()
        print(f"\nCreated {len(tables)} tables in public schema:")
        for schema, table in tables:
            print(f"  ✓ {schema}.{table}")

        # Read and execute seed data
        seed_file = 'supabase/seed.sql'
        if os.path.exists(seed_file):
            print(f"\nReading seed data from: {seed_file}")
            with open(seed_file, 'r', encoding='utf-8') as f:
                seed_sql = f.read()

            print("Executing seed data...")
            cur.execute(seed_sql)
            conn.commit()
            print("✓ Seed data loaded successfully")

        # Final verification
        cur.execute("SELECT COUNT(*) FROM catalog_items;")
        catalog_count = cur.fetchone()[0]
        print(f"\nFinal verification:")
        print(f"  - Catalog items: {catalog_count} rows")

        cur.close()
        conn.close()

        print("\n" + "=" * 60)
        print("✅ NABERAL Project schema deployment successful!")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ Deployment failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
