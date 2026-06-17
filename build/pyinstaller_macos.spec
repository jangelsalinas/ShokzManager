# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para macOS
# Uso: pyinstaller build/pyinstaller_macos.spec

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

ROOT = Path(SPECPATH).parent  # shokzmanager/

# Incluir datas sólo si existen (bin se descarga en CI antes del build)
datas = []
mac_bin = ROOT / "resources" / "bin" / "macos"
if mac_bin.exists() and any(f for f in mac_bin.iterdir() if f.name == "ffmpeg"):
    datas.append((str(mac_bin), "resources/bin/macos"))
icons_dir = ROOT / "resources" / "icons"
if icons_dir.exists() and any(icons_dir.iterdir()):
    datas.append((str(icons_dir), "resources/icons"))

# Flet carga este archivo JSON en runtime para resolver iconos de Material.
datas += collect_data_files("flet.controls.material", includes=["icons.json"])

icon_file = ROOT / "resources" / "icons" / "app.icns"
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
    [],
    exclude_binaries=True,
    name="ShokzManager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # UPX no disponible en runners de CI
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,    # None = arco nativo; usa "universal2" para fat binary
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_arg,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ShokzManager",
)

app = BUNDLE(
    coll,
    name="ShokzManager.app",
    icon=icon_arg,
    bundle_identifier="com.shokzmanager.app",
    version="0.1.0",
    info_plist={
        "CFBundleDisplayName": "ShokzManager",
        "CFBundleShortVersionString": "0.1.0",
        "NSHighResolutionCapable": True,
        "NSRequiresAquaSystemAppearance": False,
    },
)
