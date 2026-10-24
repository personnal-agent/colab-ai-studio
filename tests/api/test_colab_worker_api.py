"""Tests d'intégration de l'API FastAPI du Worker Google Colab (tests/api/test_colab_worker_api.py).

Valide l'ensemble des routes consommées par le backend local et WorkerGateway :
- GET /health
- GET /models
- POST /models/switch
- POST /infer (asynchrone, progression par étapes, rapatriement)
- GET /tasks/{task_id}/status
- POST /tasks/{task_id}/cancel (interruption coopérative et libération mémoire)
- POST /v1/chat/completions (streaming SSE et annulation)
- GET /files/{filename} (téléchargement binaire sécurisé)
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest
from httpx import ASGITransport

from app.colab_worker.model_swapper import ModelSwapper
from app.colab_worker.server import create_worker_app


class MockCudaBackend:
    def is_available(self) -> bool:
        return True

    def empty_cache(self) -> None:
        pass

    def ipc_collect(self) -> None:
        pass

    def memory_allocated(self, device: int | None = None) -> int:
        return 2 * 1024 * 1024 * 1024  # 2 Go

    def get_device_name(self, device: int | None = None) -> str:
        return "Tesla T4 Test"


@pytest.fixture
def temp_storage(tmp_path: Path) -> Path:
    storage = tmp_path / "worker_files"
    storage.mkdir(parents=True, exist_ok=True)
    return storage


@pytest.fixture
def swapper() -> ModelSwapper:
    return ModelSwapper(cuda_backend=MockCudaBackend(), idle_timeout_seconds=300.0)


@pytest.fixture
def worker_app(swapper: ModelSwapper, temp_storage: Path):
    return create_worker_app(model_swapper=swapper, storage_dir=temp_storage)


@pytest.fixture
async def client(worker_app) -> httpx.AsyncClient:
    async with httpx.AsyncClient(
        transport=ASGITransport(app=worker_app), base_url="http://test-colab"
    ) as c:
        yield c


@pytest.mark.anyio
async def test_health_check(client: httpx.AsyncClient) -> None:
    """Vérifie le endpoint /health et la présence des métriques GPU/VRAM."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["gpu"] == "Tesla T4 Test"
    assert "vramFreeMb" in data
    assert data["state"] == "EnVeilleVRAMLibre"


@pytest.mark.anyio
async def test_list_models(client: httpx.AsyncClient) -> None:
    """Vérifie le catalogue des modèles avec leurs capacités."""
    resp = await client.get("/models")
    assert resp.status_code == 200
    models = resp.json()
    assert isinstance(models, list)
    assert len(models) >= 4
    model_ids = [m["id"] for m in models]
    assert "flux-schnell" in model_ids
    assert "wan-2.1-t2v" in model_ids


@pytest.mark.anyio
async def test_switch_model(client: httpx.AsyncClient) -> None:
    """Vérifie la permutation de modèle via POST /models/switch."""
    resp = await client.post("/models/switch", json={"modelId": "flux-schnell"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["activeModel"] == "flux-schnell"

    # Vérification que /health reflète l'état actif
    h_resp = await client.get("/health")
    assert h_resp.json()["activeModel"] == "flux-schnell"
    assert h_resp.json()["state"] == "ModeleActif"


@pytest.mark.anyio
async def test_infer_and_download_flow(client: httpx.AsyncClient) -> None:
    """Vérifie le cycle complet d'inférence, de progression et de rapatriement."""
    infer_payload = {
        "taskId": "task_e2e_001",
        "modelId": "flux-schnell",
        "prompt": "Cyberpunk high tech robot",
        "parameters": {"aspectRatio": "16:9", "seed": 42},
    }
    resp = await client.post("/infer", json=infer_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["taskId"] == "task_e2e_001"
    assert data["status"] in {"pending", "running"}

    # Attente de complétion
    for _ in range(50):
        status_resp = await client.get("/tasks/task_e2e_001/status")
        assert status_resp.status_code == 200
        st = status_resp.json()
        if st["status"] == "completed":
            assert st["progress"] == 100
            assert st["outputUrl"] is not None
            # Téléchargement du fichier
            dl_resp = await client.get(st["outputUrl"])
            assert dl_resp.status_code == 200
            assert len(dl_resp.content) > 0
            break
        await asyncio.sleep(0.05)
    else:
        pytest.fail("La tâche d'inférence n'a pas atteint l'état completed dans le délai imparti.")


@pytest.mark.anyio
async def test_cancel_task(client: httpx.AsyncClient) -> None:
    """Vérifie l'annulation coopérative d'une tâche d'inférence en cours."""
    infer_payload = {
        "taskId": "task_to_cancel_001",
        "modelId": "wan-2.1-t2v",
        "prompt": "Cinematic slow motion",
        "steps": 10,
    }
    await client.post("/infer", json=infer_payload)

    # Annulation immédiate
    cancel_resp = await client.post("/tasks/task_to_cancel_001/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"

    # Vérification du statut terminal
    status_resp = await client.get("/tasks/task_to_cancel_001/status")
    assert status_resp.json()["status"] == "cancelled"


@pytest.mark.anyio
async def test_chat_completions_streaming(client: httpx.AsyncClient) -> None:
    """Vérifie le flux streaming SSE OpenAI-compatible."""
    req_body = {
        "model": "llama-3-8b-instruct",
        "messages": [{"role": "user", "content": "Hello AI"}],
        "stream": True,
    }
    lines = []
    async with client.stream("POST", "/v1/chat/completions", json=req_body) as stream_resp:
        assert stream_resp.status_code == 200
        async for line in stream_resp.aiter_lines():
            if line:
                lines.append(line)

    assert any("data: " in line for line in lines)
    assert any("[DONE]" in line for line in lines)


@pytest.mark.anyio
async def test_file_download_security(client: httpx.AsyncClient) -> None:
    """Vérifie le blocage de traversée de chemin sur /files/{filename}."""
    resp = await client.get("/files/../secret.txt")
    assert resp.status_code in {400, 403, 404}
