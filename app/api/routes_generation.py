"""Routes de génération multimédia et flux SSE (app/api/routes_generation.py)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.routes_crud import verify_trusted_origin
from app.services.task_orchestrator import GenerationCreateRequest, TaskOrchestrator

router = APIRouter(prefix="/api", tags=["Génération"])

_default_orchestrator = TaskOrchestrator()


def get_task_orchestrator() -> TaskOrchestrator:
    """Fournisseur de dépendance pour l'orchestrateur de tâches."""
    return _default_orchestrator


@router.post(
    "/generate/media",
    status_code=202,
    response_model=dict[str, Any],
    dependencies=[Depends(verify_trusted_origin)],
)
async def generate_media(
    payload: GenerationCreateRequest,
    orchestrator: TaskOrchestrator = Depends(get_task_orchestrator),
) -> dict[str, Any]:
    """Déclenche une génération asynchrone d'image ou de vidéo."""
    try:
        gen = await orchestrator.submit_generation(payload)
        return {
            "taskId": gen.id,
            "generationId": gen.id,
            "status": "pending",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Échec de soumission de génération : {e}",
        ) from e


@router.get("/tasks/{task_id}/status")
async def get_task_status_stream(
    task_id: str,
    orchestrator: TaskOrchestrator = Depends(get_task_orchestrator),
) -> StreamingResponse:
    """Abonnement au flux SSE temps réel d'une tâche de génération."""
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(
        orchestrator.subscribe_task(task_id),
        media_type="text/event-stream",
        headers=headers,
    )


@router.post(
    "/tasks/{task_id}/cancel",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_trusted_origin)],
)
async def cancel_task(
    task_id: str,
    orchestrator: TaskOrchestrator = Depends(get_task_orchestrator),
) -> dict[str, Any]:
    """Annule une tâche de génération de façon idempotente."""
    res = await orchestrator.cancel_task(task_id)
    if res.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    return res
