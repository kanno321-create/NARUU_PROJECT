"""
Unit Tests for core/ssot/branch_bus.py
Coverage target: 51.25% → 75%+

Tests Branch/Bus SSOT Adapter:
- load_branch_bus_rules: JSON SSOT loading and validation
- _validate_schema: Schema validation with error cases
- get_rule: Rule lookup by dot notation
- get_pole_policy: Pole-specific policy retrieval
- get_validation_guards: Validation guards retrieval
- is_n_phase_rightmost: N-phase position check
- get_n_phase_row_rules: 4P N-phase row rules

Zero-Mock exception: Uses unittest.mock to simulate missing/invalid JSON files.
"""

from unittest.mock import MagicMock, patch

import pytest

from kis_estimator_core.core.ssot import branch_bus


class TestLoadBranchBusRules:
    """Tests for load_branch_bus_rules function"""

    def test_load_success(self):
        """Load valid JSON SSOT file - PASS"""
        rules = branch_bus.load_branch_bus_rules()

        assert "meta" in rules
        assert "panel" in rules
        assert "phases" in rules
        assert "policy" in rules
        assert "validation_guards" in rules

    def test_load_file_not_found(self, tmp_path):
        """Load from nonexistent path raises FileNotFoundError (line 36)"""
        # Patch the JSON path to a nonexistent location
        fake_path = tmp_path / "nonexistent.json"

        with patch.object(branch_bus, "_JSON_SSOT_PATH", fake_path):
            with pytest.raises(FileNotFoundError, match="JSON SSOT file not found"):
                branch_bus.load_branch_bus_rules()


class TestValidateSchema:
    """Tests for _validate_schema function"""

    def test_validate_missing_meta_version(self):
        """Missing meta.version raises error (lines 80, 86)"""
        from kis_estimator_core.core.ssot.errors import EstimatorError

        # Rules without meta.version
        invalid_rules = {
            "meta": {},  # Missing 'version'
            "panel": {"layout": "center_feed_single_branch_bus"},
            "phases": {"order": ["R", "S", "T", "N"]},
            "policy": {"2P": {}, "3P": {}, "4P": {}},
            "validation_guards": {
                "phase_alignment": True,
                "bolt_integrity": True,
                "n_no_cross_link": True,
                "outputs_outer_only": True,
                "center_feed_direction": True,
                "row_aware_n_phase": True,
            },
        }

        with pytest.raises(EstimatorError):
            branch_bus._validate_schema(invalid_rules)

    def test_validate_missing_panel(self):
        """Missing panel raises error (line 80)"""
        from kis_estimator_core.core.ssot.errors import EstimatorError

        invalid_rules = {
            "meta": {"version": "1.0"},
            # Missing 'panel'
            "phases": {"order": ["R", "S", "T", "N"]},
            "policy": {"2P": {}, "3P": {}, "4P": {}},
            "validation_guards": {
                "phase_alignment": True,
                "bolt_integrity": True,
                "n_no_cross_link": True,
                "outputs_outer_only": True,
                "center_feed_direction": True,
                "row_aware_n_phase": True,
            },
        }

        with pytest.raises(EstimatorError):
            branch_bus._validate_schema(invalid_rules)

    def test_validate_invalid_layout(self):
        """Invalid panel.layout raises error (line 93)"""
        from kis_estimator_core.core.ssot.errors import EstimatorError

        invalid_rules = {
            "meta": {"version": "1.0"},
            "panel": {"layout": "invalid_layout"},  # Wrong layout
            "phases": {"order": ["R", "S", "T", "N"]},
            "policy": {"2P": {}, "3P": {}, "4P": {}},
            "validation_guards": {
                "phase_alignment": True,
                "bolt_integrity": True,
                "n_no_cross_link": True,
                "outputs_outer_only": True,
                "center_feed_direction": True,
                "row_aware_n_phase": True,
            },
        }

        with pytest.raises(EstimatorError, match="Invalid layout"):
            branch_bus._validate_schema(invalid_rules)

    def test_validate_invalid_phases_order(self):
        """Invalid phases.order raises error (line 100)"""
        from kis_estimator_core.core.ssot.errors import EstimatorError

        invalid_rules = {
            "meta": {"version": "1.0"},
            "panel": {"layout": "center_feed_single_branch_bus"},
            "phases": {"order": ["R", "S"]},  # Missing T and N
            "policy": {"2P": {}, "3P": {}, "4P": {}},
            "validation_guards": {
                "phase_alignment": True,
                "bolt_integrity": True,
                "n_no_cross_link": True,
                "outputs_outer_only": True,
                "center_feed_direction": True,
                "row_aware_n_phase": True,
            },
        }

        with pytest.raises(EstimatorError, match="Invalid phases.order"):
            branch_bus._validate_schema(invalid_rules)


class TestGetRule:
    """Tests for get_rule function (lines 121-137)"""

    def test_get_rule_simple_path(self):
        """Get rule with simple dot notation path"""
        # Get meta.version
        result = branch_bus.get_rule("meta.version")

        assert result is not None
        assert isinstance(result, str)

    def test_get_rule_nested_path(self):
        """Get rule with nested dot notation path"""
        # Get policy.4P.n_phase.row_rules.shared_if_pair
        result = branch_bus.get_rule("policy.4P.n_phase.row_rules.shared_if_pair")

        assert result is True

    def test_get_rule_not_found(self):
        """Get nonexistent rule raises error (lines 131-134)"""
        from kis_estimator_core.core.ssot.errors import EstimatorError

        with pytest.raises(EstimatorError, match="Rule not found"):
            branch_bus.get_rule("nonexistent.path.to.rule")

    def test_get_rule_invalid_path_not_dict(self):
        """Get rule with invalid path (not a dict) raises error (lines 126-130)"""
        from kis_estimator_core.core.ssot.errors import EstimatorError

        # Try to access sub-path of a non-dict value
        with pytest.raises(EstimatorError, match="Invalid rule path"):
            branch_bus.get_rule("meta.version.invalid")


class TestGetPolePolicy:
    """Tests for get_pole_policy function (lines 153-164)"""

    def test_get_pole_policy_2p(self):
        """Get 2P pole policy - PASS"""
        policy = branch_bus.get_pole_policy(2)

        assert "shared_branch_bus" in policy
        assert "bolt_to_main" in policy

    def test_get_pole_policy_3p(self):
        """Get 3P pole policy - PASS"""
        policy = branch_bus.get_pole_policy(3)

        assert "shared_branch_bus" in policy
        assert "bolt_to_main" in policy

    def test_get_pole_policy_4p(self):
        """Get 4P pole policy - PASS"""
        policy = branch_bus.get_pole_policy(4)

        assert "rst_shared_branch_bus" in policy
        assert "n_phase" in policy

    def test_get_pole_policy_invalid_poles(self):
        """Get policy for unsupported poles raises error (lines 153-156)"""
        from kis_estimator_core.core.ssot.errors import EstimatorError

        with pytest.raises(EstimatorError, match="Unsupported poles"):
            branch_bus.get_pole_policy(5)

        with pytest.raises(EstimatorError, match="Unsupported poles"):
            branch_bus.get_pole_policy(1)


class TestGetValidationGuards:
    """Tests for get_validation_guards function"""

    def test_get_validation_guards(self):
        """Get all validation guards - PASS"""
        guards = branch_bus.get_validation_guards()

        assert "phase_alignment" in guards
        assert "bolt_integrity" in guards
        assert "n_no_cross_link" in guards
        assert "outputs_outer_only" in guards
        assert "center_feed_direction" in guards
        assert "row_aware_n_phase" in guards


class TestIsNPhaseRightmost:
    """Tests for is_n_phase_rightmost function (lines 180-181)"""

    def test_is_n_phase_rightmost_true(self):
        """N-phase rightmost check returns True - PASS"""
        result = branch_bus.is_n_phase_rightmost()

        assert result is True


class TestGetNPhaseRowRules:
    """Tests for get_n_phase_row_rules function"""

    def test_get_n_phase_row_rules(self):
        """Get 4P N-phase row rules - PASS"""
        rules = branch_bus.get_n_phase_row_rules()

        assert rules["shared_if_pair"] is True
        assert rules["split_if_single"] is True
        assert rules["no_cross_link"] is True
        assert rules["n_phase_rightmost"] is True
