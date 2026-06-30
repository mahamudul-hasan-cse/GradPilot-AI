#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../apps/api"

if [ ! -d ".venv" ]; then
  echo "Backend virtualenv not found. Run scripts/setup_backend.sh first."
  exit 1
fi

source .venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
