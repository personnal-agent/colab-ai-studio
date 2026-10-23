"""Tests unitaires pour JSONDocumentStore (Step 3 du Plan 01).

Vérifie l'écriture atomique (.tmp + os.replace), la sérialisation concurrente
via asyncio.Lock, et la résilience aux écritures corrompues ou concurrentes.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from app.storage.json_store import JSONDocumentStore


@pytest.fixture
def store(tmp_path: Path) -> JSONDocumentStore:
    return JSONDocumentStore(data_dir=tmp_path)


async def test_read_empty_collection_returns_empty_list(store: JSONDocumentStore):
    data = await store.read_list("generations.json")
    assert data == []


async def test_atomic_write_and_read_roundtrip(store: JSONDocumentStore):
    items = [{"id": "gen_1", "prompt": "test 1"}, {"id": "gen_2", "prompt": "test 2"}]
    await store.write_list("generations.json", items)
    loaded = await store.read_list("generations.json")
    assert loaded == items


async def test_concurrent_writes_are_serialized(store: JSONDocumentStore):
    async def append_item(idx: int) -> None:
        async with store.lock_for("generations.json"):
            current = await store.read_list_unlocked("generations.json")
            current.append({"id": f"gen_{idx}", "order": idx})
            await store.write_list_unlocked("generations.json", current)

    await asyncio.gather(*(append_item(i) for i in range(10)))
    final = await store.read_list("generations.json")
    assert len(final) == 10
    ids = {item["id"] for item in final}
    assert ids == {f"gen_{i}" for i in range(10)}


async def test_atomic_replace_leaves_no_temp_files(store: JSONDocumentStore, tmp_path: Path):
    await store.write_list("generations.json", [{"id": "gen_clean"}])
    tmp_files = list(tmp_path.glob("*.tmp"))
    assert tmp_files == []
    assert (tmp_path / "generations.json").exists()


async def test_singleton_config_read_and_write(store: JSONDocumentStore):
    default_config = {"executionMode": "colab", "colab": {"tunnelUrl": ""}}
    loaded_default = await store.read_dict("config.json", default=default_config)
    assert loaded_default["executionMode"] == "colab"

    modified = {"executionMode": "local", "local": {"workerUrl": "http://127.0.0.1:8190"}}
    await store.write_dict("config.json", modified)

    reloaded = await store.read_dict("config.json")
    assert reloaded["executionMode"] == "local"
    assert reloaded["local"]["workerUrl"] == "http://127.0.0.1:8190"


async def test_partial_write_failure_does_not_corrupt_existing_file(
    store: JSONDocumentStore, tmp_path: Path, monkeypatch
):
    initial = [{"id": "safe_item", "value": 42}]
    await store.write_list("generations.json", initial)

    import os

    def failing_replace(src, dst):
        raise OSError("Simulated disk failure during replace")

    monkeypatch.setattr(os, "replace", failing_replace)

    with pytest.raises(OSError, match="Simulated disk failure"):
        await store.write_list("generations.json", [{"id": "corrupted"}])

    intact = await store.read_list("generations.json")
    assert intact == initial
