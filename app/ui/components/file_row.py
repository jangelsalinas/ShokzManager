"""
Fila de fichero en la biblioteca con acciones: mover y borrar.
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
from app.core.library import LibraryItem


def file_row(
    item: LibraryItem,
    on_move=None,
    on_delete=None,
    other_kind_label: str = "Podcast",
) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.AUDIO_FILE, color=COLOR_PRIMARY, size=18),
                ft.Column(
                    controls=[
                        ft.Text(item.name, color=COLOR_TEXT, size=13, no_wrap=True),
                        ft.Text(item.size_str, color=COLOR_TEXT_MUTED, size=11),
                    ],
                    spacing=1,
                    expand=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.SWAP_HORIZ,
                    icon_color=COLOR_TEXT_MUTED,
                    icon_size=18,
                    tooltip=f"Mover a {other_kind_label}",
                    on_click=on_move,
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=COLOR_ERROR,
                    icon_size=18,
                    tooltip="Eliminar",
                    on_click=on_delete,
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        bgcolor=COLOR_SURFACE,
        border=ft.Border.all(1, COLOR_BORDER),
        border_radius=6,
        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        margin=ft.Margin.only(bottom=4),
    )
