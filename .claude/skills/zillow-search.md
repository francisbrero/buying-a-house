# Zillow Search Import Skill

Import multiple house listings from a Zillow search results page.

## When to Use

When user shares a Zillow search URL and wants to import all listings from that search for batch scoring.

Example URLs:
- `https://www.zillow.com/santa-cruz-ca/`
- `https://www.zillow.com/homes/for_sale/?searchQueryState=...`

## Prerequisites

- Browser tab available (use `mcp__claude-in-chrome__tabs_context_mcp` first)
- Virtual environment activated with dependencies installed

## Process Overview

1. Navigate to search results page
2. Extract listing URLs and basic data from cards
3. For each listing: scrape full data + images
4. Save all listings via CLI command

## Step 1: Navigate to Search Results

```
mcp__claude-in-chrome__navigate
url: <zillow_search_url>
tabId: <tab_id>
```

Wait for page load:
```
mcp__claude-in-chrome__computer
action: wait
duration: 3
tabId: <tab_id>
```

Take screenshot to verify listings loaded:
```
mcp__claude-in-chrome__computer
action: screenshot
tabId: <tab_id>
```

## Step 2: Extract Listing Cards

Run JavaScript to get all listing URLs and basic data:

```javascript
// Extract from search results page
Array.from(document.querySelectorAll('article[data-test="property-card"], [class*="property-card"], [class*="list-card"]'))
  .map(card => {
    const link = card.querySelector('a[href*="/homedetails/"]');
    const address = card.querySelector('address, [data-test="property-card-addr"]');
    const price = card.querySelector('[data-test="property-card-price"], [class*="price"]');
    return {
      url: link?.href,
      address: address?.textContent?.trim(),
      price: price?.textContent?.replace(/[^0-9]/g, '')
    };
  })
  .filter(l => l.url && l.url.includes('/homedetails/'))
```

Store the results. If fewer than expected, scroll down to load more:

```
mcp__claude-in-chrome__computer
action: scroll
scroll_direction: down
scroll_amount: 5
tabId: <tab_id>
```

Repeat extraction until you have all visible listings (or reach limit).

## Step 3: Scrape Each Listing

For each listing URL, collect full data:

### 3a. Navigate to Listing Detail

```
mcp__claude-in-chrome__navigate
url: <listing_url>
tabId: <tab_id>
```

Wait 2 seconds for load.

### 3b. Extract Listing Data

```javascript
({
  address: document.querySelector('[data-testid="bdp-summary-address"], h1')?.textContent?.trim(),
  price: parseInt(document.querySelector('[data-testid="price"], [class*="price"]')?.textContent?.replace(/[^0-9]/g, '') || '0'),
  description: document.querySelector('[data-testid="description"], [class*="description"]')?.textContent?.slice(0, 2000) || '',
  city: document.querySelector('[data-testid="bdp-summary-address"]')?.textContent?.split(',')[1]?.trim() || '',
  state: document.querySelector('[data-testid="bdp-summary-address"]')?.textContent?.match(/,\s*([A-Z]{2})\s/)?.[1] || 'CA',
  zip_code: document.querySelector('[data-testid="bdp-summary-address"]')?.textContent?.match(/(\d{5})$/)?.[1] || '',
  features: {
    bedrooms: parseInt(document.querySelector('[data-testid="bed-bath-item"]:first-child')?.textContent?.match(/\d+/)?.[0] || '0'),
    bathrooms: parseFloat(document.querySelector('[data-testid="bed-bath-item"]:nth-child(2)')?.textContent?.match(/[\d.]+/)?.[0] || '0'),
    sqft: parseInt(document.querySelector('[data-testid="bed-bath-item"]:nth-child(3)')?.textContent?.replace(/[^0-9]/g, '') || '0')
  }
})
```

### 3c. Extract Images

Navigate to gallery:
```
mcp__claude-in-chrome__navigate
url: <listing_url>?mmlb=g,0
tabId: <tab_id>
```

Wait 3 seconds, then extract all images using the pattern from `zillow-images` skill:

```javascript
// Get all unique image URLs from page
const html = document.body.innerHTML;
const regex = new RegExp('photos\\.zillowstatic\\.com\\/fp\\/[a-f0-9]+', 'g');
const matches = html.match(regex) || [];
[...new Set(matches)].map(u => 'https://' + u + '-p_e.jpg')
```

Click through gallery to load more images if needed (use ArrowRight key).

### 3d. Combine Data

Add the listing to your results array:

```javascript
{
  url: "<listing_url>",
  address: "123 Main St, Santa Cruz, CA 95060",
  price: 1500000,
  description: "Beautiful home...",
  city: "Santa Cruz",
  state: "CA",
  zip_code: "95060",
  features: {
    bedrooms: 3,
    bathrooms: 2,
    sqft: 1800
  },
  image_urls: ["https://photos.zillowstatic.com/fp/abc123-p_e.jpg", ...]
}
```

## Step 4: Save via CLI

Once all listings are scraped, save them using the CLI:

```bash
cd /Users/francis/Documents/MadKudu/buying-a-house
source .venv/bin/activate
python -m src.cli house import-search "<search_url>" --data '<json_array>'
```

The JSON array should contain all scraped listings.

## Handling Pagination

If search has multiple pages:
1. Look for "Next" button or page numbers
2. Click to load next page
3. Extract listings from new page
4. Repeat until all pages processed or limit reached

## Handling Sold Listings

If a listing redirects to "Your Home" page:
1. Look for "Public view" button
2. Click it to access public listing
3. Continue with normal extraction

## Rate Limiting

Add small delays between listing scrapes to avoid detection:
- Wait 1-2 seconds between navigations
- Don't scrape more than 20-30 listings per session

## Output Format

Return JSON array of listings:

```json
[
  {
    "url": "https://www.zillow.com/homedetails/123-Main-St/12345_zpid/",
    "address": "123 Main St, Santa Cruz, CA 95060",
    "price": 1500000,
    "description": "Beautiful 3 bed home...",
    "city": "Santa Cruz",
    "state": "CA",
    "zip_code": "95060",
    "features": {
      "bedrooms": 3,
      "bathrooms": 2.0,
      "sqft": 1800
    },
    "image_urls": [
      "https://photos.zillowstatic.com/fp/abc123-p_e.jpg",
      "https://photos.zillowstatic.com/fp/def456-p_e.jpg"
    ]
  },
  ...
]
```

## After Import

Run batch scoring on new listings:

```bash
python -m src.cli house batch-score --all
```

Then generate updated report:

```bash
python -m src.cli house report
```
