"""Tests unitaires pour TaskOrchestrator (Step 3 du Plan 02).

Vérifie :
1. Cycle de vie nominal d'une tâche (pending -> running -> completed avec rapatriement).
2. Annulation idempotente propageant l'arrêt au worker.
3. Rapatriement et écriture dans MediaFileStore et generations.json.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest

from app.models.domain import (
    GenerationParameters,
    GenerationReferences,
    TaskStatus,
)
from app.services.brand_compiler import BrandContextCompiler
from app.services.task_orchestrator import GenerationPayload, TaskOrchestrator
from app.services.worker_gateway import WorkerGateway
from app.storage.json_store import JSONDocumentStore
from app.storage.media_store import MediaFileStore


@pytest.fixture
def orchestrator_env(tmp_path: Path):
    data_dir = tmp_path / "data"
    outputs_dir = tmp_path / "outputs"
    data_dir.mkdir()
    outputs_dir.mkdir()

    (data_dir / "config.json").write_text(
        '{"executionMode": "local", "local": {"workerUrl": "http://mock-worker"}}',
        encoding="utf-8",
    )

    json_store = JSONDocumentStore(data_dir)
    media_store = MediaFileStore(outputs_dir)
    compiler = BrandContextCompiler()

    def mock_worker(request: httpx.Request):
        if request.url.path == "/infer" and request.method == "POST":
            return httpx.Response(200, json={"taskId": "worker_task_123", "status": "pending"})
        if request.url.path == "/tasks/worker_task_123/status":
            return httpx.Response(
                200,
                json={
                    "taskId": "worker_task_123",
                    "status": "completed",
                    "progress": 100,
                    "outputFilename": "out_video.mp4",
                },
            )
        if request.url.path == "/files/out_video.mp4":
            return httpx.Response(200, content=b"BIN_VIDEO_DATA")
        if request.url.path == "/tasks/worker_task_123/cancel" and request.method == "POST":
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
    return orchestrator, json_store, media_store


async def test_nominal_generation_lifecycle(orchestrator_env):
    orchestrator, json_store, media_store = orchestrator_env

    payload = GenerationPayload(
        mediaType="video",
        prompt="A misty sunrise over the mountains",
        modelId="seedance-2.5-pro",
        modelName="Seedance 2.5",
        parameters=GenerationParameters(
            seed=42, aspectRatio="16:9", resolution="720p", duration="5s"
        ),
        references=GenerationReferences(),
    )

    gen = await orchestrator.submit_generation(payload)
    assert gen.status == TaskStatus.PENDING

    # Attente de la complétion du cycle asynchrone
    await asyncio.sleep(0.1)

    generations = await json_store.read_list("generations.json")
    assert len(generations) == 1
    completed_gen = generations[0]
    assert completed_gen["status"] == TaskStatus.COMPLETED.value
    assert completed_gen["progress"] == 100
    assert completed_gen["filePath"] is not None
    assert Path(completed_gen["filePath"]).read_bytes() == b"BIN_VIDEO_DATA"


async def test_cancel_generation_idempotent(orchestrator_env):
    orchestrator, json_store, _ = orchestrator_env

    payload = GenerationPayload(
        mediaType="video",
        prompt="A misty sunrise",
        modelId="seedance-2.5-pro",
        modelName="Seedance 2.5",
        parameters=GenerationParameters(
            seed=12, aspectRatio="16:9", resolution="720p", duration="5s"
        ),
        references=GenerationReferences(),
    )

    gen = await orchestrator.submit_generation(payload)
    cancelled = await orchestrator.cancel_generation(gen.id)
    assert cancelled.status == TaskStatus.CANCELLED

    # Seconde annulation (idempotence)
    cancelled_again = await orchestrator.cancel_generation(gen.id)
    assert cancelled_again.status == TaskStatus.CANCELLED
