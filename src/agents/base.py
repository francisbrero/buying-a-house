"""Base agent setup and shared utilities."""

import os
from functools import lru_cache

from agents import Agent, Runner
from openai import OpenAI

from src.storage import JsonStore
from src.services.openrouter import OpenRouterClient


@lru_cache()
def get_openai_client() -> OpenAI:
    """Get OpenAI client configured for OpenRouter."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable required")

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "http://localhost",
            "X-Title": "House Evaluator",
        },
    )


def get_openrouter_client() -> OpenRouterClient:
    """Get OpenRouter client for vision requests."""
    return OpenRouterClient()


# Default models - using Gemini 3 Flash for best price/performance
DEFAULT_MODEL = "google/gemini-3-flash-preview"
VISION_MODEL = "google/gemini-3-flash-preview"
FAST_MODEL = "google/gemini-2.0-flash-001"


class BaseAgent:
    """Base class for house evaluator agents."""

    name: str = "base"
    instructions: str = "You are a helpful assistant."
    model: str = DEFAULT_MODEL

    def __init__(self, store: JsonStore):
        self.store = store
        self._client = get_openai_client()
        self._openrouter = None

    @property
    def openrouter(self) -> OpenRouterClient:
        """Lazy-load OpenRouter client for vision."""
        if self._openrouter is None:
            self._openrouter = get_openrouter_client()
        return self._openrouter

    def create_agent(self, **kwargs) -> Agent:
        """Create an OpenAI Agent SDK agent."""
        return Agent(
            name=self.name,
            instructions=self.instructions,
            model=self.model,
            **kwargs,
        )

    def run_sync(self, agent: Agent, prompt: str) -> str:
        """Run an agent synchronously and return the response."""
        result = Runner.run_sync(agent, prompt)
        return result.final_output

    def cleanup(self):
        """Clean up resources."""
        if self._openrouter:
            self._openrouter.close()


# Shared instruction components
AESTHETIC_CONTEXT = """
You are evaluating residential real estate listings for aesthetic and functional fit.
Your analysis should be detailed, specific, and actionable.
Focus on visual and spatial qualities, not just features.
Be honest about both positives and negatives.
"""

SCORING_CONTEXT = """
When scoring, use the full 0-100 range meaningfully:
- 90-100: Exceptional match, meets virtually all criteria
- 80-89: Strong match, minor compromises
- 70-79: Good match, some notable trade-offs
- 60-69: Acceptable, significant compromises needed
- 50-59: Marginal, major issues present
- 40-49: Poor match, fundamental problems
- Below 40: Significant mismatch, likely reject

Be conservative - it's better to under-score than over-score.
A house that barely passes should score in the 60s, not 70s.
"""
