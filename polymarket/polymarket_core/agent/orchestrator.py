from __future__ import annotations

import json
from typing import Any

from polymarket_core.config import PipelineConfig

from .ollama_client import OllamaClient
from .tools import AgentTool, default_tools


class AgentOrchestrator:
    def __init__(
        self,
        *,
        config: PipelineConfig | None = None,
        llm: OllamaClient | None = None,
        tools: list[AgentTool] | None = None,
        max_steps: int = 6,
    ) -> None:
        self.config = config or PipelineConfig()
        self.llm = llm or OllamaClient()
        self.max_steps = max_steps
        self.tools = tools or default_tools(self.config)
        self.tool_map = {tool.name: tool for tool in self.tools}

    def run(self, user_goal: str) -> dict[str, Any]:
        messages = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": user_goal},
        ]
        trace: list[dict[str, Any]] = []

        for _ in range(self.max_steps):
            raw = self.llm.chat(messages)
            parsed = self._parse_response(raw)
            if "final_answer" in parsed and parsed["final_answer"]:
                return {"final_answer": parsed["final_answer"], "trace": trace}

            tool_name = parsed.get("tool")
            tool_input = parsed.get("tool_input", {})
            if not isinstance(tool_name, str) or tool_name not in self.tool_map:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Invalid tool choice. Pick one tool from the allowed list "
                            "or provide final_answer."
                        ),
                    }
                )
                continue

            normalized_input = tool_input if isinstance(tool_input, dict) else {}
            result = self.tool_map[tool_name].run(normalized_input)
            trace.append({"tool": tool_name, "input": tool_input, "result": result})
            messages.extend(
                [
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content": f"Tool result:\n{json.dumps(result)}"},
                ]
            )

        return {
            "final_answer": "Stopped after max steps without final answer.",
            "trace": trace,
        }

    def _system_prompt(self) -> str:
        tool_lines = [f"- {tool.name}: {tool.description}" for tool in self.tools]
        return (
            "You are a quantitative research agent. "
            "Use tools to gather evidence before final recommendations.\n"
            "Available tools:\n"
            + "\n".join(tool_lines)
            + "\nReturn ONLY JSON with keys: thought, tool, tool_input, final_answer.\n"
            "If using a tool, set final_answer to ''. "
            "When done, set final_answer and tool to ''."
        )

    @staticmethod
    def _parse_response(raw: str) -> dict[str, Any]:
        direct = _try_parse_json(raw)
        if direct is not None:
            return direct
        fenced = _extract_fenced_json(raw)
        if fenced is not None:
            parsed = _try_parse_json(fenced)
            if parsed is not None:
                return parsed
        return {"final_answer": raw}


def _try_parse_json(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


def _extract_fenced_json(text: str) -> str | None:
    start = text.find("```")
    if start < 0:
        return None
    end = text.find("```", start + 3)
    if end < 0:
        return None
    fenced = text[start + 3 : end].strip()
    if fenced.startswith("json"):
        return fenced[4:].strip()
    return fenced

