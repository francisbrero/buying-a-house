# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agentic home listing aesthetic evaluator - a CLI-first system that ingests real estate listings (primarily Zillow URLs), analyzes them using vision models via OpenRouter, and ranks houses based on aesthetic preferences stored in a taste model.

## Commands

```bash
# Install
pip install -e .

# CLI commands
house house ingest <url> --data '<json>'  # Ingest listing with scraped data
house house ingest <url> --interactive    # Manual data entry
house house score <house_id>              # Run full scoring pipeline
house house list                          # List all houses
house house show <house_id>               # Display house details and brief

house taste init                          # Interactive taste interview
house taste show                          # Display current taste model
house taste distill                       # Regenerate aesthetics.md
house taste annotate <id> --verdict liked # Add user feedback
```

## Architecture

```
src/
├── cli.py                 # Typer CLI entry point
├── models/                # Pydantic data models
│   ├── house.py          # House, HouseFeatures
│   ├── taste.py          # TasteModel, WeightedDimension
│   └── scores.py         # VisionAnalysis, PresentFitScore, PotentialScore
├── storage/
│   └── json_store.py     # JSON file persistence
├── services/
│   ├── image_composite.py # Creates grid image from listing photos
│   └── openrouter.py     # OpenRouter API client for vision/text
└── agents/
    ├── base.py           # Base agent class, OpenRouter client setup
    ├── vision.py         # Analyzes composite image of listing
    ├── present_fit.py    # Strict scoring against taste model
    ├── potential.py      # Renovation potential evaluation
    ├── brief.py          # Generates house summary markdown
    ├── taste_curator.py  # Evolves preferences from feedback
    ├── distiller.py      # Generates aesthetics.md
    └── orchestrator.py   # Coordinates scoring pipeline
```

## Data Flow

1. **Ingestion**: Zillow scraping via Claude Code MCP browser tools → house JSON saved to `data/houses/`
2. **Scoring Pipeline** (orchestrator.py):
   - Vision Agent: Fetches images → creates composite grid → sends to OpenRouter vision model
   - Present-Fit Agent: Compares vision analysis against taste.json → strict score
   - Potential Agent: Evaluates renovation opportunities → potential score
   - Brief Agent: Synthesizes all analysis → markdown brief
3. **Taste Evolution**: User verdicts (liked/disliked) → Taste Curator proposes updates → aesthetics.md regenerated

## Key Files

- `data/taste.json` - Machine-readable taste preferences
- `data/aesthetics.md` - Human-readable taste document
- `data/houses/<id>.json` - Individual house records with scores

## Environment

Requires `OPENROUTER_API_KEY` environment variable.

## Zillow Scraping Workflow

Since scraping uses Claude Code's MCP browser tools:

1. User provides Zillow URL
2. Claude Code navigates to URL and extracts: address, price, description, image URLs, features
3. Extracted data passed to CLI: `house house ingest <url> --data '<json>'`

## Extracting Zillow Image URLs (Step-by-Step)

When scraping a Zillow listing, follow this exact process to get all listing photos:

### Step 1: Navigate to the Gallery URL
Navigate directly to the gallery view by appending `?mmlb=g,0` to the listing URL:
```
https://www.zillow.com/homedetails/ADDRESS/ZPID_zpid/?mmlb=g,0
```

### Step 2: Wait for Gallery to Load
Wait 2-3 seconds for the gallery to fully load. You should see "1 of N" in the top-right corner.

### Step 3: Extract Image URLs via JavaScript
Run this JavaScript to extract all listing photo URLs:
```javascript
const allImages = document.querySelectorAll('img[src*="zillowstatic"]');
const urls = [...allImages]
  .map(img => img.src)
  .filter(url => url && !url.includes('logo') && !url.includes('icon') && !url.includes('svg') && !url.includes('avatar') && !url.includes('map'))
  .filter(url => url.includes('p_f') || url.includes('p_e') || url.includes('uncropped') || url.includes('p_h'));
[...new Set(urls)]
```

### Step 4: Navigate Through Gallery to Load More Images
The gallery lazy-loads images. To get more:
- Click the right arrow button (coordinates ~[1476, 400]) multiple times
- Or use keyboard: `ArrowRight` key (may not work in all cases)
- Re-run the JavaScript extraction after navigating

### Step 5: Normalize URLs to p_e Format
Convert any URL format to the standard `-p_e.jpg` format for consistency:
- `fp/HASH-uncropped_scaled_within_1344_1008.jpg` → `fp/HASH-p_e.jpg`
- `fp/HASH-cc_ft_960.jpg` → `fp/HASH-p_e.jpg`
- `fp/HASH-p_f.jpg` → `fp/HASH-p_e.jpg`

### Important Notes

1. **Browser Cache Issues**: The browser may show cached images from previous listings. Always navigate to a fresh gallery URL (`?mmlb=g,0`) to ensure you're getting images for the current listing.

2. **Sold Listings**: If a listing shows "Sold" and redirects to "Your Home" page, click the "Public view" button to access the original listing with photos.

3. **Tab Group**: Ensure you have a clean MCP tab group. Use `tabs_context_mcp` to check and `tabs_create_mcp` if needed.

4. **Typical Image Count**: Most Zillow listings have 15-50 photos. Aim to capture at least 15-20 for good vision analysis.

### Example Complete Flow

```
1. mcp__claude-in-chrome__navigate → URL?mmlb=g,0
2. mcp__claude-in-chrome__computer (wait 3 seconds)
3. mcp__claude-in-chrome__screenshot (verify gallery loaded)
4. mcp__claude-in-chrome__javascript_tool (extract URLs)
5. mcp__claude-in-chrome__computer (click right arrow)
6. Repeat steps 4-5 until ~20 unique URLs collected
7. Save URLs to house JSON file
```
