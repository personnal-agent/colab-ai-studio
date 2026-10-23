"""Gestionnaire de fichiers médias et d'isolation physique de stockage (MediaFileStore).

Règles strictes de destination (SPECIFICATION.md §4.2.3 et Plan 01 Step 4) :
1. Si Project.storagePath est renseigné : sauvegarde exclusive dans ce dossier,
   avec 0 fichier créé dans outputs/.
2. Si le projet n'a pas de storagePath : outputs/projects/<id>/.
3. Si la génération est hors projet : outputs/YYYY-MM-DD/ (partition chronologique).
4. Sécurité anti-traversée : rejet strict des répertoires système sensibles.
"""

from __future__ import annotations

import contextlib
import os
from datetime import datetime, timezone
from pathlib import Path

from app.models.domain import Project

FORBIDDEN_PREFIXES = (
    "/etc",
    "/proc",
    "/sys",
    "/dev",
    "/bin",
    "/sbin",
    "/usr",
    "/var",
    ".git",
    ".githooks",
    ".gouvernance",
    ".GCC",
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
            resolved_str = str(resolved)
            for prefix in FORBIDDEN_PREFIXES:
                if resolved_str == prefix or resolved_str.startswith(f"{prefix}/"):
                    msg = (
                        "Chemin storagePath interdit pour raisons de sécurité : "
                        f"{project.storagePath}"
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
        media_path = dest_dir / Path(filename).name

        # Écriture atomique avec synchro disque
        tmp_media = media_path.with_suffix(f"{media_path.suffix}.tmp")
        tmp_media.write_bytes(content)
        os.replace(tmp_media, media_path)

        thumb_path_str: str | None = None
        if thumbnail_content is not None:
            thumb_dir = dest_dir / "thumbnails"
            thumb_dir.mkdir(parents=True, exist_ok=True)
            stem = media_path.stem
            thumb_path = thumb_dir / f"{stem}.jpg"
            tmp_thumb = thumb_path.with_suffix(".tmp")
            tmp_thumb.write_bytes(thumbnail_content)
            os.replace(tmp_thumb, thumb_path)
            thumb_path_str = str(thumb_path.resolve())

        return str(media_path.resolve()), thumb_path_str

    async def delete_media(
        self,
        file_path: str | None,
        thumbnail_path: str | None = None,
    ) -> bool:
        def _sync_delete() -> bool:
            deleted_any = False
            if file_path:
                with contextlib.suppress(OSError):
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        deleted_any = True
            if thumbnail_path:
                with contextlib.suppress(OSError):
                    if os.path.isfile(thumbnail_path):
                        os.unlink(thumbnail_path)
                        deleted_any = True
            return deleted_any

        import asyncio

        return await asyncio.to_thread(_sync_delete)
