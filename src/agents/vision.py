"""Vision analysis agent for house images."""

import json
from datetime import datetime

from src.models import House, VisionAnalysis, RoomAnalysis
from src.storage import JsonStore
from src.services.image_composite import create_composite_sync
from .base import BaseAgent, AESTHETIC_CONTEXT, VISION_MODEL


VISION_SYSTEM_PROMPT = f"""{AESTHETIC_CONTEXT}

You are analyzing a composite grid image of a real estate listing.
Each cell in the grid shows a different photo from the listing.
Analyze ALL visible rooms and spaces in the grid.

Your task:
1. Identify each distinct room/space visible (kitchen, living room, bedroom, bathroom, exterior, etc.)
2. Assess aesthetic quality of each (materials, light, proportions, condition)
3. Detect any red flags (flip patterns, cheap materials, bad proportions, visual clutter)
4. Note positive signals (quality materials, good light, architectural character)
5. Determine overall renovation state

Be specific and observant. Note actual materials visible (hardwood vs laminate, granite vs formica).
Look for signs of recent flips (grey paint everywhere, cheap LVP, builder-grade everything).
"""

VISION_ANALYSIS_PROMPT = """Analyze this composite image of a real estate listing.

Respond with a JSON object in this exact format:
{{
    "rooms": [
        {{
            "room_type": "kitchen",
            "aesthetic_quality": 7,
            "materials": ["granite counters", "hardwood floors", "stainless appliances"],
            "light_quality": "abundant",
            "condition": "updated",
            "notes": "Modern renovation with quality materials"
        }}
    ],
    "overall_aesthetic": 7,
    "architectural_style": "craftsman",
    "red_flags": ["grey paint throughout suggests recent flip"],
    "positive_signals": ["original hardwood floors", "large windows"],
    "renovation_state": "partial"
}}

Analyze every distinct room visible in the grid. Be thorough and specific.
"""


class VisionAgent(BaseAgent):
    """Agent for analyzing house listing images."""

    name = "vision_analyst"
    model = VISION_MODEL
    instructions = VISION_SYSTEM_PROMPT

    def analyze(self, house_id: str) -> VisionAnalysis | None:
        """Analyze a house's images and return vision analysis."""
        house = self.store.load_house(house_id)
        if not house:
            return None

        if not house.image_urls:
            # No images to analyze - still save placeholder analysis
            analysis = VisionAnalysis(
                overall_aesthetic=5,
                raw_description="No images available for analysis",
            )
            house.vision_analysis = analysis
            self.store.save_house(house)
            return analysis

        # Create composite image (limit to 36 images for reasonable grid size)
        # This creates a 6x6 grid at most, balancing coverage with image size
        composite_bytes = create_composite_sync(house.image_urls, max_images=36)

        # Send to vision model
        response = self.openrouter.vision(
            prompt=VISION_ANALYSIS_PROMPT,
            image_bytes=composite_bytes,
            system_prompt=VISION_SYSTEM_PROMPT,
        )

        # Parse response
        analysis = self._parse_response(response)
        analysis.raw_description = response

        # Save to house
        house.vision_analysis = analysis
        self.store.save_house(house)

        return analysis

    def _parse_response(self, response: str) -> VisionAnalysis:
        """Parse vision model response into VisionAnalysis."""
        # Try to extract JSON from response
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

            rooms = []
            for room_data in data.get("rooms", []):
                rooms.append(RoomAnalysis(
                    room_type=room_data.get("room_type", "unknown"),
                    aesthetic_quality=room_data.get("aesthetic_quality", 5),
                    materials=room_data.get("materials", []),
                    light_quality=room_data.get("light_quality", ""),
                    condition=room_data.get("condition", ""),
                    notes=room_data.get("notes", ""),
                ))

            return VisionAnalysis(
                rooms=rooms,
                overall_aesthetic=data.get("overall_aesthetic", 5),
                architectural_style=data.get("architectural_style", ""),
                red_flags=data.get("red_flags", []),
                positive_signals=data.get("positive_signals", []),
                renovation_state=data.get("renovation_state", ""),
            )

        except (json.JSONDecodeError, KeyError, TypeError):
            # Fallback if parsing fails
            return VisionAnalysis(
                overall_aesthetic=5,
                raw_description=f"Parse error. Raw response: {response[:500]}",
            )
