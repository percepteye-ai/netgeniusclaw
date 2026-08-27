# Research: Zscaler MCP Server Integration

**Feature**: 020-zscaler-mcp-server | **Date**: 2026-04-04

## Research Tasks

### RT1: Official Zscaler MCP Server Evaluation

**Decision**: Use official Zscaler MCP server

**Rationale**:
- Maintained by Zscaler (official repository)
- MIT licensed
- Comprehensive coverage of all Zscaler services
- 300+ tools covering entire Zero Trust platform
- Active development with regular updates

**Alternatives Considered**:
| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| Official zscaler-mcp-server | Full coverage, official | Large binary | Selected |
| Individual service wrappers | Smaller footprint | Maintenance burden | Rejected |
| Custom implementation | Full control | Massive API surface | Rejected |

### RT2: Installation Method

**Decision**: Go binary (go install or pre-built binary)

**Rationale**:
- Official distribution method
- Single binary with all services
- Multi-transport support (stdio, SSE, StreamableHTTP)
- Cross-platform support

**Installation Options**:
```bash
# Go install
go install github.com/zscaler/zscaler-mcp-server@latest

# Pre-built binary
curl -LO https://github.com/zscaler/zscaler-mcp-server/releases/latest/download/zscaler-mcp-server_linux_amd64.tar.gz
```

### RT3: Service Configuration

**Decision**: Enable ALL 9 services

**Rationale**:
- User preference from clarification session
- Maximum capability for Zero Trust management
- Read-only tools always safe
- Write tools require explicit enablement

**Enabled Services**:
| Service | Tools | Description |
|---------|-------|-------------|
| ZIA | 106 | Internet Access |
| ZPA | 88 | Private Access |
| ZDX | 31 | Digital Experience |
| ZMS | 20 | Microsegmentation |
| ZTW | 19 | Workload Segmentation |
| Z-Insights | 16 | Analytics |
| ZIdentity | 10 | Identity Management |
| EASM | 7 | Attack Surface |
| ZCC | 4 | Client Connector |

### RT4: Authentication Method

**Decision**: OneAPI OAuth credentials via environment variables

**Rationale**:
- Modern OAuth2 authentication
- Single credential set for all services
- Supports customer multi-tenancy
- Standard Zscaler recommended approach

**Required Variables**:
- `ZSCALER_CLIENT_ID`: OAuth client ID
- `ZSCALER_CLIENT_SECRET`: OAuth client secret
- `ZSCALER_CUSTOMER_ID`: Customer identifier
- `ZSCALER_VANITY_DOMAIN`: Organization domain

### RT5: Skill Organization

**Decision**: 5 focused skills covering primary use cases

**Rationale**:
- ZPA: Private application access (20 tools)
- ZIA: Internet security (20 tools)
- ZDX: Experience monitoring (10 tools)
- Identity: User and connector management (8 tools)
- Insights: Analytics and intelligence (6 tools)

**Tool Distribution**:
| Skill | Tools | Primary Focus |
|-------|-------|---------------|
| zscaler-zpa | 20 | Application segments, policies, connectors |
| zscaler-zia | 20 | Firewall rules, URL filtering, DLP |
| zscaler-zdx | 10 | User experience, application performance |
| zscaler-identity | 8 | Users, groups, IdP configuration |
| zscaler-insights | 6 | Analytics, threat intelligence |

Note: Remaining tools (200+) available via direct tool invocation.

## Security Considerations

### Write Operation Gating
- Write tools disabled by default
- Requires `ZSCALER_MCP_WRITE_ENABLED=true`
- Optional allowlist via `ZSCALER_MCP_WRITE_TOOLS`
- ServiceNow CR for production changes

### Delete Operation Protection
- Delete operations require cryptographic confirmation
- Confirmation token generated per-request
- Prevents accidental deletions

## Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| zscaler-mcp-server | latest | Official MCP server |
| Go | 1.21+ | Server runtime |
| Zscaler OneAPI | - | Backend APIs |

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Large tool count confusion | Medium | Low | Focused skill organization |
| OAuth token expiration | Low | Medium | Auto-refresh built-in |
| Write operation misuse | Low | High | Disabled by default, allowlist |
| API rate limiting | Medium | Low | Zscaler has generous limits |

## Open Questions Resolved

All research tasks completed. No blocking unknowns remain.
