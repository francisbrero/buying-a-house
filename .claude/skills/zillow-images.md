# Zillow Image Scraping Skill

Extract all listing photo URLs from a Zillow property listing.

## Usage

When user provides a Zillow URL and wants to extract images, follow this process:

## Step 1: Navigate to Gallery View

Append `?mmlb=g,0` to open the photo gallery directly:

```
mcp__claude-in-chrome__navigate
url: https://www.zillow.com/homedetails/ADDRESS/ZPID_zpid/?mmlb=g,0
```

## Step 2: Wait and Verify

```
mcp__claude-in-chrome__computer
action: wait
duration: 3

mcp__claude-in-chrome__computer
action: screenshot
```

Verify you see "1 of N" in top-right corner indicating gallery loaded.

## Step 3: Extract Image URLs

Run this JavaScript to get all unique image URLs:

```
mcp__claude-in-chrome__javascript_tool
action: javascript_exec
text: Array.from(document.querySelectorAll('img')).map(i => i.src).filter(u => u.includes('fp/') && !u.includes('logo') && !u.includes('zillow_web')).map(u => u.replace(/-[^-]+$/, '-p_e.jpg')).filter((v,i,a) => a.indexOf(v) === i)
```

## Step 4: Load More Images

Gallery lazy-loads. Click through to load ALL images:

```
mcp__claude-in-chrome__computer
action: key
text: ArrowRight ArrowRight ArrowRight ArrowRight ArrowRight ArrowRight ArrowRight ArrowRight ArrowRight ArrowRight
repeat: 5
```

Repeat steps 3-4 until you have captured ALL unique URLs (check "X of N" counter in gallery).

**Important:** Get ALL images, not just 20. The vision model benefits from seeing every room.

## Step 5: Normalize URLs

Convert all URLs to standard `-p_e.jpg` format:
- `HASH-uncropped_scaled_within_1344_1008.jpg` → `HASH-p_e.jpg`
- `HASH-cc_ft_960.jpg` → `HASH-p_e.jpg`
- `HASH-p_f.jpg` → `HASH-p_e.jpg`

## Troubleshooting

### Sold Listings
If redirected to "Your Home" page, click "Public view" button first, then navigate to gallery.

### Browser Cache
If seeing images from previous listings, navigate to a fresh gallery URL with `?mmlb=g,0`.

### Tab Issues
Check tab context first:
```
mcp__claude-in-chrome__tabs_context_mcp
```
Create new tab if needed:
```
mcp__claude-in-chrome__tabs_create_mcp
```

## Output

Return array of ALL image URLs in this format:
```json
[
  "https://photos.zillowstatic.com/fp/HASH1-p_e.jpg",
  "https://photos.zillowstatic.com/fp/HASH2-p_e.jpg",
  ...
]
```

**Capture ALL available images** - the vision model creates a grid and benefits from seeing every room and angle. A listing with 40 photos should have 40 URLs.
