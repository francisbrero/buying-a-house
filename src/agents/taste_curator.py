"""Taste curator agent - evolves preferences from feedback."""

from rich.console import Console
from rich.prompt import Prompt

from src.models import TasteModel, WeightedDimension, Exemplar
from src.storage import JsonStore
from .base import BaseAgent, DEFAULT_MODEL


CURATOR_INSTRUCTIONS = """You are the Taste Curator Agent. Your job is to help build and evolve
the user's aesthetic preferences for real estate.

When interviewing:
- Ask one question at a time
- Build on previous answers
- Extract both explicit preferences and implicit patterns
- Be conversational but efficient

When reviewing decisions:
- Compare predicted scores to actual user verdicts
- Identify patterns in disagreements
- Propose specific, testable updates to the taste model
"""


class TasteCuratorAgent(BaseAgent):
    """Agent for curating and evolving the taste model."""

    name = "taste_curator"
    model = DEFAULT_MODEL
    instructions = CURATOR_INSTRUCTIONS

    def review_recent_decisions(self) -> list[str]:
        """Review recent user decisions and propose taste updates."""
        houses = self.store.list_houses()

        # Find houses with both scores and user verdicts
        annotated = [h for h in houses if h.user_verdict and h.present_fit_score]

        if len(annotated) < 2:
            return []

        # Analyze patterns
        context = "## Recent Decisions\n"
        for h in annotated[:10]:
            context += f"""
House: {h.address}
Score: {h.present_fit_score.score:.0f}
User Verdict: {h.user_verdict}
Key violations: {', '.join(h.present_fit_score.violations[:3]) or 'None'}
"""

        taste = self.store.load_or_create_taste()
        context += f"""
## Current Taste Model
Principles: {taste.principles}
Anti-Principles: {taste.anti_principles}
"""

        prompt = f"""Based on these recent decisions, identify any patterns where the scoring
doesn't match user preferences. Propose specific updates.

{context}

For each proposal, format as:
PROPOSAL: [what to change]
REASON: [why, based on evidence]
"""

        response = self.openrouter.chat(
            prompt=prompt,
            system_prompt=self.instructions,
        )

        # Parse proposals (simple extraction)
        proposals = []
        for line in response.split("\n"):
            if line.startswith("PROPOSAL:"):
                proposals.append(line[9:].strip())

        return proposals if proposals else [response]

    def apply_proposal(self, proposal: str):
        """Apply a taste update proposal."""
        taste = self.store.load_or_create_taste()

        # Use agent to interpret and apply
        prompt = f"""Given this taste model update proposal, generate the specific change.

Proposal: {proposal}

Current model:
- Principles: {taste.principles}
- Anti-principles: {taste.anti_principles}
- Hard constraints: {taste.hard_constraints}
- Violation patterns: {taste.violation_patterns}

Respond with JSON indicating the change:
{{
    "action": "add_principle" | "remove_principle" | "add_anti_principle" | "add_violation_pattern" | "adjust_weight",
    "target": "the specific text or dimension name",
    "value": "new value if applicable"
}}
"""

        response = self.openrouter.chat(prompt=prompt, system_prompt=self.instructions)

        # Simple application based on keywords
        if "add_principle" in response.lower() or "principle" in proposal.lower():
            taste.principles.append(proposal)
        elif "anti" in proposal.lower():
            taste.anti_principles.append(proposal)
        elif "violation" in proposal.lower():
            taste.violation_patterns.append(proposal)

        taste.version += 1
        self.store.save_taste(taste)


def run_taste_interview(store: JsonStore) -> TasteModel:
    """Run interactive taste interview to bootstrap preferences."""
    console = Console()
    taste = TasteModel.create_empty()

    questions = [
        ("What architectural styles do you love?", "principles"),
        ("What architectural styles do you hate?", "anti_principles"),
        ("Describe your ideal kitchen.", "principles"),
        ("What makes a house feel 'cheap' to you?", "anti_principles"),
        ("What's your take on open floor plans?", "principles"),
        ("What are absolute deal-breakers for you?", "hard_constraints"),
        ("How do you feel about recent flips/renovations?", "anti_principles"),
        ("What's your renovation tolerance? (none/light/medium/heavy)", "renovation"),
        ("Any specific must-haves?", "hard_constraints"),
    ]

    for question, category in questions:
        console.print(f"\n[cyan]{question}[/cyan]")
        answer = Prompt.ask(">")

        if not answer.strip():
            continue

        if category == "principles":
            taste.principles.append(answer)
        elif category == "anti_principles":
            taste.anti_principles.append(answer)
        elif category == "hard_constraints":
            taste.hard_constraints.append(answer)
        elif category == "renovation":
            if answer.lower() in ("none", "light", "medium", "heavy"):
                taste.renovation_tolerance = answer.lower()

    # Ask for budget
    console.print("\n[cyan]What's your maximum renovation budget? (e.g., 100000)[/cyan]")
    budget = Prompt.ask(">", default="")
    if budget.isdigit():
        taste.renovation_budget_max = int(budget)

    store.save_taste(taste)
    return taste
