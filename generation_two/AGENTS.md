<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-26 | Updated: 2026-04-26 -->

# generation_two

## Purpose
Main Python GUI alpha mining system with WorldQuant Brain integration. Recommended entry point for alpha mining operations. Provides complete workflow: data fields → operators → config → generation → simulation → mining.

## Key Files

| File | Description |
|------|-------------|
| `__init__.py` | Package init, exports `EnhancedTemplateGeneratorV3` |
| `build.py` | Build script for releases |
| `setup.py` | Package setup configuration |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `core/` | Template generation, mining, correlation (see `core/AGENTS.md`) |
| `gui/` | Tkinter GUI with workflow panels (see `gui/AGENTS.md`) |
| `ollama/` | Ollama integration, model management (see `ollama/AGENTS.md`) |
| `storage/` | Backtest storage, cluster analysis (see `storage/AGENTS.md`) |
| `data_fetcher/` | Data field and operator fetchers (see `data_fetcher/AGENTS.md`) |
| `evolution/` | Alpha evolution, bandits, quality monitoring (see `evolution/AGENTS.md`) |
| `self_evolution/` | Self-evolving code generation (see `self_evolution/AGENTS.md`) |
| `spec/` | Template specifications |
| `constants/` | Constants and enums |
| `tests/` | Test suites (see `tests/AGENTS.md`) |

## For AI Agents

### Entry Point
```python
from generation_two import EnhancedTemplateGeneratorV3
gen = EnhancedTemplateGeneratorV3(credentials_path="credential.txt")
gen.run_full_workflow()
```

### Key Patterns
- **Tkinter GUI**: Multi-step workflow (data fields → mining)
- **WorldQuant Brain API**: Expression submission, simulation
- **Ollama integration**: Local LLM for alpha ideation
- **SQLite storage**: Backtest history, alpha pool

### Dependencies
- Python 3.10+
- pandas, numpy, requests
- Tkinter (built-in)
- yfinance (data)

<!-- MANUAL: -->