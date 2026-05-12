"""
Configuración del sistema de logging de la aplicación.
"""
from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from platformdirs import user_log_dir

from app.config import APP_NAME


def setup_logging(level: int = logging.DEBUG) -> Path:
    """Inicializa el logging a consola y a fichero rotativo. Devuelve la ruta del log."""
    log_dir = Path(user_log_dir(APP_NAME))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "shokzmanager.log"

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Fichero rotativo (max 2 MB × 3 backups).
    fh = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)

    # Consola.
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    ch.setLevel(logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(fh)
    root.addHandler(ch)

    return log_file


def get_log_dir() -> Path:
    return Path(user_log_dir(APP_NAME))
