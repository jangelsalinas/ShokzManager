"""
Tests de core/device.py
"""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.core.device import DeviceWatcher, scan_devices, device_from_manual_path


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_partition(mountpoint: str, opts: str = "rw") -> MagicMock:
    p = MagicMock()
    p.mountpoint = mountpoint
    p.opts = opts
    p.fstype = "msdos"
    return p


def _make_usage(total=4_000_000_000, used=1_000_000_000, free=3_000_000_000) -> MagicMock:
    u = MagicMock()
    u.total = total
    u.used = used
    u.free = free
    return u


# ── scan_devices ─────────────────────────────────────────────────────────

class TestScanDevices:
    def test_detects_no_name_on_macos(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "darwin")
        partitions = [_make_partition("/Volumes/NO NAME")]
        with (
            patch("psutil.disk_partitions", return_value=partitions),
            patch("psutil.disk_usage", return_value=_make_usage()),
        ):
            result = scan_devices(["NO NAME"])
        assert len(result) == 1
        assert result[0].label == "NO NAME"
        assert result[0].mountpoint == "/Volumes/NO NAME"

    def test_ignores_system_volumes_on_macos(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "darwin")
        partitions = [
            _make_partition("/"),
            _make_partition("/System/Volumes/Data"),
            _make_partition("/Volumes/NO NAME"),
        ]
        with (
            patch("psutil.disk_partitions", return_value=partitions),
            patch("psutil.disk_usage", return_value=_make_usage()),
        ):
            result = scan_devices(["NO NAME"])
        assert len(result) == 1

    def test_returns_empty_when_no_match(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "darwin")
        partitions = [_make_partition("/Volumes/BACKUP")]
        with (
            patch("psutil.disk_partitions", return_value=partitions),
            patch("psutil.disk_usage", return_value=_make_usage()),
        ):
            result = scan_devices(["NO NAME", "Shokz"])
        assert result == []

    def test_case_insensitive_match(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "darwin")
        partitions = [_make_partition("/Volumes/no name")]
        with (
            patch("psutil.disk_partitions", return_value=partitions),
            patch("psutil.disk_usage", return_value=_make_usage()),
        ):
            result = scan_devices(["NO NAME"])
        assert len(result) == 1

    def test_psutil_error_returns_empty(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "darwin")
        with patch("psutil.disk_partitions", side_effect=RuntimeError("fail")):
            result = scan_devices(["NO NAME"])
        assert result == []


# ── device_from_manual_path ───────────────────────────────────────────────

class TestDeviceFromManualPath:
    def test_returns_none_for_nonexistent_path(self, tmp_path):
        result = device_from_manual_path(str(tmp_path / "nonexistent"))
        assert result is None

    def test_returns_device_for_valid_path(self, tmp_path):
        with patch("psutil.disk_usage", return_value=_make_usage()):
            result = device_from_manual_path(str(tmp_path))
        assert result is not None
        assert result.mountpoint == str(tmp_path)


# ── DeviceWatcher ─────────────────────────────────────────────────────────

class TestDeviceWatcher:
    @pytest.mark.asyncio
    async def test_calls_on_connected_when_device_found(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "darwin")
        connected_calls = []
        watcher = DeviceWatcher(on_connected=lambda d: connected_calls.append(d))

        part = _make_partition("/Volumes/NO NAME")
        with (
            patch("psutil.disk_partitions", return_value=[part]),
            patch("psutil.disk_usage", return_value=_make_usage()),
            patch.object(watcher, "_check", wraps=watcher._check),
        ):
            await watcher._check()

        assert len(connected_calls) == 1
        assert connected_calls[0].label == "NO NAME"

    @pytest.mark.asyncio
    async def test_calls_on_disconnected_when_device_removed(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "darwin")
        disconnected_calls = []
        watcher = DeviceWatcher(on_disconnected=lambda: disconnected_calls.append(True))

        # Simular que había un dispositivo conectado
        watcher._current = MagicMock()
        watcher._current.label = "NO NAME"

        with patch("psutil.disk_partitions", return_value=[]):
            await watcher._check()

        assert len(disconnected_calls) == 1

    def test_set_manual_persists_path(self, tmp_path):
        watcher = DeviceWatcher()
        with patch("psutil.disk_usage", return_value=_make_usage()):
            device = watcher.set_manual(str(tmp_path))
        assert device is not None
        assert watcher._manual_override is not None

    def test_clear_manual_resets_override(self, tmp_path):
        watcher = DeviceWatcher()
        with patch("psutil.disk_usage", return_value=_make_usage()):
            watcher.set_manual(str(tmp_path))
        watcher.clear_manual()
        assert watcher._manual_override is None
