# MCP Tool Contracts: Azure Networking MCP Server

**Feature**: 004-azure-network-mcp | **Date**: 2026-03-26
**Transport**: stdio | **Protocol**: MCP JSON-RPC

## Tool Inventory (18 tools)

### VNet Tools (3)

#### `azure_list_vnets`

List all Virtual Networks in a subscription.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription_id | string | No | Target subscription ID (defaults to AZURE_SUBSCRIPTION_ID) |

**Returns**: JSON array of VNet objects (name, id, resource_group, location, address_space, subnet_count, peering_count, provisioning_state, tags).

**Errors**: AuthenticationError, AuthorizationError, SubscriptionNotFoundError.

---

#### `azure_get_vnet_details`

Get detailed VNet configuration including subnets, peerings, and DNS settings.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| vnet_name | string | Yes* | VNet name (required if resource_id not provided) |
| resource_group | string | Yes* | Resource group (required if resource_id not provided) |
| resource_id | string | Yes* | Full Azure resource ID (alternative to name+RG) |
| subscription_id | string | No | Target subscription ID |

**Returns**: Full VNet object with all subnets (including NSG and route table associations), peerings (with status), and DNS settings.

**Errors**: ResourceNotFoundError, AuthenticationError, AuthorizationError.

---

#### `azure_get_vnet_peerings`

Get VNet peering status for a specific VNet.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| vnet_name | string | Yes | VNet name |
| resource_group | string | Yes | Resource group name |
| subscription_id | string | No | Target subscription ID |

**Returns**: JSON array of VNetPeering objects with peering state and traffic forwarding settings.

---

### NSG Tools (3)

#### `azure_list_nsgs`

List all Network Security Groups in a subscription.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription_id | string | No | Target subscription ID |

**Returns**: JSON array of NSG objects with association info and orphaned status.

---

#### `azure_get_nsg_rules`

Get all rules for a specific NSG.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| nsg_name | string | Yes | NSG name |
| resource_group | string | Yes | Resource group name |
| subscription_id | string | No | Target subscription ID |

**Returns**: JSON object with sorted inbound and outbound rules (custom + default).

---

#### `azure_get_effective_security_rules`

Get effective (aggregated) security rules for a network interface.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| nic_name | string | Yes | Network interface name |
| resource_group | string | Yes | Resource group name |
| subscription_id | string | No | Target subscription ID |

**Returns**: Aggregated effective security rules from all applicable NSGs.

---

### Compliance Tool (1)

#### `azure_audit_nsg_compliance`

Audit NSG rules against CIS Azure Foundations Benchmark.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| nsg_name | string | No | Specific NSG to audit (omit for all NSGs) |
| resource_group | string | No | Resource group filter |
| subscription_id | string | No | Target subscription ID |

**Returns**: JSON array of ComplianceFinding objects with severity, description, and remediation.

---

### ExpressRoute Tools (2)

#### `azure_get_expressroute_status`

Get ExpressRoute circuit status and peering details.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| circuit_name | string | No | Specific circuit (omit for all circuits) |
| resource_group | string | No | Resource group filter |
| subscription_id | string | No | Target subscription ID |

**Returns**: JSON array of ExpressRouteCircuit objects with peering configuration.

---

#### `azure_get_expressroute_routes`

Get route table for an ExpressRoute peering.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| circuit_name | string | Yes | Circuit name |
| resource_group | string | Yes | Resource group name |
| peering_name | string | Yes | Peering type (AzurePrivatePeering/MicrosoftPeering) |
| subscription_id | string | No | Target subscription ID |

**Returns**: JSON array of learned routes (prefix, next_hop, as_path, origin).

---

### VPN Gateway Tools (1)

#### `azure_get_vpn_gateway_status`

Get VPN Gateway configuration and connection status.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| gateway_name | string | No | Specific gateway (omit for all gateways) |
| resource_group | string | No | Resource group filter |
| subscription_id | string | No | Target subscription ID |

**Returns**: JSON array of VPNGateway objects with connection status and BGP settings.

---

### Firewall Tools (2)

#### `azure_list_firewalls`

List Azure Firewalls and associated policies.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription_id | string | No | Target subscription ID |

**Returns**: JSON array of AzureFirewall objects with SKU and policy association.

---

#### `azure_get_firewall_policy`

Get firewall policy details including rule collections and threat intelligence.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| policy_name | string | Yes | Firewall policy name |
| resource_group | string | Yes | Resource group name |
| subscription_id | string | No | Target subscription ID |

**Returns**: FirewallPolicy object with rule collection groups and threat intel config.

---

### Load Balancer Tools (2)

#### `azure_list_load_balancers`

List Load Balancers with frontend IP and backend pool summary.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription_id | string | No | Target subscription ID |

**Returns**: JSON array of LoadBalancer objects.

---

#### `azure_get_lb_backend_health`

Get backend pool health status for a Load Balancer.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| lb_name | string | Yes | Load Balancer name |
| resource_group | string | Yes | Resource group name |
| subscription_id | string | No | Target subscription ID |

**Returns**: Backend pool health with per-member status (Healthy/Unhealthy/Unknown).

---

### Application Gateway / Front Door Tool (1)

#### `azure_get_app_gateway_health`

Get Application Gateway or Front Door configuration and backend health.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| gateway_name | string | No | Specific gateway (omit for all) |
| resource_group | string | No | Resource group filter |
| subscription_id | string | No | Target subscription ID |

**Returns**: Application Gateway/Front Door config with WAF status and backend health.

---

### Route Table Tool (1)

#### `azure_get_route_tables`

Get route tables and effective routes.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| route_table_name | string | No | Specific route table (omit for all) |
| resource_group | string | No | Resource group filter |
| nic_name | string | No | NIC name for effective routes |
| subscription_id | string | No | Target subscription ID |

**Returns**: Route table configuration with UDRs and subnet associations.

---

### Private Link Tool (1)

#### `azure_get_private_endpoints`

Get Private Endpoint and Private Link configurations.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| resource_group | string | No | Resource group filter |
| subscription_id | string | No | Target subscription ID |

**Returns**: JSON array of PrivateEndpoint objects with DNS zone associations.

---

### DNS Tool (1)

#### `azure_get_dns_zones`

Get Azure DNS zone configuration and record sets.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| zone_name | string | No | Specific zone (omit for all zones) |
| zone_type | string | No | Filter by Public/Private |
| subscription_id | string | No | Target subscription ID |

**Returns**: JSON array of DnsZone objects with record sets.

---

## Common Error Responses

All tools return errors in the following format:

```json
{
  "error": {
    "code": "AuthenticationError",
    "message": "Failed to authenticate. Verify AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET environment variables are set correctly.",
    "details": "ClientAuthenticationError: ..."
  }
}
```

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| AuthenticationError | 401 | Invalid or expired credentials |
| AuthorizationError | 403 | Service principal lacks required permissions |
| SubscriptionNotFoundError | 404 | Subscription ID not found or not accessible |
| ResourceNotFoundError | 404 | Specified resource does not exist |
| ThrottlingError | 429 | ARM API rate limit exceeded (auto-retry) |
| ValidationError | 400 | Invalid parameter (e.g., malformed resource ID) |
| NetworkWatcherUnavailable | 404 | Network Watcher not enabled in target region |
