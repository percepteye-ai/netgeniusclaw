# MCP Tool Contracts: DevNet Content Search

**Feature**: 026-devnet-content-search-mcp
**Date**: 2026-04-09
**MCP Server**: devnet-content-search
**Endpoint**: https://devnet.cisco.com/v1/foundation-search-mcp/mcp

## Tools Overview

| Tool ID | Type | Description |
|---------|------|-------------|
| Meraki-API-Doc-Search | Read | Search Meraki API documentation |
| CatalystCenter-API-Doc-Search | Read | Search Catalyst Center API documentation |
| Meraki-API-OperationId-Search | Read | Lookup specific Meraki operation by ID |

---

## Tool: Meraki-API-Doc-Search

**Purpose**: Search Meraki API documentation with keyword queries

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search terms for finding Meraki API documentation"
    },
    "limit": {
      "type": "integer",
      "description": "Maximum number of results to return (optional)",
      "minimum": 1,
      "maximum": 50
    }
  },
  "required": ["query"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "operationId": { "type": "string" },
          "path": { "type": "string" },
          "method": { "type": "string" },
          "summary": { "type": "string" },
          "description": { "type": "string" },
          "tags": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "count": { "type": "integer" }
  }
}
```

### Example Usage

**Request**:
```json
{
  "query": "L3 firewall rules",
  "limit": 5
}
```

**Response**:
```json
{
  "results": [
    {
      "operationId": "updateNetworkApplianceFirewallL3FirewallRules",
      "path": "/networks/{networkId}/appliance/firewall/l3FirewallRules",
      "method": "PUT",
      "summary": "Update the L3 firewall rules of an MX network",
      "description": "Update the L3 firewall rules of an MX network...",
      "tags": ["appliance", "configure", "firewall"]
    },
    {
      "operationId": "getNetworkApplianceFirewallL3FirewallRules",
      "path": "/networks/{networkId}/appliance/firewall/l3FirewallRules",
      "method": "GET",
      "summary": "Return the L3 firewall rules for an MX network",
      "description": "Return the L3 firewall rules for an MX network...",
      "tags": ["appliance", "configure", "firewall"]
    }
  ],
  "count": 2
}
```

---

## Tool: CatalystCenter-API-Doc-Search

**Purpose**: Search Catalyst Center (DNA Center) API documentation

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search terms for finding Catalyst Center API documentation"
    },
    "limit": {
      "type": "integer",
      "description": "Maximum number of results to return (optional)",
      "minimum": 1,
      "maximum": 50
    }
  },
  "required": ["query"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "operationId": { "type": "string" },
          "path": { "type": "string" },
          "method": { "type": "string" },
          "summary": { "type": "string" },
          "description": { "type": "string" },
          "tags": { "type": "array", "items": { "type": "string" } },
          "implementationGuide": { "type": "string" }
        }
      }
    },
    "count": { "type": "integer" }
  }
}
```

### Example Usage

**Request**:
```json
{
  "query": "device inventory"
}
```

**Response**:
```json
{
  "results": [
    {
      "operationId": "getNetworkDeviceList",
      "path": "/dna/intent/api/v1/network-device",
      "method": "GET",
      "summary": "Get network device list",
      "description": "Returns list of network devices based on filter criteria...",
      "tags": ["Devices", "Inventory"],
      "implementationGuide": "Use pagination for large deployments..."
    }
  ],
  "count": 1
}
```

---

## Tool: Meraki-API-OperationId-Search

**Purpose**: Retrieve complete OpenAPI specification for a specific Meraki operation

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "operationId": {
      "type": "string",
      "description": "Exact operation ID to look up (e.g., 'createNetworkMerakiAuthUser')"
    }
  },
  "required": ["operationId"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "operationId": { "type": "string" },
    "path": { "type": "string" },
    "method": { "type": "string" },
    "summary": { "type": "string" },
    "description": { "type": "string" },
    "parameters": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "in": { "type": "string" },
          "required": { "type": "boolean" },
          "schema": { "type": "object" }
        }
      }
    },
    "requestBody": { "type": "object" },
    "responses": { "type": "object" },
    "examples": { "type": "array" }
  }
}
```

### Example Usage

**Request**:
```json
{
  "operationId": "updateNetworkApplianceFirewallL3FirewallRules"
}
```

**Response**:
```json
{
  "operationId": "updateNetworkApplianceFirewallL3FirewallRules",
  "path": "/networks/{networkId}/appliance/firewall/l3FirewallRules",
  "method": "PUT",
  "summary": "Update the L3 firewall rules of an MX network",
  "description": "Update the L3 firewall rules of an MX network...",
  "parameters": [
    {
      "name": "networkId",
      "in": "path",
      "required": true,
      "schema": { "type": "string" }
    }
  ],
  "requestBody": {
    "content": {
      "application/json": {
        "schema": {
          "type": "object",
          "properties": {
            "rules": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "comment": { "type": "string" },
                  "policy": { "type": "string", "enum": ["allow", "deny"] },
                  "protocol": { "type": "string" },
                  "srcPort": { "type": "string" },
                  "srcCidr": { "type": "string" },
                  "destPort": { "type": "string" },
                  "destCidr": { "type": "string" }
                }
              }
            }
          }
        }
      }
    }
  },
  "responses": {
    "200": {
      "description": "Successful operation"
    }
  }
}
```

---

## Error Handling

All tools return standard MCP error responses:

| Error | Description |
|-------|-------------|
| `invalid_params` | Missing or invalid parameters |
| `not_found` | Operation ID not found (Meraki-API-OperationId-Search) |
| `server_error` | DevNet server unavailable |
| `rate_limited` | Too many requests |

**Error Response Format**:
```json
{
  "error": {
    "code": "not_found",
    "message": "Operation ID 'invalidOperation' not found"
  }
}
```
