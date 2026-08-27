# Research: HashiCorp Vault MCP Server Integration

**Feature**: 019-vault-mcp-server | **Date**: 2026-04-04

## Research Tasks

### RT1: Official Vault MCP Server Evaluation

**Decision**: Use official HashiCorp Vault MCP server

**Rationale**:
- Maintained by HashiCorp (official repository)
- MPL-2.0 licensed (standard HashiCorp license)
- Comprehensive toolset covering KV and PKI
- Built-in security protections
- Integrates with Vault Enterprise features

**Alternatives Considered**:
| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| Official vault-mcp-server | Full feature set, official | Requires Go runtime | Selected |
| Custom FastMCP server | Full control | Security risk | Rejected |
| Vault CLI wrapper | Simple | No secret protection | Rejected |

### RT2: Installation Method

**Decision**: Go binary (go install or pre-built binary)

**Rationale**:
- Official distribution method from HashiCorp
- Single binary, no dependencies
- Easy updates via go install
- Cross-platform support

**Installation Options**:
```bash
# Go install
go install github.com/hashicorp/vault-mcp-server@latest

# Pre-built binary
curl -LO https://releases.hashicorp.com/vault-mcp-server/latest/vault-mcp-server_linux_amd64.zip
```

### RT3: Secret Display Policy

**Decision**: Never display secret values (only confirm existence)

**Rationale**:
- User preference from clarification session (Option C)
- Secrets injected directly to integrations
- Prevents accidental exposure in logs/output
- Aligns with zero-trust security model

**Output Behavior**:
| Operation | Returns |
|-----------|---------|
| read_secret | `{exists: true, keys: [...], version: n}` |
| write_secret | `{success: true, version: n}` |
| issue_pki_certificate | Certificate injected to target, path returned |

### RT4: Authentication Method

**Decision**: VAULT_TOKEN via environment variable

**Rationale**:
- Standard Vault authentication method
- Token stored in VAULT_TOKEN environment variable
- Supports all token types (root, service, batch)
- Enterprise namespace support via VAULT_NAMESPACE

**Policy Requirements**:
```hcl
# Minimum policy for network credentials
path "secret/data/network/*" {
  capabilities = ["read", "list"]
}
path "pki/issue/network-devices" {
  capabilities = ["update"]
}
```

### RT5: Skill Organization

**Decision**: 3 focused skills aligned with Vault domains

**Rationale**:
- Secrets: KV operations (4 tools)
- PKI: Certificate management (6 tools)
- Mounts: Discovery and management (3 tools)

**Tool Distribution**:
| Skill | Tools | Description |
|-------|-------|-------------|
| vault-secrets | 4 | read_secret, write_secret, list_secrets, delete_secret |
| vault-pki | 6 | enable_pki, create_pki_issuer, create_pki_role, issue_pki_certificate, etc. |
| vault-mounts | 3 | list_mounts, create_mount, delete_mount |

## Security Considerations

### Secret Value Protection
- Secret values NEVER appear in output
- Values injected directly to integrations
- Only metadata (exists, version, keys) returned
- Audit logging enabled in Vault

### Token Management
- Use minimum required policies
- Token rotation recommended
- Periodic tokens for automated workflows
- Orphan tokens to prevent inheritance

## Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| vault-mcp-server | latest | Official MCP server |
| Vault | 1.x+ | Secrets backend |
| Go | 1.21+ | Server runtime |

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Token exposure | Low | Critical | Environment variable, never logged |
| Over-permissioned token | Medium | High | Minimum policy documentation |
| Certificate misuse | Low | Medium | TTL limits, role constraints |
| Secret overwrite | Low | Medium | Write confirmation required |

## Open Questions Resolved

All research tasks completed. No blocking unknowns remain.
