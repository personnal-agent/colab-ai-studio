"""Tests d'intégration d'API pour /api/health et /api/models."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes_models import get_worker_gateway
from app.main import app
from app.services.worker_gateway import WorkerNotConfiguredError, WorkerUnavailableError


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_endpoint_includes_worker_status(client):
    class Fake:
        async def health(self):
            return {
                "executionMode": "local",
                "worker": {
                    "reachable": True,
                    "latencyMs": 12.5,
                    "gpu": "RTX 3080",
                    "vramFreeMb": 8192,
                    "error": None,
                },
            }

    app.dependency_overrides[get_worker_gateway] = lambda: Fake()
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy" and data["worker"]["gpu"] == "RTX 3080"


@pytest.mark.asyncio
async def test_get_models_success(client):
    class Fake:
        async def list_models(self):
            return [{"id": "wan2.1-t2v-14b", "name": "Wan 2.1 14B", "type": "video"}]

    app.dependency_overrides[get_worker_gateway] = lambda: Fake()
    resp = await client.get("/api/models")
    assert resp.status_code == 200 and resp.json()[0]["id"] == "wan2.1-t2v-14b"


@pytest.mark.asyncio
async def test_get_models_worker_not_configured_returns_503(client):
    class Fake:
        async def list_models(self):
            raise WorkerNotConfiguredError("Worker Colab non configuré")

    app.dependency_overrides[get_worker_gateway] = lambda: Fake()
    resp = await client.get("/api/models")
    assert resp.status_code == 503 and "Worker Colab non configuré" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_switch_model_success_and_failure(client):
    class Fake:
        async def switch_model(self, m):
            if m == "unknown":
                raise WorkerUnavailableError("Modèle non supporté")
            return {"status": "switched", "activeModel": m}

    app.dependency_overrides[get_worker_gateway] = lambda: Fake()
    r1 = await client.post("/api/models/switch", json={"modelId": "wan2.1-t2v-14b"})
    assert r1.status_code == 200 and r1.json()["activeModel"] == "wan2.1-t2v-14b"

    r2 = await client.post("/api/models/switch", json={"modelId": "unknown"})
    assert r2.status_code == 503 and "Modèle non supporté" in r2.json()["detail"]

    r3 = await client.post(
        "/api/models/switch",
        json={"modelId": "wan2.1-t2v-14b"},
        headers={"Sec-Fetch-Site": "cross-site"},
    )
    assert r3.status_code == 403
