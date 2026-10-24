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
    received_requests = []
    raw = (
        'data: {"choices":[{"delta":{"content":"Bonjour "}}]}\n\n'
        'data: {"choices":[{"delta":{"content":"monde !"}}]}\n\n'
        "data: [DONE]\n\n"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        received_requests.append(json.loads(request.content.decode("utf-8")))
        return httpx.Response(200, headers={"Content-Type": "text/event-stream"}, text=raw)

    gw = WorkerGateway(
        JSONDocumentStore(tmp_path),
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    gw.get_active_worker_url = lambda: asyncio.sleep(0, result=("local", "http://127.0.0.1:8190"))
    app.dependency_overrides[get_worker_gateway] = lambda: gw

    payload = {
        "model": "qwen2.5-7b",
        "stream": True,
        "seed": 42,
        "custom_param": "foo",
        "messages": [{"role": "user", "content": [{"type": "text", "text": "Hi"}]}],
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
    raw = (
        'data: {"choices":[{"delta":{"content":"Token 1"}}]}\n\n'
        'data: {"choices":[{"delta":{"content":"Token 2"}}]}\n\n'
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/chat/cancel":
            cancelled.append(json.loads(request.content.decode("utf-8")).get("requestId"))
            return httpx.Response(200, json={"status": "cancelled"})
        return httpx.Response(200, headers={"Content-Type": "text/event-stream"}, text=raw)

    gw = WorkerGateway(
        JSONDocumentStore(tmp_path),
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    gw.get_active_worker_url = lambda: asyncio.sleep(
        0, result=("colab", "https://colab-active.ngrok-free.app")
    )
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
async def test_llm_proxy_asgi_disconnect_during_silent_wait(tmp_path):
    cancelled = []

    async def slow_stream():
        yield b'data: {"choices":[{"delta":{"content":"First"}}}\n\n'
        await asyncio.sleep(1.0)
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

    payload = {
        "model": "qwen2.5-7b",
        "messages": [{"role": "user", "content": "Hi"}],
        "stream": True,
    }
    body = json.dumps(payload).encode("utf-8")
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "path": "/v1/chat/completions",
        "raw_path": b"/v1/chat/completions",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json"), (b"origin", b"http://localhost:5173")],
    }

    rx_queue = asyncio.Queue()
    await rx_queue.put({"type": "http.request", "body": body, "more_body": False})
    sent_messages = []

    first_received = asyncio.Event()

    async def send(msg):
        sent_messages.append(msg)
        if msg.get("type") == "http.response.body" and b"First" in msg.get("body", b""):
            first_received.set()

    app_task = asyncio.create_task(app(scope, rx_queue.get, send))
    await asyncio.wait_for(first_received.wait(), timeout=2.0)

    # Transmission réelle de l'événement ASGI http.disconnect
    await rx_queue.put({"type": "http.disconnect"})
    await asyncio.wait_for(app_task, timeout=2.0)
    await asyncio.sleep(0.05)

    assert len(cancelled) == 1
    assert cancelled[0].startswith("chat_")
    await gw.aclose()
    app.dependency_overrides.clear()
