#!/usr/bin/env python3
"""
Supabase Schema Deployment Script
Deploys db/schema.sql to Supabase PostgreSQL
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv('.env.supabase')

def deploy_schema():
    """Deploy schema.sql to Supabase"""

    # Get Supabase credentials
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')

    if not url or not service_key:
        print("[ERROR] SUPABASE_URL or SUPABASE_SERVICE_KEY not found in .env.supabase")
        sys.exit(1)

    # Read schema file
    schema_path = Path('db/schema.sql')
    if not schema_path.exists():
        print(f"[ERROR] {schema_path} not found")
        sys.exit(1)

    schema_sql = schema_path.read_text(encoding='utf-8')

    print(f"[*] Deploying schema from {schema_path}")
    print(f"[*] Target: {url}")
    print(f"[*] Schema size: {len(schema_sql)} bytes")
    print()

    try:
        # Create Supabase client
        supabase: Client = create_client(url, service_key)

        # Execute schema SQL via RPC
        # Note: Supabase doesn't support direct SQL execution via client
        # We need to use psycopg2 for raw SQL
        import psycopg2

        db_url = os.getenv('SUPABASE_DB_URL')
        if not db_url:
            print("[ERROR] SUPABASE_DB_URL not found")
            sys.exit(1)

        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        print("[*] Executing schema SQL...")
        cur.execute(schema_sql)
        conn.commit()

        print("[OK] Schema deployed successfully!")

        # Verify tables
        cur.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema IN ('estimator', 'shared')
            ORDER BY table_schema, table_name
        """)

        tables = cur.fetchall()
        print(f"\n[*] Deployed Tables ({len(tables)}):")
        for schema, table in tables:
            print(f"  [OK] {schema}.{table}")

        cur.close()
        conn.close()

        print("\n[SUCCESS] Deployment complete!")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    deploy_schema()
