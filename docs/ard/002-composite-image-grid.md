# ARD-002: Composite Image Grid for Vision Analysis

## Status
ACCEPTED

## Context
Zillow listings typically have 15-50 photos. Sending each image separately to the vision model would be:
- Expensive (per-image API costs)
- Slow (sequential API calls)
- Context-limited (model can't compare rooms)

## Decision
Create a single composite grid image from all listing photos before sending to the vision model.

**Implementation:**
- `src/services/image_composite.py` handles grid creation
- Fetches images concurrently via `httpx` async
- Calculates optimal grid layout: `sqrt(n)` columns, max 5 columns
- Resizes images to uniform 400x300 pixels
- Arranges in grid using Pillow
- Returns PNG bytes for vision API

**Grid sizing:**
- 4 images → 2x2 grid
- 9 images → 3x3 grid
- 16 images → 4x4 grid
- 20+ images → 5xN grid (capped at 5 columns)

## Consequences

**Positive:**
- Single API call analyzes entire listing
- Model can compare rooms and identify patterns (e.g., "grey paint everywhere")
- ~10x cost reduction vs individual image calls
- Faster overall processing

**Negative:**
- Individual image resolution reduced
- Very large listings (50+ photos) may lose detail
- Grid layout is fixed, not optimized per-listing

## Alternatives Considered

1. **Sequential individual images**: Too slow and expensive
2. **Sample subset of images**: Might miss important rooms or red flags
3. **Video-style frame sequence**: More complex, overkill for static listings
4. **Multiple API calls with batched images**: More complex orchestration, marginal benefit
