"""Routes CRUD pour les Directives et Instructions de l'Agent Créatif."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.routes_crud import get_json_store, verify_trusted_origin
from app.config import AGENT_INSTRUCTIONS_FILE
from app.models.domain import AgentInstruction, _utc_now_iso
from app.storage.json_store import JSONDocumentStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-instructions", tags=["Agent Instructions"])


class AgentInstructionCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, description="Titre de la consigne (ex: Style Néo-Noir)")
    description: str = Field(
        ...,
        min_length=3,
        description="Directives stylistiques ou scénaristiques précises",
    )
    isActive: bool = True
    referenceAssetUrls: list[str] = Field(default_factory=list)
    order: int | None = None


class AgentInstructionUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    isActive: bool | None = None
    referenceAssetUrls: list[str] | None = None
    order: int | None = None


class ReorderInstructionsRequest(BaseModel):
    instructionIds: list[str] = Field(..., min_length=1)


@router.get("", response_model=list[dict[str, Any]])
async def list_agent_instructions(
    store: JSONDocumentStore = Depends(get_json_store),
) -> list[dict[str, Any]]:
    """Liste toutes les instructions agent triées par ordre croissant."""
    items = await store.read_list(AGENT_INSTRUCTIONS_FILE.name)
    items.sort(key=lambda x: int(x.get("order", 0)))
    return items


@router.get("/{instruction_id}", response_model=dict[str, Any])
async def get_agent_instruction(
    instruction_id: str,
    store: JSONDocumentStore = Depends(get_json_store),
) -> dict[str, Any]:
    """Récupère une instruction agent par son identifiant."""
    items = await store.read_list(AGENT_INSTRUCTIONS_FILE.name)
    for it in items:
        if it.get("id") == instruction_id:
            return it
    raise HTTPException(status_code=404, detail="Instruction agent introuvable")


@router.post(
    "",
    response_model=dict[str, Any],
    status_code=201,
    dependencies=[Depends(verify_trusted_origin)],
)
async def create_agent_instruction(
    payload: AgentInstructionCreateRequest,
    store: JSONDocumentStore = Depends(get_json_store),
) -> dict[str, Any]:
    """Crée une nouvelle instruction agent modulaire."""
    inst_id = f"inst_{uuid.uuid4().hex[:8]}"

    async with store.lock_for(AGENT_INSTRUCTIONS_FILE.name):
        items = await store.read_list_unlocked(AGENT_INSTRUCTIONS_FILE.name)

        if payload.order is not None:
            order = payload.order
        else:
            existing_orders = [int(it.get("order", 0)) for it in items]
            order = max(existing_orders) + 1 if existing_orders else 0

        instruction = AgentInstruction(
            id=inst_id,
            title=payload.title.strip(),
            description=payload.description.strip(),
            isActive=payload.isActive,
            referenceAssetUrls=payload.referenceAssetUrls,
            order=order,
        )

        items.append(instruction.model_dump())
        await store.write_list_unlocked(AGENT_INSTRUCTIONS_FILE.name, items)

    return instruction.model_dump()


@router.put(
    "/reorder",
    response_model=list[dict[str, Any]],
    dependencies=[Depends(verify_trusted_origin)],
)
async def reorder_agent_instructions(
    payload: ReorderInstructionsRequest,
    store: JSONDocumentStore = Depends(get_json_store),
) -> list[dict[str, Any]]:
    """Réordonne la liste des instructions agent selon les IDs fournis."""
    async with store.lock_for(AGENT_INSTRUCTIONS_FILE.name):
        items = await store.read_list_unlocked(AGENT_INSTRUCTIONS_FILE.name)
        id_to_item = {it.get("id"): it for it in items}

        reordered: list[dict[str, Any]] = []
        for idx, i_id in enumerate(payload.instructionIds):
            if i_id in id_to_item:
                target = id_to_item[i_id]
                target["order"] = idx
                target["updatedAt"] = _utc_now_iso()
                reordered.append(target)

        # Ajouter les éléments non mentionnés à la fin
        for it in items:
            if it.get("id") not in payload.instructionIds:
                it["order"] = len(reordered)
                reordered.append(it)

        await store.write_list_unlocked(AGENT_INSTRUCTIONS_FILE.name, reordered)

    reordered.sort(key=lambda x: int(x.get("order", 0)))
    return reordered


@router.put(
    "/{instruction_id}",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_trusted_origin)],
)
async def update_agent_instruction(
    instruction_id: str,
    payload: AgentInstructionUpdateRequest,
    store: JSONDocumentStore = Depends(get_json_store),
) -> dict[str, Any]:
    """Met à jour une instruction existante."""
    async with store.lock_for(AGENT_INSTRUCTIONS_FILE.name):
        items = await store.read_list_unlocked(AGENT_INSTRUCTIONS_FILE.name)
        target_idx = -1
        for idx, it in enumerate(items):
            if it.get("id") == instruction_id:
                target_idx = idx
                break

        if target_idx == -1:
            raise HTTPException(status_code=404, detail="Instruction introuvable")

        existing = dict(items[target_idx])
        updates = payload.model_dump(exclude_unset=True)

        for field, value in updates.items():
            if value is not None:
                existing[field] = value.strip() if isinstance(value, str) else value

        existing["updatedAt"] = _utc_now_iso()
        validated = AgentInstruction.model_validate(existing)
        items[target_idx] = validated.model_dump()
        await store.write_list_unlocked(AGENT_INSTRUCTIONS_FILE.name, items)

    return items[target_idx]


@router.patch(
    "/{instruction_id}/toggle",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_trusted_origin)],
)
async def toggle_agent_instruction(
    instruction_id: str,
    store: JSONDocumentStore = Depends(get_json_store),
) -> dict[str, Any]:
    """Bascule l'état actif/inactif d'une instruction."""
    async with store.lock_for(AGENT_INSTRUCTIONS_FILE.name):
        items = await store.read_list_unlocked(AGENT_INSTRUCTIONS_FILE.name)
        target_idx = -1
        for idx, it in enumerate(items):
            if it.get("id") == instruction_id:
                target_idx = idx
                break

        if target_idx == -1:
            raise HTTPException(status_code=404, detail="Instruction introuvable")

        current_active = bool(items[target_idx].get("isActive", True))
        items[target_idx]["isActive"] = not current_active
        items[target_idx]["updatedAt"] = _utc_now_iso()
        await store.write_list_unlocked(AGENT_INSTRUCTIONS_FILE.name, items)

    return {"id": instruction_id, "isActive": items[target_idx]["isActive"]}


@router.delete(
    "/{instruction_id}",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_trusted_origin)],
)
async def delete_agent_instruction(
    instruction_id: str,
    store: JSONDocumentStore = Depends(get_json_store),
) -> dict[str, Any]:
    """Supprime une instruction agent."""
    async with store.lock_for(AGENT_INSTRUCTIONS_FILE.name):
        items = await store.read_list_unlocked(AGENT_INSTRUCTIONS_FILE.name)
        rem = [it for it in items if it.get("id") != instruction_id]
        if len(rem) == len(items):
            raise HTTPException(status_code=404, detail="Instruction introuvable")
        await store.write_list_unlocked(AGENT_INSTRUCTIONS_FILE.name, rem)

    return {"deleted": True, "id": instruction_id}
