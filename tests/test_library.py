"""
Tests de core/library.py
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.core.library import Library, LibraryItem


@pytest.fixture
def device(tmp_path: Path) -> Path:
    """Crea la estructura de carpetas del dispositivo en un tmpdir."""
    (tmp_path / "Musica").mkdir()
    (tmp_path / "Podcasts").mkdir()
    return tmp_path


@pytest.fixture
def lib(device: Path) -> Library:
    return Library(device)


# ── list ──────────────────────────────────────────────────────────────────

class TestList:
    def test_empty_library_returns_empty(self, lib):
        assert lib.list("musica") == []
        assert lib.list("podcast") == []

    def test_lists_mp3_files(self, lib, device):
        (device / "Musica" / "track1.mp3").write_text("x")
        (device / "Musica" / "track2.mp3").write_text("x")
        result = lib.list("musica")
        assert len(result) == 2
        assert all(isinstance(i, LibraryItem) for i in result)

    def test_ignores_non_mp3_files(self, lib, device):
        (device / "Musica" / "cover.jpg").write_text("x")
        (device / "Musica" / "track.m4a").write_text("x")
        assert lib.list("musica") == []

    def test_sorted_by_name(self, lib, device):
        (device / "Musica" / "b.mp3").write_text("x")
        (device / "Musica" / "a.mp3").write_text("x")
        result = lib.list("musica")
        assert result[0].name == "a.mp3"
        assert result[1].name == "b.mp3"

    def test_list_all_returns_both(self, lib, device):
        (device / "Musica" / "song.mp3").write_text("x")
        (device / "Podcasts" / "ep1.mp3").write_text("x")
        result = lib.list_all()
        assert len(result) == 2


# ── delete ────────────────────────────────────────────────────────────────

class TestDelete:
    def test_deletes_existing_file(self, lib, device):
        f = device / "Musica" / "track.mp3"
        f.write_text("x")
        lib.delete(str(f))
        assert not f.exists()

    def test_raises_for_nonexistent_file(self, lib):
        with pytest.raises(FileNotFoundError):
            lib.delete("/nonexistent/path/track.mp3")


# ── move ──────────────────────────────────────────────────────────────────

class TestMove:
    def test_moves_from_musica_to_podcast(self, lib, device):
        src = device / "Musica" / "track.mp3"
        src.write_text("audio data")
        new_path = lib.move(str(src), "podcast")
        assert not src.exists()
        assert Path(new_path).exists()
        assert "Podcasts" in new_path

    def test_moves_from_podcast_to_musica(self, lib, device):
        src = device / "Podcasts" / "ep.mp3"
        src.write_text("audio data")
        new_path = lib.move(str(src), "musica")
        assert "Musica" in new_path
        assert Path(new_path).exists()

    def test_avoids_name_collision(self, lib, device):
        src = device / "Musica" / "track.mp3"
        src.write_text("original")
        existing = device / "Podcasts" / "track.mp3"
        existing.write_text("existing")
        new_path = lib.move(str(src), "podcast")
        assert "track_1.mp3" in new_path

    def test_raises_for_nonexistent_file(self, lib):
        with pytest.raises(FileNotFoundError):
            lib.move("/nonexistent/track.mp3", "podcast")


# ── rename ────────────────────────────────────────────────────────────────

class TestRename:
    def test_renames_file(self, lib, device):
        src = device / "Musica" / "old.mp3"
        src.write_text("x")
        new_path = lib.rename(str(src), "new.mp3")
        assert Path(new_path).name == "new.mp3"
        assert not src.exists()

    def test_raises_for_nonexistent_file(self, lib):
        with pytest.raises(FileNotFoundError):
            lib.rename("/nonexistent/old.mp3", "new.mp3")


# ── LibraryItem helpers ───────────────────────────────────────────────────

class TestLibraryItem:
    def test_size_str_in_mb(self):
        item = LibraryItem(path="", name="t.mp3", size=5_242_880, mtime=0, kind="musica")
        assert item.size_str == "5.0 MB"

    def test_size_str_in_kb(self):
        item = LibraryItem(path="", name="t.mp3", size=512 * 1024, mtime=0, kind="musica")
        assert item.size_str == "512 KB"
