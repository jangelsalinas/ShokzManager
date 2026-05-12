"""
Tests de core/downloader.py
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.downloader import (
    DownloadJob,
    DownloadStatus,
    Downloader,
    sanitize_filename,
    validate_url,
    _find_mp3,
)


# ── validate_url ──────────────────────────────────────────────────────────

class TestValidateUrl:
    @pytest.mark.parametrize("url", [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtube.com/watch?v=abc",
        "https://www.mixcloud.com/user/track/",
        "https://mixcloud.com/user/track/",
    ])
    def test_valid_urls(self, url):
        assert validate_url(url) is True

    @pytest.mark.parametrize("url", [
        "https://soundcloud.com/track",
        "https://spotify.com/track",
        "not-a-url",
        "",
        "ftp://youtube.com/watch?v=abc",
    ])
    def test_invalid_urls(self, url):
        assert validate_url(url) is False


# ── sanitize_filename ─────────────────────────────────────────────────────

class TestSanitizeFilename:
    def test_removes_illegal_chars(self):
        result = sanitize_filename('My Track: "Best" <Song> | 2024')
        assert ":" not in result
        assert '"' not in result
        assert "<" not in result
        assert ">" not in result
        assert "|" not in result

    def test_strips_leading_trailing_dots_spaces(self):
        # strip(". ") elimina puntos Y espacios de ambos extremos
        assert sanitize_filename("  ..hello.. ") == "hello"

    def test_empty_becomes_audio(self):
        assert sanitize_filename("") == "audio"

    def test_truncates_long_names(self):
        long_name = "a" * 300
        assert len(sanitize_filename(long_name)) <= 200


# ── _find_mp3 ─────────────────────────────────────────────────────────────

class TestFindMp3:
    def test_returns_none_for_empty_directory(self, tmp_path):
        assert _find_mp3(tmp_path, "title") is None

    def test_returns_most_recent_mp3(self, tmp_path):
        f1 = tmp_path / "old.mp3"
        f2 = tmp_path / "new.mp3"
        f1.write_text("x")
        f2.write_text("x")
        import time; time.sleep(0.01)
        f2.touch()  # f2 más reciente
        result = _find_mp3(tmp_path, "")
        assert result == f2

    def test_ignores_non_mp3_files(self, tmp_path):
        (tmp_path / "track.m4a").write_text("x")
        (tmp_path / "track.wav").write_text("x")
        assert _find_mp3(tmp_path, "") is None


# ── Downloader (integración ligera) ──────────────────────────────────────

class TestDownloader:
    def test_enqueue_adds_job(self):
        dl = Downloader()
        job = dl.enqueue("https://youtube.com/watch?v=abc", "musica")
        assert job.id in {j.id for j in dl.get_jobs()}
        assert job.status == DownloadStatus.QUEUED

    def test_cancel_marks_job_cancelled(self):
        dl = Downloader()
        job = dl.enqueue("https://youtube.com/watch?v=abc", "musica")
        dl.cancel(job.id)
        assert dl._jobs[job.id].status == DownloadStatus.CANCELLED

    def test_cancel_nonexistent_job_does_not_raise(self):
        dl = Downloader()
        dl.cancel("nonexistent-id")  # no debe lanzar

    def test_dest_dir_returns_none_without_device(self):
        dl = Downloader()
        assert dl._dest_dir("musica") is None

    def test_dest_dir_returns_correct_path(self, tmp_path):
        dl = Downloader()
        dl.device_root = tmp_path
        dest = dl._dest_dir("musica")
        assert dest == tmp_path / "Musica"
        dest2 = dl._dest_dir("podcast")
        assert dest2 == tmp_path / "Podcasts"

    @pytest.mark.asyncio
    async def test_worker_skips_cancelled_jobs(self):
        dl = Downloader()
        job = dl.enqueue("https://youtube.com/watch?v=abc", "musica")
        dl.cancel(job.id)
        # El worker debe consumir el job sin llamar a _process
        with patch.object(dl, "_process") as mock_process:
            await dl._worker_single_pass()
        mock_process.assert_not_called()
