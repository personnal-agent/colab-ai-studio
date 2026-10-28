"""Tests d'intégration d'API pour la validation des contrats d'entrée et /v1/models."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes_generation import get_task_orchestrator
from app.api.routes_models import get_worker_gateway
from app.main import app
from app.models.domain import Generation, GenerationParameters


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_generate_media_rejects_incompatible_reference_input(client):
    """Vérifie le rejet HTTP 422 si les références sont incompatibles avec les capabilities."""
    class FakeGateway:
        async def list_models(self):
            return [
                {
                    "id": "text-only-model",
                    "name": "Text Only Model",
                    "type": "video",
                    "capabilities": {
                        "acceptedInputTypes": ["text"],
                    },
                }
            ]

    app.dependency_overrides[get_worker_gateway] = lambda: FakeGateway()

    payload = {
        "prompt": "Animate character",
        "type": "video",
        "modelId": "text-only-model",
        "parameters": {"seed": 42},
        "references": {
            "imageRefs": ["https://example.com/character.png"],
        },
    }

    resp = await client.post(
        "/api/generate/media",
        json=payload,
        headers={"Origin": "http://localhost:5173"},
    )
    assert resp.status_code == 422
    data = resp.json()
    assert "Incompatibilité média" in data["detail"]


@pytest.mark.asyncio
async def test_generate_media_accepts_compatible_mesh_input(client):
    """Vérifie l'acceptation quand les références (ex. meshRef 3D) sont supportées."""
    class FakeGateway:
        async def list_models(self):
            return [
                {
                    "id": "mesh-3d-model",
                    "name": "Mesh 3D Model",
                    "type": "3d",
                    "capabilities": {
                        "acceptedInputTypes": ["text", "3d", "image"],
                    },
                }
            ]

    class FakeOrchestrator:
        async def submit_generation(self, payload):
            return Generation(
                id="gen_mesh_test_123",
                prompt=payload.prompt,
                modelId=payload.modelId,
                modelName="Mesh 3D Model",
                parameters=payload.parameters or GenerationParameters(seed=42),
            )

    app.dependency_overrides[get_worker_gateway] = lambda: FakeGateway()
    app.dependency_overrides[get_task_orchestrator] = lambda: FakeOrchestrator()

    payload = {
        "prompt": "Generate 3D avatar",
        "type": "3d",
        "modelId": "mesh-3d-model",
        "parameters": {"seed": 42},
        "references": {
            "meshRef": "https://example.com/base_mesh.obj",
        },
    }

    resp = await client.post(
        "/api/generate/media",
        json=payload,
        headers={"Origin": "http://localhost:5173"},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "pending"
    assert data["taskId"] == "gen_mesh_test_123"


@pytest.mark.asyncio
async def test_get_v1_models_endpoint(client):
    """Vérifie le point de terminaison standard /v1/models."""
    class FakeGateway:
        async def list_models(self):
            return [
                {
                    "id": "wan-2.1",
                    "name": "Wan 2.1 Video",
                    "type": "video",
                    "capabilities": {"acceptedInputTypes": ["text", "image"]},
                }
            ]

    app.dependency_overrides[get_worker_gateway] = lambda: FakeGateway()

    resp = await client.get("/v1/models")
    assert resp.status_code == 200
    res = resp.json()
    assert res["object"] == "list"
    ids = [m["id"] for m in res["data"]]
    assert "wan-2.1" in ids
    assert "hilo-agent" in ids
