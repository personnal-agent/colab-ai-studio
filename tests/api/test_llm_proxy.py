"""Tests d'intégration d'API pour le proxy LLM compatible OpenAI."""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes_models import get_worker_gateway
from app.main import app
from app.services.worker_gateway import WorkerGateway
from app.storage.json_store import JSONDocumentStore


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_llm_proxy_nominal_streaming(client, tmp_path):
    chunks = [
        'data: {"choices":[{"delta":{"content":"Bonjour "}}]}\n\n',
        'data: {"choices":[{"delta":{"content":"monde !"}}]}\n\n',
        "data: [DONE]\n\n",
    ]

    received_requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        received_requests.append(json.loads(request.content.decode("utf-8")))
        return httpx.Response(
            200, headers={"Content-Type": "text/event-stream"}, text="".join(chunks)
        )

    gw = WorkerGateway(
        JSONDocumentStore(tmp_path),
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    async def get_url():
        return "local", "http://127.0.0.1:8190"

    gw.get_active_worker_url = get_url
    app.dependency_overrides[get_worker_gateway] = lambda: gw

    payload = {
        "model": "qwen2.5-7b",
        "messages": [{"role": "user", "content": [{"type": "text", "text": "Hi"}]}],
        "stream": True,
        "seed": 42,
        "custom_param": "foo",
    }
    resp = await client.post(
        "/v1/chat/completions", json=payload, headers={"Origin": "http://localhost:5173"}
    )
    assert resp.status_code == 200
    assert "Bonjour " in resp.text
    assert "monde !" in resp.text
    assert "data: [DONE]" in resp.text
    assert received_requests[0]["seed"] == 42
    assert received_requests[0]["custom_param"] == "foo"
    assert received_requests[0]["messages"][0]["content"] == [{"type": "text", "text": "Hi"}]
    await gw.aclose()


@pytest.mark.asyncio
async def test_llm_proxy_client_disconnect_triggers_cancel(client, tmp_path, monkeypatch):
    cancelled = []
    chunks = [
        'data: {"choices":[{"delta":{"content":"Token 1"}}]}\n\n',
        'data: {"choices":[{"delta":{"content":"Token 2"}}]}\n\n',
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/chat/cancel":
            cancelled.append(json.loads(request.content.decode("utf-8")).get("requestId"))
            return httpx.Response(200, json={"status": "cancelled"})
        return httpx.Response(
            200, headers={"Content-Type": "text/event-stream"}, text="".join(chunks)
        )

    gw = WorkerGateway(
        JSONDocumentStore(tmp_path),
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    async def get_url():
        return "colab", "https://colab-active.ngrok-free.app"

    gw.get_active_worker_url = get_url
    app.dependency_overrides[get_worker_gateway] = lambda: gw

    from fastapi import Request

    calls = [0]

    async def mock_is_disconnected(self):
        calls[0] += 1
        return calls[0] >= 2

    monkeypatch.setattr(Request, "is_disconnected", mock_is_disconnected)
    payload = {
        "model": "qwen2.5-7b",
        "messages": [{"role": "user", "content": "Hi"}],
        "stream": True,
    }
    resp = await client.post(
        "/v1/chat/completions", json=payload, headers={"Origin": "http://localhost:5173"}
    )
    assert resp.status_code == 200 and "Token 1" in resp.text and "data: [DONE]" not in resp.text
    assert len(cancelled) == 1 and cancelled[0].startswith("chat_")
    await gw.aclose()


@pytest.mark.asyncio
async def test_llm_proxy_asgi_disconnect_during_silent_wait(client, tmp_path, monkeypatch):
    cancelled = []

    async def slow_stream():
        yield b'data: {"choices":[{"delta":{"content":"First"}}}\n\n'
        await asyncio.sleep(0.8)
        yield b"data: [DONE]\n\n"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/chat/cancel":
            cancelled.append(json.loads(request.content.decode("utf-8")).get("requestId"))
            return httpx.Response(200, json={"status": "cancelled"})
        return httpx.Response(
            200, headers={"Content-Type": "text/event-stream"}, content=slow_stream()
        )

    gw = WorkerGateway(
        JSONDocumentStore(tmp_path),
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    async def get_url():
        return "local", "http://127.0.0.1:8190"

    gw.get_active_worker_url = get_url
    app.dependency_overrides[get_worker_gateway] = lambda: gw

    from fastapi import Request

    disconnect_after = False

    async def mock_is_disconnected(self):
        return disconnect_after

    monkeypatch.setattr(Request, "is_disconnected", mock_is_disconnected)

    async def trigger_disconnect():
        nonlocal disconnect_after
        await asyncio.sleep(0.15)
        disconnect_after = True

    asyncio.create_task(trigger_disconnect())

    payload = {
        "model": "qwen2.5-7b",
        "messages": [{"role": "user", "content": "Hi"}],
        "stream": True,
    }
    resp = await client.post(
        "/v1/chat/completions", json=payload, headers={"Origin": "http://localhost:5173"}
    )
    assert resp.status_code == 200
    assert len(cancelled) == 1
    assert cancelled[0].startswith("chat_")
    await gw.aclose()
