"""Routes de gestion de la configuration et bascule de mode (app/api/routes_config.py)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.routes_crud import verify_trusted_origin
from app.api.routes_generation import get_task_orchestrator
from app.config import CONFIG_FILE, DATA_DIR, GENERATIONS_FILE
from app.models.domain import ExecutionMode, StudioConfig, TaskStatus
from app.services.task_orchestrator import TaskOrchestrator
from app.storage.json_store import JSONDocumentStore

router = APIRouter(prefix="/api/config", tags=["Configuration"])

_default_store = JSONDocumentStore(DATA_DIR)


def get_config_store() -> JSONDocumentStore:
    """Fournisseur de dépendance pour le store JSON de configuration."""
    return _default_store


def _mask_config_secrets(cfg_dict: dict[str, Any]) -> dict[str, Any]:
    """Masque les clés API et secrets sensibles."""
    res = dict(cfg_dict)
    if res.get("compilerLlm", {}).get("apiKey"):
        res["compilerLlm"] = dict(res["compilerLlm"])
        res["compilerLlm"]["apiKey"] = "***"
    return res


class ExecutionModeUpdate(BaseModel):
    executionMode: ExecutionMode


@router.get("", response_model=dict[str, Any])
async def get_config(
    store: JSONDocumentStore = Depends(get_config_store),
) -> dict[str, Any]:
    """Retourne la configuration active en masquant les secrets."""
    cfg_dict = await store.read_dict(CONFIG_FILE.name, default=StudioConfig().model_dump())
    cfg = StudioConfig.model_validate(cfg_dict)
    return _mask_config_secrets(cfg.model_dump())


@router.post(
    "/execution-mode",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_trusted_origin)],
)
async def set_execution_mode(
    payload: ExecutionModeUpdate,
    store: JSONDocumentStore = Depends(get_config_store),
    orchestrator: TaskOrchestrator = Depends(get_task_orchestrator),
) -> Any:
    """Bascule le mode d'exécution actif (local <-> colab). Refusé en cas de tâche en cours."""
    async with orchestrator.coordination_lock:
        # Vérification des tâches actives
        generations = await store.read_list(GENERATIONS_FILE.name)
        active_tasks = [
            gen["id"]
            for gen in generations
            if gen.get("status") in {TaskStatus.PENDING.value, TaskStatus.RUNNING.value}
        ]

        if active_tasks:
            return JSONResponse(
                status_code=409,
                content={
                    "detail": (
                        "Impossible de basculer de mode d'exécution pendant une tâche en cours"
                    ),
                    "activeTaskIds": active_tasks,
                },
            )

        async with store.lock_for(CONFIG_FILE.name):
            cfg_dict = await store.read_dict_unlocked(
                CONFIG_FILE.name, default=StudioConfig().model_dump()
            )
            cfg_dict["executionMode"] = payload.executionMode.value
            await store.write_dict_unlocked(CONFIG_FILE.name, cfg_dict)

        return _mask_config_secrets(cfg_dict)
