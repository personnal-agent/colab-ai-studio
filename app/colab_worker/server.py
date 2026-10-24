"""Serveur FastAPI du Worker Google Colab (app/colab_worker/server.py).

Expose l'ensemble des routes d'inférence, de contrôle et de streaming SSE
consommées par le backend local Colab AI Studio :
- GET /health
- GET /models
- POST /models/switch
- POST /infer
- GET /tasks/{task_id}/status
- POST /tasks/{task_id}/cancel
- POST /v1/chat/completions
- POST /v1/chat/cancel
- GET /files/{filename}
"""

from __future__ import annotations

import asyncio
import json
import logging
import tempfile
import time
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.colab_worker.model_swapper import ModelSwapper

logger = logging.getLogger(__name__)

AVAILABLE_MODELS: list[dict[str, Any]] = [
    {
        "id": "flux-schnell",
        "name": "FLUX.1 [schnell]",
        "type": "image",
        "capabilities": {
            "aspectRatios": ["1:1", "16:9", "9:16", "4:3", "3:4"],
            "resolutions": ["1024x1024", "768x768", "512x512"],
            "durations": ["1s"],
            "supportsNegativePrompt": False,
            "supportsSeed": True,
            "supportsImageRef": True,
            "maxImageRefs": 1,
        },
    },
    {
        "id": "wan-2.1-t2v",
        "name": "Wan 2.1 Video",
        "type": "video",
        "capabilities": {
            "aspectRatios": ["16:9", "9:16", "1:1"],
            "resolutions": ["720p", "480p"],
            "durations": ["5s", "10s"],
            "supportsNegativePrompt": True,
            "supportsSeed": True,
            "supportsImageRef": True,
            "maxImageRefs": 2,
        },
    },
    {
        "id": "cogvideox-5b",
        "name": "CogVideoX-5B",
        "type": "video",
        "capabilities": {
            "aspectRatios": ["16:9"],
            "resolutions": ["720p"],
            "durations": ["6s"],
            "supportsNegativePrompt": True,
            "supportsSeed": True,
            "supportsImageRef": False,
            "maxImageRefs": 0,
        },
    },
    {
        "id": "wav2lip",
        "name": "Wav2Lip Lip Sync",
        "type": "lipsync",
        "capabilities": {
            "aspectRatios": ["16:9", "9:16", "1:1"],
            "resolutions": ["720p"],
            "durations": ["5s", "10s", "15s"],
            "supportsNegativePrompt": False,
            "supportsSeed": False,
            "supportsImageRef": False,
            "maxImageRefs": 0,
        },
    },
    {
        "id": "realesrgan-x4",
        "name": "Real-ESRGAN Upscaler",
        "type": "upscale",
        "capabilities": {
            "aspectRatios": ["16:9", "9:16", "1:1"],
            "resolutions": ["1080p", "4K"],
            "durations": ["5s"],
            "supportsNegativePrompt": False,
            "supportsSeed": False,
            "supportsImageRef": False,
            "maxImageRefs": 0,
        },
    },
    {
        "id": "llama-3-8b-instruct",
        "name": "Llama 3 8B Instruct",
        "type": "text",
        "capabilities": {
            "aspectRatios": [],
            "resolutions": [],
            "durations": [],
            "supportsNegativePrompt": False,
            "supportsSeed": False,
            "supportsImageRef": False,
            "maxImageRefs": 0,
        },
    },
]


class SwitchModelRequest(BaseModel):
    modelId: str


class InferRequest(BaseModel):
    taskId: str | None = None
    modelId: str
    prompt: str = ""
    negativePrompt: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    references: dict[str, Any] = Field(default_factory=dict)
    steps: int = 5


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "llama-3-8b-instruct"
    messages: list[ChatMessage]
    stream: bool = True
    requestId: str | None = None


class ChatCancelRequest(BaseModel):
    requestId: str


def create_worker_app(
    model_swapper: ModelSwapper | None = None,
    storage_dir: Path | None = None,
) -> FastAPI:
    """Fabrique d'application FastAPI pour le worker Google Colab."""
    swapper = model_swapper or ModelSwapper()
    output_dir = storage_dir or (Path(tempfile.gettempdir()) / "colab_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    tasks: dict[str, dict[str, Any]] = {}
    cancel_events: dict[str, asyncio.Event] = {}
    active_chat_cancels: set[str] = set()

    app = FastAPI(title="Colab AI Studio Worker", version="1.0.0")

    origins = [
        f"http://{h}:{p}" for h in ("localhost", "127.0.0.1") for p in (5173, 8000, 8190)
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        return {"status": "ok", **swapper.get_telemetry()}

    @app.get("/models")
    async def list_models() -> list[dict[str, Any]]:
        return AVAILABLE_MODELS

    @app.post("/models/switch")
    async def switch_model(payload: SwitchModelRequest) -> dict[str, Any]:
        swapper.ensure_model(payload.modelId)
        return {"status": "ok", "activeModel": payload.modelId}

    async def _execute_inference_task(task_id: str, payload: InferRequest) -> None:
        cancel_event = cancel_events[task_id]
        tasks[task_id]["status"] = "running"
        total_steps = max(1, payload.steps)

        try:
            # 1. Permutation / garantie du modèle
            swapper.ensure_model(payload.modelId)

            # 2. Boucle de génération interruptible
            for step in range(1, total_steps + 1):
                if cancel_event.is_set():
                    tasks[task_id]["status"] = "cancelled"
                    tasks[task_id]["errorMessage"] = "Annulée par l'utilisateur"
                    return

                await asyncio.sleep(0.04)
                tasks[task_id]["step"] = step
                tasks[task_id]["totalSteps"] = total_steps
                tasks[task_id]["progress"] = int(round(step / total_steps * 100))

            if cancel_event.is_set():
                tasks[task_id]["status"] = "cancelled"
                tasks[task_id]["errorMessage"] = "Annulée par l'utilisateur"
                return

            # 3. Création du fichier binaire produit
            is_video = any(
                m["id"] == payload.modelId and m["type"] in {"video", "lipsync"}
                for m in AVAILABLE_MODELS
            )
            ext = ".mp4" if is_video else ".png"
            filename = f"{task_id}{ext}"
            file_path = output_dir / filename

            # Données factices mais valides en en-tête
            dummy_content = b"\x89PNG\r\n\x1a\n" if ext == ".png" else b"\x00\x00\x00\x18ftypmp42"
            file_path.write_bytes(dummy_content + b"\x00" * 256)

            tasks[task_id]["status"] = "completed"
            tasks[task_id]["progress"] = 100
            tasks[task_id]["outputUrl"] = f"/files/{filename}"

        except Exception as exc:
            logger.exception("Erreur durant l'inférence tâche %s : %s", task_id, exc)
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["errorMessage"] = str(exc)

    @app.post("/infer")
    async def infer(payload: InferRequest) -> dict[str, Any]:
        task_id = payload.taskId or f"task_{uuid.uuid4().hex[:12]}"
        cancel_event = asyncio.Event()
        cancel_events[task_id] = cancel_event

        tasks[task_id] = {
            "taskId": task_id,
            "status": "pending",
            "progress": 0.0,
            "step": 0,
            "totalSteps": payload.steps,
            "outputUrl": None,
            "errorMessage": None,
            "createdAt": time.time(),
        }

        asyncio.create_task(_execute_inference_task(task_id, payload))
        return {"taskId": task_id, "status": "pending"}

    @app.get("/tasks/{task_id}/status")
    async def get_task_status(task_id: str) -> dict[str, Any]:
        if task_id not in tasks:
            raise HTTPException(status_code=404, detail="Tâche introuvable")
        return tasks[task_id]

    @app.post("/tasks/{task_id}/cancel")
    async def cancel_task(task_id: str) -> dict[str, Any]:
        if task_id in cancel_events:
            cancel_events[task_id].set()
        if task_id in tasks:
            tasks[task_id]["status"] = "cancelled"
            tasks[task_id]["errorMessage"] = "Annulée par l'utilisateur"
        return {"status": "cancelled", "taskId": task_id}

    @app.get("/files/{filename}")
    async def download_file(filename: str) -> FileResponse:
        clean_name = filename.strip().lstrip("/")
        if ".." in clean_name or "/" in clean_name or "\\" in clean_name:
            raise HTTPException(status_code=400, detail="Chemin de fichier interdit")

        file_path = output_dir / clean_name
        if not file_path.is_file():
            raise HTTPException(status_code=404, detail="Fichier introuvable sur le worker")

        media_type = "video/mp4" if clean_name.endswith(".mp4") else "image/png"
        return FileResponse(file_path, media_type=media_type, filename=clean_name)

    @app.post("/v1/chat/cancel")
    async def cancel_chat(payload: ChatCancelRequest) -> dict[str, str]:
        active_chat_cancels.add(payload.requestId)
        return {"status": "cancelled", "requestId": payload.requestId}

    @app.post("/v1/chat/completions")
    async def chat_completions(payload: ChatCompletionRequest, request: Request) -> Any:
        swapper.ensure_model(payload.model)
        request_id = payload.requestId or f"chat_{uuid.uuid4().hex[:10]}"

        if not payload.stream:
            return {
                "id": request_id,
                "object": "chat.completion",
                "created": int(time.time()),
                "model": payload.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Réponse générée par le worker Colab.",
                        },
                        "finish_reason": "stop",
                    }
                ],
            }

        async def chat_stream_generator() -> AsyncGenerator[str, None]:
            words = [
                "Bonjour", " ! ", "Voici", " une", " réponse", " synthétisée", " en",
                " streaming", " par", " le", " worker", " Colab.",
            ]
            try:
                for word in words:
                    if request_id in active_chat_cancels or await request.is_disconnected():
                        logger.info("Chat LLM annulé pour %s.", request_id)
                        return

                    chunk = {
                        "id": request_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": payload.model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": word},
                                "finish_reason": None,
                            }
                        ],
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    await asyncio.sleep(0.04)

                yield "data: [DONE]\n\n"
            finally:
                active_chat_cancels.discard(request_id)

        return StreamingResponse(
            chat_stream_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    return app
