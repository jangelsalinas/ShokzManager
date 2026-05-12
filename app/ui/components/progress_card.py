"""
Tarjeta de progreso de una descarga activa.
"""
from __future__ import annotations

import flet as ft

from app.config import (
    COLOR_BORDER,
    COLOR_ERROR,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_SURFACE,
    COLOR_TEXT,
    COLOR_TEXT_MUTED,
    COLOR_WARNING,
)
from app.core.downloader import DownloadJob, DownloadStatus


def _status_color(status: DownloadStatus) -> str:
    mapping = {
        DownloadStatus.DONE: COLOR_SUCCESS,
        DownloadStatus.ERROR: COLOR_ERROR,
        DownloadStatus.CANCELLED: COLOR_TEXT_MUTED,
        DownloadStatus.QUEUED: COLOR_TEXT_MUTED,
        DownloadStatus.DOWNLOADING: COLOR_PRIMARY,
        DownloadStatus.CONVERTING: COLOR_WARNING,
        DownloadStatus.MOVING: COLOR_WARNING,
    }
    return mapping.get(status, COLOR_TEXT_MUTED)


def _status_label(status: DownloadStatus) -> str:
    mapping = {
        DownloadStatus.QUEUED: "En cola",
        DownloadStatus.DOWNLOADING: "Descargando",
        DownloadStatus.CONVERTING: "Convirtiendo a MP3",
        DownloadStatus.MOVING: "Enviando al dispositivo",
        DownloadStatus.DONE: "Completado",
        DownloadStatus.ERROR: "Error",
        DownloadStatus.CANCELLED: "Cancelado",
    }
    return mapping.get(status, str(status))


def progress_card(
    job: DownloadJob,
    on_cancel=None,
) -> ft.Container:
    title = job.title or job.url
    if len(title) > 60:
        title = title[:57] + "..."

    is_active = job.status in (
        DownloadStatus.QUEUED,
        DownloadStatus.DOWNLOADING,
        DownloadStatus.CONVERTING,
        DownloadStatus.MOVING,
    )

    kind_badge = ft.Container(
        content=ft.Text(
            "MÚSICA" if job.kind == "musica" else "PODCAST",
            size=10,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
        ),
        bgcolor=COLOR_PRIMARY if job.kind == "musica" else "#7b2ff7",
        border_radius=4,
        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
    )

    status_color = _status_color(job.status)

    controls: list[ft.Control] = [
        ft.Row(
            controls=[
                kind_badge,
                ft.Text(title, color=COLOR_TEXT, size=13, expand=True),
                ft.Text(
                    _status_label(job.status),
                    color=status_color,
                    size=12,
                ),
            ],
            spacing=8,
        ),
    ]

    if is_active:
        controls.append(
            ft.ProgressBar(
                value=job.progress / 100,
                color=COLOR_PRIMARY,
                bgcolor=COLOR_BORDER,
                height=4,
                border_radius=2,
            )
        )
        if on_cancel:
            controls.append(
                ft.Row(
                    controls=[
                        ft.Container(expand=True),
                        ft.Button(
                            content="Cancelar",
                            icon=ft.Icons.CANCEL_OUTLINED,
                            on_click=on_cancel,
                            color=COLOR_ERROR,
                        ),
                    ]
                )
            )
    elif job.status == DownloadStatus.ERROR:
        controls.append(
            ft.Text(job.error_message, color=COLOR_ERROR, size=11, italic=True)
        )
    elif job.status == DownloadStatus.DONE and job.dest_path:
        controls.append(
            ft.Text(
                f"Guardado en: {job.dest_path}",
                color=COLOR_TEXT_MUTED,
                size=11,
            )
        )

    return ft.Container(
        content=ft.Column(controls=controls, spacing=6),
        bgcolor=COLOR_SURFACE,
        border=ft.Border.all(1, COLOR_BORDER),
        border_radius=8,
        padding=12,
        margin=ft.Margin.only(bottom=8),
    )
