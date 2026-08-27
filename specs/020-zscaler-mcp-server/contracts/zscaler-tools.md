# Zscaler MCP Tools Contract

**Feature**: 020-zscaler-mcp-server | **Date**: 2026-04-04

## Overview

This document defines the tool interface contract for the official Zscaler MCP server integration. With 300+ tools across 9 services, this is the largest integration in NetGeniusClaw.

## MCP Server Configuration

```json
{
  "zscaler-mcp": {
    "command": "zscaler-mcp-server",
    "args": ["--transport", "stdio"],
    "env": {
      "ZSCALER_CLIENT_ID": "${ZSCALER_CLIENT_ID}",
      "ZSCALER_CLIENT_SECRET": "${ZSCALER_CLIENT_SECRET}",
      "ZSCALER_CUSTOMER_ID": "${ZSCALER_CUSTOMER_ID}",
      "ZSCALER_VANITY_DOMAIN": "${ZSCALER_VANITY_DOMAIN}",
      "ZSCALER_MCP_SERVICES": "zia,zpa,zdx,zms,ztw,zinsights,zidentity,easm,zcc"
    }
  }
}
```

## Tool Catalog by Skill

### zscaler-zpa (20 representative tools)

| Tool | Type | Parameters | Returns |
|------|------|------------|---------|
| `list_application_segments` | read | segment_group_id? | Array of segments |
| `get_application_segment` | read | id | Segment details |
| `list_segment_groups` | read | - | Array of groups |
| `get_segment_group` | read | id | Group details |
| `list_access_policies` | read | - | Array of policies |
| `get_access_policy` | read | id | Policy details |
| `list_app_connectors` | read | - | Array of connectors |
| `get_app_connector` | read | id | Connector details |
| `list_connector_groups` | read | - | Array of groups |
| `get_connector_group` | read | id | Group details |
| `list_server_groups` | read | - | Array of servers |
| `get_server_group` | read | id | Server details |
| `create_application_segment` | write | name, domains, ports | Created segment |
| `update_application_segment` | write | id, fields | Updated segment |
| `delete_application_segment` | write | id, confirm_token | Deletion result |
| `create_access_policy` | write | name, action, rules | Created policy |
| `update_access_policy` | write | id, fields | Updated policy |
| `delete_access_policy` | write | id, confirm_token | Deletion result |

### zscaler-zia (20 representative tools)

| Tool | Type | Parameters | Returns |
|------|------|------------|---------|
| `list_firewall_rules` | read | - | Array of rules |
| `get_firewall_rule` | read | id | Rule details |
| `list_url_filtering_rules` | read | - | Array of rules |
| `get_url_filtering_rule` | read | id | Rule details |
| `list_dlp_dictionaries` | read | - | Array of dictionaries |
| `get_dlp_dictionary` | read | id | Dictionary details |
| `list_url_categories` | read | - | Array of categories |
| `get_url_category` | read | id | Category details |
| `list_locations` | read | - | Array of locations |
| `get_location` | read | id | Location details |
| `create_firewall_rule` | write | name, action, config | Created rule |
| `update_firewall_rule` | write | id, fields | Updated rule |
| `delete_firewall_rule` | write | id, confirm_token | Deletion result |
| `create_url_filtering_rule` | write | name, action, config | Created rule |
| `update_url_filtering_rule` | write | id, fields | Updated rule |

### zscaler-zdx (10 tools)

| Tool | Type | Parameters | Returns |
|------|------|------------|---------|
| `list_zdx_applications` | read | time_range? | Array of apps with scores |
| `get_zdx_application` | read | id | App details and metrics |
| `list_zdx_users` | read | time_range?, score_threshold? | Array of users |
| `get_zdx_user` | read | id | User experience details |
| `list_zdx_devices` | read | time_range? | Array of devices |
| `get_zdx_device` | read | id | Device health details |
| `get_zdx_score_trends` | read | app_id?, time_range | Score trend data |
| `list_zdx_events` | read | time_range, severity? | Array of events |
| `get_zdx_probes` | read | app_id | Probe configurations |
| `list_zdx_alerts` | read | status? | Array of alerts |

### zscaler-identity (8 tools)

| Tool | Type | Parameters | Returns |
|------|------|------------|---------|
| `list_users` | read | search?, dept? | Array of users |
| `get_user` | read | id | User details |
| `list_groups` | read | search? | Array of groups |
| `get_group` | read | id | Group details |
| `list_departments` | read | - | Array of departments |
| `get_department` | read | id | Department details |
| `list_idp_configs` | read | - | Array of IdP configs |
| `get_idp_config` | read | id | IdP configuration |

### zscaler-insights (6 tools)

| Tool | Type | Parameters | Returns |
|------|------|------------|---------|
| `get_threat_intelligence` | read | time_range | Threat summary |
| `list_security_events` | read | time_range, type? | Array of events |
| `get_security_event` | read | id | Event details |
| `list_blocked_threats` | read | time_range | Blocked threat list |
| `get_traffic_analytics` | read | time_range, dimension | Traffic analysis |
| `list_anomalies` | read | time_range | Detected anomalies |

## Service-Specific Tool Counts

| Service | Read | Write | Delete | Total |
|---------|------|-------|--------|-------|
| ZIA | 60 | 36 | 10 | 106 |
| ZPA | 50 | 30 | 8 | 88 |
| ZDX | 31 | 0 | 0 | 31 |
| ZMS | 12 | 6 | 2 | 20 |
| ZTW | 11 | 6 | 2 | 19 |
| Z-Insights | 16 | 0 | 0 | 16 |
| ZIdentity | 6 | 3 | 1 | 10 |
| EASM | 7 | 0 | 0 | 7 |
| ZCC | 4 | 0 | 0 | 4 |

## Delete Confirmation

Delete operations require a confirmation token:

```json
{
  "tool": "delete_application_segment",
  "params": {
    "id": "segment-123",
    "confirm_token": "CONFIRM-DELETE-segment-123-2026-04-04T12:00:00Z"
  }
}
```

## Error Responses

| Code | Meaning | Example |
|------|---------|---------|
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Invalid credentials |
| 403 | Forbidden | Write tools not enabled |
| 404 | Not Found | Resource doesn't exist |
| 429 | Rate Limited | Too many requests |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ZSCALER_CLIENT_ID` | Yes | OAuth client ID |
| `ZSCALER_CLIENT_SECRET` | Yes | OAuth client secret |
| `ZSCALER_CUSTOMER_ID` | Yes | Customer ID |
| `ZSCALER_VANITY_DOMAIN` | Yes | Vanity domain |
| `ZSCALER_MCP_SERVICES` | No | Comma-separated service list |
| `ZSCALER_MCP_WRITE_ENABLED` | No | Enable write tools |
