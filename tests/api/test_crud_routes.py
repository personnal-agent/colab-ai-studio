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


@pytest.fixture(autouse=True)
def mock_dns_resolution(monkeypatch):
    import socket

    def deterministic_getaddrinfo(host, port, *args, **kwargs):
        if host in ("127.0.0.1", "localhost", "::1"):
            return [(2, 1, 6, "", ("127.0.0.1", port))]
        return [(2, 1, 6, "", ("93.184.216.34", port))]

    monkeypatch.setattr(socket, "getaddrinfo", deterministic_getaddrinfo)


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

    # 7. Physical deletion failure propagates 500 and preserves JSON record
    import unittest.mock

    patch_del = unittest.mock.patch.object(
        media_store, "stage_delete_media", side_effect=OSError("Disk")
    )
    with patch_del:
        res_fail_del = await client.delete("/api/generations/gen_2")
        assert res_fail_del.status_code == 500

    intact_rem = await store.read_list("generations.json")
    assert any(item["id"] == "gen_2" for item in intact_rem)


async def test_delete_generation_transactional_rollback(test_env, monkeypatch):
    client, store, _, data_dir = test_env
    file_path = data_dir / "rollback_gen.mp4"
    thumb_path = data_dir / "rollback_gen.jpg"
    file_path.write_bytes(b"VIDEO_BYTES")
    thumb_path.write_bytes(b"THUMB_BYTES")

    gen_item = {
        "id": "gen_rollback",
        "mediaType": "video",
        "prompt": "Test rollback",
        "filePath": str(file_path),
        "thumbnailPath": str(thumb_path),
    }
    await store.write_list("generations.json", [gen_item])

    async def failing_write_list_unlocked(filename, data):
        raise OSError("Disque plein lors de l'écriture JSON")

    monkeypatch.setattr(store, "write_list_unlocked", failing_write_list_unlocked)

    with pytest.raises(OSError, match="Disque plein"):
        await client.delete("/api/generations/gen_rollback")

    # Les fichiers médias physiques ont été restaurés par le rollback
    assert file_path.exists()
    assert thumb_path.exists()
    assert file_path.read_bytes() == b"VIDEO_BYTES"


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

    # 5. Invalid colorTag returns 422 Unprocessable Entity
    res_bad_color = await client.post(
        "/api/projects",
        json={"name": "Bad Color", "colorTag": "not_a_hex"},
    )
    assert res_bad_color.status_code == 422


async def test_brand_kits_crud_blank_and_files(test_env, monkeypatch):
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

    # 3. Extract from website (mock hermétique sans dépendance réseau)
    class MockGoogleClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            class MockGoogleResponse:
                status_code = 200
                headers = {}
                url = httpx.URL("https://google.com")
                text = (
                    "<title>Google Search</title>"
                    "<meta name='description' content='Recherche mondiale'>"
                )

            return MockGoogleResponse()

    monkeypatch.setattr(httpx, "AsyncClient", MockGoogleClient)
    res_web = await client.post(
        "/api/brand-kits",
        data={"name": "Google", "websiteUrl": "https://google.com"},
    )
    assert res_web.status_code == 201
    assert "google" in res_web.json()["overview"].lower()

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

    # 6. Extract fonts from CSS file
    css_content = (
        b"@font-face { font-family: 'Montserrat'; }\n"
        b"body { font-family: 'Open Sans', sans-serif; color: #123456; }"
    )
    res_css = await client.post(
        "/api/brand-kits",
        data={"name": "Font Brand", "overview": "Test fonts"},
        files=[("files", ("style.css", css_content, "text/css"))],
    )
    assert res_css.status_code == 201
    bk_css = res_css.json()
    extracted_families = [f["family"] for f in bk_css["fonts"]]
    assert "Montserrat" in extracted_families or "Open Sans" in extracted_families


async def test_csrf_and_untrusted_origin_rejection(test_env):
    client, _, _, _ = test_env

    # 1. Sec-Fetch-Site: cross-site rejected with 403
    res_cross = await client.post(
        "/api/brand-kits",
        data={"name": "Attacker Kit"},
        headers={"sec-fetch-site": "cross-site"},
    )
    assert res_cross.status_code == 403
    assert "cross-origin" in res_cross.json()["detail"].lower()

    # 2. Origin: evil.com rejected with 403
    res_bad_origin = await client.post(
        "/api/projects",
        json={"name": "Attacker Project"},
        headers={"origin": "http://evil.com"},
    )
    assert res_bad_origin.status_code == 403


async def test_brand_kit_extract_from_website_parsing(test_env, monkeypatch):
    client, _, _, _ = test_env
    import httpx

    fake_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Studio Horizon</title>
        <meta name="description" content="Cinematic AI Production Studio">
        <link rel="icon" href="/favicon.ico">
        <style>
            :root { --primary: #0A84FF; --bg: #0D1117; }
            body { font-family: 'Cabinet Grotesk', sans-serif; }
        </style>
    </head>
    <body><h1>Horizon</h1></body>
    </html>
    """

    class MockResponse:
        status_code = 200
        text = fake_html

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            return MockResponse()

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    res_web = await client.post(
        "/api/brand-kits",
        data={"name": "Horizon Studio", "websiteUrl": "https://horizon.ai"},
    )
    assert res_web.status_code == 201
    bk = res_web.json()
    assert "Cinematic AI Production Studio" in bk["overview"]
    assert "#0A84FF" in [c["hex"] for c in bk["colors"]]
    assert any("Cabinet Grotesk" in f["family"] for f in bk["fonts"])
    assert len(bk["logos"]) >= 1


async def test_brand_kit_ssrf_rejects_private_and_local_ips(test_env):
    client, _, _, _ = test_env

    # 1. Adresse locale 127.0.0.1
    res1 = await client.post(
        "/api/brand-kits",
        data={"name": "Attacker", "websiteUrl": "http://127.0.0.1:8190/secret"},
    )
    assert res1.status_code == 400
    assert "interdit" in res1.json()["detail"].lower() or "privée" in res1.json()["detail"].lower()

    # 2. Nom d'hôte localhost
    res2 = await client.post(
        "/api/brand-kits",
        data={"name": "Attacker", "websiteUrl": "http://localhost:8000/private"},
    )
    assert res2.status_code == 400
    assert "interdit" in res2.json()["detail"].lower() or "privée" in res2.json()["detail"].lower()


async def test_brand_kit_ssrf_rejects_redirect_to_private_ip(test_env, monkeypatch):
    client, _, _, _ = test_env
    import httpx

    class RedirectMockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            class RedirectResponse:
                status_code = 302
                headers = {"location": "http://127.0.0.1:8190/admin"}
                url = httpx.URL("https://public-site.com")
                text = ""

            return RedirectResponse()

    monkeypatch.setattr(httpx, "AsyncClient", RedirectMockAsyncClient)

    # Note: public-site.com resolves to public IP, but its redirect points to 127.0.0.1
    res = await client.post(
        "/api/brand-kits",
        data={"name": "Sneaky", "websiteUrl": "https://google.com"},
    )
    assert res.status_code == 400
    assert "interdit" in res.json()["detail"].lower() or "privée" in res.json()["detail"].lower()


async def test_brand_kit_website_http_error_returns_400(test_env, monkeypatch):
    client, _, _, _ = test_env
    import httpx

    class ErrorMockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            class ErrorResponse:
                status_code = 404
                headers = {}
                url = httpx.URL("https://google.com/notfound")
                text = "Not Found"

            return ErrorResponse()

    monkeypatch.setattr(httpx, "AsyncClient", ErrorMockAsyncClient)

    res = await client.post(
        "/api/brand-kits",
        data={"name": "Broken", "websiteUrl": "https://google.com/notfound"},
    )
    assert res.status_code == 400
    assert "404" in res.json()["detail"]


async def test_brand_kit_favicon_resolves_against_redirect_url(test_env, monkeypatch):
    client, _, _, _ = test_env
    import httpx

    call_count = 0

    class MultiStepClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            nonlocal call_count
            call_count += 1
            if call_count == 1:

                class Step1Response:
                    status_code = 301
                    headers = {"location": "https://google.com/brand/home"}
                    url = httpx.URL("https://google.com/old-page")
                    text = ""

                return Step1Response()

            class FinalResponse:
                status_code = 200
                headers = {}
                url = httpx.URL("https://google.com/brand/home")
                text = '<link rel="icon" href="favicon.ico">'

            return FinalResponse()

    monkeypatch.setattr(httpx, "AsyncClient", MultiStepClient)

    res = await client.post(
        "/api/brand-kits",
        data={"name": "RedirectFavicon", "websiteUrl": "https://google.com/old-page"},
    )
    assert res.status_code == 201
    bk = res.json()
    assert len(bk["logos"]) == 1
    # Résolu depuis l'URL finale (https://google.com/brand/home -> https://google.com/brand/favicon.ico)
    assert bk["logos"][0]["filePath"] == "https://google.com/brand/favicon.ico"


async def test_config_colab_url_update(test_env):
    client, _, _, _ = test_env
    res = await client.post(
        "/api/config/colab-url",
        json={"tunnelUrl": "https://active-tunnel-123.ngrok-free.app"},
    )
    assert res.status_code == 200
    assert res.json()["tunnelUrl"] == "https://active-tunnel-123.ngrok-free.app"
