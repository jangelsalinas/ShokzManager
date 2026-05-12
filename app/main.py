"""
Entry point de ShokzManager.
"""
from __future__ import annotations

import flet as ft

from app.ui.app_view import build_app
from app.utils.logging import setup_logging
from app.config import WINDOW_HEIGHT, WINDOW_WIDTH


def main() -> None:
    setup_logging()
    ft.app(target=build_app)


if __name__ == "__main__":
    main()
