.PHONY: up down build logs migrate migration shell-api shell-db test

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

migrate:
	docker compose exec api alembic upgrade head

ingest-sources:
	docker compose exec api python scripts/load_sources.py

migration:
	docker compose exec api alembic revision --autogenerate -m "$(msg)"

shell-api:
	docker compose exec api bash

shell-db:
	docker compose exec postgres psql -U gradpilot -d gradpilot

test:
	docker compose exec api pytest -v
