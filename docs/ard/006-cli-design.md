# ARD-006: Typer CLI Design

## Status
ACCEPTED

## Context
Users need to interact with the system to:
- Ingest new house listings
- Score houses against their taste
- View and manage houses
- Manage their taste model

Options: Web UI, TUI, CLI, or API-first.

## Decision
Build a CLI using Typer with subcommand groups.

**Command Structure:**
```
house ingest <url>        # Add new listing
house score <house_id>    # Run scoring pipeline
house batch-score         # Score all unscored houses
house list                # List houses with scores
house show <house_id>     # Display house brief

taste init                # Bootstrap taste model via interview
taste review              # Review recent decisions, provide feedback
taste distill             # Generate aesthetics.md from taste.json
taste annotate <id>       # Add feedback to specific house
```

**Implementation:**
- `src/cli.py` as single entry point
- Typer for argument parsing and help generation
- Rich for formatted terminal output
- House IDs use address-slug format for readability

**Output Format:**
- `house list`: Table with scores, truncated address
- `house show`: Full markdown brief rendered in terminal
- Progress indicators for long-running operations

## Consequences

**Positive:**
- No server to run, works offline
- Fast iteration (edit, run, see results)
- Easy to script and automate
- Typer provides excellent help and completion
- Rich makes output readable and attractive

**Negative:**
- No persistent state between commands (reload each time)
- Limited discoverability vs GUI
- Harder to visualize images in terminal
- Multi-step workflows require multiple commands

## Alternatives Considered

1. **Web UI (Streamlit/FastAPI)**: More visual but requires server
2. **TUI (Textual)**: More interactive but complex to build
3. **Jupyter notebook**: Good for exploration but not daily use
4. **API-first**: Overhead without a clear client need
