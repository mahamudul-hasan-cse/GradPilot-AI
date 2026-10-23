targetScope = 'resourceGroup'

@description('ACR name. Alphanumeric only, 5-50 characters.')
@minLength(5)
@maxLength(50)
param name string

param location string = resourceGroup().location

param tags object = {}

resource registry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

output name string = registry.name
output loginServer string = registry.properties.loginServer
output id string = registry.id
