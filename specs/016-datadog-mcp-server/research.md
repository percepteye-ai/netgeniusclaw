# Research: Datadog MCP Server Integration

**Feature**: 016-datadog-mcp-server | **Date**: 2026-04-04

## Research Tasks

### RT1: Official Datadog MCP Server Evaluation

**Decision**: Use official Datadog MCP server (datadog-labs/mcp-server)

**Rationale**:
- Maintained by Datadog Labs (official team)
- Apache-2.0 licensed
- Remote MCP architecture (managed service)
- Comprehensive toolset covering logs, metrics, traces, incidents
- Active development with extensible toolset architecture

**Alternatives Considered**:
| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| Official Datadog MCP | Managed, full API coverage | Requires remote connection | Selected |
| Custom FastMCP server | Full control | Massive API surface | Rejected |
| REST API direct | No MCP dependency | No MCP integration | Rejected |

### RT2: Connection Method

**Decision**: Remote MCP (managed service endpoint)

**Rationale**:
- Datadog MCP runs as a remote service
- No local installation required
- Automatic updates and maintenance
- Consistent with Datadog's managed service philosophy

**Configuration**:
```json
{
  "datadog-mcp": {
    "transport": "remote",
    "url": "mcp://datadog.com/mcp",
    "env": {
      "DD_API_KEY": "${DD_API_KEY}",
      "DD_APP_KEY": "${DD_APP_KEY}"
    }
  }
}
```

### RT3: Optional Toolsets

**Decision**: Enable ALL optional toolsets

**Rationale**:
- User preference from clarification session
- Maximum observability coverage
- All toolsets are read-focused with low risk
- Enables full correlation capabilities

**Enabled Toolsets**:
| Toolset | Purpose |
|---------|---------|
| APM | Application performance traces and spans |
| Error Tracking | Error aggregation and analysis |
| Feature Flags | Feature rollout monitoring |
| DBM | Database query performance |
| Security | Security signals and threats |
| LLM Observability | AI/ML model metrics |

### RT4: Authentication Method

**Decision**: API Key + Application Key via environment variables

**Rationale**:
- Datadog requires both keys for API access
- DD_API_KEY: Identifies the account
- DD_APP_KEY: Grants programmatic access
- Standard pattern for Datadog integrations

**Key Requirements**:
- API Key: Organization-level key from Datadog
- App Key: User or service account key with required scopes
- EU customers use datadoghq.eu endpoint

### RT5: Skill Organization

**Decision**: 4 focused skills aligned with Datadog domains

**Rationale**:
- Logs: Core troubleshooting capability
- Metrics: Performance analysis
- Incidents: Correlation with PagerDuty
- APM: Latency investigation

**Tool Distribution**:
| Skill | Tools | Description |
|-------|-------|-------------|
| datadog-logs | 4 | Log search, filtering, analysis |
| datadog-metrics | 4 | Metric queries, dashboards |
| datadog-incidents | 4 | Incident management |
| datadog-apm | 4 | APM traces, performance |

## Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Datadog MCP | remote | Managed MCP service |
| DD_API_KEY | - | Account authentication |
| DD_APP_KEY | - | Programmatic access |

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Remote MCP latency | Medium | Low | Expected for managed service |
| API rate limiting | Medium | Medium | Datadog has generous limits |
| Key rotation | Low | Medium | Documentation for key management |
| Feature deprecation | Low | Low | Use stable API versions |

## Open Questions Resolved

All research tasks completed. No blocking unknowns remain.
