"""Tests unitaires pour JSONDocumentStore (Step 3 du Plan 01).

Vérifie l'écriture atomique (.tmp + os.replace), la sérialisation concurrente
via asyncio.Lock, et la résilience aux écritures corrompues ou concurrentes.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from app.storage.json_store import CorruptedDocumentStoreError, JSONDocumentStore


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


async def test_corrupted_json_raises_and_prevents_silent_data_loss(
    store: JSONDocumentStore, tmp_path: Path
):
    target_file = tmp_path / "generations.json"
    target_file.write_text("{ unclosed invalid json ...", encoding="utf-8")

    with pytest.raises(CorruptedDocumentStoreError, match="Fichier JSON corrompu"):
        await store.read_list("generations.json")


async def test_invalid_json_type_raises_corrupted_document_store_error(
    store: JSONDocumentStore, tmp_path: Path
):
    target_file = tmp_path / "generations.json"
    target_file.write_text('{"error": "expected a list but got a dict"}', encoding="utf-8")

    with pytest.raises(CorruptedDocumentStoreError, match="Type inattendu dans generations.json"):
        await store.read_list("generations.json")


async def test_corrupted_json_refuses_subsequent_writes(store: JSONDocumentStore, tmp_path: Path):
    target_file = tmp_path / "generations.json"
    target_file.write_text("{ corrupted invalid json ...", encoding="utf-8")

    # 1. La lecture échoue et marque le fichier comme corrompu
    with pytest.raises(CorruptedDocumentStoreError):
        await store.read_list("generations.json")

    # 2. Toute tentative d'écriture ultérieure est rejetée pour préserver l'intégrité
    with pytest.raises(CorruptedDocumentStoreError, match="Écriture refusée"):
        await store.write_list("generations.json", [{"id": "new_item"}])


async def test_empty_existing_file_raises_and_refuses_overwrite(
    store: JSONDocumentStore, tmp_path: Path
):
    target_file = tmp_path / "brand-kits.json"
    target_file.write_text("", encoding="utf-8")

    # Un fichier existant vide est corrompu et ne doit pas être traité comme absent
    with pytest.raises(CorruptedDocumentStoreError, match="vide ou corrompu"):
        await store.read_list("brand-kits.json")

    with pytest.raises(CorruptedDocumentStoreError, match="Écriture refusée"):
        await store.write_list("brand-kits.json", [{"id": "bk_1"}])


async def test_direct_write_to_damaged_file_is_refused(store: JSONDocumentStore, tmp_path: Path):
    target_file = tmp_path / "config.json"
    target_file.write_text("NOT_JSON", encoding="utf-8")

    with pytest.raises(CorruptedDocumentStoreError, match="Écriture refusée"):
        await store.write_dict("config.json", {"key": "val"})
