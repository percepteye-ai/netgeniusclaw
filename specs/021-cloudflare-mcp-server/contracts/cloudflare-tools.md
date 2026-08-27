# Cloudflare MCP Tools Contract

**Feature**: 021-cloudflare-mcp-server | **Date**: 2026-04-04

## Overview

This document defines the tool interface contract for the official Cloudflare domain-specific MCP server integration. Using 15 focused MCP servers instead of the unified API for safety and clarity.

## MCP Server Configurations

### Primary Servers for Network Operations

```json
{
  "cloudflare-dns-analytics": {
    "transport": "remote",
    "url": "dns-analytics.mcp.cloudflare.com",
    "env": {
      "CLOUDFLARE_API_TOKEN": "${CLOUDFLARE_API_TOKEN}",
      "CLOUDFLARE_ACCOUNT_ID": "${CLOUDFLARE_ACCOUNT_ID}"
    }
  },
  "cloudflare-observability": {
    "transport": "remote",
    "url": "observability.mcp.cloudflare.com",
    "env": {
      "CLOUDFLARE_API_TOKEN": "${CLOUDFLARE_API_TOKEN}",
      "CLOUDFLARE_ACCOUNT_ID": "${CLOUDFLARE_ACCOUNT_ID}"
    }
  },
  "cloudflare-audit-logs": {
    "transport": "remote",
    "url": "audit-logs.mcp.cloudflare.com",
    "env": {
      "CLOUDFLARE_API_TOKEN": "${CLOUDFLARE_API_TOKEN}",
      "CLOUDFLARE_ACCOUNT_ID": "${CLOUDFLARE_ACCOUNT_ID}"
    }
  },
  "cloudflare-casb": {
    "transport": "remote",
    "url": "casb.mcp.cloudflare.com",
    "env": {
      "CLOUDFLARE_API_TOKEN": "${CLOUDFLARE_API_TOKEN}",
      "CLOUDFLARE_ACCOUNT_ID": "${CLOUDFLARE_ACCOUNT_ID}"
    }
  },
  "cloudflare-radar": {
    "transport": "remote",
    "url": "radar.mcp.cloudflare.com",
    "env": {
      "CLOUDFLARE_API_TOKEN": "${CLOUDFLARE_API_TOKEN}",
      "CLOUDFLARE_ACCOUNT_ID": "${CLOUDFLARE_ACCOUNT_ID}"
    }
  }
}
```

## Tool Catalog by Skill

### cloudflare-dns (6 tools)

| Tool | Type | Source Server | Parameters | Returns |
|------|------|---------------|------------|---------|
| `list_zones` | read | dns-analytics | account_id | Array of zones |
| `get_zone` | read | dns-analytics | zone_id | Zone details |
| `list_dns_records` | read | dns-analytics | zone_id, type? | Array of records |
| `get_dns_analytics` | read | dns-analytics | zone_id, since, until | DNS metrics |
| `get_dns_performance` | read | dns-analytics | zone_id | Performance data |
| `get_dns_trends` | read | dns-analytics | zone_id, metric | Trend analysis |

### cloudflare-zerotrust (8 tools)

| Tool | Type | Source Server | Parameters | Returns |
|------|------|---------------|------------|---------|
| `list_access_applications` | read | casb | account_id | Array of apps |
| `get_access_application` | read | casb | account_id, app_id | App details |
| `list_access_policies` | read | casb | account_id, app_id | Array of policies |
| `get_access_policy` | read | casb | account_id, app_id, policy_id | Policy details |
| `list_tunnels` | read | casb | account_id | Array of tunnels |
| `get_tunnel` | read | casb | account_id, tunnel_id | Tunnel details |
| `list_casb_findings` | read | casb | account_id | Security findings |
| `get_casb_finding` | read | casb | account_id, finding_id | Finding details |

### cloudflare-analytics (6 tools)

| Tool | Type | Source Server | Parameters | Returns |
|------|------|---------------|------------|---------|
| `get_zone_analytics` | read | observability | zone_id, since, until | Zone metrics |
| `search_logs` | read | observability | query, since, until | Log entries |
| `get_traffic_insights` | read | radar | region?, asn? | Traffic data |
| `scan_url` | read | radar | url | URL analysis |
| `get_threat_intel` | read | radar | indicator | Threat data |
| `get_internet_trends` | read | radar | metric, since, until | Trend data |

### cloudflare-workers (6 tools)

| Tool | Type | Source Server | Parameters | Returns |
|------|------|---------------|------------|---------|
| `list_workers` | read | workers-bindings | account_id | Array of workers |
| `get_worker` | read | workers-bindings | account_id, name | Worker details |
| `get_worker_bindings` | read | workers-bindings | account_id, name | Bindings config |
| `list_builds` | read | workers-builds | account_id, name | Build history |
| `get_build` | read | workers-builds | account_id, build_id | Build details |
| `get_worker_analytics` | read | workers-bindings | account_id, name | Usage metrics |

### cloudflare-security (6 tools)

| Tool | Type | Source Server | Parameters | Returns |
|------|------|---------------|------------|---------|
| `list_firewall_rules` | read | observability | zone_id | Array of rules |
| `get_firewall_events` | read | observability | zone_id, since, until | Firewall events |
| `list_audit_logs` | read | audit-logs | account_id, since, until | Audit entries |
| `get_audit_log` | read | audit-logs | account_id, log_id | Entry details |
| `list_security_events` | read | observability | zone_id | Security events |
| `get_threat_score` | read | radar | ip | IP threat score |

## Domain-Specific Server Reference

| Server | URL | Primary Use |
|--------|-----|-------------|
| Documentation | docs.mcp.cloudflare.com | Reference docs |
| Workers Bindings | workers-bindings.mcp.cloudflare.com | Worker management |
| Workers Builds | workers-builds.mcp.cloudflare.com | Build insights |
| Observability | observability.mcp.cloudflare.com | Logs/analytics |
| Radar | radar.mcp.cloudflare.com | Traffic insights |
| Container | container.mcp.cloudflare.com | Sandboxes |
| Browser | browser.mcp.cloudflare.com | Page rendering |
| Logpush | logpush.mcp.cloudflare.com | Log forwarding |
| AI Gateway | ai-gateway.mcp.cloudflare.com | AI logging |
| AutoRAG | autorag.mcp.cloudflare.com | RAG search |
| Audit Logs | audit-logs.mcp.cloudflare.com | Audit queries |
| DNS Analytics | dns-analytics.mcp.cloudflare.com | DNS performance |
| Digital Experience | dex.mcp.cloudflare.com | App insights |
| CASB | casb.mcp.cloudflare.com | SaaS security |
| GraphQL | graphql.mcp.cloudflare.com | Analytics API |

## Error Responses

| Code | Meaning | Example |
|------|---------|---------|
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Invalid API token |
| 403 | Forbidden | Token lacks permission |
| 404 | Not Found | Resource doesn't exist |
| 429 | Rate Limited | Too many requests |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CLOUDFLARE_API_TOKEN` | Yes | Scoped API token |
| `CLOUDFLARE_ACCOUNT_ID` | Yes | Account identifier |
| `CLOUDFLARE_ZONE_ID` | No | Default zone for DNS |
