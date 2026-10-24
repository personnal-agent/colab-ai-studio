"""Tests pour la commutation du mode d'exécution (Issue #2 Step 1)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes_config import get_config_store
from app.main import app
from app.models.domain import CompilerLlmConfig, ExecutionMode, StudioConfig, TaskStatus
from app.storage.json_store import JSONDocumentStore


@pytest.fixture
def store(tmp_path):
    return JSONDocumentStore(tmp_path)


@pytest.fixture
async def client(store):
    app.dependency_overrides[get_config_store] = lambda: store
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_config_masks_api_key(client, store):
    cfg = StudioConfig(
        executionMode=ExecutionMode.LOCAL, compilerLlm=CompilerLlmConfig(apiKey="mock_dummy_key")
    )
    await store.write_dict("config.json", cfg.model_dump())
    resp = await client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["executionMode"] == "local" and data["compilerLlm"]["apiKey"] == "***"


@pytest.mark.asyncio
async def test_switch_execution_mode_success(client, store):
    cfg = StudioConfig(
        executionMode=ExecutionMode.COLAB, compilerLlm=CompilerLlmConfig(apiKey="mock_dummy_key")
    )
    await store.write_dict("config.json", cfg.model_dump())
    await store.write_list("generations.json", [])
    resp = await client.post(
        "/api/config/execution-mode",
        json={"executionMode": "local"},
        headers={"Origin": "http://localhost:5173"},
    )
    assert resp.status_code == 200
    assert resp.json()["executionMode"] == "local"
    assert resp.json()["compilerLlm"]["apiKey"] == "***"
    saved = await store.read_dict("config.json")
    assert saved["executionMode"] == "local"
    assert saved["compilerLlm"]["apiKey"] == "mock_dummy_key"


@pytest.mark.asyncio
async def test_switch_execution_mode_invalid_value_returns_422(client):
    resp = await client.post(
        "/api/config/execution-mode",
        json={"executionMode": "cloud-cluster"},
        headers={"Origin": "http://localhost:5173"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_switch_execution_mode_conflict_when_active_tasks(client, store):
    await store.write_dict(
        "config.json", StudioConfig(executionMode=ExecutionMode.COLAB).model_dump()
    )
    await store.write_list(
        "generations.json",
        [
            {"id": "gen_1", "status": TaskStatus.COMPLETED.value},
            {"id": "gen_2", "status": TaskStatus.RUNNING.value},
        ],
    )
    resp = await client.post(
        "/api/config/execution-mode",
        json={"executionMode": "local"},
        headers={"Origin": "http://localhost:5173"},
    )
    assert resp.status_code == 409
    data = resp.json()
    assert "tâche" in data["detail"].lower() and "gen_2" in data["activeTaskIds"]
    saved = await store.read_dict("config.json")
    assert saved["executionMode"] == "colab"
