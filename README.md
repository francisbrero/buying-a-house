# House Evaluator

An agentic CLI tool that analyzes real estate listings using vision and text models to score houses against your aesthetic preferences.

## Features

- **Vision Analysis**: Analyzes listing photos to identify rooms, materials, light quality, and red flags
- **Dual Scoring**: Present-fit score (how it matches now) + Potential score (renovation upside)
- **Taste Model**: Evolving preferences that improve with feedback
- **House Briefs**: Human-readable summaries with verdict and recommendations

## Quick Start

```bash
# Install dependencies
pip install -e .

# Set your OpenRouter API key
export OPENROUTER_API_KEY=your_key_here

# Ingest a listing
python -m src.cli house ingest <zillow_url>

# Score a house
python -m src.cli house score <house_id>

# List all houses with scores
python -m src.cli house list
```

## Cost

The system uses **Gemini 3 Flash Preview** via OpenRouter for optimal price/performance.

| Operation | Cost |
|-----------|------|
| **Per house scored** | ~$0.008 |
| 10 houses | ~$0.08 |
| 100 houses | ~$0.80 |
| 1000 houses | ~$8.00 |

### Pricing Breakdown

Each house scoring runs 4 API calls:

| Agent | Task | Est. Tokens |
|-------|------|-------------|
| Vision | Analyze composite image grid | ~2,300 |
| Present-Fit | Score against taste model | ~2,500 |
| Potential | Evaluate renovation opportunities | ~2,100 |
| Brief | Generate summary | ~2,400 |

**Gemini 3 Flash Preview pricing**: $0.50/1M input, $3.00/1M output

### Model Options

Models can be changed in `src/agents/base.py`:

| Model | Input $/1M | Output $/1M | Cost/House |
|-------|------------|-------------|------------|
| Gemini 3 Flash (default) | $0.50 | $3.00 | ~$0.008 |
| Gemini 2.5 Flash | $0.15 | $0.60 | ~$0.002 |
| GPT-4o | $5.00 | $20.00 | ~$0.05 |
| Claude Sonnet 4 | $3.00 | $15.00 | ~$0.04 |

## Architecture

See [docs/ard/](docs/ard/) for architectural decision records:

- **ARD-001**: OpenRouter API gateway
- **ARD-002**: Composite image grid for vision
- **ARD-003**: JSON file storage
- **ARD-004**: Multi-agent architecture
- **ARD-009**: Gemini 3 Flash as default model

## Project Structure

```
src/
├── cli.py              # Typer CLI commands
├── models/             # Pydantic data models
├── storage/            # JSON persistence
├── services/           # OpenRouter, image composite
└── agents/             # Vision, scoring, brief agents

data/
├── houses/             # One JSON file per house
├── taste.json          # Taste model
└── aesthetics.md       # Human-readable preferences
```

## Live Report

View the live house evaluation report at:

**https://francisbrero.github.io/buying-a-house/**

The report is automatically updated whenever changes are pushed to the master branch.

## Automation Workflow

This project is designed to be run by an automated agent (e.g., Claude Code) to discover and score new listings. Here's the typical workflow:

### 1. Import New Listings from Zillow Search

```bash
# Use Claude Code to scrape a Zillow search page, then import the listings
python -m src.cli house import-search "<zillow_search_url>" --data '[
  {"address": "123 Main St", "price": 1500000, "url": "...", ...},
  ...
]'
```

### 2. Geocode New Houses (for map display)

```bash
python -m src.cli house geocode
```

### 3. Score All Unscored Houses

```bash
python -m src.cli house batch-score
```

### 4. Generate the HTML Report

```bash
python -m src.cli house report --no-open
```

### 5. Commit and Push to Deploy

```bash
git add -A
git commit -m "Update listings $(date +%Y-%m-%d)"
git push origin master
```

The GitHub Actions workflow will automatically deploy the updated `report.html` to GitHub Pages.

### One-liner for Automation

After importing new listings, run this to process and deploy:

```bash
python -m src.cli house geocode && \
python -m src.cli house batch-score && \
python -m src.cli house report --no-open && \
git add -A && git commit -m "Update listings $(date +%Y-%m-%d)" && git push
```

## Requirements

- Python 3.11+
- OpenRouter API key
- Chrome + Claude Code (for Zillow scraping)
