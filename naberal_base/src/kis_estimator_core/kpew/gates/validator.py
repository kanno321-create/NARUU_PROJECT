"""
Quality Gate Validator for K-PEW Pipeline
Enforces quality gates based on estimation.yaml policy
"""

from pathlib import Path

import yaml

from ...errors.error_codes import ENC_001, LAY_001, LAY_002
from ...errors.exceptions import EstimatorError


class GateValidator:
    """Quality gate validator based on policy file"""

    def __init__(self):
        policy_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "specs"
            / "gates"
            / "estimation.yaml"
        )
        with open(policy_path, encoding="utf-8") as f:
            self.policy = yaml.safe_load(f)

    def validate_balance(
        self, phase_loads: dict[str, float]
    ) -> tuple[bool, list[EstimatorError]]:
        """Check phase balance ≤ balance_limit

        Args:
            phase_loads: {"Ia": 100, "Ib": 98, "Ic": 102} or {"L1": 100, "L2": 98, "L3": 102}

        Returns:
            (is_valid, errors)
        """
        errors = []

        # Normalize keys
        normalized_loads = {}
        for key, value in phase_loads.items():
            if key in ["Ia", "L1"]:
                normalized_loads["L1"] = value
            elif key in ["Ib", "L2"]:
                normalized_loads["L2"] = value
            elif key in ["Ic", "L3"]:
                normalized_loads["L3"] = value

        # Calculate imbalance
        loads = [
            normalized_loads.get("L1", 0),
            normalized_loads.get("L2", 0),
            normalized_loads.get("L3", 0),
        ]
        avg_load = sum(loads) / len(loads) if loads else 0

        if avg_load == 0:
            return True, []  # No load = no imbalance

        max_diff = max(abs(load - avg_load) for load in loads)
        imbalance = max_diff / avg_load

        limit = self.policy["rules"]["balance_limit"]

        if imbalance > limit:
            errors.append(
                EstimatorError(
                    error_code=LAY_001,
                    phase="Stage 3: Balance",
                    details={
                        "imbalance": imbalance,
                        "limit": limit,
                        "phase_loads": phase_loads,
                    },
                )
            )
            return False, errors

        return True, []

    def validate_fit_score(self, fit_score: float) -> tuple[bool, list[EstimatorError]]:
        """Check fit_score ≥ fit_score_min"""
        errors = []

        min_score = self.policy["rules"]["fit_score_min"]

        if fit_score < min_score:
            errors.append(
                EstimatorError(
                    error_code=ENC_001,
                    phase="Stage 1: Enclosure",
                    details={"fit_score": fit_score, "min_required": min_score},
                )
            )
            return False, errors

        return True, []

    def validate_violations(
        self, violations: list[str]
    ) -> tuple[bool, list[EstimatorError]]:
        """Check violations = 0"""
        errors = []

        forbid_violations = self.policy["rules"]["forbid_violations"]

        if forbid_violations and len(violations) > 0:
            for violation in violations:
                errors.append(
                    EstimatorError(
                        error_code=LAY_002,
                        phase="Stage 2: Layout",
                        details={"violation": violation},
                    )
                )
            return False, errors

        return True, []
