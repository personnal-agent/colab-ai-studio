"""Tests d'intégration de l'API du Worker Local (Step 3 de l'Issue #2).

Vérifie :
1. GET /health (statut, GPU, VRAM libre).
2. GET /models (lecture dynamique du manifeste de modèles locaux).
3. POST /models/switch (changement de modèle actif avec vérification).
4. POST /infer (lancement asynchrone d'une tâche).
5. GET /tasks/{task_id}/status (suivi de progression).
6. POST /tasks/{task_id}/cancel (annulation d'une tâche).
7. GET /files/{filename} (téléchargement du binaire produit).
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from app.local_worker.server import create_worker_app


@pytest.fixture
def worker_client(tmp_path: Path):
    manifest_file = tmp_path / "manifest.json"
    manifest_data = [
        {
            "id": "test-video-model",
            "name": "Test Video Model",
            "mediaType": "video",
            "backend": "mock",
            "capabilities": {"aspectRatios": ["16:9"]},
        }
    ]
    manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")

    files_dir = tmp_path / "files"
    files_dir.mkdir(parents=True)
    sample_file = files_dir / "sample_output.mp4"
    sample_file.write_bytes(b"TEST_MP4_BYTES")

    app = create_worker_app(
        manifest_path=manifest_file,
        files_dir=files_dir,
        gpu_name_override="NVIDIA RTX 5000 Ada",
        vram_free_override=13500,
    )

    transport = httpx.ASGITransport(app=app)
    client = httpx.AsyncClient(transport=transport, base_url="http://local-worker")
    return client, files_dir


async def test_worker_health(worker_client):
    client, _ = worker_client
    res = await client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["gpu"] == "NVIDIA RTX 5000 Ada"
    assert body["vramFreeMb"] == 13500


async def test_worker_list_and_switch_models(worker_client):
    client, _ = worker_client
    # Liste
    res = await client.get("/models")
    assert res.status_code == 200
    models = res.json()
    assert len(models) == 1
    assert models[0]["id"] == "test-video-model"

    # Switch valide
    res_switch = await client.post("/models/switch", json={"modelId": "test-video-model"})
    assert res_switch.status_code == 200
    assert res_switch.json()["switched"] is True
    assert res_switch.json()["activeModel"] == "test-video-model"

    # Switch invalide
    res_bad = await client.post("/models/switch", json={"modelId": "non-existent"})
    assert res_bad.status_code == 404


async def test_worker_infer_and_task_lifecycle(worker_client):
    client, _ = worker_client
    infer_payload = {
        "modelId": "test-video-model",
        "prompt": "Cinematic shot",
        "parameters": {"aspectRatio": "16:9"},
    }
    res = await client.post("/infer", json=infer_payload)
    assert res.status_code == 200
    task_id = res.json()["taskId"]
    assert task_id.startswith("task_")

    # Status
    res_status = await client.get(f"/tasks/{task_id}/status")
    assert res_status.status_code == 200
    assert res_status.json()["taskId"] == task_id
    assert res_status.json()["status"] in {"pending", "running", "completed"}

    # Annulation
    res_cancel = await client.post(f"/tasks/{task_id}/cancel")
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "cancelled"


async def test_worker_download_file(worker_client):
    client, _ = worker_client
    res = await client.get("/files/sample_output.mp4")
    assert res.status_code == 200
    assert res.content == b"TEST_MP4_BYTES"

    # Fichier inexistant
    res_404 = await client.get("/files/missing.mp4")
    assert res_404.status_code == 404


async def test_worker_chat_completions_sync_and_stream(worker_client):
    client, _ = worker_client

    # Synchrone
    res_sync = await client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Hello"}], "stream": False},
    )
    assert res_sync.status_code == 200
    data = res_sync.json()
    assert "choices" in data
    assert data["choices"][0]["message"]["content"] == "Bonjour ! Je suis le modèle local."

    # Streaming
    async with client.stream(
        "POST",
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Hello"}], "stream": True},
    ) as res_stream:
        assert res_stream.status_code == 200
        lines = []
        async for line in res_stream.aiter_lines():
            clean = line.strip()
            if clean:
                lines.append(clean)

    assert len(lines) > 2
    assert lines[-1] == "data: [DONE]"

    # Annulation
    res_cancel = await client.post("/v1/chat/cancel", json={"requestId": "req_123"})
    assert res_cancel.status_code == 200
    assert res_cancel.json()["cancelled"] is True
