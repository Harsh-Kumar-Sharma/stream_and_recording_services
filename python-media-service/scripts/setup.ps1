param(
    [string]$PythonVersion = "3.12"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

Set-Location $ProjectRoot

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Write-Error "Python Launcher 'py' was not found. Install Python 3.12 or 3.13, then rerun this script."
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating virtual environment with Python $PythonVersion..."
    py "-$PythonVersion" -m venv .venv
}

& $VenvPython scripts\check_python_version.py
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Your existing .venv uses an unsupported Python version."
    Write-Host "Fix:"
    Write-Host "  Remove-Item -Recurse -Force .venv"
    Write-Host "  .\scripts\setup.ps1"
    exit $LASTEXITCODE
}

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r requirements.txt

