from polymarket_core.adapters.credentials import load_polymarket_credentials
from polymarket_core.adapters.market_adapter import MarketDataAdapter
from polymarket_core.adapters.polymarket_http_adapter import PolymarketHTTPAdapter
from polymarket_core.alpha.factors import FactorEngine
from polymarket_core.config import PipelineConfig
from polymarket_core.data.ingestion import MarketIngestionService
from polymarket_core.engine.simulator import PaperSimulator, SimulationReport
from polymarket_core.portfolio.risk import PositionIntent, RiskManager


class ResearchPipeline:
    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig()
        self.adapter = self._build_adapter()
        self.ingestion = MarketIngestionService(adapter=self.adapter)
        self.factor_engine = FactorEngine()
        self.risk_manager = RiskManager(self.config)
        self.simulator = PaperSimulator()

    def run(self) -> tuple[list[PositionIntent], SimulationReport]:
        records = self.ingestion.load()
        filtered = [r for r in records if r.liquidity >= self.config.min_liquidity]
        scored = self.factor_engine.score(filtered)
        positions = self.risk_manager.build_positions(scored)
        report = self.simulator.run(positions)
        return positions, report

    def _build_adapter(self) -> MarketDataAdapter:
        credentials = load_polymarket_credentials(self.config.credentials_path)
        api_key = credentials.api_key if credentials is not None else None
        api_secret = credentials.api_secret if credentials is not None else None
        api_passphrase = credentials.api_passphrase if credentials is not None else None
        return PolymarketHTTPAdapter(
            api_key=api_key,
            api_secret=api_secret,
            api_passphrase=api_passphrase,
        )

