"""Gestionnaire de persistance documentaire JSON atomique (data/*.json).

Conformité stricte :
- Un asyncio.Lock dédié par collection pour sérialiser les écritures concurrentes.
- Écriture dans un fichier temporaire .tmp dans le même répertoire que la cible.
- Remplacement atomique POSIX via os.replace pour immunité contre les crashs.
- Détection et isolation des fichiers JSON corrompus ou invalides.
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
    _global_locks: dict[tuple[str, str], asyncio.Lock] = {}

    def __init__(self, data_dir: Path | str) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._corrupted_files: set[str] = set()

    def is_corrupted(self, filename: str) -> bool:
        return Path(filename).name in self._corrupted_files

    def mark_corrupted(self, filename: str) -> None:
        self._corrupted_files.add(Path(filename).name)

    def lock_for(self, filename: str) -> asyncio.Lock:
        canon_name = Path(filename).name
        key = (str(self.data_dir.resolve()), canon_name)
        if key not in self._global_locks:
            self._global_locks[key] = asyncio.Lock()
        return self._global_locks[key]

    def _resolve(self, filename: str) -> Path:
        target = (self.data_dir / Path(filename).name).resolve()
        if not str(target).startswith(str(self.data_dir.resolve())):
            raise ValueError(f"Tentative d'accès hors du répertoire data : {filename}")
        return target

    def _perform_read(self, target: Path, expected_type: type, default: Any) -> Any:
        filename = target.name
        if not target.exists():
            return default() if callable(default) else default
        try:
            content = target.read_text(encoding="utf-8")
        except OSError as e:
            self._corrupted_files.add(filename)
            raise CorruptedDocumentStoreError(
                f"Impossible de lire le fichier {filename} : {e}"
            ) from e

        if not content.strip():
            self._corrupted_files.add(filename)
            raise CorruptedDocumentStoreError(f"Fichier JSON vide ou corrompu {filename}")

        try:
            loaded = json.loads(content)
        except json.JSONDecodeError as e:
            self._corrupted_files.add(filename)
            raise CorruptedDocumentStoreError(
                f"Fichier JSON corrompu {filename} à la position {e.pos} : {e.msg}"
            ) from e

        if not isinstance(loaded, expected_type):
            self._corrupted_files.add(filename)
            exp, act = expected_type.__name__, type(loaded).__name__
            raise CorruptedDocumentStoreError(
                f"Type inattendu dans {filename} : attendu '{exp}', obtenu '{act}'"
            )

        self._corrupted_files.discard(filename)
        return loaded

    async def read_list(self, filename: str) -> list[dict[str, Any]]:
        async with self.lock_for(filename):
            return await self.read_list_unlocked(filename)

    async def read_list_unlocked(self, filename: str) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._perform_read, self._resolve(filename), list, list)

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
        return await asyncio.to_thread(
            self._perform_read, self._resolve(filename), dict, dict(default or {})
        )

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
        if target.exists():
            try:
                existing_raw = target.read_text(encoding="utf-8")
                if not existing_raw.strip():
                    self._corrupted_files.add(filename)
                    raise CorruptedDocumentStoreError(
                        f"Écriture refusée : le fichier existant {filename} est vide ou corrompu."
                    )
                json.loads(existing_raw)
                self._corrupted_files.discard(filename)
            except (json.JSONDecodeError, OSError) as e:
                self._corrupted_files.add(filename)
                raise CorruptedDocumentStoreError(
                    f"Écriture refusée : le fichier existant {filename} est corrompu ({e})."
                ) from e
        elif filename in self._corrupted_files:
            self._corrupted_files.discard(filename)

        if filename in self._corrupted_files:
            msg = (
                f"Écriture refusée : le fichier {filename} a été marqué "
                "comme corrompu lors d'une lecture précédente."
            )
            raise CorruptedDocumentStoreError(msg)
        tmp_fd, tmp_path_str = tempfile.mkstemp(
            dir=self.data_dir, prefix=f".{target.name}.", suffix=".tmp"
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
