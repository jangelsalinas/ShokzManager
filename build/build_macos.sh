#!/bin/bash
# build/build_macos.sh
# Genera ShokzManager.app para macOS.
# Ejecutar desde la raíz de shokzmanager/ con el venv activo.
#
# Opciones:
#   --download-ffmpeg   Descarga ffmpeg automáticamente si no existe

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."
FFMPEG_PATH="$ROOT/resources/bin/macos/ffmpeg"
DOWNLOAD_FFMPEG=false

for arg in "$@"; do
  [[ "$arg" == "--download-ffmpeg" ]] && DOWNLOAD_FFMPEG=true
done

echo "==> Comprobando ffmpeg en resources/bin/macos/..."
if [ ! -f "$FFMPEG_PATH" ]; then
  if [ "$DOWNLOAD_FFMPEG" = true ]; then
    echo "  Descargando ffmpeg..."
    mkdir -p "$ROOT/resources/bin/macos"
    curl -L "https://evermeet.cx/ffmpeg/getrelease/zip" -o /tmp/ffmpeg.zip
    unzip -o /tmp/ffmpeg.zip -d /tmp/ffmpeg_extracted
    cp /tmp/ffmpeg_extracted/ffmpeg "$FFMPEG_PATH"
  else
    echo "ERROR: Falta resources/bin/macos/ffmpeg"
    echo "Descárgalo de https://evermeet.cx/ffmpeg/ o usa --download-ffmpeg"
    exit 1
  fi
fi
chmod +x "$FFMPEG_PATH"
echo "  ffmpeg OK: $("$FFMPEG_PATH" -version 2>&1 | head -1)"

echo "==> Instalando dependencias..."
pip install -q -r "$ROOT/requirements.txt"
pip install -q pyinstaller

echo "==> Ejecutando PyInstaller..."
cd "$ROOT"
pyinstaller build/pyinstaller_macos.spec --noconfirm --clean

echo ""
echo "Build completado. Resultado: dist/ShokzManager.app"
echo ""
echo "Si macOS bloquea la app, ejecuta:"
echo "  xattr -rd com.apple.quarantine dist/ShokzManager.app"
