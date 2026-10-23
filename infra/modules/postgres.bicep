targetScope = 'resourceGroup'

@description('Flexible Server name. Lowercase letters, numbers, and hyphens.')
@minLength(3)
@maxLength(63)
param name string

param location string = resourceGroup().location

param tags object = {}

param administratorLogin string

@secure()
param administratorLoginPassword string

param databaseName string = 'gradpilot'

@description('true allows 0.0.0.0-255.255.255.255. false allows only other Azure services (0.0.0.0).')
param publicAccess bool = true

var postgresApiVersion = '2025-08-01'

resource server 'Microsoft.DBforPostgreSQL/flexibleServers@2025-08-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    administratorLogin: administratorLogin
    administratorLoginPassword: administratorLoginPassword
    authConfig: {
      activeDirectoryAuth: 'Disabled'
      passwordAuth: 'Enabled'
    }
    storage: {
      storageSizeGB: 32
      autoGrow: 'Disabled'
      type: 'Premium_LRS'
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    network: {
      publicNetworkAccess: 'Enabled'
    }
    createMode: 'Default'
  }
}

resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2025-08-01' = {
  parent: server
  name: databaseName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

resource firewall 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2025-08-01' = {
  parent: server
  name: 'ClientAccess'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: publicAccess ? '255.255.255.255' : '0.0.0.0'
  }
}

resource requireTls 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2025-08-01' = {
  parent: server
  name: 'require_secure_transport'
  properties: {
    value: 'ON'
    source: 'user-override'
  }
}

// Flexible Server uses the short login (not user@server). sslmode is for libpq/psycopg2.
// The API rewrites sslmode=require to asyncpg's ssl=require at startup.
var databaseUrl = 'postgresql://${administratorLogin}:${uriComponent(administratorLoginPassword)}@${server.properties.fullyQualifiedDomainName}:5432/${databaseName}?sslmode=require'

@secure()
output databaseUrl string = databaseUrl

output fqdn string = server.properties.fullyQualifiedDomainName
output name string = server.name
output databaseName string = database.name
output firewallRuleName string = firewall.name
output tlsConfigurationName string = requireTls.name
output apiVersion string = postgresApiVersion
