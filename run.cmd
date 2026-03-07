@echo off
setlocal

if not exist ".venv" (
  python -m venv .venv
)

call .venv\Scripts\activate.bat

echo [1/3] Installing demo_app deps...
pip install -r demo_app\requirements.txt

echo [2/3] Installing backend deps...
pip install -r backend\requirements.txt

echo [3/3] Starting servers...
start "demo_app" cmd /k "cd demo_app && ..\.venv\Scripts\python.exe app.py"

cd backend
python -m uvicorn app.main:app --reload --port 8000
