"""
Vista de biblioteca: tabs Música / Podcasts con acciones por fichero.
API Flet 0.85: ft.Tabs(length=N, content=Column([TabBar, TabBarView]), on_change=...)
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
from app.core.library import Library, LibraryItem
from app.ui.components.file_row import file_row


class LibraryView(ft.Column):
    def __init__(self) -> None:
        super().__init__(expand=True, spacing=0)
        self._library: Library | None = None

        self._music_list = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
        self._podcast_list = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)

        self._tabs_widget = ft.Tabs(
            length=2,
            expand=True,
            on_change=self._on_tab_change,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="Música / Sesiones", icon=ft.Icons.MUSIC_NOTE),
                            ft.Tab(label="Podcasts", icon=ft.Icons.PODCASTS),
                        ],
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            ft.Container(
                                content=self._music_list,
                                padding=ft.Padding.symmetric(vertical=12),
                                expand=True,
                            ),
                            ft.Container(
                                content=self._podcast_list,
                                padding=ft.Padding.symmetric(vertical=12),
                                expand=True,
                            ),
                        ],
                    ),
                ],
            ),
        )

        self._no_device_banner = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.USB_OFF, size=48, color=COLOR_TEXT_MUTED),
                    ft.Text(
                        "Conecta los Shokz OpenSwim Pro para ver la biblioteca.",
                        color=COLOR_TEXT_MUTED,
                        size=14,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
        )
        self._build_ui()

    def _build_ui(self) -> None:
        self.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[self._header_row(), self._no_device_banner],
                    spacing=16,
                    expand=True,
                ),
                padding=ft.Padding.all(24),
                expand=True,
            )
        ]

    def _header_row(self) -> ft.Row:
        return ft.Row(
            controls=[
                ft.Text(
                    "Biblioteca en el dispositivo",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=COLOR_TEXT,
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Actualizar biblioteca",
                    icon_color=COLOR_TEXT_MUTED,
                    on_click=lambda _: self.refresh(),
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def set_library(self, library: Library | None) -> None:
        self._library = library
        self.refresh()

    def refresh(self) -> None:
        col = self.controls[0].content  # ft.Column

        if self._library is None:
            col.controls = [self._header_row(), self._no_device_banner]
        else:
            col.controls = [self._header_row(), self._tabs_widget]
            self._load_kind("musica")
            self._load_kind("podcast")

        try:
            self.update()
        except Exception:
            pass

    def _load_kind(self, kind: str) -> None:
        if self._library is None:
            return
        items = self._library.list(kind)
        target = self._music_list if kind == "musica" else self._podcast_list
        other_label = "Podcasts" if kind == "musica" else "Música"

        if not items:
            folder = "Música / Sesiones" if kind == "musica" else "Podcasts"
            target.controls = [
                ft.Container(
                    content=ft.Text(
                        f"No hay ficheros en {folder}.",
                        color=COLOR_TEXT_MUTED,
                        size=13,
                    ),
                    padding=ft.Padding.all(16),
                )
            ]
        else:
            target.controls = [
                file_row(
                    item,
                    on_move=self._make_move_handler(item, kind),
                    on_delete=self._make_delete_handler(item),
                    other_kind_label=other_label,
                )
                for item in items
            ]
        try:
            target.update()
        except Exception:
            pass

    def _make_move_handler(self, item: LibraryItem, current_kind: str):
        def handler(e: ft.ControlEvent) -> None:
            if self._library is None:
                return
            new_kind = "podcast" if current_kind == "musica" else "musica"
            try:
                self._library.move(item.path, new_kind)
                self.refresh()
            except Exception as exc:
                self._show_snack(str(exc), error=True, page=e.page)
        return handler

    def _make_delete_handler(self, item: LibraryItem):
        def handler(e: ft.ControlEvent) -> None:
            def confirm(ev: ft.ControlEvent) -> None:
                e.page.pop_dialog()
                if self._library is None:
                    return
                try:
                    self._library.delete(item.path)
                    self.refresh()
                except Exception as exc:
                    self._show_snack(str(exc), error=True, page=e.page)

            def cancel(ev: ft.ControlEvent) -> None:
                e.page.pop_dialog()

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Eliminar fichero"),
                content=ft.Text(
                    f"¿Seguro que quieres eliminar '{item.name}'?\n"
                    "Esta acción no se puede deshacer."
                ),
                actions=[
                    ft.Button(content="Cancelar", on_click=cancel),
                    ft.Button(
                        content="Eliminar",
                        bgcolor=COLOR_ERROR,
                        color=ft.Colors.WHITE,
                        on_click=confirm,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            e.page.show_dialog(dlg)
        return handler

    def _on_tab_change(self, e: ft.ControlEvent) -> None:
        pass  # La carga ya ocurrió en refresh()

    def _show_snack(self, msg: str, error: bool = False, page=None) -> None:
        if page is None:
            return
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(msg),
                bgcolor=COLOR_ERROR if error else None,
            )
        )
