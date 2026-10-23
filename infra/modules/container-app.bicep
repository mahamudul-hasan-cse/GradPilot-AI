targetScope = 'resourceGroup'

param name string

param location string = resourceGroup().location

param tags object = {}

param environmentId string

param userAssignedIdentityId string

@description('PostgreSQL URL. Passed as a Container App secret value. Express environments reject keyVaultUrl references.')
@secure()
param databaseUrl string

@description('Application SECRET_KEY.')
@secure()
param secretKey string

@description('JWT signing secret.')
@secure()
param jwtSecret string

@description('OpenRouter API key.')
@secure()
param openRouterApiKey string

param corsOrigins string

param openRouterModel string

@secure()
param applicationInsightsConnectionString string

param minReplicas int = 0

param maxReplicas int = 1

@description('Placeholder so provision succeeds before azd deploy pushes the API image. azd deploy replaces it.')
param containerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

var targetPort = 8000

resource api 'Microsoft.App/containerApps@2025-01-01' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned, UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityId}': {}
    }
  }
  properties: {
    environmentId: environmentId
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: targetPort
        transport: 'auto'
        allowInsecure: false
      }
      // No registries block. azd deploy runs
      // `az containerapp registry set --identity system` and then updates the image.
      // Express Container Apps environments reject keyVaultUrl (ExpressEnvironmentFeatureNotSupported).
      // Values are still copied into Key Vault by the keyvault module for storage and rotation.
      secrets: [
        {
          name: 'database-url'
          value: databaseUrl
        }
        {
          name: 'secret-key'
          value: secretKey
        }
        {
          name: 'jwt-secret'
          value: jwtSecret
        }
        {
          name: 'openrouter-api-key'
          value: openRouterApiKey
        }
        {
          name: 'appinsights-connection-string'
          value: applicationInsightsConnectionString
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: containerImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'PORT'
              value: '${targetPort}'
            }
            {
              name: 'ENVIRONMENT'
              value: 'production'
            }
            {
              name: 'DEBUG'
              value: 'false'
            }
            {
              name: 'REDIS_ENABLED'
              value: 'false'
            }
            {
              name: 'LOG_LEVEL'
              value: 'INFO'
            }
            {
              name: 'CORS_ORIGINS'
              value: corsOrigins
            }
            {
              name: 'OPENROUTER_MODEL'
              value: openRouterModel
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              secretRef: 'appinsights-connection-string'
            }
            {
              name: 'DATABASE_URL'
              secretRef: 'database-url'
            }
            {
              name: 'SECRET_KEY'
              secretRef: 'secret-key'
            }
            {
              name: 'JWT_SECRET'
              secretRef: 'jwt-secret'
            }
            {
              name: 'OPENROUTER_API_KEY'
              secretRef: 'openrouter-api-key'
            }
          ]
          probes: [
            {
              type: 'Startup'
              httpGet: {
                path: '/health'
                port: targetPort
                scheme: 'HTTP'
              }
              initialDelaySeconds: 1
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 10
            }
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: targetPort
                scheme: 'HTTP'
              }
              initialDelaySeconds: 5
              periodSeconds: 30
              timeoutSeconds: 5
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health/ready'
                port: targetPort
                scheme: 'HTTP'
              }
              initialDelaySeconds: 5
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

output name string = api.name
output uri string = 'https://${api.properties.configuration.ingress.fqdn}'
output systemAssignedPrincipalId string = api.identity.principalId
output fqdn string = api.properties.configuration.ingress.fqdn
