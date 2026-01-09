"""Potential scoring agent - renovation and transformation opportunities."""

import json
from datetime import datetime

from src.models import House, TasteModel, PotentialScore, RenovationIdea
from src.storage import JsonStore
from .base import BaseAgent, AESTHETIC_CONTEXT, DEFAULT_MODEL


POTENTIAL_INSTRUCTIONS = f"""{AESTHETIC_CONTEXT}

You are the Potential & Renovation Agent. Your job is to evaluate what a house
COULD BECOME with thoughtful renovation.

Consider:
- What transformations would unlock the house's potential?
- What's the realistic feasibility (light/medium/heavy work)?
- What cost class would renovations fall into?
- What are the risks of renovation?
- What's the upside narrative - what could this become?

Be practical about costs and feasibility.
Consider the user's renovation tolerance and budget from the taste model.
Focus on high-impact changes, not cosmetic tweaks.
"""


class PotentialAgent(BaseAgent):
    """Agent for evaluating renovation potential."""

    name = "potential_agent"
    model = DEFAULT_MODEL
    instructions = POTENTIAL_INSTRUCTIONS

    def score(self, house_id: str) -> PotentialScore | None:
        """Score a house's renovation potential."""
        house = self.store.load_house(house_id)
        if not house:
            return None

        taste = self.store.load_or_create_taste()

        # Need vision analysis first
        if not house.vision_analysis:
            return None

        # Build context
        context = self._build_context(house, taste)

        prompt = f"""Evaluate this house's renovation potential.

{context}

Respond with JSON in this format:
{{
    "score": 75.0,
    "renovation_ideas": [
        {{
            "area": "kitchen",
            "current_state": "dated but functional 1990s kitchen",
            "proposed_change": "full renovation with new cabinets, counters, appliances",
            "impact": "Would transform the heart of the home, add significant value",
            "difficulty": "medium"
        }}
    ],
    "feasibility": "medium",
    "cost_class": "$100-200k",
    "risk_notes": ["Load-bearing wall limits layout changes", "Old electrical may need upgrade"],
    "upside_narrative": "With a thoughtful renovation, this could become a stunning modern home that honors its original character while adding contemporary comfort."
}}

Cost classes: <$50k, $50-100k, $100-200k, $200k+
Feasibility: light (paint/cosmetic), medium (kitchen/bath), heavy (structural/addition)
"""

        response = self.openrouter.chat(
            prompt=prompt,
            system_prompt=self.instructions,
        )

        # Parse response
        score = self._parse_response(response)

        # Save to house
        house.potential_score = score
        self.store.save_house(house)

        return score

    def _build_context(self, house: House, taste: TasteModel) -> str:
        """Build context for potential scoring."""
        vision = house.vision_analysis

        context = f"""## House Information
Address: {house.address}
Price: ${house.price:,} if house.price else 'N/A'
Year Built: {house.features.year_built or 'Unknown'}
Sqft: {house.features.sqft or 'Unknown'}

## Current State (from Vision Analysis)
Overall Aesthetic: {vision.overall_aesthetic}/10
Renovation State: {vision.renovation_state}
Architectural Style: {vision.architectural_style}

### Room-by-Room:
"""
        for room in vision.rooms:
            context += f"""
- {room.room_type}:
  Current quality: {room.aesthetic_quality}/10
  Materials: {', '.join(room.materials)}
  Condition: {room.condition}
  Notes: {room.notes}
"""

        context += f"""
### Red Flags (issues to address):
{chr(10).join('- ' + f for f in vision.red_flags) or '(none)'}

### Positive Signals (good bones):
{chr(10).join('- ' + s for s in vision.positive_signals) or '(none)'}

## User's Renovation Tolerance
Tolerance: {taste.renovation_tolerance}
Max Budget: ${taste.renovation_budget_max:,} if taste.renovation_budget_max else 'Not specified'

## User's Aesthetic Principles (what renovation should achieve):
{chr(10).join('- ' + p for p in taste.principles) or '(none specified)'}
"""

        return context

    def _parse_response(self, response: str) -> PotentialScore:
        """Parse response into PotentialScore."""
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            data = json.loads(response)

            ideas = []
            for idea in data.get("renovation_ideas", []):
                ideas.append(RenovationIdea(
                    area=idea.get("area", ""),
                    current_state=idea.get("current_state", ""),
                    proposed_change=idea.get("proposed_change", ""),
                    impact=idea.get("impact", ""),
                    difficulty=idea.get("difficulty", "medium"),
                ))

            return PotentialScore(
                score=data.get("score", 50.0),
                renovation_ideas=ideas,
                feasibility=data.get("feasibility", "medium"),
                cost_class=data.get("cost_class", "$50-100k"),
                risk_notes=data.get("risk_notes", []),
                upside_narrative=data.get("upside_narrative", ""),
            )

        except (json.JSONDecodeError, KeyError, TypeError):
            return PotentialScore(
                score=50.0,
                feasibility="unknown",
                cost_class="unknown",
                upside_narrative=f"Parse error. Raw: {response[:300]}",
            )
