"""Scoring result models."""

from pydantic import BaseModel, Field


class RoomAnalysis(BaseModel):
    """Analysis of a single room from vision."""

    room_type: str = Field(description="Type of room (kitchen, living, bedroom, bathroom, exterior, etc.)")
    aesthetic_quality: float = Field(ge=1, le=10, description="Overall aesthetic quality 1-10")
    materials: list[str] = Field(default_factory=list, description="Visible materials (hardwood, granite, laminate, etc.)")
    light_quality: str = Field(default="", description="Natural light assessment (abundant, moderate, poor)")
    condition: str = Field(default="", description="Condition (original, updated, renovated, flip-quality)")
    notes: str = Field(default="", description="Additional observations")


class VisionAnalysis(BaseModel):
    """Complete vision analysis of a house."""

    rooms: list[RoomAnalysis] = Field(default_factory=list)
    overall_aesthetic: float = Field(ge=1, le=10, description="Overall aesthetic score 1-10")
    architectural_style: str = Field(default="", description="Architectural style if identifiable")
    red_flags: list[str] = Field(default_factory=list, description="Concerning patterns (flip signs, cheap materials, etc.)")
    positive_signals: list[str] = Field(default_factory=list, description="Positive aesthetic signals")
    renovation_state: str = Field(default="", description="Overall renovation state (original, partial, full, flip)")
    raw_description: str = Field(default="", description="Raw vision model output for reference")


class DimensionScore(BaseModel):
    """Score for a single aesthetic dimension."""

    dimension: str
    score: float = Field(ge=0, le=10)
    weight: float = Field(ge=0, le=1)
    notes: str = ""


class PresentFitScore(BaseModel):
    """Present-fit scoring result - strict, penalty-oriented."""

    score: float = Field(ge=0, le=100, description="Overall present-fit score 0-100")
    passed: bool = Field(description="Whether house passes minimum threshold")
    violations: list[str] = Field(default_factory=list, description="Hard constraint violations")
    dimension_scores: list[DimensionScore] = Field(default_factory=list)
    justification: str = Field(default="", description="Brief explanation of score")
    deal_breakers: list[str] = Field(default_factory=list, description="Absolute deal-breakers found")


class RenovationIdea(BaseModel):
    """A potential renovation opportunity."""

    area: str = Field(description="Area to renovate (kitchen, bathroom, etc.)")
    current_state: str = Field(description="Current condition")
    proposed_change: str = Field(description="What could be done")
    impact: str = Field(description="Expected aesthetic/value impact")
    difficulty: str = Field(description="light, medium, or heavy")


class PotentialScore(BaseModel):
    """Potential scoring result - transformation opportunities."""

    score: float = Field(ge=0, le=100, description="Overall potential score 0-100")
    renovation_ideas: list[RenovationIdea] = Field(default_factory=list)
    feasibility: str = Field(description="Overall feasibility: light, medium, heavy")
    cost_class: str = Field(description="Rough cost: <$50k, $50-100k, $100-200k, $200k+")
    risk_notes: list[str] = Field(default_factory=list, description="Risks with renovation")
    upside_narrative: str = Field(default="", description="What this house could become")
