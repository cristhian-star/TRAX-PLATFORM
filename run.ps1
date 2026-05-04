Write-Host "=============================" -ForegroundColor DarkGray
Write-Host "Iniciando TRAX..." -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor DarkGray

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Write-Host "Activando entorno virtual..." -ForegroundColor Yellow

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "ERROR: No se encontró el entorno virtual (.venv)" -ForegroundColor Red
    exit
}

Write-Host "Ejecutando servidor Flask..." -ForegroundColor Green

python run.py