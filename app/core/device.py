"""
Detección automática del dispositivo Shokz vía psutil.
Polling cada DEVICE_POLL_INTERVAL segundos con fallback manual.
"""
from __future__ import annotations

import asyncio
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import psutil

from app.config import DEVICE_FOLDERS, DEVICE_POLL_INTERVAL, PREFERRED_VOLUME_NAMES
from app import settings

logger = logging.getLogger(__name__)


@dataclass
class DeviceInfo:
    mountpoint: str
    label: str
    total: int = 0
    used: int = 0
    free: int = 0

    @property
    def mountpath(self) -> Path:
        return Path(self.mountpoint)

    @property
    def music_path(self) -> Path:
        return self.mountpath / DEVICE_FOLDERS["musica"]

    @property
    def podcasts_path(self) -> Path:
        return self.mountpath / DEVICE_FOLDERS["podcast"]

    def ensure_folders(self) -> None:
        """Crea Musica/ y Podcasts/ si no existen."""
        for folder in DEVICE_FOLDERS.values():
            target = self.mountpath / folder
            target.mkdir(parents=True, exist_ok=True)
            logger.debug("Carpeta asegurada: %s", target)


def _is_removable_partition(p: psutil.sdiskpart) -> bool:  # type: ignore[name-defined]
    """Heurística multiplataforma para detectar USB/extraíble."""
    opts = p.opts.lower() if hasattr(p, "opts") else ""
    mountpoint = p.mountpoint

    if sys.platform == "win32":
        # En Windows, las unidades extraíbles suelen tener opts con 'rw'
        # y el fstype no es NTFS de sistema.
        return "removable" in opts or (
            len(mountpoint) == 3
            and mountpoint[1] == ":"
            and mountpoint[0].upper() not in ("C",)
        )
    else:
        # macOS/Linux: montar en /Volumes o /media o /mnt suele indicar extraíble.
        # Excluimos el disco de arranque y los volúmenes del sistema.
        if mountpoint in ("/", "/System/Volumes/Data", "/private/var/vm"):
            return False
        if sys.platform == "darwin":
            return mountpoint.startswith("/Volumes/")
        # Linux
        return mountpoint.startswith(("/media/", "/mnt/", "/run/media/"))


def scan_devices(volume_names: list[str] | None = None) -> list[DeviceInfo]:
    """
    Escanea particiones montadas y devuelve las que coinciden con
    alguno de los nombres de volumen preferidos.
    Si volume_names es None usa los de settings.
    """
    if volume_names is None:
        volume_names = settings.get("preferred_volume_names", PREFERRED_VOLUME_NAMES)

    results: list[DeviceInfo] = []
    try:
        partitions = psutil.disk_partitions(all=False)
    except Exception as exc:
        logger.warning("Error listando particiones: %s", exc)
        return results

    for part in partitions:
        if not _is_removable_partition(part):
            continue
        mp = Path(part.mountpoint)
        label = mp.name  # Nombre del volumen (ej. "NO NAME")
        # Comparación case-insensitive
        if any(label.upper() == v.upper() for v in volume_names):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                results.append(
                    DeviceInfo(
                        mountpoint=part.mountpoint,
                        label=label,
                        total=usage.total,
                        used=usage.used,
                        free=usage.free,
                    )
                )
                logger.debug("Dispositivo Shokz detectado: %s", part.mountpoint)
            except Exception as exc:
                logger.warning("No se pudo leer usage de %s: %s", part.mountpoint, exc)

    return results


def device_from_manual_path(path: str) -> DeviceInfo | None:
    """Construye un DeviceInfo a partir de una ruta manual."""
    p = Path(path)
    if not p.exists():
        return None
    try:
        usage = psutil.disk_usage(path)
        return DeviceInfo(
            mountpoint=path,
            label=p.name or path,
            total=usage.total,
            used=usage.used,
            free=usage.free,
        )
    except Exception as exc:
        logger.warning("No se pudo leer usage de ruta manual %s: %s", path, exc)
        return None


class DeviceWatcher:
    """
    Ejecuta polling periódico en background y notifica cambios mediante callbacks.
    Uso:
        watcher = DeviceWatcher(on_connected=..., on_disconnected=...)
        await watcher.start()
        ...
        watcher.stop()
    """

    def __init__(
        self,
        on_connected: Callable[[DeviceInfo], None] | None = None,
        on_disconnected: Callable[[], None] | None = None,
    ) -> None:
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected
        self._current: DeviceInfo | None = None
        self._running = False
        self._task: asyncio.Task | None = None
        # Si el usuario eligió ruta manual, no hacemos polling automático.
        self._manual_override: DeviceInfo | None = None

    @property
    def current_device(self) -> DeviceInfo | None:
        return self._manual_override or self._current

    def set_manual(self, path: str) -> DeviceInfo | None:
        """Fija la ruta del dispositivo manualmente y persiste en settings."""
        device = device_from_manual_path(path)
        if device:
            self._manual_override = device
            settings.set_value("last_manual_device_path", path)
            logger.info("Dispositivo fijado manualmente: %s", path)
            if self._on_connected:
                self._on_connected(device)
        return device

    def clear_manual(self) -> None:
        """Vuelve a la detección automática."""
        self._manual_override = None
        settings.set_value("last_manual_device_path", None)

    async def start(self) -> None:
        """Inicia el polling asíncrono."""
        # Intentar recuperar última ruta manual guardada.
        last_path = settings.get("last_manual_device_path")
        if last_path and settings.get("auto_detect", True) is False:
            self.set_manual(last_path)

        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.debug("DeviceWatcher iniciado")

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
        logger.debug("DeviceWatcher detenido")

    async def _poll_loop(self) -> None:
        while self._running:
            if self._manual_override is None and settings.get("auto_detect", True):
                await self._check()
            await asyncio.sleep(DEVICE_POLL_INTERVAL)

    async def _check(self) -> None:
        loop = asyncio.get_event_loop()
        devices = await loop.run_in_executor(None, scan_devices)
        found = devices[0] if devices else None

        if found and self._current is None:
            self._current = found
            logger.info("Dispositivo conectado: %s", found.mountpoint)
            try:
                found.ensure_folders()
            except Exception as exc:
                logger.warning("No se pudieron crear carpetas en dispositivo: %s", exc)
            if self._on_connected:
                self._on_connected(found)

        elif not found and self._current is not None:
            logger.info("Dispositivo desconectado")
            self._current = None
            if self._on_disconnected:
                self._on_disconnected()
