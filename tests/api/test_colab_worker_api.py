"""Tests d'intégration de l'API FastAPI du Worker Google Colab."""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest
from httpx import ASGITransport

from app.colab_worker.model_swapper import ModelSwapper
from app.colab_worker.server import create_worker_app


class MockCudaBackend:
    def is_available(self) -> bool: return True
    def empty_cache(self) -> None: pass
    def ipc_collect(self) -> None: pass
    def memory_allocated(self, device: int | None = None) -> int: return 2 * 1024 * 1024 * 1024
    def get_device_name(self, device: int | None = None) -> str: return "Tesla T4 Test"


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
    data = (await client.get("/health")).json()
    assert data["status"] == "ok" and data["gpu"] == "Tesla T4 Test"
    assert "vramFreeMb" in data and data["state"] == "EnVeilleVRAMLibre"


@pytest.mark.anyio
async def test_list_models(client: httpx.AsyncClient) -> None:
    models = (await client.get("/models")).json()
    assert isinstance(models, list) and len(models) >= 4
    ids = [m["id"] for m in models]
    assert "flux-schnell" in ids and "wan-2.1-t2v" in ids


@pytest.mark.anyio
async def test_switch_model(client: httpx.AsyncClient) -> None:
    resp = await client.post("/models/switch", json={"modelId": "flux-schnell"})
    assert resp.status_code == 200 and resp.json()["activeModel"] == "flux-schnell"
    h = (await client.get("/health")).json()
    assert h["activeModel"] == "flux-schnell" and h["state"] == "ModeleActif"


@pytest.mark.anyio
async def test_infer_and_download_flow(client: httpx.AsyncClient) -> None:
    """Vérifie le cycle complet d'inférence, de progression et de rapatriement."""
    params = {"aspectRatio": "16:9"}
    p = {"taskId": "task_01", "modelId": "flux-schnell", "prompt": "Robot", "parameters": params}
    assert (await client.post("/infer", json=p)).status_code == 200
    for _ in range(50):
        st = (await client.get("/tasks/task_01/status")).json()
        if st["status"] == "completed":
            assert st["progress"] == 100 and st["artifactUri"] == "task_01.png"
            dl = await client.get(st["outputUrl"])
            assert dl.status_code == 200 and dl.content.startswith(b"\x89PNG\r\n\x1a\n")
            break
        await asyncio.sleep(0.04)
    else:
        pytest.fail("Inférence non complétée")


@pytest.mark.anyio
async def test_cancel_task(client: httpx.AsyncClient) -> None:
    """Vérifie l'annulation coopérative d'une tâche d'inférence en cours."""
    p = {"taskId": "task_cancel_01", "modelId": "wan-2.1-t2v", "prompt": "Video", "steps": 10}
    await client.post("/infer", json=p)
    cancel = await client.post("/tasks/task_cancel_01/cancel")
    assert cancel.status_code == 200 and cancel.json()["status"] == "cancelled"
    assert (await client.get("/tasks/task_cancel_01/status")).json()["status"] == "cancelled"


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
    assert (await client.get("/files/../secret.txt")).status_code in {400, 403, 404}


@pytest.mark.anyio
async def test_task_id_validation_prevents_path_traversal(client: httpx.AsyncClient) -> None:
    bad = {"taskId": "../victim", "modelId": "flux-schnell", "prompt": "Test"}
    assert (await client.post("/infer", json=bad)).status_code == 422


@pytest.mark.anyio
async def test_worker_secret_authentication(temp_storage: Path) -> None:
    sw = ModelSwapper(cuda_backend=MockCudaBackend())
    secured_app = create_worker_app(
        model_swapper=sw, storage_dir=temp_storage, worker_secret="secret-colab-42"
    )

    async with httpx.AsyncClient(
        transport=ASGITransport(app=secured_app), base_url="http://secured-colab"
    ) as sec_client:
        assert (await sec_client.get("/models")).status_code == 401
        h_bad = {"X-Colab-Secret": "bad"}
        assert (await sec_client.get("/models", headers=h_bad)).status_code == 401
        h_sec = {"X-Colab-Secret": "secret-colab-42"}
        assert (await sec_client.get("/models", headers=h_sec)).status_code == 200
        h_auth = {"Authorization": "Bearer secret-colab-42"}
        assert (await sec_client.get("/models", headers=h_auth)).status_code == 200


@pytest.mark.anyio
async def test_idle_timeout_lifespan_trigger(temp_storage: Path) -> None:
    sw = ModelSwapper(cuda_backend=MockCudaBackend(), idle_timeout_seconds=0.15)
    worker_app = create_worker_app(
        model_swapper=sw, storage_dir=temp_storage, idle_check_interval=0.08,
    )
    t = ASGITransport(app=worker_app)
    ctx = worker_app.router.lifespan_context(worker_app)
    async with ctx, httpx.AsyncClient(transport=t, base_url="http://idle") as c:
        assert (await c.post("/models/switch", json={"modelId": "flux-schnell"})).status_code == 200
        assert sw.state.value == "ModeleActif"
        await asyncio.sleep(0.35)
        h = (await c.get("/health")).json()
        assert h["state"] == "EnVeilleVRAMLibre" and sw.active_model is None


@pytest.mark.anyio
async def test_real_callable_pipeline_execution(temp_storage: Path) -> None:
    """Vérifie l'exécution réelle d'un pipeline, la conversion des kwargs et la purge sur OOM."""
    received_kwargs = {}

    def mock_pipe(**kw):
        received_kwargs.update(kw)
        if kw.get("prompt") == "trigger_oom":
            raise RuntimeError("CUDA out of memory in computation")
        return b"REAL_PNG"

    sw = ModelSwapper(cuda_backend=MockCudaBackend())
    app_real = create_worker_app(
        model_swapper=sw, storage_dir=temp_storage,
        model_loaders={"flux-schnell": lambda _: mock_pipe}, simulation_mode=False,
    )
    transport = ASGITransport(app=app_real)
    async with httpx.AsyncClient(transport=transport, base_url="http://real") as c:
        # 1. Test conversion de paramètres et respect du format (Issue 1)
        resp = await c.post(
            "/infer",
            json={
                "taskId": "real_1", "modelId": "flux-schnell",
                "parameters": {"aspectRatio": "16:9", "resolution": "1024x1024", "duration": "5s"},
            },
        )
        assert resp.status_code == 200
        for _ in range(25):
            st = (await c.get("/tasks/real_1/status")).json()
            if st["status"] == "completed":
                assert (temp_storage / "real_1.png").read_bytes() == b"REAL_PNG"
                assert "aspectRatio" not in received_kwargs and "resolution" not in received_kwargs
                assert received_kwargs.get("width") == 1024 and received_kwargs.get("height") == 576
                break
            await asyncio.sleep(0.04)
        else:
            pytest.fail("Tâche réelle non complétée")

        # 2. Test éviction sur OOM en cours de calcul (Issue 4)
        oom_resp = await c.post(
            "/infer",
            json={"taskId": "oom_task", "modelId": "flux-schnell", "prompt": "trigger_oom"},
        )
        assert oom_resp.status_code == 200
        for _ in range(25):
            st = (await c.get("/tasks/oom_task/status")).json()
            if st["status"] == "failed":
                assert "out of memory" in st["error"].lower()
                assert sw.state.value == "EnVeilleVRAMLibre"
                assert sw.active_model is None
                break
            await asyncio.sleep(0.04)
        else:
            pytest.fail("Tâche OOM non échouée")

