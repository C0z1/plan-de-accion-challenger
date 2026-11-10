# Build de HTC (How to Climb): onedir (arranca sin desempacar) + instalador si hay Inno Setup.
#   powershell -File instalador/build.ps1
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot)
python -m PyInstaller --noconfirm --onedir --windowed --name HTC --icon instalador/htc.ico --distpath dist --workpath build `
  --add-data "scripts/web;web" --paths scripts scripts/companion_web.py
if ($LASTEXITCODE) { exit $LASTEXITCODE }
python scripts/humo_exe.py dist/HTC/HTC.exe
if ($LASTEXITCODE) { exit $LASTEXITCODE }
$iscc = @("$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe", "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($iscc) { & $iscc instalador/htc.iss } else { "Sin Inno Setup: winget install JRSoftware.InnoSetup (dist/HTC ya sirve sin instalar)" }
