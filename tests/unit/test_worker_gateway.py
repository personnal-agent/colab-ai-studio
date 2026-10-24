"""Tests unitaires pour WorkerGateway (app/services/worker_gateway.py)."""

from __future__ import annotations

import httpx
import pytest

from app.models.domain import ColabConfig, ExecutionMode, LocalConfig, StudioConfig
from app.services.worker_gateway import (
    WorkerGateway,
    WorkerNotConfiguredError,
    WorkerUnavailableError,
)
from app.storage.json_store import JSONDocumentStore


@pytest.fixture
def store(tmp_path):
    return JSONDocumentStore(tmp_path)


@pytest.mark.asyncio
async def test_resolve_worker_url_dynamically(store):
    cfg = StudioConfig(
        executionMode=ExecutionMode.COLAB,
        colab=ColabConfig(tunnelUrl="https://active-colab.ngrok-free.app"),
        local=LocalConfig(workerUrl="http://127.0.0.1:8190"),
    )
    await store.write_dict("config.json", cfg.model_dump())
    gw = WorkerGateway(json_store=store)

    assert await gw.get_active_worker_url() == ("colab", "https://active-colab.ngrok-free.app")
    cfg.executionMode = ExecutionMode.LOCAL
    await store.write_dict("config.json", cfg.model_dump())
    assert await gw.get_active_worker_url() == ("local", "http://127.0.0.1:8190")
    await gw.aclose()


@pytest.mark.asyncio
async def test_unconfigured_colab_raises_explicit_error(store):
    await store.write_dict(
        "config.json", StudioConfig(executionMode=ExecutionMode.COLAB).model_dump()
    )
    gw = WorkerGateway(json_store=store)
    with pytest.raises(WorkerNotConfiguredError, match="Worker Colab non configuré"):
        await gw.get_active_worker_url()
    await gw.aclose()


@pytest.mark.asyncio
async def test_health_check_success_and_latency(store):
    await store.write_dict(
        "config.json",
        StudioConfig(
            executionMode=ExecutionMode.LOCAL, local=LocalConfig(workerUrl="http://127.0.0.1:8190")
        ).model_dump(),
    )

    def handler(r):
        return httpx.Response(200, json={"status": "ready", "gpu": "RTX 4090", "vramFreeMb": 18450})

    gw = WorkerGateway(
        json_store=store, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    res = await gw.health()
    assert res["worker"]["reachable"] and res["worker"]["gpu"] == "RTX 4090"
    await gw.aclose()


@pytest.mark.asyncio
async def test_health_check_unreachable_worker(store):
    await store.write_dict(
        "config.json",
        StudioConfig(
            executionMode=ExecutionMode.LOCAL, local=LocalConfig(workerUrl="http://127.0.0.1:8190")
        ).model_dump(),
    )

    def handler(r):
        raise httpx.ConnectError("Offline")

    gw = WorkerGateway(
        json_store=store, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    res = await gw.health()
    assert not res["worker"]["reachable"] and "Offline" in res["worker"]["error"]
    await gw.aclose()


@pytest.mark.asyncio
async def test_list_and_switch_models(store):
    await store.write_dict(
        "config.json",
        StudioConfig(
            executionMode=ExecutionMode.COLAB,
            colab=ColabConfig(tunnelUrl="https://colab.ngrok-free.app"),
        ).model_dump(),
    )

    def handler(r):
        if r.url.path == "/models":
            return httpx.Response(200, json=[{"id": "wan2.1", "name": "Wan 2.1"}])
        return httpx.Response(200, json={"status": "switched", "activeModel": "wan2.1"})

    gw = WorkerGateway(
        json_store=store, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    models = await gw.list_models()
    assert len(models) == 1 and models[0]["id"] == "wan2.1"
    assert (await gw.switch_model("wan2.1"))["activeModel"] == "wan2.1"
    await gw.aclose()


@pytest.mark.asyncio
async def test_worker_unavailable_error_on_network_failure(store):
    await store.write_dict(
        "config.json",
        StudioConfig(
            executionMode=ExecutionMode.LOCAL, local=LocalConfig(workerUrl="http://127.0.0.1:8190")
        ).model_dump(),
    )

    def handler(r):
        raise httpx.ConnectError("Offline")

    gw = WorkerGateway(
        json_store=store, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    with pytest.raises(WorkerUnavailableError):
        await gw.list_models()
    with pytest.raises(WorkerUnavailableError):
        await gw.switch_model("wan2.1")
    await gw.aclose()


@pytest.mark.asyncio
async def test_worker_gateway_download_file_anti_ssrf(store):
    await store.write_dict(
        "config.json",
        StudioConfig(
            executionMode=ExecutionMode.LOCAL,
            local=LocalConfig(workerUrl="http://127.0.0.1:8190"),
        ).model_dump(),
    )

    def handler(r):
        return httpx.Response(200, content=b"BIN_OK")

    gw = WorkerGateway(
        json_store=store,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    # 1. Path traversal rejeté
    with pytest.raises(ValueError, match="path traversal"):
        await gw.download_file("../../etc/passwd")

    # 2. SSRF vers hôte externe non autorisé rejeté
    with pytest.raises(ValueError, match="Accès refusé"):
        await gw.download_file("http://attacker.com/steal")

    # 3. URL légitime vers le worker local autorisée
    res1 = await gw.download_file("output.mp4")
    assert res1 == b"BIN_OK"

    res2 = await gw.download_file("http://127.0.0.1:8190/files/output.mp4")
    assert res2 == b"BIN_OK"

    await gw.aclose()
