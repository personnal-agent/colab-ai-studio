"""Gestionnaire de persistance documentaire JSON atomique (data/*.json).

Conformité stricte :
- Un asyncio.Lock dédié par collection pour sérialiser les écritures concurrentes.
- Écriture dans un fichier temporaire .tmp dans le même répertoire que la cible.
- Remplacement atomique POSIX via os.replace pour immunité contre les crashs.
- Respect de la contrainte <constraint id="filesystem"> d'AGENTS.md.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


class CorruptedDocumentStoreError(RuntimeError):
    """Exception levée lorsqu'un document JSON existant est corrompu ou illisible sur le disque."""


class JSONDocumentStore:
    def __init__(self, data_dir: Path | str) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, asyncio.Lock] = {}
        self._registry_lock = asyncio.Lock()
        self._corrupted_files: set[str] = set()

    def is_corrupted(self, filename: str) -> bool:
        return Path(filename).name in self._corrupted_files

    def mark_corrupted(self, filename: str) -> None:
        self._corrupted_files.add(Path(filename).name)

    def lock_for(self, filename: str) -> asyncio.Lock:
        canon_name = Path(filename).name
        if canon_name not in self._locks:
            self._locks[canon_name] = asyncio.Lock()
        return self._locks[canon_name]

    def _resolve(self, filename: str) -> Path:
        target = (self.data_dir / Path(filename).name).resolve()
        # Sécurité path traversal
        if not str(target).startswith(str(self.data_dir.resolve())):
            msg = f"Tentative d'accès hors du répertoire data : {filename}"
            raise ValueError(msg)
        return target

    async def read_list(self, filename: str) -> list[dict[str, Any]]:
        async with self.lock_for(filename):
            return await self.read_list_unlocked(filename)

    async def read_list_unlocked(self, filename: str) -> list[dict[str, Any]]:
        target = self._resolve(filename)
        return await asyncio.to_thread(self._perform_read_list, target)

    def _perform_read_list(self, target: Path) -> list[dict[str, Any]]:
        filename = target.name
        if not target.exists():
            return []
        try:
            content = target.read_text(encoding="utf-8")
        except OSError as e:
            self._corrupted_files.add(filename)
            msg = f"Impossible de lire le fichier {filename} : {e}"
            raise CorruptedDocumentStoreError(msg) from e

        if not content.strip():
            self._corrupted_files.add(filename)
            msg = f"Fichier JSON vide ou corrompu {filename}"
            raise CorruptedDocumentStoreError(msg)

        try:
            loaded = json.loads(content)
        except json.JSONDecodeError as e:
            self._corrupted_files.add(filename)
            msg = f"Fichier JSON corrompu {filename} à la position {e.pos} : {e.msg}"
            raise CorruptedDocumentStoreError(msg) from e

        if not isinstance(loaded, list):
            self._corrupted_files.add(filename)
            actual = type(loaded).__name__
            msg = f"Type inattendu dans {filename} : attendu 'list', obtenu '{actual}'"
            raise CorruptedDocumentStoreError(msg)

        return loaded

    async def write_list(self, filename: str, data: list[dict[str, Any]]) -> None:
        async with self.lock_for(filename):
            await self.write_list_unlocked(filename, data)

    async def write_list_unlocked(self, filename: str, data: list[dict[str, Any]]) -> None:
        await self._write_json_atomic(filename, data)

    async def read_dict(
        self, filename: str, default: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        async with self.lock_for(filename):
            return await self.read_dict_unlocked(filename, default)

    async def read_dict_unlocked(
        self, filename: str, default: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        target = self._resolve(filename)
        return await asyncio.to_thread(self._perform_read_dict, target, default)

    def _perform_read_dict(self, target: Path, default: dict[str, Any] | None) -> dict[str, Any]:
        filename = target.name
        if not target.exists():
            return dict(default or {})
        try:
            content = target.read_text(encoding="utf-8")
        except OSError as e:
            self._corrupted_files.add(filename)
            msg = f"Impossible de lire le fichier {filename} : {e}"
            raise CorruptedDocumentStoreError(msg) from e

        if not content.strip():
            self._corrupted_files.add(filename)
            msg = f"Fichier JSON vide ou corrompu {filename}"
            raise CorruptedDocumentStoreError(msg)

        try:
            loaded = json.loads(content)
        except json.JSONDecodeError as e:
            self._corrupted_files.add(filename)
            msg = f"Fichier JSON corrompu {filename} à la position {e.pos} : {e.msg}"
            raise CorruptedDocumentStoreError(msg) from e

        if not isinstance(loaded, dict):
            self._corrupted_files.add(filename)
            actual = type(loaded).__name__
            msg = f"Type inattendu dans {filename} : attendu 'dict', obtenu '{actual}'"
            raise CorruptedDocumentStoreError(msg)

        return loaded

    async def write_dict(self, filename: str, data: dict[str, Any]) -> None:
        async with self.lock_for(filename):
            await self.write_dict_unlocked(filename, data)

    async def write_dict_unlocked(self, filename: str, data: dict[str, Any]) -> None:
        await self._write_json_atomic(filename, data)

    async def _write_json_atomic(self, filename: str, payload: Any) -> None:
        target = self._resolve(filename)
        serialized = json.dumps(payload, indent=2, ensure_ascii=False)
        await asyncio.to_thread(self._perform_atomic_write, target, serialized)

    def _perform_atomic_write(self, target: Path, serialized: str) -> None:
        filename = target.name
        if filename in self._corrupted_files:
            msg = (
                f"Écriture refusée : le fichier {filename} a été marqué comme corrompu "
                f"lors d'une lecture précédente et ne doit pas être écrasé."
            )
            raise CorruptedDocumentStoreError(msg)

        if target.exists():
            try:
                existing_raw = target.read_text(encoding="utf-8")
                if not existing_raw.strip():
                    self._corrupted_files.add(filename)
                    msg = f"Écriture refusée : le fichier existant {filename} est vide ou corrompu."
                    raise CorruptedDocumentStoreError(msg)
                json.loads(existing_raw)
            except (json.JSONDecodeError, OSError) as e:
                self._corrupted_files.add(filename)
                msg = f"Écriture refusée : le fichier existant {filename} est corrompu ({e})."
                raise CorruptedDocumentStoreError(msg) from e
        tmp_fd, tmp_path_str = tempfile.mkstemp(
            dir=self.data_dir,
            prefix=f".{target.name}.",
            suffix=".tmp",
        )
        tmp_path = Path(tmp_path_str)
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                f.write(serialized)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, target)
            if os.name == "posix":
                dir_fd = os.open(self.data_dir, os.O_RDONLY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
        except Exception:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path_str)
            raise
