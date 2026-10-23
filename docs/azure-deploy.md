# Deploy GradPilot on Azure for Students

The Next.js app stays on Vercel. The FastAPI API in `apps/api` runs as a Linux container on Azure App Service. This is the live production layout. Nothing in git contains secret values.

## Live layout

| Piece | Where it runs |
|-------|----------------|
| Frontend | Vercel — [https://gradpilot-ai.vercel.app](https://gradpilot-ai.vercel.app) |
| API | Azure App Service (Linux container) — [https://gradpilot-api-gp.azurewebsites.net](https://gradpilot-api-gp.azurewebsites.net) |
| Resource group | `rg-gradpilot` in `centralindia` |
| Database | PostgreSQL Flexible Server (still used) |
| Secrets | Key Vault (still used) |
| Images | Azure Container Registry (still used) |

`infra/` and `azure.yaml` still describe an earlier Container Apps deployment. Container App `ca-gp-api-ge7asi` may still exist in `rg-gradpilot`, but it is scaled down and is **not** the live API.

## Why App Service

Azure for Students **Express** Container Apps silently drop registry credentials, so pulls from a private ACR fail. App Service with ACR admin credentials succeeds, so that is the production host.

ACR Tasks are blocked on the Students subscription. Build the image locally and push it:

```bash
docker build -t crgpge7asi.azurecr.io/gradpilot-api:latest apps/api
docker push crgpge7asi.azurecr.io/gradpilot-api:latest
```

The live image is `crgpge7asi.azurecr.io/gradpilot-api:latest`.

## App Service settings

Set these on the App Service (`gradpilot-api-gp`):

| Name | Value |
|------|--------|
| `DATABASE_URL` | Postgres URL for Flexible Server (`sslmode=require`) |
| `SECRET_KEY` | At least 32 characters |
| `JWT_SECRET` | At least 32 characters. The API signs tokens with this |
| `OPENROUTER_API_KEY` | OpenRouter key |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` |
| `CORS_ORIGINS` | Must include `https://gradpilot-ai.vercel.app`. Loopback origins (`localhost`, `127.0.0.1`) are dropped automatically when `ENVIRONMENT=production` |
| `WEBSITES_PORT` | `8000` |

`WEBSITES_PORT` tells App Service which port the container listens on. The image runs uvicorn on port 8000.

## Migrate the database

Run Alembic **once** as a one-shot Azure Container Instance that uses the same image and `DATABASE_URL`:

```bash
alembic upgrade head
```

The dev machine cannot reach Flexible Server. App Service can, and a Container Instance in Azure can, so the one-shot ACI is the migration path.

`apps/api/alembic/env.py` passes `settings.sync_database_url` through `str.replace("%", "%%")` before `config.set_main_option`. Alembic's ConfigParser treats `%` as interpolation. URL-encoded passwords (and other `%` sequences) must be doubled or the migration exits before it connects.

There is no data copy from another host. `upgrade head` creates the schema on this Flexible Server.

## Point Vercel at the API

In the Vercel project for `apps/web`:

1. Set `NEXT_PUBLIC_API_URL` to `https://gradpilot-api-gp.azurewebsites.net` (no trailing slash).
2. Redeploy the web app.

The frontend stays on Vercel.

## Health

```bash
curl https://gradpilot-api-gp.azurewebsites.net/health
curl https://gradpilot-api-gp.azurewebsites.net/health/ready
```

| Path | Meaning |
|------|---------|
| `GET /health` | Process is up. Returns `{"status":"healthy",...}` |
| `GET /health/ready` | Process is up and Postgres accepts `SELECT 1` |
