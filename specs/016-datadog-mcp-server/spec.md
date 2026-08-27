# Feature Specification: Datadog MCP Server Integration

**Feature ID**: 016-datadog-mcp-server
**Status**: Draft
**Created**: 2026-04-04

## Overview

Integrate the official Datadog MCP server to provide observability capabilities within NetGeniusClaw. This enables teams using Datadog to leverage NetGeniusClaw for log queries, metric analysis, incident investigation, and APM trace exploration.

## Source

- **Repository**: https://github.com/datadog-labs/mcp-server
- **Type**: Official (Datadog-maintained)
- **License**: Apache-2.0
- **Transport**: Remote MCP (managed service)

## Tools Available (16+ core, extensible)

### Core Tools

| Category | Tools |
|----------|-------|
| **Logs** | search_logs, get_log_details |
| **Metrics** | query_metrics, list_metrics, get_metric_metadata |
| **Traces** | search_traces, get_trace_details |
| **Incidents** | list_incidents, get_incident, create_incident, update_incident |
| **Monitors** | list_monitors, get_monitor, mute_monitor |
| **Dashboards** | list_dashboards, get_dashboard |

### Optional Toolsets

| Toolset | Description |
|---------|-------------|
| **APM** | Application Performance Monitoring traces and spans |
| **Error Tracking** | Error aggregation and stack trace analysis |
| **Feature Flags** | Feature flag state and rollout status |
| **DBM** | Database Monitoring queries and performance |
| **Security** | Security signals and threat detection |
| **LLM Observability** | AI/ML model performance tracking |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DD_API_KEY` | Yes | Datadog API key |
| `DD_APP_KEY` | Yes | Datadog Application key |
| `DD_SITE` | No | Datadog site (default: datadoghq.com, EU: datadoghq.eu) |

## User Stories

### US1: Log Investigation (Priority: P1) MVP
**As a** network engineer troubleshooting an issue
**I want to** search Datadog logs from NetGeniusClaw
**So that** I can correlate network events with application logs

**Acceptance Criteria:**
- Can search logs by query, time range, and service
- Can filter by log level, host, or custom tags
- Results include timestamp, message, and relevant attributes

### US2: Metric Analysis (Priority: P1) MVP
**As a** network engineer
**I want to** query Datadog metrics
**So that** I can analyze network device performance alongside application metrics

**Acceptance Criteria:**
- Can query metrics by name and time range
- Can apply aggregations (avg, sum, max, min)
- Can group by tags (host, device, interface)

### US3: Incident Correlation (Priority: P2)
**As a** network engineer responding to an alert
**I want to** view Datadog incidents related to network services
**So that** I can understand the full impact of network issues

**Acceptance Criteria:**
- Can list active incidents filtered by service or tag
- Can view incident timeline and status
- Can correlate with PagerDuty incidents

### US4: APM Trace Analysis (Priority: P3)
**As a** network engineer investigating latency
**I want to** search APM traces for network-related services
**So that** I can identify if network latency is causing application slowdowns

**Acceptance Criteria:**
- Can search traces by service, operation, or duration
- Can view trace waterfall with timing breakdown
- Can identify network spans vs application spans

## Proposed Skills

| Skill | Tools | Description |
|-------|-------|-------------|
| `datadog-logs` | 4 | Log search, filtering, and analysis |
| `datadog-metrics` | 4 | Metric queries and dashboard access |
| `datadog-incidents` | 4 | Incident management and correlation |
| `datadog-apm` | 4 | APM traces and performance analysis |

## Integration Points

- **Grafana**: Alternative/complementary observability
- **PagerDuty**: Incident correlation
- **SuzieQ**: Network state correlation with Datadog metrics
- **Syslog Receiver**: Forward network logs to Datadog

## Clarifications

### Session 2026-04-04
- Q: Optional toolsets enablement? → A: Enable ALL optional toolsets (APM, Error Tracking, Feature Flags, DBM, Security, LLM Observability)

## Security Considerations

- API keys stored in .env, never logged
- Read-only operations by default
- Incident creation requires explicit user confirmation
- All optional toolsets enabled for maximum observability coverage

## Success Criteria

1. Can query "search Datadog logs for BGP errors in last hour" and get results
2. Can query "show network interface metrics from Datadog" and get time series
3. Integration appears in NetGeniusClaw UI with correct tool count
4. All 4 skills documented with SKILL.md files
