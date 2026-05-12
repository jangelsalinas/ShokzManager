"""Utilidades de rutas multiplataforma."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from app.config import TEMP_DOWNLOAD_SUBDIR


def temp_download_dir() -> Path:
    """Devuelve (y crea si hace falta) la carpeta temporal para descargas."""
    tmp = Path(tempfile.gettempdir()) / TEMP_DOWNLOAD_SUBDIR
    tmp.mkdir(parents=True, exist_ok=True)
    return tmp


def is_windows() -> bool:
    return sys.platform == "win32"


def is_macos() -> bool:
    return sys.platform == "darwin"
