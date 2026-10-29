"""
Hilo SQLite Repository.
Provides WAL-mode relational persistence for .hilo/index.sqlite
(46 tables, migrations 0001 to 0019).
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.storage.sqlite_migrations import MIGRATIONS


class ResourceCollisionError(Exception):
    """
    Raised when attempting to insert a duplicate resource
    with existing (workspace_id, generation_id, artifact_id).
    """


@dataclass
class ResourceRecord:
    id: str
    workspace_id: str
    generation_id: str
    artifact_id: str
    file_path: str
    sha256_digest: str
    byte_size: int
    mime_type: str
    media_type: str
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "committed"
    created_at: str = ""
    updated_at: str = ""


class HiloSQLiteRepository:
    """Async repository for .hilo/index.sqlite managing the 46 tables under WAL mode."""

    _ALLOWED_PRAGMAS: dict[str, str] = {
        "journal_mode": "PRAGMA journal_mode;",
        "foreign_keys": "PRAGMA foreign_keys;",
        "synchronous": "PRAGMA synchronous;",
        "busy_timeout": "PRAGMA busy_timeout;",
    }

    def __init__(self, db_path: Path | str = Path(".hilo/index.sqlite")) -> None:
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None
        self._lock = asyncio.Lock()

    def _sync_connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=5.0,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    def _sync_initialize(self) -> None:
        if self._conn is None:
            self._conn = self._sync_connect()

        # Schema migrations table
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        self._conn.commit()

        cursor = self._conn.execute("SELECT version FROM schema_migrations;")
        applied = {row[0] for row in cursor.fetchall()}

        for version, sql in MIGRATIONS:
            if version not in applied:
                with self._conn:
                    self._conn.executescript(sql)
                    self._conn.execute(
                        "INSERT INTO schema_migrations (version) VALUES (?);",
                        (version,),
                    )

    async def initialize(self) -> None:
        """Initialize database, enable WAL pragmas, and execute migrations 0001 to 0019."""
        async with self._lock:
            await asyncio.to_thread(self._sync_initialize)

    def _sync_get_pragma(self, name: str) -> Any:
        if self._conn is None:
            self._conn = self._sync_connect()
        stmt = self._ALLOWED_PRAGMAS.get(name.lower())
        if not stmt:
            raise ValueError(f"Unauthorized or unsupported PRAGMA: {name}")
        cursor = self._conn.execute(stmt)
        row = cursor.fetchone()
        return row[0] if row else None

    async def get_pragma(self, name: str) -> Any:
        async with self._lock:
            return await asyncio.to_thread(self._sync_get_pragma, name)

    def _sync_get_applied_migrations(self) -> list[str]:
        if self._conn is None:
            self._conn = self._sync_connect()
        cursor = self._conn.execute(
            "SELECT version FROM schema_migrations ORDER BY version ASC;"
        )
        return [row[0] for row in cursor.fetchall()]

    async def get_applied_migrations(self) -> list[str]:
        async with self._lock:
            return await asyncio.to_thread(self._sync_get_applied_migrations)

    def _sync_get_table_names(self) -> list[str]:
        if self._conn is None:
            self._conn = self._sync_connect()
        cursor = self._conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name ASC;"
        )
        return [row[0] for row in cursor.fetchall()]

    async def get_table_names(self) -> list[str]:
        async with self._lock:
            return await asyncio.to_thread(self._sync_get_table_names)

    def _sync_register_resource(
        self,
        workspace_id: str,
        generation_id: str,
        artifact_id: str,
        file_path: str,
        sha256_digest: str,
        byte_size: int,
        mime_type: str,
        media_type: str,
        metadata: dict[str, Any] | None,
    ) -> ResourceRecord:
        if self._conn is None:
            self._conn = self._sync_connect()

        resource_id = str(uuid.uuid4())
        meta_json = json.dumps(metadata or {})

        try:
            with self._conn:
                self._conn.execute(
                    """
                    INSERT INTO resource_v3 (
                        id, workspace_id, generation_id, artifact_id,
                        file_path, sha256_digest, byte_size, mime_type,
                        media_type, metadata_json, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'committed');
                    """,
                    (
                        resource_id,
                        workspace_id,
                        generation_id,
                        artifact_id,
                        file_path,
                        sha256_digest,
                        byte_size,
                        mime_type,
                        media_type,
                        meta_json,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            if "UNIQUE constraint failed" in str(exc) or "uq_resource_key" in str(exc):
                msg = (
                    f"Resource collision: workspace='{workspace_id}', "
                    f"generation='{generation_id}', artifact='{artifact_id}' "
                    "already registered."
                )
                raise ResourceCollisionError(msg) from exc
            raise

        cursor = self._conn.execute(
            "SELECT created_at, updated_at FROM resource_v3 WHERE id = ?;",
            (resource_id,),
        )
        row = cursor.fetchone()
        created_at = row["created_at"] if row else ""
        updated_at = row["updated_at"] if row else ""

        return ResourceRecord(
            id=resource_id,
            workspace_id=workspace_id,
            generation_id=generation_id,
            artifact_id=artifact_id,
            file_path=file_path,
            sha256_digest=sha256_digest,
            byte_size=byte_size,
            mime_type=mime_type,
            media_type=media_type,
            metadata=metadata or {},
            status="committed",
            created_at=created_at,
            updated_at=updated_at,
        )

    async def register_resource(
        self,
        workspace_id: str,
        generation_id: str,
        artifact_id: str,
        file_path: str,
        sha256_digest: str,
        byte_size: int,
        mime_type: str,
        media_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> ResourceRecord:
        async with self._lock:
            return await asyncio.to_thread(
                self._sync_register_resource,
                workspace_id,
                generation_id,
                artifact_id,
                file_path,
                sha256_digest,
                byte_size,
                mime_type,
                media_type,
                metadata,
            )

    def _sync_get_resource(
        self,
        workspace_id: str,
        generation_id: str,
        artifact_id: str,
    ) -> ResourceRecord | None:
        if self._conn is None:
            self._conn = self._sync_connect()

        cursor = self._conn.execute(
            """
            SELECT * FROM resource_v3
            WHERE workspace_id = ? AND generation_id = ? AND artifact_id = ?;
            """,
            (workspace_id, generation_id, artifact_id),
        )
        row = cursor.fetchone()
        if not row:
            return None

        meta = {}
        if row["metadata_json"]:
            try:
                meta = json.loads(row["metadata_json"])
            except (json.JSONDecodeError, TypeError):
                meta = {}

        return ResourceRecord(
            id=row["id"],
            workspace_id=row["workspace_id"],
            generation_id=row["generation_id"],
            artifact_id=row["artifact_id"],
            file_path=row["file_path"],
            sha256_digest=row["sha256_digest"],
            byte_size=row["byte_size"],
            mime_type=row["mime_type"],
            media_type=row["media_type"],
            metadata=meta,
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def get_resource(
        self,
        workspace_id: str,
        generation_id: str,
        artifact_id: str,
    ) -> ResourceRecord | None:
        async with self._lock:
            return await asyncio.to_thread(
                self._sync_get_resource,
                workspace_id,
                generation_id,
                artifact_id,
            )

    def _sync_list_resources(
        self,
        workspace_id: str,
        media_type: str | None,
        limit: int,
        offset: int,
    ) -> list[ResourceRecord]:
        if self._conn is None:
            self._conn = self._sync_connect()

        query = "SELECT * FROM resource_v3 WHERE workspace_id = ?"
        params: list[Any] = [workspace_id]

        if media_type is not None:
            query += " AND media_type = ?"
            params.append(media_type)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        cursor = self._conn.execute(query, params)
        rows = cursor.fetchall()
        result: list[ResourceRecord] = []

        for row in rows:
            meta = {}
            if row["metadata_json"]:
                try:
                    meta = json.loads(row["metadata_json"])
                except (json.JSONDecodeError, TypeError):
                    meta = {}

            result.append(
                ResourceRecord(
                    id=row["id"],
                    workspace_id=row["workspace_id"],
                    generation_id=row["generation_id"],
                    artifact_id=row["artifact_id"],
                    file_path=row["file_path"],
                    sha256_digest=row["sha256_digest"],
                    byte_size=row["byte_size"],
                    mime_type=row["mime_type"],
                    media_type=row["media_type"],
                    metadata=meta,
                    status=row["status"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )
        return result

    async def list_resources(
        self,
        workspace_id: str,
        media_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ResourceRecord]:
        async with self._lock:
            return await asyncio.to_thread(
                self._sync_list_resources,
                workspace_id,
                media_type,
                limit,
                offset,
            )

    def _sync_stage_journal_entry(
        self,
        operation_id: str,
        workspace_id: str,
        generation_id: str,
        artifact_id: str,
        temp_path: str,
        final_path: str,
        sha256_digest: str,
        file_size: int,
    ) -> dict[str, Any]:
        if self._conn is None:
            self._conn = self._sync_connect()

        with self._conn:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO journal_staging_no_replace (
                    operation_id, workspace_id, generation_id, artifact_id,
                    temp_path, final_path, sha256_digest, file_size, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'STAGED');
                """,
                (
                    operation_id,
                    workspace_id,
                    generation_id,
                    artifact_id,
                    temp_path,
                    final_path,
                    sha256_digest,
                    file_size,
                ),
            )

        cursor = self._conn.execute(
            "SELECT * FROM journal_staging_no_replace WHERE operation_id = ?;",
            (operation_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else {}

    async def stage_journal_entry(
        self,
        operation_id: str,
        workspace_id: str,
        generation_id: str,
        artifact_id: str,
        temp_path: str,
        final_path: str,
        sha256_digest: str,
        file_size: int,
    ) -> dict[str, Any]:
        async with self._lock:
            return await asyncio.to_thread(
                self._sync_stage_journal_entry,
                operation_id,
                workspace_id,
                generation_id,
                artifact_id,
                temp_path,
                final_path,
                sha256_digest,
                file_size,
            )

    def _sync_update_journal_status(self, operation_id: str, status: str) -> None:
        if self._conn is None:
            self._conn = self._sync_connect()

        with self._conn:
            self._conn.execute(
                """
                UPDATE journal_staging_no_replace
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE operation_id = ?;
                """,
                (status, operation_id),
            )

    async def commit_journal_entry(self, operation_id: str) -> None:
        async with self._lock:
            await asyncio.to_thread(self._sync_update_journal_status, operation_id, "COMMITTED")

    async def abort_journal_entry(self, operation_id: str) -> None:
        async with self._lock:
            await asyncio.to_thread(self._sync_update_journal_status, operation_id, "ABORTED")

    def _sync_get_pending_journal_entries(self) -> list[dict[str, Any]]:
        if self._conn is None:
            self._conn = self._sync_connect()

        cursor = self._conn.execute(
            "SELECT * FROM journal_staging_no_replace "
            "WHERE status = 'STAGED' ORDER BY created_at ASC;"
        )
        return [dict(row) for row in cursor.fetchall()]

    async def get_pending_journal_entries(self) -> list[dict[str, Any]]:
        async with self._lock:
            return await asyncio.to_thread(self._sync_get_pending_journal_entries)

    def _sync_close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    async def close(self) -> None:
        async with self._lock:
            await asyncio.to_thread(self._sync_close)


_default_hilo_repo: HiloSQLiteRepository | None = None


def get_hilo_sqlite_repo() -> HiloSQLiteRepository:
    global _default_hilo_repo
    if _default_hilo_repo is None:
        _default_hilo_repo = HiloSQLiteRepository()
    return _default_hilo_repo

