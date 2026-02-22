from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineConfig:
    lookback: int = 20
    min_liquidity: float = 1_000.0
    max_position: float = 0.10
    signal_threshold: float = 0.05
    credentials_path: str = "credential.txt"
    artifacts_dir: str = "artifacts"
    initial_capital_usd: float = 10_000.0
    execution_mode: str = "paper"
    clob_host: str = "https://clob.polymarket.com"
    clob_chain_id: int = 137
    live_max_orders: int = 3
    live_min_edge: float = 0.06
    force_real_data: bool = False
    cycle_backtest_scenarios: int = 80
    cycle_backtest_shock: float = 0.25
    cycle_min_avg_return: float = 0.02
    cycle_min_worst_return: float = -0.05

