# ARD-007: Browser Scraping via Claude Code MCP

## Status
ACCEPTED

## Context
Zillow listings contain structured data (price, beds, baths) and images that need to be extracted. Options:
- HTTP requests with HTML parsing
- Headless browser automation (Playwright/Selenium)
- Claude Code MCP browser tools

Zillow has anti-bot measures and dynamic JavaScript rendering.

## Decision
Use Claude Code's MCP browser tools for scraping during interactive sessions.

**Approach:**
- No standalone browser automation code in the project
- Scraping happens during Claude Code sessions using:
  - `mcp__claude-in-chrome__navigate` for page navigation
  - `mcp__claude-in-chrome__javascript_tool` for data extraction
  - `mcp__claude-in-chrome__computer` for interactions (clicks, waits)
- Extracted data passed to CLI via `house ingest --data <json>`

**Image Extraction Pattern:**
1. Navigate to gallery: `<url>?mmlb=g,0`
2. Wait for gallery to load
3. Extract URLs via JavaScript:
   ```javascript
   document.querySelectorAll('img[src*="zillowstatic"]')
   ```
4. Click through gallery to lazy-load more images
5. Normalize URLs to `-p_e.jpg` format

**Skill Documentation:**
- `.claude/skills/zillow-images.md` documents the full process
- Ensures reproducibility across sessions

## Consequences

**Positive:**
- Uses real browser (defeats anti-bot measures)
- No Playwright/Selenium dependencies
- Leverages Claude Code's existing browser capabilities
- Human-in-the-loop for edge cases (CAPTCHAs, sold listings)
- Adaptable to site changes (Claude can reason about DOM)

**Negative:**
- Requires Claude Code session (not fully automated)
- Can't run headless/scheduled batch jobs
- Session-dependent (no persistent browser state)
- Slower than direct HTTP (interactive scraping)

## Alternatives Considered

1. **Playwright automation**: Blocked by Zillow anti-bot
2. **HTTP + BeautifulSoup**: Missing JS-rendered content
3. **Zillow API**: No public API available
4. **Third-party scraping service**: Cost, reliability concerns
