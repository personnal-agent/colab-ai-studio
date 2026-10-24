"""Tests unitaires pour JSONDocumentStore (Step 3 du Plan 01)."""

from __future__ import annotations

import asyncio
import os
import unittest.mock
from pathlib import Path

import pytest

from app.storage.json_store import CorruptedDocumentStoreError, JSONDocumentStore


@pytest.fixture
def store(tmp_path: Path) -> JSONDocumentStore:
    return JSONDocumentStore(data_dir=tmp_path)


async def test_read_empty_collection_returns_empty_list(store: JSONDocumentStore):
    assert await store.read_list("generations.json") == []


async def test_atomic_write_and_read_roundtrip(store: JSONDocumentStore):
    items = [{"id": "gen_1", "prompt": "test 1"}, {"id": "gen_2", "prompt": "test 2"}]
    await store.write_list("generations.json", items)
    assert await store.read_list("generations.json") == items


async def test_concurrent_writes_are_serialized(store: JSONDocumentStore):
    async def append_item(idx: int) -> None:
        async with store.lock_for("generations.json"):
            current = await store.read_list_unlocked("generations.json")
            current.append({"id": f"gen_{idx}", "order": idx})
            await store.write_list_unlocked("generations.json", current)

    await asyncio.gather(*(append_item(i) for i in range(10)))
    final = await store.read_list("generations.json")
    assert len(final) == 10 and {item["id"] for item in final} == {f"gen_{i}" for i in range(10)}


async def test_atomic_replace_leaves_no_temp_files(store: JSONDocumentStore, tmp_path: Path):
    await store.write_list("generations.json", [{"id": "gen_clean"}])
    assert list(tmp_path.glob("*.tmp")) == [] and (tmp_path / "generations.json").exists()


async def test_singleton_config_read_and_write(store: JSONDocumentStore):
    cfg = await store.read_dict("config.json", default={"executionMode": "colab"})
    assert cfg["executionMode"] == "colab"
    await store.write_dict(
        "config.json",
        {"executionMode": "local", "local": {"workerUrl": "http://127.0.0.1:8190"}},
    )
    reloaded = await store.read_dict("config.json")
    assert (
        reloaded["executionMode"] == "local"
        and reloaded["local"]["workerUrl"] == "http://127.0.0.1:8190"
    )


async def test_partial_write_failure_does_not_corrupt_existing_file(
    store: JSONDocumentStore, tmp_path: Path, monkeypatch
):
    initial = [{"id": "safe_item", "value": 42}]
    await store.write_list("generations.json", initial)
    monkeypatch.setattr(
        os, "replace", unittest.mock.Mock(side_effect=OSError("Simulated replace fail"))
    )
    with pytest.raises(OSError, match="Simulated replace fail"):
        await store.write_list("generations.json", [{"id": "corrupted"}])
    assert await store.read_list("generations.json") == initial


@pytest.mark.parametrize(
    ("filename", "content", "err_match"),
    [
        ("generations.json", "{ unclosed invalid json ...", "Fichier JSON corrompu"),
        (
            "generations.json",
            '{"error": "expected a list"}',
            "Type inattendu dans generations.json",
        ),
        ("brand-kits.json", "", "vide ou corrompu"),
    ],
)
async def test_corrupted_json_raises(
    store: JSONDocumentStore, tmp_path: Path, filename: str, content: str, err_match: str
):
    (tmp_path / filename).write_text(content, encoding="utf-8")
    with pytest.raises(CorruptedDocumentStoreError, match=err_match):
        await store.read_list(filename)


async def test_corrupted_json_refuses_subsequent_writes(store: JSONDocumentStore, tmp_path: Path):
    (tmp_path / "generations.json").write_text("{ corrupted", encoding="utf-8")
    with pytest.raises(CorruptedDocumentStoreError):
        await store.read_list("generations.json")
    with pytest.raises(CorruptedDocumentStoreError, match="Écriture refusée"):
        await store.write_list("generations.json", [{"id": "new"}])


async def test_direct_write_to_damaged_file_is_refused(store: JSONDocumentStore, tmp_path: Path):
    (tmp_path / "config.json").write_text("NOT_JSON", encoding="utf-8")
    with pytest.raises(CorruptedDocumentStoreError, match="Écriture refusée"):
        await store.write_dict("config.json", {"k": "v"})


async def test_repaired_file_recovers_and_allows_write(store: JSONDocumentStore, tmp_path: Path):
    f = tmp_path / "projects.json"
    f.write_text("CORRUPTED", encoding="utf-8")
    with pytest.raises(CorruptedDocumentStoreError):
        await store.read_list("projects.json")
    assert store.is_corrupted("projects.json")

    # Repair file
    f.write_text('[{"id": "p1", "name": "Repaired"}]', encoding="utf-8")
    data = await store.read_list("projects.json")
    assert len(data) == 1 and not store.is_corrupted("projects.json")
    data.append({"id": "p2"})
    await store.write_list("projects.json", data)
    assert len(await store.read_list("projects.json")) == 2
