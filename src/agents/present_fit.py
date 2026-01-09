"""Present-fit scoring agent - strict, penalty-oriented evaluation."""

import json
from datetime import datetime

from agents import Agent, function_tool

from src.models import House, TasteModel, PresentFitScore, DimensionScore
from src.storage import JsonStore
from .base import BaseAgent, AESTHETIC_CONTEXT, SCORING_CONTEXT, DEFAULT_MODEL


PRESENT_FIT_INSTRUCTIONS = f"""{AESTHETIC_CONTEXT}

{SCORING_CONTEXT}

You are the Present-Fit Judge. Your job is to evaluate how well a house matches
the user's aesthetic preferences RIGHT NOW, without renovation.

Your evaluation should be:
- Strict and penalty-oriented
- Conservative (when in doubt, score lower)
- Focused on rejection accuracy (false positives are costly)

Hard constraints are absolute - any violation means the house fails.
Soft constraints are trade-offs - they lower the score but don't fail the house.
Violation patterns trigger automatic penalties.

When scoring dimensions, weight them according to the taste model weights.
The final score is a weighted average, minus penalties for violations.
"""


class PresentFitAgent(BaseAgent):
    """Agent for present-fit scoring against taste model."""

    name = "present_fit_judge"
    model = DEFAULT_MODEL
    instructions = PRESENT_FIT_INSTRUCTIONS

    def score(self, house_id: str) -> PresentFitScore | None:
        """Score a house for present-fit against taste model."""
        house = self.store.load_house(house_id)
        if not house:
            return None

        taste = self.store.load_or_create_taste()

        # Need vision analysis first
        if not house.vision_analysis:
            return None

        # Build scoring context
        context = self._build_context(house, taste)

        # Create agent with tools
        agent = Agent(
            name=self.name,
            instructions=self.instructions,
            model=self.model,
        )

        # Run scoring
        prompt = f"""Score this house for present-fit.

{context}

Analyze the house against the taste model and provide a score.
Respond with JSON in this format:
{{
    "score": 72.5,
    "passed": true,
    "violations": ["grey paint everywhere - flip signal"],
    "dimension_scores": [
        {{"dimension": "natural_light", "score": 8.0, "weight": 0.15, "notes": "Large windows throughout"}},
        {{"dimension": "materials_quality", "score": 6.0, "weight": 0.15, "notes": "Mix of original and updated"}}
    ],
    "justification": "Solid house with good bones. The recent flip cosmetics are concerning but underlying quality is there.",
    "deal_breakers": []
}}
"""

        response = self.openrouter.chat(
            prompt=prompt,
            system_prompt=self.instructions,
        )

        # Parse response
        score = self._parse_response(response, taste)

        # Save to house
        house.present_fit_score = score
        house.scored_at = datetime.now()
        self.store.save_house(house)

        return score

    def _build_context(self, house: House, taste: TasteModel) -> str:
        """Build context string for scoring."""
        vision = house.vision_analysis

        context = f"""## House Information
Address: {house.address}
Price: ${house.price:,} if house.price else 'N/A'
Beds: {house.features.bedrooms} | Baths: {house.features.bathrooms} | Sqft: {house.features.sqft}

## Listing Description
{house.description[:1000] if house.description else 'No description'}

## Vision Analysis
Overall Aesthetic: {vision.overall_aesthetic}/10
Architectural Style: {vision.architectural_style}
Renovation State: {vision.renovation_state}

### Rooms Analyzed:
"""
        for room in vision.rooms:
            context += f"""
- {room.room_type}: {room.aesthetic_quality}/10
  Materials: {', '.join(room.materials)}
  Light: {room.light_quality}
  Condition: {room.condition}
  Notes: {room.notes}
"""

        context += f"""
### Red Flags:
{chr(10).join('- ' + f for f in vision.red_flags) or '(none)'}

### Positive Signals:
{chr(10).join('- ' + s for s in vision.positive_signals) or '(none)'}

## Taste Model

### Principles (what to look for):
{chr(10).join('- ' + p for p in taste.principles) or '(none specified)'}

### Anti-Principles (what to avoid):
{chr(10).join('- ' + p for p in taste.anti_principles) or '(none specified)'}

### Hard Constraints (must have):
{chr(10).join('- ' + c for c in taste.hard_constraints) or '(none specified)'}

### Soft Constraints (prefer):
{chr(10).join('- ' + c for c in taste.soft_constraints) or '(none specified)'}

### Violation Patterns (auto-reject signals):
{chr(10).join('- ' + v for v in taste.violation_patterns) or '(none specified)'}

### Scoring Dimensions:
"""
        for dim in taste.dimensions:
            context += f"- {dim.name} (weight: {dim.weight}): {dim.description}\n"

        return context

    def _parse_response(self, response: str, taste: TasteModel) -> PresentFitScore:
        """Parse scoring response into PresentFitScore."""
        try:
            # Handle markdown code blocks
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            data = json.loads(response)

            dimension_scores = []
            for ds in data.get("dimension_scores", []):
                # Clamp score to 0-10 range (some models may return 0-100)
                raw_score = ds.get("score", 5.0)
                clamped_score = min(10.0, max(0.0, raw_score if raw_score <= 10 else raw_score / 10))
                dimension_scores.append(DimensionScore(
                    dimension=ds.get("dimension", ""),
                    score=clamped_score,
                    weight=min(1.0, max(0.0, ds.get("weight", 0.1))),
                    notes=ds.get("notes", ""),
                ))

            return PresentFitScore(
                score=data.get("score", 50.0),
                passed=data.get("passed", True),
                violations=data.get("violations", []),
                dimension_scores=dimension_scores,
                justification=data.get("justification", ""),
                deal_breakers=data.get("deal_breakers", []),
            )

        except (json.JSONDecodeError, KeyError, TypeError):
            # Fallback score
            return PresentFitScore(
                score=50.0,
                passed=True,
                violations=[],
                justification=f"Scoring parse error. Raw: {response[:300]}",
            )
