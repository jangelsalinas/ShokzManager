"""
Motor de descarga con yt-dlp.
Convierte a MP3 y mueve el fichero al dispositivo Shokz.
"""
from __future__ import annotations

import asyncio
import logging
import re
import shutil
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import yt_dlp

from app.config import AUDIO_QUALITY_OPTIONS, DEFAULT_AUDIO_QUALITY, SUPPORTED_DOMAINS
from app.core.ffmpeg import require_ffmpeg
from app import settings
from app.utils.paths import temp_download_dir

logger = logging.getLogger(__name__)

# Caracteres ilegales en nombres de fichero Windows
_WIN_ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class DownloadStatus(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    CONVERTING = "converting"
    MOVING = "moving"
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class DownloadJob:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    url: str = ""
    kind: str = "musica"  # "musica" | "podcast"
    title: str = ""
    progress: float = 0.0
    status: DownloadStatus = DownloadStatus.QUEUED
    error_message: str = ""
    dest_path: str = ""


def sanitize_filename(name: str) -> str:
    """Limpia el nombre para que sea válido en Windows y macOS."""
    name = _WIN_ILLEGAL.sub("_", name)
    name = name.strip(". ")
    return name[:200] or "audio"


def validate_url(url: str) -> bool:
    """Comprueba que la URL pertenezca a un dominio soportado y use http/https."""
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.netloc.lower().removeprefix("www.")
        return any(
            host == d.removeprefix("www.") for d in SUPPORTED_DOMAINS
        )
    except Exception:
        return False


class Downloader:
    """
    Gestiona una cola FIFO de descargas (1 simultánea).
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[DownloadJob] = asyncio.Queue()
        self._jobs: dict[str, DownloadJob] = {}
        self._current_job: DownloadJob | None = None
        self._ydl_instance: yt_dlp.YoutubeDL | None = None
        self._running = False
        self._task: asyncio.Task | None = None
        self._on_update: Callable[[DownloadJob], None] | None = None
        # Ruta raíz del dispositivo (se inyecta desde fuera al conectar)
        self.device_root: Path | None = None

    def set_on_update(self, callback: Callable[[DownloadJob], None]) -> None:
        self._on_update = callback

    def _notify(self, job: DownloadJob) -> None:
        if self._on_update:
            self._on_update(job)

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._worker())
        logger.debug("Downloader worker iniciado")

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()

    def enqueue(self, url: str, kind: str) -> DownloadJob:
        """Añade una URL a la cola y devuelve el DownloadJob."""
        job = DownloadJob(url=url, kind=kind)
        self._jobs[job.id] = job
        self._queue.put_nowait(job)
        logger.info("URL encolada [%s]: %s", kind, url)
        self._notify(job)
        return job

    def cancel(self, job_id: str) -> None:
        """Marca el job como cancelado; si está en curso interrumpe yt-dlp."""
        job = self._jobs.get(job_id)
        if not job:
            return
        job.status = DownloadStatus.CANCELLED
        self._notify(job)
        if self._current_job and self._current_job.id == job_id:
            if self._ydl_instance:
                # yt-dlp respeta esta flag en su bucle interno
                try:
                    self._ydl_instance.params["abort_after_first"] = True
                except Exception:
                    pass

    def get_jobs(self) -> list[DownloadJob]:
        return list(self._jobs.values())

    async def _worker(self) -> None:
        while self._running:
            await self._worker_single_pass()

    async def _worker_single_pass(self) -> None:
        """Procesa un único item de la cola (útil para tests)."""
        try:
            job = await asyncio.wait_for(self._queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return

        if job.status == DownloadStatus.CANCELLED:
            self._queue.task_done()
            return

        self._current_job = job
        try:
            await self._process(job)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Error inesperado procesando job %s", job.id)
            job.status = DownloadStatus.ERROR
            job.error_message = str(exc)
            self._notify(job)
        finally:
            self._current_job = None
            self._ydl_instance = None
            self._queue.task_done()

    async def _process(self, job: DownloadJob) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._download_sync, job)

    def _download_sync(self, job: DownloadJob) -> None:
        """Ejecutado en un hilo executor para no bloquear el event loop."""
        if job.status == DownloadStatus.CANCELLED:
            return

        tmp_dir = temp_download_dir()
        quality = settings.get("audio_quality", DEFAULT_AUDIO_QUALITY)

        try:
            ffmpeg_path = require_ffmpeg()
        except RuntimeError as exc:
            job.status = DownloadStatus.ERROR
            job.error_message = str(exc)
            self._notify(job)
            return

        outtmpl = str(tmp_dir / "%(title)s.%(ext)s")

        def progress_hook(d: dict) -> None:
            if job.status == DownloadStatus.CANCELLED:
                raise yt_dlp.utils.DownloadError("Cancelado por el usuario")
            status = d.get("status")
            if status == "downloading":
                job.status = DownloadStatus.DOWNLOADING
                pct_str = d.get("_percent_str", "0%").strip().replace("%", "")
                try:
                    job.progress = float(pct_str)
                except ValueError:
                    pass
                if not job.title:
                    job.title = d.get("info_dict", {}).get("title", "")
                self._notify(job)
            elif status == "finished":
                job.status = DownloadStatus.CONVERTING
                job.progress = 99.0
                self._notify(job)

        ydl_opts: dict = {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "ffmpeg_location": ffmpeg_path,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": quality,
                }
            ],
            "progress_hooks": [progress_hook],
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

        try:
            job.status = DownloadStatus.DOWNLOADING
            self._notify(job)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self._ydl_instance = ydl
                info = ydl.extract_info(job.url, download=True)
                if not job.title and info:
                    job.title = info.get("title", "")
        except yt_dlp.utils.DownloadError as exc:
            if job.status != DownloadStatus.CANCELLED:
                job.status = DownloadStatus.ERROR
                job.error_message = str(exc)
                self._notify(job)
            return
        except Exception as exc:
            job.status = DownloadStatus.ERROR
            job.error_message = str(exc)
            self._notify(job)
            return

        if job.status == DownloadStatus.CANCELLED:
            # Limpieza del temporal
            _cleanup_tmp(tmp_dir, job.title)
            return

        # Mover al dispositivo
        job.status = DownloadStatus.MOVING
        self._notify(job)

        mp3_file = _find_mp3(tmp_dir, job.title)
        if not mp3_file:
            job.status = DownloadStatus.ERROR
            job.error_message = "No se encontró el fichero MP3 tras la conversión."
            self._notify(job)
            return

        dest_dir = self._dest_dir(job.kind)
        if not dest_dir:
            job.status = DownloadStatus.ERROR
            job.error_message = "No hay dispositivo conectado. Conecta los Shokz."
            self._notify(job)
            return

        dest_dir.mkdir(parents=True, exist_ok=True)
        safe_name = sanitize_filename(mp3_file.stem) + ".mp3"
        dest_file = dest_dir / safe_name

        # Evitar duplicados añadiendo sufijo
        counter = 1
        while dest_file.exists():
            dest_file = dest_dir / f"{sanitize_filename(mp3_file.stem)}_{counter}.mp3"
            counter += 1

        try:
            shutil.move(str(mp3_file), str(dest_file))
        except Exception as exc:
            # Si falla move (cross-device), intentamos copy+delete
            try:
                shutil.copy2(str(mp3_file), str(dest_file))
                mp3_file.unlink(missing_ok=True)
            except Exception as exc2:
                job.status = DownloadStatus.ERROR
                job.error_message = f"Error al mover fichero: {exc2}"
                self._notify(job)
                return

        job.dest_path = str(dest_file)
        job.progress = 100.0
        job.status = DownloadStatus.DONE
        self._notify(job)
        logger.info("Descarga completada: %s → %s", job.url, dest_file)

    def _dest_dir(self, kind: str) -> Path | None:
        if not self.device_root:
            return None
        from app.config import DEVICE_FOLDERS
        folder = DEVICE_FOLDERS.get(kind, DEVICE_FOLDERS["musica"])
        return self.device_root / folder


def _find_mp3(directory: Path, title: str) -> Path | None:
    """Busca el .mp3 más reciente en directory."""
    mp3s = sorted(directory.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    return mp3s[0] if mp3s else None


def _cleanup_tmp(directory: Path, title: str) -> None:
    """Elimina ficheros temporales que contengan el título."""
    if not title:
        return
    safe = sanitize_filename(title)
    for f in directory.iterdir():
        if safe.lower() in f.name.lower():
            try:
                f.unlink()
            except Exception:
                pass
