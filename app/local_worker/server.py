"""Serveur FastAPI du Worker Local (app/local_worker/server.py).

Processus séparé conforme au contrat unique de worker :
- Port par défaut : 8190
- Charge les modèles depuis LOCAL_WORKER_MANIFEST (ou local_models.example.json)
- Métriques GPU via nvidia-smi
- Gestion de tâches asynchrones et distribution de fichiers binaires
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import shutil
import subprocess
import tempfile
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

DEFAULT_MANIFEST_PATH = Path(__file__).resolve().parent / "local_models.example.json"
DEFAULT_FILES_DIR = Path(
    os.environ.get(
        "LOCAL_WORKER_FILES_DIR",
        str(Path(tempfile.gettempdir()) / "colab_studio_worker_files"),
    )
)


class SwitchModelPayload(BaseModel):
    modelId: str


class InferPayload(BaseModel):
    modelId: str
    prompt: str
    negativePrompt: str | None = None
    parameters: dict[str, Any] = {}
    references: dict[str, Any] = {}


def _detect_gpu() -> tuple[str | None, int | None]:
    if not shutil.which("nvidia-smi"):
        return None, None
    with contextlib.suppress(Exception):
        cmd = [
            "nvidia-smi",
            "--query-gpu=name,memory.free",
            "--format=csv,noheader,nounits",
        ]
        out = subprocess.check_output(cmd, timeout=3).decode("utf-8").strip()
        lines = out.splitlines()
        if lines:
            parts = lines[0].split(",")
            name = parts[0].strip()
            free_mb = int(parts[1].strip()) if len(parts) > 1 else None
            return name, free_mb
    return None, None


def create_worker_app(
    manifest_path: Path | str | None = None,
    files_dir: Path | str | None = None,
    gpu_name_override: str | None = None,
    vram_free_override: int | None = None,
) -> FastAPI:
    app = FastAPI(title="Colab AI Studio Local Worker", version="1.0.0")

    resolved_manifest = Path(
        manifest_path or os.environ.get("LOCAL_WORKER_MANIFEST") or DEFAULT_MANIFEST_PATH
    )
    resolved_files = Path(files_dir or DEFAULT_FILES_DIR).resolve()
    resolved_files.mkdir(parents=True, exist_ok=True)
    resolved_files_str = str(resolved_files)

    # État mémoire du worker
    active_model_id: str | None = None
    tasks: dict[str, dict[str, Any]] = {}
    tasks_lock = asyncio.Lock()

    def _load_models() -> list[dict[str, Any]]:
        if not resolved_manifest.exists():
            return []
        try:
            raw = resolved_manifest.read_text(encoding="utf-8")
            data = json.loads(raw)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    models_cache = _load_models()
    if models_cache:
        active_model_id = models_cache[0]["id"]

    @app.get("/health")
    async def get_health() -> dict[str, Any]:
        if gpu_name_override is not None:
            gpu_name = gpu_name_override
            vram_free = vram_free_override
        else:
            gpu_name, vram_free = await asyncio.to_thread(_detect_gpu)

        return {
            "status": "ok",
            "service": "Colab AI Studio Local Worker",
            "version": "1.0.0",
            "gpu": gpu_name,
            "vramFreeMb": vram_free,
            "activeModel": active_model_id,
        }

    @app.get("/models")
    async def list_models() -> list[dict[str, Any]]:
        return _load_models()

    @app.post("/models/switch")
    async def switch_model(payload: SwitchModelPayload) -> dict[str, Any]:
        nonlocal active_model_id
        valid_ids = {m.get("id") for m in _load_models()}
        if payload.modelId not in valid_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Modèle inconnu dans le manifeste local : {payload.modelId}",
            )
        active_model_id = payload.modelId
        return {"switched": True, "activeModel": active_model_id}

    @app.post("/infer")
    async def start_inference(payload: InferPayload) -> dict[str, Any]:
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        task_entry: dict[str, Any] = {
            "taskId": task_id,
            "status": "pending",
            "progress": 0,
            "modelId": payload.modelId,
            "prompt": payload.prompt,
            "createdAt": now,
            "filePath": None,
            "errorMessage": None,
        }

        async with tasks_lock:
            tasks[task_id] = task_entry

        # Simulation de l'achèvement de tâche pour le runner
        async def _run_async_job(tid: str) -> None:
            await asyncio.sleep(0.05)
            async with tasks_lock:
                if tid in tasks and tasks[tid]["status"] != "cancelled":
                    tasks[tid]["status"] = "running"
                    tasks[tid]["progress"] = 50
            await asyncio.sleep(0.05)
            async with tasks_lock:
                if tid in tasks and tasks[tid]["status"] != "cancelled":
                    tasks[tid]["status"] = "completed"
                    tasks[tid]["progress"] = 100

        asyncio.create_task(_run_async_job(task_id))
        return {"taskId": task_id, "status": "pending"}

    @app.get("/tasks/{task_id}/status")
    async def get_task_status(task_id: str) -> dict[str, Any]:
        async with tasks_lock:
            if task_id not in tasks:
                raise HTTPException(status_code=404, detail="Tâche introuvable")
            return dict(tasks[task_id])

    @app.post("/tasks/{task_id}/cancel")
    async def cancel_task(task_id: str) -> dict[str, Any]:
        async with tasks_lock:
            if task_id not in tasks:
                raise HTTPException(status_code=404, detail="Tâche introuvable")
            tasks[task_id]["status"] = "cancelled"
            return dict(tasks[task_id])

    @app.get("/files/{filename}")
    async def get_file(filename: str) -> Any:
        def _check_file() -> tuple[bool, bool, str]:
            safe_name = Path(filename).name
            target = (resolved_files / safe_name).resolve()
            is_valid_dir = str(target).startswith(resolved_files_str)
            return is_valid_dir, target.is_file(), str(target)

        valid_dir, is_file, path_str = await asyncio.to_thread(_check_file)
        if not valid_dir:
            return JSONResponse(status_code=403, content={"detail": "Accès interdit"})
        if not is_file:
            raise HTTPException(status_code=404, detail="Fichier introuvable")
        return FileResponse(path_str)

    @app.post("/v1/chat/completions")
    async def local_chat_completions(request: Request) -> Response:
        try:
            body = await request.json()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Corps JSON invalide") from exc

        is_stream = bool(body.get("stream", False))
        chat_id = f"chatcmpl_{uuid.uuid4().hex[:12]}"
        now = int(datetime.now(timezone.utc).timestamp())
        model_name = body.get("model", active_model_id or "default")

        if is_stream:

            async def _stream_tokens() -> AsyncIterator[str]:
                tokens = ["Bonjour", " !", " Je", " suis", " le", " modèle", " local", "."]
                for tok in tokens:
                    chunk = {
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "created": now,
                        "model": model_name,
                        "choices": [{"index": 0, "delta": {"content": tok}, "finish_reason": None}],
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    await asyncio.sleep(0.01)
                final_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": now,
                    "model": model_name,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                }
                yield f"data: {json.dumps(final_chunk)}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(_stream_tokens(), media_type="text/event-stream")

        return JSONResponse(
            status_code=200,
            content={
                "id": chat_id,
                "object": "chat.completion",
                "created": now,
                "model": model_name,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Bonjour ! Je suis le modèle local.",
                        },
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    @app.post("/v1/chat/cancel")
    async def cancel_chat(payload: dict[str, Any]) -> dict[str, Any]:
        return {"cancelled": True, "requestId": payload.get("requestId")}

    return app


# Application singleton par défaut pour exécution CLI uvicorn app.local_worker.server:app
app = create_worker_app()
