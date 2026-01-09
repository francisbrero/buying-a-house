"""Taste model for aesthetic preferences."""

from pydantic import BaseModel, Field


class WeightedDimension(BaseModel):
    """A weighted aesthetic dimension."""

    name: str
    weight: float = Field(ge=0, le=1, description="Importance weight 0-1")
    description: str = Field(default="", description="What this dimension means")
    positive_signals: list[str] = Field(default_factory=list)
    negative_signals: list[str] = Field(default_factory=list)


class Exemplar(BaseModel):
    """A house exemplar for taste matching."""

    house_id: str
    address: str = ""
    sentiment: str = Field(description="liked or disliked")
    reason: str = Field(default="", description="Why this is an exemplar")


class TasteModel(BaseModel):
    """Complete taste model for aesthetic preferences."""

    # Core principles
    principles: list[str] = Field(
        default_factory=list,
        description="Positive aesthetic principles (what to look for)",
    )
    anti_principles: list[str] = Field(
        default_factory=list,
        description="Negative aesthetic principles (what to avoid)",
    )

    # Constraints
    hard_constraints: list[str] = Field(
        default_factory=list,
        description="Absolute requirements that must be met",
    )
    soft_constraints: list[str] = Field(
        default_factory=list,
        description="Preferences that can be traded off",
    )

    # Weighted dimensions for scoring
    dimensions: list[WeightedDimension] = Field(default_factory=list)

    # Exemplars for reference
    exemplars: list[Exemplar] = Field(default_factory=list)

    # Violation patterns
    violation_patterns: list[str] = Field(
        default_factory=list,
        description="Patterns that trigger automatic rejection",
    )

    # Location preferences
    location_preferences: dict[str, str] = Field(
        default_factory=dict,
        description="Location-related preferences (neighborhood type, etc.)",
    )

    # Renovation tolerance
    renovation_budget_max: int | None = Field(
        default=None, description="Maximum renovation budget in dollars"
    )
    renovation_tolerance: str = Field(
        default="medium", description="Willingness to renovate: none, light, medium, heavy"
    )

    # Metadata
    version: int = Field(default=1, description="Taste model version for tracking changes")
    notes: str = Field(default="", description="Free-form notes about preferences")

    @classmethod
    def create_empty(cls) -> "TasteModel":
        """Create an empty taste model for bootstrapping."""
        return cls(
            dimensions=[
                WeightedDimension(
                    name="natural_light",
                    weight=0.15,
                    description="Quality and abundance of natural light",
                ),
                WeightedDimension(
                    name="materials_quality",
                    weight=0.15,
                    description="Quality of visible materials and finishes",
                ),
                WeightedDimension(
                    name="layout_flow",
                    weight=0.12,
                    description="How well spaces flow and connect",
                ),
                WeightedDimension(
                    name="architectural_character",
                    weight=0.12,
                    description="Architectural interest and character",
                ),
                WeightedDimension(
                    name="kitchen_quality",
                    weight=0.12,
                    description="Kitchen design and functionality",
                ),
                WeightedDimension(
                    name="outdoor_space",
                    weight=0.10,
                    description="Quality of outdoor spaces and views",
                ),
                WeightedDimension(
                    name="proportions",
                    weight=0.08,
                    description="Room proportions and ceiling heights",
                ),
                WeightedDimension(
                    name="condition",
                    weight=0.08,
                    description="Overall maintenance and condition",
                ),
                WeightedDimension(
                    name="storage",
                    weight=0.04,
                    description="Storage space availability",
                ),
                WeightedDimension(
                    name="privacy",
                    weight=0.04,
                    description="Privacy from neighbors and street",
                ),
            ]
        )
