"""
OpenAPI 3.1 Contract Extraction Script

Phase D: Extract OpenAPI schema from FastAPI app and save to dist/contract/

Requirements:
- Extract from running app (not import - avoids DB init issues)
- Save as JSON and YAML
- Verify 9 endpoints present
- Add x-kis-alias-of to deprecated endpoint
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Import app (this will trigger all router registrations)
from api.main import app


def extract_openapi():
    """Extract OpenAPI schema from FastAPI app"""

    # Get OpenAPI schema
    openapi_schema = app.openapi()

    # Add custom extensions for deprecated endpoint
    if "/v1/estimate" in openapi_schema.get("paths", {}):
        estimate_endpoint = openapi_schema["paths"]["/v1/estimate"]
        if "post" in estimate_endpoint:
            estimate_endpoint["post"]["deprecated"] = True
            estimate_endpoint["post"]["x-kis-alias-of"] = "/v1/estimate/plan"
            estimate_endpoint["post"]["x-kis-deprecation-reason"] = "Migrating to K-PEW Plan-Execute architecture"

    return openapi_schema


def save_contracts(schema: dict):
    """Save OpenAPI schema as JSON and YAML"""

    # Create output directory
    contract_dir = project_root / "dist" / "contract"
    contract_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON
    json_path = contract_dir / "openapi_v1.0.0.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved JSON: {json_path}")

    # Save YAML (optional, for human readability)
    try:
        import yaml
        yaml_path = contract_dir / "openapi_v1.0.0.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(schema, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f"[OK] Saved YAML: {yaml_path}")
    except ImportError:
        print("[WARN] PyYAML not installed, skipping YAML export")

    return json_path


def verify_endpoints(schema: dict):
    """Verify 9 required endpoints are present"""

    required_endpoints = [
        ("GET", "/health"),
        ("GET", "/readyz"),
        ("POST", "/v1/estimate"),
        ("POST", "/v1/estimate/plan"),
        ("POST", "/v1/estimate/execute"),
        ("GET", "/v1/estimate/{estimate_id}"),
        ("GET", "/v1/catalog/items"),
        ("GET", "/v1/catalog/items/{sku}"),
        ("GET", "/v1/catalog/stats"),
    ]

    paths = schema.get("paths", {})
    found = []
    missing = []

    for method, path in required_endpoints:
        method_lower = method.lower()
        if path in paths and method_lower in paths[path]:
            found.append((method, path))
        else:
            missing.append((method, path))

    print(f"\n[VERIFICATION] Endpoints: {len(found)}/9")
    for method, path in found:
        deprecated = " [DEPRECATED]" if path == "/v1/estimate" and method == "POST" else ""
        print(f"  [OK] {method:6} {path}{deprecated}")

    if missing:
        print(f"\n[ERROR] Missing endpoints: {len(missing)}")
        for method, path in missing:
            print(f"  [FAIL] {method:6} {path}")
        return False

    return True


def main():
    """Main extraction workflow"""

    print("=" * 60)
    print("OpenAPI 3.1 Contract Extraction")
    print("=" * 60)

    # Extract schema
    print("\n[1/3] Extracting OpenAPI schema from FastAPI app...")
    schema = extract_openapi()

    # Verify endpoints
    print("\n[2/3] Verifying required endpoints...")
    if not verify_endpoints(schema):
        print("\n[FAIL] Contract verification failed")
        sys.exit(1)

    # Save contracts
    print("\n[3/3] Saving contract files...")
    json_path = save_contracts(schema)

    print("\n" + "=" * 60)
    print(f"[SUCCESS] OpenAPI contract extracted")
    print(f"Contract: {json_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
