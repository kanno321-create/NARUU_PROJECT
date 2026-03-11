#!/usr/bin/env python3
"""
Load Knowledge Files to Supabase
Loads consolidated knowledge from knowledge_consolidation/output/ into Supabase
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from dotenv import load_dotenv
from kis_estimator_core.infra.knowledge_loader import load_knowledge_to_supabase

# Load environment
load_dotenv('.env.supabase')

def main():
    """Load all knowledge files"""

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

    if not supabase_url or not supabase_key:
        print("[ERROR] SUPABASE_URL or SUPABASE_SERVICE_KEY not found")
        sys.exit(1)

    print(f"[*] Loading knowledge files to Supabase")
    print(f"[*] Target: {supabase_url}")
    print()

    try:
        results = load_knowledge_to_supabase(supabase_url, supabase_key)

        print("[OK] Knowledge load complete!")
        print(f"\n[*] Results:")
        for category, count in results.items():
            print(f"  [OK] {category}: {count} items")

        total = sum(results.values())
        print(f"\n[SUCCESS] Total: {total} items loaded")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
