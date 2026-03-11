"""
LLM integration for EPDL generation

Real Claude API integration - NO MOCKS, NO DUMMIES.
"""

from .orchestrator import LLMOrchestrator, LLMOrchestratorError
from .prompt_templates import PromptTemplates

__all__ = [
    "LLMOrchestrator",
    "LLMOrchestratorError",
    "PromptTemplates",
]
