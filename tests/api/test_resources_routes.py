"""Integration tests for /api/resources SQLite endpoints."""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.storage.sqlite_repository import (
    HiloSQLiteRepository,
    get_hilo_sqlite_repo,
)


@pytest.fixture
async def sqlite_repo(tmp_path: Path):
    db_file = tmp_path / ".hilo" / "test_api.sqlite"
    repo = HiloSQLiteRepository(db_file)
    await repo.initialize()
    yield repo
    await repo.close()


@pytest.fixture
async def client(sqlite_repo: HiloSQLiteRepository):
    app.dependency_overrides[get_hilo_sqlite_repo] = lambda: sqlite_repo
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_schema_status(client: AsyncClient):
    resp = await client.get("/api/resources/schema-status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["journal_mode"].lower() == "wal"
    assert data["foreign_keys_enabled"] is True
    assert data["migrations_count"] == 19
    assert data["application_tables_count"] == 46
    assert "resource_v3" in data["tables"]


@pytest.mark.asyncio
async def test_post_and_get_resource(client: AsyncClient):
    payload = {
        "workspace_id": "ws_api_test",
        "generation_id": "gen_api_01",
        "artifact_id": "art_video",
        "file_path": "outputs/test_video.mp4",
        "sha256_digest": "abcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdef",
        "byte_size": 2048,
        "mime_type": "video/mp4",
        "media_type": "video",
        "metadata": {"resolution": "1080p"},
    }
    resp = await client.post("/api/resources", json=payload)
    assert resp.status_code == 201
    created = resp.json()
    assert created["workspace_id"] == "ws_api_test"
    assert created["generation_id"] == "gen_api_01"
    assert created["artifact_id"] == "art_video"
    assert created["file_path"] == "outputs/test_video.mp4"
    assert created["metadata"]["resolution"] == "1080p"

    # Get single resource
    get_resp = await client.get("/api/resources/ws_api_test/gen_api_01/art_video")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["id"] == created["id"]
    assert fetched["file_path"] == "outputs/test_video.mp4"


@pytest.mark.asyncio
async def test_post_resource_collision_returns_409(client: AsyncClient):
    payload = {
        "workspace_id": "ws_collision",
        "generation_id": "gen_col",
        "artifact_id": "art_col",
        "file_path": "outputs/one.mp4",
        "sha256_digest": "1111111111111111111111111111111111111111111111111111111111111111",
        "byte_size": 100,
        "mime_type": "video/mp4",
        "media_type": "video",
    }
    resp1 = await client.post("/api/resources", json=payload)
    assert resp1.status_code == 201

    # Conflict on same unique key
    resp2 = await client.post("/api/resources", json=payload)
    assert resp2.status_code == 409
    assert "collision" in resp2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_resource_not_found(client: AsyncClient):
    resp = await client.get("/api/resources/ws_unknown/gen_unknown/art_unknown")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_resources_with_query_filter(client: AsyncClient):
    # Insert multiple
    for i, m_type in enumerate(["video", "video", "image"]):
        await client.post(
            "/api/resources",
            json={
                "workspace_id": "ws_query",
                "generation_id": f"gen_{i}",
                "artifact_id": f"art_{i}",
                "file_path": f"outputs/file_{i}.dat",
                "sha256_digest": f"digest_{i}",
                "byte_size": 100 * (i + 1),
                "mime_type": "application/octet-stream",
                "media_type": m_type,
            },
        )

    # List all for workspace
    resp_all = await client.get("/api/resources", params={"workspace_id": "ws_query"})
    assert resp_all.status_code == 200
    assert resp_all.json()["count"] == 3

    # Filter by video
    resp_video = await client.get(
        "/api/resources",
        params={"workspace_id": "ws_query", "media_type": "video"},
    )
    assert resp_video.status_code == 200
    assert resp_video.json()["count"] == 2

    # Filter by image
    resp_img = await client.get(
        "/api/resources",
        params={"workspace_id": "ws_query", "media_type": "image"},
    )
    assert resp_img.status_code == 200
    assert resp_img.json()["count"] == 1
