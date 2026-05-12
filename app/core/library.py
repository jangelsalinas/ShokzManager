"""
CRUD de ficheros en el dispositivo Shokz.
"""
from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from app.config import DEVICE_FOLDERS

logger = logging.getLogger(__name__)


@dataclass
class LibraryItem:
    path: str
    name: str
    size: int        # bytes
    mtime: float     # timestamp
    kind: str        # "musica" | "podcast"

    @property
    def size_mb(self) -> float:
        return self.size / (1024 * 1024)

    @property
    def size_str(self) -> str:
        if self.size_mb >= 1:
            return f"{self.size_mb:.1f} MB"
        return f"{self.size / 1024:.0f} KB"


class Library:
    """Gestiona los ficheros MP3 en el dispositivo."""

    def __init__(self, device_root: Path) -> None:
        self.device_root = device_root

    def _folder(self, kind: str) -> Path:
        folder_name = DEVICE_FOLDERS.get(kind, DEVICE_FOLDERS["musica"])
        return self.device_root / folder_name

    def list(self, kind: str) -> list[LibraryItem]:
        """Lista los MP3 de una carpeta ordenados por nombre."""
        folder = self._folder(kind)
        if not folder.exists():
            return []
        items: list[LibraryItem] = []
        for p in sorted(folder.glob("*.mp3"), key=lambda x: x.name.lower()):
            try:
                stat = p.stat()
                items.append(
                    LibraryItem(
                        path=str(p),
                        name=p.name,
                        size=stat.st_size,
                        mtime=stat.st_mtime,
                        kind=kind,
                    )
                )
            except Exception as exc:
                logger.warning("No se pudo leer %s: %s", p, exc)
        return items

    def list_all(self) -> list[LibraryItem]:
        return self.list("musica") + self.list("podcast")

    def delete(self, path: str) -> None:
        """Elimina un fichero del dispositivo."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Fichero no encontrado: {path}")
        p.unlink()
        logger.info("Eliminado: %s", path)

    def move(self, path: str, new_kind: str) -> str:
        """
        Mueve un fichero entre Musica/ y Podcasts/.
        Devuelve la nueva ruta.
        """
        src = Path(path)
        if not src.exists():
            raise FileNotFoundError(f"Fichero no encontrado: {path}")

        dest_dir = self._folder(new_kind)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name

        # Evitar colisión de nombres
        counter = 1
        while dest.exists():
            dest = dest_dir / f"{src.stem}_{counter}.mp3"
            counter += 1

        try:
            shutil.move(str(src), str(dest))
        except Exception as exc:
            shutil.copy2(str(src), str(dest))
            src.unlink(missing_ok=True)

        logger.info("Movido: %s → %s", src, dest)
        return str(dest)

    def rename(self, path: str, new_name: str) -> str:
        """Renombra un fichero. new_name debe incluir extensión .mp3."""
        src = Path(path)
        if not src.exists():
            raise FileNotFoundError(f"Fichero no encontrado: {path}")
        dest = src.parent / new_name
        src.rename(dest)
        logger.info("Renombrado: %s → %s", src, dest)
        return str(dest)
