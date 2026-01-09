# PRD — Agentic Home Listing Aesthetic Evaluator

## 1. Purpose

Create a local, agentic system that ingests real estate listings (primarily Zillow URLs, secondarily agent-shared listings), analyzes them using vision and text models, and produces a reliable ranking of houses based on Francis’s aesthetic, functional, and contextual preferences.

The system’s core objective is to outperform manual scanning by filtering, scoring, and shortlisting houses that genuinely match taste, while explicitly penalizing violations.

Secondarily, the system should:

• Generate human-readable house briefs
• Surface renovation and transformation potential
• Evolve and refine a persistent “taste model”
• Periodically distill preferences into a single `aesthetics.md` reference file

This is a founder prototype. CLIs, local services, and automations are acceptable.

---

## 2. Primary Users

Primary: Francis
Secondary: none (v1 explicitly single-user, taste-specific)

---

## 3. Core User Problems

• Zillow filters cannot express aesthetic or qualitative constraints.
• Visual scanning is slow, noisy, and cognitively expensive.
• Taste evolves during a search but is rarely formalized.
• Renovation upside is hard to evaluate consistently.
• Human shortlisting scales poorly.

---

## 4. Success Criteria

The system is successful if:

• It consistently pushes strong matches to the top and weak matches to the bottom.
• It disqualifies obvious aesthetic mismatches without manual review.
• It produces explanations that feel aligned with real taste.
• It reduces the time spent per viable house by at least 3–5×.
• After multiple runs, `aesthetics.md` becomes sharper, not vaguer.

Non-goals (v1):

• Generalization to other users
• Full UI or marketplace integration
• Autonomous outreach or scheduling

---

## 5. Core Concepts

### 5.1 Taste Model (Persistent Local Object)

A local, versioned domain object that agents read from and write to.

Must include:

• Explicit principles and anti-principles
• Weighted aesthetic dimensions
• Hard vs soft constraints
• Visual exemplars (liked / disliked)
• Extracted latent preferences
• Location and contextual attributes (neighborhood type, school score sensitivity, density, etc.)
• Renovation tolerance and budget heuristics
• Violation patterns (“reject if…”)

Canonical projection:

`aesthetics.md`
Human-readable, periodically regenerated, treated as the authoritative spec.

Machine representation:

`taste.json` (or equivalent structured form)
Used by agents for scoring and inference.

---

### 5.2 Dual Evaluation Tracks

Each house produces two independent evaluations:

1. **Present-Fit Score (Primary)**
   Strict, penalty-oriented, optimized for filtering.

2. **Potential Score (Secondary)**
   Design-oriented, highlights transformation paths, rough cost classes, and upside scenarios.

---

### 5.3 House Object

Each ingested house becomes a normalized internal object:

• Listing metadata
• Structured features
• Image set
• Derived vision descriptors
• Evaluation outputs
• User annotations
• Versioned scores

Stored locally for re-scoring.

---

## 6. User Experience (v1)

CLI-first.

Examples:

`house ingest zillow <url>`
`house ingest zillow-search <url>`
`house ingest folder ./listings/`
`house score <house_id>`
`house batch-score ./active-search/`
`taste review`
`taste distill`
`taste annotate <house_id>`

Primary flows:

1. Drop Zillow URL or search → system fetches, parses, stores, scores.
2. System outputs:
   • Present-fit score
   • Potential score
   • Justification
   • House brief
   • Ranked batch if applicable
3. Francis adds free-form feedback.
4. Agents propose taste updates.
5. Periodic regeneration of `aesthetics.md`.

---

## 7. Functional Requirements

### 7.1 Ingestion

• Accept Zillow listing URLs
• Accept Zillow search results pages
• Accept manual listing bundles (images + text)
• Extract: images, captions, descriptions, structured facts
• Normalize into internal schema

---

### 7.2 Vision Analysis

• Multi-image aesthetic analysis
• Room-level classification (kitchen, living, exterior, etc.)
• Feature extraction (light, materials, layout signals, renovation quality)
• Negative signal detection (flip patterns, cheap materials, visual clutter, bad proportions, etc.)
• Embedding generation for taste matching

---

### 7.3 Present-Fit Scoring

Produces:

• Numerical score
• Pass/fail risk flags
• Violations
• Dimension breakdown
• Short justification

Behavior:

• Hard penalties for anti-requirements
• Conservative bias
• Optimized for rejection accuracy

---

### 7.4 Potential Scoring

Produces:

• Potential score
• Renovation ideas
• Feasibility band (light / medium / heavy)
• Rough cost class
• Risk notes
• Upside narrative

---

### 7.5 House Brief Generator

Generates a structured brief:

• Executive summary
• Aesthetic alignment
• Strengths
• Weaknesses
• Deal-breakers
• Renovation paths
• Who this house is “for”
• Verdict

---

### 7.6 Taste Evolution

• Accept raw user commentary
• Compare decisions vs predictions
• Detect emerging patterns
• Propose new requirements and anti-requirements
• Update weighted dimensions
• Store new exemplars
• Track rejected vs shortlisted houses

All taste changes must be:

• Reviewable
• Diffable
• Reversible

---

### 7.7 Distillation Engine

On demand:

`taste distill`

Produces:

• Updated `aesthetics.md`
• Change log
• Confidence notes
• Open questions

---

## 8. Non-Functional Requirements

• Local-first
• Automatable
• Idempotent ingestion
• Re-scorable history
• Traceable outputs
• Deterministic enough to compare runs
• Cheap enough for repeated use
• Fast enough to batch dozens of houses

---

## 9. Agent Architecture (Conceptual)

Minimum viable agents:

1. Ingestion Agent
2. Vision Analysis Agent
3. Present-Fit Judge
4. Potential & Renovation Agent
5. House Brief Agent
6. Taste Curator Agent
7. Distillation Agent
8. Batch Ranking Orchestrator

Shared resources:

• Taste store
• House store
• Embedding store
• Scoring rubric
• Audit log

---

## 10. Out of Scope (v1)

• Mobile app
• Browser extension
• Realtor integrations
• Automated offer logic
• Full financial modeling
• Multi-user profiles

---

## 11. Open Questions (to close during design)

• How strict should automatic disqualification be?
• How to weight image vs description vs inferred signals?
• What constitutes a “violation” vs “tradeoff”?
• What is the minimal renovation cost model?
• How often should taste auto-update vs prompt?

---

## 12. v1 Milestone Plan (Suggested)

Phase 1 — Core loop
• Zillow ingestion
• Image analysis
• Present-fit scoring
• CLI batch runs
• Local persistence

Phase 2 — Taste system
• Exemplars
• Feedback ingestion
• Taste proposals
• `aesthetics.md` generation

Phase 3 — Potential layer
• Renovation ideation
• Cost banding
• Transformation scoring
• Comparative ranking

---