"""
Carga y guardado de preferencias del usuario en disco.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir

from app.config import APP_NAME, DEFAULT_AUDIO_QUALITY, PREFERRED_VOLUME_NAMES

logger = logging.getLogger(__name__)

_DEFAULTS: dict[str, Any] = {
    "last_manual_device_path": None,
    "audio_quality": DEFAULT_AUDIO_QUALITY,
    "auto_detect": True,
    "preferred_volume_names": PREFERRED_VOLUME_NAMES,
}


def _settings_path() -> Path:
    config_dir = Path(user_config_dir(APP_NAME))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "settings.json"


def load() -> dict[str, Any]:
    """Devuelve las preferencias guardadas, completando con valores por defecto."""
    path = _settings_path()
    data: dict[str, Any] = {}
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as exc:
            logger.warning("No se pudo leer settings.json: %s", exc)
    # Mezclar con defaults para campos que falten.
    merged = {**_DEFAULTS, **data}
    return merged


def save(settings: dict[str, Any]) -> None:
    """Persiste el diccionario de preferencias en disco."""
    path = _settings_path()
    try:
        with path.open("w", encoding="utf-8") as fh:
            json.dump(settings, fh, indent=2, ensure_ascii=False)
    except Exception as exc:
        logger.error("No se pudo guardar settings.json: %s", exc)


def get(key: str, default: Any = None) -> Any:
    return load().get(key, default)


def set_value(key: str, value: Any) -> None:
    settings = load()
    settings[key] = value
    save(settings)
