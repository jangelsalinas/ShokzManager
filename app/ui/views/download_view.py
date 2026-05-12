"""
Vista de descarga: input URL, selector tipo, cola de progreso.
"""
from __future__ import annotations

import flet as ft

from app.config import (
    COLOR_BORDER,
    COLOR_ERROR,
    COLOR_PRIMARY,
    COLOR_SURFACE,
    COLOR_TEXT,
    COLOR_TEXT_MUTED,
)
from app.core.downloader import DownloadJob, DownloadStatus, Downloader, validate_url
from app.ui.components.progress_card import progress_card


class DownloadView(ft.Column):
    def __init__(self, downloader: Downloader) -> None:
        super().__init__(expand=True, scroll=ft.ScrollMode.AUTO, spacing=0)
        self._downloader = downloader
        self._jobs_column = ft.Column(spacing=0)
        self._url_field = ft.TextField(
            hint_text="https://youtube.com/watch?v=...  o  https://www.mixcloud.com/...",
            expand=True,
            border_color=COLOR_BORDER,
            focused_border_color=COLOR_PRIMARY,
            color=COLOR_TEXT,
            bgcolor=COLOR_SURFACE,
            border_radius=8,
            text_size=13,
        )
        self._kind_radio = ft.RadioGroup(
            value="musica",
            content=ft.Row(
                controls=[
                    ft.Radio(value="musica", label="Música / Sesión"),
                    ft.Radio(value="podcast", label="Podcast"),
                ],
                spacing=24,
            ),
        )
        self._error_text = ft.Text("", color=COLOR_ERROR, size=12, visible=False)
        self._build_ui()
        self._downloader.set_on_update(self._on_job_update)

    def _build_ui(self) -> None:
        header = ft.Text(
            "Descargar audio",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=COLOR_TEXT,
        )
        sub = ft.Text(
            "Pega una URL de YouTube o Mixcloud, elige el tipo y pulsa Descargar.",
            size=13,
            color=COLOR_TEXT_MUTED,
        )
        download_btn = ft.Button(
            content="Descargar y enviar",
            icon=ft.Icons.DOWNLOAD,
            bgcolor=COLOR_PRIMARY,
            color=ft.Colors.WHITE,
            on_click=self._on_download_click,
        )
        form = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(controls=[self._url_field]),
                    ft.Row(
                        controls=[
                            ft.Text("Tipo:", color=COLOR_TEXT_MUTED, size=13),
                            self._kind_radio,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                    ),
                    self._error_text,
                    ft.Row(controls=[download_btn]),
                ],
                spacing=14,
            ),
            bgcolor=COLOR_SURFACE,
            border=ft.Border.all(1, COLOR_BORDER),
            border_radius=10,
            padding=20,
        )

        queue_header = ft.Text(
            "Cola de descargas",
            size=15,
            weight=ft.FontWeight.W_600,
            color=COLOR_TEXT,
        )

        self.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[header, sub, form, queue_header, self._jobs_column],
                    spacing=16,
                ),
                padding=ft.Padding.all(24),
                expand=True,
            )
        ]

    def _on_download_click(self, e: ft.ControlEvent) -> None:
        url = (self._url_field.value or "").strip()
        if not url:
            self._show_error("Introduce una URL.")
            return
        if not validate_url(url):
            self._show_error("URL no válida. Solo se admiten YouTube y Mixcloud.")
            return
        self._hide_error()
        kind = self._kind_radio.value or "musica"
        self._downloader.enqueue(url, kind)
        self._url_field.value = ""
        self._url_field.update()

    def _show_error(self, msg: str) -> None:
        self._error_text.value = msg
        self._error_text.visible = True
        try:
            self._error_text.update()
        except Exception:
            pass

    def _hide_error(self) -> None:
        self._error_text.visible = False
        try:
            self._error_text.update()
        except Exception:
            pass

    def _on_job_update(self, job: DownloadJob) -> None:
        self._refresh_jobs()

    def _refresh_jobs(self) -> None:
        jobs = self._downloader.get_jobs()
        cards: list[ft.Control] = []
        for job in reversed(jobs):
            def make_cancel(j: DownloadJob):
                def handler(e: ft.ControlEvent) -> None:
                    self._downloader.cancel(j.id)
                return handler

            cards.append(progress_card(job, on_cancel=make_cancel(job)))
        self._jobs_column.controls = cards
        try:
            self._jobs_column.update()
        except Exception:
            pass
