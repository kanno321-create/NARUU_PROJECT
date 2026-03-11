#!/usr/bin/env python3
"""Check Supabase tables"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('.env.supabase')

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

supabase = create_client(supabase_url, supabase_key)

# Try to query catalog_items
try:
    result = supabase.table('catalog_items').select('*').limit(1).execute()
    print(f"[OK] catalog_items table exists")
    print(f"  Columns: {result.data}")
except Exception as e:
    print(f"[ERROR] {e}")
