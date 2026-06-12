from __future__ import annotations

from app.config import APP_NAME, APP_VERSION
from app.main import main


def test_main_version_flag_prints_version_and_exits(capsys):
    exit_code = main(["--version"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == f"{APP_NAME} {APP_VERSION}"


def test_main_runs_flet_app_without_version(monkeypatch):
    called = {"setup_logging": False, "ft_app": False}

    def fake_setup_logging():
        called["setup_logging"] = True
        return None

    def fake_ft_app(*, target):
        called["ft_app"] = True
        assert callable(target)

    monkeypatch.setattr("app.main.setup_logging", fake_setup_logging)
    monkeypatch.setattr("app.main.ft.app", fake_ft_app)

    exit_code = main([])

    assert exit_code == 0
    assert called["setup_logging"] is True
    assert called["ft_app"] is True
