# Feature Specification: Cloudflare MCP Server Integration

**Feature ID**: 021-cloudflare-mcp-server
**Status**: Draft
**Created**: 2026-04-04

## Overview

Integrate the official Cloudflare MCP server collection to provide Zero Trust, DNS, Workers, and edge security capabilities within NetGeniusClaw. Cloudflare offers both domain-specific MCP servers and a unified API server with 2500+ endpoints accessible via 2 tools.

## Source

- **Repository**: https://github.com/cloudflare/mcp-server-cloudflare
- **Type**: Official (Cloudflare-maintained)
- **License**: Apache-2.0
- **Transport**: Remote MCP (managed service via mcp-remote)

## MCP Servers Available (15 domain-specific)

| Server | URL | Description |
|--------|-----|-------------|
| **Documentation** | docs.mcp.cloudflare.com | Reference information on Cloudflare |
| **Workers Bindings** | workers-bindings.mcp.cloudflare.com | Workers with storage, AI, compute |
| **Workers Builds** | workers-builds.mcp.cloudflare.com | Workers build insights and management |
| **Observability** | observability.mcp.cloudflare.com | Logs and analytics debugging |
| **Radar** | radar.mcp.cloudflare.com | Global Internet traffic insights, URL scans |
| **Container** | container.mcp.cloudflare.com | Sandbox development environments |
| **Browser Rendering** | browser.mcp.cloudflare.com | Web page fetch, markdown conversion, screenshots |
| **Logpush** | logpush.mcp.cloudflare.com | Logpush job health summaries |
| **AI Gateway** | ai-gateway.mcp.cloudflare.com | AI prompt/response log search |
| **AutoRAG** | autorag.mcp.cloudflare.com | RAG document listing and search |
| **Audit Logs** | audit-logs.mcp.cloudflare.com | Audit log queries and reports |
| **DNS Analytics** | dns-analytics.mcp.cloudflare.com | DNS performance optimization |
| **Digital Experience** | dex.mcp.cloudflare.com | Critical application insights |
| **CASB** | casb.mcp.cloudflare.com | SaaS security misconfiguration detection |
| **GraphQL** | graphql.mcp.cloudflare.com | Analytics via Cloudflare GraphQL API |

## Unified API Server

The Cloudflare API MCP server provides access to the entire Cloudflare API (2500+ endpoints) through just 2 tools:

| Tool | Description |
|------|-------------|
| `search()` | Search API endpoints by keyword or capability |
| `execute()` | Execute any Cloudflare API endpoint |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CLOUDFLARE_API_TOKEN` | Yes | Cloudflare API token |
| `CLOUDFLARE_ACCOUNT_ID` | Yes | Cloudflare account ID |
| `CLOUDFLARE_ZONE_ID` | No | Default zone ID for DNS operations |

## User Stories

### US1: DNS Management (Priority: P1) MVP
**As a** network engineer
**I want to** manage Cloudflare DNS records
**So that** I can configure network service discovery

**Acceptance Criteria:**
- Can list DNS zones and records
- Can create/update/delete DNS records
- Can view DNS analytics

### US2: Zero Trust Access (Priority: P1) MVP
**As a** network security engineer
**I want to** inspect Cloudflare Zero Trust configurations
**So that** I can audit access policies

**Acceptance Criteria:**
- Can list access policies and applications
- Can view tunnel configurations
- Can inspect CASB findings

### US3: Traffic Analytics (Priority: P2)
**As a** network engineer
**I want to** view Cloudflare Radar traffic insights
**So that** I can understand global traffic patterns

**Acceptance Criteria:**
- Can query traffic trends by region
- Can view threat intelligence data
- Can scan URLs for security analysis

### US4: Log Analysis (Priority: P2)
**As a** network operations engineer
**I want to** query Cloudflare logs
**So that** I can troubleshoot edge issues

**Acceptance Criteria:**
- Can search HTTP request logs
- Can view firewall event logs
- Can query audit logs

## Proposed Skills

| Skill | Tools | Description |
|-------|-------|-------------|
| `cloudflare-dns` | 6 | DNS zone and record management |
| `cloudflare-zerotrust` | 8 | Zero Trust access and tunnel configuration |
| `cloudflare-analytics` | 6 | Traffic, DNS, and security analytics |
| `cloudflare-workers` | 6 | Workers deployment and monitoring |
| `cloudflare-security` | 6 | WAF, CASB, and firewall rules |

## Integration Points

- **Infoblox**: Hybrid DNS management
- **Grafana**: Cloudflare metrics visualization
- **Splunk**: Cloudflare log forwarding
- **PagerDuty**: Alert on security events

## Clarifications

### Session 2026-04-04
- Q: Cloudflare MCP architecture? → A: Domain-specific servers only (no unified API execute())

## Security Considerations

- Domain-specific MCP servers only (no unified API execute() for safety)
- API token scoped to minimum required permissions
- Write operations require explicit confirmation
- Audit logs track all API calls
- Zone-level permissions for DNS changes

## Success Criteria

1. Can query "list my Cloudflare DNS records for example.com" and get results
2. Can query "show Cloudflare Zero Trust access policies" and see policies
3. Integration appears in NetGeniusClaw UI with correct tool count
4. All 5 skills documented with SKILL.md files
