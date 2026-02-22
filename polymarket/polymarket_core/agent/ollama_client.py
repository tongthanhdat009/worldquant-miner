from __future__ import annotations

import json
from urllib import request
from urllib.error import HTTPError


class OllamaClient:
    def __init__(
        self,
        *,
        model: str = "qwen2.5-coder:1.5b",
        host: str = "http://127.0.0.1:11434",
        timeout_seconds: int = 60,
    ) -> None:
        self.model = model
        self.host = host.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def chat(self, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.1},
        }
        chat_req = request.Request(
            f"{self.host}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(chat_req, timeout=self.timeout_seconds) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            message = body.get("message", {})
            return str(message.get("content", ""))
        except HTTPError as exc:
            if exc.code != 404:
                raise

        # Fallback for environments where /api/chat is unavailable.
        prompt = "\n".join(f"{item['role']}: {item['content']}" for item in messages)
        generate_payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1},
        }
        gen_req = request.Request(
            f"{self.host}/api/generate",
            data=json.dumps(generate_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(gen_req, timeout=self.timeout_seconds) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return str(body.get("response", ""))

