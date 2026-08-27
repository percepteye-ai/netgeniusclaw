# Datadog MCP Tools Contract

**Feature**: 016-datadog-mcp-server | **Date**: 2026-04-04

## Overview

This document defines the tool interface contract for the official Datadog MCP server integration.

## MCP Server Configuration

```json
{
  "datadog-mcp": {
    "transport": "remote",
    "url": "mcp://datadog.com/mcp",
    "env": {
      "DD_API_KEY": "${DD_API_KEY}",
      "DD_APP_KEY": "${DD_APP_KEY}",
      "DD_SITE": "${DD_SITE}"
    },
    "toolsets": ["apm", "error_tracking", "feature_flags", "dbm", "security", "llm_observability"]
  }
}
```

## Tool Catalog by Skill

### datadog-logs (4 tools)

| Tool | Type | Parameters | Returns |
|------|------|------------|---------|
| `search_logs` | read | query, from?, to?, limit?, sort? | Array of log entries |
| `get_log_details` | read | log_id | Log entry details |
| `list_log_indexes` | read | - | Available log indexes |
| `get_log_pipeline` | read | pipeline_id | Processing pipeline config |

### datadog-metrics (4 tools)

| Tool | Type | Parameters | Returns |
|------|------|------------|---------|
| `query_metrics` | read | query, from, to | Time series data |
| `list_metrics` | read | query?, filter? | Available metrics |
| `get_metric_metadata` | read | metric_name | Metric metadata |
| `list_dashboards` | read | - | Dashboard list |
| `get_dashboard` | read | dashboard_id | Dashboard config |

### datadog-incidents (4 tools)

| Tool | Type | Parameters | Returns |
|------|------|------------|---------|
| `list_incidents` | read | status?, severity?, query? | Array of incidents |
| `get_incident` | read | incident_id | Incident details |
| `create_incident` | write | title, severity, customer_impacted? | Created incident |
| `update_incident` | write | incident_id, status?, severity? | Updated incident |

### datadog-apm (4 tools)

| Tool | Type | Parameters | Returns |
|------|------|------------|---------|
| `search_traces` | read | query?, service?, operation?, from?, to? | Array of traces |
| `get_trace_details` | read | trace_id | Trace with spans |
| `list_services` | read | env? | APM services |
| `get_service_summary` | read | service_name, env? | Service performance summary |

## Optional Toolsets

All enabled per user clarification:

### APM Toolset
- `search_traces`, `get_trace_details`, `list_services`, `get_service_summary`

### Error Tracking Toolset
- `list_errors`, `get_error_details`, `list_error_groups`

### Feature Flags Toolset
- `list_feature_flags`, `get_feature_flag`, `get_flag_evaluations`

### DBM Toolset
- `list_db_queries`, `get_query_details`, `get_db_hosts`

### Security Toolset
- `list_security_signals`, `get_security_signal`, `list_findings`

### LLM Observability Toolset
- `list_llm_traces`, `get_llm_metrics`, `list_model_spans`

## Error Responses

| Code | Meaning | Example |
|------|---------|---------|
| 400 | Bad Request | Invalid query syntax |
| 401 | Unauthorized | Invalid API/App key |
| 403 | Forbidden | Missing required scope |
| 404 | Not Found | Resource doesn't exist |
| 429 | Rate Limited | Too many requests |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DD_API_KEY` | Yes | Datadog API Key |
| `DD_APP_KEY` | Yes | Datadog Application Key |
| `DD_SITE` | No | Datadog site (default: datadoghq.com) |
