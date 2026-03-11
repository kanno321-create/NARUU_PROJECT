"""
Unit Tests for EPDL v0.9 System

Tests JSON Schema validation, Pydantic parsing, and verb execution
"""

import pytest

from kis_estimator_core.kpew.dsl.models import (
    EPDLPlan,
    EPDLStep,
    GlobalParams,
    PlaceParams,
    RebalanceParams,
    PickEnclosureParams,
    DocExportParams,
    AssertParams,
)
from kis_estimator_core.kpew.dsl.parser import EPDLParser
from kis_estimator_core.kpew.dsl.schema import EPDLSchemaValidator


class TestEPDLModels:
    """Test Pydantic models"""

    def test_global_params_valid(self):
        """Test valid global params"""
        params = GlobalParams(
            balance_limit=0.03, spare_ratio=0.2, tab_policy="2->1&2 | 3+->1&3"
        )
        assert params.balance_limit == 0.03
        assert params.spare_ratio == 0.2

    def test_global_params_invalid_balance(self):
        """Test invalid balance limit"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            GlobalParams(balance_limit=0.06)  # > 0.05

    def test_place_params(self):
        """Test PLACE verb params"""
        params = PlaceParams(panel="MAIN", algo="greedy", seed=42)
        assert params.panel == "MAIN"
        assert params.algo == "greedy"
        assert params.seed == 42

    def test_rebalance_params(self):
        """Test REBALANCE verb params"""
        params = RebalanceParams(panel="MAIN", method="swap_local", max_iter=100)
        assert params.panel == "MAIN"
        assert params.method == "swap_local"
        assert params.max_iter == 100

    def test_pick_enclosure_params(self):
        """Test PICK_ENCLOSURE verb params"""
        params = PickEnclosureParams(panel="MAIN", strategy="min_size_with_spare")
        assert params.panel == "MAIN"
        assert params.strategy == "min_size_with_spare"

    def test_doc_export_params(self):
        """Test DOC_EXPORT verb params"""
        params = DocExportParams(fmt=["pdf", "xlsx"])
        assert params.fmt == ["pdf", "xlsx"]

    def test_doc_export_unique_formats(self):
        """Test DOC_EXPORT rejects duplicate formats"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            DocExportParams(fmt=["pdf", "pdf"])

    def test_assert_params(self):
        """Test ASSERT verb params"""
        params = AssertParams(imbalance_max=0.03, violations_max=0, fit_score_min=0.90)
        assert params.imbalance_max == 0.03
        assert params.violations_max == 0
        assert params.fit_score_min == 0.90

    def test_epdl_step_single_verb(self):
        """Test EPDLStep with single verb"""
        step = EPDLStep(PLACE=PlaceParams(panel="MAIN", algo="greedy", seed=42))
        assert step.get_verb_name() == "PLACE"
        assert step.get_verb_params().panel == "MAIN"


class TestEPDLParser:
    """Test EPDL parser"""

    def test_parse_valid_plan(self):
        """Test parsing valid EPDL plan"""
        plan_json = {
            "global": {
                "balance_limit": 0.03,
                "spare_ratio": 0.2,
                "tab_policy": "2->1&2 | 3+->1&3",
            },
            "steps": [
                {
                    "PICK_ENCLOSURE": {
                        "panel": "MAIN",
                        "strategy": "min_size_with_spare",
                    }
                },
                {"PLACE": {"panel": "MAIN", "algo": "greedy", "seed": 42}},
                {
                    "REBALANCE": {
                        "panel": "MAIN",
                        "method": "swap_local",
                        "max_iter": 100,
                    }
                },
                {"ASSERT": {"imbalance_max": 0.03, "violations_max": 0}},
            ],
        }

        parser = EPDLParser(validate_schema=False)
        plan = parser.parse(plan_json)

        assert isinstance(plan, EPDLPlan)
        assert plan.global_params.balance_limit == 0.03
        assert len(plan.steps) == 4

    def test_extract_verbs(self):
        """Test extracting verb sequence"""
        plan_json = {
            "global": {
                "balance_limit": 0.03,
                "spare_ratio": 0.2,
                "tab_policy": "2->1&2 | 3+->1&3",
            },
            "steps": [
                {
                    "PICK_ENCLOSURE": {
                        "panel": "MAIN",
                        "strategy": "min_size_with_spare",
                    }
                },
                {"PLACE": {"panel": "MAIN", "algo": "greedy"}},
                {"ASSERT": {"imbalance_max": 0.03}},
            ],
        }

        parser = EPDLParser(validate_schema=False)
        plan = parser.parse(plan_json)
        verbs = parser.extract_verbs(plan)

        assert verbs == ["PICK_ENCLOSURE", "PLACE", "ASSERT"]

    def test_validate_semantics(self):
        """Test semantic validation"""
        plan_json = {
            "global": {
                "balance_limit": 0.03,
                "spare_ratio": 0.2,
                "tab_policy": "2->1&2 | 3+->1&3",
            },
            "steps": [
                {
                    "PLACE": {"panel": "MAIN", "algo": "greedy"}
                },  # No PICK_ENCLOSURE before
                {
                    "PICK_ENCLOSURE": {
                        "panel": "MAIN",
                        "strategy": "min_size_with_spare",
                    }
                },
                {"ASSERT": {"imbalance_max": 0.03}},
                {"DOC_EXPORT": {"fmt": ["pdf"]}},  # DOC_EXPORT after ASSERT
            ],
        }

        parser = EPDLParser(validate_schema=False)
        plan = parser.parse(plan_json)
        warnings = parser.validate_plan_semantics(plan)

        # Should have warnings about PLACE before PICK_ENCLOSURE and DOC_EXPORT after ASSERT
        assert len(warnings) >= 2

    def test_to_json(self):
        """Test converting plan back to JSON"""
        plan_json = {
            "global": {
                "balance_limit": 0.03,
                "spare_ratio": 0.2,
                "tab_policy": "2->1&2 | 3+->1&3",
            },
            "steps": [{"PLACE": {"panel": "MAIN", "algo": "greedy", "seed": 42}}],
        }

        parser = EPDLParser(validate_schema=False)
        plan = parser.parse(plan_json)
        reconstructed = parser.to_json(plan)

        assert reconstructed["global"]["balance_limit"] == 0.03
        assert reconstructed["steps"][0]["PLACE"]["panel"] == "MAIN"


class TestEPDLSchemaValidator:
    """Test JSON Schema validator"""

    @pytest.fixture
    def validator(self):
        """Create validator instance"""
        return EPDLSchemaValidator()

    def test_validate_valid_plan(self, validator):
        """Test validating valid plan"""
        plan_json = {
            "global": {
                "balance_limit": 0.03,
                "spare_ratio": 0.2,
                "tab_policy": "2->1&2 | 3+->1&3",
            },
            "steps": [
                {
                    "PICK_ENCLOSURE": {
                        "panel": "MAIN",
                        "strategy": "min_size_with_spare",
                    }
                },
                {"PLACE": {"panel": "MAIN", "algo": "greedy", "seed": 42}},
                {
                    "REBALANCE": {
                        "panel": "MAIN",
                        "method": "swap_local",
                        "max_iter": 100,
                    }
                },
                {"ASSERT": {"imbalance_max": 0.03, "violations_max": 0}},
            ],
        }

        is_valid, errors = validator.validate(plan_json)
        assert is_valid
        assert len(errors) == 0

    def test_validate_missing_global(self, validator):
        """Test validation fails with missing global"""
        plan_json = {"steps": [{"PLACE": {"panel": "MAIN", "algo": "greedy"}}]}

        is_valid, errors = validator.validate(plan_json)
        assert not is_valid
        assert len(errors) > 0

    def test_validate_invalid_verb(self, validator):
        """Test validation fails with invalid verb"""
        plan_json = {
            "global": {
                "balance_limit": 0.03,
                "spare_ratio": 0.2,
                "tab_policy": "2->1&2 | 3+->1&3",
            },
            "steps": [{"INVALID_VERB": {"panel": "MAIN"}}],
        }

        is_valid, errors = validator.validate(plan_json)
        assert not is_valid
        assert len(errors) > 0

    def test_validate_invalid_balance_limit(self, validator):
        """Test validation fails with invalid balance limit"""
        plan_json = {
            "global": {
                "balance_limit": 0.06,  # > 0.05 (invalid)
                "spare_ratio": 0.2,
                "tab_policy": "2->1&2 | 3+->1&3",
            },
            "steps": [{"PLACE": {"panel": "MAIN", "algo": "greedy"}}],
        }

        is_valid, errors = validator.validate(plan_json)
        assert not is_valid

    def test_get_allowed_verbs(self, validator):
        """Test extracting allowed verbs from schema"""
        verbs = validator.get_allowed_verbs()
        expected = [
            "PLACE",
            "REBALANCE",
            "TRY",
            "PICK_ENCLOSURE",
            "DOC_EXPORT",
            "ASSERT",
        ]
        assert set(verbs) == set(expected)

    def test_get_schema_version(self, validator):
        """Test getting schema version"""
        version = validator.get_schema_version()
        assert "EPDL" in version
        assert "v0.9" in version


class TestEPDLIntegration:
    """Integration tests for complete EPDL workflow"""

    def test_full_parse_and_validate(self):
        """Test full parsing and validation workflow"""
        plan_json = {
            "global": {
                "balance_limit": 0.03,
                "spare_ratio": 0.2,
                "tab_policy": "2->1&2 | 3+->1&3",
            },
            "steps": [
                {
                    "PICK_ENCLOSURE": {
                        "panel": "MAIN",
                        "strategy": "min_size_with_spare",
                    }
                },
                {"PLACE": {"panel": "MAIN", "algo": "greedy", "seed": 42}},
                {
                    "REBALANCE": {
                        "panel": "MAIN",
                        "method": "swap_local",
                        "max_iter": 100,
                    }
                },
                {
                    "ASSERT": {
                        "imbalance_max": 0.03,
                        "violations_max": 0,
                        "fit_score_min": 0.90,
                    }
                },
            ],
        }

        # Step 1: JSON Schema validation
        validator = EPDLSchemaValidator()
        is_valid, errors = validator.validate(plan_json)
        assert is_valid, f"Schema validation failed: {errors}"

        # Step 2: Pydantic parsing
        parser = EPDLParser(validate_schema=False)
        plan = parser.parse(plan_json)
        assert isinstance(plan, EPDLPlan)

        # Step 3: Extract verb sequence
        verbs = parser.extract_verbs(plan)
        assert verbs == ["PICK_ENCLOSURE", "PLACE", "REBALANCE", "ASSERT"]

        # Step 4: Semantic validation
        warnings = parser.validate_plan_semantics(plan)
        # PICK_ENCLOSURE before PLACE is correct, should have minimal warnings
        assert len(warnings) <= 1  # Only ASSERT not at end warning

        # Step 5: Convert back to JSON
        reconstructed = parser.to_json(plan)
        assert reconstructed["global"]["balance_limit"] == 0.03
        assert len(reconstructed["steps"]) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
