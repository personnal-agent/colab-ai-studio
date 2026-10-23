"""Tests de l'API du Worker Colab (tests/api/test_colab_worker_api.py).

Valide les endpoints exposés sur le tunnel Colab :
- GET /health (métriques GPU/VRAM et swapper)
- GET /models
- POST /models/switch
- POST /infer & GET /tasks/{id}/status & POST /tasks/{id}/cancel
- POST /v1/chat/completions (sync & stream)
- GET /files/{filename}
"""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.colab_worker.model_swapper import ModelSwapper
from app.colab_worker.server import create_colab_worker_app


class DummyCuda:
    def empty_cache(self):
        pass

    def ipc_collect(self):
        pass

    def gc_collect(self):
        pass


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    out = tmp_path / "colab_outputs"
    out.mkdir(parents=True, exist_ok=True)
    return out


@pytest.fixture
def test_swapper() -> ModelSwapper:
    return ModelSwapper(cuda_manager=DummyCuda())


@pytest.fixture
def colab_app(test_swapper: ModelSwapper, temp_output_dir: Path):
    return create_colab_worker_app(
        swapper=test_swapper,
        outputs_dir=temp_output_dir,
        gpu_name="NVIDIA Tesla T4",
        vram_free_mb=14500,
    )


@pytest.mark.asyncio
async def test_colab_health(colab_app):
    transport = ASGITransport(app=colab_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["gpu"] == "NVIDIA Tesla T4"
        assert data["vramFreeMb"] == 14500
        assert "swapperState" in data


@pytest.mark.asyncio
async def test_colab_list_and_switch_models(colab_app):
    transport = ASGITransport(app=colab_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/models")
        assert resp.status_code == 200
        models = resp.json()
        assert len(models) >= 2
        model_ids = [m["id"] for m in models]
        target_model = model_ids[0]

        # Switch model
        switch_resp = await client.post("/models/switch", json={"modelId": target_model})
        assert switch_resp.status_code == 200
        assert switch_resp.json()["activeModel"] == target_model


@pytest.mark.asyncio
async def test_colab_infer_and_cancel_lifecycle(colab_app):
    transport = ASGITransport(app=colab_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Soumission
        infer_resp = await client.post(
            "/infer",
            json={
                "modelId": "minimax-h3",
                "prompt": "Cyberpunk night view",
                "parameters": {"aspectRatio": "16:9", "duration": "5s"},
            },
        )
        assert infer_resp.status_code == 200
        task_id = infer_resp.json()["taskId"]

        # Status
        status_resp = await client.get(f"/tasks/{task_id}/status")
        assert status_resp.status_code == 200
        assert status_resp.json()["taskId"] == task_id

        # Annulation
        cancel_resp = await client.post(f"/tasks/{task_id}/cancel")
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_colab_file_download(colab_app, temp_output_dir: Path):
    # Créer un fichier binaire factice
    test_file = temp_output_dir / "sample_video.mp4"
    test_file.write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00")

    transport = ASGITransport(app=colab_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/files/sample_video.mp4")
        assert resp.status_code == 200
        assert resp.content == b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00"


@pytest.mark.asyncio
async def test_colab_chat_completions_stream(colab_app):
    transport = ASGITransport(app=colab_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "model": "qwen3.8-turbo",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True,
        }
        resp = await client.post("/v1/chat/completions", json=payload)
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")
        body = resp.text
        assert "data: " in body
        assert "[DONE]" in body
