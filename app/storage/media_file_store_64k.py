"""Gestionnaire de persistance média par fragments de 64 Ko et publication no-replace.

Conforme à INTEGRATION_PLAN_V3.md § Phase 4 :
- Streaming binaire direct par fragments de 64 Ko vers un temporaire exclusif (O_CREAT | O_EXCL).
- Calcul du digest SHA-256 et du comptage d'octets au vol.
- Journalisation durable d'intention via JSONDocumentStore (journal_staging_no_replace.json).
- Publication atomique sans écrasement (no-replace) via os.link sur le même système de fichiers.
- Compensation et nettoyage chirurgical uniquement sur confirmation d'échec ou abandon.
- Reprise après crash (Crash Recovery) garantissant l'absence d'orphelins ou de corruption.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import os
import uuid
from collections.abc import AsyncIterator, Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models.domain import Project
from app.storage.json_store import JSONDocumentStore
from app.storage.media_store import MediaFileStore

DEFAULT_CHUNK_SIZE = 64 * 1024  # 64 Ko
JOURNAL_FILENAME = "journal_staging_no_replace.json"


class StagingOperationError(RuntimeError):
    """Exception de base pour les erreurs du protocole de publication no-replace."""


class DestinationCollisionError(StagingOperationError):
    """Levée quand le fichier de destination existe déjà (violation no-replace)."""


class StagingIntegrityError(StagingOperationError):
    """Levée en cas de divergence de digest SHA-256 ou de taille de fichier."""


def _fsync_directory_if_supported(dir_path: Path) -> None:
    """Synchronise les métadonnées d'un répertoire sur disque si supporté par l'OS."""
    if os.name == "posix":
        with contextlib.suppress(OSError):
            dir_fd = os.open(dir_path, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)


class MediaFileStore64k(MediaFileStore):
    """Extension de MediaFileStore avec streaming 64 Ko, publication no-replace et journal."""

    def __init__(
        self,
        outputs_dir: Path | str,
        json_store: JSONDocumentStore | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> None:
        super().__init__(outputs_dir)
        self.chunk_size = chunk_size
        self._json_store = json_store or JSONDocumentStore(self.outputs_dir / ".hilo_journal")

    async def stream_write_temp(
        self,
        filename: str,
        chunks: AsyncIterator[bytes] | Iterable[bytes],
        project: Project | None = None,
    ) -> tuple[str, str, int]:
        """Écrit un flux par fragments dans un fichier temporaire exclusif du même dossier."""
        dest_dir = self.resolve_destination_dir(project)
        temp_id = uuid.uuid4().hex[:12]
        safe_name = Path(filename).name
        temp_path = dest_dir / f".{safe_name}.{temp_id}.part"

        def _open_exclusive() -> int:
            flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
            return os.open(temp_path, flags, 0o600)

        fd = await asyncio.to_thread(_open_exclusive)
        hasher = hashlib.sha256()
        total_bytes = 0

        try:
            if hasattr(chunks, "__aiter__"):
                async for chunk in chunks:
                    if chunk:
                        await asyncio.to_thread(os.write, fd, chunk)
                        hasher.update(chunk)
                        total_bytes += len(chunk)
            else:
                for chunk in chunks:
                    if chunk:
                        await asyncio.to_thread(os.write, fd, chunk)
                        hasher.update(chunk)
                        total_bytes += len(chunk)

            # Flush et synchronisation disque
            def _sync_close() -> None:
                os.fsync(fd)
                os.close(fd)
                _fsync_directory_if_supported(dest_dir)

            await asyncio.to_thread(_sync_close)
        except Exception:
            with contextlib.suppress(OSError):
                os.close(fd)
            with contextlib.suppress(OSError):
                if temp_path.exists():
                    temp_path.unlink()
            raise

        digest = hasher.hexdigest()
        temp_resolved = await asyncio.to_thread(lambda: str(temp_path.resolve()))
        return temp_resolved, digest, total_bytes

    async def stage_operation(
        self,
        operation_id: str,
        resource_key: str,
        temp_path: str,
        final_filename: str,
        sha256_digest: str,
        byte_size: int,
        project: Project | None = None,
    ) -> dict[str, Any]:
        """Enregistre l'intention dans le journal durable JSON avec verrou."""
        dest_dir = self.resolve_destination_dir(project)

        def _resolve_paths() -> tuple[str, str]:
            final_p = (dest_dir / Path(final_filename).name).resolve()
            temp_p = Path(temp_path).resolve()
            return str(temp_p), str(final_p)

        temp_resolved, final_resolved = await asyncio.to_thread(_resolve_paths)

        entry: dict[str, Any] = {
            "operationId": operation_id,
            "resourceKey": resource_key,
            "tempPath": temp_resolved,
            "finalPath": final_resolved,
            "sha256Digest": sha256_digest,
            "byteSize": byte_size,
            "status": "STAGED",
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

        async with self._json_store.lock_for(JOURNAL_FILENAME):
            journal = await self._json_store.read_list_unlocked(JOURNAL_FILENAME)
            # Remplacement ou ajout
            journal = [op for op in journal if op.get("operationId") != operation_id]
            journal.append(entry)
            await self._json_store.write_list_unlocked(JOURNAL_FILENAME, journal)

        return entry

    async def publish_no_replace(self, operation_id: str) -> str:
        """Publie le fichier temporaire vers la destination finale via os.link (no-replace)."""
        async with self._json_store.lock_for(JOURNAL_FILENAME):
            journal = await self._json_store.read_list_unlocked(JOURNAL_FILENAME)
            entry = next((op for op in journal if op.get("operationId") == operation_id), None)
            if not entry:
                raise StagingOperationError(f"Opération introuvable : {operation_id}")

            temp_path = Path(entry["tempPath"])
            final_path = Path(entry["finalPath"])
            expected_digest = entry["sha256Digest"]

            def _sync_link_and_verify() -> str:
                if not temp_path.is_file():
                    raise StagingIntegrityError(f"Fichier temporaire manquant : {temp_path}")

                # Si final_path existe déjà, os.link lève FileExistsError sans écrasement
                try:
                    os.link(temp_path, final_path)
                except FileExistsError as err:
                    raise DestinationCollisionError(
                        f"Collision no-replace : la destination '{final_path}' existe déjà"
                    ) from err
                except OSError as err:
                    raise StagingOperationError(
                        f"Échec création du lien no-replace '{final_path}' : {err}"
                    ) from err

                _fsync_directory_if_supported(final_path.parent)

                # Suppression du temporaire
                with contextlib.suppress(OSError):
                    temp_path.unlink()

                _fsync_directory_if_supported(final_path.parent)

                # Vérification finale d'intégrité
                hasher = hashlib.sha256()
                with open(final_path, "rb") as f:
                    while chunk := f.read(DEFAULT_CHUNK_SIZE):
                        hasher.update(chunk)
                if hasher.hexdigest() != expected_digest:
                    raise StagingIntegrityError(
                        f"Digest final divergent pour {final_path} : "
                        f"{hasher.hexdigest()} != {expected_digest}"
                    )

                return str(final_path.resolve())

            published_path = await asyncio.to_thread(_sync_link_and_verify)

            entry["status"] = "PUBLISHED_PENDING_COMMIT"
            entry["publishedAt"] = datetime.now(timezone.utc).isoformat()
            await self._json_store.write_list_unlocked(JOURNAL_FILENAME, journal)
            return published_path

    async def commit_operation(self, operation_id: str) -> None:
        """Marque l'opération comme COMMITTED après confirmation de l'indexation SQLite."""
        async with self._json_store.lock_for(JOURNAL_FILENAME):
            journal = await self._json_store.read_list_unlocked(JOURNAL_FILENAME)
            entry = next((op for op in journal if op.get("operationId") == operation_id), None)
            if entry:
                entry["status"] = "COMMITTED"
                entry["committedAt"] = datetime.now(timezone.utc).isoformat()
                await self._json_store.write_list_unlocked(JOURNAL_FILENAME, journal)

    async def abort_and_compensate(self, operation_id: str) -> None:
        """Nettoie chirurgicalement l'opération avortée sans impacter les fichiers préexistants."""
        async with self._json_store.lock_for(JOURNAL_FILENAME):
            journal = await self._json_store.read_list_unlocked(JOURNAL_FILENAME)
            entry = next((op for op in journal if op.get("operationId") == operation_id), None)
            if not entry:
                return

            temp_path = Path(entry["tempPath"])
            final_path = Path(entry["finalPath"])
            expected_digest = entry["sha256Digest"]

            def _sync_cleanup() -> None:
                # 1. Nettoyage du temporaire si encore présent
                if temp_path.exists():
                    with contextlib.suppress(OSError):
                        temp_path.unlink()

                # 2. Nettoyage de la destination finale UNIQUEMENT si son digest correspond
                if final_path.is_file():
                    hasher = hashlib.sha256()
                    with open(final_path, "rb") as f:
                        while chunk := f.read(DEFAULT_CHUNK_SIZE):
                            hasher.update(chunk)
                    if hasher.hexdigest() == expected_digest:
                        with contextlib.suppress(OSError):
                            final_path.unlink()
                            _fsync_directory_if_supported(final_path.parent)

            await asyncio.to_thread(_sync_cleanup)

            entry["status"] = "ABORTED"
            entry["abortedAt"] = datetime.now(timezone.utc).isoformat()
            await self._json_store.write_list_unlocked(JOURNAL_FILENAME, journal)

    async def list_pending_operations(self) -> list[dict[str, Any]]:
        """Liste les opérations non finalisées (STAGED ou PUBLISHED_PENDING_COMMIT)."""
        async with self._json_store.lock_for(JOURNAL_FILENAME):
            journal = await self._json_store.read_list_unlocked(JOURNAL_FILENAME)
            return [
                op for op in journal
                if op.get("status") in ("STAGED", "PUBLISHED_PENDING_COMMIT")
            ]
