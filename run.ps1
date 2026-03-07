# Run both demo_app and backend (Windows / PowerShell)
$ErrorActionPreference = "Stop"

# Create venv if missing
if (-not (Test-Path ".\.venv")) {
  python -m venv .venv
}

# Activate venv
. .\.venv\Scripts\Activate.ps1

Write-Host "[1/3] Installing demo_app deps..."
pip install -r .\demo_app\requirements.txt

Write-Host "[2/3] Installing backend deps..."
pip install -r .\backend\requirements.txt

Write-Host "[3/3] Starting servers..."
Start-Process powershell.exe -ArgumentList '-NoExit','-Command','cd demo_app; ..\.venv\Scripts\python.exe app.py'

cd backend
python -m uvicorn app.main:app --reload --port 8000
