import json

from polymarket_core.agent.orchestrator import AgentOrchestrator
from polymarket_core.config import PipelineConfig


class FakeLLM:
    def __init__(self) -> None:
        self.calls = 0

    def chat(self, _messages):
        self.calls += 1
        if self.calls == 1:
            return json.dumps(
                {
                    "thought": "Need data first",
                    "tool": "market_research",
                    "tool_input": {"top_k": 2},
                    "final_answer": "",
                }
            )
        return json.dumps(
            {
                "thought": "Done",
                "tool": "",
                "tool_input": {},
                "final_answer": "Top opportunities prepared.",
            }
        )


class StubResearchTool:
    name = "market_research"
    description = "stub"

    def run(self, _params):
        return {"top_positions": [{"market_id": "x"}]}


def test_orchestrator_tool_then_finalize() -> None:
    orchestrator = AgentOrchestrator(
        config=PipelineConfig(),
        llm=FakeLLM(),
        tools=[StubResearchTool()],
    )
    result = orchestrator.run("find opportunities")
    assert "Top opportunities prepared." in result["final_answer"]
    assert len(result["trace"]) == 1
    assert result["trace"][0]["tool"] == "market_research"

