"""Tests unitaires pour WorkerGateway (Step 2 de l'Issue #2).

Vérifie :
1. Résolution dynamique de l'URL du worker actif (colab.tunnelUrl vs local.workerUrl).
2. Erreur 503 explicite si le worker Colab n'est pas configuré.
3. Diagnostic d'injoignabilité du worker avec latence et détails.
4. Relais des routes /models et /models/switch vers le worker actif.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from app.models.domain import ExecutionMode, StudioConfig
from app.services.worker_gateway import WorkerGateway, WorkerGatewayError
from app.storage.json_store import JSONDocumentStore


@pytest.fixture
def gateway_env(tmp_path: Path):
    store = JSONDocumentStore(tmp_path)
    return store


async def test_resolve_active_url_dynamic_switch(gateway_env):
    store = gateway_env
    # 1. Config Colab active
    cfg = StudioConfig(executionMode=ExecutionMode.COLAB)
    cfg.colab.tunnelUrl = "https://colab-active.ngrok-free.app"
    await store.write_dict("config.json", cfg.model_dump())

    gateway = WorkerGateway(store=store)
    mode, url = await gateway.get_active_worker_url()
    assert mode == ExecutionMode.COLAB
    assert url == "https://colab-active.ngrok-free.app"

    # 2. Bascule en mode Local sans redémarrage
    cfg.executionMode = ExecutionMode.LOCAL
    cfg.local.workerUrl = "http://127.0.0.1:8190"
    await store.write_dict("config.json", cfg.model_dump())

    mode2, url2 = await gateway.get_active_worker_url()
    assert mode2 == ExecutionMode.LOCAL
    assert url2 == "http://127.0.0.1:8190"


async def test_colab_unconfigured_raises_explicit_error(gateway_env):
    store = gateway_env
    cfg = StudioConfig(executionMode=ExecutionMode.COLAB)
    cfg.colab.tunnelUrl = ""  # Non configuré
    await store.write_dict("config.json", cfg.model_dump())

    gateway = WorkerGateway(store=store)
    with pytest.raises(WorkerGatewayError, match="Worker Colab non configuré"):
        await gateway.get_active_worker_url()


async def test_worker_health_check_reachable(gateway_env):
    store = gateway_env
    cfg = StudioConfig(executionMode=ExecutionMode.LOCAL)
    cfg.local.workerUrl = "http://mock-worker"
    await store.write_dict("config.json", cfg.model_dump())

    def mock_handler(request: httpx.Request):
        if request.url.path == "/health":
            return httpx.Response(
                200,
                json={"status": "ok", "gpu": "RTX 5000 Ada", "vramFreeMb": 12400},
            )
        return httpx.Response(404)

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    gateway = WorkerGateway(store=store, client=mock_client)

    health = await gateway.check_worker_health()
    assert health["reachable"] is True
    assert health["executionMode"] == "local"
    assert health["gpu"] == "RTX 5000 Ada"
    assert health["vramFreeMb"] == 12400
    assert "latencyMs" in health


async def test_worker_health_check_unreachable(gateway_env):
    store = gateway_env
    cfg = StudioConfig(executionMode=ExecutionMode.LOCAL)
    cfg.local.workerUrl = "http://unreachable-worker:9999"
    await store.write_dict("config.json", cfg.model_dump())

    def failing_handler(request: httpx.Request):
        raise httpx.ConnectError("Connection refused")

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(failing_handler))
    gateway = WorkerGateway(store=store, client=mock_client)

    health = await gateway.check_worker_health()
    assert health["reachable"] is False
    assert health["executionMode"] == "local"
    assert "injoignable" in health["error"].lower()


async def test_list_and_switch_models(gateway_env):
    store = gateway_env
    cfg = StudioConfig(executionMode=ExecutionMode.LOCAL)
    cfg.local.workerUrl = "http://mock-worker"
    await store.write_dict("config.json", cfg.model_dump())

    mock_models = [
        {
            "id": "minimax-h3-heretic",
            "name": "MiniMax-H3 Heretic",
            "mediaType": "video",
            "capabilities": {"maxDuration": "10s"},
        }
    ]

    def mock_handler(request: httpx.Request):
        if request.url.path == "/models" and request.method == "GET":
            return httpx.Response(200, json=mock_models)
        if request.url.path == "/models/switch" and request.method == "POST":
            return httpx.Response(200, json={"switched": True, "activeModel": "minimax-h3-heretic"})
        return httpx.Response(404)

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    gateway = WorkerGateway(store=store, client=mock_client)

    models = await gateway.list_models()
    assert len(models) == 1
    assert models[0]["id"] == "minimax-h3-heretic"

    switch_res = await gateway.switch_model("minimax-h3-heretic")
    assert switch_res["switched"] is True
