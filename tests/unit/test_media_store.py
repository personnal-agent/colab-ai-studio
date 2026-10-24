"""Tests unitaires pour MediaFileStore (Step 4 du Plan 01).

Vérifie :
1. Règle d'isolation Project.storagePath exclusif (0 fichier dans outputs/).
2. Règle projet sans storagePath -> outputs/projects/<id>/.
3. Règle hors projet -> outputs/YYYY-MM-DD/.
4. Sauvegarde binaire et miniature.
5. Suppression sur disque.
6. Prévention path traversal sur storagePath malveillant.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config import REPO_ROOT
from app.models.domain import Project
from app.storage.media_store import MediaFileStore


@pytest.fixture
def base_dirs(tmp_path: Path):
    outputs = tmp_path / "outputs"
    custom_project_dir = tmp_path / "custom_project_storage"
    return outputs, custom_project_dir


def test_resolve_destination_with_custom_storage_path(base_dirs):
    outputs, custom_dir = base_dirs
    store = MediaFileStore(outputs_dir=outputs)
    project = Project(
        id="proj_court_metrage_01",
        name="Brume",
        storagePath=str(custom_dir),
    )
    dest_dir = store.resolve_destination_dir(project=project)
    assert dest_dir == custom_dir.resolve()
    assert dest_dir.exists()


def test_resolve_destination_with_project_no_storage_path(base_dirs):
    outputs, _ = base_dirs
    store = MediaFileStore(outputs_dir=outputs)
    project = Project(
        id="proj_standard",
        name="Standard",
        storagePath=None,
    )
    dest_dir = store.resolve_destination_dir(project=project)
    assert dest_dir == (outputs / "projects" / "proj_standard").resolve()
    assert dest_dir.exists()


def test_resolve_destination_no_project_chronological(base_dirs):
    outputs, _ = base_dirs
    store = MediaFileStore(outputs_dir=outputs)
    dest_dir = store.resolve_destination_dir(project=None)
    # Vérifie le format outputs/YYYY-MM-DD
    assert dest_dir.parent == outputs.resolve()
    assert len(dest_dir.name) == 10  # YYYY-MM-DD
    assert dest_dir.name.count("-") == 2
    assert dest_dir.exists()


async def test_save_binary_in_custom_storage_creates_zero_files_in_outputs(base_dirs):
    outputs, custom_dir = base_dirs
    store = MediaFileStore(outputs_dir=outputs)
    project = Project(
        id="proj_isolated",
        name="Isolated",
        storagePath=str(custom_dir),
    )
    file_bytes = b"FAKE_MP4_CONTENT"
    thumb_bytes = b"FAKE_THUMBNAIL_JPG"

    saved_path, thumb_path = await store.save_media(
        filename="gen_test_01.mp4",
        content=file_bytes,
        project=project,
        thumbnail_content=thumb_bytes,
    )

    assert Path(saved_path).read_bytes() == file_bytes
    assert Path(thumb_path).read_bytes() == thumb_bytes
    assert str(custom_dir) in saved_path

    # Invariant strict : 0 fichier dans outputs/
    output_files = list(outputs.rglob("*"))
    assert output_files == []


async def test_delete_media_removes_both_files(base_dirs):
    outputs, _ = base_dirs
    store = MediaFileStore(outputs_dir=outputs)
    saved_path, thumb_path = await store.save_media(
        filename="gen_to_delete.mp4",
        content=b"DATA",
        project=None,
        thumbnail_content=b"THUMB",
    )
    assert Path(saved_path).exists()
    assert Path(thumb_path).exists()

    deleted = await store.delete_media(saved_path, thumb_path)
    assert deleted is True
    assert not Path(saved_path).exists()
    assert not Path(thumb_path).exists()


async def test_distinct_media_homonyms_do_not_share_or_overwrite_thumbnails(base_dirs):
    outputs, _ = base_dirs
    store = MediaFileStore(outputs_dir=outputs)
    p1, t1 = await store.save_media("clip.mp4", b"MP4_DATA", thumbnail_content=b"THUMB_MP4")
    p2, t2 = await store.save_media("clip.png", b"PNG_DATA", thumbnail_content=b"THUMB_PNG")

    assert t1 != t2
    assert Path(t1).name == "clip.mp4.thumb.jpg"
    assert Path(t2).name == "clip.png.thumb.jpg"
    assert Path(t1).read_bytes() == b"THUMB_MP4"
    assert Path(t2).read_bytes() == b"THUMB_PNG"

    await store.delete_media(p1, t1)
    assert not Path(p1).exists()
    assert not Path(t1).exists()
    assert Path(p2).exists()
    assert Path(t2).exists()


async def test_delete_media_error_propagates_on_permission_error(base_dirs, monkeypatch):
    outputs, _ = base_dirs
    store = MediaFileStore(outputs_dir=outputs)
    saved_path, thumb_path = await store.save_media("test_err.mp4", b"DATA")

    def failing_unlink(p):
        raise PermissionError("Accès refusé pour la suppression")

    import os

    monkeypatch.setattr(os, "unlink", failing_unlink)

    with pytest.raises(PermissionError, match="Accès refusé"):
        await store.delete_media(saved_path, thumb_path)


@pytest.mark.parametrize(
    "forbidden_path",
    [
        "/etc/malicious",
        ".githooks",
        ".githooks/sub",
        str(REPO_ROOT / ".GCC"),
        str(REPO_ROOT / ".GCC" / "branches"),
        ".gouvernance",
        ".git",
    ],
)
def test_storage_path_traversal_rejection(base_dirs, forbidden_path):
    outputs, _ = base_dirs
    store = MediaFileStore(outputs_dir=outputs)
    malicious = Project(
        id="p_bad",
        name="Bad",
        storagePath=forbidden_path,
    )
    with pytest.raises(ValueError, match="Chemin storagePath interdit"):
        store.resolve_destination_dir(project=malicious)
