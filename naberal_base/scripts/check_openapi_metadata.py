"""Check OpenAPI metadata for POST /v1/estimate"""
import json
from pathlib import Path

spec_path = Path("dist/contract/openapi_v1.0.0.json")
with open(spec_path, encoding="utf-8") as f:
    spec = json.load(f)

post_estimate = spec['paths']['/v1/estimate']['post']

print("=== POST /v1/estimate Metadata ===")
print(f"deprecated: {post_estimate.get('deprecated', 'MISSING')}")
print(f"x-kis-alias-of: {post_estimate.get('x-kis-alias-of', 'MISSING')}")
print(f"x-kis-sunset-days: {post_estimate.get('x-kis-sunset-days', 'MISSING')}")

if not post_estimate.get('x-kis-alias-of'):
    print("\n[WARNING] x-kis-* metadata MISSING!")
    print("Need to enhance extract_openapi_spec.py")
