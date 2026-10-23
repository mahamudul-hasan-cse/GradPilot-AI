targetScope = 'subscription'

@description('azd environment name. Used for tags and globally unique resource suffixes.')
@minLength(1)
@maxLength(32)
param environmentName string

@description('Azure region for all resources. Approved default is centralindia.')
param location string = 'centralindia'

@description('Resource group. Approved name is rg-gradpilot.')
param resourceGroupName string = 'rg-gradpilot'

@description('PostgreSQL administrator login. Cannot be changed after the server is created.')
param postgresAdminLogin string = 'gradpilot'

@description('PostgreSQL administrator password. Set with azd env set POSTGRES_ADMIN_PASSWORD --secret. Not stored in git.')
@secure()
@minLength(8)
@maxLength(128)
param postgresAdminPassword string

@description('Application SECRET_KEY. At least 32 characters. Set with azd env set SECRET_KEY --secret.')
@secure()
@minLength(32)
param secretKey string

@description('JWT signing secret. At least 32 characters. Set with azd env set JWT_SECRET --secret.')
@secure()
@minLength(32)
param jwtSecret string

@description('OpenRouter API key. Set with azd env set OPENROUTER_API_KEY --secret.')
@secure()
@minLength(1)
param openRouterApiKey string

@description('OpenRouter model id. Override with azd env set OPENROUTER_MODEL.')
param openRouterModel string = 'openai/gpt-4o-mini'

@description('Comma-separated browser origins. Must include the Vercel app and local dev.')
param corsOrigins string = 'https://gradpilot-ai.vercel.app'

@description('When true, Postgres accepts any client IP over TLS. Container Apps Consumption has no stable egress IP. Set false to allow only the Azure services firewall rule.')
param postgresPublicAccess bool = true

@description('Container Apps min replicas. 0 scales to zero while idle.')
@minValue(0)
@maxValue(2)
param apiMinReplicas int = 0

@description('Container Apps max replicas.')
@minValue(1)
@maxValue(4)
param apiMaxReplicas int = 1

@description('Entra object id granted Key Vault Secrets Officer so this deployment can write secrets. Defaults to the principal running the deployment.')
param keyVaultOfficerPrincipalId string = deployer().objectId

@description('User for an interactive azd login. Set ServicePrincipal for a pipeline identity.')
@allowed([
  'User'
  'ServicePrincipal'
])
param keyVaultOfficerPrincipalType string = 'User'

var resourceSuffix = take(uniqueString(subscription().id, environmentName, location), 6)
var tags = {
  'azd-env-name': environmentName
  project: 'gradpilot'
}

resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    name: 'gp-${resourceSuffix}'
    location: location
    tags: tags
  }
}

module registry 'modules/registry.bicep' = {
  name: 'registry'
  scope: rg
  params: {
    name: 'crgp${resourceSuffix}'
    location: location
    tags: tags
  }
}

module identity 'modules/identity.bicep' = {
  name: 'identity'
  scope: rg
  params: {
    name: 'id-gp-api-${resourceSuffix}'
    location: location
    tags: tags
  }
}

module postgres 'modules/postgres.bicep' = {
  name: 'postgres'
  scope: rg
  params: {
    name: 'psql-gp-${resourceSuffix}'
    location: location
    tags: tags
    administratorLogin: postgresAdminLogin
    administratorLoginPassword: postgresAdminPassword
    databaseName: 'gradpilot'
    publicAccess: postgresPublicAccess
  }
}

module keyVault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  scope: rg
  params: {
    name: 'kv-gp-${resourceSuffix}'
    location: location
    tags: tags
    officerPrincipalId: keyVaultOfficerPrincipalId
    officerPrincipalType: keyVaultOfficerPrincipalType
    databaseUrl: postgres.outputs.databaseUrl
    secretKey: secretKey
    jwtSecret: jwtSecret
    openRouterApiKey: openRouterApiKey
  }
}

module keyVaultSecretsUser 'modules/kv-secrets-user.bicep' = {
  name: 'kv-secrets-user'
  scope: rg
  params: {
    vaultName: keyVault.outputs.name
    principalId: identity.outputs.principalId
  }
}

module acrPullUser 'modules/acr-pull.bicep' = {
  name: 'acr-pull-user'
  scope: rg
  params: {
    acrName: registry.outputs.name
    principalId: identity.outputs.principalId
  }
}

module containerAppsEnvironment 'modules/container-apps-env.bicep' = {
  name: 'container-apps-env'
  scope: rg
  params: {
    name: 'cae-gp-${resourceSuffix}'
    location: location
    tags: tags
    logAnalyticsCustomerId: monitoring.outputs.logAnalyticsCustomerId
    logAnalyticsSharedKey: monitoring.outputs.logAnalyticsSharedKey
  }
}

module api 'modules/container-app.bicep' = {
  name: 'api'
  scope: rg
  params: {
    name: 'ca-gp-api-${resourceSuffix}'
    location: location
    tags: union(tags, { 'azd-service-name': 'api' })
    environmentId: containerAppsEnvironment.outputs.id
    userAssignedIdentityId: identity.outputs.id
    keyVaultUri: keyVault.outputs.uri
    corsOrigins: corsOrigins
    openRouterModel: openRouterModel
    applicationInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    minReplicas: apiMinReplicas
    maxReplicas: apiMaxReplicas
  }
  dependsOn: [
    keyVaultSecretsUser
  ]
}

module acrPullSystem 'modules/acr-pull.bicep' = {
  name: 'acr-pull-system'
  scope: rg
  params: {
    acrName: registry.outputs.name
    principalId: api.outputs.systemAssignedPrincipalId
  }
}

output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_LOCATION string = location
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = registry.outputs.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = registry.outputs.name
output AZURE_KEY_VAULT_NAME string = keyVault.outputs.name
output AZURE_KEY_VAULT_URI string = keyVault.outputs.uri
output AZURE_LOG_ANALYTICS_WORKSPACE_ID string = monitoring.outputs.logAnalyticsWorkspaceId
output AZURE_CONTAINER_APP_NAME string = api.outputs.name
output AZURE_POSTGRES_FQDN string = postgres.outputs.fqdn
output API_URL string = api.outputs.uri
output AZURE_CONTAINER_APPS_ENVIRONMENT_NAME string = containerAppsEnvironment.outputs.name
output AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID string = identity.outputs.clientId
