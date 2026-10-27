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
    def is_available(self) -> bool:
        return True

    def empty_cache(self) -> None:
        pass

    def ipc_collect(self) -> None:
        pass

    def memory_allocated(self, device: int | None = None) -> int:
        return 2 * 1024 * 1024 * 1024

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
    """Vérifie le flux streaming SSE OpenAI-compatible et l'annulation."""
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

    # Annulation anticipée du flux de chat
    req_c = {**req_body, "requestId": "req_cancel_test"}
    await client.post("/v1/chat/cancel", json={"requestId": "req_cancel_test"})
    c_lines = []
    async with client.stream("POST", "/v1/chat/completions", json=req_c) as s_resp:
        assert s_resp.status_code == 200
        async for line in s_resp.aiter_lines():
            if line:
                c_lines.append(line)
    assert not c_lines

    # Interruption mi-flux pour vérifier la libération saine du verrou
    async with client.stream("POST", "/v1/chat/completions", json=req_body) as s_resp:
        async for line in s_resp.aiter_lines():
            if line:
                break
    assert (await client.get("/health")).json()["status"] == "ok"


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
    app_sec = create_worker_app(model_swapper=sw, storage_dir=temp_storage, worker_secret="sec42")
    async with httpx.AsyncClient(transport=ASGITransport(app=app_sec), base_url="http://sec") as sc:
        assert (await sc.get("/models")).status_code == 401
        assert (await sc.get("/models", headers={"X-Colab-Secret": "bad"})).status_code == 401
        assert (await sc.get("/models", headers={"X-Colab-Secret": "sec42"})).status_code == 200
        h_auth = {"Authorization": "Bearer sec42"}
        assert (await sc.get("/models", headers=h_auth)).status_code == 200


@pytest.mark.anyio
async def test_idle_timeout_lifespan_trigger(temp_storage: Path) -> None:
    sw = ModelSwapper(cuda_backend=MockCudaBackend(), idle_timeout_seconds=0.15)
    worker_app = create_worker_app(
        model_swapper=sw,
        storage_dir=temp_storage,
        idle_check_interval=0.08,
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
        model_swapper=sw,
        storage_dir=temp_storage,
        model_loaders={"flux-schnell": lambda _: mock_pipe},
        simulation_mode=False,
    )
    transport = ASGITransport(app=app_real)
    async with httpx.AsyncClient(transport=transport, base_url="http://real") as c:
        # 1. Test conversion de paramètres et respect du format (Issue 1)
        p_real = {
            "taskId": "real_1",
            "modelId": "flux-schnell",
            "parameters": {"aspectRatio": "16:9", "resolution": "1024x1024"},
        }
        assert (await c.post("/infer", json=p_real)).status_code == 200
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
        p_oom = {"taskId": "oom_task", "modelId": "flux-schnell", "prompt": "trigger_oom"}
        assert (await c.post("/infer", json=p_oom)).status_code == 200
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


@pytest.mark.anyio
async def test_chat_concurrency_and_gpu_lock_retention_on_cancel(temp_storage: Path) -> None:
    """Vérifie que gpu_lock reste acquis tant que le calcul du thread n'est pas terminé."""
    import contextlib
    import threading

    compute_started = threading.Event()
    finish_compute = threading.Event()
    compute_ended = threading.Event()
    poke_stream = threading.Event()
    cleanup_entered = threading.Event()

    class FakeStreamer:
        """Streamer de test synchronisé avec les étapes d'annulation."""

        def __init__(self, tok, skip_prompt=True, skip_special_tokens=True):
            self.tok = tok
            self.ended = False

        def __iter__(self):
            return self

        def __next__(self):
            while not poke_stream.wait(0.01):
                if finish_compute.is_set():
                    raise StopIteration
            poke_stream.clear()
            return "x"

        def end(self):
            self.ended = True
            cleanup_entered.set()

    class FakeTokenizer:
        TextIteratorStreamer = FakeStreamer

    class SlowChatModel:
        def __init__(self):
            self.tokenizer = FakeTokenizer()

        def __call__(self, prompt, **kwargs):
            compute_started.set()
            finish_compute.wait(timeout=5.0)
            compute_ended.set()
            streamer = kwargs.get("streamer")
            if streamer:
                streamer.end()

    sw = ModelSwapper(cuda_backend=MockCudaBackend())
    app = create_worker_app(
        model_swapper=sw,
        storage_dir=temp_storage,
        model_loaders={"qwen-2.5-7b": lambda _: SlowChatModel()},
        simulation_mode=False,
    )
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        req = {
            "model": "qwen-2.5-7b",
            "messages": [{"role": "user", "content": "Hello slow model"}],
            "stream": True,
            "requestId": "req_slow_1",
        }

        async def _run_stream():
            async with c.stream("POST", "/v1/chat/completions", json=req) as resp:
                async for _ in resp.aiter_lines():
                    pass

        stream_task = asyncio.create_task(_run_stream())

        for _ in range(50):
            if compute_started.is_set():
                break
            await asyncio.sleep(0.04)
        assert compute_started.is_set()

        cancel_resp = await c.post("/v1/chat/cancel", json={"requestId": "req_slow_1"})
        assert cancel_resp.status_code == 200

        poke_stream.set()
        assert await asyncio.to_thread(cleanup_entered.wait, 4.0)

        switch_task = asyncio.create_task(
            c.post("/models/switch", json={"modelId": "flux-schnell"})
        )
        await asyncio.sleep(0.1)

        assert not switch_task.done()
        assert not compute_ended.is_set()

        finish_compute.set()
        poke_stream.set()

        switch_res = await asyncio.wait_for(switch_task, timeout=4.0)
        assert switch_res.status_code == 200
        assert compute_ended.is_set()

        with contextlib.suppress(Exception):
            await stream_task


@pytest.mark.anyio
async def test_chat_no_tokenizer_cancellation_and_lock(
    temp_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Vérifie l'annulation et la rétention du verrou pour un modèle sans tokenizer."""
    import contextlib
    import threading

    compute_started = threading.Event()
    finish_compute = threading.Event()
    compute_ended = threading.Event()
    cleanup_entered = threading.Event()
    real_thread = threading.Thread

    class ObservedThread(real_thread):
        def __init__(self, *args, **kwargs):
            target = kwargs.get("target")
            self.observes_no_tok_cleanup = getattr(target, "__name__", "") == "_no_tok_worker"
            super().__init__(*args, **kwargs)

        def join(self, *args, **kwargs):
            if self.observes_no_tok_cleanup:
                cleanup_entered.set()
            return super().join(*args, **kwargs)

    monkeypatch.setattr(threading, "Thread", ObservedThread)

    class SlowCallableNoTok:
        def __call__(self, prompt, **kwargs):
            compute_started.set()
            finish_compute.wait(timeout=5.0)
            compute_ended.set()
            return [{"generated_text": prompt + " réponse finie"}]

    sw = ModelSwapper(cuda_backend=MockCudaBackend())
    app = create_worker_app(
        model_swapper=sw,
        storage_dir=temp_storage,
        model_loaders={"qwen-2.5-7b": lambda _: SlowCallableNoTok()},
        simulation_mode=False,
    )
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        req = {
            "model": "qwen-2.5-7b",
            "messages": [{"role": "user", "content": "Hello slow callable"}],
            "stream": True,
            "requestId": "req_no_tok_1",
        }

        async def _run_stream():
            async with c.stream("POST", "/v1/chat/completions", json=req) as resp:
                async for _ in resp.aiter_lines():
                    pass

        stream_task = asyncio.create_task(_run_stream())

        for _ in range(50):
            if compute_started.is_set():
                break
            await asyncio.sleep(0.04)
        assert compute_started.is_set()

        cancel_resp = await c.post("/v1/chat/cancel", json={"requestId": "req_no_tok_1"})
        assert cancel_resp.status_code == 200

        assert await asyncio.to_thread(cleanup_entered.wait, 4.0)

        switch_task = asyncio.create_task(
            c.post("/models/switch", json={"modelId": "flux-schnell"})
        )
        await asyncio.sleep(0.1)

        assert not switch_task.done()
        assert not compute_ended.is_set()

        finish_compute.set()

        switch_res = await asyncio.wait_for(switch_task, timeout=4.0)
        assert switch_res.status_code == 200
        assert compute_ended.is_set()

        with contextlib.suppress(Exception):
            await stream_task


@pytest.mark.anyio
async def test_chat_no_tokenizer_successful_response(temp_storage: Path) -> None:
    """Vérifie qu'un modèle sans tokenizer génère et diffuse correctement sa réponse."""
    import json

    class SimpleNoTokModel:
        def __call__(self, prompt, **kwargs):
            return [{"generated_text": prompt + " Réponse complète sans tokenizer."}]

    sw = ModelSwapper(cuda_backend=MockCudaBackend())
    app = create_worker_app(
        model_swapper=sw,
        storage_dir=temp_storage,
        model_loaders={"qwen-2.5-7b": lambda _: SimpleNoTokModel()},
        simulation_mode=False,
    )
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        req = {
            "model": "qwen-2.5-7b",
            "messages": [{"role": "user", "content": "Question"}],
            "stream": True,
            "requestId": "req_notok_success",
        }
        collected: list[str] = []
        saw_done = False
        async with c.stream("POST", "/v1/chat/completions", json=req) as resp:
            assert resp.status_code == 200
            async for line in resp.aiter_lines():
                if line == "data: [DONE]":
                    saw_done = True
                elif line.startswith("data: "):
                    payload = json.loads(line[6:])
                    delta = payload["choices"][0]["delta"].get("content", "")
                    collected.append(delta)

        assert saw_done is True
        full_text = "".join(collected)
        assert "Réponse complète sans tokenizer." in full_text


@pytest.mark.parametrize("anyio_backend", ["asyncio"])
@pytest.mark.anyio
async def test_chat_no_tokenizer_asyncio_task_cancellation(
    temp_storage: Path, anyio_backend: str
) -> None:
    """Vérifie que l'annulation asyncio de la tâche de flux signale bien l'arrêt au modèle."""
    import contextlib
    import threading
    import time

    compute_started = threading.Event()
    stopping_criteria_seen = threading.Event()

    class StoppableNoTokModel:
        def __call__(self, prompt, **kwargs):
            compute_started.set()
            crits = kwargs.get("stopping_criteria") or []
            # Simule une boucle de génération surveillant stopping_criteria
            for _ in range(100):
                if any(c(None, None) for c in crits):
                    stopping_criteria_seen.set()
                    return [{"generated_text": prompt + " [Interrompu]"}]
                time.sleep(0.02)
            return [{"generated_text": prompt + " [Fini]"}]

    sw = ModelSwapper(cuda_backend=MockCudaBackend())
    app = create_worker_app(
        model_swapper=sw,
        storage_dir=temp_storage,
        model_loaders={"qwen-2.5-7b": lambda _: StoppableNoTokModel()},
        simulation_mode=False,
    )
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        req = {
            "model": "qwen-2.5-7b",
            "messages": [{"role": "user", "content": "Question"}],
            "stream": True,
            "requestId": "req_notok_asyncio_cancel",
        }

        async def _run_stream():
            async with c.stream("POST", "/v1/chat/completions", json=req) as resp:
                async for _ in resp.aiter_lines():
                    pass

        stream_task = asyncio.create_task(_run_stream())

        # Attendre que le modèle démarre son calcul
        for _ in range(50):
            if compute_started.is_set():
                break
            await asyncio.sleep(0.02)
        assert compute_started.is_set()

        # Annuler la tâche asynchrone de streaming (lève asyncio.CancelledError dans le generator)
        stream_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await stream_task

        # Vérifier que le critère d'arrêt a bien été prévenu grâce à active_chat_cancels
        assert stopping_criteria_seen.wait(timeout=2.0)
