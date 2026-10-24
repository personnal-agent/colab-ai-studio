"""Tests unitaires pour TaskOrchestrator (app/services/task_orchestrator.py)."""

from __future__ import annotations

import asyncio

import pytest

from app.models.domain import (
    Asset,
    BrandKit,
    Color,
    Generation,
    GenerationParameters,
    GenerationReferences,
    TaskStatus,
)
from app.services.brand_compiler import BrandContextCompiler
from app.services.task_orchestrator import GenerationCreateRequest, TaskOrchestrator
from app.storage.json_store import JSONDocumentStore
from app.storage.media_store import MediaFileStore


class MockWorkerGateway:
    def __init__(self):
        self.inferred_specs, self.cancelled_tasks = [], []
        self.default_status = {"status": "completed", "progress": 100, "artifactUri": "output.mp4"}

    async def get_active_worker_url(self):
        return "local", "http://127.0.0.1:8190"

    async def list_models(self):
        return []

    async def infer(self, spec: dict, *args, **kwargs):
        self.inferred_specs.append(spec)
        return {"taskId": spec["taskId"], "status": "queued"}

    async def get_task_status(self, task_id: str, *args, **kwargs):
        return self.default_status

    async def cancel_task(self, task_id: str, *args, **kwargs):
        self.cancelled_tasks.append(task_id)
        return {"status": "cancelled", "taskId": task_id}

    async def download_file(self, path: str, *args, **kwargs):
        return b"MOCK_MP4_BINARY_DATA"

    async def aclose(self):
        pass


@pytest.fixture
def stores(tmp_path):
    d, o = tmp_path / "data", tmp_path / "outputs"
    d.mkdir()
    o.mkdir()
    return JSONDocumentStore(d), MediaFileStore(o)


@pytest.fixture
def sample_kit():
    return BrandKit(
        id="bk_neon",
        name="Neon Corp",
        overview="Cyberpunk aesthetic",
        colors=[Color(hex="#00FFCC", label="Cyan")],
        referenceImages=[Asset(id="ref1", filePath="/data/assets/neon.jpg")],
    )


@pytest.mark.asyncio
async def test_submit_generation_compiles_brand_kit_and_persists(stores, sample_kit):
    js, ms = stores
    await js.write_list("brand_kits.json", [sample_kit.model_dump()])
    await js.write_list("generations.json", [])

    worker = MockWorkerGateway()
    orch = TaskOrchestrator(js, ms, worker, BrandContextCompiler(), poll_interval=0.01)

    req = GenerationCreateRequest(
        prompt="A neon car",
        modelId="wan2.1-t2v-14b",
        type="video",
        brandKitId="bk_neon",
        parameters=GenerationParameters(seed=42),
        references=GenerationReferences(imageRefs=["data/assets/user_ref.png"]),
    )

    gen = await orch.submit_generation(req)
    assert gen.id.startswith("gen_") and "[Brand Identity: Neon Corp]" in gen.compiledPrompt
    await orch.wait_task(gen.id, timeout=2.0)

    assert len(worker.inferred_specs) == 1 and worker.inferred_specs[0]["taskId"] == gen.id
    saved = next(g for g in await js.read_list("generations.json") if g["id"] == gen.id)
    assert saved["status"] == TaskStatus.COMPLETED.value and saved["filePath"] is not None


@pytest.mark.asyncio
async def test_cancel_running_task_is_idempotent(stores):
    js, ms = stores
    await js.write_list("generations.json", [])
    worker = MockWorkerGateway()
    worker.default_status = {"status": "running", "progress": 40}

    orch = TaskOrchestrator(js, ms, worker, BrandContextCompiler(), poll_interval=0.05)
    req = GenerationCreateRequest(prompt="Long run", modelId="wan2.1-t2v-14b")
    gen = await orch.submit_generation(req)

    await asyncio.sleep(0.02)
    assert (await orch.cancel_task(gen.id))["status"] == "cancelled"
    assert (await orch.cancel_task(gen.id))["status"] == "cancelled"
    assert gen.id in worker.cancelled_tasks

    saved = next(g for g in await js.read_list("generations.json") if g["id"] == gen.id)
    assert saved["status"] == TaskStatus.CANCELLED.value


@pytest.mark.asyncio
async def test_cancel_already_completed_task_does_not_modify(stores):
    js, ms = stores
    await js.write_list(
        "generations.json", [{"id": "gen_done", "status": TaskStatus.COMPLETED.value}]
    )
    worker = MockWorkerGateway()
    orch = TaskOrchestrator(js, ms, worker, BrandContextCompiler())

    res = await orch.cancel_task("gen_done")
    assert res["status"] == TaskStatus.COMPLETED.value and "gen_done" not in worker.cancelled_tasks


@pytest.mark.asyncio
async def test_cancel_already_failed_task_does_not_modify(stores):
    js, ms = stores
    await js.write_list(
        "generations.json", [{"id": "gen_failed", "status": TaskStatus.FAILED.value}]
    )
    worker = MockWorkerGateway()
    orch = TaskOrchestrator(js, ms, worker, BrandContextCompiler())

    res = await orch.cancel_task("gen_failed")
    assert res["status"] == TaskStatus.FAILED.value and "gen_failed" not in worker.cancelled_tasks


@pytest.mark.asyncio
async def test_task_failure_on_worker_error(stores):
    js, ms = stores
    await js.write_list("generations.json", [])
    worker = MockWorkerGateway()
    worker.default_status = {"status": "failed", "error": "CUDA out of memory"}

    orch = TaskOrchestrator(js, ms, worker, BrandContextCompiler(), poll_interval=0.01)
    gen = await orch.submit_generation(
        GenerationCreateRequest(prompt="Fail", modelId="wan2.1-t2v-14b")
    )
    await orch.wait_task(gen.id, timeout=2.0)

    saved = next(g for g in await js.read_list("generations.json") if g["id"] == gen.id)
    assert (
        saved["status"] == TaskStatus.FAILED.value and "CUDA out of memory" in saved["errorMessage"]
    )


@pytest.mark.asyncio
async def test_terminal_state_sanctuary(stores):
    js, ms = stores
    gen_dummy = Generation(
        id="gen_term_1",
        status=TaskStatus.CANCELLED,
        prompt="p",
        modelId="m",
        modelName="M",
        parameters=GenerationParameters(seed=0),
        errorMessage="Cancelled",
    )
    await js.write_list("generations.json", [gen_dummy.model_dump()])
    orch = TaskOrchestrator(js, ms, MockWorkerGateway(), BrandContextCompiler())

    # Tentative d'écraser vers COMPLETED
    updated = await orch._update_generation(
        "gen_term_1", status=TaskStatus.COMPLETED.value, progress=100
    )
    assert updated.status == TaskStatus.CANCELLED

    saved = next(g for g in await js.read_list("generations.json") if g["id"] == "gen_term_1")
    assert saved["status"] == TaskStatus.CANCELLED.value


@pytest.mark.asyncio
async def test_text_only_model_clears_image_refs(stores):
    js, ms = stores
    await js.write_list("generations.json", [])
    orch = TaskOrchestrator(js, ms, MockWorkerGateway(), BrandContextCompiler())

    req = GenerationCreateRequest(
        prompt="Write a poem",
        modelId="qwen2.5-7b-instruct",
        type="text",
        references=GenerationReferences(imageRefs=["data/assets/dummy.png"]),
    )
    gen = await orch.submit_generation(req)
    assert gen.references.imageRefs == []


@pytest.mark.asyncio
async def test_subscribe_task_orphaned_exits_cleanly(stores):
    js, ms = stores
    gen = Generation(
        id="gen_orphan_test",
        status=TaskStatus.RUNNING,
        prompt="p",
        modelId="m",
        modelName="M",
        parameters=GenerationParameters(seed=0),
    )
    await js.write_list("generations.json", [gen.model_dump()])
    orch = TaskOrchestrator(js, ms, MockWorkerGateway(), BrandContextCompiler())

    events = []
    async for evt in orch.subscribe_task("gen_orphan_test", keepalive_timeout=0.05):
        events.append(evt)
    assert len(events) == 1
    assert "running" in events[0]


@pytest.mark.asyncio
async def test_subscribe_task_drains_queued_final_event_when_inactive(stores):
    js, ms = stores
    gen = Generation(
        id="gen_queued_final",
        status=TaskStatus.RUNNING,
        prompt="p",
        modelId="m",
        modelName="M",
        parameters=GenerationParameters(seed=0),
    )
    await js.write_list("generations.json", [gen.model_dump()])
    orch = TaskOrchestrator(js, ms, MockWorkerGateway(), BrandContextCompiler())

    gen_sub = orch.subscribe_task("gen_queued_final", keepalive_timeout=0.05)
    first_evt = await gen_sub.__anext__()
    assert "running" in first_evt

    assert "gen_queued_final" in orch._listeners
    q = orch._listeners["gen_queued_final"][0]
    await q.put({"type": "completed", "status": "completed", "filePath": "assets/final.png"})

    second_evt = await gen_sub.__anext__()
    assert "completed" in second_evt
    assert "assets/final.png" in second_evt

    with pytest.raises(StopAsyncIteration):
        await gen_sub.__anext__()
