@echo off
setlocal

cd /d "%~dp0.."

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Created .env from .env.example. Update DATABASE_URL and GEMINI_API_KEY as needed.
)

cd apps\api
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo Backend setup complete.
