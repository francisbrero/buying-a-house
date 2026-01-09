# ARD-008: Two-Score Evaluation System

## Status
ACCEPTED

## Context
House evaluation needs to capture two distinct perspectives:
1. How well does this house fit my taste **as-is**?
2. What's the **potential** if I make changes?

A single score conflates these, making it hard to find diamonds in the rough.

## Decision
Implement a two-score system: Present-Fit and Potential.

**Present-Fit Score (0-100):**

- Evaluates house against taste model in current state
- Checks hard constraints (violations reduce score significantly)
- Weighted dimension scores (natural light, kitchen, etc.)
- Strict grading: violations = deal-breakers
- Output: score, violations list, dimension breakdown, justification

**Potential Score (0-100):**

- Assumes reasonable renovation budget
- Identifies transformation opportunities
- Considers:
  - Layout bones (can't change easily)
  - Lot/location (fixed)
  - What cosmetic changes would unlock
- Output: score, renovation ideas, feasibility class, cost estimate, upside narrative

**Interpretation Matrix:**
| Present | Potential | Meaning |
|---------|-----------|---------|
| High    | High      | Great as-is, could be even better |
| High    | Low       | Good fit, limited upside |
| Low     | High      | Diamond in the rough |
| Low     | Low       | Skip it |

**Pipeline Order:**
1. Vision analysis (required for both)
2. Present-fit scoring (independent)
3. Potential scoring (independent)
4. Brief generation (needs both scores)

## Consequences

**Positive:**

- Clear separation of "now" vs "possible"
- Surfaces renovation opportunities
- Helps calibrate viewing priority
- Each score has clear criteria

**Negative:**

- Two scores more complex than one
- Potential score requires renovation cost intuition
- May overvalue fixable problems
- Scores can seem contradictory to users

## Alternatives Considered

1. **Single composite score**: Loses the present/potential distinction
2. **Three scores (present, light reno, heavy reno)**: Too granular
3. **Letter grades**: Less precise, harder to rank
4. **Percentile ranking**: Requires large dataset first
