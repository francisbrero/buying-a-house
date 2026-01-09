# Architecture Decision Records (ARD) Skill

Document architectural decisions for the house evaluator project.

## When to Use

Use this skill when:
- Making a significant technical decision
- Choosing between multiple implementation approaches
- Documenting why something was built a certain way
- Updating an existing decision

## ARD Location

All ARDs are stored in `docs/ard/` with the naming convention:
```
docs/ard/{NNN}-{slug}.md
```

Example: `docs/ard/004-multi-agent-architecture.md`

## Creating a New ARD

### Step 1: Find Next Number

```bash
ls docs/ard/*.md | tail -1
```

Increment the highest number (e.g., if 008 exists, use 009).

### Step 2: Create ARD File

Use this template structure:

```markdown
# ARD-{NNN}: {Title}

## Status
{PROPOSED | ACCEPTED | DEPRECATED | SUPERSEDED}

## Context
What is the issue that we're seeing that is motivating this decision or change?

## Decision
What is the change that we're proposing and/or doing?

## Consequences

**Positive:**
- Benefit 1
- Benefit 2

**Negative:**
- Drawback 1
- Drawback 2

## Alternatives Considered

1. **Alternative 1**: Why not chosen
2. **Alternative 2**: Why not chosen
```

### Step 3: Write Content

- **Context**: Explain the problem being solved
- **Decision**: Be specific about what was decided and how it's implemented
- **Consequences**: List both positive and negative outcomes honestly
- **Alternatives**: Show what else was considered

## Updating an Existing ARD

When updating a decision:

1. **Minor clarification**: Edit the existing ARD directly
2. **Status change**: Update Status section (e.g., ACCEPTED → DEPRECATED)
3. **Major change**: Create new ARD that supersedes old one:
   - New ARD references old: "Supersedes ARD-003"
   - Old ARD updated: Status = SUPERSEDED by ARD-009

## ARD Status Values

- **PROPOSED**: Under discussion, not yet decided
- **ACCEPTED**: Decision made and implemented
- **DEPRECATED**: No longer recommended but not replaced
- **SUPERSEDED**: Replaced by a newer ARD

## Current ARDs

| Number | Title | Status |
|--------|-------|--------|
| 000 | Template | TEMPLATE |
| 001 | OpenRouter for Vision and Text Models | ACCEPTED |
| 002 | Composite Image Grid for Vision Analysis | ACCEPTED |
| 003 | JSON File Storage | ACCEPTED |
| 004 | Multi-Agent Architecture | ACCEPTED |
| 005 | Taste Model Design | ACCEPTED |
| 006 | Typer CLI Design | ACCEPTED |
| 007 | Browser Scraping via Claude Code MCP | ACCEPTED |
| 008 | Two-Score Evaluation System | ACCEPTED |
| 009 | Gemini 3 Flash as Default Model | ACCEPTED |

## Tips

- Keep ARDs concise (1-2 pages max)
- Focus on the "why" not just the "what"
- Include code paths/file references where relevant
- Be honest about trade-offs in Consequences
- Reference other ARDs when decisions are related
