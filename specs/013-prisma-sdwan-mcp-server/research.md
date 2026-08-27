# Research: Prisma SD-WAN MCP Server Integration

**Feature**: 013-prisma-sdwan-mcp-server
**Date**: 2026-04-03

## Research Topics

### 1. Community MCP Server Capabilities

**Decision**: Use the community MCP server from https://github.com/iamdheerajdubey/prisma-sdwan-mcp

**Rationale**: The community server provides comprehensive read-only access to Prisma SD-WAN with 15+ tools covering all required functionality (sites, elements, interfaces, routing, policies, alarms, events). It follows MCP standards and uses the official `prisma_sase` SDK for authentication.

**Alternatives Considered**:
- Build custom MCP server: Rejected — duplicates existing work, higher maintenance burden
- Direct REST API integration: Rejected — violates MCP-native integration principle (Constitution V)

### 2. Authentication Method

**Decision**: OAuth2 via `prisma_sase` SDK with service account credentials

**Rationale**: The community server implements OAuth2 authentication with automatic token refresh (15 minutes before expiration). This follows Palo Alto Networks' recommended authentication pattern for programmatic access.

**Required Credentials**:
- `PAN_CLIENT_ID`: Service account client ID (format: `name@tsg.iam.panserviceaccount.com`)
- `PAN_CLIENT_SECRET`: Service account secret key
- `PAN_TSG_ID`: Tenant Service Group ID
- `PAN_REGION`: Optional; `americas` (default) or `europe`

**Alternatives Considered**:
- API key authentication: Not supported by Prisma SASE API
- User/password auth: Not recommended for service accounts

### 3. MCP Server Transport

**Decision**: Use stdio transport for local integration

**Rationale**: Consistent with other MCP server integrations in NetGeniusClaw (CML, GNS3, GitLab, etc.). The community server supports stdio, SSE, and streamable HTTP — stdio is the standard for OpenClaw/the agent Desktop integration.

**Alternatives Considered**:
- SSE transport: Useful for remote/web agents, not needed for local NetGeniusClaw
- Streamable HTTP: Alternative to SSE, same considerations

### 4. Installation Pattern

**Decision**: Clone community repo via install.sh, add to .gitignore exceptions

**Rationale**: Follows the established pattern for community MCP servers (GitLab, Jenkins, Atlassian). The server is cloned to `mcp-servers/prisma-sdwan-mcp/` and registered in openclaw.json.

**Install Steps**:
1. Clone repo to `mcp-servers/prisma-sdwan-mcp/`
2. Install dependencies: `pip install prisma-sase` (or use server's requirements.txt)
3. Add .gitignore exception: `!mcp-servers/prisma-sdwan-mcp/`
4. Register in `config/openclaw.json`

### 5. Skill Organization

**Decision**: 4 skills organized by operational domain

**Rationale**: Groups related tools by use case, making it easier for users to discover and invoke relevant capabilities. Each skill focuses on a specific operational concern.

| Skill | Tools | Purpose |
|-------|-------|---------|
| `prisma-sdwan-topology` | get_sites, get_elements, get_machines, get_topology | Discover fabric structure |
| `prisma-sdwan-status` | get_element_status, get_software_status, get_events, get_alarms | Monitor health/issues |
| `prisma-sdwan-config` | get_interfaces, get_wan_interfaces, get_bgp_peers, get_static_routes, get_policy_sets, get_security_zones, generate_site_config | Inspect configuration |
| `prisma-sdwan-apps` | get_app_defs | Application visibility |

**Alternatives Considered**:
- Single skill with all tools: Rejected — too broad, violates modularity principle
- One skill per tool: Rejected — too granular, poor discoverability

### 6. Regional API Endpoints

**Decision**: Support both Americas and Europe regions via `PAN_REGION` environment variable

**Rationale**: Prisma SASE has regional API endpoints. The community server supports this via the `PAN_REGION` variable (defaults to `americas`). European customers must set `PAN_REGION=europe`.

**API Endpoints**:
- Americas: `api.sase.paloaltonetworks.com`
- Europe: `api.eu.sase.paloaltonetworks.com`

### 7. Error Handling

**Decision**: Surface API errors with clear remediation guidance

**Rationale**: Per spec FR-020 and SC-006, authentication errors and API failures should provide actionable guidance. The community server returns structured JSON errors suitable for LLM consumption.

**Common Error Scenarios**:
- Invalid credentials → Prompt to check PAN_CLIENT_ID, PAN_CLIENT_SECRET
- Expired token → Automatic refresh (handled by SDK)
- Network unreachable → Check connectivity to api.sase.paloaltonetworks.com
- Site/element not found → List available sites/elements

### 8. GAIT Audit Integration

**Decision**: Log all tool invocations via existing GAIT decorator pattern

**Rationale**: Per Constitution IV, all operations must be audited. NetGeniusClaw's existing GAIT integration can wrap MCP tool calls, similar to other MCP servers.

**Logged Information**:
- Tool name and parameters
- Timestamp and session ID
- Success/failure status
- Response summary (not full payload for large responses)

## Open Questions (Resolved)

All research questions have been resolved. No NEEDS CLARIFICATION items remain.

## References

- Community MCP Server: https://github.com/iamdheerajdubey/prisma-sdwan-mcp
- Prisma SASE API Documentation: https://pan.dev/sase/docs/
- prisma_sase SDK: https://pypi.org/project/prisma-sase/
