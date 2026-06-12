"""
Entry point de ShokzManager.
"""
from __future__ import annotations

import argparse

import flet as ft

from app.config import APP_NAME, APP_VERSION
from app.ui.app_view import build_app
from app.utils.logging import setup_logging


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=APP_NAME)
    parser.add_argument("--version", action="store_true", help="Muestra versión y sale")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.version:
        print(f"{APP_NAME} {APP_VERSION}")
        return 0

    setup_logging()
    ft.app(target=build_app)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
