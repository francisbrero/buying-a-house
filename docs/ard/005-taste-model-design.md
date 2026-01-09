# ARD-005: Taste Model Design

## Status
ACCEPTED

## Context
The system needs to capture and evolve a user's aesthetic preferences for homes. Preferences are subjective, multi-dimensional, and change over time as the user sees more homes.

## Decision
Use a structured taste model stored in `data/taste.json` with the following schema:

**Structure:**
```python
class TasteModel:
    principles: list[str]           # Core aesthetic beliefs
    anti_principles: list[str]      # Things to avoid
    weighted_dimensions: dict       # {dimension: weight} for scoring
    hard_constraints: list[str]     # Must-haves (violations = low score)
    soft_constraints: list[str]     # Nice-to-haves
    exemplars: Exemplars            # Liked/disliked house references
    violation_patterns: list[str]   # Learned red flags
```

**Weighted Dimensions (example):**
- natural_light: 0.20
- architectural_character: 0.15
- outdoor_space: 0.15
- kitchen_quality: 0.15
- layout_flow: 0.10
- bathroom_quality: 0.10
- storage: 0.05
- condition: 0.10

**Evolution Mechanism:**
- User provides feedback after seeing scores/briefs
- Taste Curator Agent analyzes prediction errors
- Proposes specific updates to taste model
- Updates require explicit user approval

## Consequences

**Positive:**
- Explicit, inspectable preferences
- Scoring is deterministic given same taste model
- Users can manually edit taste.json
- Evolution is controlled (approval required)
- Dimension weights sum to 1.0 for normalized scoring

**Negative:**
- Initial taste model requires interview/setup
- Dimensions are fixed (adding new ones requires code change)
- Weights may not capture non-linear preferences
- User may not know their preferences until they see examples

## Alternatives Considered

1. **Embedding-based similarity**: Less interpretable, harder to debug
2. **Binary like/dislike without dimensions**: Loses nuance
3. **Free-form text preferences**: Hard to score consistently
4. **Learned weights via ML**: Requires more training data than practical
