"""
Vista de ajustes: ruta manual, detección automática, calidad de audio.
"""
from __future__ import annotations

import flet as ft

from app.config import (
    AUDIO_QUALITY_OPTIONS,
    COLOR_BORDER,
    COLOR_PRIMARY,
    COLOR_SURFACE,
    COLOR_TEXT,
    COLOR_TEXT_MUTED,
    COLOR_SUCCESS,
)
from app import settings
from app.utils.logging import get_log_dir


class SettingsView(ft.Column):
    def __init__(self, on_manual_path_change=None) -> None:
        super().__init__(expand=True, scroll=ft.ScrollMode.AUTO, spacing=0)
        self._on_manual_path_change = on_manual_path_change
        self._saved_text = ft.Text("", color=COLOR_SUCCESS, size=12, visible=False)
        self._manual_path_field = ft.TextField(
            label="Ruta manual del dispositivo",
            value=settings.get("last_manual_device_path") or "",
            hint_text="/Volumes/NO NAME",
            border_color=COLOR_BORDER,
            focused_border_color=COLOR_PRIMARY,
            color=COLOR_TEXT,
            bgcolor=COLOR_SURFACE,
            border_radius=8,
            expand=True,
        )
        self._auto_detect_switch = ft.Switch(
            label="Detección automática",
            value=settings.get("auto_detect", True),
            active_color=COLOR_PRIMARY,
            on_change=self._on_auto_detect_change,
        )
        s = settings.get("audio_quality", "192")
        self._quality_dropdown = ft.Dropdown(
            label="Calidad de audio",
            value=s,
            options=[
                ft.dropdown.Option(key=q, text=f"{q} kbps")
                for q in AUDIO_QUALITY_OPTIONS
            ],
            border_color=COLOR_BORDER,
            focused_border_color=COLOR_PRIMARY,
            color=COLOR_TEXT,
            bgcolor=COLOR_SURFACE,
            border_radius=8,
            width=200,
        )
        self._build_ui()

    def _build_ui(self) -> None:
        header = ft.Text("Ajustes", size=20, weight=ft.FontWeight.BOLD, color=COLOR_TEXT)

        save_btn = ft.Button(
            content="Guardar ajustes",
            icon=ft.Icons.SAVE,
            bgcolor=COLOR_PRIMARY,
            color=ft.Colors.WHITE,
            on_click=self._on_save,
        )

        log_btn = ft.Button(
            content="Abrir carpeta de logs",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self._open_logs,
        )

        section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Dispositivo",
                        size=15,
                        weight=ft.FontWeight.W_600,
                        color=COLOR_TEXT,
                    ),
                    ft.Row(controls=[self._manual_path_field]),
                    ft.Text(
                        "Si la detección automática no funciona, introduce aquí la ruta completa al volumen.",
                        color=COLOR_TEXT_MUTED,
                        size=12,
                    ),
                    self._auto_detect_switch,
                    ft.Divider(color=COLOR_BORDER),
                    ft.Text(
                        "Descarga",
                        size=15,
                        weight=ft.FontWeight.W_600,
                        color=COLOR_TEXT,
                    ),
                    self._quality_dropdown,
                    ft.Text(
                        "Calidad del MP3 generado. A mayor kbps, mayor tamaño de fichero.",
                        color=COLOR_TEXT_MUTED,
                        size=12,
                    ),
                    ft.Divider(color=COLOR_BORDER),
                    ft.Row(controls=[save_btn, log_btn], spacing=12),
                    self._saved_text,
                ],
                spacing=12,
            ),
            bgcolor=COLOR_SURFACE,
            border=ft.Border.all(1, COLOR_BORDER),
            border_radius=10,
            padding=20,
        )

        self.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[header, section],
                    spacing=16,
                ),
                padding=ft.Padding.all(24),
                expand=True,
            )
        ]

    def _on_save(self, e: ft.ControlEvent) -> None:
        s = settings.load()
        s["last_manual_device_path"] = (self._manual_path_field.value or "").strip() or None
        s["auto_detect"] = self._auto_detect_switch.value
        s["audio_quality"] = self._quality_dropdown.value or "192"
        settings.save(s)

        if self._on_manual_path_change and s["last_manual_device_path"]:
            self._on_manual_path_change(s["last_manual_device_path"])

        self._saved_text.value = "Ajustes guardados correctamente."
        self._saved_text.visible = True
        try:
            self._saved_text.update()
        except Exception:
            pass

    def _on_auto_detect_change(self, e: ft.ControlEvent) -> None:
        settings.set_value("auto_detect", e.control.value)

    def _open_logs(self, e: ft.ControlEvent) -> None:
        import subprocess
        import sys
        log_dir = str(get_log_dir())
        if sys.platform == "darwin":
            subprocess.Popen(["open", log_dir])
        elif sys.platform == "win32":
            subprocess.Popen(["explorer", log_dir])
        else:
            subprocess.Popen(["xdg-open", log_dir])
