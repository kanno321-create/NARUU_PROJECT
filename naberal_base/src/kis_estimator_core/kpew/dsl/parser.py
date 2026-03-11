"""
EPDL Parser

Parses and validates EPDL JSON to Pydantic models
"""


from pydantic import ValidationError

from .models import EPDLPlan
from .schema import EPDLSchemaValidator


class EPDLParseError(Exception):
    """EPDL parsing error"""

    pass


class EPDLParser:
    """Parser for EPDL v0.9"""

    def __init__(self, validate_schema: bool = True):
        """
        Initialize parser

        Args:
            validate_schema: Whether to validate against JSON Schema first
        """
        self.validate_schema = validate_schema
        if validate_schema:
            self.schema_validator = EPDLSchemaValidator()

    @staticmethod
    def parse(epdl_json: dict) -> EPDLPlan:
        """
        Parse EPDL JSON to Pydantic model

        Args:
            epdl_json: Raw EPDL JSON from LLM

        Returns:
            EPDLPlan: Validated Pydantic model

        Raises:
            ValidationError: If JSON structure is invalid
            EPDLParseError: If parsing fails
        """
        try:
            return EPDLPlan.model_validate(epdl_json)
        except ValidationError as e:
            error_msg = f"EPDL parsing failed:\n{str(e)}"
            raise EPDLParseError(error_msg) from e

    def parse_with_schema_validation(self, epdl_json: dict) -> EPDLPlan:
        """
        Parse EPDL with JSON Schema validation first

        Args:
            epdl_json: Raw EPDL JSON

        Returns:
            EPDLPlan: Validated plan

        Raises:
            EPDLParseError: If schema validation or parsing fails
        """
        # Step 1: JSON Schema validation
        if self.validate_schema:
            is_valid, errors = self.schema_validator.validate(epdl_json)
            if not is_valid:
                error_msg = "JSON Schema validation failed:\n" + "\n".join(errors)
                raise EPDLParseError(error_msg)

        # Step 2: Pydantic parsing
        try:
            return EPDLPlan.model_validate(epdl_json)
        except ValidationError as e:
            error_msg = f"Pydantic validation failed:\n{str(e)}"
            raise EPDLParseError(error_msg) from e

    @staticmethod
    def extract_verbs(plan: EPDLPlan) -> list[str]:
        """
        Extract list of verbs from plan

        Args:
            plan: Parsed EPDL plan

        Returns:
            List of verb names in order, e.g. ["PLACE", "REBALANCE", "TRY", ...]
        """
        return plan.get_verb_sequence()

    @staticmethod
    def extract_verb_params(plan: EPDLPlan) -> list[dict]:
        """
        Extract verb parameters from plan

        Args:
            plan: Parsed EPDL plan

        Returns:
            List of (verb_name, params) dictionaries
        """
        result = []
        for step in plan.steps:
            verb_name = step.get_verb_name()
            params = step.get_verb_params().model_dump()
            result.append({"verb": verb_name, "params": params})
        return result

    @staticmethod
    def validate_plan_semantics(plan: EPDLPlan) -> list[str]:
        """
        Validate plan semantics (beyond schema validation)

        Args:
            plan: Parsed EPDL plan

        Returns:
            List of semantic warnings (empty if no issues)
        """
        warnings = []

        # Check 1: ASSERT should typically be last
        verbs = plan.get_verb_sequence()
        if "ASSERT" in verbs and verbs[-1] != "ASSERT":
            warnings.append(
                "Warning: ASSERT verb found but not at end of plan. "
                "Quality gates typically execute last."
            )

        # Check 2: DOC_EXPORT before ASSERT
        if "DOC_EXPORT" in verbs and "ASSERT" in verbs:
            doc_idx = verbs.index("DOC_EXPORT")
            assert_idx = verbs.index("ASSERT")
            if doc_idx > assert_idx:
                warnings.append(
                    "Warning: DOC_EXPORT after ASSERT. "
                    "Documents should be generated after validation."
                )

        # Check 3: PICK_ENCLOSURE before PLACE
        if "PLACE" in verbs and "PICK_ENCLOSURE" not in verbs[: verbs.index("PLACE")]:
            warnings.append(
                "Warning: PLACE without prior PICK_ENCLOSURE. "
                "Enclosure should be calculated before placement."
            )

        # Check 4: Multiple TRY verbs (unusual)
        if verbs.count("TRY") > 1:
            warnings.append(
                "Warning: Multiple TRY verbs found. "
                "Multiple MILP fallbacks may indicate plan issues."
            )

        return warnings

    @staticmethod
    def to_json(plan: EPDLPlan) -> dict:
        """
        Convert plan back to JSON format

        Args:
            plan: EPDL plan

        Returns:
            JSON-compatible dictionary
        """
        return plan.to_dict()
