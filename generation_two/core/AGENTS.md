<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-26 | Updated: 2026-04-26 -->

# core

## Purpose
Template generation engine, mining coordination, and WorldQuant Brain API integration. Contains the core alpha mining logic.

## Key Files

| File | Description |
|------|-------------|
| `enhanced_template_generator_v3.py` | Main generator with LLM integration |
| `template_generator.py` | Base template generation |
| `algorithmic_template_generator.py` | Algorithm-based template creation |
| `expression_compiler.py` | Alpha expression compilation |
| `mining/mining_coordinator.py` | Coordinates mining operations |
| `mining/duplicate_detector.py` | Detects duplicate alphas |
| `mining/correlation_tracker.py` | Tracks alpha correlations |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `mining/` | Alpha mining logic |
| `recorder/` | Decision and audit logging |
| `utils/` | Request handling, retries |
| `config/` | Configuration management |

## Dependencies
- WorldQuant Brain API
- Ollama (local LLM)

<!-- MANUAL: -->