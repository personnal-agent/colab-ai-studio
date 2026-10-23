"""Adaptateur d'inférence LLM OpenAI-compatible (app/local_worker/backends/openai_compat.py).

Gère la communication avec LM Studio ou tout serveur compatible OpenAI (port 1234 par défaut) :
- Appels standards POST /v1/chat/completions (bloquants).
- Relais streaming SSE asynchrone avec extraction des deltas textuels.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx


class OpenAICompatibleBackend:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:1234",
        client: httpx.AsyncClient | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client
        self.timeout = timeout

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(timeout=self.timeout)

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        client = self._get_client()
        payload = {"model": model, "messages": messages, "stream": False, **kwargs}
        try:
            res = await client.post(f"{self.base_url}/v1/chat/completions", json=payload)
            res.raise_for_status()
            return res.json()
        finally:
            if self._client is None:
                await client.aclose()

    async def stream_chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        client = self._get_client()
        payload = {"model": model, "messages": messages, "stream": True, **kwargs}
        try:
            async with client.stream(
                "POST", f"{self.base_url}/v1/chat/completions", json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    clean_line = line.strip()
                    if not clean_line or clean_line.startswith(":"):
                        continue
                    if clean_line == "data: [DONE]":
                        break
                    if clean_line.startswith("data: "):
                        data_str = clean_line[6:].strip()
                        try:
                            chunk_json = json.loads(data_str)
                            choices = chunk_json.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        finally:
            if self._client is None:
                await client.aclose()
