# Azure Deployment Plan

> **Status:** Ready for provisioning

Generated: 2026-10-23

---

## 1. Project Overview

**Goal:** Prepare the GradPilot FastAPI API for Azure Container Apps in `centralindia` on the Azure for Students subscription. Keep the Next.js frontend on Vercel (`https://gradpilot-ai.vercel.app`). This change adds azd + Bicep and a production Dockerfile on top of `main` (OpenRouter provider already merged). It does not run `azd up` and does not delete Render resources.

**Path:** Modernize Existing

---

## 2. Requirements

| Attribute | Value |
|-----------|-------|
| Classification | Production (student portfolio / live app) |
| Scale | Small |
| Budget | Cost-Optimized (Azure for Students $100, spending limit On) |
| **Subscription** | Azure for Students (approved 2026-10-23) |
| **Location** | `centralindia` (approved 2026-10-23). Fallback if a SKU is unavailable: `southeastasia` |

---

## 3. Components Detected

| Component | Type | Technology | Path |
|-----------|------|------------|------|
| API | API | FastAPI + Uvicorn + SQLAlchemy/asyncpg + Alembic | `apps/api` |
| Web | Frontend | Next.js, already on Vercel | `apps/web` — not deployed to Azure |
| DB | Database | PostgreSQL | Azure Database for PostgreSQL Flexible Server |
| Secrets | Config | DATABASE_URL, SECRET_KEY, JWT_SECRET, OPENROUTER_API_KEY | Key Vault, referenced by the Container App |

---

## 4. Recipe Selection

**Selected:** AZD (Bicep infra)

**Rationale:** Official Azure Developer CLI path. Container Apps + Flexible Server fit the FastAPI image. AVM resource modules were considered (`br/public:avm/res/app/container-app`, `br/public:avm/res/db-for-postgre-sql/flexible-server`). Native Bicep is used instead so `azd deploy` can attach ACR with the system-assigned identity (no `registries` block) and so Key Vault references use a user-assigned identity that exists before the container app is created.

---

## 5. Architecture

**Stack:** Containers (Azure Container Apps, Consumption)

### Service Mapping

| Component | Azure Service | SKU |
|-----------|---------------|-----|
| API | Azure Container Apps | Consumption, min replicas 0, max 1, 0.5 vCPU / 1Gi |
| Container registry | Azure Container Registry | Basic, admin user disabled |
| Database | Azure Database for PostgreSQL Flexible Server | Burstable Standard_B1ms, 32GB, HA off, geo-backup off, TLS required |
| Secrets | Key Vault | Standard, RBAC, soft delete 7 days |
| Logs / APM | Log Analytics + Application Insights | PerGB2018, 30-day retention, 0.1 GB daily cap |
| Resource group | `rg-gradpilot` | Parameter default |

### Supporting Services

| Service | Purpose |
|---------|---------|
| Log Analytics | Container Apps console logs |
| Application Insights | Workspace-based APM resource; connection string passed to the app |
| Key Vault | DATABASE_URL, SECRET_KEY, JWT_SECRET, OPENROUTER_API_KEY |
| User-assigned managed identity | Key Vault Secrets User, so secret references exist at app create time |
| System-assigned managed identity | AcrPull for `azd deploy` (`az containerapp registry set --identity system`) |

### Out of scope on Azure

- Next.js stays at https://gradpilot-ai.vercel.app
- Redis and Qdrant stay off (`REDIS_ENABLED=false`)
- Render teardown is not part of this pull request

### Security notes

- No secret values in git. Secure parameters come from the azd environment.
- PostgreSQL password authentication is required for asyncpg. The SQL Server Entra-only rule does not apply to Flexible Server. The admin password is a secure parameter and is stored only in Key Vault.
- Container Apps Consumption has dynamic egress. The default firewall allows public clients over TLS so the API can connect without a NAT gateway. Set `postgresPublicAccess=false` later to limit the rule to Azure services only.

---

## 6. Provisioning Limit Checklist

Quota CLI was checked on 2026-10-23 against the Azure for Students subscription in `centralindia`. Providers that returned BadRequest use the published service limits. An existing resource group `MyVM` is already in this region. No new storage account is required.

### Phase 1 and Phase 2

| Resource Type | Number to Deploy | Total After Deployment | Limit/Quota | Notes |
|---------------|------------------|------------------------|-------------|-------|
| Microsoft.Resources/resourceGroups | 1 | 2 | Soft / high | `rg-gradpilot` plus existing `MyVM`. Source: approved plan, 2026-10-23 |
| Microsoft.App/managedEnvironments | 1 | 1 | Students subscription allows Consumption environments | Quota API was registering; docs fallback. Source: approved plan |
| Microsoft.App/containerApps | 1 | 1 | Same as managed environments | Consumption. Source: approved plan |
| Microsoft.ContainerRegistry/registries | 1 | 1 | Basic SKU available in centralindia | Quota CLI BadRequest; docs fallback |
| Microsoft.DBforPostgreSQL/flexibleServers | 1 | 1 | Burstable B1ms is the smallest Flexible Server size | Quota CLI BadRequest; docs fallback |
| Microsoft.KeyVault/vaults | 1 | 1 | Standard vault per region well above 1 | Docs fallback |
| Microsoft.OperationalInsights/workspaces | 1 | 1 | Pay-as-you-go workspace | Docs fallback |
| Microsoft.Insights/components | 1 | 1 | Workspace-based Application Insights | Docs fallback |
| Microsoft.ManagedIdentity/userAssignedIdentities | 1 | 1 | High soft limit | Identity for Key Vault |
| Microsoft.Storage/storageAccounts | 0 | unchanged | n/a | Not deployed |

**Status:** All planned resources are within published limits for a first deployment in `centralindia`.

**Capacity decision:** Proceed in `centralindia`. If B1ms or Container Apps capacity is refused, retry `southeastasia` by setting `AZURE_LOCATION`.

---

## 7. Execution Checklist

### Phase 1: Planning
- [x] Analyze workspace
- [x] Gather requirements
- [x] Confirm subscription and location with user
- [x] Prepare resource inventory
- [x] Fetch quotas and validate capacity (approved plan, 2026-10-23)
- [x] Scan codebase
- [x] Select recipe
- [x] Plan architecture
- [x] **User approved this plan**

### Phase 2: Execution
- [x] Research components
- [x] Generate infrastructure files
- [x] Generate application configuration
- [x] Generate Dockerfiles
- [x] Update plan status to Ready for provisioning

### Phase 3: Validation
- [x] Local validation (`bicep build`, settings boot check, unit tests)
- [x] Record validation proof below
- [ ] Live `azd provision --preview` (requires an interactive Azure login; not run in this change)

### Phase 4: Deployment
- [ ] Operator runs `azd up` from a machine logged into Azure for Students
- [ ] Alembic migrate
- [ ] Set Vercel `NEXT_PUBLIC_API_URL`

---

## 7. Validation Proof

| Check | Command Run | Result | Timestamp |
|-------|-------------|--------|-----------|
| Bicep compile | `bicep build infra/main.bicep` (Bicep CLI 0.48.1) | Pass | 2026-10-23 |
| Boot unit tests | `pytest apps/api/tests/test_azure_boot.py apps/api/tests/test_auth_tokens.py --noconftest` | 8 passed | 2026-10-23 |
| Production settings import | `ENVIRONMENT=production` with `OPENROUTER_API_KEY` and Azure `sslmode=require` URL | URL rewritten to `ssl=require`; startup validation passed | 2026-10-23 |

**Validated by:** local checks in this change. Live `azd provision` is left for the operator after merge so the student subscription is not charged from this pull request.

---

## 8. Files to Generate

| File | Purpose | Status |
|------|---------|--------|
| `.azure/deployment-plan.md` | This plan | ✅ |
| `.azure/config.json` | azd default environment name | ⏳ |
| `azure.yaml` | AZD service map (API only) | ⏳ |
| `infra/main.bicep` | Subscription-scoped entry point | ⏳ |
| `infra/main.parameters.json` | azd parameter substitution, no secret values | ⏳ |
| `infra/modules/*.bicep` | Monitoring, ACR, Postgres, Key Vault, Container App, RBAC | ⏳ |
| `apps/api/Dockerfile` | Production image | ⏳ |
| `docs/azure-deploy.md` | Operator runbook | ⏳ |

---

## 9. Next Steps

> Current: Pull request ready for squash-merge. Operator provisions after merge.

1. Merge this branch to `main`.
2. On a machine logged into Azure for Students, follow `docs/azure-deploy.md` (`azd env new gradpilot`, set secrets, `azd up`).
3. Run Alembic inside the Container App and set Vercel `NEXT_PUBLIC_API_URL`.
