# ARD-009: Gemini 3 Flash as Default Model

## Status
ACCEPTED

## Context
The system was using GPT-4o for all vision and text operations. While GPT-4o provides excellent quality, the cost of ~$0.05 per house scored adds up:
- 100 houses = ~$5.00
- 1000 houses = ~$50.00

Given that house scoring involves relatively straightforward image description (rooms, materials, finishes) rather than complex reasoning, we evaluated whether a cheaper model could deliver comparable results.

## Decision
Switch default models from GPT-4o to Google's Gemini 3 Flash Preview.

**New model configuration:**
```python
DEFAULT_MODEL = "google/gemini-3-flash-preview"
VISION_MODEL = "google/gemini-3-flash-preview"
FAST_MODEL = "google/gemini-2.0-flash-001"
```

**Pricing comparison (per 1M tokens):**

| Model | Input | Output | Cost/House |
|-------|-------|--------|------------|
| GPT-4o (old) | $5.00 | $20.00 | ~$0.05 |
| Gemini 3 Flash (new) | $0.50 | $3.00 | ~$0.008 |

**Cost reduction: ~6x cheaper**

## Rationale

1. **Quality**: Gemini 3 Flash reportedly outperforms Gemini 2.5 Pro in benchmarks while being 3x faster. For real estate image analysis, this is more than sufficient.

2. **Multimodal**: Full support for images, text, and 1M token context window.

3. **Speed**: Designed for agentic workflows with low latency.

4. **Risk mitigation**: OpenRouter allows easy model switching if quality issues emerge.

## Consequences

**Positive:**
- 6x cost reduction (~$0.008 vs ~$0.05 per house)
- 100 houses: ~$0.80 instead of ~$5.00
- Faster response times
- Can afford more experimentation and iteration

**Negative:**
- Preview model (may have occasional instability)
- Less battle-tested than GPT-4o for vision tasks
- Output format may differ slightly (JSON parsing may need adjustment)
- Google model availability/rate limits differ from OpenAI

## Alternatives Considered

| Model | Input $/1M | Output $/1M | Notes |
|-------|------------|-------------|-------|
| GPT-4o Mini | $0.60 | $2.40 | Good but less capable than Gemini 3 Flash |
| Claude Sonnet 4 | $3.00 | $15.00 | Excellent but only 40% cheaper than GPT-4o |
| Claude Haiku 3.5 | $0.80 | $4.00 | Budget option, may miss material details |
| Gemini 2.5 Pro | $1.25 | $10.00 | Good middle ground |
| Gemini 2.5 Flash | $0.15 | $0.60 | Cheapest, but may sacrifice quality |

Gemini 3 Flash Preview offers the best balance of quality and cost for this use case.

## Rollback Plan

If quality issues emerge, revert to GPT-4o by changing `src/agents/base.py`:
```python
DEFAULT_MODEL = "openai/gpt-4o"
VISION_MODEL = "openai/gpt-4o"
```

## References
- [Gemini 3 Flash Preview | OpenRouter](https://openrouter.ai/google/gemini-3-flash-preview)
- [Google Gemini 3 Flash Announcement](https://blog.google/products/gemini/gemini-3-flash/)
