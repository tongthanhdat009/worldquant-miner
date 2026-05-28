# Provider Alpha Architecture

## Overview

Replace local Ollama with external API providers (OpenAI, Anthropic, custom) for alpha generation.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ProviderAlphaGenerator                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   OpenAI    │  │  Anthropic  │  │   Custom    │           │
│  │   Client    │  │   Client    │  │   Client    │           │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘           │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           ▼                                    │
│                  ┌──────────────┐                              │
│                  │  API Router  │                              │
│                  └──────┬───────┘                              │
└──────────────────────────┼──────────────────────────────────────┘
                           ▼
              ┌────────────────────────┐
              │  External API Provider │
              │  (OpenAI/Anthropic)    │
              └────────────────────────┘
```

## Components

### 1. ProviderAlphaGenerator

Main class - generate alphas via external API.

```python
class ProviderAlphaGenerator:
    def __init__(
        self,
        provider: str,      # "openai" | "anthropic" | "custom"
        api_key: str,       # API key
        api_base: str,       # Base URL
        model: str           # Model name
    )

    def generate_alpha(self, prompt: str) -> Dict
    def generate_batch(self, prompts: List[str]) -> List[Dict]
```

### 2. Supported Providers

| Provider | API Endpoint | Default Model |
|----------|-------------|---------------|
| OpenAI | `https://api.openai.com/v1/chat/completions` | gpt-4o |
| Anthropic | `https://api.anthropic.com/v1/messages` | claude-sonnet-4-20250514 |
| Custom | User-defined | user-defined |

### 3. Environment Variables

```bash
# Provider Config
PROVIDER=openai                    # openai | anthropic | custom
PROVIDER_API_KEY=sk-...            # API key
PROVIDER_API_BASE=https://api...   # Base URL (optional)
PROVIDER_MODEL=gpt-4o              # Model name (optional)
```

## Implementation

### File: provider_alpha_generator.py

```python
# Usage
from provider_alpha_generator import ProviderAlphaGenerator

gen = ProviderAlphaGenerator(
    provider="openai",
    api_key="sk-...",
    model="gpt-4o"
)

result = gen.generate_alpha("Generate alpha for tech stocks")
# {"expression": "...", "idea": "...", "rationale": "..."}
```

### Integration with Orchestrator

```python
# Replace Ollama with Provider
class AlphaOrchestrator:
    def __init__(self, config):
        if config.get("use_provider"):
            self.generator = ProviderAlphaGenerator(**config["provider"])
        else:
            self.generator = OllamaAlphaGenerator(**config["ollama"])
```

## Flow

```
User Request
    │
    ▼
AlphaOrchestrator
    │
    ▼
ProviderAlphaGenerator
    │
    ├──► OpenAI API ──► gpt-4o/gpt-4o-mini
    │
    ├──► Anthropic API ──► claude-sonnet/claude-haiku
    │
    └──► Custom API ──► User-defined model
    │
    ▼
Parse Response (JSON)
    │
    ▼
AlphaExpressionMiner (validate)
    │
    ▼
WorldQuantBrain API (simulate/submit)
```

## Response Format

```json
{
  "expression": "ts_mean(rank(close(0) / close(20)), 20)",
  "idea": "Mean reversion strategy",
  "rationale": "Use rank + ts_mean for mean reversion"
}
```

## Error Handling

| Error | Handling |
|-------|----------|
| API timeout | Retry 3x with exponential backoff |
| Invalid API key | Log error, fallback to next provider |
| Rate limit | Wait 60s, retry |
| Parse error | Return raw response |

## Testing

```bash
# Test OpenAI
python provider_alpha_generator.py --provider openai --api-key $OPENAI_API_KEY

# Test Anthropic
python provider_alpha_generator.py --provider anthropic --api-key $ANTHROPIC_API_KEY

# Test Custom
python provider_alpha_generator.py --provider custom --api-base http://localhost:8000 --model custom-model
```

## Migration from Ollama

| Ollama | Provider |
|--------|----------|
| `POST /api/generate` | `POST /v1/chat/completions` |
| Local model | Remote model |
| No API key | Requires API key |
| localhost:11434 | api.openai.com / api.anthropic.com |

## Cost Estimation

| Provider | Input | Output | Notes |
|----------|-------|--------|-------|
| OpenAI gpt-4o | $2.50/1M | $10/1M | Best quality |
| OpenAI gpt-4o-mini | $0.15/1M | $0.60/1M | Fast, cheap |
| Anthropic Sonnet | $3/1M | $15/1M | Good reasoning |
| Anthropic Haiku | $0.25/1M | $1.25/1M | Fast |

## Security

- Store API keys in environment variables
- Never commit keys to source
- Use `.env` file with `.gitignore`
- Rotate keys periodically