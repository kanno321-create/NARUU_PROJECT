"""
EPDL JSON Schema Validator

Validates EPDL JSON against official JSON Schema v0.9
"""

import json
from pathlib import Path

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error

try:
    import jsonschema
    from jsonschema import Draft7Validator

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


class EPDLSchemaValidator:
    """JSON Schema validator for EPDL v0.9"""

    def __init__(self, schema_path: Path | None = None):
        """
        Initialize validator with JSON Schema

        Args:
            schema_path: Path to epdl.schema.json (default: specs/epdl.schema.json)

        Raises:
            FileNotFoundError: If schema file not found
            ImportError: If jsonschema package not installed
        """
        if not JSONSCHEMA_AVAILABLE:
            raise ImportError(
                "jsonschema package required. Install: pip install jsonschema"
            )

        if schema_path is None:
            # Default: PROJECT_ROOT/specs/epdl.schema.json
            schema_path = (
                Path(__file__).parent.parent.parent.parent.parent
                / "specs"
                / "epdl.schema.json"
            )

        if not schema_path.exists():
            raise_error(
                ErrorCode.E_INTERNAL,
                f"EPDL schema not found: {schema_path}\n"
                f"Expected location: specs/epdl.schema.json",
            )

        with open(schema_path, encoding="utf-8") as f:
            self.schema = json.load(f)

        # Create validator instance
        self.validator = Draft7Validator(self.schema)

    def validate(self, epdl_json: dict) -> tuple[bool, list[str]]:
        """
        Validate EPDL JSON against schema

        Args:
            epdl_json: EPDL plan as dictionary

        Returns:
            (is_valid, error_messages)
                is_valid: True if valid, False otherwise
                error_messages: List of validation errors (empty if valid)
        """
        errors = []

        try:
            # Collect all validation errors
            validation_errors = list(self.validator.iter_errors(epdl_json))

            if validation_errors:
                for error in validation_errors:
                    # Build error path
                    path = (
                        " → ".join(str(p) for p in error.absolute_path)
                        if error.absolute_path
                        else "root"
                    )
                    error_msg = f"Schema validation failed at [{path}]: {error.message}"
                    errors.append(error_msg)

                return False, errors

            return True, []

        except Exception as e:
            errors.append(f"Unexpected validation error: {str(e)}")
            return False, errors

    def validate_strict(self, epdl_json: dict) -> None:
        """
        Strict validation - raises exception on failure

        Args:
            epdl_json: EPDL plan as dictionary

        Raises:
            jsonschema.ValidationError: If validation fails
        """
        jsonschema.validate(epdl_json, self.schema)

    def get_schema_version(self) -> str:
        """Get schema version from title"""
        return self.schema.get("title", "Unknown")

    def get_allowed_verbs(self) -> list[str]:
        """Extract allowed verbs from schema"""
        verbs = []

        # Parse oneOf from steps items schema
        steps_schema = self.schema["properties"]["steps"]["items"]
        if "oneOf" in steps_schema:
            for verb_schema in steps_schema["oneOf"]:
                if "required" in verb_schema and verb_schema["required"]:
                    verbs.append(verb_schema["required"][0])

        return verbs
