# Research: Cloudflare MCP Server Integration

**Feature**: 021-cloudflare-mcp-server | **Date**: 2026-04-04

## Research Tasks

### RT1: Cloudflare MCP Architecture Evaluation

**Decision**: Use domain-specific MCP servers only

**Rationale**:
- User preference from clarification session (Option B)
- Domain-specific servers provide focused, well-defined tools
- No risk of arbitrary API execution
- Better discoverability and documentation
- Aligns with principle of least privilege

**Alternatives Considered**:
| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| Domain-specific servers | Focused tools, safe | Multiple registrations | Selected |
| Unified API (execute()) | Full API access | Security risk, broad access | Rejected |
| Hybrid approach | Flexibility | Complexity | Rejected |

### RT2: Server Selection

**Decision**: Register primary domain-specific servers for network use cases

**Selected Servers**:
| Server | URL | Network Relevance |
|--------|-----|-------------------|
| Observability | observability.mcp.cloudflare.com | Log and analytics debugging |
| DNS Analytics | dns-analytics.mcp.cloudflare.com | DNS performance |
| Audit Logs | audit-logs.mcp.cloudflare.com | Security audit |
| CASB | casb.mcp.cloudflare.com | SaaS security |
| Radar | radar.mcp.cloudflare.com | Traffic intelligence |
| Digital Experience | dex.mcp.cloudflare.com | Application insights |
| Logpush | logpush.mcp.cloudflare.com | Log management |

### RT3: Connection Method

**Decision**: Remote MCP via mcp-remote

**Rationale**:
- Cloudflare provides managed MCP endpoints
- mcp-remote handles authentication and transport
- No local installation required
- Automatic updates from Cloudflare

**Configuration Pattern**:
```json
{
  "cloudflare-dns": {
    "transport": "remote",
    "url": "dns-analytics.mcp.cloudflare.com",
    "env": {
      "CLOUDFLARE_API_TOKEN": "${CLOUDFLARE_API_TOKEN}",
      "CLOUDFLARE_ACCOUNT_ID": "${CLOUDFLARE_ACCOUNT_ID}"
    }
  }
}
```

### RT4: Authentication Method

**Decision**: API Token via environment variable

**Rationale**:
- Cloudflare recommends API tokens over Global API Key
- Tokens can be scoped to specific permissions
- Standard environment variable pattern

**Required Variables**:
- `CLOUDFLARE_API_TOKEN`: Scoped API token
- `CLOUDFLARE_ACCOUNT_ID`: Account identifier
- `CLOUDFLARE_ZONE_ID`: Optional, for DNS operations

### RT5: Skill Organization

**Decision**: 5 focused skills covering primary use cases

**Rationale**:
- DNS: Zone and record management (6 tools)
- Zero Trust: Access policies and tunnels (8 tools)
- Analytics: Traffic and DNS analytics (6 tools)
- Workers: Deployment and monitoring (6 tools)
- Security: WAF, CASB, firewall (6 tools)

**Tool Distribution**:
| Skill | Servers | Tools |
|-------|---------|-------|
| cloudflare-dns | dns-analytics | 6 |
| cloudflare-zerotrust | casb, audit-logs | 8 |
| cloudflare-analytics | observability, radar | 6 |
| cloudflare-workers | workers-bindings, workers-builds | 6 |
| cloudflare-security | casb, audit-logs | 6 |

## Security Considerations

### Token Scoping
- Use minimal required permissions
- Zone-specific tokens for DNS
- Account-wide tokens for analytics only

### Write Operation Protection
- Write operations require confirmation
- Audit logs track all changes
- Zone-level permissions enforced

## Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| mcp-remote | latest | Remote MCP transport |
| Cloudflare API | v4 | Backend APIs |

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Token over-privilege | Medium | Medium | Minimum scope documentation |
| Remote service latency | Low | Low | Edge deployment |
| API changes | Low | Medium | Domain-specific servers versioned |
| Zone confusion | Medium | Medium | Require explicit zone ID |

## Open Questions Resolved

All research tasks completed. No blocking unknowns remain.
