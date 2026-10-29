import asyncio
from pathlib import Path

import pytest

from app.storage.sqlite_repository import (
    HiloSQLiteRepository,
    ResourceCollisionError,
    ResourceRecord,
)


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    return tmp_path / ".hilo" / "index.sqlite"


@pytest.mark.asyncio
async def test_schema_initialization_wal_and_46_tables(temp_db_path: Path) -> None:
    repo = HiloSQLiteRepository(temp_db_path)
    try:
        await repo.initialize()

        # Check WAL mode & foreign keys
        journal_mode = await repo.get_pragma("journal_mode")
        assert journal_mode.lower() == "wal"

        foreign_keys = await repo.get_pragma("foreign_keys")
        assert foreign_keys in (1, "1")

        # Check 19 migrations recorded
        applied_migrations = await repo.get_applied_migrations()
        assert len(applied_migrations) == 19
        assert applied_migrations[0] == "0001_workspaces"
        assert applied_migrations[-1] == "0019_telemetry_audit"

        # Check exactly 46 application tables exist
        tables = await repo.get_table_names()
        # Filter internal tables like schema_migrations and sqlite_sequence
        app_tables = [t for t in tables if t not in ("schema_migrations", "sqlite_sequence")]
        assert len(app_tables) == 46

        # Check key tables exist
        assert "resource_v3" in app_tables
        assert "journal_staging_no_replace" in app_tables
        assert "workspaces" in app_tables
        assert "canvas_documents" in app_tables
        assert "layers" in app_tables
        assert "timelines" in app_tables
        assert "agent_sessions" in app_tables
        assert "brand_kits" in app_tables
        assert "character_anchors" in app_tables
        assert "inference_tasks" in app_tables
    finally:
        await repo.close()


@pytest.mark.asyncio
async def test_initialization_is_idempotent(temp_db_path: Path) -> None:
    repo = HiloSQLiteRepository(temp_db_path)
    try:
        await repo.initialize()
        # Call initialize again
        await repo.initialize()

        applied = await repo.get_applied_migrations()
        assert len(applied) == 19
    finally:
        await repo.close()


@pytest.mark.asyncio
async def test_register_resource_nominal(temp_db_path: Path) -> None:
    repo = HiloSQLiteRepository(temp_db_path)
    try:
        await repo.initialize()

        rec = await repo.register_resource(
            workspace_id="ws_default",
            generation_id="gen_001",
            artifact_id="art_video_01",
            file_path="outputs/gen_001_art_video_01.mp4",
            sha256_digest="abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
            byte_size=1048576,
            mime_type="video/mp4",
            media_type="video",
            metadata={"fps": 30, "duration": 5.0},
        )

        assert isinstance(rec, ResourceRecord)
        assert rec.workspace_id == "ws_default"
        assert rec.generation_id == "gen_001"
        assert rec.artifact_id == "art_video_01"
        assert rec.file_path == "outputs/gen_001_art_video_01.mp4"
        assert rec.byte_size == 1048576
        assert rec.media_type == "video"
        assert rec.metadata.get("fps") == 30

        # Retrieve and verify
        fetched = await repo.get_resource(
            workspace_id="ws_default",
            generation_id="gen_001",
            artifact_id="art_video_01",
        )
        assert fetched is not None
        assert fetched.id == rec.id
        assert fetched.sha256_digest == rec.sha256_digest
    finally:
        await repo.close()


@pytest.mark.asyncio
async def test_resource_collision_error(temp_db_path: Path) -> None:
    repo = HiloSQLiteRepository(temp_db_path)
    try:
        await repo.initialize()

        await repo.register_resource(
            workspace_id="ws_default",
            generation_id="gen_001",
            artifact_id="art_video_01",
            file_path="outputs/first.mp4",
            sha256_digest="1111111111111111111111111111111111111111111111111111111111111111",
            byte_size=5000,
            mime_type="video/mp4",
            media_type="video",
        )

        # Attempt to insert same unique key (workspace_id, generation_id, artifact_id)
        with pytest.raises(ResourceCollisionError) as exc_info:
            await repo.register_resource(
                workspace_id="ws_default",
                generation_id="gen_001",
                artifact_id="art_video_01",
                file_path="outputs/second.mp4",
                sha256_digest="2222222222222222222222222222222222222222222222222222222222222222",
                byte_size=6000,
                mime_type="video/mp4",
                media_type="video",
            )

        assert "ws_default" in str(exc_info.value)
        assert "gen_001" in str(exc_info.value)
    finally:
        await repo.close()


@pytest.mark.asyncio
async def test_list_resources_and_filtering(temp_db_path: Path) -> None:
    repo = HiloSQLiteRepository(temp_db_path)
    try:
        await repo.initialize()

        await repo.register_resource(
            workspace_id="ws_filters",
            generation_id="g1",
            artifact_id="a1",
            file_path="outputs/v1.mp4",
            sha256_digest="aaa",
            byte_size=1000,
            mime_type="video/mp4",
            media_type="video",
        )
        await repo.register_resource(
            workspace_id="ws_filters",
            generation_id="g2",
            artifact_id="a2",
            file_path="outputs/img.png",
            sha256_digest="bbb",
            byte_size=2000,
            mime_type="image/png",
            media_type="image",
        )
        await repo.register_resource(
            workspace_id="ws_filters",
            generation_id="g3",
            artifact_id="a3",
            file_path="outputs/mesh.glb",
            sha256_digest="ccc",
            byte_size=3000,
            mime_type="model/gltf-binary",
            media_type="mesh_3d",
        )

        all_res = await repo.list_resources(workspace_id="ws_filters")
        assert len(all_res) == 3

        video_res = await repo.list_resources(workspace_id="ws_filters", media_type="video")
        assert len(video_res) == 1
        assert video_res[0].media_type == "video"

        mesh_res = await repo.list_resources(workspace_id="ws_filters", media_type="mesh_3d")
        assert len(mesh_res) == 1
        assert mesh_res[0].media_type == "mesh_3d"
    finally:
        await repo.close()


@pytest.mark.asyncio
async def test_journal_staging_lifecycle(temp_db_path: Path) -> None:
    repo = HiloSQLiteRepository(temp_db_path)
    try:
        await repo.initialize()

        op1 = await repo.stage_journal_entry(
            operation_id="op_stg_01",
            workspace_id="ws_journal",
            generation_id="g_10",
            artifact_id="art_10",
            temp_path="outputs/tmp_10.part",
            final_path="outputs/final_10.mp4",
            sha256_digest="digest10",
            file_size=8192,
        )
        assert op1["status"] == "STAGED"

        pending = await repo.get_pending_journal_entries()
        assert len(pending) == 1
        assert pending[0]["operation_id"] == "op_stg_01"

        await repo.commit_journal_entry("op_stg_01")
        pending_after_commit = await repo.get_pending_journal_entries()
        assert len(pending_after_commit) == 0

        # Stage second entry and abort it
        await repo.stage_journal_entry(
            operation_id="op_stg_02",
            workspace_id="ws_journal",
            generation_id="g_20",
            artifact_id="art_20",
            temp_path="outputs/tmp_20.part",
            final_path="outputs/final_20.mp4",
            sha256_digest="digest20",
            file_size=4096,
        )
        await repo.abort_journal_entry("op_stg_02")
        pending_after_abort = await repo.get_pending_journal_entries()
        assert len(pending_after_abort) == 0
    finally:
        await repo.close()


@pytest.mark.asyncio
async def test_concurrent_writes_and_reads_under_wal(temp_db_path: Path) -> None:
    repo = HiloSQLiteRepository(temp_db_path)
    try:
        await repo.initialize()

        async def writer(task_idx: int) -> None:
            for i in range(5):
                await repo.register_resource(
                    workspace_id="ws_concurrent",
                    generation_id=f"gen_{task_idx}_{i}",
                    artifact_id="art_main",
                    file_path=f"outputs/gen_{task_idx}_{i}.mp4",
                    sha256_digest=f"hash_{task_idx}_{i}",
                    byte_size=1024,
                    mime_type="video/mp4",
                    media_type="video",
                )
                await asyncio.sleep(0.001)

        async def reader() -> None:
            for _ in range(10):
                await repo.list_resources(workspace_id="ws_concurrent")
                await asyncio.sleep(0.002)

        # Launch 4 concurrent writers and 2 concurrent readers
        await asyncio.gather(
            writer(1),
            writer(2),
            writer(3),
            writer(4),
            reader(),
            reader(),
        )

        total = await repo.list_resources(workspace_id="ws_concurrent")
        assert len(total) == 20
    finally:
        await repo.close()
