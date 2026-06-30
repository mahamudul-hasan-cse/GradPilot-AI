@echo off
setlocal

cd /d "%~dp0..\apps\api"

if not exist ".venv\Scripts\activate.bat" (
  echo Backend virtualenv not found. Run scripts\setup_backend.bat first.
  exit /b 1
)

call .venv\Scripts\activate.bat
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
