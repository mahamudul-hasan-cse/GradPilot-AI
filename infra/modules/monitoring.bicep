targetScope = 'resourceGroup'

@description('Short name token. The module appends resource abbreviations.')
param name string

param location string = resourceGroup().location

param tags object = {}

var workspaceName = 'log-${name}'
var appInsightsName = 'appi-${name}'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: workspaceName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    workspaceCapping: {
      dailyQuotaGb: json('0.1')
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  tags: tags
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
  }
}

output logAnalyticsWorkspaceId string = logAnalytics.id
output logAnalyticsCustomerId string = logAnalytics.properties.customerId

@secure()
output logAnalyticsSharedKey string = logAnalytics.listKeys().primarySharedKey

@secure()
output appInsightsConnectionString string = appInsights.properties.ConnectionString
