"""Tests de bout en bout (E2E) couvrant UC-01 à UC-08 de Colab AI Studio."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from httpx import ASGITransport

from app.api import routes_crud
from app.api.routes_generation import get_task_orchestrator
from app.api.routes_models import get_worker_gateway
from app.colab_worker.model_swapper import ModelSwapper
from app.colab_worker.server import create_worker_app
from app.config import (
    CONFIG_FILE,
    GENERATIONS_FILE,
)
from app.main import app
from app.models.domain import ExecutionMode, StudioConfig
from app.services.brand_compiler import BrandContextCompiler
from app.services.brand_extractor import BrandKitExtractor
from app.services.task_orchestrator import TaskOrchestrator
from app.services.worker_gateway import WorkerGateway
from app.storage.json_store import JSONDocumentStore
from app.storage.media_store import MediaFileStore


class MockWorkerCuda:
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
def e2e_env(tmp_path: Path):
    d_dir, out_dir = tmp_path / "data", tmp_path / "outputs"
    ast_dir, w_storage = d_dir / "assets", tmp_path / "w_storage"
    c_storage = tmp_path / "c_storage"
    for d in (d_dir, out_dir, ast_dir, w_storage, c_storage):
        d.mkdir(parents=True, exist_ok=True)

    json_store = JSONDocumentStore(d_dir)
    media_store = MediaFileStore(out_dir)
    brand_extractor = BrandKitExtractor(ast_dir)

    orig_j, orig_m = routes_crud._json_store, routes_crud._media_store
    orig_e = routes_crud._extractor
    routes_crud._json_store, routes_crud._media_store = json_store, media_store
    routes_crud._extractor = brand_extractor

    worker_secret = "e2e-secret-key-42"
    swapper = ModelSwapper(cuda_backend=MockWorkerCuda(), idle_timeout_seconds=300.0)
    worker_fastapi = create_worker_app(
        model_swapper=swapper, storage_dir=w_storage, worker_secret=worker_secret
    )
    worker_client = httpx.AsyncClient(
        transport=ASGITransport(app=worker_fastapi), base_url="http://test-colab-worker"
    )
    gateway = WorkerGateway(json_store=json_store, http_client=worker_client)
    orchestrator = TaskOrchestrator(
        json_store=json_store,
        media_store=media_store,
        worker_gateway=gateway,
        brand_compiler=BrandContextCompiler(),
        poll_interval=0.02,
        task_timeout=15.0,
    )
    app.dependency_overrides[get_worker_gateway] = lambda: gateway
    app.dependency_overrides[get_task_orchestrator] = lambda: orchestrator

    try:
        yield {
            "data_dir": d_dir,
            "outputs_dir": out_dir,
            "custom_project_storage": c_storage,
            "json_store": json_store,
            "gateway": gateway,
            "orchestrator": orchestrator,
            "worker_secret": worker_secret,
        }
    finally:
        routes_crud._json_store = orig_j
        routes_crud._media_store = orig_m
        routes_crud._extractor = orig_e
        app.dependency_overrides.clear()


@pytest.fixture
async def client(e2e_env) -> httpx.AsyncClient:
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as c:
        yield c


@pytest.mark.anyio
async def test_full_pipeline_uc01_to_uc08(
    client: httpx.AsyncClient, e2e_env: dict[str, Any]
) -> None:
    """Valide de bout en bout l'enchaînement exhaustif des 8 cas d'utilisation."""
    json_store: JSONDocumentStore = e2e_env["json_store"]
    custom_project_storage: Path = e2e_env["custom_project_storage"]

    # --- UC-08 : Connecter l'environnement distant ---
    colab_cfg = {"tunnelUrl": "http://test-colab-worker", "secret": e2e_env["worker_secret"]}
    cfg = StudioConfig(executionMode=ExecutionMode.COLAB, colab=colab_cfg)
    await json_store.write_dict(CONFIG_FILE.name, cfg.model_dump())

    health_resp = await client.get("/api/health")
    assert health_resp.status_code == 200
    h_data = health_resp.json()
    assert h_data["executionMode"] == "colab"
    assert h_data["worker"]["reachable"] is True
    assert h_data["worker"]["gpu"] == "Tesla T4 Test"

    # --- UC-06 : Gérer les Brand Kits ---
    bk_form = {"name": "NovaCyber", "overview": "Cyberpunk néon"}
    kit_id = (await client.post("/api/brand-kits", data=bk_form)).json()["id"]
    assert any(k["id"] == kit_id for k in (await client.get("/api/brand-kits")).json())

    # --- UC-07 : Organiser les projets ---
    proj_payload = {"name": "Film Sci-Fi", "storagePath": str(custom_project_storage)}
    proj_id = (await client.post("/api/projects", json=proj_payload)).json()["id"]

    # --- UC-01 & UC-03 : Produire un média & Suivre la génération via SSE ---
    gen_payload = {
        "prompt": "Un agent cyborg sous une pluie néon",
        "modelId": "wan-2.1-t2v",
        "type": "video",
        "brandKitId": kit_id,
        "projectId": proj_id,
        "parameters": {"aspectRatio": "16:9", "duration": "5s", "seed": 101},
    }
    gen_submit_resp = await client.post("/api/generate/media", json=gen_payload)
    assert gen_submit_resp.status_code == 202
    task_id = gen_submit_resp.json()["taskId"]

    # Écoute du flux SSE
    sse_events = []
    async with client.stream("GET", f"/api/tasks/{task_id}/status") as sse_stream:
        assert sse_stream.status_code == 200
        async for line in sse_stream.aiter_lines():
            if line.startswith("data: "):
                payload_str = line[6:].strip()
                try:
                    data = json.loads(payload_str)
                    sse_events.append(data)
                    if data.get("status") in {"completed", "failed", "cancelled"}:
                        break
                except json.JSONDecodeError:
                    pass

    assert len(sse_events) >= 1
    last_event = sse_events[-1]
    assert last_event["status"] == "completed"

    # Vérification du rapatriement physique dans le storagePath du projet
    repatriated_files = list(custom_project_storage.glob("*.mp4"))
    assert len(repatriated_files) == 1, (
        f"Le fichier binaire produit n'a pas été rapatrié dans {custom_project_storage}"
    )
    assert repatriated_files[0].stat().st_size > 0

    # Vérification de l'enregistrement documentaire
    all_gens = await json_store.read_list(GENERATIONS_FILE.name)
    saved_gen = next((g for g in all_gens if g["id"] == task_id), None)
    assert saved_gen is not None
    assert saved_gen["status"] == "completed"
    assert saved_gen["projectId"] == proj_id
    assert saved_gen["brandKitSnapshot"]["id"] == kit_id

    # Génération d'image (flux-schnell) avec rapatriement en .png conforme (Thread #5)
    img_payload = {
        "prompt": "Portrait cyberpunk",
        "modelId": "flux-schnell",
        "type": "image",
        "projectId": proj_id,
    }
    img_submit_resp = await client.post("/api/generate/media", json=img_payload)
    assert img_submit_resp.status_code == 202
    img_task_id = img_submit_resp.json()["taskId"]

    async with client.stream("GET", f"/api/tasks/{img_task_id}/status") as sse_stream:
        async for line in sse_stream.aiter_lines():
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:].strip())
                    if data.get("status") in {"completed", "failed", "cancelled"}:
                        assert data.get("status") == "completed"
                        break
                except json.JSONDecodeError:
                    pass

    repatriated_pngs = list(custom_project_storage.glob("*.png"))
    assert len(repatriated_pngs) == 1
    assert repatriated_pngs[0].read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

    # --- UC-05 : Parcourir et remixer ---
    list_gens_resp = await client.get("/api/generations?projectId=" + proj_id)
    assert list_gens_resp.status_code == 200
    assert len(list_gens_resp.json()) == 2

    # Bascule Favori
    fav_resp = await client.patch(f"/api/generations/{task_id}/favorite")
    assert fav_resp.status_code == 200
    assert fav_resp.json()["isFavorite"] is True

    # --- UC-04 : Annuler une génération ---
    cancel_payload = {"prompt": "Annuler", "modelId": "wan-2.1-t2v", "type": "video"}
    res = await client.post("/api/generate/media", json=cancel_payload)
    task_to_cancel_id = res.json()["taskId"]
    cancel_call = await client.post(f"/api/tasks/{task_to_cancel_id}/cancel")
    assert cancel_call.status_code == 200 and cancel_call.json()["status"] == "cancelled"

    # Vérification que le statut persisté est cancelled
    gens_after_cancel = await json_store.read_list(GENERATIONS_FILE.name)
    cancelled_gen = next((g for g in gens_after_cancel if g["id"] == task_to_cancel_id), None)
    assert cancelled_gen is not None
    assert cancelled_gen["status"] == "cancelled"

    # --- UC-02 : Interagir avec l'assistant textuel IA (LLM Proxy) ---
    chat_payload = {
        "model": "llama-3-8b-instruct",
        "messages": [{"role": "user", "content": "Slogan NovaCyber"}],
        "stream": True,
    }
    chat_lines = []
    async with client.stream("POST", "/v1/chat/completions", json=chat_payload) as chat_stream:
        assert chat_stream.status_code == 200
        async for line in chat_stream.aiter_lines():
            if line:
                chat_lines.append(line)

    assert any("data: " in line for line in chat_lines)
    assert any("[DONE]" in line for line in chat_lines)

    # Nettoyage final : suppression des créations UC-05
    del_resp = await client.delete(f"/api/generations/{task_id}")
    assert del_resp.status_code == 200
    assert len(list(custom_project_storage.glob("*.mp4"))) == 0

    del_img_resp = await client.delete(f"/api/generations/{img_task_id}")
    assert del_img_resp.status_code == 200
    assert len(list(custom_project_storage.glob("*.png"))) == 0
