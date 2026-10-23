targetScope = 'resourceGroup'

@description('Key Vault name. 3-24 characters, globally unique.')
@minLength(3)
@maxLength(24)
param name string

param location string = resourceGroup().location

param tags object = {}

@description('Principal allowed to create and update Key Vault secrets during deployment.')
param officerPrincipalId string

@description('User for an interactive azd login. ServicePrincipal when a pipeline identity deploys.')
@allowed([
  'User'
  'ServicePrincipal'
])
param officerPrincipalType string = 'User'

@secure()
param databaseUrl string

@secure()
param secretKey string

@secure()
param jwtSecret string

@secure()
param openRouterApiKey string

var secretsOfficerRoleId = 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7'

resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

resource secretsOfficer 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(vault.id, officerPrincipalId, secretsOfficerRoleId)
  scope: vault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', secretsOfficerRoleId)
    principalId: officerPrincipalId
    principalType: officerPrincipalType
  }
}

resource databaseUrlSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: 'database-url'
  properties: {
    value: databaseUrl
  }
  dependsOn: [
    secretsOfficer
  ]
}

resource secretKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: 'secret-key'
  properties: {
    value: secretKey
  }
  dependsOn: [
    secretsOfficer
  ]
}

resource jwtSecretSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: 'jwt-secret'
  properties: {
    value: jwtSecret
  }
  dependsOn: [
    secretsOfficer
  ]
}

resource openRouterSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: 'openrouter-api-key'
  properties: {
    value: openRouterApiKey
  }
  dependsOn: [
    secretsOfficer
  ]
}

output name string = vault.name
output uri string = vault.properties.vaultUri
output id string = vault.id
output databaseUrlSecretName string = databaseUrlSecret.name
output secretKeySecretName string = secretKeySecret.name
output jwtSecretSecretName string = jwtSecretSecret.name
output openRouterSecretName string = openRouterSecret.name
