@echo off
setlocal

cd /d "%~dp0.."
npm install

if not exist "apps\web\.env.local" (
  copy "apps\web\.env.example" "apps\web\.env.local" >nul
  echo Created apps\web\.env.local from .env.example. Update AUTH_SECRET to match root .env.
)

echo Frontend setup complete.
