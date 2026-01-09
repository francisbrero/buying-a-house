# ARD-003: JSON File Storage

## Status
ACCEPTED

## Context
The system needs to persist:
- House listings with scores and analysis
- Taste model (preferences, dimensions, exemplars)
- Generated briefs and annotations

Options: SQLite, PostgreSQL, JSON files, or a document database.

## Decision
Use JSON files stored in the `data/` directory.

**Structure:**
```
data/
├── houses/
│   ├── {house-id}.json      # One file per house
│   └── ...
├── taste.json               # Taste model
└── aesthetics.md            # Human-readable taste doc
```

**House ID format:** `{address-slug}-{timestamp}`
Example: `2304-mattison-ln-santa-cruz-ca-95062-20260108230000`

**Implementation:**
- `src/storage/json_store.py` provides CRUD operations
- Pydantic models serialize/deserialize automatically
- Files are human-readable and git-friendly

## Consequences

**Positive:**
- Zero setup, no database to configure
- Human-readable, easy to inspect and debug
- Git-friendly for version control
- Easy backup (just copy files)
- Works offline

**Negative:**
- No query capabilities (must load all files to search)
- No concurrent write safety
- Scales poorly beyond ~1000 houses
- No relational queries (e.g., "houses liked in Capitola")

## Alternatives Considered

1. **SQLite**: Better querying, but adds complexity for a CLI tool
2. **PostgreSQL**: Overkill for single-user CLI
3. **TinyDB**: JSON-based but adds dependency for minimal benefit
4. **MongoDB**: Document model fits, but requires running a server
