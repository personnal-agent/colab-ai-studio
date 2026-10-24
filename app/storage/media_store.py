"""Gestionnaire de fichiers médias et d'isolation physique de stockage (MediaFileStore).

Règles strictes de destination (SPECIFICATION.md §4.2.3 et Plan 01 Step 4) :
1. Si Project.storagePath est renseigné : sauvegarde exclusive dans ce dossier,
   avec 0 fichier créé dans outputs/.
2. Si le projet n'a pas de storagePath : outputs/projects/<id>/.
3. Si la génération est hors projet : outputs/YYYY-MM-DD/ (partition chronologique).
4. Sécurité anti-traversée : rejet strict des répertoires système sensibles.
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

_SYSTEM_DIRS = ("/etc", "/proc", "/sys", "/dev", "/bin", "/sbin", "/usr", "/var")
_REPO_DIRS = (".git", ".githooks", ".gouvernance", ".GCC")
FORBIDDEN_PATHS = (
    *(Path(path).resolve() for path in _SYSTEM_DIRS),
    *((REPO_ROOT / path).resolve() for path in _REPO_DIRS),
)


class MediaFileStore:
    def __init__(self, outputs_dir: Path | str) -> None:
        self.outputs_dir = Path(outputs_dir).resolve()
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def resolve_destination_dir(self, project: Project | None = None) -> Path:
        if project and project.storagePath:
            raw_path = Path(project.storagePath)
            # Sécurité anti-traversée
            resolved = raw_path.expanduser().resolve()
            if any(resolved.is_relative_to(path) for path in FORBIDDEN_PATHS):
                msg = (
                    f"Chemin storagePath interdit pour raisons de sécurité : {project.storagePath}"
                )
                raise ValueError(msg)
            resolved.mkdir(parents=True, exist_ok=True)
            return resolved

        if project and project.id:
            dest = (self.outputs_dir / "projects" / project.id).resolve()
            dest.mkdir(parents=True, exist_ok=True)
            return dest

        # Hors projet : partitionnement chronologique YYYY-MM-DD
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

            # Écriture atomique avec synchro disque et temporaire unique
            tmp_media = media_path.with_suffix(f".{uuid.uuid4().hex[:8]}.tmp")
            try:
                with open(tmp_media, "wb") as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_media, media_path)
            except Exception:
                with contextlib.suppress(OSError):
                    if tmp_media.exists():
                        os.unlink(tmp_media)
                raise

            if os.name == "posix":
                dir_fd = os.open(dest_dir, os.O_RDONLY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)

            thumb_path_str: str | None = None
            if thumbnail_content is not None:
                thumb_dir = dest_dir / "thumbnails"
                thumb_dir.mkdir(parents=True, exist_ok=True)
                thumb_path = thumb_dir / f"{media_path.name}.thumb.jpg"
                tmp_thumb = thumb_path.with_suffix(f".{uuid.uuid4().hex[:8]}.tmp")
                try:
                    with open(tmp_thumb, "wb") as f:
                        f.write(thumbnail_content)
                        f.flush()
                        os.fsync(f.fileno())
                    os.replace(tmp_thumb, thumb_path)
                except Exception:
                    with contextlib.suppress(OSError):
                        if tmp_thumb.exists():
                            os.unlink(tmp_thumb)
                    raise

                if os.name == "posix":
                    thumb_dir_fd = os.open(thumb_dir, os.O_RDONLY)
                    try:
                        os.fsync(thumb_dir_fd)
                    finally:
                        os.close(thumb_dir_fd)

                thumb_path_str = str(thumb_path.resolve())

            return str(media_path.resolve()), thumb_path_str

        return await asyncio.to_thread(_sync_save)

    async def delete_media(
        self,
        file_path: str | None,
        thumbnail_path: str | None = None,
    ) -> bool:
        def _sync_delete() -> bool:
            deleted_any = False
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
                deleted_any = True
            if thumbnail_path and os.path.exists(thumbnail_path):
                os.unlink(thumbnail_path)
                deleted_any = True
            return deleted_any

        return await asyncio.to_thread(_sync_delete)
