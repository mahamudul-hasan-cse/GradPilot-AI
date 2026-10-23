# Deploy the GradPilot API to Azure

The FastAPI app in `apps/api` runs on Azure Container Apps in **centralindia**. The Next.js app stays on Vercel at `https://gradpilot-ai.vercel.app`.

Infrastructure is Azure Developer CLI (`azd`) plus Bicep in `infra/`. Nothing in git contains secret values. `azd` keeps them in `.azure/<environment>/.env`, which is gitignored.

## What gets created

Resource group **`rg-gradpilot`**:

| Piece | Setting |
|-------|---------|
| Container Apps environment | Consumption |
| Container App `api` | Public HTTPS ingress, port 8000, min replicas 0, max 1, 0.5 vCPU / 1Gi |
| Container Registry | Basic, admin user off |
| PostgreSQL Flexible Server | Burstable **Standard_B1ms**, PostgreSQL 16, 32GB, autogrow off, HA off, TLS required |
| Key Vault | RBAC, soft-delete 7 days |
| Log Analytics | 30-day retention, 0.1GB daily cap |
| Application Insights | Workspace-based |

The container app receives `DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET`, and `OPENROUTER_API_KEY` as Container App secret values. Azure for Students uses Express Container Apps environments, which reject Key Vault URL secret references (`ExpressEnvironmentFeatureNotSupported`). The same four values are still written to Key Vault for storage and rotation. A **system-assigned** identity is used for ACR pull (`azd deploy` runs `az containerapp registry set --identity system`). The user-assigned identity keeps Key Vault Secrets User for operators.

Postgres is reached over TLS. Container Apps Consumption does not have a stable outbound IP, so the firewall allows public clients by default (`postgresPublicAccess = true` in `infra/main.bicep`). The password is a secure parameter, stored in Key Vault and injected into the Container App. It is not committed. To restrict the rule to other Azure services, set that parameter to `false` and provision again. If the API then cannot connect, the region needs a NAT gateway, which this student layout avoids.

## Prerequisites

- Azure CLI and [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- Docker (used by `azd deploy` to build `apps/api/Dockerfile`)
- Access to the **Azure for Students** subscription
- `Microsoft.App`, `Microsoft.DBforPostgreSQL`, `Microsoft.ContainerRegistry`, `Microsoft.KeyVault`, `Microsoft.OperationalInsights`, and `Microsoft.Insights` registered

```bash
az login
az account set --subscription "<Azure for Students subscription name or id>"
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.DBforPostgreSQL
az provider register --namespace Microsoft.ContainerRegistry
az provider register --namespace Microsoft.KeyVault
az provider register --namespace Microsoft.OperationalInsights
az provider register --namespace Microsoft.Insights
```

## Environment variables

Set these with `azd env set` **before** `azd up`. `--secret` keeps the value out of process listings and out of git.

| azd / process name | Required | Where it goes | Notes |
|--------------------|----------|---------------|-------|
| `AZURE_ENV_NAME` | Yes | Resource tags and name suffix | Set by `azd env new gradpilot` |
| `AZURE_LOCATION` | Yes | All resources | `centralindia` |
| `AZURE_SUBSCRIPTION_ID` | Yes | Deployment target | Azure for Students subscription |
| `AZURE_RESOURCE_GROUP` | No | Resource group name | Default `rg-gradpilot` |
| `POSTGRES_ADMIN_LOGIN` | No | Postgres admin user | Default `gradpilot`. Cannot change later |
| `POSTGRES_ADMIN_PASSWORD` | Yes | Key Vault secret `database-url` | 8–128 chars. Use upper, lower, number, and symbol |
| `SECRET_KEY` | Yes | Key Vault secret `secret-key` | At least 32 characters |
| `JWT_SECRET` | Yes | Key Vault secret `jwt-secret` | At least 32 characters. This is what the API uses to sign tokens |
| `OPENROUTER_API_KEY` | Yes | Key Vault secret `openrouter-api-key` | Preferred LLM. Gemini is not required when this is set |
| `OPENROUTER_MODEL` | No | Container env | Default `openai/gpt-4o-mini` (same as the API) |
| `CORS_ORIGINS` | No | Container env | Default `https://gradpilot-ai.vercel.app,http://localhost:3000,http://127.0.0.1:3000` |
| `KEY_VAULT_OFFICER_PRINCIPAL_TYPE` | No | Key Vault RBAC | `User` for `azd auth login`. `ServicePrincipal` for a pipeline identity |

The container also receives these plain settings (not secrets):

| Name | Value |
|------|-------|
| `PORT` | `8000` |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `REDIS_ENABLED` | `false` |
| `LOG_LEVEL` | `INFO` |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | From Application Insights |

`DATABASE_URL` is built as `postgresql://<user>:<password>@<host>:5432/gradpilot?sslmode=require`. The app rewrites `sslmode` to asyncpg's `ssl=require`. Alembic keeps `sslmode` for psycopg2.

Health probes:

| Probe | Path |
|-------|------|
| Startup and liveness | `/health` |
| Readiness | `/health/ready` (runs `SELECT 1`) |

Scale defaults live in `infra/main.bicep` (`apiMinReplicas = 0`, `apiMaxReplicas = 1`). Idle replicas cost no Container Apps CPU. The first request after idle has a cold start. Set `apiMinReplicas` to `1` if the API should stay warm.

## Provision and deploy

From the repository root:

```bash
azd auth login
azd env new gradpilot
azd env set AZURE_LOCATION centralindia
azd env set AZURE_SUBSCRIPTION_ID "<subscription-id>"
azd env set AZURE_RESOURCE_GROUP rg-gradpilot

azd env set POSTGRES_ADMIN_PASSWORD "$(openssl rand -base64 24)" --secret
azd env set SECRET_KEY "$(openssl rand -hex 32)" --secret
azd env set JWT_SECRET "$(openssl rand -hex 32)" --secret
azd env set OPENROUTER_API_KEY "<your-openrouter-key>" --secret
```

`POSTGRES_ADMIN_PASSWORD` from `openssl rand -base64` can include characters the server accepts. If Flexible Server rejects the password, generate another value that contains upper, lower, number, and a symbol such as `_`.

```bash
azd up
```

`azd up` provisions `infra/main.bicep`, builds `apps/api/Dockerfile`, pushes it to ACR, and points the Container App at that image. The first provision uses a public placeholder image so the app and its identity can be created. `azd deploy` (included in `azd up`) then switches the image.

If Key Vault secret creation returns Forbidden, wait a minute and run `azd provision` again. The deployment grants **Key Vault Secrets Officer** to your user, and that role can take a moment to propagate. The same applies to **AcrPull** on the system identity if the new revision cannot pull the image. Run `azd deploy` again after a few minutes.

Useful outputs (also stored in the azd environment):

```bash
azd env get-values
```

| Output | Meaning |
|--------|---------|
| `API_URL` | Public HTTPS URL, for example `https://ca-gp-api-xxxxxx.<region>.azurecontainerapps.io` |
| `AZURE_RESOURCE_GROUP` | `rg-gradpilot` |
| `AZURE_KEY_VAULT_NAME` | Vault that holds the four secrets |
| `AZURE_CONTAINER_REGISTRY_ENDPOINT` | ACR login server |
| `AZURE_CONTAINER_APP_NAME` | Container App name |
| `AZURE_POSTGRES_FQDN` | Database host |

Check the process:

```bash
curl "$(azd env get-value API_URL)/health"
curl "$(azd env get-value API_URL)/health/ready"
```

`/health` returns `{"status":"healthy",...}`. `/health/ready` also checks Postgres.

## Migrate the database

The image includes Alembic. Run the migration inside the Container App so it uses the injected `DATABASE_URL`:

```bash
az containerapp exec \
  --resource-group rg-gradpilot \
  --name "$(azd env get-value AZURE_CONTAINER_APP_NAME)" \
  --command "sh -c 'cd /app && alembic upgrade head'"
```

There is no data copy from Render. This creates a fresh schema.

## Point Vercel at the API

In the Vercel project for `apps/web`:

1. Set `NEXT_PUBLIC_API_URL` to the `API_URL` value (`https://...azurecontainerapps.io`, no trailing slash).
2. Redeploy the web app.

The API `CORS_ORIGINS` value already allows `https://gradpilot-ai.vercel.app` and local Next.js. Add preview origins by updating the env var and provisioning again:

```bash
azd env set CORS_ORIGINS "https://gradpilot-ai.vercel.app,https://<preview>.vercel.app,http://localhost:3000,http://127.0.0.1:3000"
azd provision
```

Do not move the Next.js app into this `azure.yaml`. It is not an Azure service.

## Rotate a secret

```bash
azd env set OPENROUTER_API_KEY "<new-key>" --secret
azd provision
```

Provision rewrites the Key Vault secret and the Container App secret value. Start a new revision if the running one still has the old value:

```bash
az containerapp revision restart \
  --resource-group rg-gradpilot \
  --name "$(azd env get-value AZURE_CONTAINER_APP_NAME)"
```

## Cost notes

This layout stays on the smallest Flexible Server size (B1ms), Basic registry, Consumption with scale-to-zero, and a Log Analytics daily cap. Postgres and the registry are the steady charges. Container Apps CPU is billed only while a replica is running. The Azure for Students spending limit remains the backstop. Watch Cost Management after the first day, and stop the Flexible Server from the portal if the app will sit unused.

## Local image check

```bash
docker build -t gradpilot-api:local apps/api
docker run --rm -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DEBUG=false \
  -e SECRET_KEY="$(openssl rand -hex 32)" \
  -e JWT_SECRET="$(openssl rand -hex 32)" \
  -e OPENROUTER_API_KEY=local-check \
  -e DATABASE_URL=postgresql://gradpilot:gradpilot@127.0.0.1:5432/gradpilot \
  gradpilot-api:local
```

`GET /health` should return 200 without `GEMINI_API_KEY`. `/health/ready` needs a reachable Postgres instance.
