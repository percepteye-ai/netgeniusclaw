# Tasks: Zscaler MCP Server Integration

**Feature**: 020-zscaler-mcp-server | **Date**: 2026-04-04
**Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

## Task Overview

| Category | Tasks | Priority |
|----------|-------|----------|
| MCP Registration | 2 | P0 |
| Skills | 5 | P1 |
| Configuration | 2 | P1 |
| Documentation | 4 | P2 |
| UI Integration | 1 | P2 |

---

## P0: MCP Server Registration

### T1: Register Zscaler MCP Server in openclaw.json
**File**: `config/openclaw.json`
**Action**: Add MCP server configuration

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

**Acceptance**: Server appears in `openclaw list` output

### T2: Add Environment Variables to .env.example
**File**: `.env.example`
**Action**: Add Zscaler environment variables

```bash
# Zscaler MCP Server - OneAPI Authentication
ZSCALER_CLIENT_ID=your_client_id
ZSCALER_CLIENT_SECRET=your_client_secret
ZSCALER_CUSTOMER_ID=your_customer_id
ZSCALER_VANITY_DOMAIN=yourcompany

# All 9 services enabled
ZSCALER_MCP_SERVICES=zia,zpa,zdx,zms,ztw,zinsights,zidentity,easm,zcc

# Optional: Enable write operations (disabled by default)
# ZSCALER_MCP_WRITE_ENABLED=true
```

**Acceptance**: Variables documented with comments

---

## P1: Skill Creation

### T3: Create zscaler-zpa Skill
**File**: `workspace/skills/zscaler-zpa/SKILL.md`
**Action**: Create skill documentation

**Content Requirements**:
- Skill name and description
- Tool list: list_application_segments, get_application_segment, list_segment_groups, list_access_policies, get_access_policy, list_app_connectors, list_connector_groups, list_server_groups, create_application_segment, update_application_segment, delete_application_segment, etc.
- Example queries
- Prerequisites

**Acceptance**: Skill invocable via `/zscaler-zpa`

### T4: Create zscaler-zia Skill
**File**: `workspace/skills/zscaler-zia/SKILL.md`
**Action**: Create skill documentation

**Content Requirements**:
- Skill name and description
- Tool list: list_firewall_rules, get_firewall_rule, list_url_filtering_rules, list_dlp_dictionaries, list_url_categories, list_locations, create_firewall_rule, etc.
- Example queries
- Prerequisites

**Acceptance**: Skill invocable via `/zscaler-zia`

### T5: Create zscaler-zdx Skill
**File**: `workspace/skills/zscaler-zdx/SKILL.md`
**Action**: Create skill documentation

**Content Requirements**:
- Skill name and description
- Tool list: list_zdx_applications, get_zdx_application, list_zdx_users, get_zdx_user, list_zdx_devices, get_zdx_score_trends, list_zdx_events, list_zdx_alerts
- Example queries (score analysis, user experience)
- Prerequisites

**Acceptance**: Skill invocable via `/zscaler-zdx`

### T6: Create zscaler-identity Skill
**File**: `workspace/skills/zscaler-identity/SKILL.md`
**Action**: Create skill documentation

**Content Requirements**:
- Skill name and description
- Tool list: list_users, get_user, list_groups, get_group, list_departments, get_department, list_idp_configs, get_idp_config
- Example queries
- Prerequisites

**Acceptance**: Skill invocable via `/zscaler-identity`

### T7: Create zscaler-insights Skill
**File**: `workspace/skills/zscaler-insights/SKILL.md`
**Action**: Create skill documentation

**Content Requirements**:
- Skill name and description
- Tool list: get_threat_intelligence, list_security_events, get_security_event, list_blocked_threats, get_traffic_analytics, list_anomalies
- Example queries
- Prerequisites

**Acceptance**: Skill invocable via `/zscaler-insights`

---

## P1: Configuration Updates

### T8: Update install.sh with Zscaler Dependencies
**File**: `scripts/install.sh`
**Action**: Add Go/zscaler-mcp-server installation

```bash
# Zscaler MCP Server
if command -v zscaler-mcp-server &> /dev/null; then
    echo "✓ zscaler-mcp-server installed"
else
    echo "⚠ Install zscaler-mcp-server:"
    echo "  go install github.com/zscaler/zscaler-mcp-server@latest"
fi
```

**Acceptance**: Installation script checks for dependencies

### T9: Update SOUL.md Skill Index
**File**: `SOUL.md`
**Action**: Add Zscaler skills to index

```markdown
### Zero Trust Security
- `/zscaler-zpa` - Private Access applications and policies
- `/zscaler-zia` - Internet Access firewall and filtering
- `/zscaler-zdx` - Digital Experience monitoring
- `/zscaler-identity` - User and group management
- `/zscaler-insights` - Analytics and threat intelligence
```

**Acceptance**: Skills appear in SOUL.md index

---

## P2: Documentation Updates

### T10: Update README.md Architecture Section
**File**: `README.md`
**Action**: Add Zscaler to MCP server count and integration list

- Update total MCP server count
- Add Zscaler to integrations table
- Update tool count (+300 tools!)

**Acceptance**: README reflects new integration

### T11: Update README.md Tool Count
**File**: `README.md`
**Action**: Update total tool count (+300 tools)

**Acceptance**: Tool count accurate

### T12: Create Zscaler Section in README
**File**: `README.md`
**Action**: Add Zscaler integration description

```markdown
### Zscaler (300+ tools)
Comprehensive Zero Trust security management across all 9 services.
- ZPA: Private Access applications and policies (88 tools)
- ZIA: Internet Access firewall and filtering (106 tools)
- ZDX: Digital Experience monitoring (31 tools)
- ZMS/ZTW: Microsegmentation and workload protection
- Z-Insights: Analytics and threat intelligence
- ZIdentity: Identity and access management
- EASM: External Attack Surface Management
- ZCC: Client Connector management
```

**Acceptance**: Zscaler documented in README

### T13: Update Skill Count in README
**File**: `README.md`
**Action**: Update total skill count (+5 skills)

**Acceptance**: Skill count accurate

---

## P2: UI Integration

### T14: Add Zscaler to UI INTEGRATION_CATALOG
**File**: `ui/netclaw-visual/server.js`
**Action**: Add Zscaler integration entry

```javascript
{
  id: 'zscaler',
  name: 'Zscaler',
  category: 'Zero Trust Security',
  prefixes: ['zscaler-'],
  color: '#0078d4',
  transport: 'stdio',
  toolEstimate: 300,
  skills: ['zscaler-zpa', 'zscaler-zia', 'zscaler-zdx', 'zscaler-identity', 'zscaler-insights']
}
```

**Also update ENV_MAP**:
```javascript
'zscaler': ['ZSCALER_CLIENT_ID', 'ZSCALER_CLIENT_SECRET', 'ZSCALER_CUSTOMER_ID', 'ZSCALER_VANITY_DOMAIN', 'ZSCALER_MCP_SERVICES']
```

**Acceptance**: Zscaler appears in UI integration catalog

---

## Dependency Graph

```
T1 (MCP registration) ──┬──> T3, T4, T5, T6, T7 (Skills)
T2 (env variables)     │
                       └──> T8 (install.sh)
                            │
T3-T7 ─────────────────────> T9 (SOUL.md)
                            │
T9 ────────────────────────> T10, T11, T12, T13 (README)
                            │
T10 ───────────────────────> T14 (UI)
```

## Verification Checklist

- [ ] `zscaler-mcp-server --help` works
- [ ] Server appears in `openclaw list`
- [ ] All 5 skills invocable
- [ ] Skills appear in SOUL.md
- [ ] Zscaler in README integrations
- [ ] Zscaler in UI catalog
- [ ] Tool count updated (+300)
- [ ] Skill count updated (+5)
