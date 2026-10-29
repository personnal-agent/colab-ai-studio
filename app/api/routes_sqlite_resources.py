"""
FastAPI router for .hilo/index.sqlite resource_v3 indexation and schema inspection.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.storage.sqlite_repository import (
    HiloSQLiteRepository,
    ResourceCollisionError,
    get_hilo_sqlite_repo,
)

router = APIRouter(prefix="/api/resources", tags=["Resources V3"])


class ResourceCreateRequest(BaseModel):
    workspace_id: str = Field(..., description="Target workspace ID")
    generation_id: str = Field(..., description="Generation task ID")
    artifact_id: str = Field(..., description="Artifact identifier")
    file_path: str = Field(..., description="Resolved storage path")
    sha256_digest: str = Field(..., description="SHA-256 integrity hash")
    byte_size: int = Field(..., ge=0, description="Payload byte size")
    mime_type: str = Field(..., description="MIME content type")
    media_type: str = Field(..., description="Logical media category")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata attributes")


@router.get("", summary="List indexed resources in workspace")
async def list_resources(
    workspace_id: str = Query("default", description="Workspace ID"),
    media_type: str | None = Query(None, description="Filter by media category"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    repo: HiloSQLiteRepository = Depends(get_hilo_sqlite_repo),
) -> dict[str, Any]:
    resources = await repo.list_resources(
        workspace_id=workspace_id,
        media_type=media_type,
        limit=limit,
        offset=offset,
    )
    return {
        "workspace_id": workspace_id,
        "media_type": media_type,
        "count": len(resources),
        "items": [
            {
                "id": r.id,
                "workspace_id": r.workspace_id,
                "generation_id": r.generation_id,
                "artifact_id": r.artifact_id,
                "file_path": r.file_path,
                "sha256_digest": r.sha256_digest,
                "byte_size": r.byte_size,
                "mime_type": r.mime_type,
                "media_type": r.media_type,
                "metadata": r.metadata,
                "status": r.status,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            }
            for r in resources
        ],
    }


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Atomically index resource in resource_v3",
)
async def register_resource(
    payload: ResourceCreateRequest,
    repo: HiloSQLiteRepository = Depends(get_hilo_sqlite_repo),
) -> dict[str, Any]:
    try:
        record = await repo.register_resource(
            workspace_id=payload.workspace_id,
            generation_id=payload.generation_id,
            artifact_id=payload.artifact_id,
            file_path=payload.file_path,
            sha256_digest=payload.sha256_digest,
            byte_size=payload.byte_size,
            mime_type=payload.mime_type,
            media_type=payload.media_type,
            metadata=payload.metadata,
        )
        return {
            "id": record.id,
            "workspace_id": record.workspace_id,
            "generation_id": record.generation_id,
            "artifact_id": record.artifact_id,
            "file_path": record.file_path,
            "sha256_digest": record.sha256_digest,
            "byte_size": record.byte_size,
            "mime_type": record.mime_type,
            "media_type": record.media_type,
            "metadata": record.metadata,
            "status": record.status,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }
    except ResourceCollisionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "/{workspace_id}/{generation_id}/{artifact_id}",
    summary="Retrieve single resource by unique key",
)
async def get_resource(
    workspace_id: str,
    generation_id: str,
    artifact_id: str,
    repo: HiloSQLiteRepository = Depends(get_hilo_sqlite_repo),
) -> dict[str, Any]:
    rec = await repo.get_resource(
        workspace_id=workspace_id,
        generation_id=generation_id,
        artifact_id=artifact_id,
    )
    if rec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Resource not found: workspace='{workspace_id}', "
                f"generation='{generation_id}', artifact='{artifact_id}'"
            ),
        )
    return {
        "id": rec.id,
        "workspace_id": rec.workspace_id,
        "generation_id": rec.generation_id,
        "artifact_id": rec.artifact_id,
        "file_path": rec.file_path,
        "sha256_digest": rec.sha256_digest,
        "byte_size": rec.byte_size,
        "mime_type": rec.mime_type,
        "media_type": rec.media_type,
        "metadata": rec.metadata,
        "status": rec.status,
        "created_at": rec.created_at,
        "updated_at": rec.updated_at,
    }


@router.get("/schema-status", summary="Diagnostic inspection of SQLite WAL schema")
async def get_schema_status(
    repo: HiloSQLiteRepository = Depends(get_hilo_sqlite_repo),
) -> dict[str, Any]:
    journal_mode = await repo.get_pragma("journal_mode")
    foreign_keys = await repo.get_pragma("foreign_keys")
    migrations = await repo.get_applied_migrations()
    tables = await repo.get_table_names()
    app_tables = [t for t in tables if t not in ("schema_migrations", "sqlite_sequence")]

    return {
        "database_path": str(repo.db_path),
        "journal_mode": journal_mode,
        "foreign_keys_enabled": foreign_keys in (1, "1"),
        "migrations_count": len(migrations),
        "application_tables_count": len(app_tables),
        "tables": app_tables,
    }
