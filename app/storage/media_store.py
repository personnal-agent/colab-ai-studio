"""Gestionnaire de persistance des fichiers médias (outputs/ et personnalisés).

Conformité SPECIFICATION.md §4.2.3 :
- Stockage exclusif dans Project.storagePath si défini (aucun fichier dans outputs/).
- Stockage sous outputs/projects/<id>/ si projet sans storagePath.
- Stockage chronologique sous outputs/YYYY-MM-DD/ si génération orpheline.
- Sécurité anti-traversée absolue sur les répertoires protégés.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import REPO_ROOT
from app.models.domain import Project

_SYSTEM_DIRS = tuple(
    Path(p).resolve() for p in ("/etc", "/proc", "/sys", "/dev", "/bin", "/sbin", "/usr")
)
_VAR_DIR = Path("/var").resolve()
_MACOS_TEMP_DIR = Path("/var/folders").resolve()
_REPO_DIRS = (".git", ".githooks", ".gouvernance", ".GCC")
_FORBIDDEN_REPO_PATHS = tuple((REPO_ROOT / p).resolve() for p in _REPO_DIRS)
FORBIDDEN_PATHS = (*_SYSTEM_DIRS, _VAR_DIR, *_FORBIDDEN_REPO_PATHS)


def _atomic_write_bytes(dest: Path, data: bytes) -> None:
    tmp = dest.with_suffix(f".{uuid.uuid4().hex[:8]}.tmp")
    try:
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, dest)
    except Exception:
        with contextlib.suppress(OSError):
            if tmp.exists():
                os.unlink(tmp)
        raise
    if os.name == "posix":
        dir_fd = os.open(dest.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)


class MediaFileStore:
    def __init__(self, outputs_dir: Path | str) -> None:
        self.outputs_dir = Path(outputs_dir)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def resolve_destination_dir(self, project: Project | None = None) -> Path:
        if project and project.storagePath:
            raw_str = str(project.storagePath).strip()
            resolved = Path(raw_str).expanduser().resolve()
            # 1. Protection absolue des dossiers critiques du dépôt (sans exception)
            if (
                any(p in _REPO_DIRS for p in resolved.parts)
                or raw_str in _REPO_DIRS
                or any(resolved == p or resolved.is_relative_to(p) for p in _FORBIDDEN_REPO_PATHS)
            ):
                raise ValueError(
                    f"Chemin storagePath interdit pour raisons de sécurité : {project.storagePath}"
                )
            # 2. Protection des répertoires système Linux/POSIX
            if any(resolved == p or resolved.is_relative_to(p) for p in _SYSTEM_DIRS):
                raise ValueError(
                    f"Chemin storagePath interdit pour raisons de sécurité : {project.storagePath}"
                )
            # 3. Protection stricte de /var (seul /var/folders exempté)
            if (resolved == _VAR_DIR or resolved.is_relative_to(_VAR_DIR)) and not (
                resolved == _MACOS_TEMP_DIR or resolved.is_relative_to(_MACOS_TEMP_DIR)
            ):
                raise ValueError(
                    f"Chemin storagePath interdit pour raisons de sécurité : {project.storagePath}"
                )
            # 4. Protection contre les fichiers existants
            if resolved.exists() and not resolved.is_dir():
                raise ValueError(
                    f"Chemin storagePath interdit pour raisons de sécurité : {project.storagePath}"
                )
            resolved.mkdir(parents=True, exist_ok=True)
            return resolved

        if project and project.id:
            dest = (self.outputs_dir / "projects" / project.id).resolve()
            dest.mkdir(parents=True, exist_ok=True)
            return dest

        today_slug = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        dest = (self.outputs_dir / today_slug).resolve()
        dest.mkdir(parents=True, exist_ok=True)
        return dest

    async def save_media(
        self,
        filename: str,
        content: bytes,
        project: Project | None = None,
        thumbnail_content: bytes | None = None,
    ) -> tuple[str, str | None]:
        dest_dir = self.resolve_destination_dir(project)

        def _sync_save() -> tuple[str, str | None]:
            media_path = dest_dir / Path(filename).name
            _atomic_write_bytes(media_path, content)

            thumb_path_str: str | None = None
            if thumbnail_content is not None:
                thumb_dir = dest_dir / "thumbnails"
                thumb_dir.mkdir(parents=True, exist_ok=True)
                thumb_path = thumb_dir / f"{media_path.name}.thumb.jpg"
                _atomic_write_bytes(thumb_path, thumbnail_content)
                thumb_path_str = str(thumb_path.resolve())

            return str(media_path.resolve()), thumb_path_str

        return await asyncio.to_thread(_sync_save)

    async def stage_delete_media(
        self, file_path: str | None, thumbnail_path: str | None = None
    ) -> list[tuple[Path, Path]]:
        def _sync_stage() -> list[tuple[Path, Path]]:
            staged: list[tuple[Path, Path]] = []
            for path_str in (file_path, thumbnail_path):
                if path_str:
                    orig = Path(path_str)
                    if orig.exists():
                        target = orig.with_name(f".{orig.name}.{uuid.uuid4().hex[:8]}.del")
                        os.replace(orig, target)
                        staged.append((orig, target))
            return staged

        return await asyncio.to_thread(_sync_stage)

    async def commit_delete_media(self, staged_moves: list[tuple[Path, Path]]) -> None:
        def _sync_commit():
            for _, staged_path in staged_moves:
                if staged_path.exists():
                    staged_path.unlink()

        await asyncio.to_thread(_sync_commit)

    async def rollback_delete_media(self, staged_moves: list[tuple[Path, Path]]) -> None:
        def _sync_rollback():
            for orig_path, staged_path in staged_moves:
                with contextlib.suppress(OSError):
                    if staged_path.exists():
                        os.replace(staged_path, orig_path)

        await asyncio.to_thread(_sync_rollback)

    async def delete_media(self, file_path: str | None, thumbnail_path: str | None = None) -> bool:
        staged = await self.stage_delete_media(file_path, thumbnail_path)
        await self.commit_delete_media(staged)
        return bool(staged)
