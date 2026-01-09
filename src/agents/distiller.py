"""Distiller agent - regenerates aesthetics.md from taste model."""

from src.storage import JsonStore
from .base import BaseAgent, DEFAULT_MODEL


DISTILLER_INSTRUCTIONS = """You are the Distillation Agent. Your job is to transform
the machine-readable taste model into a clear, human-readable aesthetics.md document.

The document should:
- Be scannable and well-organized
- Capture the essence of preferences
- Include examples where helpful
- Note any tensions or open questions
- Be useful as a reference during house hunting

Format as markdown with clear sections.
"""


class DistillerAgent(BaseAgent):
    """Agent for distilling taste model to aesthetics.md."""

    name = "distiller"
    model = DEFAULT_MODEL
    instructions = DISTILLER_INSTRUCTIONS

    def distill(self) -> str:
        """Generate aesthetics.md content from taste model."""
        taste = self.store.load_or_create_taste()

        # Build comprehensive context
        context = f"""## Taste Model Data

### Core Principles
{chr(10).join('- ' + p for p in taste.principles) or '(none)'}

### Anti-Principles (Things to Avoid)
{chr(10).join('- ' + p for p in taste.anti_principles) or '(none)'}

### Hard Constraints (Must Have)
{chr(10).join('- ' + c for c in taste.hard_constraints) or '(none)'}

### Soft Constraints (Prefer)
{chr(10).join('- ' + c for c in taste.soft_constraints) or '(none)'}

### Violation Patterns (Auto-Reject Signals)
{chr(10).join('- ' + v for v in taste.violation_patterns) or '(none)'}

### Weighted Dimensions
"""
        for dim in taste.dimensions:
            context += f"- {dim.name} ({dim.weight:.0%}): {dim.description}\n"

        context += f"""
### Location Preferences
{taste.location_preferences or '(none specified)'}

### Renovation Stance
- Tolerance: {taste.renovation_tolerance}
- Max Budget: ${taste.renovation_budget_max:,} if taste.renovation_budget_max else 'Not specified'

### Exemplars
"""
        for ex in taste.exemplars:
            context += f"- {ex.address}: {ex.sentiment} - {ex.reason}\n"

        if not taste.exemplars:
            context += "(no exemplars yet)\n"

        context += f"""
### Version: {taste.version}
### Notes: {taste.notes or '(none)'}
"""

        prompt = f"""Transform this taste model data into a well-written aesthetics.md document.

{context}

Create a document that:
1. Opens with a brief summary of aesthetic philosophy
2. Details what makes a house attractive (principles)
3. Lists clear deal-breakers and red flags
4. Explains the scoring dimensions and their importance
5. Notes the renovation stance
6. Ends with any open questions or tensions in preferences

Make it feel personal and useful, not just a data dump.
"""

        response = self.openrouter.chat(
            prompt=prompt,
            system_prompt=self.instructions,
        )

        return response
