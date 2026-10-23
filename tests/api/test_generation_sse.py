"""Tests d'intégration API pour la génération asynchrone et le flux SSE (Step 3 Plan 02).

Couvre :
1. POST /api/generate/media lance la tâche et renvoie la génération.
2. GET /api/tasks/{task_id}/status streame les événements SSE de progression.
3. POST /api/tasks/{task_id}/cancel annule la tâche.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from app.api import routes_config, routes_crud, routes_generation
from app.main import app
from app.models.domain import ExecutionMode, StudioConfig
from app.services.brand_compiler import BrandContextCompiler
from app.services.task_orchestrator import TaskOrchestrator
from app.services.worker_gateway import WorkerGateway
from app.storage.json_store import JSONDocumentStore
from app.storage.media_store import MediaFileStore


@pytest.fixture
async def generation_api_env(tmp_path: Path):
    data_dir = tmp_path / "data"
    outputs_dir = tmp_path / "outputs"
    data_dir.mkdir()
    outputs_dir.mkdir()

    json_store = JSONDocumentStore(data_dir)
    media_store = MediaFileStore(outputs_dir)
    compiler = BrandContextCompiler()

    routes_crud._json_store = json_store
    routes_config._json_store = json_store
    routes_generation._json_store = json_store

    cfg = StudioConfig(executionMode=ExecutionMode.LOCAL)
    cfg.local.workerUrl = "http://mock-worker"
    await json_store.write_dict("config.json", cfg.model_dump())

    def mock_worker(request: httpx.Request):
        if request.url.path == "/infer" and request.method == "POST":
            return httpx.Response(200, json={"taskId": "worker_task_999", "status": "pending"})
        if request.url.path == "/tasks/worker_task_999/status":
            return httpx.Response(
                200,
                json={
                    "taskId": "worker_task_999",
                    "status": "completed",
                    "progress": 100,
                    "outputFilename": "out.mp4",
                },
            )
        if request.url.path == "/files/out.mp4":
            return httpx.Response(200, content=b"VIDEO_DATA")
        if request.url.path == "/tasks/worker_task_999/cancel":
            return httpx.Response(200, json={"status": "cancelled"})
        return httpx.Response(404)

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_worker))
    gateway = WorkerGateway(store=json_store, client=mock_client)

    orchestrator = TaskOrchestrator(
        json_store=json_store,
        media_store=media_store,
        gateway=gateway,
        brand_compiler=compiler,
        poll_interval=0.01,
        timeout=5.0,
    )
    routes_generation._orchestrator = orchestrator

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, orchestrator


async def test_api_generate_media_and_cancel(generation_api_env):
    client, _ = generation_api_env

    payload = {
        "mediaType": "video",
        "prompt": "Sunset over river",
        "modelId": "seedance-2.5",
        "modelName": "Seedance",
        "parameters": {
            "seed": 100,
            "aspectRatio": "16:9",
            "resolution": "720p",
            "duration": "5s",
        },
    }

    res = await client.post("/api/generate/media", json=payload)
    assert res.status_code == 201
    gen_id = res.json()["id"]

    # Annulation
    res_cancel = await client.post(f"/api/tasks/{gen_id}/cancel")
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "cancelled"


async def test_api_task_status_not_found(generation_api_env):
    client, _ = generation_api_env
    res = await client.get("/api/tasks/non_existent_task_id/status")
    assert res.status_code == 404


async def test_api_sse_streaming(generation_api_env):
    client, _ = generation_api_env

    payload = {
        "mediaType": "video",
        "prompt": "Misty mountains",
        "modelId": "seedance-2.5",
        "modelName": "Seedance",
        "parameters": {
            "seed": 42,
            "aspectRatio": "16:9",
            "resolution": "720p",
            "duration": "5s",
        },
    }
    res = await client.post("/api/generate/media", json=payload)
    assert res.status_code == 201
    gen_id = res.json()["id"]

    events = []
    async with client.stream("GET", f"/api/tasks/{gen_id}/status") as sse_res:
        assert sse_res.status_code == 200
        assert "text/event-stream" in sse_res.headers["content-type"]
        async for line in sse_res.aiter_lines():
            if line.startswith("data: "):
                data = json.loads(line[6:])
                events.append(data)
                if data.get("status") in {"completed", "failed", "cancelled"}:
                    break

    assert len(events) >= 1
    assert any(ev.get("status") in {"pending", "running", "completed"} for ev in events)
