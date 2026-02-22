import argparse
import json

from polymarket_core.agent.ollama_client import OllamaClient
from polymarket_core.agent.orchestrator import AgentOrchestrator
from polymarket_core.config import PipelineConfig


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Ollama-based polymarket AI agent.")
    parser.add_argument(
        "--goal",
        required=True,
        help="Research goal for the agent, e.g. 'Find top 3 markets and backtest them'.",
    )
    parser.add_argument("--model", default="qwen2.5-coder:1.5b", help="Ollama model name.")
    parser.add_argument("--host", default="http://127.0.0.1:11434", help="Ollama host.")
    parser.add_argument("--max-steps", type=int, default=6, help="Maximum tool-use steps.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    orchestrator = AgentOrchestrator(
        config=PipelineConfig(),
        llm=OllamaClient(model=args.model, host=args.host),
        max_steps=args.max_steps,
    )
    result = orchestrator.run(args.goal)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

