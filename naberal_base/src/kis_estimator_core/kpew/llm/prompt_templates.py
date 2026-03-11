"""
Prompt Template Manager

Manages prompt templates for LLM integration.
"""

import json
from pathlib import Path

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error


class PromptTemplates:
    """Prompt template manager for LLM orchestrator"""

    @staticmethod
    def load_template(name: str) -> str:
        """Load prompt template by name

        Args:
            name: Template name (e.g., "plan_guard")

        Returns:
            Template content

        Raises:
            FileNotFoundError: If template not found
        """
        # Navigate from src/kis_estimator_core/kpew/llm/prompt_templates.py
        # to specs/prompts/{name}.md
        template_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "specs"
            / "prompts"
            / f"{name}.md"
        )

        if not template_path.exists():
            raise_error(
                ErrorCode.E_INTERNAL,
                f"Template not found: {template_path}\n"
                f"Available templates should be in: specs/prompts/",
            )

        return template_path.read_text(encoding="utf-8")

    @staticmethod
    def format_user_request(request: dict) -> str:
        """Format user request as JSON string

        Args:
            request: User requirements dictionary

        Returns:
            Formatted JSON string for LLM input

        Example:
            >>> request = {
            ...     "customer_name": "테스트고객",
            ...     "main_breaker": {"poles": 3, "current": 100}
            ... }
            >>> formatted = PromptTemplates.format_user_request(request)
            >>> print(formatted)
            {
              "customer_name": "테스트고객",
              "main_breaker": {
                "poles": 3,
                "current": 100
              }
            }
        """
        return json.dumps(request, ensure_ascii=False, indent=2)

    @staticmethod
    def list_templates() -> list[str]:
        """List available prompt templates

        Returns:
            List of template names (without .md extension)
        """
        prompts_dir = (
            Path(__file__).parent.parent.parent.parent.parent / "specs" / "prompts"
        )

        if not prompts_dir.exists():
            return []

        templates = []
        for template_file in prompts_dir.glob("*.md"):
            templates.append(template_file.stem)

        return sorted(templates)
