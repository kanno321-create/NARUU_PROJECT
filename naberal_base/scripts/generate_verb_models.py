#!/usr/bin/env python3
"""
Verb Model Generator (I-3.3)

Reads params.json from core/ssot/verbs/
Generates Pydantic BaseModel classes to core/ssot/generated_verbs.py

LAW-02: SSOT 준수 - params.json 단일 출처
LAW-03: 하드코딩 금지 - 모델 자동 생성
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict


# Input path
PARAMS_FILE = Path("src/kis_estimator_core/core/ssot/verbs/params.json")

# Output path
OUTPUT_FILE = Path("src/kis_estimator_core/core/ssot/generated_verbs.py")


def load_params_json() -> Dict[str, Any]:
    """Load params.json"""
    with open(PARAMS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def py_type_from_json_type(json_type: str) -> str:
    """Convert JSON type to Python type hint"""
    type_map = {
        "str": "str",
        "int": "int",
        "float": "float",
        "bool": "bool",
        "object": "Dict[str, Any]",
        "array": "List[Any]",
    }
    return type_map.get(json_type, "Any")


def generate_param_model(verb_name: str, params_def: Dict[str, Any]) -> str:
    """Generate Pydantic model for a Verb's params"""
    class_name = f"{verb_name.replace('_', '').title()}Params"
    lines = []

    lines.append(f"class {class_name}(VerbParamsBase):")
    lines.append(f'    """')
    lines.append(f'    {params_def.get("description", f"{verb_name} 파라미터")}')
    lines.append(f'    """')
    lines.append("")

    fields = params_def.get("fields", {})
    for field_name, field_def in fields.items():
        json_type = field_def.get("type", "Any")
        py_type = py_type_from_json_type(json_type)
        required = field_def.get("required", False)
        default = field_def.get("default")
        description = field_def.get("description", "")

        # Field line
        if required:
            lines.append(f'    {field_name}: {py_type} = Field(..., description="{description}")')
        else:
            if default is None:
                lines.append(f'    {field_name}: Optional[{py_type}] = Field(None, description="{description}")')
            elif isinstance(default, str):
                lines.append(f'    {field_name}: {py_type} = Field("{default}", description="{description}")')
            elif isinstance(default, list):
                lines.append(f'    {field_name}: {py_type} = Field(default_factory=list, description="{description}")')
            else:
                lines.append(f'    {field_name}: {py_type} = Field({default}, description="{description}")')

    return "\n".join(lines)


def generate_verb_models() -> None:
    """Generate generated_verbs.py from params.json"""

    print("=" * 60)
    print("Verb Model Generator - I-3.3")
    print("=" * 60)

    print(f"\nLoading: {PARAMS_FILE}")
    if not PARAMS_FILE.exists():
        print(f"[ERROR] File not found: {PARAMS_FILE}")
        return

    data = load_params_json()
    print(f"[OK] Loaded params.json")

    # Generate Python code
    print(f"\nGenerating: {OUTPUT_FILE}")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        # Header
        f.write('"""\n')
        f.write("SSOT Generated Verb Models (I-3.3)\n\n")
        f.write("WARNING: This file is AUTO-GENERATED.\n")
        f.write("Do NOT edit manually. Run scripts/generate_verb_models.py instead.\n\n")
        f.write(f"Generated: {datetime.utcnow().isoformat()}Z\n")
        f.write(f"Source: {PARAMS_FILE}\n\n")
        f.write("LAW-02: SSOT Single Source - No duplication\n")
        f.write("LAW-03: No Hardcoding - Import from here only\n")
        f.write('"""\n\n')

        # Imports
        f.write("from typing import Dict, List, Any, Optional, Type\n")
        f.write("from pydantic import BaseModel, Field\n\n")

        # Base class
        f.write("# ============================================================\n")
        f.write("# VerbParamsBase - 모든 Verb Params의 Base\n")
        f.write("# ============================================================\n\n")
        f.write("class VerbParamsBase(BaseModel):\n")
        f.write('    """Base class for all Verb parameters"""\n')
        f.write("    pass\n\n")

        # VerbSpecModel
        f.write("# ============================================================\n")
        f.write("# VerbSpecModel - VerbSpec 최상위 모델\n")
        f.write("# ============================================================\n\n")
        f.write("class VerbSpecModel(BaseModel):\n")
        f.write('    """VerbSpec 최상위 모델 (SSOT)"""\n\n')
        f.write('    verb_name: str = Field(..., description="Verb 이름 (대문자)")\n')
        f.write('    params: Dict[str, Any] = Field(..., description="Verb별 파라미터 객체")\n')
        f.write('    version: str = Field("1.0.0", description="Verb spec 버전")\n\n')

        # Generate param models for each verb
        f.write("# ============================================================\n")
        f.write("# Verb Params Models (Auto-Generated)\n")
        f.write("# ============================================================\n\n")

        verb_params = data.get("verb_params", {})
        model_names = []

        for verb_name, params_def in verb_params.items():
            model_code = generate_param_model(verb_name, params_def)
            f.write(model_code)
            f.write("\n\n")

            class_name = f"{verb_name.replace('_', '').title()}Params"
            model_names.append((verb_name, class_name))

        # resolve_params_model function
        f.write("# ============================================================\n")
        f.write("# resolve_params_model - Verb name → Params Model 매핑\n")
        f.write("# ============================================================\n\n")
        f.write("def resolve_params_model(verb_name: str) -> Type[VerbParamsBase]:\n")
        f.write('    """\n')
        f.write('    Verb name에서 해당 Params 모델 클래스 반환\n\n')
        f.write('    Args:\n')
        f.write('        verb_name: Verb 이름 (대문자, 예: "PICK_ENCLOSURE")\n\n')
        f.write('    Returns:\n')
        f.write('        VerbParamsBase 서브클래스\n\n')
        f.write('    Raises:\n')
        f.write('        KeyError: 알 수 없는 verb_name\n')
        f.write('    """\n')
        f.write('    PARAMS_MODEL_REGISTRY: Dict[str, Type[VerbParamsBase]] = {\n')
        for verb_name, class_name in model_names:
            f.write(f'        "{verb_name}": {class_name},\n')
        f.write('    }\n\n')
        f.write('    if verb_name.upper() not in PARAMS_MODEL_REGISTRY:\n')
        f.write('        raise KeyError(f"Unknown verb_name: {verb_name}")\n\n')
        f.write('    return PARAMS_MODEL_REGISTRY[verb_name.upper()]\n')

    print(f"[OK] Generated: {OUTPUT_FILE}")
    print(f"   Size: {OUTPUT_FILE.stat().st_size:,} bytes")
    print(f"   Models: {len(model_names)}")

    print(f"\n{'=' * 60}")
    print("[OK] Verb Model Generation COMPLETE")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    generate_verb_models()
