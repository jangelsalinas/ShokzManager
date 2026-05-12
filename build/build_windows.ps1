# build/build_windows.ps1
# Genera ShokzManager.exe para Windows.
# Ejecutar desde la raiz de shokzmanager\ con el venv activo.
#
# Opciones:
#   -DownloadFfmpeg   Descarga ffmpeg automaticamente si no existe

param(
    [switch]$DownloadFfmpeg
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$FfmpegPath = "$Root\resources\bin\windows\ffmpeg.exe"

Write-Host "==> Comprobando ffmpeg en resources\bin\windows\..."
if (-not (Test-Path $FfmpegPath)) {
    if ($DownloadFfmpeg) {
        Write-Host "  Descargando ffmpeg..."
        New-Item -ItemType Directory -Force -Path "$Root\resources\bin\windows" | Out-Null
        $url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        Invoke-WebRequest -Uri $url -OutFile "$env:TEMP\ffmpeg.zip"
        Expand-Archive -Path "$env:TEMP\ffmpeg.zip" -DestinationPath "$env:TEMP\ffmpeg_extracted" -Force
        $ffmpegExe = Get-ChildItem -Path "$env:TEMP\ffmpeg_extracted" -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
        Copy-Item $ffmpegExe.FullName -Destination $FfmpegPath
    } else {
        Write-Error "Falta resources\bin\windows\ffmpeg.exe`nDescargalo de https://www.gyan.dev/ffmpeg/builds/ o usa -DownloadFfmpeg"
        exit 1
    }
}
Write-Host "  ffmpeg OK: $(& $FfmpegPath -version 2>&1 | Select-Object -First 1)"

Write-Host "==> Instalando dependencias..."
pip install -q -r "$Root\requirements.txt"
pip install -q pyinstaller

Write-Host "==> Ejecutando PyInstaller..."
Set-Location $Root
pyinstaller build\pyinstaller_windows.spec --noconfirm --clean

Write-Host ""
Write-Host "Build completado. Resultado: dist\ShokzManager.exe"
