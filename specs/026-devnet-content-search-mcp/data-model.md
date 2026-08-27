# Data Model: DevNet Content Search MCP Server Integration

**Feature**: 026-devnet-content-search-mcp
**Date**: 2026-04-09

## Overview

This integration does not introduce new persistent data models. All data is retrieved in real-time from the remote DevNet MCP server. This document describes the data structures returned by the MCP tools.

## Entities

### SearchQuery

Represents user input for documentation search.

| Field | Type | Description |
|-------|------|-------------|
| query | string | Search terms (e.g., "L3 firewall rules") |
| limit | integer (optional) | Maximum results to return |

**Validation Rules**:
- `query` must be non-empty string
- `limit` must be positive integer if provided

---

### SearchResult

Represents a collection of matching API endpoints returned from search.

| Field | Type | Description |
|-------|------|-------------|
| results | array | List of APIEndpoint objects |
| count | integer | Number of results returned |
| query | string | Original search query |

---

### APIEndpoint

Represents documentation for a single API operation.

| Field | Type | Description |
|-------|------|-------------|
| operationId | string | Unique identifier (e.g., "updateNetworkApplianceFirewallL3FirewallRules") |
| path | string | API endpoint path (e.g., "/networks/{networkId}/appliance/firewall/l3FirewallRules") |
| method | string | HTTP method (GET, POST, PUT, DELETE, etc.) |
| summary | string | Brief description of the operation |
| description | string | Detailed description with usage context |
| parameters | array | Request parameters (path, query, header) |
| requestBody | object | Request body schema (if applicable) |
| responses | object | Response schemas by status code |
| tags | array | Categorization tags |
| examples | array | Code examples (when available) |

---

### OperationLookup

Represents input for specific operation ID lookup.

| Field | Type | Description |
|-------|------|-------------|
| operationId | string | Exact operation ID to retrieve |

**Validation Rules**:
- `operationId` must be non-empty string
- Case-sensitive matching

---

## Relationships

```
SearchQuery ─────> SearchResult ─────> APIEndpoint[]
                                              │
OperationLookup ──────────────────────────────┘
                   (direct lookup by ID)
```

## State Transitions

N/A - This integration is stateless. Each search or lookup is independent with no persistent state.

## Data Flow

```
User Query
    │
    ▼
┌─────────────────────┐
│ NetGeniusClaw Skill       │
│ (devnet-*-search)   │
└─────────────────────┘
    │
    ▼ MCP Tool Call
┌─────────────────────┐
│ devnet-content-     │
│ search MCP Server   │
│ (remote)            │
└─────────────────────┘
    │
    ▼ JSON Response
┌─────────────────────┐
│ SearchResult /      │
│ APIEndpoint         │
└─────────────────────┘
    │
    ▼
User Display
```
