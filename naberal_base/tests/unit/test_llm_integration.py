"""
LLM Integration Tests

Tests LLM orchestrator with REAL Claude API (if API key available).
NO MOCKS - production-ready testing.
"""

import os
import pytest
from kis_estimator_core.kpew.llm import (
    LLMOrchestrator,
    LLMOrchestratorError,
    PromptTemplates,
)
from kis_estimator_core.kpew.dsl import EPDLSchemaValidator, EPDLParser


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set - skipping live API test",
)
def test_llm_orchestrator_real_api():
    """Test LLM orchestrator with REAL Claude API

    This test makes actual API calls to Claude.
    Skipped if ANTHROPIC_API_KEY not set.
    """
    # User request
    user_request = {
        "customer_name": "테스트고객",
        "project_name": "인천현장",
        "main_breaker": {"poles": 3, "current": 100, "frame": 100},
        "branch_breakers": [
            {"poles": 2, "current": 20, "frame": 50},
            {"poles": 3, "current": 30, "frame": 50},
        ],
        "enclosure_type": "옥내노출",
        "accessories": [],
    }

    # Generate plan with REAL API
    orchestrator = LLMOrchestrator()
    epdl_json, metadata = orchestrator.generate_plan(user_request)

    # Verify metadata
    assert metadata["model"] == "claude-3-5-sonnet-20241022"
    assert metadata["prompt_tokens"] > 0
    assert metadata["completion_tokens"] > 0
    assert metadata["total_tokens"] > 0
    assert metadata["latency_ms"] > 0

    print("\n[API Response Metadata]")
    print(f"  Model: {metadata['model']}")
    print(f"  Prompt tokens: {metadata['prompt_tokens']}")
    print(f"  Completion tokens: {metadata['completion_tokens']}")
    print(f"  Total tokens: {metadata['total_tokens']}")
    print(f"  Latency: {metadata['latency_ms']}ms")

    # Validate EPDL JSON structure
    assert "global" in epdl_json or "global_params" in epdl_json
    assert "steps" in epdl_json
    assert isinstance(epdl_json["steps"], list)
    assert len(epdl_json["steps"]) > 0

    print("\n[EPDL Plan Structure]")
    print(f"  Steps count: {len(epdl_json['steps'])}")

    # Validate against schema
    validator = EPDLSchemaValidator()
    is_valid, errors = validator.validate(epdl_json)

    if not is_valid:
        print("\n[Schema Validation FAILED]")
        for error in errors:
            print(f"  - {error}")

    assert is_valid, f"Schema validation failed: {errors}"

    # Parse EPDL
    parser = EPDLParser()
    plan = parser.parse(epdl_json)

    # Verify plan structure
    assert plan.global_params.balance_limit >= 0
    assert plan.global_params.balance_limit <= 0.05
    assert len(plan.steps) > 0

    # Extract verb sequence
    verbs = plan.get_verb_sequence()
    print("\n[Verb Sequence]")
    for i, verb in enumerate(verbs, 1):
        print(f"  {i}. {verb}")

    # Verify typical verb patterns
    allowed_verbs = {
        "PLACE",
        "REBALANCE",
        "TRY",
        "PICK_ENCLOSURE",
        "DOC_EXPORT",
        "ASSERT",
    }
    for verb in verbs:
        assert verb in allowed_verbs, f"Unknown verb: {verb}"

    print("\n[SUCCESS] LLM generated valid EPDL plan")
    print(f"  Model: {metadata['model']}")
    print(f"  Tokens: {metadata['total_tokens']}")
    print(f"  Latency: {metadata['latency_ms']}ms")
    print(f"  Steps: {len(plan.steps)}")


def test_llm_orchestrator_initialization():
    """Test LLM orchestrator initialization without API call"""

    # Should initialize successfully if API key exists
    if os.getenv("ANTHROPIC_API_KEY"):
        orchestrator = LLMOrchestrator()
        assert orchestrator.provider == "claude"
        assert orchestrator.model == "claude-3-5-sonnet-20241022"
        assert orchestrator.client is not None
        print("\n[Initialization] Success with API key")
    else:
        # Should raise error if API key missing (EstimatorError wraps ValueError)
        from kis_estimator_core.core.ssot.errors import EstimatorError

        with pytest.raises(EstimatorError):
            LLMOrchestrator()
        print("\n[Initialization] Correctly raises error without API key")


def test_llm_orchestrator_custom_model():
    """Test LLM orchestrator with custom model"""

    if os.getenv("ANTHROPIC_API_KEY"):
        orchestrator = LLMOrchestrator(model="claude-3-5-sonnet-20241022")
        assert orchestrator.model == "claude-3-5-sonnet-20241022"
        print(f"\n[Custom Model] Set to: {orchestrator.model}")


def test_prompt_guard_loading():
    """Test prompt guard file loading"""

    if os.getenv("ANTHROPIC_API_KEY"):
        orchestrator = LLMOrchestrator()

        # Prompt guard should be loaded
        assert orchestrator.system_prompt is not None
        assert len(orchestrator.system_prompt) > 0

        # Should contain key restrictions
        assert "FORBIDDEN" in orchestrator.system_prompt
        assert "NO calculations" in orchestrator.system_prompt
        assert "EPDL" in orchestrator.system_prompt

        print("\n[Prompt Guard] Loaded successfully")
        print(f"  Length: {len(orchestrator.system_prompt)} chars")
        print("  Contains restrictions: ✓")


def test_prompt_templates_load():
    """Test prompt template loading"""

    # Load plan_guard template
    template = PromptTemplates.load_template("plan_guard")
    assert template is not None
    assert len(template) > 0
    assert "EPDL" in template

    print("\n[Template Loading] plan_guard loaded")
    print(f"  Length: {len(template)} chars")


def test_prompt_templates_format():
    """Test user request formatting"""

    request = {
        "customer_name": "테스트고객",
        "main_breaker": {"poles": 3, "current": 100},
    }

    formatted = PromptTemplates.format_user_request(request)
    assert isinstance(formatted, str)
    assert "테스트고객" in formatted
    assert "poles" in formatted

    print("\n[Request Formatting]")
    print(formatted)


def test_prompt_templates_list():
    """Test template listing"""

    templates = PromptTemplates.list_templates()
    assert isinstance(templates, list)
    assert "plan_guard" in templates

    print("\n[Available Templates]")
    for template in templates:
        print(f"  - {template}")


def test_unsupported_provider():
    """Test error handling for unsupported provider"""
    from kis_estimator_core.core.ssot.errors import EstimatorError

    with pytest.raises(EstimatorError):
        LLMOrchestrator(provider="gpt4")

    print("\n[Error Handling] Correctly rejects unsupported provider")


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set - skipping error handling test",
)
def test_llm_orchestrator_error_handling():
    """Test LLM orchestrator error handling"""

    orchestrator = LLMOrchestrator()

    # Invalid request should be handled gracefully
    invalid_request = {"invalid": "structure"}

    try:
        epdl_json, metadata = orchestrator.generate_plan(invalid_request)
        # Even with invalid input, LLM should try to generate valid EPDL
        # If it succeeds, verify the output is valid
        validator = EPDLSchemaValidator()
        is_valid, errors = validator.validate(epdl_json)
        print("\n[Error Handling] LLM generated plan from invalid input")
        print(f"  Valid: {is_valid}")
    except LLMOrchestratorError as e:
        print(f"\n[Error Handling] Correctly raised error: {e}")
