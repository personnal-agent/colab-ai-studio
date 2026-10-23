"""Routeur des modèles et de la santé du worker (app/api/routes_models.py).

Gère :
- GET /api/health (état du backend local + diagnostic en direct du worker actif)
- GET /api/models (liste dynamique des modèles supportés par le worker)
- POST /api/models/switch (demande d'éviction/chargement VRAM au worker)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import DATA_DIR
from app.services.worker_gateway import WorkerGateway, WorkerGatewayError
from app.storage.json_store import JSONDocumentStore

router = APIRouter(prefix="/api", tags=["Modèles & Worker"])

_json_store = JSONDocumentStore(DATA_DIR)
_gateway = WorkerGateway(store=_json_store)


class ModelSwitchRequest(BaseModel):
    modelId: str


@router.get("/health", tags=["Diagnostic"])
async def health_check() -> dict[str, Any]:
    worker_health = await _gateway.check_worker_health()
    return {
        "status": "healthy",
        "service": "Colab AI Studio Local Backend",
        "version": "1.0.0",
        "executionMode": worker_health.get("executionMode"),
        "worker": worker_health,
    }


@router.get("/models", response_model=list[dict[str, Any]])
async def list_models() -> list[dict[str, Any]]:
    try:
        return await _gateway.list_models()
    except WorkerGatewayError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e)) from e


@router.post("/models/switch", response_model=dict[str, Any])
async def switch_model(payload: ModelSwitchRequest) -> dict[str, Any]:
    try:
        return await _gateway.switch_model(payload.modelId)
    except WorkerGatewayError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e)) from e
