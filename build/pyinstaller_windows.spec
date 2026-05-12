# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para Windows
# Uso (en PowerShell): pyinstaller build\pyinstaller_windows.spec

from pathlib import Path

ROOT = Path(SPECPATH).parent  # shokzmanager\

# Incluir datas sólo si existen (bin se descarga en CI antes del build)
datas = []
win_bin = ROOT / "resources" / "bin" / "windows"
if any(f for f in win_bin.iterdir() if f.suffix == ".exe") if win_bin.exists() else False:
    datas.append((str(win_bin), "resources/bin/windows"))
icons_dir = ROOT / "resources" / "icons"
if icons_dir.exists() and any(icons_dir.iterdir()):
    datas.append((str(icons_dir), "resources/icons"))

icon_file = ROOT / "resources" / "icons" / "app.ico"
icon_arg = str(icon_file) if icon_file.exists() else None

a = Analysis(
    [str(ROOT / "app" / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "flet",
        "flet_core",
        "yt_dlp",
        "psutil",
        "platformdirs",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ShokzManager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # UPX no disponible en runners de CI
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_arg,
    version_file=None,
)
