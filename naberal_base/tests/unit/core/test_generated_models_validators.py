"""
Phase I-4 Supplement: generated_models.py validator coverage tests

Target: 90.57% → 95%+ by covering validator error paths (lines 42, 48-51)
"""

import pytest
from pydantic import ValidationError

from kis_estimator_core.core.ssot.generated_models import (
    BreakerInput,
    EnclosureDimensionsInput,
    EnclosureInput,
    PlacementInput,
)


# ============================================================
# BreakerInput Validator Tests
# ============================================================


def test_breaker_input_valid_poles():
    """Valid poles (2, 3, 4) should pass"""
    for poles in [2, 3, 4]:
        breaker = BreakerInput(
            id="TEST",
            frame=100,  # Use alias (required)
            current=75,  # Use alias (required)
            poles=poles,
        )
        assert breaker.poles == poles


def test_breaker_input_invalid_poles():
    """Invalid poles should raise ValidationError (line 42)"""
    with pytest.raises(ValidationError) as exc_info:
        BreakerInput(
            id="TEST",
            frame=100,
            current=75,
            poles=5,  # Invalid
        )

    # Verify error message contains validator error
    error_msg = str(exc_info.value)
    assert "poles must be 2, 3, or 4" in error_msg


def test_breaker_input_valid_frames():
    """Valid frames should pass"""
    valid_frames = [32, 50, 60, 100, 125, 200, 225, 250, 400, 600, 800]
    for frame in valid_frames:
        breaker = BreakerInput(
            id="TEST",
            frame=frame,  # Use alias
            current=75,
            poles=3,
        )
        assert breaker.frame_af == frame


def test_breaker_input_invalid_frame():
    """Invalid frame should raise ValidationError (lines 48-51)"""
    with pytest.raises(ValidationError) as exc_info:
        BreakerInput(
            id="TEST",
            frame=999,  # Invalid frame
            current=75,
            poles=3,
        )

    # Verify error message contains validator error
    error_msg = str(exc_info.value)
    assert "frame_af must be in" in error_msg


def test_breaker_input_with_alias():
    """Test alias support (frame/current)"""
    breaker = BreakerInput(
        id="TEST",
        frame=100,  # Using alias
        current=75,  # Using alias
        poles=3,
    )
    assert breaker.frame_af == 100
    assert breaker.current_a == 75


def test_breaker_input_full_fields():
    """Test all fields including optional ones"""
    breaker = BreakerInput(
        id="MAIN",
        model="SBE-104",
        frame=100,  # Use alias
        current=75,  # Use alias
        poles=4,
        width_mm=100.0,
        height_mm=130.0,
        depth_mm=60.0,
        breaker_type="elb",
        type="ELB",
    )
    assert breaker.id == "MAIN"
    assert breaker.model == "SBE-104"
    assert breaker.type == "ELB"


# ============================================================
# EnclosureDimensionsInput Tests
# ============================================================


def test_enclosure_dimensions_valid():
    """Valid dimensions should pass"""
    dims = EnclosureDimensionsInput(
        width_mm=600.0,
        height_mm=800.0,
        depth_mm=200.0,
    )
    assert dims.width_mm == 600.0
    assert dims.height_mm == 800.0
    assert dims.depth_mm == 200.0


def test_enclosure_dimensions_forbid_extra():
    """Extra fields should be forbidden"""
    with pytest.raises(ValidationError):
        EnclosureDimensionsInput(
            width_mm=600.0,
            height_mm=800.0,
            depth_mm=200.0,
            extra_field="not_allowed",  # Should fail
        )


# ============================================================
# EnclosureInput Tests
# ============================================================


def test_enclosure_input_with_size():
    """Test with 'size' field"""
    enclosure = EnclosureInput(
        id="ENC1",
        code="HDS-600*800*200",
        size=EnclosureDimensionsInput(
            width_mm=600.0,
            height_mm=800.0,
            depth_mm=200.0,
        ),
        enclosure_type="옥내노출",
        material="STEEL",
        thickness="1.6T",
    )
    assert enclosure.id == "ENC1"
    assert enclosure.size.width_mm == 600.0


def test_enclosure_input_with_dimensions():
    """Test with 'dimensions' field (alternative)"""
    enclosure = EnclosureInput(
        dimensions=EnclosureDimensionsInput(
            width_mm=700.0,
            height_mm=900.0,
            depth_mm=250.0,
        ),
    )
    assert enclosure.dimensions.width_mm == 700.0


def test_enclosure_input_extra_allowed():
    """Extra fields should be allowed"""
    enclosure = EnclosureInput(
        id="ENC1",
        extra_custom_field="allowed",  # Should pass
    )
    assert enclosure.id == "ENC1"


# ============================================================
# PlacementInput Tests
# ============================================================


def test_placement_input_minimal():
    """Test minimal required fields"""
    placement = PlacementInput(
        breaker_id="BR1",
        x=100.0,
        y=200.0,
    )
    assert placement.breaker_id == "BR1"
    assert placement.x == 100.0
    assert placement.y == 200.0


def test_placement_input_full():
    """Test all fields"""
    placement = PlacementInput(
        breaker_id="BR1",
        x=100.0,
        y=200.0,
        phase="R",
        row=1,
        column=2,
    )
    assert placement.phase == "R"
    assert placement.row == 1
    assert placement.column == 2


def test_placement_input_extra_allowed():
    """Extra fields should be allowed"""
    placement = PlacementInput(
        breaker_id="BR1",
        x=100.0,
        y=200.0,
        custom_field="allowed",
    )
    assert placement.breaker_id == "BR1"
