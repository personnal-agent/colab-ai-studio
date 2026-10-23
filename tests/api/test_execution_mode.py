"""Tests d'intégration pour la bascule d'exécution Local / Colab (Step 1 de l'Issue #2).

Couvre :
1. GET /api/config retourne la configuration sans fuite de secrets (apiKey masquée).
2. POST /api/config/execution-mode bascule vers "local" et "colab" avec persistance.
3. Valeur invalide d'executionMode renvoie 422.
4. Blocage 409 Conflict si des tâches sont actives (pending ou running) avec liste des IDs.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from app.api import routes_config, routes_crud
from app.main import app
from app.models.domain import ExecutionMode, StudioConfig, TaskStatus
from app.storage.json_store import JSONDocumentStore


@pytest.fixture
async def config_test_env(tmp_path: Path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)

    store = JSONDocumentStore(data_dir)
    routes_crud._json_store = store
    routes_config._json_store = store

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, store, data_dir


async def test_get_config_masks_secret(config_test_env):
    client, store, _ = config_test_env
    initial_config = StudioConfig(executionMode=ExecutionMode.COLAB)
    initial_config.compilerLlm.apiKey = "test-compiler-key-value"
    await store.write_dict("config.json", initial_config.model_dump())

    res = await client.get("/api/config")
    assert res.status_code == 200
    data = res.json()
    assert data["executionMode"] == "colab"
    assert data["compilerLlm"]["apiKey"] is None
    assert data["local"]["workerUrl"] == "http://127.0.0.1:8190"


async def test_post_execution_mode_switch(config_test_env):
    client, store, _ = config_test_env

    # Bascule vers local
    res = await client.post("/api/config/execution-mode", json={"executionMode": "local"})
    assert res.status_code == 200
    assert res.json()["executionMode"] == "local"

    # Vérification persistance disque
    persisted = await store.read_dict("config.json")
    assert persisted["executionMode"] == "local"

    # Bascule vers colab
    res2 = await client.post("/api/config/execution-mode", json={"executionMode": "colab"})
    assert res2.status_code == 200
    assert res2.json()["executionMode"] == "colab"


async def test_post_execution_mode_invalid_value(config_test_env):
    client, _, _ = config_test_env
    res = await client.post("/api/config/execution-mode", json={"executionMode": "invalid_mode"})
    assert res.status_code == 422


async def test_post_execution_mode_conflict_when_tasks_active(config_test_env):
    client, store, _ = config_test_env

    # Injection d'une tâche en cours (running) et une en attente (pending)
    active_tasks = [
        {
            "id": "gen_running_01",
            "status": TaskStatus.RUNNING.value,
            "mediaType": "video",
            "prompt": "Test video in flight",
            "modelName": "Seedance",
        },
        {
            "id": "gen_pending_02",
            "status": TaskStatus.PENDING.value,
            "mediaType": "image",
            "prompt": "Test image queued",
            "modelName": "NoctQ",
        },
        {
            "id": "gen_completed_03",
            "status": TaskStatus.COMPLETED.value,
            "mediaType": "image",
            "prompt": "Finished task",
            "modelName": "NoctQ",
        },
    ]
    await store.write_list("generations.json", active_tasks)

    # Tentative de bascule de mode
    res = await client.post("/api/config/execution-mode", json={"executionMode": "local"})
    assert res.status_code == 409
    body = res.json()
    assert "activeTaskIds" in body
    assert set(body["activeTaskIds"]) == {"gen_running_01", "gen_pending_02"}
    assert "en cours d'exécution" in body["detail"]

    # Vérification que le mode n'a PAS été modifié
    config = await store.read_dict("config.json", default=StudioConfig().model_dump())
    assert config["executionMode"] == "colab"
