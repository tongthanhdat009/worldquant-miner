# Polymarket Research Engine

<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-26 | Updated: 2026-04-26 -->

## Purpose

`polymarket` is a prediction-market research and execution framework for Polymarket event contracts. It provides a modular pipeline architecture with clear separation between data ingestion, factor scoring, backtesting, risk management, and order execution.

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies (Flask, py-clob-client), pytest config |
| `scripts/run_research.py` | Research pipeline entry point - scores markets and outputs position weights |
| `scripts/run_e2e.py` | End-to-end execution pipeline with paper/live modes |
| `scripts/run_full_cycle.py` | Full cycle: research -> backtest gate -> optional execution |
| `scripts/run_dashboard.py` | Flask web dashboard on port 5080 |
| `polymarket_core/config.py` | PipelineConfig dataclass with all tunable parameters |
| `polymarket_core/cycle/full_cycle_runner.py` | Orchestrates research, backtest, and execution phases |
| `polymarket_core/web/dashboard.py` | Flask app with /api/markets and /api/backtest endpoints |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `polymarket_core/adapters/` | External API adapters (Polymarket CLOB, mock adapters) |
| `polymarket_core/agent/` | Ollama AI agent orchestration layer |
| `polymarket_core/alpha/` | Factor library and scoring engine |
| `polymarket_core/backtest/` | Scenario backtesting with shock simulation |
| `polymarket_core/cycle/` | Full-cycle runner coordinating research/backtest/execution |
| `polymarket_core/data/` | Data ingestion and normalization from gamma-api.polymarket.com |
| `polymarket_core/engine/` | Paper simulation and evaluation |
| `polymarket_core/execution/` | Order execution via py-clob-client |
| `polymarket_core/pipeline/` | Research and E2E pipeline orchestration |
| `polymarket_core/portfolio/` | Risk constraints and position sizing |
| `polymarket_core/storage/` | Artifact persistence (JSON, HTML reports) |
| `polymarket_core/web/` | Flask dashboard and templates |
| `scripts/` | CLI entry points for all workflows |
| `tests/` | pytest test suite |

## For AI Agents

### Working Instructions

1. **Run research pipeline**:
   ```bash
   cd D:/repo/worldquant-miner/polymarket
   python -m scripts.run_research
   ```

2. **Run end-to-end (paper mode)**:
   ```bash
   python -m scripts.run_e2e --mode paper
   ```

3. **Run full cycle with auto-execute**:
   ```bash
   python -m scripts.run_full_cycle --mode paper --auto-execute
   ```

4. **Start dashboard**:
   ```bash
   python -m scripts.run_dashboard
   # Opens at http://127.0.0.1:5080
   ```

5. **Run tests**:
   ```bash
   pytest tests/ -v
   ```

### Testing Requirements

- Use pytest framework
- Run `pytest tests/ -v` before committing changes
- Test coverage target: 80%+
- All new modules require corresponding test files

### Common Patterns

**PipelineConfig usage**:
```python
from polymarket_core.config import PipelineConfig

config = PipelineConfig(
    execution_mode="paper",
    min_liquidity=500.0,
    signal_threshold=0.02,
    force_real_data=True,
)
```

**ResearchPipeline**:
```python
from polymarket_core.pipeline.research_pipeline import ResearchPipeline

pipeline = ResearchPipeline(config=config)
positions, report = pipeline.run()
```

**FullCycleRunner**:
```python
from polymarket_core.cycle.full_cycle_runner import FullCycleRunner

result = FullCycleRunner(config).run(
    mode="paper",
    auto_execute=True,
)
```

### Credentials

Set via environment variables or `polymarket/credential.txt`:
- `POLYMARKET_API_KEY`
- `POLYMARKET_API_SECRET`
- `POLYMARKET_API_PASSPHRASE`
- `POLYMARKET_PRIVATE_KEY` (required for live orders)

### Artifacts

All runs persist to `polymarket/artifacts/`:
- JSON artifacts with full run metadata
- HTML reports with trade summaries and PnL charts

## Dependencies

| Package | Purpose |
|---------|---------|
| `flask>=3.0.0` | Web dashboard |
| `py-clob-client>=0.34.6` | Polymarket CLOB integration |
| `pytest` | Testing framework (dev) |
