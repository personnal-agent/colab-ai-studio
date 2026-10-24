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

import asyncio
import mimetypes
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, field_validator

from app.config import (
    ASSETS_DIR,
    BRAND_KITS_FILE,
    CONFIG_FILE,
    DATA_DIR,
    GENERATIONS_FILE,
    OUTPUTS_DIR,
    PROJECTS_FILE,
)
from app.models.domain import HEX_COLOR_REGEX, Project, StudioConfig, TaskStatus
from app.services.brand_extractor import BrandKitExtractor
from app.storage.json_store import JSONDocumentStore
from app.storage.media_store import MediaFileStore

router = APIRouter(prefix="/api", tags=["CRUD"])

# Instances par défaut (surchargées dans les tests via dependency injection ou app.state)
_json_store = JSONDocumentStore(DATA_DIR)
_media_store = MediaFileStore(OUTPUTS_DIR)
_extractor = BrandKitExtractor(ASSETS_DIR)


def get_json_store() -> JSONDocumentStore:
    """Fournisseur de dépendance pour le store JSON partagé."""
    return _json_store


def get_media_store() -> MediaFileStore:
    """Fournisseur de dépendance pour le store média partagé."""
    return _media_store


def verify_trusted_origin(request: Request) -> None:
    """Protection stricte anti-CSRF et contre les écritures cross-origin non sollicitées."""
    sec_site = request.headers.get("sec-fetch-site")
    if sec_site == "cross-site":
        raise HTTPException(
            status_code=403, detail="Requête cross-origin non autorisée (protection CSRF)"
        )
    origin = request.headers.get("origin")
    if origin:
        parsed = urlparse(origin)
        if parsed.hostname not in {"localhost", "127.0.0.1", "testserver", "test"}:
            raise HTTPException(
                status_code=403, detail=f"Origine cross-site non autorisée : '{origin}'"
            )


class ColabUrlUpdate(BaseModel):
    tunnelUrl: str


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    colorTag: str | None = None
    storagePath: str | None = None

    @field_validator("colorTag")
    @classmethod
    def validate_color_tag(cls, v: str | None) -> str | None:
        if v is not None and not HEX_COLOR_REGEX.match(v):
            raise ValueError(f"colorTag doit être un code hexadécimal valide : '{v}'")
        return v.upper() if v else None


# --- Generations ---


@router.get("/generations", response_model=list[dict[str, Any]])
async def list_generations(
    favorite: bool | None = Query(default=None),
    mediaType: str | None = Query(default=None),
    projectId: str | None = Query(default=None),
    q: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    items = await _json_store.read_list("generations.json")
    results = [
        item
        for item in items
        if (favorite is None or item.get("isFavorite") == favorite)
        and (not mediaType or item.get("mediaType") == mediaType)
        and (not projectId or item.get("projectId") == projectId)
        and (
            not q
            or q.lower() in str(item.get("prompt", "")).lower()
            or q.lower() in str(item.get("modelName", "")).lower()
        )
    ]
    results.sort(key=lambda x: str(x.get("createdAt", "")), reverse=True)
    return results


@router.patch(
    "/generations/{generation_id}/favorite",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_trusted_origin)],
)
async def toggle_favorite(generation_id: str) -> dict[str, Any]:
    async with _json_store.lock_for("generations.json"):
        items = await _json_store.read_list_unlocked("generations.json")
        for item in items:
            if item.get("id") == generation_id:
                item["isFavorite"] = not bool(item.get("isFavorite", False))
                await _json_store.write_list_unlocked("generations.json", items)
                return item
    raise HTTPException(status_code=404, detail="Génération introuvable")


@router.delete(
    "/generations/{generation_id}",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_trusted_origin)],
)
async def delete_generation(generation_id: str) -> dict[str, Any]:
    async with _json_store.lock_for("generations.json"):
        items = await _json_store.read_list_unlocked("generations.json")
        target = next((it for it in items if it.get("id") == generation_id), None)
        if target is None:
            raise HTTPException(status_code=404, detail="Génération introuvable")

        try:
            staged = await _media_store.stage_delete_media(
                target.get("filePath"), target.get("thumbnailPath")
            )
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"Échec suppression : {e}") from e

        try:
            rem = [it for it in items if it.get("id") != generation_id]
            await _json_store.write_list_unlocked("generations.json", rem)
        except Exception:
            await _media_store.rollback_delete_media(staged)
            raise

        await _media_store.commit_delete_media(staged)
    return {"deleted": True, "id": generation_id}


def _resolve_existing_file(path_str: str) -> Path | None:
    p = Path(path_str).resolve()
    return p if p.is_file() else None


@router.get("/generations/{generation_id}/file")
async def get_generation_file(generation_id: str) -> FileResponse:
    items = await _json_store.read_list(GENERATIONS_FILE.name)
    gen = next((it for it in items if it.get("id") == generation_id), None)
    if not gen or not gen.get("filePath"):
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    path = await asyncio.to_thread(_resolve_existing_file, gen["filePath"])
    if not path:
        raise HTTPException(status_code=404, detail="Fichier introuvable sur disque")
    media_type, _ = mimetypes.guess_type(str(path))
    return FileResponse(path=path, media_type=media_type or "application/octet-stream")


@router.get("/generations/{generation_id}/thumbnail")
async def get_generation_thumbnail(generation_id: str) -> FileResponse:
    items = await _json_store.read_list(GENERATIONS_FILE.name)
    gen = next((it for it in items if it.get("id") == generation_id), None)
    if not gen or not gen.get("thumbnailPath"):
        raise HTTPException(status_code=404, detail="Miniature introuvable")
    path = await asyncio.to_thread(_resolve_existing_file, gen["thumbnailPath"])
    if not path:
        raise HTTPException(status_code=404, detail="Miniature introuvable sur disque")
    media_type, _ = mimetypes.guess_type(str(path))
    return FileResponse(path=path, media_type=media_type or "image/jpeg")


# --- Brand Kits ---


@router.get("/brand-kits", response_model=list[dict[str, Any]])
async def list_brand_kits() -> list[dict[str, Any]]:
    return await _json_store.read_list(BRAND_KITS_FILE.name)


@router.post(
    "/brand-kits",
    response_model=dict[str, Any],
    status_code=201,
    dependencies=[Depends(verify_trusted_origin)],
)
async def create_brand_kit(
    name: str = Form(...),
    overview: str = Form(default=""),
    websiteUrl: str | None = Form(default=None),
    files: list[UploadFile] = File(default=[]),
) -> dict[str, Any]:
    if websiteUrl and websiteUrl.strip():
        try:
            new_kit = await _extractor.extract_from_website(name=name, website_url=websiteUrl)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    elif files:
        total_size = 0
        file_tuples: list[tuple[str, bytes]] = []
        for f in files:
            chunks: list[bytes] = []
            while chunk := await f.read(1024 * 1024):
                total_size += len(chunk)
                if total_size > 50 * 1024 * 1024:
                    raise HTTPException(
                        status_code=413, detail="Taille cumulée des fichiers supérieure à 50 Mo"
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


@router.post(
    "/projects",
    response_model=dict[str, Any],
    status_code=201,
    dependencies=[Depends(verify_trusted_origin)],
)
async def create_project(payload: ProjectCreate) -> dict[str, Any]:
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
        except (FileExistsError, NotADirectoryError) as e:
            raise HTTPException(status_code=422, detail="storagePath inutilisable") from e

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


@router.delete(
    "/projects/{project_id}",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_trusted_origin)],
)
async def delete_project(project_id: str) -> dict[str, Any]:
    async with _json_store.lock_for(PROJECTS_FILE.name):
        projects = await _json_store.read_list_unlocked(PROJECTS_FILE.name)
        new_projects = [p for p in projects if p.get("id") != project_id]
        if len(new_projects) == len(projects):
            raise HTTPException(status_code=404, detail="Projet introuvable")
        await _json_store.write_list_unlocked(PROJECTS_FILE.name, new_projects)
    return {"deleted": True, "id": project_id}


# --- Configuration ---


@router.post(
    "/config/colab-url",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_trusted_origin)],
)
async def update_colab_url(payload: ColabUrlUpdate) -> Any:
    from app.api.routes_generation import get_task_orchestrator

    orchestrator = get_task_orchestrator()
    async with orchestrator.coordination_lock:
        async with _json_store.lock_for(CONFIG_FILE.name):
            generations = await _json_store.read_list(GENERATIONS_FILE.name)
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
                            "Impossible de modifier le tunnel Colab pendant une tâche en cours"
                        ),
                        "activeTaskIds": active_tasks,
                    },
                )

            cfg = await _json_store.read_dict_unlocked(
                CONFIG_FILE.name, default=StudioConfig().model_dump()
            )
            cfg.setdefault("colab", {})["tunnelUrl"] = payload.tunnelUrl.strip()
            await _json_store.write_dict_unlocked(CONFIG_FILE.name, cfg)
        return {"updated": True, "tunnelUrl": payload.tunnelUrl.strip()}
