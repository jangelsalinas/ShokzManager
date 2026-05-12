"""
Localiza el binario de ffmpeg.
Orden de búsqueda:
  1. resources/bin/<so>/ (empaquetado con PyInstaller)
  2. PATH del sistema
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from app.config import BIN_DIR


def find_ffmpeg() -> str | None:
    """
    Devuelve la ruta absoluta al binario de ffmpeg, o None si no se encuentra.
    """
    # 1. Binario empaquetado
    if sys.platform == "win32":
        subdir = "windows"
        binary = "ffmpeg.exe"
    else:
        subdir = "macos"
        binary = "ffmpeg"

    bundled = BIN_DIR / subdir / binary
    if bundled.exists():
        bundled.chmod(0o755)
        return str(bundled)

    # 2. PATH del sistema
    system_ffmpeg = shutil.which("ffmpeg")
    return system_ffmpeg


def require_ffmpeg() -> str:
    """Como find_ffmpeg pero lanza RuntimeError si no existe."""
    path = find_ffmpeg()
    if not path:
        raise RuntimeError(
            "ffmpeg no encontrado. Instálalo o coloca el binario en resources/bin/."
        )
    return path
