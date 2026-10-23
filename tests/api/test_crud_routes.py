"""Tests d'intégration des routes CRUD documentaires (Step 5 du Plan 01).

Couvre via httpx.AsyncClient (ASGITransport asynchrone pur) :
- GET /api/health
- GET /api/generations (avec filtres favorite, mediaType, projectId, search q)
- PATCH /api/generations/{id}/favorite
- DELETE /api/generations/{id}
- GET /api/brand-kits
- POST /api/brand-kits (Blank, files, website)
- GET /api/projects
- POST /api/projects (avec validation storagePath)
- POST /api/config/colab-url
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from app.api import routes_crud
from app.main import app
from app.services.brand_extractor import BrandKitExtractor
from app.storage.json_store import JSONDocumentStore
from app.storage.media_store import MediaFileStore


@pytest.fixture
async def test_env(tmp_path: Path):
    data_dir = tmp_path / "data"
    outputs_dir = tmp_path / "outputs"
    assets_dir = data_dir / "assets"
    data_dir.mkdir(parents=True)
    outputs_dir.mkdir(parents=True)
    assets_dir.mkdir(parents=True)

    store = JSONDocumentStore(data_dir)
    media_store = MediaFileStore(outputs_dir)
    extractor = BrandKitExtractor(assets_dir)

    routes_crud._json_store = store
    routes_crud._media_store = media_store
    routes_crud._extractor = extractor

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, store, media_store, data_dir


async def test_health_check(test_env):
    client, _, _, _ = test_env
    res = await client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


async def test_generations_crud_and_filters(test_env):
    client, store, media_store, data_dir = test_env

    sample_gen1 = {
        "id": "gen_1",
        "mediaType": "video",
        "prompt": "Aerial view of a misty forest",
        "modelName": "Seedance 2.5",
        "isFavorite": False,
        "projectId": "proj_a",
        "filePath": str(data_dir / "gen_1.mp4"),
        "thumbnailPath": str(data_dir / "gen_1.jpg"),
        "createdAt": "2026-10-09T10:00:00Z",
    }
    sample_gen2 = {
        "id": "gen_2",
        "mediaType": "image",
        "prompt": "Cyberpunk city night",
        "modelName": "NoctQ V4",
        "isFavorite": True,
        "projectId": "proj_b",
        "createdAt": "2026-10-09T11:00:00Z",
    }
    await store.write_list("generations.json", [sample_gen1, sample_gen2])

    # 1. List all
    res = await client.get("/api/generations")
    assert res.status_code == 200
    assert len(res.json()) == 2
    assert res.json()[0]["id"] == "gen_2"

    # 2. Filter favorite
    res_fav = await client.get("/api/generations?favorite=true")
    assert len(res_fav.json()) == 1
    assert res_fav.json()[0]["id"] == "gen_2"

    # 3. Filter mediaType
    res_vid = await client.get("/api/generations?mediaType=video")
    assert len(res_vid.json()) == 1
    assert res_vid.json()[0]["id"] == "gen_1"

    # 4. Filter search q
    res_q = await client.get("/api/generations?q=misty")
    assert len(res_q.json()) == 1
    assert res_q.json()[0]["id"] == "gen_1"

    # 5. Toggle favorite
    res_toggle = await client.patch("/api/generations/gen_1/favorite")
    assert res_toggle.status_code == 200
    assert res_toggle.json()["isFavorite"] is True

    # 6. Delete generation
    Path(sample_gen1["filePath"]).write_text("dummy")
    Path(sample_gen1["thumbnailPath"]).write_text("dummy")
    res_del = await client.delete("/api/generations/gen_1")
    assert res_del.status_code == 200
    assert res_del.json()["deleted"] is True
    assert not Path(sample_gen1["filePath"]).exists()
    assert not Path(sample_gen1["thumbnailPath"]).exists()

    remaining = await store.read_list("generations.json")
    assert len(remaining) == 1
    assert remaining[0]["id"] == "gen_2"


async def test_projects_crud_and_storage_path_validation(test_env):
    client, _, _, tmp_path = test_env

    # 1. Create project with standard storage
    res = await client.post("/api/projects", json={"name": "Court Métrage", "colorTag": "#3B82F6"})
    assert res.status_code == 201
    proj1 = res.json()
    assert proj1["name"] == "Court Métrage"
    assert proj1["colorTag"] == "#3B82F6"

    # 2. Create project with custom valid storagePath
    custom_dir = tmp_path / "custom_storage"
    res_custom = await client.post(
        "/api/projects",
        json={"name": "Projet Isolé", "storagePath": str(custom_dir)},
    )
    assert res_custom.status_code == 201
    assert custom_dir.exists()
    assert res_custom.json()["storagePath"] == str(custom_dir.resolve())

    # 3. Create project with malicious forbidden path
    res_bad = await client.post(
        "/api/projects",
        json={"name": "Bad Path", "storagePath": "/etc/shadow"},
    )
    assert res_bad.status_code == 422
    assert "interdit" in res_bad.json()["detail"].lower()

    res_bad_githooks = await client.post(
        "/api/projects",
        json={"name": "Bad Hooks", "storagePath": ".githooks"},
    )
    assert res_bad_githooks.status_code == 422
    assert "interdit" in res_bad_githooks.json()["detail"].lower()

    # 4. List projects
    res_list = await client.get("/api/projects")
    assert res_list.status_code == 200
    assert len(res_list.json()) == 2


async def test_brand_kits_crud_blank_and_files(test_env):
    client, _, _, _ = test_env

    # 1. Blank
    res_blank = await client.post(
        "/api/brand-kits",
        data={"name": "Apple Style", "overview": "Minimalist aesthetic."},
    )
    assert res_blank.status_code == 201
    bk = res_blank.json()
    assert bk["name"] == "Apple Style"
    assert bk["overview"] == "Minimalist aesthetic."

    # 2. Extract from SVG file containing hex colors
    svg_content = b'<svg><rect fill="#FF0000" /><circle fill="#00FF00" /></svg>'
    res_files = await client.post(
        "/api/brand-kits",
        data={"name": "Color Brand", "overview": "Test colors"},
        files=[("files", ("logo.svg", svg_content, "image/svg+xml"))],
    )
    assert res_files.status_code == 201
    bk_files = res_files.json()
    assert len(bk_files["logos"]) == 1
    hex_colors = [c["hex"] for c in bk_files["colors"]]
    assert "#FF0000" in hex_colors or "#00FF00" in hex_colors

    # 3. Extract from website
    res_web = await client.post(
        "/api/brand-kits",
        data={"name": "Google", "websiteUrl": "https://google.com"},
    )
    assert res_web.status_code == 201
    assert "google.com" in res_web.json()["overview"]

    # 4. List brand kits
    res_list = await client.get("/api/brand-kits")
    assert res_list.status_code == 200
    assert len(res_list.json()) == 3

    # 5. Aggregate file upload exceeding 50 MB cap returns 413
    oversized_chunk = b"X" * (51 * 1024 * 1024)
    res_oversized = await client.post(
        "/api/brand-kits",
        data={"name": "Oversized Kit"},
        files=[("files", ("huge.bin", oversized_chunk, "application/octet-stream"))],
    )
    assert res_oversized.status_code == 413


async def test_config_colab_url_update(test_env):
    client, _, _, _ = test_env
    res = await client.post(
        "/api/config/colab-url",
        json={"tunnelUrl": "https://active-tunnel-123.ngrok-free.app"},
    )
    assert res.status_code == 200
    assert res.json()["tunnelUrl"] == "https://active-tunnel-123.ngrok-free.app"
