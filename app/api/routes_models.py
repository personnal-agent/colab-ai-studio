"""Routes de gestion des modèles et bascule de VRAM (app/api/routes_models.py)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.routes_crud import verify_trusted_origin
from app.services.worker_gateway import (
    WorkerGateway,
    WorkerNotConfiguredError,
    WorkerUnavailableError,
)

router = APIRouter(prefix="/api/models", tags=["Modèles"])

_default_gateway = WorkerGateway()


def get_worker_gateway() -> WorkerGateway:
    """Fournisseur de dépendance pour la passerelle worker."""
    return _default_gateway


class ModelSwitchRequest(BaseModel):
    modelId: str


@router.get("", response_model=list[dict[str, Any]])
async def list_models(
    gateway: WorkerGateway = Depends(get_worker_gateway),
) -> list[dict[str, Any]]:
    """Retourne la liste des modèles disponibles sur le worker actif."""
    try:
        return await gateway.list_models()
    except (WorkerNotConfiguredError, WorkerUnavailableError) as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@router.post(
    "/switch",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_trusted_origin)],
)
async def switch_model(
    payload: ModelSwitchRequest,
    gateway: WorkerGateway = Depends(get_worker_gateway),
) -> dict[str, Any]:
    """Bascule le modèle actif en VRAM sur le worker de calcul."""
    try:
        return await gateway.switch_model(payload.modelId)
    except (WorkerNotConfiguredError, WorkerUnavailableError) as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
