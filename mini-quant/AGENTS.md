<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-26 | Updated: 2026-04-26 -->

# Mini-Quant

A complete, self-sustained quantitative research and trading platform optimized for one-man operations. Encompasses the entire lifecycle from research to execution.

## Purpose

Mini-Quant provides an end-to-end quant trading workflow:
- Data gathering from free/public APIs
- Alpha ideation and expression generation
- Multi-region backtesting (USA, EMEA, CHN, IND, AMER)
- Alpha management and evaluation
- Trade execution with risk management

## Key Files

| File | Purpose |
|------|---------|
| `__init__.py` | Package initialization, exports `OneManQuantSystem` |
| `one_man_quant_system.py` | Main orchestrator, coordinates all components |
| `data_gathering_engine.py` | Multi-source data collection (Yahoo Finance, Alpha Vantage, etc.) |
| `quant_research_module.py` | Research hypothesis generation, alpha expression creation |
| `alpha_backtesting_system.py` | Multi-region backtesting with performance metrics |
| `alpha_pool_storage.py` | SQLite database for alpha management and tracking |
| `trading_algorithm_engine.py` | Real-time signal evaluation, position sizing, risk management |
| `requirements.txt` | Dependencies: pandas, numpy, yfinance |

## Architecture

```
OneManQuantSystem
    ├── DataGatheringEngine
    ├── QuantResearchModule
    ├── AlphaBacktestingSystem
    ├── AlphaPoolStorage
    ├── TradingAlgorithmEngine
    └── BrokerAccessLayer
```

## For AI Agents

### Entry Point
```python
from mini_quant import OneManQuantSystem

system = OneManQuantSystem(config)
system.run_complete_workflow(regions=['USA', 'EMEA', 'CHN'])
```

### Key Patterns
- **Orchestrator pattern**: `OneManQuantSystem` coordinates all sub-modules
- **Region-specific handling**: Each module supports USA, EMEA, CHN, IND, AMER
- **SQLite persistence**: Alpha pool stored in `alpha_pool.db`
- **Free data sources**: Yahoo Finance, Alpha Vantage, Polygon.io

### Alpha Evaluation Criteria
- Minimum Sharpe: 1.5
- Minimum Positive Regions: 3
- Maximum Drawdown: -15%
- Minimum Win Rate: 55%
- Minimum Trades: 50

### Risk Management
- Position Size Limit: 10% per position
- Daily Loss Limit: 2%
- Maximum Exposure: 100%

### Integration with Generation Two
```python
from generation_two import EnhancedTemplateGeneratorV3
gen2 = EnhancedTemplateGeneratorV3(credentials_path="credential.txt")
config = {'alpha_generator': gen2}
```
