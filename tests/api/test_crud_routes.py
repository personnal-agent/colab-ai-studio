"""Tests d'intégration des routes CRUD documentaires (Step 5 du Plan 01).

Couvre via httpx.AsyncClient (ASGITransport asynchrone pur) :
- GET /api/health
- GET /api/generations (avec filtres favorite, mediaType, projectId, search q)
- PATCH /api/generations/{id}/favorite
- DELETE /api/generations/{id} (suppression transactionnelle avec rollback)
- GET /api/brand-kits
- POST /api/brand-kits (Blank, files, website, validation SSRF et redirection)
- GET /api/projects
- POST /api/projects (avec validation storagePath)
- POST /api/config/colab-url
"""

from __future__ import annotations

import contextlib
import ipaddress
import socket
import unittest.mock
from pathlib import Path

import httpx
import pytest

from app.api import routes_crud
from app.main import app
from app.services.brand_extractor import BrandKitExtractor
from app.storage.json_store import JSONDocumentStore
from app.storage.media_store import MediaFileStore


class MockResp:
    def __init__(
        self,
        status_code: int = 200,
        text: str = "",
        headers: dict | None = None,
        url: str = "https://google.com",
        server_ip: str | None = None,
    ):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}
        self.url = httpx.URL(url)
        self.extensions: dict = {}
        if server_ip:
            stream = unittest.mock.Mock()
            stream.get_extra_info.return_value = (server_ip, 443)
            self.extensions["network_stream"] = stream


def mock_http(monkeypatch, responses):
    class Client:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            if callable(responses):
                return responses(url)
            return responses.pop(0) if isinstance(responses, list) else responses

    monkeypatch.setattr(httpx, "AsyncClient", Client)


def _gen(
    gid: str,
    mt: str,
    prompt: str,
    fav: bool = False,
    proj: str = "p",
    fp: str = "",
    tp: str = "",
    dt: str = "2026-10-09T10:00:00Z",
):
    return {
        "id": gid,
        "mediaType": mt,
        "prompt": prompt,
        "modelName": "Seedance 2.5",
        "isFavorite": fav,
        "projectId": proj,
        "filePath": fp,
        "thumbnailPath": tp,
        "createdAt": dt,
    }


@pytest.fixture
async def test_env(tmp_path: Path):
    data_dir, outputs_dir, assets_dir = (
        tmp_path / "data",
        tmp_path / "outputs",
        tmp_path / "data" / "assets",
    )
    for d in (data_dir, outputs_dir, assets_dir):
        d.mkdir(parents=True, exist_ok=True)
    store = JSONDocumentStore(data_dir)
    media_store = MediaFileStore(outputs_dir)
    extractor = BrandKitExtractor(assets_dir)
    routes_crud._json_store, routes_crud._media_store, routes_crud._extractor = (
        store,
        media_store,
        extractor,
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, store, media_store, data_dir


@pytest.fixture(autouse=True)
def mock_dns_resolution(monkeypatch):
    def deterministic_getaddrinfo(host, port, *_, **__):
        with contextlib.suppress(ValueError):
            if not ipaddress.ip_address(host).is_global:
                return [(2, 1, 6, "", (host, port))]
        if host in ("127.0.0.1", "localhost", "::1") or host.endswith((".local", ".internal")):
            return [(2, 1, 6, "", ("127.0.0.1", port))]
        return [(2, 1, 6, "", ("93.184.216.34", port))]

    monkeypatch.setattr(socket, "getaddrinfo", deterministic_getaddrinfo)


async def test_health_check(test_env):
    client, _, _, _ = test_env
    res = await client.get("/api/health")
    assert res.status_code == 200 and res.json()["status"] == "healthy"


async def test_generations_crud_and_filters(test_env):
    client, store, media_store, data_dir = test_env
    fp, tp = str(data_dir / "gen_1.mp4"), str(data_dir / "gen_1.jpg")
    g1 = _gen("gen_1", "video", "Aerial misty forest", False, "proj_a", fp, tp)
    g2 = _gen("gen_2", "image", "Cyberpunk night", True, "proj_b", dt="2026-10-09T11:00:00Z")
    await store.write_list("generations.json", [g1, g2])

    res_all = (await client.get("/api/generations")).json()
    assert len(res_all) == 2
    assert res_all[0]["id"] == "gen_2" and res_all[1]["id"] == "gen_1"
    assert (await client.get("/api/generations?favorite=true")).json()[0]["id"] == "gen_2"
    assert (await client.get("/api/generations?mediaType=video")).json()[0]["id"] == "gen_1"
    assert (await client.get("/api/generations?q=misty")).json()[0]["id"] == "gen_1"

    # Toggle favorite
    assert (await client.patch("/api/generations/gen_1/favorite")).json()["isFavorite"] is True

    # Delete generation
    Path(fp).write_text("dummy")
    Path(tp).write_text("dummy")
    assert (await client.delete("/api/generations/gen_1")).json()["deleted"] is True
    assert not Path(fp).exists() and not Path(tp).exists()
    assert len(await store.read_list("generations.json")) == 1

    # Physical deletion staging failure propagates 500 and preserves JSON
    with unittest.mock.patch.object(media_store, "stage_delete_media", side_effect=OSError("Disk")):
        assert (await client.delete("/api/generations/gen_2")).status_code == 500
    assert any(it["id"] == "gen_2" for it in await store.read_list("generations.json"))


async def test_delete_generation_transactional_rollback(test_env, monkeypatch):
    client, store, _, data_dir = test_env
    fp, tp = data_dir / "rb.mp4", data_dir / "rb.jpg"
    fp.write_bytes(b"VIDEO")
    tp.write_bytes(b"THUMB")
    await store.write_list(
        "generations.json", [{"id": "gen_rb", "filePath": str(fp), "thumbnailPath": str(tp)}]
    )

    monkeypatch.setattr(
        store, "write_list_unlocked", unittest.mock.AsyncMock(side_effect=OSError("Disque plein"))
    )
    with pytest.raises(OSError, match="Disque plein"):
        await client.delete("/api/generations/gen_rb")
    assert fp.exists() and tp.exists() and fp.read_bytes() == b"VIDEO"


async def test_projects_crud_and_storage_path_validation(test_env, tmp_path):
    client, _, _, _ = test_env
    res = await client.post("/api/projects", json={"name": "Court Métrage", "colorTag": "#3B82F6"})
    assert res.status_code == 201 and res.json()["colorTag"] == "#3B82F6"

    custom_dir = tmp_path / "custom_storage"
    res_c = await client.post("/api/projects", json={"name": "Iso", "storagePath": str(custom_dir)})
    assert res_c.status_code == 201 and custom_dir.exists()

    file_as_dir = tmp_path / "file_exists.txt"
    file_as_dir.write_text("hello")
    for bad in ("/etc/shadow", ".githooks", "not_a_hex", str(file_as_dir)):
        key = "storagePath" if "/" in bad or "." in bad else "colorTag"
        assert (
            await client.post("/api/projects", json={"name": "Bad", key: bad})
        ).status_code == 422

    assert len((await client.get("/api/projects")).json()) == 2


async def test_brand_kits_crud_blank_and_files(test_env, monkeypatch):
    client, _, _, _ = test_env
    # 1. Blank
    res_b = await client.post("/api/brand-kits", data={"name": "Apple", "overview": "Minimal."})
    assert res_b.status_code == 201 and res_b.json()["name"] == "Apple"

    # 2. Extract from SVG file
    svg = b'<svg><rect fill="#FF0000" /><circle fill="#00FF00" /></svg>'
    f_svg = [("files", ("logo.svg", svg, "image/svg+xml"))]
    res_f = await client.post("/api/brand-kits", data={"name": "Colors"}, files=f_svg)
    assert res_f.status_code == 201 and len(res_f.json()["logos"]) == 1

    # 3. Extract from website with title, description, colors and fonts
    html = (
        "<title>Horizon</title><meta name='description' content='Cinematic AI'>"
        "<link rel='icon' href='/favicon.ico'>"
        "<style>:root{--primary:#0A84FF;}body{font-family:'Cabinet Grotesk';}</style>"
    )
    mock_http(monkeypatch, MockResp(text=html, url="https://horizon.ai"))
    res_w = await client.post(
        "/api/brand-kits", data={"name": "Horizon", "websiteUrl": "https://horizon.ai"}
    )
    assert res_w.status_code == 201
    bk = res_w.json()
    assert "Cinematic AI" in bk["overview"] and "#0A84FF" in [c["hex"] for c in bk["colors"]]
    assert any("Cabinet Grotesk" in f["family"] for f in bk["fonts"]) and len(bk["logos"]) >= 1
    assert len((await client.get("/api/brand-kits")).json()) == 3

    # 4. Over 50 MB cap returns 413
    res_h = await client.post(
        "/api/brand-kits",
        data={"name": "H"},
        files=[("files", ("h.bin", b"X" * (51 * 1024 * 1024), "app/bin"))],
    )
    assert res_h.status_code == 413

    # 5. Extract fonts from CSS
    css = (
        b"@font-face { font-family: 'Montserrat'; }\n"
        b"body { font-family: 'Open Sans'; color: #123; }"
    )
    res_c = await client.post(
        "/api/brand-kits", data={"name": "Fonts"}, files=[("files", ("s.css", css, "text/css"))]
    )
    assert res_c.status_code == 201
    fams = [f["family"] for f in res_c.json()["fonts"]]
    assert "Montserrat" in fams or "Open Sans" in fams


async def test_csrf_and_untrusted_origin_rejection(test_env):
    client, _, _, _ = test_env
    res_cross = await client.post(
        "/api/brand-kits", data={"name": "Attacker"}, headers={"sec-fetch-site": "cross-site"}
    )
    res_bad = await client.post(
        "/api/projects", json={"name": "Attacker"}, headers={"origin": "http://evil.com"}
    )
    assert res_cross.status_code == 403 and res_bad.status_code == 403


async def test_brand_kit_ssrf_rejects_private_and_redirects(test_env, monkeypatch):
    client, _, _, _ = test_env
    # 1. Direct IPs & local hostnames
    for url in ("http://127.0.0.1:8190/secret", "http://localhost:8000/private"):
        res = await client.post("/api/brand-kits", data={"name": "Attacker", "websiteUrl": url})
        assert res.status_code == 400 and (
            "interdit" in res.json()["detail"].lower() or "privée" in res.json()["detail"].lower()
        )
    # 2. Redirect to private IP
    mock_http(
        monkeypatch,
        MockResp(302, headers={"location": "http://127.0.0.1:8190/admin"}, url="https://pub.com"),
    )
    res = await client.post(
        "/api/brand-kits", data={"name": "Sneaky", "websiteUrl": "https://pub.com"}
    )
    assert res.status_code == 400 and (
        "interdit" in res.json()["detail"].lower() or "privée" in res.json()["detail"].lower()
    )
    # 3. DNS rebinding on connected socket
    mock_http(monkeypatch, MockResp(server_ip="127.0.0.1", url="https://pub.com"))
    res_r = await client.post(
        "/api/brand-kits", data={"name": "Rebind", "websiteUrl": "https://pub.com"}
    )
    assert res_r.status_code == 400 and "privée" in res_r.json()["detail"].lower()


async def test_brand_kit_website_http_error_returns_400(test_env, monkeypatch):
    client, _, _, _ = test_env
    mock_http(monkeypatch, MockResp(404, text="Not Found", url="https://google.com/404"))
    res = await client.post(
        "/api/brand-kits", data={"name": "Broken", "websiteUrl": "https://google.com/404"}
    )
    assert res.status_code == 400 and "404" in res.json()["detail"]


async def test_brand_kit_favicon_resolves_against_redirect_url(test_env, monkeypatch):
    client, _, _, _ = test_env
    resps = [
        MockResp(
            301, headers={"location": "https://google.com/brand/home"}, url="https://g.com/old"
        ),
        MockResp(
            200, text='<link rel="icon" href="favicon.ico">', url="https://google.com/brand/home"
        ),
    ]
    mock_http(monkeypatch, resps)
    res = await client.post(
        "/api/brand-kits", data={"name": "Fav", "websiteUrl": "https://g.com/old"}
    )
    assert res.status_code == 201
    assert res.json()["logos"][0]["filePath"] == "https://google.com/brand/favicon.ico"


async def test_config_colab_url_update(test_env):
    client, _, _, _ = test_env
    res = await client.post(
        "/api/config/colab-url", json={"tunnelUrl": "https://active-tunnel-123.ngrok-free.app"}
    )
    assert res.status_code == 200
    assert res.json()["tunnelUrl"] == "https://active-tunnel-123.ngrok-free.app"
