# Tasks: Cloudflare MCP Server Integration

**Feature**: 021-cloudflare-mcp-server | **Date**: 2026-04-04
**Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

## Task Overview

| Category | Tasks | Priority |
|----------|-------|----------|
| MCP Registration | 6 | P0 |
| Skills | 5 | P1 |
| Configuration | 2 | P1 |
| Documentation | 4 | P2 |
| UI Integration | 1 | P2 |

---

## P0: MCP Server Registration (Multiple Remote Servers)

### T1: Register Cloudflare DNS Analytics Server in openclaw.json
**File**: `config/openclaw.json`
**Action**: Add remote MCP server configuration

```json
{
  "cloudflare-dns-analytics": {
    "transport": "remote",
    "url": "dns-analytics.mcp.cloudflare.com",
    "env": {
      "CLOUDFLARE_API_TOKEN": "${CLOUDFLARE_API_TOKEN}",
      "CLOUDFLARE_ACCOUNT_ID": "${CLOUDFLARE_ACCOUNT_ID}"
    }
  }
}
```

**Acceptance**: Server appears in `openclaw list` output

### T2: Register Cloudflare Observability Server
**File**: `config/openclaw.json`
**Action**: Add remote MCP server configuration

```json
{
  "cloudflare-observability": {
    "transport": "remote",
    "url": "observability.mcp.cloudflare.com",
    "env": {
      "CLOUDFLARE_API_TOKEN": "${CLOUDFLARE_API_TOKEN}",
      "CLOUDFLARE_ACCOUNT_ID": "${CLOUDFLARE_ACCOUNT_ID}"
    }
  }
}
```

**Acceptance**: Server reachable

### T3: Register Cloudflare Audit Logs Server
**File**: `config/openclaw.json`
**Action**: Add remote MCP server configuration

```json
{
  "cloudflare-audit-logs": {
    "transport": "remote",
    "url": "audit-logs.mcp.cloudflare.com",
    "env": {
      "CLOUDFLARE_API_TOKEN": "${CLOUDFLARE_API_TOKEN}",
      "CLOUDFLARE_ACCOUNT_ID": "${CLOUDFLARE_ACCOUNT_ID}"
    }
  }
}
```

**Acceptance**: Server reachable

### T4: Register Cloudflare CASB Server
**File**: `config/openclaw.json`
**Action**: Add remote MCP server configuration

```json
{
  "cloudflare-casb": {
    "transport": "remote",
    "url": "casb.mcp.cloudflare.com",
    "env": {
      "CLOUDFLARE_API_TOKEN": "${CLOUDFLARE_API_TOKEN}",
      "CLOUDFLARE_ACCOUNT_ID": "${CLOUDFLARE_ACCOUNT_ID}"
    }
  }
}
```

**Acceptance**: Server reachable

### T5: Register Cloudflare Radar Server
**File**: `config/openclaw.json`
**Action**: Add remote MCP server configuration

```json
{
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

**Acceptance**: Server reachable

### T6: Add Environment Variables to .env.example
**File**: `.env.example`
**Action**: Add Cloudflare environment variables

```bash
# Cloudflare MCP Servers
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
CLOUDFLARE_ACCOUNT_ID=your_account_id
# CLOUDFLARE_ZONE_ID=your_zone_id  # Optional default zone
```

**Acceptance**: Variables documented with comments

---

## P1: Skill Creation

### T7: Create cloudflare-dns Skill
**File**: `workspace/skills/cloudflare-dns/SKILL.md`
**Action**: Create skill documentation

**Content Requirements**:
- Skill name and description
- Tool list: list_zones, get_zone, list_dns_records, get_dns_analytics, get_dns_performance, get_dns_trends
- Example queries (zone listing, record queries)
- Prerequisites

**Acceptance**: Skill invocable via `/cloudflare-dns`

### T8: Create cloudflare-zerotrust Skill
**File**: `workspace/skills/cloudflare-zerotrust/SKILL.md`
**Action**: Create skill documentation

**Content Requirements**:
- Skill name and description
- Tool list: list_access_applications, get_access_application, list_access_policies, get_access_policy, list_tunnels, get_tunnel, list_casb_findings, get_casb_finding
- Example queries
- Prerequisites

**Acceptance**: Skill invocable via `/cloudflare-zerotrust`

### T9: Create cloudflare-analytics Skill
**File**: `workspace/skills/cloudflare-analytics/SKILL.md`
**Action**: Create skill documentation

**Content Requirements**:
- Skill name and description
- Tool list: get_zone_analytics, search_logs, get_traffic_insights, scan_url, get_threat_intel, get_internet_trends
- Example queries (Radar insights, URL scanning)
- Prerequisites

**Acceptance**: Skill invocable via `/cloudflare-analytics`

### T10: Create cloudflare-workers Skill
**File**: `workspace/skills/cloudflare-workers/SKILL.md`
**Action**: Create skill documentation

**Content Requirements**:
- Skill name and description
- Tool list: list_workers, get_worker, get_worker_bindings, list_builds, get_build, get_worker_analytics
- Example queries
- Prerequisites

**Acceptance**: Skill invocable via `/cloudflare-workers`

### T11: Create cloudflare-security Skill
**File**: `workspace/skills/cloudflare-security/SKILL.md`
**Action**: Create skill documentation

**Content Requirements**:
- Skill name and description
- Tool list: list_firewall_rules, get_firewall_events, list_audit_logs, get_audit_log, list_security_events, get_threat_score
- Example queries
- Prerequisites

**Acceptance**: Skill invocable via `/cloudflare-security`

---

## P1: Configuration Updates

### T12: Update install.sh with Cloudflare Requirements
**File**: `scripts/install.sh`
**Action**: Add Cloudflare connectivity check

```bash
# Cloudflare MCP Servers (Remote)
echo "ℹ Cloudflare MCP uses remote transport - no local installation required"
echo "  Domain-specific servers: dns-analytics, observability, audit-logs, casb, radar"
echo "  Ensure CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID are configured"
```

**Acceptance**: Installation script documents remote transport

### T13: Update SOUL.md Skill Index
**File**: `SOUL.md`
**Action**: Add Cloudflare skills to index

```markdown
### Edge Security & CDN
- `/cloudflare-dns` - DNS zone and record management
- `/cloudflare-zerotrust` - Zero Trust access and tunnels
- `/cloudflare-analytics` - Traffic and Radar insights
- `/cloudflare-workers` - Workers deployment and monitoring
- `/cloudflare-security` - WAF, audit, and threat analysis
```

**Acceptance**: Skills appear in SOUL.md index

---

## P2: Documentation Updates

### T14: Update README.md Architecture Section
**File**: `README.md`
**Action**: Add Cloudflare to MCP server count and integration list

- Update total MCP server count (+5 remote servers)
- Add Cloudflare to integrations table
- Update tool count

**Acceptance**: README reflects new integration

### T15: Update README.md Tool Count
**File**: `README.md`
**Action**: Update total tool count (+32 tools)

**Acceptance**: Tool count accurate

### T16: Create Cloudflare Section in README
**File**: `README.md`
**Action**: Add Cloudflare integration description

```markdown
### Cloudflare (32+ tools via 5 domain-specific servers)
Edge security, DNS, and Zero Trust capabilities.
- DNS zone and record management with analytics
- Zero Trust Access applications and tunnels
- CASB SaaS security findings
- Radar global Internet insights
- Traffic analytics and log search
```

**Acceptance**: Cloudflare documented in README

### T17: Update Skill Count in README
**File**: `README.md`
**Action**: Update total skill count (+5 skills)

**Acceptance**: Skill count accurate

---

## P2: UI Integration

### T18: Add Cloudflare to UI INTEGRATION_CATALOG
**File**: `ui/netclaw-visual/server.js`
**Action**: Add Cloudflare integration entry

```javascript
{
  id: 'cloudflare',
  name: 'Cloudflare',
  category: 'Edge Security & CDN',
  prefixes: ['cloudflare-'],
  color: '#f38020',
  transport: 'remote',
  toolEstimate: 32,
  skills: ['cloudflare-dns', 'cloudflare-zerotrust', 'cloudflare-analytics', 'cloudflare-workers', 'cloudflare-security']
}
```

**Also update ENV_MAP**:
```javascript
'cloudflare': ['CLOUDFLARE_API_TOKEN', 'CLOUDFLARE_ACCOUNT_ID', 'CLOUDFLARE_ZONE_ID']
```

**Acceptance**: Cloudflare appears in UI integration catalog

---

## Dependency Graph

```
T1-T5 (MCP registrations) ──┬──> T7-T11 (Skills)
T6 (env variables)         │
                           └──> T12 (install.sh)
                                │
T7-T11 ────────────────────────> T13 (SOUL.md)
                                │
T13 ───────────────────────────> T14, T15, T16, T17 (README)
                                │
T14 ───────────────────────────> T18 (UI)
```

## Verification Checklist

- [ ] All 5 Cloudflare MCP endpoints reachable
- [ ] Servers appear in `openclaw list`
- [ ] All 5 skills invocable
- [ ] Skills appear in SOUL.md
- [ ] Cloudflare in README integrations
- [ ] Cloudflare in UI catalog
- [ ] Tool count updated (+32)
- [ ] Skill count updated (+5)
