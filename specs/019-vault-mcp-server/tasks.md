# Tasks: HashiCorp Vault MCP Server Integration

**Feature**: 019-vault-mcp-server | **Date**: 2026-04-04
**Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

## Task Overview

| Category | Tasks | Priority |
|----------|-------|----------|
| MCP Registration | 2 | P0 |
| Skills | 3 | P1 |
| Configuration | 2 | P1 |
| Documentation | 4 | P2 |
| UI Integration | 1 | P2 |

---

## P0: MCP Server Registration

### T1: Register Vault MCP Server in openclaw.json
**File**: `config/openclaw.json`
**Action**: Add MCP server configuration

```json
{
  "vault-mcp": {
    "command": "vault-mcp-server",
    "args": [],
    "env": {
      "VAULT_ADDR": "${VAULT_ADDR}",
      "VAULT_TOKEN": "${VAULT_TOKEN}",
      "VAULT_NAMESPACE": "${VAULT_NAMESPACE}"
    }
  }
}
```

**Acceptance**: Server appears in `openclaw list` output

### T2: Add Environment Variables to .env.example
**File**: `.env.example`
**Action**: Add Vault environment variables

```bash
# Vault MCP Server
VAULT_ADDR=https://vault.example.com:8200
VAULT_TOKEN=hvs.your_vault_token
# VAULT_NAMESPACE=network-ops  # For Enterprise namespaces
```

**Acceptance**: Variables documented with comments

---

## P1: Skill Creation

### T3: Create vault-secrets Skill
**File**: `workspace/skills/vault-secrets/SKILL.md`
**Action**: Create skill documentation

**Content Requirements**:
- Skill name and description
- Tool list: read_secret, write_secret, list_secrets, delete_secret
- **CRITICAL**: Note that secret values are NEVER displayed (per clarification)
- Example queries (with inject_to parameter)
- Prerequisites

**Acceptance**: Skill invocable via `/vault-secrets`

### T4: Create vault-pki Skill
**File**: `workspace/skills/vault-pki/SKILL.md`
**Action**: Create skill documentation

**Content Requirements**:
- Skill name and description
- Tool list: enable_pki, create_pki_issuer, list_pki_issuers, create_pki_role, list_pki_roles, issue_pki_certificate
- Certificate issuance examples
- Prerequisites

**Acceptance**: Skill invocable via `/vault-pki`

### T5: Create vault-mounts Skill
**File**: `workspace/skills/vault-mounts/SKILL.md`
**Action**: Create skill documentation

**Content Requirements**:
- Skill name and description
- Tool list: list_mounts, create_mount, delete_mount
- Example queries
- Prerequisites

**Acceptance**: Skill invocable via `/vault-mounts`

---

## P1: Configuration Updates

### T6: Update install.sh with Vault Dependencies
**File**: `scripts/install.sh`
**Action**: Add Go/vault-mcp-server installation

```bash
# Vault MCP Server
if command -v vault-mcp-server &> /dev/null; then
    echo "✓ vault-mcp-server installed"
else
    echo "⚠ Install vault-mcp-server:"
    echo "  go install github.com/hashicorp/vault-mcp-server@latest"
fi
```

**Acceptance**: Installation script checks for dependencies

### T7: Update SOUL.md Skill Index
**File**: `SOUL.md`
**Action**: Add Vault skills to index

```markdown
### Secrets Management
- `/vault-secrets` - KV secret operations (values never displayed)
- `/vault-pki` - PKI certificate management
- `/vault-mounts` - Secret engine discovery
```

**Acceptance**: Skills appear in SOUL.md index

---

## P2: Documentation Updates

### T8: Update README.md Architecture Section
**File**: `README.md`
**Action**: Add Vault to MCP server count and integration list

- Update total MCP server count
- Add Vault to integrations table
- Update tool count

**Acceptance**: README reflects new integration

### T9: Update README.md Tool Count
**File**: `README.md`
**Action**: Update total tool count (+15 tools)

**Acceptance**: Tool count accurate

### T10: Create Vault Section in README
**File**: `README.md`
**Action**: Add Vault integration description

```markdown
### HashiCorp Vault (15+ tools)
Secrets management with strict value protection.
- KV secret operations (values never displayed)
- PKI certificate issuance
- Secret engine management
- Secrets injected directly to integrations
```

**Acceptance**: Vault documented in README

### T11: Update Skill Count in README
**File**: `README.md`
**Action**: Update total skill count (+3 skills)

**Acceptance**: Skill count accurate

---

## P2: UI Integration

### T12: Add Vault to UI INTEGRATION_CATALOG
**File**: `ui/netclaw-visual/server.js`
**Action**: Add Vault integration entry

```javascript
{
  id: 'vault',
  name: 'HashiCorp Vault',
  category: 'Secrets Management',
  prefixes: ['vault-'],
  color: '#000000',
  transport: 'stdio',
  toolEstimate: 15,
  skills: ['vault-secrets', 'vault-pki', 'vault-mounts']
}
```

**Also update ENV_MAP**:
```javascript
'vault': ['VAULT_ADDR', 'VAULT_TOKEN', 'VAULT_NAMESPACE']
```

**Acceptance**: Vault appears in UI integration catalog

---

## Dependency Graph

```
T1 (MCP registration) ──┬──> T3, T4, T5 (Skills)
T2 (env variables)     │
                       └──> T6 (install.sh)
                            │
T3, T4, T5 ────────────────> T7 (SOUL.md)
                            │
T7 ────────────────────────> T8, T9, T10, T11 (README)
                            │
T8 ────────────────────────> T12 (UI)
```

## Verification Checklist

- [ ] `vault-mcp-server --help` works
- [ ] Server appears in `openclaw list`
- [ ] All 3 skills invocable
- [ ] Secret values confirmed NOT displayed
- [ ] Skills appear in SOUL.md
- [ ] Vault in README integrations
- [ ] Vault in UI catalog
- [ ] Tool count updated
- [ ] Skill count updated
