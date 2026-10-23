"""Tests d'intégration pour GET /api/health enrichi et routes modèles (Step 2 Issue #2).

Couvre :
1. GET /api/health retourne le diagnostic du worker actif.
2. GET /api/models relaie vers le worker actif sans hardcoding.
3. POST /api/models/switch ordonne le changement au worker actif.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from app.api import routes_config, routes_crud, routes_models
from app.main import app
from app.models.domain import ExecutionMode, StudioConfig
from app.services.worker_gateway import WorkerGateway
from app.storage.json_store import JSONDocumentStore


@pytest.fixture
async def models_test_env(tmp_path: Path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)

    store = JSONDocumentStore(data_dir)
    routes_crud._json_store = store
    routes_config._json_store = store

    cfg = StudioConfig(executionMode=ExecutionMode.LOCAL)
    cfg.local.workerUrl = "http://mock-worker"
    await store.write_dict("config.json", cfg.model_dump())

    mock_models = [
        {
            "id": "noctq-v4-image",
            "name": "NoctQ V4 Image",
            "mediaType": "image",
            "capabilities": {"aspectRatios": ["16:9", "9:16", "1:1"]},
        }
    ]

    def mock_worker(request: httpx.Request):
        if request.url.path == "/health":
            return httpx.Response(
                200,
                json={"status": "ok", "gpu": "RTX 5000 Ada", "vramFreeMb": 14200},
            )
        if request.url.path == "/models" and request.method == "GET":
            return httpx.Response(200, json=mock_models)
        if request.url.path == "/models/switch" and request.method == "POST":
            return httpx.Response(200, json={"switched": True, "activeModel": "noctq-v4-image"})
        return httpx.Response(404)

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_worker))
    gateway = WorkerGateway(store=store, client=mock_client)
    routes_models._gateway = gateway

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, store, gateway


async def test_health_includes_worker_diagnostic(models_test_env):
    client, _, gateway = models_test_env
    # Injecte la passerelle dans app.state ou router
    routes_models._gateway = gateway
    res = await client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "healthy"
    assert "worker" in body
    assert body["worker"]["reachable"] is True
    assert body["worker"]["gpu"] == "RTX 5000 Ada"


async def test_get_models_from_worker(models_test_env):
    client, _, _ = models_test_env
    res = await client.get("/api/models")
    assert res.status_code == 200
    models = res.json()
    assert len(models) == 1
    assert models[0]["id"] == "noctq-v4-image"


async def test_switch_model_on_worker(models_test_env):
    client, _, _ = models_test_env
    res = await client.post("/api/models/switch", json={"modelId": "noctq-v4-image"})
    assert res.status_code == 200
    assert res.json()["switched"] is True
