"""Tests unitaires pour OpenAICompatibleBackend (Step 4 Issue #2).

Vérifie :
1. Appel non-streaming renvoyant le contenu complet.
2. Appel streaming renvoyant les chunks SSE delta.
"""

from __future__ import annotations

import httpx

from app.local_worker.backends.openai_compat import OpenAICompatibleBackend


async def test_chat_completion_non_streaming():
    def mock_handler(request: httpx.Request):
        if request.url.path == "/v1/chat/completions" and request.method == "POST":
            return httpx.Response(
                200,
                json={
                    "id": "chatcmpl-1",
                    "choices": [{"message": {"role": "assistant", "content": "Scénario généré"}}],
                },
            )
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    backend = OpenAICompatibleBackend(base_url="http://mock-llm", client=client)

    messages = [{"role": "user", "content": "Écris une scène"}]
    res = await backend.chat_completion(messages=messages, model="qwen-3.8-turbo")
    assert res["choices"][0]["message"]["content"] == "Scénario généré"


async def test_chat_completion_streaming():
    stream_content = (
        b'data: {"choices":[{"delta":{"content":"Plan 1 : "}}]}\n\n'
        b'data: {"choices":[{"delta":{"content":"La brume."}}]}\n\n'
        b"data: [DONE]\n\n"
    )

    def mock_handler(request: httpx.Request):
        if request.url.path == "/v1/chat/completions" and request.method == "POST":
            return httpx.Response(
                200,
                content=stream_content,
                headers={"content-type": "text/event-stream"},
            )
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    backend = OpenAICompatibleBackend(base_url="http://mock-llm", client=client)

    chunks: list[str] = []
    async for chunk in backend.stream_chat_completion(
        messages=[{"role": "user", "content": "prompt"}], model="qwen-3.8-turbo"
    ):
        chunks.append(chunk)

    assert len(chunks) == 2
    assert "".join(chunks) == "Plan 1 : La brume."
