"""
Layout principal: NavigationRail lateral + contenido central + banner de dispositivo.
API Flet 0.85:
  - FilePicker es un Service → page.services.append(fp)
  - fp.get_directory_path() es async y devuelve Optional[str] directamente
  - on_window_event con WindowEventType
"""
from __future__ import annotations

import asyncio
import logging

import flet as ft

from app.config import (
    APP_NAME,
    APP_VERSION,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_PRIMARY,
    COLOR_SURFACE,
    COLOR_TEXT,
    COLOR_TEXT_MUTED,
)
from app.core.device import DeviceInfo, DeviceWatcher
from app.core.downloader import Downloader
from app.core.library import Library
from app.ui.components.device_status import device_status_banner
from app.ui.views.download_view import DownloadView
from app.ui.views.library_view import LibraryView
from app.ui.views.settings_view import SettingsView

logger = logging.getLogger(__name__)

NAV_ITEMS = [
    ("Descargar", ft.Icons.DOWNLOAD_ROUNDED),
    ("Biblioteca", ft.Icons.LIBRARY_MUSIC_ROUNDED),
    ("Ajustes", ft.Icons.SETTINGS_ROUNDED),
]


async def build_app(page: ft.Page) -> None:
    # ── Configuración de la ventana ────────────────────────────────────────
    page.title = f"{APP_NAME} v{APP_VERSION}"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = COLOR_BG
    page.padding = 0
    page.window.width = 1100
    page.window.height = 720
    page.window.min_width = 800
    page.window.min_height = 560

    # ── FilePicker como Service (API 0.85) ─────────────────────────────────
    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    # ── Core ───────────────────────────────────────────────────────────────
    downloader = Downloader()
    await downloader.start()

    # ── Vistas ────────────────────────────────────────────────────────────
    # watcher se crea después del banner para poder referenciar _update_banner
    download_view = DownloadView(downloader)
    library_view = LibraryView()

    # ── Banner de dispositivo ──────────────────────────────────────────────
    device_banner_row = ft.Row(controls=[], expand=False)

    def _update_banner(status: str, label: str = "", free_str: str = "") -> None:
        device_banner_row.controls = [
            device_status_banner(
                status=status,
                label=label,
                free_str=free_str,
                on_manual_pick=_pick_folder_click,
            )
        ]
        try:
            device_banner_row.update()
        except Exception:
            pass

    def _on_device_connected(device: DeviceInfo) -> None:
        downloader.device_root = device.mountpath
        library_view.set_library(Library(device.mountpath))
        free_str = f"{device.free / (1024**3):.1f} GB"
        _update_banner("connected", device.label, free_str)

    def _on_device_disconnected() -> None:
        downloader.device_root = None
        library_view.set_library(None)
        _update_banner("disconnected")

    watcher = DeviceWatcher(
        on_connected=_on_device_connected,
        on_disconnected=_on_device_disconnected,
    )

    settings_view = SettingsView(
        on_manual_path_change=lambda path: watcher.set_manual(path)
    )
    views: list[ft.Control] = [download_view, library_view, settings_view]

    # ── Selector manual de carpeta (async en 0.85) ─────────────────────────
    def _pick_folder_click(e: ft.ControlEvent) -> None:
        asyncio.ensure_future(_pick_folder_async())

    async def _pick_folder_async() -> None:
        path = await file_picker.get_directory_path(
            dialog_title="Selecciona el volumen Shokz"
        )
        if path:
            watcher.set_manual(path)

    # ── NavigationRail ─────────────────────────────────────────────────────
    content_area = ft.Container(
        content=views[0],
        expand=True,
        bgcolor=COLOR_BG,
    )

    def _on_nav_change(e: ft.ControlEvent) -> None:
        idx = e.control.selected_index
        content_area.content = views[idx]
        if idx == 1:
            library_view.refresh()
        try:
            content_area.update()
        except Exception:
            pass

    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        bgcolor=COLOR_SURFACE,
        indicator_color=COLOR_PRIMARY,
        destinations=[
            ft.NavigationRailDestination(
                icon=icon,
                selected_icon=icon,
                label=label,
            )
            for label, icon in NAV_ITEMS
        ],
        on_change=_on_nav_change,
        min_width=80,
        min_extended_width=160,
    )

    # ── Layout final ──────────────────────────────────────────────────────
    top_bar = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(APP_NAME, size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                ft.Container(width=24),
                ft.Container(content=device_banner_row, expand=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=COLOR_SURFACE,
        border=ft.Border.only(bottom=ft.BorderSide(1, COLOR_BORDER)),
        padding=ft.Padding.symmetric(horizontal=16, vertical=10),
        height=52,
    )

    body = ft.Row(
        controls=[
            nav_rail,
            ft.VerticalDivider(width=1, color=COLOR_BORDER),
            content_area,
        ],
        expand=True,
        spacing=0,
    )

    page.add(
        ft.Column(
            controls=[top_bar, body],
            spacing=0,
            expand=True,
        )
    )

    # ── Cleanup al cerrar ──────────────────────────────────────────────────
    def on_window_event(e: ft.WindowEvent) -> None:
        if e.type == ft.WindowEventType.CLOSE:
            watcher.stop()
            downloader.stop()

    page.window.on_event = on_window_event

    # ── Iniciar watcher ────────────────────────────────────────────────────
    _update_banner("searching")
    await watcher.start()
