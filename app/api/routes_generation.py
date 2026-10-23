"""Routeur de génération multimédia et Server-Sent Events (app/api/routes_generation.py).

Gère :
- POST /api/generate/media (lancement asynchrone d'une tâche de génération)
- GET /api/tasks/{task_id}/status (flux SSE de progression en temps réel)
- POST /api/tasks/{task_id}/cancel (annulation idempotente)
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.config import DATA_DIR, OUTPUTS_DIR
from app.models.domain import Generation, TaskStatus
from app.services.brand_compiler import BrandContextCompiler
from app.services.task_orchestrator import GenerationPayload, TaskOrchestrator
from app.services.worker_gateway import WorkerGateway
from app.storage.json_store import JSONDocumentStore
from app.storage.media_store import MediaFileStore

router = APIRouter(prefix="/api", tags=["Génération Média"])

_json_store = JSONDocumentStore(DATA_DIR)
_media_store = MediaFileStore(OUTPUTS_DIR)
_gateway = WorkerGateway(store=_json_store)
_compiler = BrandContextCompiler()
_orchestrator = TaskOrchestrator(
    json_store=_json_store,
    media_store=_media_store,
    gateway=_gateway,
    brand_compiler=_compiler,
)


@router.post("/generate/media", response_model=dict[str, Any], status_code=201)
async def generate_media(payload: GenerationPayload) -> dict[str, Any]:
    gen: Generation = await _orchestrator.submit_generation(payload)
    return gen.model_dump()


@router.get("/tasks/{task_id}/status")
async def task_status_sse(task_id: str, request: Request) -> StreamingResponse:
    # 1. Vérification que la tâche existe
    items = await _orchestrator.json_store.read_list("generations.json")
    item = next((it for it in items if it.get("id") == task_id), None)
    if not item:
        raise HTTPException(status_code=404, detail=f"Tâche {task_id} introuvable")

    queue = await _orchestrator.register_listener(task_id)

    async def event_generator() -> AsyncIterator[str]:
        try:
            # Événement initial avec l'état courant
            initial_data = {
                "taskId": task_id,
                "status": item.get("status"),
                "progress": item.get("progress", 0),
            }
            yield f"data: {json.dumps(initial_data)}\n\n"

            if item.get("status") in {
                TaskStatus.COMPLETED.value,
                TaskStatus.FAILED.value,
                TaskStatus.CANCELLED.value,
            }:
                return

            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=2.0)
                    yield f"data: {json.dumps(event)}\n\n"
                    if event.get("status") in {
                        TaskStatus.COMPLETED.value,
                        TaskStatus.FAILED.value,
                        TaskStatus.CANCELLED.value,
                    }:
                        break
                except asyncio.TimeoutError:
                    # Ping keep-alive pour maintenir la connexion SSE ouverte
                    yield ": ping\n\n"
        finally:
            await _orchestrator.unregister_listener(task_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/tasks/{task_id}/cancel", response_model=dict[str, Any])
async def cancel_task(task_id: str) -> dict[str, Any]:
    try:
        gen = await _orchestrator.cancel_generation(task_id)
        return gen.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
