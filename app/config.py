"""
Constantes y configuración global de ShokzManager.
"""
from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Versión
# ---------------------------------------------------------------------------
APP_NAME = "ShokzManager"
APP_VERSION = "0.1.0"
APP_BUNDLE_ID = "com.shokzmanager.app"

# ---------------------------------------------------------------------------
# Rutas base
# ---------------------------------------------------------------------------
# En producción (PyInstaller), los recursos están en sys._MEIPASS
if getattr(sys, "frozen", False):
    RESOURCES_DIR = Path(sys._MEIPASS) / "resources"  # type: ignore[attr-defined]
else:
    RESOURCES_DIR = Path(__file__).parent.parent / "resources"

ICONS_DIR = RESOURCES_DIR / "icons"
BIN_DIR = RESOURCES_DIR / "bin"

# ---------------------------------------------------------------------------
# Dispositivo
# ---------------------------------------------------------------------------
# Nombres de volumen que se consideran el Shokz.
PREFERRED_VOLUME_NAMES: list[str] = ["NO NAME", "Shokz", "OpenSwim", "SHOKZ"]

# Carpetas que se crean en la raíz del dispositivo.
DEVICE_FOLDERS: dict[str, str] = {
    "musica": "Musica",
    "podcast": "Podcasts",
}

# Intervalo de polling de detección USB (segundos).
DEVICE_POLL_INTERVAL = 3.0

# ---------------------------------------------------------------------------
# Descarga
# ---------------------------------------------------------------------------
SUPPORTED_DOMAINS = [
    "youtube.com",
    "youtu.be",
    "www.youtube.com",
    "mixcloud.com",
    "www.mixcloud.com",
]

DEFAULT_AUDIO_QUALITY = "192"
AUDIO_QUALITY_OPTIONS = ["128", "192", "320"]

# Carpeta temporal para descargas en proceso.
TEMP_DOWNLOAD_SUBDIR = "shokzmanager_tmp"

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 720
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 560

# Colores base (modo oscuro)
COLOR_BG = "#1a1a2e"
COLOR_SURFACE = "#16213e"
COLOR_SURFACE_2 = "#0f3460"
COLOR_PRIMARY = "#e94560"
COLOR_PRIMARY_HOVER = "#c73652"
COLOR_TEXT = "#eaeaea"
COLOR_TEXT_MUTED = "#9a9ab0"
COLOR_SUCCESS = "#4caf50"
COLOR_WARNING = "#ff9800"
COLOR_ERROR = "#f44336"
COLOR_BORDER = "#2a2a4a"
