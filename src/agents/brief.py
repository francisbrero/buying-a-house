"""Brief generation agent - synthesizes house analysis into readable brief."""

from src.models import House
from src.storage import JsonStore
from .base import BaseAgent, AESTHETIC_CONTEXT, DEFAULT_MODEL


BRIEF_INSTRUCTIONS = f"""{AESTHETIC_CONTEXT}

You are the House Brief Agent. Your job is to synthesize all analysis
into a clear, readable brief that helps the user make a decision.

The brief should be:
- Scannable (use headers, bullets)
- Honest (don't sugarcoat problems)
- Actionable (clear verdict at the end)
- Concise (target 300-500 words)

Format as markdown with these sections:
- Executive Summary (2-3 sentences)
- Aesthetic Alignment (how it matches taste)
- Strengths
- Weaknesses
- Deal-Breakers (if any)
- Renovation Paths (if applicable)
- Who This House Is For
- Verdict
"""


class BriefAgent(BaseAgent):
    """Agent for generating house briefs."""

    name = "brief_agent"
    model = DEFAULT_MODEL
    instructions = BRIEF_INSTRUCTIONS

    def generate(self, house_id: str) -> str | None:
        """Generate a brief for a house."""
        house = self.store.load_house(house_id)
        if not house:
            return None

        taste = self.store.load_or_create_taste()

        # Build context from all available data
        context = self._build_context(house, taste)

        prompt = f"""Generate a house brief based on this analysis.

{context}

Write a clear, honest brief in markdown format with these sections:
- Executive Summary
- Aesthetic Alignment
- Strengths
- Weaknesses
- Deal-Breakers (if any)
- Renovation Paths
- Who This House Is For
- Verdict

Be direct and helpful. The reader needs to decide whether to pursue this house.
"""

        response = self.openrouter.chat(
            prompt=prompt,
            system_prompt=self.instructions,
        )

        # Save to house
        house.brief = response
        self.store.save_house(house)

        return response

    def _build_context(self, house: House, taste) -> str:
        """Build context for brief generation."""
        context = f"""## House
Address: {house.address}
Price: ${house.price:,} if house.price else 'N/A'
Beds: {house.features.bedrooms} | Baths: {house.features.bathrooms} | Sqft: {house.features.sqft}
URL: {house.url}

## Description
{house.description[:800] if house.description else 'No description'}
"""

        if house.vision_analysis:
            va = house.vision_analysis
            context += f"""
## Vision Analysis
Overall Aesthetic: {va.overall_aesthetic}/10
Style: {va.architectural_style}
Renovation State: {va.renovation_state}

Red Flags: {', '.join(va.red_flags) or 'None'}
Positive Signals: {', '.join(va.positive_signals) or 'None'}
"""

        if house.present_fit_score:
            pf = house.present_fit_score
            context += f"""
## Present-Fit Score: {pf.score:.1f}/100
Passed: {'Yes' if pf.passed else 'No'}
Violations: {', '.join(pf.violations) or 'None'}
Deal-Breakers: {', '.join(pf.deal_breakers) or 'None'}

Justification: {pf.justification}
"""

        if house.potential_score:
            ps = house.potential_score
            context += f"""
## Potential Score: {ps.score:.1f}/100
Feasibility: {ps.feasibility}
Cost Class: {ps.cost_class}

Upside: {ps.upside_narrative}

Risks: {', '.join(ps.risk_notes) or 'None'}
"""

        context += f"""
## User's Key Principles
{chr(10).join('- ' + p for p in taste.principles[:5]) or '(not specified)'}

## User's Anti-Principles
{chr(10).join('- ' + p for p in taste.anti_principles[:5]) or '(not specified)'}
"""

        return context
