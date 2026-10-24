"""Tests unitaires pour MediaFileStore (Step 4 du Plan 01)."""

from __future__ import annotations

import unittest.mock
from pathlib import Path

import pytest

from app.config import REPO_ROOT
from app.models.domain import Project
from app.storage.media_store import MediaFileStore


@pytest.fixture
def base_dirs(tmp_path: Path):
    return tmp_path / "outputs", tmp_path / "custom_project_storage"


def test_resolve_destinations(base_dirs):
    outputs, custom_dir = base_dirs
    store = MediaFileStore(outputs_dir=outputs)
    # 1. Custom storagePath
    assert (
        store.resolve_destination_dir(Project(id="p1", name="Custom", storagePath=str(custom_dir)))
        == custom_dir.resolve()
    )
    # 2. Project without storagePath
    assert (
        store.resolve_destination_dir(Project(id="p2", name="Std"))
        == (outputs / "projects" / "p2").resolve()
    )
    # 3. No project (outputs/YYYY-MM-DD)
    dest_none = store.resolve_destination_dir(None)
    assert (
        dest_none.parent == outputs.resolve()
        and len(dest_none.name) == 10
        and dest_none.name.count("-") == 2
    )


async def test_save_binary_in_custom_storage_creates_zero_files_in_outputs(base_dirs):
    outputs, custom_dir = base_dirs
    store = MediaFileStore(outputs_dir=outputs)
    proj = Project(id="proj_iso", name="Iso", storagePath=str(custom_dir))
    f_bytes, t_bytes = b"FAKE_MP4", b"FAKE_THUMB"

    saved, thumb = await store.save_media(
        "clip.mp4", f_bytes, project=proj, thumbnail_content=t_bytes
    )
    assert Path(saved).read_bytes() == f_bytes and Path(thumb).read_bytes() == t_bytes
    assert str(custom_dir) in saved and list(outputs.rglob("*")) == []


async def test_delete_media_removes_both_files(base_dirs):
    outputs, _ = base_dirs
    store = MediaFileStore(outputs_dir=outputs)
    saved, thumb = await store.save_media("to_del.mp4", b"DATA", thumbnail_content=b"THUMB")
    assert Path(saved).exists() and Path(thumb).exists()
    assert await store.delete_media(saved, thumb) is True
    assert not Path(saved).exists() and not Path(thumb).exists()


async def test_distinct_media_homonyms_do_not_share_or_overwrite_thumbnails(base_dirs):
    outputs, _ = base_dirs
    store = MediaFileStore(outputs_dir=outputs)
    p1, t1 = await store.save_media("clip.mp4", b"MP4_DATA", thumbnail_content=b"THUMB_MP4")
    p2, t2 = await store.save_media("clip.png", b"PNG_DATA", thumbnail_content=b"THUMB_PNG")

    assert (
        t1 != t2 and Path(t1).name == "clip.mp4.thumb.jpg" and Path(t2).name == "clip.png.thumb.jpg"
    )
    await store.delete_media(p1, t1)
    assert (
        not Path(p1).exists() and not Path(t1).exists() and Path(p2).exists() and Path(t2).exists()
    )


async def test_delete_media_error_propagates_on_permission_error(base_dirs, monkeypatch):
    outputs, _ = base_dirs
    store = MediaFileStore(outputs_dir=outputs)
    saved, thumb = await store.save_media("test_err.mp4", b"DATA")
    monkeypatch.setattr(
        Path, "unlink", unittest.mock.Mock(side_effect=PermissionError("Accès refusé"))
    )
    with pytest.raises(PermissionError, match="Accès refusé"):
        await store.delete_media(saved, thumb)


@pytest.mark.parametrize(
    "bad",
    ["/etc/malicious", ".githooks", str(REPO_ROOT / ".GCC"), ".gouvernance", ".git"],
)
def test_storage_path_traversal_rejection(base_dirs, bad):
    outputs, _ = base_dirs
    store = MediaFileStore(outputs_dir=outputs)
    with pytest.raises(ValueError, match="Chemin storagePath interdit"):
        store.resolve_destination_dir(project=Project(id="bad", name="Bad", storagePath=bad))
