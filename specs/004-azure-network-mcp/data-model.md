# Data Model: Azure Networking MCP Server

**Feature**: 004-azure-network-mcp | **Date**: 2026-03-26

## Entities

### AzureCredentialConfig

Configuration for Azure authentication.

| Field | Type | Description |
|-------|------|-------------|
| tenant_id | str | Azure AD tenant ID (from AZURE_TENANT_ID) |
| client_id | str | Service principal client ID (from AZURE_CLIENT_ID) |
| client_secret | str | Service principal client secret (from AZURE_CLIENT_SECRET) |
| default_subscription_id | str | Default subscription (from AZURE_SUBSCRIPTION_ID) |

**Validation**: All fields required unless using DefaultAzureCredential fallback (managed identity, Azure CLI).

### VNet

Azure Virtual Network resource.

| Field | Type | Description |
|-------|------|-------------|
| name | str | VNet name |
| id | str | Azure resource ID |
| resource_group | str | Resource group name |
| location | str | Azure region |
| address_space | list[str] | CIDR address prefixes |
| subnets | list[Subnet] | Associated subnets |
| peerings | list[VNetPeering] | VNet peering connections |
| dns_servers | list[str] | Custom DNS servers (empty = Azure-provided) |
| provisioning_state | str | Succeeded/Updating/Deleting/Failed |
| tags | dict[str, str] | Azure resource tags |

### Subnet

Subnet within a VNet.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Subnet name |
| id | str | Azure resource ID |
| address_prefix | str | CIDR prefix |
| nsg_id | str | null | Associated NSG resource ID |
| nsg_name | str | null | Associated NSG name (for convenience) |
| route_table_id | str | null | Associated route table resource ID |
| route_table_name | str | null | Associated route table name |
| delegations | list[str] | Service delegations (e.g., Microsoft.Sql/managedInstances) |
| service_endpoints | list[str] | Enabled service endpoints |
| private_endpoints | list[str] | Private endpoint resource IDs |
| provisioning_state | str | Provisioning state |

### VNetPeering

VNet peering connection.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Peering name |
| id | str | Azure resource ID |
| remote_vnet_id | str | Remote VNet resource ID |
| peering_state | str | Connected/Disconnected/Initiated |
| allow_vnet_access | bool | Allow traffic to/from remote VNet |
| allow_forwarded_traffic | bool | Allow forwarded traffic |
| allow_gateway_transit | bool | Allow gateway transit |
| use_remote_gateways | bool | Use remote VNet's gateway |

### NetworkSecurityGroup

NSG resource.

| Field | Type | Description |
|-------|------|-------------|
| name | str | NSG name |
| id | str | Azure resource ID |
| resource_group | str | Resource group name |
| location | str | Azure region |
| security_rules | list[SecurityRule] | Custom security rules |
| default_rules | list[SecurityRule] | Default security rules |
| associated_subnets | list[str] | Subnet resource IDs |
| associated_nics | list[str] | NIC resource IDs |
| is_orphaned | bool | True if not associated with any subnet or NIC |
| tags | dict[str, str] | Azure resource tags |

### SecurityRule

Individual NSG rule.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Rule name |
| priority | int | Rule priority (100-4096) |
| direction | str | Inbound/Outbound |
| access | str | Allow/Deny |
| protocol | str | TCP/UDP/ICMP/*/Ah/Esp |
| source_address_prefix | str | Source CIDR or tag |
| source_address_prefixes | list[str] | Multiple source addresses |
| source_port_range | str | Source port range |
| destination_address_prefix | str | Destination CIDR or tag |
| destination_address_prefixes | list[str] | Multiple destination addresses |
| destination_port_range | str | Destination port range |
| description | str | null | Rule description |

### ComplianceFinding

Result of a CIS benchmark compliance check.

| Field | Type | Description |
|-------|------|-------------|
| rule_id | str | CIS benchmark rule ID (e.g., "6.1") |
| rule_name | str | Human-readable rule name |
| severity | str | Critical/High/Medium/Low |
| resource_id | str | Affected resource ID |
| resource_name | str | Affected resource name |
| description | str | What the finding means |
| remediation | str | How to fix it |
| nsg_rule_name | str | null | Offending rule name if applicable |

### ExpressRouteCircuit

ExpressRoute circuit resource.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Circuit name |
| id | str | Azure resource ID |
| resource_group | str | Resource group name |
| location | str | Azure region |
| sku_name | str | SKU name (Standard/Premium) |
| sku_tier | str | SKU tier |
| sku_family | str | MeteredData/UnlimitedData |
| bandwidth_in_mbps | int | Provisioned bandwidth |
| peering_location | str | Peering facility location |
| service_provider_name | str | Connectivity provider name |
| provisioning_state | str | Provisioning state |
| circuit_provisioning_state | str | Enabled/Disabled |
| peerings | list[ExpressRoutePeering] | Configured peerings |

### ExpressRoutePeering

ExpressRoute peering configuration.

| Field | Type | Description |
|-------|------|-------------|
| name | str | AzurePrivatePeering/AzurePublicPeering/MicrosoftPeering |
| peering_type | str | Peering type |
| state | str | Enabled/Disabled |
| primary_peer_address_prefix | str | Primary /30 subnet |
| secondary_peer_address_prefix | str | Secondary /30 subnet |
| vlan_id | int | VLAN ID |
| azure_asn | int | Azure BGP ASN |
| peer_asn | int | Customer BGP ASN |

### VPNGateway

VPN Gateway resource.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Gateway name |
| id | str | Azure resource ID |
| resource_group | str | Resource group name |
| location | str | Azure region |
| sku | str | Gateway SKU (VpnGw1/VpnGw2/etc.) |
| gateway_type | str | Vpn/ExpressRoute |
| vpn_type | str | RouteBased/PolicyBased |
| active_active | bool | Active-active configuration |
| bgp_settings | dict | null | BGP configuration |
| connections | list[VPNConnection] | Gateway connections |
| provisioning_state | str | Provisioning state |

### VPNConnection

VPN Gateway connection.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Connection name |
| id | str | Azure resource ID |
| connection_type | str | IPsec/Vnet2Vnet/ExpressRoute |
| connection_status | str | Connected/Connecting/NotConnected/Unknown |
| routing_weight | int | Route weight |
| shared_key_set | bool | Whether shared key is configured (never expose the key) |
| egress_bytes_transferred | int | Bytes sent |
| ingress_bytes_transferred | int | Bytes received |

### AzureFirewall

Azure Firewall resource.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Firewall name |
| id | str | Azure resource ID |
| resource_group | str | Resource group name |
| location | str | Azure region |
| sku_tier | str | Standard/Premium |
| provisioning_state | str | Provisioning state |
| firewall_policy_id | str | null | Associated policy resource ID |
| threat_intel_mode | str | Off/Alert/Deny |
| ip_configurations | list[dict] | IP configurations |

### FirewallPolicy

Azure Firewall Policy resource.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Policy name |
| id | str | Azure resource ID |
| threat_intelligence_mode | str | Off/Alert/Deny |
| dns_proxy_enabled | bool | DNS proxy status |
| intrusion_detection_mode | str | null | Off/Alert/Deny (Premium only) |
| rule_collection_groups | list[RuleCollectionGroup] | Associated rule collection groups |

### RuleCollectionGroup

Firewall policy rule collection group.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Group name |
| priority | int | Group priority |
| rule_collections | list[RuleCollection] | Rule collections in group |

### RuleCollection

Firewall rule collection.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Collection name |
| priority | int | Collection priority |
| action_type | str | Allow/Deny |
| rule_type | str | Network/Application/NAT |
| rules | list[dict] | Individual rules (schema varies by type) |

### LoadBalancer

Azure Load Balancer resource.

| Field | Type | Description |
|-------|------|-------------|
| name | str | LB name |
| id | str | Azure resource ID |
| resource_group | str | Resource group name |
| location | str | Azure region |
| sku | str | Basic/Standard/Gateway |
| type | str | Public/Internal |
| frontend_ip_configs | list[dict] | Frontend IP configurations |
| backend_pools | list[BackendPool] | Backend address pools |
| health_probes | list[HealthProbe] | Health probes |
| load_balancing_rules | list[dict] | Load balancing rules |
| nat_rules | list[dict] | Inbound NAT rules |
| provisioning_state | str | Provisioning state |

### BackendPool

Load balancer backend pool.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Pool name |
| id | str | Azure resource ID |
| members | list[dict] | Backend pool members (VM/NIC references) |
| health_status | list[dict] | Per-member health status |

### HealthProbe

Load balancer health probe.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Probe name |
| protocol | str | TCP/HTTP/HTTPS |
| port | int | Probe port |
| request_path | str | null | HTTP path (for HTTP/HTTPS probes) |
| interval_in_seconds | int | Probe interval |
| number_of_probes | int | Unhealthy threshold |

### RouteTable

Azure Route Table resource.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Route table name |
| id | str | Azure resource ID |
| resource_group | str | Resource group name |
| location | str | Azure region |
| routes | list[Route] | User-defined routes |
| associated_subnets | list[str] | Subnet resource IDs |
| disable_bgp_route_propagation | bool | Whether BGP routes are suppressed |

### Route

User-defined route.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Route name |
| address_prefix | str | Destination CIDR |
| next_hop_type | str | VirtualNetworkGateway/VnetLocal/Internet/VirtualAppliance/None |
| next_hop_ip | str | null | Next hop IP (for VirtualAppliance) |

### PrivateEndpoint

Azure Private Endpoint resource.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Endpoint name |
| id | str | Azure resource ID |
| resource_group | str | Resource group name |
| location | str | Azure region |
| subnet_id | str | Subnet resource ID |
| private_ip | str | Private IP address |
| service_connection | dict | Private link service connection details |
| private_dns_zones | list[str] | Associated private DNS zone IDs |
| provisioning_state | str | Provisioning state |

### DnsZone

Azure DNS zone resource.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Zone name (e.g., contoso.com) |
| id | str | Azure resource ID |
| resource_group | str | Resource group name |
| zone_type | str | Public/Private |
| record_count | int | Number of record sets |
| name_servers | list[str] | Assigned name servers (public zones) |
| linked_vnets | list[str] | Linked VNet IDs (private zones) |

### DnsRecordSet

DNS record set.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Record name |
| type | str | A/AAAA/CNAME/MX/NS/PTR/SOA/SRV/TXT |
| ttl | int | Time-to-live in seconds |
| records | list[str] | Record values |

## State Transitions

### Resource Provisioning States

All Azure resources follow the same provisioning lifecycle:

```
Creating -> Succeeded
Creating -> Failed
Succeeded -> Updating -> Succeeded
Succeeded -> Updating -> Failed
Succeeded -> Deleting -> (removed)
```

The MCP server reports the current provisioning state as-is without treating transitional states as errors.

### VNet Peering States

```
Initiated -> Connected (when both sides configured)
Connected -> Disconnected (when remote side removed)
Disconnected -> Connected (when re-established)
```

### VPN Connection States

```
Connecting -> Connected
Connected -> NotConnected (tunnel down)
NotConnected -> Connecting (reconnect attempt)
Unknown (when status cannot be determined)
```

## Relationships

```
Subscription (1) --> (*) VNet
VNet (1) --> (*) Subnet
VNet (1) --> (*) VNetPeering
Subnet (*) --> (0..1) NSG
Subnet (*) --> (0..1) RouteTable
Subnet (1) --> (*) PrivateEndpoint
NSG (1) --> (*) SecurityRule
RouteTable (1) --> (*) Route
Subscription (1) --> (*) ExpressRouteCircuit
ExpressRouteCircuit (1) --> (*) ExpressRoutePeering
Subscription (1) --> (*) VPNGateway
VPNGateway (1) --> (*) VPNConnection
Subscription (1) --> (*) AzureFirewall
AzureFirewall (*) --> (0..1) FirewallPolicy
FirewallPolicy (1) --> (*) RuleCollectionGroup
RuleCollectionGroup (1) --> (*) RuleCollection
Subscription (1) --> (*) LoadBalancer
LoadBalancer (1) --> (*) BackendPool
LoadBalancer (1) --> (*) HealthProbe
Subscription (1) --> (*) DnsZone
DnsZone (1) --> (*) DnsRecordSet
```
