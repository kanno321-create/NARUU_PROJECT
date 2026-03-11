"""
LLM Orchestrator for EPDL Plan Generation

REAL Claude API integration for generating EPDL plans from user requirements.
NO MOCKS, NO DUMMIES - Production-ready implementation.
"""

import json
import os
import time
from pathlib import Path

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error

try:
    import anthropic
    from anthropic import APIError, APITimeoutError, RateLimitError

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None  # type: ignore
    APIError = Exception  # type: ignore
    APITimeoutError = Exception  # type: ignore
    RateLimitError = Exception  # type: ignore


class LLMOrchestratorError(Exception):
    """LLM orchestrator error"""

    pass


class LLMOrchestrator:
    """LLM Orchestrator for EPDL Plan Generation

    Uses Claude API to generate EPDL plans from user requirements.
    Enforces strict prompt guard to prevent LLM from doing calculations.
    """

    def __init__(self, provider: str = "claude", model: str | None = None):
        """Initialize LLM orchestrator

        Args:
            provider: "claude" (only supported provider)
            model: Model name (default: claude-3-5-sonnet-20241022)

        Raises:
            ValueError: If provider unsupported or API key missing
            ImportError: If anthropic package not installed
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package required for LLM orchestrator.\n"
                "Install: pip install anthropic"
            )

        if provider != "claude":
            raise_error(
                ErrorCode.E_INTERNAL,
                f"Unsupported provider: {provider}. Only 'claude' is supported.",
            )

        self.provider = provider
        self.model = model or "claude-sonnet-4-5-20241022"

        # Real Anthropic API client (NO MOCKS!)
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise_error(
                ErrorCode.E_INTERNAL,
                "ANTHROPIC_API_KEY environment variable not set.\n"
                "Set it with: export ANTHROPIC_API_KEY='your-api-key'",
            )

        self.client = anthropic.Anthropic(api_key=api_key)

        # Load prompt guard
        self.system_prompt = self._load_prompt_guard()

    def _load_prompt_guard(self) -> str:
        """Load prompt guard from specs/prompts/plan_guard.md

        Returns:
            Prompt guard content

        Raises:
            FileNotFoundError: If prompt guard file not found
        """
        # Navigate from src/kis_estimator_core/kpew/llm/orchestrator.py
        # to specs/prompts/plan_guard.md
        prompt_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "specs"
            / "prompts"
            / "plan_guard.md"
        )

        if not prompt_path.exists():
            raise_error(
                ErrorCode.E_INTERNAL,
                f"Prompt guard not found: {prompt_path}\n"
                f"Expected location: specs/prompts/plan_guard.md",
            )

        return prompt_path.read_text(encoding="utf-8")

    def generate_plan(self, user_request: dict) -> tuple[dict, dict]:
        """Generate EPDL plan from user request

        Uses REAL Claude API to generate valid EPDL JSON.

        Args:
            user_request: User requirements (customer, breakers, etc)
                Example:
                {
                    "customer_name": "테스트고객",
                    "project_name": "인천현장",
                    "main_breaker": {"poles": 3, "current": 100, "frame": 100},
                    "branch_breakers": [
                        {"poles": 2, "current": 20, "frame": 50}
                    ],
                    "enclosure_type": "옥내노출",
                    "accessories": []
                }

        Returns:
            (epdl_json, metadata)
            - epdl_json: Valid EPDL plan dictionary
            - metadata: {
                "model": str,
                "prompt_tokens": int,
                "completion_tokens": int,
                "total_tokens": int,
                "latency_ms": int
              }

        Raises:
            LLMOrchestratorError: If API call fails or JSON invalid
        """
        # Format user request as JSON
        user_message = json.dumps(user_request, ensure_ascii=False, indent=2)

        start_time = time.time()

        try:
            # REAL Claude API call (NO MOCKS!)
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=self.system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            latency_ms = int((time.time() - start_time) * 1000)

            # Extract JSON from response
            content = response.content[0].text

            # Parse JSON (strict - no markdown allowed)
            try:
                epdl_json = json.loads(content)
            except json.JSONDecodeError as e:
                # Try to extract JSON from markdown if LLM violated rules
                if "```json" in content:
                    # Extract from markdown
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    if json_end == -1:
                        raise LLMOrchestratorError(
                            f"Invalid JSON response from LLM (malformed markdown): {e}"
                        ) from e
                    json_str = content[json_start:json_end].strip()
                    try:
                        epdl_json = json.loads(json_str)
                    except json.JSONDecodeError as e2:
                        raise LLMOrchestratorError(
                            f"Invalid JSON in markdown block: {e2}"
                        ) from e2
                elif "```" in content:
                    # Try generic code block
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    if json_end == -1:
                        raise LLMOrchestratorError(
                            f"Invalid JSON response from LLM (malformed code block): {e}"
                        ) from e
                    json_str = content[json_start:json_end].strip()
                    try:
                        epdl_json = json.loads(json_str)
                    except json.JSONDecodeError as e2:
                        raise LLMOrchestratorError(f"Invalid JSON in code block: {e2}") from e2
                else:
                    raise LLMOrchestratorError(
                        f"Invalid JSON response from LLM: {e}\n"
                        f"Response content: {content[:200]}"
                    ) from e

            # Metadata
            metadata = {
                "model": self.model,
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens
                + response.usage.output_tokens,
                "latency_ms": latency_ms,
            }

            return epdl_json, metadata

        except RateLimitError as e:
            raise LLMOrchestratorError(f"Rate limit exceeded: {e}") from e
        except APITimeoutError as e:
            raise LLMOrchestratorError(f"API timeout: {e}") from e
        except APIError as e:
            raise LLMOrchestratorError(f"API error: {e}") from e
        except Exception as e:
            if isinstance(e, LLMOrchestratorError):
                raise
            raise LLMOrchestratorError(f"Unexpected error: {e}") from e
