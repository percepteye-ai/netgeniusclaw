# Research: DevNet Content Search MCP Server Integration

**Feature**: 026-devnet-content-search-mcp
**Date**: 2026-04-09

## Research Tasks Completed

### 1. Remote MCP Server Configuration Pattern

**Question**: How to configure a remote URL-based MCP server in OpenClaw?

**Decision**: Use URL-based MCP server configuration with `url` property instead of `command`/`args`

**Rationale**: The DevNet MCP server is a remote managed service at `https://devnet.cisco.com/v1/foundation-search-mcp/mcp`. Unlike local MCP servers that require command execution, remote servers are accessed via HTTP/SSE transport.

**Configuration Pattern**:
```json
{
  "mcpServers": {
    "devnet-content-search": {
      "url": "https://devnet.cisco.com/v1/foundation-search-mcp/mcp"
    }
  }
}
```

**Alternatives Considered**:
- Local proxy server: Rejected - unnecessary complexity for a stable remote endpoint
- Command-based wrapper: Rejected - no local installation needed

---

### 2. DevNet MCP Server Tool Inventory

**Question**: What tools does the DevNet Content Search MCP server expose?

**Decision**: Document 3 tools with their exact IDs and parameters

**Findings**:

| Tool ID | Purpose | Parameters |
|---------|---------|------------|
| `Meraki-API-Doc-Search` | Search Meraki API documentation | `query` (string), `limit` (optional int) |
| `CatalystCenter-API-Doc-Search` | Search Catalyst Center API documentation | `query` (string), `limit` (optional int) |
| `Meraki-API-OperationId-Search` | Lookup specific Meraki operation by ID | `operationId` (string) |

**Response Format**: JSON with API endpoint information including:
- Endpoint path and HTTP method
- Description and summary
- Parameters and request body schemas
- Code examples (when available)
- Implementation guides (Catalyst Center)

---

### 3. Skill Organization Pattern

**Question**: How should the 3 tools be organized into skills?

**Decision**: Create 2 skills organized by platform

**Rationale**: Network engineers typically work with one platform at a time. Organizing by platform (Meraki vs Catalyst Center) provides clearer mental model and simpler skill invocation.

**Skill Mapping**:

| Skill | Tools | Use Cases |
|-------|-------|-----------|
| `devnet-meraki-search` | Meraki-API-Doc-Search, Meraki-API-OperationId-Search | Firewall, VLANs, wireless, OAuth, specific operation lookup |
| `devnet-catalyst-search` | CatalystCenter-API-Doc-Search | Device inventory, policy automation, assurance, site management |

**Alternatives Considered**:
- Single combined skill: Rejected - too broad, confusing when searching for platform-specific docs
- Three separate skills (one per tool): Rejected - Meraki operation lookup is a specialized form of Meraki search

---

### 4. Existing SKILL.md Pattern

**Question**: What format should the SKILL.md files follow?

**Decision**: Follow existing NetGeniusClaw SKILL.md format with YAML frontmatter

**Pattern** (from `workspace/skills/prisma-sdwan-topology/SKILL.md`):
```yaml
---
name: skill-name
description: Brief description
user-invocable: true/false
metadata:
  openclaw:
    requires:
      - mcp-server-name
---

# Skill Name

## Purpose
...

## Tools Used
...

## Workflow
...
```

---

### 5. Authentication Requirements

**Question**: Does DevNet Content Search require authentication?

**Decision**: No authentication required

**Rationale**: The DevNet Content Search MCP server is a public API endpoint. No API keys, OAuth tokens, or credentials are needed. This simplifies configuration significantly.

**Verification**: Confirmed in Cisco's MCP server documentation - one-click install instructions do not include any authentication setup.

---

## Summary

All research questions resolved. No clarifications needed. The integration is straightforward:
1. Register remote MCP server via URL in openclaw.json
2. Create 2 skills with proper SKILL.md format
3. Update documentation (README.md, SOUL.md)

No local code, no dependencies, no credentials required.
