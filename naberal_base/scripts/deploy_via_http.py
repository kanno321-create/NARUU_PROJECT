#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NABERAL Project - Deploy via Supabase REST API
Alternative deployment using HTTP instead of psycopg2
"""

import requests
import sys

# Supabase credentials
SUPABASE_URL = "https://jijifnzcoxglafvjltwn.supabase.co"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imppamlmbnpjb3hnbGFmdmpsdHduIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTI0NjcxMSwiZXhwIjoyMDc0ODIyNzExfQ.ZKr9WbnkNemrGw0fSRdsW6gSut8tsAOJbQuuNbJRUGQ"

def execute_sql_via_api(sql_query):
    """Execute SQL via Supabase REST API"""
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"

    headers = {
        "apikey": SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    }

    payload = {"query": sql_query}

    response = requests.post(url, headers=headers, json=payload)
    return response

def main():
    print("=" * 60)
    print("NABERAL Project - Schema Deployment via HTTP")
    print("=" * 60)
    print(f"Target: {SUPABASE_URL}")
    print()

    # Read schema file
    print("Reading schema file...")
    with open('supabase/migrations/001_initial_schema.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    print(f"Schema size: {len(schema_sql)} characters")
    print()

    # For HTTP API deployment, we need to create a stored procedure first
    print("Note: Direct SQL execution via REST API requires enabling PostgREST")
    print("Alternative approach: Use Supabase CLI or web console")
    print()
    print("Recommended steps:")
    print("1. Install Supabase CLI: npm install -g supabase")
    print("2. Link project: supabase link --project-ref jijifnzcoxglafvjltwn")
    print("3. Push migrations: supabase db push")
    print()
    print("Or use web console:")
    print(f"1. Go to: {SUPABASE_URL}/project/jijifnzcoxglafvjltwn/sql")
    print("2. Paste SQL from: supabase/migrations/001_initial_schema.sql")
    print("3. Click 'Run'")

    return 0

if __name__ == "__main__":
    sys.exit(main())
