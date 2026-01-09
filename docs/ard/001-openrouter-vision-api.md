# ARD-001: OpenRouter for Vision and Text Models

## Status
ACCEPTED

## Context
The system needs to analyze real estate listing images to extract aesthetic qualities, materials, room types, and detect red flags. It also needs text models for scoring against taste preferences and generating briefs.

Options considered:
- Direct OpenAI API
- Direct Anthropic API
- OpenRouter as unified gateway

## Decision
Use OpenRouter as the API gateway for all model access (vision and text).

**Models used:**
- Vision: `google/gemini-3-flash-preview` via OpenRouter for image analysis
- Text: `google/gemini-3-flash-preview` via OpenRouter for scoring and brief generation
- Fast: `google/gemini-2.0-flash-001` for quick operations

*Updated Jan 2026: Switched from GPT-4o ($5/$20 per 1M tokens) to Gemini 3 Flash ($0.50/$3 per 1M tokens) for ~6x cost reduction with comparable quality.*

**Implementation:**
- Single `OpenRouterClient` class in `src/services/openrouter.py`
- Configured via `OPENROUTER_API_KEY` environment variable
- Base URL: `https://openrouter.ai/api/v1`

## Consequences

**Positive:**
- Single API key manages access to multiple model providers
- Easy to swap models (e.g., switch to Claude for text, keep GPT-4o for vision)
- Cost tracking across all models in one dashboard
- Fallback options if one provider has issues

**Negative:**
- Additional latency (~50-100ms) through proxy
- Dependent on OpenRouter availability
- Slightly higher cost than direct API access

## Alternatives Considered

1. **Direct OpenAI API**: Simpler but locks us into one provider
2. **Direct Anthropic API**: Claude excels at text but vision capabilities were less mature at decision time
3. **Multiple direct APIs**: More complex key management, harder to compare costs
