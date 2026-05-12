# ShokzManager

Aplicación de escritorio multiplataforma (macOS + Windows 11) para gestionar los auriculares **Shokz OpenSwim Pro** en modo MP3.

Descarga audio de YouTube y Mixcloud, lo convierte a `.mp3` y lo organiza directamente en el dispositivo separando **Música/Sesiones** de **Podcasts**.

---

## Requisitos de desarrollo

- Python 3.11+
- `ffmpeg` (ver sección Empaquetado)

## Instalación (desarrollo)

```bash
cd shokzmanager
python3 -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\Activate.ps1       # Windows

pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Arrancar la app

```bash
source .venv/bin/activate
python -m app.main
```

## Tests

```bash
pytest tests/ -v
```

## Estructura

```
app/
├── main.py                 # Entry point
├── config.py               # Constantes globales
├── settings.py             # Preferencias persistidas en JSON
├── core/
│   ├── device.py           # Detección USB + polling
│   ├── downloader.py       # yt-dlp + cola de descargas
│   ├── library.py          # CRUD de ficheros en el dispositivo
│   └── ffmpeg.py           # Localización del binario ffmpeg
├── ui/
│   ├── app_view.py         # Layout principal
│   ├── views/
│   │   ├── download_view.py
│   │   ├── library_view.py
│   │   └── settings_view.py
│   └── components/
│       ├── device_status.py
│       ├── file_row.py
│       └── progress_card.py
└── utils/
    ├── logging.py
    └── paths.py
```

## Empaquetado

### Requisito previo: ffmpeg

Antes de hacer el build debes colocar el binario de `ffmpeg` en:

- **macOS**: `resources/bin/macos/ffmpeg`  
  Descarga desde https://evermeet.cx/ffmpeg/
- **Windows**: `resources/bin/windows/ffmpeg.exe`  
  Descarga desde https://www.gyan.dev/ffmpeg/builds/ (release-essentials)

### macOS

```bash
source .venv/bin/activate
bash build/build_macos.sh
# Resultado: dist/ShokzManager.app
```

Si macOS bloquea la app al abrirla por primera vez:
```bash
xattr -rd com.apple.quarantine dist/ShokzManager.app
```

### Windows

```powershell
.venv\Scripts\Activate.ps1
.\build\build_windows.ps1
# Resultado: dist\ShokzManager.exe
```

## Uso básico

1. Conecta los Shokz OpenSwim Pro al ordenador por USB.
2. La app detecta automáticamente el volumen `NO NAME` y crea las carpetas `Musica/` y `Podcasts/` si no existen.
3. En la pestaña **Descargar**, pega una URL de YouTube o Mixcloud, selecciona el tipo (*Música* o *Podcast*) y pulsa **Descargar y enviar**.
4. En la pestaña **Biblioteca** puedes ver, mover y eliminar los ficheros del dispositivo.
5. En **Ajustes** puedes cambiar la ruta manual, la calidad del MP3 (128/192/320 kbps) y activar/desactivar la detección automática.
