# Score Zillow Listing Skill

Score a Zillow listing URL end-to-end: scrape images, create house JSON, run scoring pipeline.

## When to Use

When user shares a Zillow URL and wants it scored against their taste model.

## Prerequisites

- Browser tab available (use `mcp__claude-in-chrome__tabs_context_mcp` first)
- Virtual environment activated with dependencies installed

## Process

### Step 1: Extract Listing Data

Navigate to the Zillow URL and extract basic listing info:

```
mcp__claude-in-chrome__navigate
url: <zillow_url>
tabId: <tab_id>
```

Wait for page load, then extract via JavaScript:

```javascript
({
  address: document.querySelector('[data-testid="bdp-summary-address"]')?.textContent || document.querySelector('h1')?.textContent,
  price: document.querySelector('[data-testid="price"]')?.textContent || document.querySelector('[class*="price"]')?.textContent,
  beds: document.querySelector('[data-testid="bed-bath-beyond"]')?.textContent,
  description: document.querySelector('[data-testid="description"]')?.textContent || document.querySelector('[class*="description"]')?.textContent?.slice(0, 1000)
})
```

### Step 2: Extract Images

Use the `zillow-images` skill to get 15-20 image URLs from the gallery.

Key steps:
1. Navigate to gallery: `<url>?mmlb=g,0`
2. Wait 3 seconds for load
3. Extract via JS: `document.querySelectorAll('img[src*="zillowstatic"]')`
4. Click through gallery to lazy-load more
5. Normalize URLs to `-p_e.jpg` format

### Step 3: Create House JSON

Generate house ID: `{address-slug}-{timestamp}`

Example: `507-la-honda-dr-aptos-ca-95003-20260109120000`

Create file at `data/houses/{house_id}.json`:

```json
{
  "id": "507-la-honda-dr-aptos-ca-95003-20260109120000",
  "url": "https://www.zillow.com/homedetails/...",
  "address": "507 La Honda Dr, Aptos, CA 95003",
  "price": 1250000,
  "description": "...",
  "features": {
    "bedrooms": 3,
    "bathrooms": 2,
    "sqft": 1800,
    "lot_size": null,
    "year_built": null,
    "parking": null
  },
  "image_urls": [
    "https://photos.zillowstatic.com/fp/HASH1-p_e.jpg",
    "https://photos.zillowstatic.com/fp/HASH2-p_e.jpg"
  ],
  "ingested_at": "2026-01-09T12:00:00",
  "scored_at": null,
  "vision_analysis": null,
  "present_fit_score": null,
  "potential_score": null,
  "brief": "",
  "user_rating": null,
  "user_notes": ""
}
```

### Step 4: Run Scoring Pipeline

```bash
cd /Users/francis/Documents/MadKudu/buying-a-house
source .venv/bin/activate
python -m src.cli house score <house_id>
```

This runs:
1. Vision analysis (composite image grid)
2. Present-fit scoring
3. Potential scoring
4. Brief generation

### Step 5: Report Results

Show the user:
- Present-fit score (0-100)
- Potential score (0-100)
- Key strengths/weaknesses
- Verdict from brief

## Batch Processing

For multiple URLs, process each listing through steps 1-3, then batch score:

```bash
python -m src.cli house batch-score
```

## Troubleshooting

### Sold Listings
If redirected to "Your Home" page, click "Public view" button first.

### No Images Found
Navigate directly to gallery URL with `?mmlb=g,0` parameter.

### Scoring Errors
Check that house JSON has valid `image_urls` array and `brief` is `""` not `null`.

## Output

After scoring, the house JSON will contain:
- `vision_analysis`: Room-by-room aesthetic evaluation
- `present_fit_score`: Score with violations and justification
- `potential_score`: Renovation opportunities and cost class
- `brief`: Markdown summary with verdict
