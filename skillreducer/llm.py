from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class LLMConfig:
    mode: str = "mock"
    base_url: str = ""
    api_key_env: str = "OPENAI_API_KEY"
    model: str = "mock-model"
    timeout: int = 60


class LLMClient:
    """Small OpenAI-compatible chat client using only the standard library."""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.0) -> str:
        if self.config.mode == "mock" or not self.config.base_url:
            return self._mock(messages)
        payload = {"model": self.config.model, "messages": messages, "temperature": temperature}
        request = urllib.request.Request(
            self.config.base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ.get(self.config.api_key_env, '')}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc
        return body["choices"][0]["message"]["content"]

    def _mock(self, messages: list[dict[str, str]]) -> str:
        joined = "\n".join(message.get("content", "") for message in messages)
        keywords: list[str] = []
        for raw in joined.split():
            word = raw.strip(".,:;()[]{}").lower()
            if len(word) > 4 and word not in keywords:
                keywords.append(word)
            if len(keywords) >= 8:
                break
        return " ".join(keywords) or "mock response"

