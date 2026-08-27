# A2UI Output Contract: Canvas Network Visualization Skill

**Version**: 1.0.0
**Date**: 2026-03-26

## Overview

The `canvas-network-viz` skill produces A2UI JSON output that the OpenClaw Canvas framework renders inline in the chat interface. This contract defines the JSON schema for all visualization types.

## Root A2UI Output Structure

Every visualization output from the skill follows this envelope:

```json
{
  "a2ui": {
    "version": "1.0",
    "type": "canvas",
    "component": "<visualization-type>",
    "props": {
      "id": "<uuid>",
      "title": "<string>",
      "timestamp": "<ISO 8601>",
      "dataSources": [ ... ],
      "scope": { ... },
      "warnings": [ ... ],
      "content": { ... }
    }
  }
}
```

### Component Types

| `component` value | Description | Content model |
|-------------------|-------------|---------------|
| `topology-map` | Network topology graph | TopologyContent |
| `dashboard-panel` | Device/site metric dashboard | DashboardContent |
| `alert-card` | Alert/incident card list | AlertContent |
| `change-timeline` | ServiceNow CR lifecycle | TimelineContent |
| `diff-view` | Configuration/route/ACL diff | DiffContent |
| `path-trace` | Hop-by-hop forwarding diagram | PathTraceContent |
| `health-scorecard` | Aggregated health scores | ScorecardContent |

## Skill Invocation Patterns

The agent invokes the skill based on natural language operator requests. The skill maps requests to visualization types:

| Operator Request Pattern | Visualization Type | Required MCP Data |
|--------------------------|--------------------|-------------------|
| "show network topology" | `topology-map` | pyATS CDP/LLDP, health metrics |
| "show health dashboard for {device}" | `dashboard-panel` | pyATS, Grafana, Prometheus |
| "show site dashboard for {site}" | `dashboard-panel` | pyATS, Grafana, Prometheus |
| "show current alerts" | `alert-card` | Grafana alerts, Prometheus alertmanager |
| "show syslog alerts for {device}" | `alert-card` | pyATS syslog |
| "show change request {CR} status" | `change-timeline` | ServiceNow |
| "show all active change requests" | `change-timeline` | ServiceNow |
| "show config diff for {device}" | `diff-view` | pyATS config |
| "show routing changes for {device}" | `diff-view` | pyATS routing |
| "show ACL diff for {device}" | `diff-view` | pyATS ACL |
| "trace path from {src} to {dst}" | `path-trace` | pyATS/SuzieQ routing/forwarding |
| "show health scorecard for {site}" | `health-scorecard` | pyATS, Grafana, Prometheus |
| "show device health for {device}" | `health-scorecard` | pyATS, Grafana, Prometheus |

## Error Responses

When a visualization cannot be generated at all (not degraded, but completely impossible):

```json
{
  "a2ui": {
    "version": "1.0",
    "type": "canvas",
    "component": "error-card",
    "props": {
      "title": "Visualization Unavailable",
      "message": "<human-readable explanation>",
      "suggestion": "<what the operator can do instead>",
      "timestamp": "<ISO 8601>"
    }
  }
}
```

## GAIT Audit Event Format

Each visualization generation emits a GAIT log entry:

```json
{
  "event": "visualization_generated",
  "visualizationType": "<component type>",
  "dataSources": ["<server:tool>", ...],
  "scope": { "devices": [...], "sites": [...] },
  "status": "complete|degraded|failed",
  "renderDurationMs": <number>,
  "timestamp": "<ISO 8601>"
}
```

## Backwards Compatibility

- This skill does not modify any existing MCP server tool schemas.
- This skill does not modify the Three.js HUD at `ui/netclaw-visual/`.
- New A2UI component types are additive — existing Canvas components are unaffected.
- The skill registers no new MCP tools — it is a consumer of existing tools only.
