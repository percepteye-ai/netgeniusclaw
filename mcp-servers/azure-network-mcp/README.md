# Azure Network MCP Server

A Python-based MCP (Model Context Protocol) server for Microsoft Azure networking services. Provides read-only access to Azure VNet topology, NSG rules and compliance auditing, ExpressRoute/VPN Gateway health, Azure Firewall policies, Load Balancer/Application Gateway health, Route Tables, Network Watcher, Private Link, and DNS.

## Transport

**stdio** -- invoked by OpenClaw gateway or Claude Code.

## Requirements

- Python 3.10+
- Azure subscription with a service principal (App Registration)
- Service principal granted **Reader** role on target subscription(s)

## Installation

```bash
cd mcp-servers/azure-network-mcp
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Azure credentials
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_TENANT_ID` | Yes | Azure AD tenant ID |
| `AZURE_CLIENT_ID` | Yes | Service principal client ID |
| `AZURE_CLIENT_SECRET` | Yes | Service principal client secret |
| `AZURE_SUBSCRIPTION_ID` | Yes | Default subscription ID |

If service principal env vars are not set, the server falls back to `DefaultAzureCredential` (managed identity, Azure CLI, etc.).

## Required Azure RBAC Permissions

Minimum: **Reader** role on target subscription(s).

The service principal needs read access to:
- Microsoft.Network/* (VNets, NSGs, LBs, Firewalls, etc.)
- Microsoft.Resources/subscriptions/read
- Microsoft.Network/networkWatchers/* (for Network Watcher tools)

## Tool Inventory (19 tools)

### VNet Tools (3)

| Tool | Description | Parameters |
|------|-------------|------------|
| `azure_list_vnets` | List all VNets in a subscription | `subscription_id?` |
| `azure_get_vnet_details` | Get full VNet config (subnets, peerings, DNS) | `vnet_name?`, `resource_group?`, `resource_id?`, `subscription_id?` |
| `azure_get_vnet_peerings` | Get VNet peering status | `vnet_name`, `resource_group`, `subscription_id?` |

### NSG Tools (3)

| Tool | Description | Parameters |
|------|-------------|------------|
| `azure_list_nsgs` | List all NSGs with orphan detection | `subscription_id?` |
| `azure_get_nsg_rules` | Get NSG rules sorted by priority | `nsg_name`, `resource_group`, `subscription_id?` |
| `azure_get_effective_security_rules` | Effective rules for a NIC | `nic_name`, `resource_group`, `subscription_id?` |

### Compliance (1)

| Tool | Description | Parameters |
|------|-------------|------------|
| `azure_audit_nsg_compliance` | CIS Azure Foundations audit | `nsg_name?`, `resource_group?`, `subscription_id?` |

### ExpressRoute (2)

| Tool | Description | Parameters |
|------|-------------|------------|
| `azure_get_expressroute_status` | Circuit status and peerings | `circuit_name?`, `resource_group?`, `subscription_id?` |
| `azure_get_expressroute_routes` | Route table for a peering | `circuit_name`, `resource_group`, `peering_name`, `subscription_id?` |

### VPN Gateway (1)

| Tool | Description | Parameters |
|------|-------------|------------|
| `azure_get_vpn_gateway_status` | Gateway config and connections | `gateway_name?`, `resource_group?`, `subscription_id?` |

### Firewall (2)

| Tool | Description | Parameters |
|------|-------------|------------|
| `azure_list_firewalls` | List Azure Firewalls | `subscription_id?` |
| `azure_get_firewall_policy` | Policy with rule collections | `policy_name`, `resource_group`, `subscription_id?` |

### Load Balancer (2)

| Tool | Description | Parameters |
|------|-------------|------------|
| `azure_list_load_balancers` | List LBs with frontend/backend summary | `subscription_id?` |
| `azure_get_lb_backend_health` | Backend pool health status | `lb_name`, `resource_group`, `subscription_id?` |

### Application Gateway / Front Door (1)

| Tool | Description | Parameters |
|------|-------------|------------|
| `azure_get_app_gateway_health` | App GW config, WAF, backend health + Front Door | `gateway_name?`, `resource_group?`, `subscription_id?` |

### Supporting Services (4)

| Tool | Description | Parameters |
|------|-------------|------------|
| `azure_get_route_tables` | Route tables, UDRs, effective routes | `route_table_name?`, `resource_group?`, `nic_name?`, `subscription_id?` |
| `azure_get_network_watcher_status` | Network Watcher, connection monitors, flow logs | `resource_group?`, `subscription_id?` |
| `azure_get_private_endpoints` | Private Endpoints with DNS zone associations | `resource_group?`, `subscription_id?` |
| `azure_get_dns_zones` | DNS zones and record sets | `zone_name?`, `zone_type?`, `subscription_id?` |

### Subscription (1)

| Tool | Description | Parameters |
|------|-------------|------------|
| `azure_list_subscriptions` | List all accessible subscriptions | (none) |

## Architecture

```
azure_network_mcp_server.py   (FastMCP entry point, GAIT logging, tool registration)
  |
  +-- clients/azure_client.py  (Azure SDK client factory, credential mgmt)
  +-- tools/
  |     +-- vnet.py            (VNet, Subnet, Peering)
  |     +-- nsg.py             (NSG rules, effective rules, compliance)
  |     +-- expressroute.py    (ExpressRoute circuits, routes)
  |     +-- vpn_gateway.py     (VPN Gateways, connections)
  |     +-- firewall.py        (Azure Firewall, policies)
  |     +-- load_balancer.py   (Load Balancers, backend health)
  |     +-- app_gateway.py     (Application Gateway, Front Door)
  |     +-- route_table.py     (Route Tables, effective routes)
  |     +-- network_watcher.py (Network Watcher, flow logs)
  |     +-- private_link.py    (Private Endpoints)
  |     +-- dns.py             (DNS zones, records)
  +-- models/responses.py      (Dataclass response models)
  +-- compliance/cis_azure.py  (CIS benchmark rules)
  +-- utils/
        +-- constants.py       (API versions, error codes)
        +-- pagination.py      (Azure SDK pagination helper)
        +-- rate_limiter.py    (Error translation, retry config)
```

## Multi-Subscription Support

All tools accept an optional `subscription_id` parameter. If omitted, the default `AZURE_SUBSCRIPTION_ID` is used. Use `azure_list_subscriptions` to discover available subscriptions.

## Read-Only by Default

All operations are read-only (GET/List). No create, modify, or delete operations are exposed. Write operations would require ITSM Change Request approval per NetGeniusClaw constitution.
