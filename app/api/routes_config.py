"""Routeur de configuration et de bascule d'exécution (app/api/routes_config.py).

Gère :
- GET /api/config (lecture de StudioConfig avec masquage de la clé API)
- POST /api/config/execution-mode (commutation à chaud avec vérification anti-conflit 409)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import CONFIG_FILE, DATA_DIR
from app.models.domain import ExecutionMode, StudioConfig, TaskStatus
from app.storage.json_store import JSONDocumentStore

router = APIRouter(prefix="/api/config", tags=["Configuration"])

_json_store = JSONDocumentStore(DATA_DIR)


class ExecutionModeUpdate(BaseModel):
    executionMode: ExecutionMode


def _mask_sensitive_config(config_dict: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(config_dict)
    if "compilerLlm" in sanitized and isinstance(sanitized["compilerLlm"], dict):
        sanitized["compilerLlm"] = dict(sanitized["compilerLlm"])
        sanitized["compilerLlm"]["apiKey"] = None
    return sanitized


@router.get("", response_model=dict[str, Any])
async def get_config() -> dict[str, Any]:
    raw_config = await _json_store.read_dict(
        CONFIG_FILE.name, default=StudioConfig().model_dump()
    )
    return _mask_sensitive_config(raw_config)


@router.post("/execution-mode", response_model=dict[str, Any])
async def switch_execution_mode(payload: ExecutionModeUpdate) -> Any:
    # 1. Vérification des tâches en vol (pending ou running)
    generations = await _json_store.read_list("generations.json")
    active_statuses = {TaskStatus.PENDING.value, TaskStatus.RUNNING.value}
    active_ids = [
        str(gen.get("id"))
        for gen in generations
        if gen.get("status") in active_statuses
    ]

    if active_ids:
        return JSONResponse(
            status_code=409,
            content={
                "detail": (
                    "Bascule de mode impossible : des tâches sont actuellement "
                    "en cours d'exécution sur le worker actif."
                ),
                "activeTaskIds": active_ids,
            },
        )

    # 2. Persistance atomique du nouveau mode
    async with _json_store.lock_for(CONFIG_FILE.name):
        raw_config = await _json_store.read_dict(
            CONFIG_FILE.name, default=StudioConfig().model_dump()
        )
        raw_config["executionMode"] = payload.executionMode.value
        await _json_store.write_dict(CONFIG_FILE.name, raw_config)

    return _mask_sensitive_config(raw_config)
