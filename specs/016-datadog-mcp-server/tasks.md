# Tasks: Datadog MCP Server Integration

**Feature**: 016-datadog-mcp-server | **Date**: 2026-04-04
**Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

## Task Overview

| Category | Tasks | Priority |
|----------|-------|----------|
| MCP Registration | 2 | P0 |
| Skills | 4 | P1 |
| Configuration | 2 | P1 |
| Documentation | 4 | P2 |
| UI Integration | 1 | P2 |

---

## P0: MCP Server Registration

### T1: Register Datadog MCP Server in openclaw.json
**File**: `config/openclaw.json`
**Action**: Add remote MCP server configuration

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

**Acceptance**: Server appears in `openclaw list` output

### T2: Add Environment Variables to .env.example
**File**: `.env.example`
**Action**: Add Datadog environment variables

```bash
# Datadog MCP Server
DD_API_KEY=your_datadog_api_key
DD_APP_KEY=your_datadog_app_key
# DD_SITE=datadoghq.eu  # For EU customers
```

**Acceptance**: Variables documented with comments

---

## P1: Skill Creation

### T3: Create datadog-logs Skill
**File**: `workspace/skills/datadog-logs/SKILL.md`
**Action**: Create skill documentation

**Content Requirements**:
- Skill name and description
- Tool list: search_logs, get_log_details, list_log_indexes, get_log_pipeline
- Example queries (search by service, status, time range)
- Prerequisites (DD_API_KEY, DD_APP_KEY)

**Acceptance**: Skill invocable via `/datadog-logs`

### T4: Create datadog-metrics Skill
**File**: `workspace/skills/datadog-metrics/SKILL.md`
**Action**: Create skill documentation

**Content Requirements**:
- Skill name and description
- Tool list: query_metrics, list_metrics, get_metric_metadata, list_dashboards, get_dashboard
- Example queries (metric queries with aggregations)
- Prerequisites

**Acceptance**: Skill invocable via `/datadog-metrics`

### T5: Create datadog-incidents Skill
**File**: `workspace/skills/datadog-incidents/SKILL.md`
**Action**: Create skill documentation

**Content Requirements**:
- Skill name and description
- Tool list: list_incidents, get_incident, create_incident, update_incident
- Example queries
- Prerequisites

**Acceptance**: Skill invocable via `/datadog-incidents`

### T6: Create datadog-apm Skill
**File**: `workspace/skills/datadog-apm/SKILL.md`
**Action**: Create skill documentation

**Content Requirements**:
- Skill name and description
- Tool list: search_traces, get_trace_details, list_services, get_service_summary
- Example queries (trace search, latency analysis)
- Prerequisites

**Acceptance**: Skill invocable via `/datadog-apm`

---

## P1: Configuration Updates

### T7: Update install.sh with Datadog Requirements
**File**: `scripts/install.sh`
**Action**: Add Datadog connectivity check

```bash
# Datadog MCP Server (Remote)
echo "ℹ Datadog MCP uses remote transport - no local installation required"
echo "  Ensure DD_API_KEY and DD_APP_KEY are configured"
```

**Acceptance**: Installation script documents remote transport

### T8: Update SOUL.md Skill Index
**File**: `SOUL.md`
**Action**: Add Datadog skills to index

```markdown
### Observability
- `/datadog-logs` - Log search and analysis
- `/datadog-metrics` - Metric queries and dashboards
- `/datadog-incidents` - Incident management
- `/datadog-apm` - APM trace investigation
```

**Acceptance**: Skills appear in SOUL.md index

---

## P2: Documentation Updates

### T9: Update README.md Architecture Section
**File**: `README.md`
**Action**: Add Datadog to MCP server count and integration list

- Update total MCP server count
- Add Datadog to integrations table
- Update tool count

**Acceptance**: README reflects new integration

### T10: Update README.md Tool Count
**File**: `README.md`
**Action**: Update total tool count (+16 tools)

**Acceptance**: Tool count accurate

### T11: Create Datadog Section in README
**File**: `README.md`
**Action**: Add Datadog integration description

```markdown
### Datadog (16+ tools)
Full observability stack integration with all optional toolsets enabled.
- Log search and filtering
- Metric queries and dashboards
- Incident management
- APM trace analysis
- Error tracking, feature flags, DBM, security, LLM observability
```

**Acceptance**: Datadog documented in README

### T12: Update Skill Count in README
**File**: `README.md`
**Action**: Update total skill count (+4 skills)

**Acceptance**: Skill count accurate

---

## P2: UI Integration

### T13: Add Datadog to UI INTEGRATION_CATALOG
**File**: `ui/netclaw-visual/server.js`
**Action**: Add Datadog integration entry

```javascript
{
  id: 'datadog',
  name: 'Datadog',
  category: 'Observability',
  prefixes: ['datadog-'],
  color: '#632ca6',
  transport: 'remote',
  toolEstimate: 16,
  skills: ['datadog-logs', 'datadog-metrics', 'datadog-incidents', 'datadog-apm']
}
```

**Also update ENV_MAP**:
```javascript
'datadog': ['DD_API_KEY', 'DD_APP_KEY', 'DD_SITE']
```

**Acceptance**: Datadog appears in UI integration catalog

---

## Dependency Graph

```
T1 (MCP registration) ──┬──> T3, T4, T5, T6 (Skills)
T2 (env variables)     │
                       └──> T7 (install.sh)
                            │
T3, T4, T5, T6 ────────────> T8 (SOUL.md)
                            │
T8 ────────────────────────> T9, T10, T11, T12 (README)
                            │
T9 ────────────────────────> T13 (UI)
```

## Verification Checklist

- [ ] Datadog MCP endpoint reachable
- [ ] Server appears in `openclaw list`
- [ ] All 4 skills invocable
- [ ] Skills appear in SOUL.md
- [ ] Datadog in README integrations
- [ ] Datadog in UI catalog
- [ ] Tool count updated
- [ ] Skill count updated
