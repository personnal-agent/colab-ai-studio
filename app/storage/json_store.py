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


class JSONDocumentStore:
    def __init__(self, data_dir: Path | str) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, asyncio.Lock] = {}
        self._registry_lock = asyncio.Lock()

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
        target = self._resolve(filename)
        if not target.exists():
            return []
        lock = self.lock_for(filename)
        if lock.locked():
            return self._perform_read_list(target)
        async with lock:
            return self._perform_read_list(target)

    def _perform_read_list(self, target: Path) -> list[dict[str, Any]]:
        try:
            content = target.read_text(encoding="utf-8")
            if not content.strip():
                return []
            loaded = json.loads(content)
            if isinstance(loaded, list):
                return loaded
            return []
        except (json.JSONDecodeError, OSError):
            return []

    async def write_list(self, filename: str, data: list[dict[str, Any]]) -> None:
        await self._write_json_atomic(filename, data)

    async def read_dict(
        self, filename: str, default: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        target = self._resolve(filename)
        if not target.exists():
            return dict(default or {})
        lock = self.lock_for(filename)
        if lock.locked():
            return self._perform_read_dict(target, default)
        async with lock:
            return self._perform_read_dict(target, default)

    def _perform_read_dict(self, target: Path, default: dict[str, Any] | None) -> dict[str, Any]:
        try:
            content = target.read_text(encoding="utf-8")
            if not content.strip():
                return dict(default or {})
            loaded = json.loads(content)
            if isinstance(loaded, dict):
                return loaded
            return dict(default or {})
        except (json.JSONDecodeError, OSError):
            return dict(default or {})

    async def write_dict(self, filename: str, data: dict[str, Any]) -> None:
        await self._write_json_atomic(filename, data)

    async def _write_json_atomic(self, filename: str, payload: Any) -> None:
        target = self._resolve(filename)
        serialized = json.dumps(payload, indent=2, ensure_ascii=False)

        lock = self.lock_for(filename)
        # Si le verrou est déjà détenu par la coroutine courante, on ne ré-acquiert pas
        if lock.locked():
            await self._perform_atomic_write(target, serialized)
        else:
            async with lock:
                await self._perform_atomic_write(target, serialized)

    async def _perform_atomic_write(self, target: Path, serialized: str) -> None:
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
        except Exception:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path_str)
            raise
