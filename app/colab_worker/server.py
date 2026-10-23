"""Serveur FastAPI du Worker Google Colab (app/colab_worker/server.py).

Exposé via tunnel sécurisé (Ngrok / Cloudflare Tunnels) :
- /health : métriques VRAM, GPU et diagnostic ModelSwapper
- /models : catalogue dynamique des modèles supportés
- /models/switch : permutation VRAM orchestrée par ModelSwapper
- /infer : exécution asynchrone des inférences image/vidéo/audio/upscale
- /tasks/{task_id}/status : consultation de l'avancement
- /tasks/{task_id}/cancel : interruption coopérative
- /v1/chat/completions : proxy LLM standardisé OpenAI (sync & stream)
- /files/{filename} : téléchargement des binaires produits vers le backend local
"""

from __future__ import annotations

import asyncio
import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.colab_worker.model_swapper import ModelSwapper

COLAB_CATALOG: list[dict[str, Any]] = [
  {
    "id": "minimax-h3",
    "name": "MiniMax-H3 (Colab T4)",
    "mediaType": "video",
    "capabilities": {
      "aspectRatios": ["16:9", "9:16", "1:1"],
      "resolutions": ["720p", "1080p"],
      "durations": ["5s", "10s"],
      "durationMode": "discrete",
      "maxImageRefs": 9,
      "supportsStartFrame": True,
      "supportsEndFrame": True,
      "supportsNativeAudio": True,
    },
  },
  {
    "id": "noctq-v4",
    "name": "NoctQ V4 Photo & Edit (Colab T4)",
    "mediaType": "image",
    "capabilities": {
      "aspectRatios": ["16:9", "9:16", "1:1", "4:5", "3:4"],
      "resolutions": ["1K", "2K"],
      "batchSize": [1, 2, 4],
      "maxImageRefs": 4,
      "supportsImageEdit": True,
    },
  },
  {
    "id": "topaz-video-upscale",
    "name": "Topaz Video Upscale (Colab T4)",
    "mediaType": "upscale",
    "capabilities": {
      "upscaleScales": ["1.25x", "2x", "4x"],
      "upscaleQualities": ["Fast", "Precise"],
      "fpsOptions": ["Same as source", "24fps", "60fps"],
    },
  },
  {
    "id": "qwen3.8-turbo",
    "name": "Qwen 3.8B Turbo (Colab T4)",
    "mediaType": "llm",
    "capabilities": {
      "contextLength": 32768,
      "streaming": True,
    },
  },
]


class SwitchModelPayload(BaseModel):
    modelId: str


class InferPayload(BaseModel):
    modelId: str
    prompt: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    references: dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    stream: bool = False
    temperature: float = 0.7


def create_colab_worker_app(
    swapper: ModelSwapper | None = None,
    outputs_dir: Path | None = None,
    gpu_name: str = "NVIDIA Tesla T4 (Colab)",
    vram_free_mb: int = 14800,
) -> FastAPI:
    app = FastAPI(title="Colab AI Studio Worker", version="1.0.0")

    model_swapper = swapper or ModelSwapper()
    resolved_outputs = outputs_dir or (Path(tempfile.gettempdir()) / "colab_outputs")
    resolved_outputs.mkdir(parents=True, exist_ok=True)

    tasks: dict[str, dict[str, Any]] = {}
    tasks_lock = asyncio.Lock()

    @app.get("/health")
    async def get_health() -> dict[str, Any]:
        swapper_status = model_swapper.get_status()
        return {
            "status": "ok",
            "service": "Colab AI Studio Remote Worker",
            "version": "1.0.0",
            "gpu": gpu_name,
            "vramFreeMb": vram_free_mb,
            "activeModel": swapper_status.get("activeModel"),
            "swapperState": swapper_status.get("state"),
        }

    @app.get("/models")
    async def list_models() -> list[dict[str, Any]]:
        return COLAB_CATALOG

    @app.post("/models/switch")
    async def switch_model(payload: SwitchModelPayload) -> dict[str, Any]:
        valid_ids = {m["id"] for m in COLAB_CATALOG}
        if payload.modelId not in valid_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Modèle non répertorié : {payload.modelId}",
            )
        await model_swapper.acquire_model(payload.modelId)
        return {
            "switched": True,
            "activeModel": model_swapper.active_model,
            "state": model_swapper.state.value,
        }

    @app.post("/infer")
    async def start_inference(payload: InferPayload) -> dict[str, Any]:
        valid_ids = {m["id"] for m in COLAB_CATALOG}
        if payload.modelId not in valid_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Modèle inconnu : {payload.modelId}",
            )

        task_id = f"task_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        # Fichier résultat factice
        out_filename = f"{task_id}.mp4" if "video" in payload.modelId else f"{task_id}.png"
        out_path = resolved_outputs / out_filename
        out_path.write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00")

        task_entry: dict[str, Any] = {
            "taskId": task_id,
            "status": "pending",
            "progress": 0,
            "modelId": payload.modelId,
            "prompt": payload.prompt,
            "createdAt": now,
            "filePath": str(out_path),
            "filename": out_filename,
            "errorMessage": None,
        }

        async with tasks_lock:
            tasks[task_id] = task_entry

        async def _run_job(tid: str) -> None:
            try:
                await model_swapper.acquire_model(payload.modelId)
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
            finally:
                model_swapper.notify_inference_completed()

        asyncio.create_task(_run_job(task_id))
        return {"taskId": task_id, "status": "pending"}

    @app.get("/tasks/{task_id}/status")
    async def get_task_status(task_id: str) -> dict[str, Any]:
        async with tasks_lock:
            if task_id not in tasks:
                raise HTTPException(status_code=404, detail="Tâche introuvable")
            return tasks[task_id]

    @app.post("/tasks/{task_id}/cancel")
    async def cancel_task(task_id: str) -> dict[str, Any]:
        async with tasks_lock:
            if task_id not in tasks:
                raise HTTPException(status_code=404, detail="Tâche introuvable")
            tasks[task_id]["status"] = "cancelled"
            tasks[task_id]["progress"] = 0
            model_swapper.notify_inference_completed()
            return tasks[task_id]

    @app.get("/files/{filename}")
    async def download_file(filename: str) -> FileResponse:
        file_path = resolved_outputs / filename
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="Fichier introuvable sur le worker Colab")
        return FileResponse(path=str(file_path))

    @app.post("/v1/chat/completions")
    async def chat_completions(req: ChatCompletionRequest) -> Any:
        await model_swapper.acquire_model(req.model)

        async def _streamer():
            chunks = ["Hello ", "from ", "Colab ", "Worker!"]
            for c in chunks:
                await asyncio.sleep(0.02)
                chunk_data = {
                    "id": f"chatcmpl_{uuid.uuid4().hex[:8]}",
                    "object": "chat.completion.chunk",
                    "created": int(datetime.now(timezone.utc).timestamp()),
                    "model": req.model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": c},
                            "finish_reason": None,
                        }
                    ],
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
            yield "data: [DONE]\n\n"
            model_swapper.notify_inference_completed()

        if req.stream:
            return StreamingResponse(_streamer(), media_type="text/event-stream")

        model_swapper.notify_inference_completed()
        return {
            "id": f"chatcmpl_{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(datetime.now(timezone.utc).timestamp()),
            "model": req.model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello from Colab Worker!"},
                    "finish_reason": "stop",
                }
            ],
        }

    return app
