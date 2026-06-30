#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
npm install

if [ ! -f "apps/web/.env.local" ]; then
  cp apps/web/.env.example apps/web/.env.local
  echo "Created apps/web/.env.local from .env.example. Update AUTH_SECRET to match root .env."
fi

echo "Frontend setup complete."
