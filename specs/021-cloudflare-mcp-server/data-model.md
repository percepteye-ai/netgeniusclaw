# Data Model: Cloudflare MCP Server Integration

**Feature**: 021-cloudflare-mcp-server | **Date**: 2026-04-04

## Overview

This is a stateless remote MCP server integration. The Cloudflare domain-specific MCP servers act as managed proxies to Cloudflare's APIs. No local data storage is required.

## External Entities

### DNS Zone

| Field | Type | Description |
|-------|------|-------------|
| id | string | Zone identifier |
| name | string | Zone name (domain) |
| status | enum | active, pending, initializing |
| paused | boolean | Zone paused status |
| type | enum | full, partial, secondary |
| development_mode | integer | Dev mode seconds remaining |
| name_servers | array | Assigned nameservers |
| original_name_servers | array | Original nameservers |
| created_on | datetime | Creation timestamp |
| modified_on | datetime | Last modification |

### DNS Record

| Field | Type | Description |
|-------|------|-------------|
| id | string | Record identifier |
| zone_id | string | Parent zone |
| zone_name | string | Zone name |
| name | string | Record name (FQDN) |
| type | enum | A, AAAA, CNAME, TXT, MX, etc. |
| content | string | Record content |
| proxied | boolean | Cloudflare proxy status |
| ttl | integer | TTL in seconds |
| priority | integer | MX priority |
| comment | string | Record comment |

### Access Application

| Field | Type | Description |
|-------|------|-------------|
| id | string | Application identifier |
| name | string | Application name |
| domain | string | Application domain |
| type | enum | self_hosted, saas, bookmark, vnc, ssh |
| session_duration | string | Session duration |
| auto_redirect_to_identity | boolean | Auto redirect |
| policies | array | Associated policies |
| allowed_idps | array | Allowed identity providers |

### Access Policy

| Field | Type | Description |
|-------|------|-------------|
| id | string | Policy identifier |
| name | string | Policy name |
| precedence | integer | Evaluation order |
| decision | enum | allow, deny, non_identity, bypass |
| include | array | Include rules |
| exclude | array | Exclude rules |
| require | array | Require rules |
| isolation_required | boolean | Browser isolation |

### Tunnel

| Field | Type | Description |
|-------|------|-------------|
| id | string | Tunnel identifier |
| name | string | Tunnel name |
| status | enum | healthy, degraded, down |
| conns_active_at | datetime | Last connection |
| created_at | datetime | Creation timestamp |
| deleted_at | datetime | Deletion timestamp |
| connections | array | Active connections |

### Firewall Rule

| Field | Type | Description |
|-------|------|-------------|
| id | string | Rule identifier |
| priority | integer | Rule priority |
| action | enum | block, challenge, js_challenge, allow, log, bypass |
| filter | object | Filter expression |
| paused | boolean | Rule paused |
| description | string | Rule description |

### Analytics

| Field | Type | Description |
|-------|------|-------------|
| since | datetime | Period start |
| until | datetime | Period end |
| requests | object | Request metrics |
| bandwidth | object | Bandwidth metrics |
| threats | object | Threat metrics |
| pageviews | object | Pageview metrics |
| uniques | object | Unique visitor metrics |

## Relationships

```
┌──────────────────────────────────────────────────────────────┐
│                    Cloudflare Account                          │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│  │    Zones    │    │ Zero Trust  │    │   Workers   │       │
│  │   (DNS)     │    │  (Access)   │    │  (Compute)  │       │
│  └─────────────┘    └─────────────┘    └─────────────┘       │
│         │                  │                  │               │
│         ▼                  ▼                  ▼               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│  │ DNS Records │    │Applications │    │   Scripts   │       │
│  │ Page Rules  │    │  Policies   │    │  Bindings   │       │
│  │ Firewall    │    │   Tunnels   │    │    Crons    │       │
│  └─────────────┘    └─────────────┘    └─────────────┘       │
│                                                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│  │  Analytics  │    │    CASB     │    │   Radar     │       │
│  │   Logs      │    │  Findings   │    │  Insights   │       │
│  └─────────────┘    └─────────────┘    └─────────────┘       │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

## Zero Trust Policy Evaluation

```
[Gateway Policy] → [Access Application] → [Access Policy]
                           ↓
                    [Identity Check]
                           ↓
                   [Device Posture]
                           ↓
                   [Allow / Deny]
```

## No Local Storage

This integration does not persist any data locally. All state is maintained by Cloudflare.
