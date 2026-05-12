"""
Banner de estado del dispositivo en la cabecera de la app.
"""
from __future__ import annotations

import flet as ft

from app.config import COLOR_ERROR, COLOR_SUCCESS, COLOR_TEXT_MUTED, COLOR_WARNING


def device_status_banner(
    status: str = "searching",  # "searching" | "connected" | "disconnected"
    label: str = "",
    free_str: str = "",
    on_manual_pick=None,
) -> ft.Row:
    if status == "connected":
        icon = ft.Icon(ft.Icons.USB, color=COLOR_SUCCESS, size=18)
        msg = f"Conectado: {label}"
        if free_str:
            msg += f"  —  {free_str} libres"
        color = COLOR_SUCCESS
    elif status == "disconnected":
        icon = ft.Icon(ft.Icons.USB_OFF, color=COLOR_ERROR, size=18)
        msg = "Dispositivo no detectado"
        color = COLOR_ERROR
    else:
        icon = ft.Icon(ft.Icons.SEARCH, color=COLOR_WARNING, size=18)
        msg = "Buscando dispositivo Shokz..."
        color = COLOR_WARNING

    manual_btn = ft.Button(
        content="Seleccionar manualmente",
        icon=ft.Icons.FOLDER_OPEN,
        on_click=on_manual_pick,
        color=COLOR_TEXT_MUTED,
    )

    return ft.Row(
        controls=[
            icon,
            ft.Text(msg, color=color, size=13, weight=ft.FontWeight.W_500),
            ft.Container(expand=True),
            manual_btn,
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
