"""Routes CRUD et compilateur d'identité pour les Fiches Personnages (@Character) (Module B)."""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.routes_crud import get_json_store, verify_trusted_origin
from app.config import CHARACTERS_FILE
from app.models.domain import Character, CharacterArchetype, EnginePreference, _utc_now_iso
from app.storage.json_store import JSONDocumentStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Characters"])


class CharacterCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Nom du personnage (ex: Tomate, Clara)")
    triggerToken: str | None = Field(default=None, description="Token d'invocation (ex: @Tomate)")
    physicalPrompt: str = Field(
        ...,
        min_length=3,
        description="Description morphologique, texture de peau et tenue fixe",
    )
    referenceImagePath: str | None = None
    voiceSamplePath: str | None = None
    voiceStyle: str | None = "feminine_soft"
    voiceProfileId: str | None = None
    archetype: CharacterArchetype = CharacterArchetype.THE_FAMILIAR
    visualAnchors: list[str] = Field(default_factory=list)
    enginePreference: EnginePreference = "local"
    loraName: str | None = None
    loraStrength: float = 0.85
    defaultSeed: int | None = None


class CharacterUpdateRequest(BaseModel):
    name: str | None = None
    triggerToken: str | None = None
    physicalPrompt: str | None = None
    referenceImagePath: str | None = None
    voiceSamplePath: str | None = None
    voiceStyle: str | None = None
    voiceProfileId: str | None = None
    archetype: CharacterArchetype | None = None
    visualAnchors: list[str] | None = None
    enginePreference: EnginePreference | None = None
    loraName: str | None = None
    loraStrength: float | None = None
    defaultSeed: int | None = None


def normalize_trigger_token(name: str, custom_token: str | None = None) -> str:
    """Normalise un token d'invocation sous la forme @NomSansEspace."""
    raw = (custom_token or name).strip()
    clean = re.sub(r"\s+", "_", raw.lstrip("@"))
    return f"@{clean}" if clean else "@Character"


def compile_character_mentions(
    prompt: str, characters_raw: list[dict[str, Any]]
) -> tuple[str, list[str], list[str], int | None]:
    """Détecte les mentions @Personnage dans un prompt et injecte leur identité fixe.

    Retourne:
        (compiled_prompt, matched_character_ids, matched_image_refs, suggested_seed)
    """
    if not prompt or not characters_raw:
        return prompt, [], [], None

    compiled = prompt
    matched_ids: list[str] = []
    matched_images: list[str] = []
    suggested_seed: int | None = None

    for raw in characters_raw:
        try:
            char = Character.model_validate(raw)
        except Exception as exc:
            logger.debug("Validation personnage ignorée: %s", exc)
            continue

        token = char.triggerToken.strip()
        alt_token = f"@{char.name.strip()}"
        pattern = re.compile(
            rf"(?<!\w)({re.escape(token)}|{re.escape(alt_token)})(?!\w)",
            re.IGNORECASE,
        )
        if pattern.search(compiled):
            matched_ids.append(char.id)
            if char.referenceImagePath and char.referenceImagePath not in matched_images:
                matched_images.append(char.referenceImagePath)
            if suggested_seed is None and char.defaultSeed and char.defaultSeed > 0:
                suggested_seed = char.defaultSeed

            # Remplace @Nom par le nom du personnage dans le corps du texte
            compiled = pattern.sub(char.name, compiled)
            if char.visualAnchors:
                anchors_str = ", ".join(char.visualAnchors)
                anchors_block = f"[Visual Anchors for {char.name}: {anchors_str}]"
                if anchors_block.lower() not in compiled.lower():
                    compiled = f"{anchors_block} {compiled}"

            identity_block = f"[{char.name} Identity: {char.physicalPrompt.strip()}]"
            if char.physicalPrompt.strip().lower() not in compiled.lower():
                compiled = f"{identity_block} {compiled}"

    return compiled, matched_ids, matched_images, suggested_seed


@router.get("/characters", response_model=list[dict[str, Any]])
async def list_characters(
    archetype: CharacterArchetype | None = None,
    store: JSONDocumentStore = Depends(get_json_store),
) -> list[dict[str, Any]]:
    """Liste toutes les fiches personnages enregistrées localement."""
    items = await store.read_list(CHARACTERS_FILE.name)
    if archetype is not None:
        arch_val = archetype.value if hasattr(archetype, "value") else str(archetype)
        items = [c for c in items if c.get("archetype") == arch_val]
    items.sort(key=lambda x: str(x.get("createdAt", "")), reverse=True)
    return items


@router.get("/characters/{character_id}", response_model=dict[str, Any])
async def get_character(
    character_id: str,
    store: JSONDocumentStore = Depends(get_json_store),
) -> dict[str, Any]:
    """Récupère une fiche personnage par son identifiant unique."""
    chars = await store.read_list(CHARACTERS_FILE.name)
    for c in chars:
        if c.get("id") == character_id:
            return c
    raise HTTPException(status_code=404, detail="Personnage introuvable")


@router.post(
    "/characters",
    response_model=dict[str, Any],
    status_code=201,
    dependencies=[Depends(verify_trusted_origin)],
)
async def create_character(
    payload: CharacterCreateRequest,
    store: JSONDocumentStore = Depends(get_json_store),
) -> dict[str, Any]:
    """Crée une nouvelle fiche personnage réutilisable via @Nom."""
    char_id = f"char_{uuid.uuid4().hex[:8]}"
    trigger = normalize_trigger_token(payload.name, payload.triggerToken)

    character = Character(
        id=char_id,
        name=payload.name.strip(),
        triggerToken=trigger,
        physicalPrompt=payload.physicalPrompt.strip(),
        referenceImagePath=payload.referenceImagePath,
        voiceSamplePath=payload.voiceSamplePath,
        voiceStyle=payload.voiceStyle or "feminine_soft",
        voiceProfileId=payload.voiceProfileId,
        archetype=payload.archetype,
        visualAnchors=payload.visualAnchors,
        enginePreference=payload.enginePreference,
        loraName=payload.loraName,
        loraStrength=payload.loraStrength,
        defaultSeed=payload.defaultSeed,
    )

    async with store.lock_for(CHARACTERS_FILE.name):
        chars = await store.read_list_unlocked(CHARACTERS_FILE.name)
        chars.insert(0, character.model_dump())
        await store.write_list_unlocked(CHARACTERS_FILE.name, chars)

    return character.model_dump()


@router.put(
    "/characters/{character_id}",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_trusted_origin)],
)
async def update_character(
    character_id: str,
    payload: CharacterUpdateRequest,
    store: JSONDocumentStore = Depends(get_json_store),
) -> dict[str, Any]:
    """Met à jour une fiche personnage existante de façon atomique."""
    async with store.lock_for(CHARACTERS_FILE.name):
        chars = await store.read_list_unlocked(CHARACTERS_FILE.name)
        target_idx = -1
        for idx, c in enumerate(chars):
            if c.get("id") == character_id:
                target_idx = idx
                break

        if target_idx == -1:
            raise HTTPException(status_code=404, detail="Personnage introuvable")

        existing = dict(chars[target_idx])
        updates = payload.model_dump(exclude_unset=True)

        if "name" in updates and updates["name"]:
            existing["name"] = updates["name"].strip()
            if "triggerToken" not in updates:
                existing["triggerToken"] = normalize_trigger_token(existing["name"])

        for field, value in updates.items():
            if field != "name" and value is not None:
                if hasattr(value, "value"):
                    existing[field] = value.value
                else:
                    existing[field] = value

        existing["updatedAt"] = _utc_now_iso()
        # Valider avec le modèle de domaine Character
        validated = Character.model_validate(existing)
        chars[target_idx] = validated.model_dump()
        await store.write_list_unlocked(CHARACTERS_FILE.name, chars)

    return chars[target_idx]


@router.delete(
    "/characters/{character_id}",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_trusted_origin)],
)
async def delete_character(
    character_id: str,
    store: JSONDocumentStore = Depends(get_json_store),
) -> dict[str, Any]:
    """Supprime une fiche personnage par son identifiant."""
    async with store.lock_for(CHARACTERS_FILE.name):
        chars = await store.read_list_unlocked(CHARACTERS_FILE.name)
        rem = [c for c in chars if c.get("id") != character_id]
        if len(rem) == len(chars):
            raise HTTPException(status_code=404, detail="Personnage introuvable")
        await store.write_list_unlocked(CHARACTERS_FILE.name, rem)

    return {"deleted": True, "id": character_id}
