# ARD-004: Multi-Agent Architecture

## Status
ACCEPTED

## Context
The system needs to analyze houses across multiple dimensions:
- Visual analysis of listing photos
- Scoring against taste preferences
- Identifying renovation potential
- Generating human-readable briefs
- Learning from user feedback

A single monolithic approach would be complex and hard to maintain.

## Decision
Use a multi-agent architecture where specialized agents handle distinct tasks.

**Agents:**
1. **Vision Agent** (`src/agents/vision.py`)
   - Analyzes composite image grid
   - Extracts room types, materials, aesthetic qualities
   - Identifies red flags (flip patterns, cheap finishes)

2. **Present-Fit Agent** (`src/agents/present_fit.py`)
   - Scores house against taste model
   - Checks hard constraints (violations)
   - Evaluates weighted dimensions
   - Generates strict justification

3. **Potential Agent** (`src/agents/potential.py`)
   - Identifies transformation opportunities
   - Estimates renovation feasibility
   - Classifies cost (light/medium/heavy)

4. **Brief Agent** (`src/agents/brief.py`)
   - Synthesizes all analysis into readable brief
   - Includes verdict and recommendations

5. **Taste Curator Agent** (`src/agents/taste_curator.py`)
   - Processes user feedback
   - Proposes taste model updates

6. **Distiller Agent** (`src/agents/distiller.py`)
   - Converts taste.json to human-readable aesthetics.md

**Orchestrator** (`src/agents/orchestrator.py`)
- Coordinates agent execution
- Manages pipeline: Vision → Present-Fit → Potential → Brief

## Consequences

**Positive:**
- Clear separation of concerns
- Each agent can be tested independently
- Easy to swap models per agent (e.g., Claude for text, GPT-4o for vision)
- Pipeline is transparent and debuggable
- Agents can be run selectively (e.g., re-score without re-analyzing vision)

**Negative:**
- More files and abstractions
- Sequential execution adds latency
- State must be persisted between agent runs
- Coordinating agent dependencies requires orchestration logic

## Alternatives Considered

1. **Single large prompt**: Simpler but unwieldy, hard to iterate on parts
2. **Function calling within one agent**: Less modular, harder to test
3. **Parallel agent execution**: More complex, agents have dependencies
4. **LangChain/LangGraph**: Additional dependency, learning curve, less control
