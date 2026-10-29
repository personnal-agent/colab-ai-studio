"""Tests unitaires pour MediaFileStore64k et le protocole de publication no-replace."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.models.domain import Project
from app.storage.json_store import JSONDocumentStore
from app.storage.media_file_store_64k import (
    DestinationCollisionError,
    MediaFileStore64k,
    StagingIntegrityError,
)


@pytest.fixture
def stores(tmp_path: Path):
    outputs_dir = tmp_path / "outputs"
    journal_dir = tmp_path / "journal"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    journal_dir.mkdir(parents=True, exist_ok=True)

    json_store = JSONDocumentStore(journal_dir)
    store64k = MediaFileStore64k(outputs_dir, json_store=json_store)
    return store64k, outputs_dir, json_store


@pytest.mark.asyncio
async def test_stream_write_temp_nominal(stores):
    store64k, _, _ = stores
    data = b"Omniforge V3 Streaming Chunks Test" * 2000  # ~70 Ko (> 64 Ko)
    chunks = [data[:65536], data[65536:]]

    expected_digest = hashlib.sha256(data).hexdigest()
    expected_size = len(data)

    temp_path, digest, size = await store64k.stream_write_temp("render.mp4", chunks)

    assert Path(temp_path).is_file()
    assert digest == expected_digest
    assert size == expected_size
    assert Path(temp_path).stat().st_size == expected_size

    # Nettoyage
    Path(temp_path).unlink()


@pytest.mark.asyncio
async def test_stream_write_temp_async_iterator(stores):
    store64k, _, _ = stores
    data = b"Asynchronous Streaming 64K Chunk Generator Data" * 1500
    expected_digest = hashlib.sha256(data).hexdigest()

    async def async_chunk_generator():
        offset = 0
        while offset < len(data):
            yield data[offset : offset + 32768]
            offset += 32768

    temp_path, digest, size = await store64k.stream_write_temp(
        "render_async.mp4", async_chunk_generator()
    )
    assert Path(temp_path).is_file()
    assert digest == expected_digest
    assert size == len(data)

    Path(temp_path).unlink()


@pytest.mark.asyncio
async def test_stage_and_publish_no_replace_nominal(stores):
    store64k, outputs_dir, _ = stores
    data = b"Video Frame 64K Binary Stream Content"
    chunks = [data]
    expected_digest = hashlib.sha256(data).hexdigest()

    temp_path, digest, size = await store64k.stream_write_temp("scene_01.mp4", chunks)
    assert digest == expected_digest

    op_id = "op-test-101"
    key = "ws1::gen1::art1"

    staged_entry = await store64k.stage_operation(
        operation_id=op_id,
        resource_key=key,
        temp_path=temp_path,
        final_filename="scene_01.mp4",
        sha256_digest=digest,
        byte_size=size,
    )
    assert staged_entry["status"] == "STAGED"

    # Vérification que le fichier temporaire existe mais pas la destination
    final_path = Path(staged_entry["finalPath"])
    assert not final_path.exists()
    assert Path(temp_path).exists()

    # Publication no-replace
    published_path = await store64k.publish_no_replace(op_id)
    assert Path(published_path).is_file()
    assert not Path(temp_path).exists()  # Temporaire supprimé après lien réussi

    # Vérification du contenu du fichier publié
    assert Path(published_path).read_bytes() == data

    # Validation de l'état dans le journal
    pending = await store64k.list_pending_operations()
    assert len(pending) == 1
    assert pending[0]["status"] == "PUBLISHED_PENDING_COMMIT"

    # Confirmation de commit après indexation SQLite
    await store64k.commit_operation(op_id)
    pending_after_commit = await store64k.list_pending_operations()
    assert len(pending_after_commit) == 0


@pytest.mark.asyncio
async def test_publish_no_replace_collision_rejection(stores):
    store64k, outputs_dir, _ = stores
    data_existing = b"Preexisting File Content"
    data_new = b"New Incoming Conflicting Stream"

    # Création préalable d'un fichier de destination existant
    dest_dir = store64k.resolve_destination_dir(None)
    final_file = dest_dir / "collision_target.mp4"
    final_file.write_bytes(data_existing)

    temp_path, digest, size = await store64k.stream_write_temp("collision_target.mp4", [data_new])

    op_id = "op-collision-test"
    await store64k.stage_operation(
        operation_id=op_id,
        resource_key="key-collision",
        temp_path=temp_path,
        final_filename="collision_target.mp4",
        sha256_digest=digest,
        byte_size=size,
    )

    # La publication doit rejeter avec DestinationCollisionError (no-replace garanti)
    with pytest.raises(DestinationCollisionError, match="la destination.*existe déjà"):
        await store64k.publish_no_replace(op_id)

    # Le fichier préexistant DOIT être intact (jamais écrasé)
    assert final_file.read_bytes() == data_existing
    # Le temporaire reste conservé pour analyse ou reprise
    assert Path(temp_path).is_file()


@pytest.mark.asyncio
async def test_publish_no_replace_identical_digest_idempotent(stores):
    store64k, outputs_dir, _ = stores
    data_content = b"Identical Content for Idempotency Test"

    dest_dir = store64k.resolve_destination_dir(None)
    final_file = dest_dir / "idempotent_target.png"
    final_file.write_bytes(data_content)

    temp_path, digest, size = await store64k.stream_write_temp(
        "idempotent_target.png", [data_content]
    )

    op_id = "op-idempotent-test"
    await store64k.stage_operation(
        operation_id=op_id,
        resource_key="key-idempotent",
        temp_path=temp_path,
        final_filename="idempotent_target.png",
        sha256_digest=digest,
        byte_size=size,
    )

    published = await store64k.publish_no_replace(op_id)
    assert published == str(final_file)
    assert final_file.is_file()
    assert not Path(temp_path).exists()
    final_file.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_abort_and_compensate_cleans_up(stores):
    store64k, _, _ = stores
    data = b"Temporary Content to Abort"
    temp_path, digest, size = await store64k.stream_write_temp("aborted.mp4", [data])

    op_id = "op-abort-test"
    await store64k.stage_operation(
        operation_id=op_id,
        resource_key="key-abort",
        temp_path=temp_path,
        final_filename="aborted.mp4",
        sha256_digest=digest,
        byte_size=size,
    )

    # Publication effectuée mais SQLite rejecte ou timeout
    published = await store64k.publish_no_replace(op_id)
    assert Path(published).exists()

    # Déclenchement de la compensation d'abandon
    await store64k.abort_and_compensate(op_id)

    # La destination et le temporaire ont été nettoyés chirurgicalement
    assert not Path(published).exists()
    assert not Path(temp_path).exists()

    # Le journal a consigné l'abandon
    pending = await store64k.list_pending_operations()
    assert len(pending) == 0


@pytest.mark.asyncio
async def test_publish_divergent_digest_rejection(stores):
    store64k, _, _ = stores
    data = b"Initial Source Chunk Data"
    temp_path, _, size = await store64k.stream_write_temp("divergent.mp4", [data])

    fake_digest = "0000000000000000000000000000000000000000000000000000000000000000"
    op_id = "op-divergent-test"
    await store64k.stage_operation(
        operation_id=op_id,
        resource_key="key-divergent",
        temp_path=temp_path,
        final_filename="divergent.mp4",
        sha256_digest=fake_digest,
        byte_size=size,
    )

    with pytest.raises(StagingIntegrityError, match="Digest final divergent"):
        await store64k.publish_no_replace(op_id)

    # Nettoyage
    dest_file = Path(store64k.resolve_destination_dir(None)) / "divergent.mp4"
    if dest_file.exists():
        dest_file.unlink()


@pytest.mark.asyncio
async def test_project_custom_storage_path(stores, tmp_path):
    store64k, _, _ = stores
    custom_dir = tmp_path / "custom_client_drive"
    custom_dir.mkdir(parents=True, exist_ok=True)

    project = Project(id="proj-custom-01", name="Custom Project", storagePath=str(custom_dir))

    data = b"Custom Storage Project Data"
    temp_path, digest, size = await store64k.stream_write_temp(
        "asset.png", [data], project=project
    )

    # Le temporaire doit se trouver dans le dossier custom
    assert str(custom_dir) in temp_path

    op_id = "op-custom-storage"
    await store64k.stage_operation(
        operation_id=op_id,
        resource_key="key-proj",
        temp_path=temp_path,
        final_filename="asset.png",
        sha256_digest=digest,
        byte_size=size,
        project=project,
    )

    published = await store64k.publish_no_replace(op_id)
    assert str(custom_dir) in published
    assert Path(published).is_file()
    assert Path(published).read_bytes() == data

    await store64k.commit_operation(op_id)
