"""Routeurs CRUD documentaires pour Colab AI Studio (app/api/routes_crud.py).

Expose :
- GET /api/generations (filtres : favorite, mediaType, projectId, q)
- PATCH /api/generations/{id}/favorite
- DELETE /api/generations/{id} (suppression atomique JSON + fichiers via MediaFileStore)
- GET /api/brand-kits
- POST /api/brand-kits (Blank, files, website)
- GET /api/projects
- POST /api/projects
- POST /api/config/colab-url
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.config import (
    ASSETS_DIR,
    BRAND_KITS_FILE,
    CONFIG_FILE,
    DATA_DIR,
    OUTPUTS_DIR,
    PROJECTS_FILE,
)
from app.models.domain import Project, StudioConfig
from app.services.brand_extractor import BrandKitExtractor
from app.storage.json_store import JSONDocumentStore
from app.storage.media_store import MediaFileStore

router = APIRouter(prefix="/api", tags=["CRUD"])

# Instances par défaut (surchargées dans les tests via dependency injection ou app.state)
_json_store = JSONDocumentStore(DATA_DIR)
_media_store = MediaFileStore(OUTPUTS_DIR)
_extractor = BrandKitExtractor(ASSETS_DIR)


class ColabUrlUpdate(BaseModel):
    tunnelUrl: str


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    colorTag: str | None = None
    storagePath: str | None = None


# --- Generations ---


@router.get("/generations", response_model=list[dict[str, Any]])
async def list_generations(
    favorite: bool | None = Query(default=None),
    mediaType: str | None = Query(default=None),
    projectId: str | None = Query(default=None),
    q: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    items = await _json_store.read_list("generations.json")
    results: list[dict[str, Any]] = []

    for item in items:
        if favorite is not None and item.get("isFavorite") != favorite:
            continue
        if mediaType and item.get("mediaType") != mediaType:
            continue
        if projectId and item.get("projectId") != projectId:
            continue
        if q:
            query_lower = q.lower()
            prompt = str(item.get("prompt", "")).lower()
            model = str(item.get("modelName", "")).lower()
            if query_lower not in prompt and query_lower not in model:
                continue
        results.append(item)

    # Tri antichronologique
    results.sort(key=lambda x: str(x.get("createdAt", "")), reverse=True)
    return results


@router.patch("/generations/{generation_id}/favorite", response_model=dict[str, Any])
async def toggle_favorite(generation_id: str) -> dict[str, Any]:
    async with _json_store.lock_for("generations.json"):
        items = await _json_store.read_list_unlocked("generations.json")
        for item in items:
            if item.get("id") == generation_id:
                current_fav = bool(item.get("isFavorite", False))
                item["isFavorite"] = not current_fav
                await _json_store.write_list_unlocked("generations.json", items)
                return item
    raise HTTPException(status_code=404, detail="Génération introuvable")


@router.delete("/generations/{generation_id}", response_model=dict[str, Any])
async def delete_generation(generation_id: str) -> dict[str, Any]:
    target_item: dict[str, Any] | None = None
    async with _json_store.lock_for("generations.json"):
        items = await _json_store.read_list_unlocked("generations.json")
        remaining: list[dict[str, Any]] = []
        for item in items:
            if item.get("id") == generation_id:
                target_item = item
            else:
                remaining.append(item)
        if target_item is None:
            raise HTTPException(status_code=404, detail="Génération introuvable")
        await _json_store.write_list_unlocked("generations.json", remaining)

    # Suppression physique sur disque
    await _media_store.delete_media(
        file_path=target_item.get("filePath"),
        thumbnail_path=target_item.get("thumbnailPath"),
    )
    return {"deleted": True, "id": generation_id}


# --- Brand Kits ---


@router.get("/brand-kits", response_model=list[dict[str, Any]])
async def list_brand_kits() -> list[dict[str, Any]]:
    return await _json_store.read_list(BRAND_KITS_FILE.name)


@router.post("/brand-kits", response_model=dict[str, Any], status_code=201)
async def create_brand_kit(
    name: str = Form(...),
    overview: str = Form(default=""),
    websiteUrl: str | None = Form(default=None),
    files: list[UploadFile] = File(default=[]),
) -> dict[str, Any]:
    if websiteUrl and websiteUrl.strip():
        new_kit = await _extractor.extract_from_website(name=name, website_url=websiteUrl)
    elif files:
        total_size = 0
        max_upload_size = 50 * 1024 * 1024  # 50 Mo aggregate cap
        file_tuples: list[tuple[str, bytes]] = []
        for f in files:
            chunks = []
            while chunk := await f.read(1024 * 1024):
                total_size += len(chunk)
                if total_size > max_upload_size:
                    raise HTTPException(
                        status_code=413,
                        detail="Taille cumulée des fichiers supérieure à 50 Mo",
                    )
                chunks.append(chunk)
            file_tuples.append((f.filename or "upload", b"".join(chunks)))
        new_kit = await _extractor.extract_from_files(
            name=name, files=file_tuples, overview=overview
        )
    else:
        new_kit = _extractor.create_blank(name=name, overview=overview)

    async with _json_store.lock_for(BRAND_KITS_FILE.name):
        kits = await _json_store.read_list_unlocked(BRAND_KITS_FILE.name)
        kits.append(new_kit.model_dump())
        await _json_store.write_list_unlocked(BRAND_KITS_FILE.name, kits)

    return new_kit.model_dump()


# --- Projects ---


@router.get("/projects", response_model=list[dict[str, Any]])
async def list_projects() -> list[dict[str, Any]]:
    return await _json_store.read_list(PROJECTS_FILE.name)


@router.post("/projects", response_model=dict[str, Any], status_code=201)
async def create_project(payload: ProjectCreate) -> dict[str, Any]:
    import asyncio
    import uuid

    proj_id = f"proj_{uuid.uuid4().hex[:8]}"
    storage_path = payload.storagePath
    if storage_path:
        dummy_project = Project(id=proj_id, name=payload.name, storagePath=storage_path)
        try:
            resolved_dest = await asyncio.to_thread(
                _media_store.resolve_destination_dir, project=dummy_project
            )
            storage_path = str(resolved_dest)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

    project = Project(
        id=proj_id,
        name=payload.name,
        description=payload.description,
        colorTag=payload.colorTag,
        storagePath=storage_path,
    )

    async with _json_store.lock_for(PROJECTS_FILE.name):
        projects = await _json_store.read_list_unlocked(PROJECTS_FILE.name)
        projects.append(project.model_dump())
        await _json_store.write_list_unlocked(PROJECTS_FILE.name, projects)

    return project.model_dump()


# --- Configuration ---


@router.post("/config/colab-url", response_model=dict[str, Any])
async def update_colab_url(payload: ColabUrlUpdate) -> dict[str, Any]:
    async with _json_store.lock_for(CONFIG_FILE.name):
        raw_config = await _json_store.read_dict_unlocked(
            CONFIG_FILE.name, default=StudioConfig().model_dump()
        )
        if "colab" not in raw_config:
            raw_config["colab"] = {}
        raw_config["colab"]["tunnelUrl"] = payload.tunnelUrl.strip()
        await _json_store.write_dict_unlocked(CONFIG_FILE.name, raw_config)
    return {"updated": True, "tunnelUrl": payload.tunnelUrl.strip()}
