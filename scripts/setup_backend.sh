#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Update DATABASE_URL and OPENROUTER_API_KEY or GEMINI_API_KEY as needed."
fi

cd apps/api
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Backend setup complete."
