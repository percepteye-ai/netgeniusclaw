# Research: GNS3 MCP Server

**Feature**: 012-gns3-mcp-server
**Date**: 2026-04-02
**Purpose**: Resolve technical unknowns and document design decisions

## Research Tasks Completed

### 1. GNS3 REST API v3 Structure

**Decision**: Use GNS3 REST API v3 with OAuth2 bearer token authentication

**Rationale**:
- GNS3 2.2.0+ provides a comprehensive REST API with OpenAPI specification
- API is well-documented at https://apiv3.gns3.net/
- Supports all required operations: projects, nodes, links, snapshots, computes
- OAuth2PasswordBearer authentication matches our security requirements

**Alternatives Considered**:
- GNS3 API v2 (legacy): Rejected — lacks features, deprecated
- Direct Telnet/SSH to controller: Rejected — no structured API, harder to parse

### 2. Authentication Approach

**Decision**: Auto-authentication with cached token (similar to clab-mcp-server pattern)

**Rationale**:
- GNS3 uses `POST /v3/access/users/authenticate` for JSON-based auth
- Returns bearer token for subsequent requests
- Token caching reduces auth overhead
- Matches established NetGeniusClaw pattern (clab-mcp-server uses 50 min TTL)

**API Endpoints**:
- Login: `POST /v3/access/users/authenticate` with `{"username": "...", "password": "..."}`
- Token usage: `Authorization: Bearer <token>` header
- Current user: `GET /v3/access/users/me` (verify token validity)

### 3. MCP Server Architecture

**Decision**: Monolithic server pattern with FastMCP

**Rationale**:
- Matches clab-mcp-server pattern (198 lines, single file)
- FastMCP is the standard for Python MCP servers in NetGeniusClaw
- Simpler than package-based structure for focused functionality
- All tools in single file for easier maintenance

**Alternative Considered**:
- Modular package structure (like netbox-mcp-server): Rejected — overkill for this scope

### 4. Tool Organization

**Decision**: 23 tools organized into 5 logical skill categories

**Tool Mapping**:

| Skill | Tools | GNS3 API Endpoints |
|-------|-------|-------------------|
| gns3-project-lifecycle | 9 tools | `/v3/projects/*` |
| gns3-node-operations | 7 tools | `/v3/projects/{id}/nodes/*` |
| gns3-link-management | 4 tools | `/v3/projects/{id}/links/*` |
| gns3-packet-capture | 3 tools | `/v3/projects/{id}/links/{id}/capture/*` |
| gns3-snapshot-ops | 4 tools | `/v3/projects/{id}/snapshots/*` |

**Rationale**:
- Matches user stories in spec (5 categories)
- Each skill has single responsibility
- Tools can be composed across skills as needed

### 5. HTTP Client Choice

**Decision**: Use `httpx` with async support

**Rationale**:
- Async operations for better performance
- Supports streaming for PCAP capture endpoint
- Modern Python HTTP client (used in other NetGeniusClaw servers)
- Better error handling than `requests`

**Alternative Considered**:
- `requests` library: Rejected — no async support, used in older servers

### 6. Error Handling Strategy

**Decision**: Structured error responses with GNS3 error codes

**Error Response Format**:
```json
{
  "success": false,
  "error": "Error description",
  "error_code": "GNS3_404_NOT_FOUND",
  "details": {...}
}
```

**GNS3 API Error Codes**:
- 404: Resource not found (project, node, link, snapshot)
- 409: Conflict (project locked, node already running)
- 422: Validation error (invalid parameters)
- 403: Forbidden (insufficient privileges)

### 7. GAIT Audit Integration

**Decision**: Use `@with_gait_logging` decorator pattern (like azure-network-mcp)

**Rationale**:
- Consistent with existing NetGeniusClaw pattern
- All operations logged to GAIT audit trail
- Satisfies FR-016 requirement

**Implementation**:
```python
@mcp.tool()
@with_gait_logging("gns3_create_project")
async def gns3_create_project(name: str, ...) -> str:
    ...
```

### 8. Environment Variables

**Decision**: Three required environment variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GNS3_URL` | GNS3 server URL (e.g., `http://localhost:3080`) | Yes |
| `GNS3_USER` | Username for authentication | Yes |
| `GNS3_PASSWORD` | Password for authentication | Yes |

**Optional Variables**:
| Variable | Description | Default |
|----------|-------------|---------|
| `GNS3_VERIFY_SSL` | Verify SSL certificates | `true` |
| `GNS3_TOKEN_TTL` | Token cache TTL in seconds | `3000` (50 min) |

### 9. Node Creation from Templates

**Decision**: Use template-based node creation with fuzzy matching

**API Flow**:
1. List templates: `GET /v3/templates`
2. Match template by name (case-insensitive, partial match)
3. Create node from template: `POST /v3/projects/{project_id}/templates/{template_id}`

**Rationale**:
- Users can say "add a Cisco IOSv router" without knowing exact template ID
- Fuzzy matching improves usability
- Matches existing CML skill behavior

### 10. Packet Capture Streaming

**Decision**: Support both file download and streaming

**API Endpoints**:
- Start capture: `POST /v3/projects/{project_id}/links/{link_id}/capture/start`
- Stop capture: `POST /v3/projects/{project_id}/links/{link_id}/capture/stop`
- Stream PCAP: `GET /v3/projects/{project_id}/links/{link_id}/capture/stream`

**Rationale**:
- Stream endpoint provides live PCAP data (Server-Sent Events)
- Can be piped to packet-analysis skill
- Stop returns PCAP file path for later retrieval

## Dependencies

### Python Packages

```
fastmcp>=0.1.0
httpx>=0.27.0
python-dotenv>=1.0.0
gait_mcp>=0.1.0  # For GAIT audit logging
```

### External Requirements

- GNS3 Server 2.2.0+ with REST API v3 enabled
- Network connectivity to GNS3 server
- Valid user credentials with appropriate privileges

## Design Decisions Summary

| Decision | Choice | Confidence |
|----------|--------|------------|
| API Version | v3 | High |
| Auth Method | OAuth2 Bearer Token | High |
| HTTP Client | httpx (async) | High |
| Server Pattern | Monolithic (single file) | High |
| Tool Count | 23 tools in 5 skills | High |
| GAIT Integration | Decorator pattern | High |
| Error Handling | Structured JSON responses | High |

## Open Questions Resolved

All technical unknowns have been resolved through API documentation review and pattern analysis of existing NetGeniusClaw MCP servers.
