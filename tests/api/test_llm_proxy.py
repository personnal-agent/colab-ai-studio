"""Tests d'intégration pour le proxy LLM compatible OpenAI (Step 4 du Plan 02).

Valide les deux branches du fragment alt de 08-sequence-proxy-llm.svg :
1. Branche nominale : streaming SSE data: {"choices":[...]} clôturé par data: [DONE].
2. Branche d'annulation : déconnexion client (request.is_disconnected() == True)
   interrompant le flux amont, propageant POST /v1/chat/cancel et ne générant pas data: [DONE].
3. Mode synchrone non-streaming (stream=False).
4. Garde-fous configuration (llmProxy.enabled = False -> 503).
5. Erreurs de transport / worker amont injoignable (503).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
from starlette.requests import Request

from app.api import routes_config, routes_crud, routes_llm_proxy
from app.main import app
from app.models.domain import ExecutionMode, StudioConfig
from app.services.worker_gateway import WorkerGateway
from app.storage.json_store import JSONDocumentStore


@pytest.fixture
async def llm_proxy_env(tmp_path: Path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)

    store = JSONDocumentStore(data_dir)
    routes_crud._json_store = store
    routes_config._json_store = store
    routes_llm_proxy._json_store = store

    cfg = StudioConfig(executionMode=ExecutionMode.LOCAL)
    cfg.local.workerUrl = "http://mock-worker"
    await store.write_dict("config.json", cfg.model_dump())

    cancelled_requests: list[str] = []

    def mock_worker(request: httpx.Request):
        if request.url.path == "/v1/chat/completions":
            body = json.loads(request.content.decode("utf-8"))
            if body.get("stream"):
                sse_lines = [
                    'data: {"id":"chat-1","choices":[{"delta":{"content":"Salut"}}]}\n\n',
                    'data: {"id":"chat-1","choices":[{"delta":{"content":" l\'ami"}}]}\n\n',
                    "data: [DONE]\n\n",
                ]
                return httpx.Response(
                    200,
                    content="".join(sse_lines).encode("utf-8"),
                    headers={"Content-Type": "text/event-stream"},
                )
            return httpx.Response(
                200,
                json={
                    "id": "chat-sync",
                    "object": "chat.completion",
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": "Reponse complete"},
                            "finish_reason": "stop",
                        }
                    ],
                },
            )

        if request.url.path == "/v1/chat/cancel" and request.method == "POST":
            cancel_body = json.loads(request.content.decode("utf-8"))
            cancelled_requests.append(cancel_body.get("requestId", ""))
            return httpx.Response(200, json={"status": "cancelled"})

        return httpx.Response(404)

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_worker))
    gateway = WorkerGateway(store=store, client=mock_client)
    routes_llm_proxy._gateway = gateway

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, gateway, cancelled_requests, store


async def test_llm_proxy_nominal_streaming(llm_proxy_env):
    client, _, _, _ = llm_proxy_env

    payload = {
        "model": "qwen-2.5-coder",
        "messages": [{"role": "user", "content": "Dis bonjour"}],
        "stream": True,
    }

    async with client.stream("POST", "/v1/chat/completions", json=payload) as res:
        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]
        lines = []
        async for line in res.aiter_lines():
            clean = line.strip()
            if clean:
                lines.append(clean)

    assert len(lines) == 3
    assert lines[0].startswith("data: ")
    assert "Salut" in lines[0]
    assert "l'ami" in lines[1]
    assert lines[2] == "data: [DONE]"


async def test_llm_proxy_non_streaming(llm_proxy_env):
    client, _, _, _ = llm_proxy_env

    payload = {
        "model": "qwen-2.5-coder",
        "messages": [{"role": "user", "content": "Dis bonjour"}],
        "stream": False,
    }

    res = await client.post("/v1/chat/completions", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["choices"][0]["message"]["content"] == "Reponse complete"


async def test_llm_proxy_client_disconnect_alt_branch(llm_proxy_env):
    _, gateway, cancelled_requests, _ = llm_proxy_env

    # Simulation d'un client déconnecté lors de la réception du second token
    mock_request = AsyncMock(spec=Request)
    call_count = 0

    async def mock_is_disconnected():
        nonlocal call_count
        call_count += 1
        # Au 2ème check, la déconnexion intervient
        return call_count >= 2

    mock_request.is_disconnected = mock_is_disconnected

    body: dict[str, Any] = {
        "model": "qwen-2.5-coder",
        "messages": [{"role": "user", "content": "Test"}],
        "requestId": "req_abort_123",
        "stream": True,
    }

    events = []
    async for chunk in routes_llm_proxy.stream_openai_chat(
        request=mock_request,
        gateway=gateway,
        body=body,
        timeout=10.0,
    ):
        events.append(chunk)

    # Vérification stricte des invariants de 08-sequence-proxy-llm.svg :
    # 1. Le flux s'arrête prématurément
    # 2. data: [DONE] n'est JAMAIS émis
    assert not any("[DONE]" in e for e in events)
    # 3. POST /v1/chat/cancel a été émis vers le worker amont avec le bon requestId
    assert "req_abort_123" in cancelled_requests


async def test_llm_proxy_disabled_in_config(llm_proxy_env):
    client, _, _, store = llm_proxy_env

    # Désactivation du proxy dans config.json
    cfg = StudioConfig(executionMode=ExecutionMode.LOCAL)
    cfg.llmProxy.enabled = False
    await store.write_dict("config.json", cfg.model_dump())

    res = await client.post(
        "/v1/chat/completions",
        json={"model": "test", "messages": [], "stream": False},
    )
    assert res.status_code == 503
    assert "désactivé" in res.json()["detail"].lower()


async def test_llm_proxy_worker_unreachable(llm_proxy_env):
    client, _, _, store = llm_proxy_env

    # Worker inaccessible
    def broken_worker(_request: httpx.Request):
        raise httpx.ConnectError("Connection refused")

    broken_client = httpx.AsyncClient(transport=httpx.MockTransport(broken_worker))
    routes_llm_proxy._gateway = WorkerGateway(store=store, client=broken_client)

    res = await client.post(
        "/v1/chat/completions",
        json={"model": "test", "messages": [], "stream": False},
    )
    assert res.status_code == 503
