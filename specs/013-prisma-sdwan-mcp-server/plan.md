# Implementation Plan: Prisma SD-WAN MCP Server Integration

**Branch**: `013-prisma-sdwan-mcp-server` | **Date**: 2026-04-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/013-prisma-sdwan-mcp-server/spec.md`

## Summary

Integrate the community Prisma SD-WAN MCP server (https://github.com/iamdheerajdubey/prisma-sdwan-mcp) to provide read-only visibility into Palo Alto Networks SD-WAN fabric. The integration includes 15 MCP tools organized into 4 skills (topology, status, config, apps), OAuth2 authentication via environment variables, and full artifact coherence updates (install.sh, README.md, openclaw.json, SOUL.md, SKILL.md files).

## Technical Context

**Language/Version**: Python 3.10+ (community MCP server uses prisma_sase SDK)
**Primary Dependencies**: prisma-sdwan-mcp (community), prisma_sase SDK (OAuth2 client)
**Storage**: N/A (stateless proxy to Prisma SASE REST API)
**Testing**: Manual verification via quickstart.md scenarios
**Target Platform**: Linux server (NetGeniusClaw runtime environment)
**Project Type**: MCP server integration (community server, NetGeniusClaw skills)
**Performance Goals**: Operations complete within 10 seconds for single-item requests
**Constraints**: Read-only operations only (except local YAML file generation)
**Scale/Scope**: SD-WAN fabrics with up to hundreds of sites and elements

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Safety-First Operations | PASS | Read-only operations; no device configuration changes |
| II. Read-Before-Write | PASS | No write operations to SD-WAN controller |
| III. ITSM-Gated Changes | PASS | Read-only — no ServiceNow CR required (per spec FR-018) |
| IV. Immutable Audit Trail | PASS | All operations logged via GAIT (FR-019) |
| V. MCP-Native Integration | PASS | Community MCP server follows MCP standard |
| VI. Multi-Vendor Neutrality | PASS | Palo Alto-specific logic in dedicated MCP server |
| VII. Skill Modularity | PASS | 4 focused skills (topology, status, config, apps) |
| VIII. Verify After Every Change | N/A | No changes to verify (read-only) |
| IX. Security by Default | PASS | OAuth2 auth, credentials via env vars |
| X. Observability | PASS | Status, alarms, events tools provide visibility |
| XI. Full-Stack Artifact Coherence | REQUIRED | Must update all artifacts per checklist |
| XII. Documentation-as-Code | REQUIRED | SKILL.md files + README updates needed |
| XIII. Credential Safety | PASS | PAN_* credentials in .env, not hardcoded |
| XIV. Human-in-the-Loop | N/A | No external communications |
| XV. Backwards Compatibility | PASS | New integration, no breaking changes |
| XVI. Spec-Driven Development | PASS | Following SDD workflow |
| XVII. Milestone Documentation | REQUIRED | Blog post at completion |

**Gate Status**: PASS — No violations requiring justification

## Project Structure

### Documentation (this feature)

```text
specs/013-prisma-sdwan-mcp-server/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── prisma-sdwan-tools.md
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
# Community MCP server (cloned by install.sh)
mcp-servers/prisma-sdwan-mcp/
├── (cloned from https://github.com/iamdheerajdubey/prisma-sdwan-mcp)
└── README.md             # Community server docs

# NetGeniusClaw skills
workspace/skills/
├── prisma-sdwan-topology/SKILL.md
├── prisma-sdwan-status/SKILL.md
├── prisma-sdwan-config/SKILL.md
└── prisma-sdwan-apps/SKILL.md

# Configuration updates
config/openclaw.json      # Add prisma-sdwan MCP server registration
.env.example              # Add PAN_CLIENT_ID, PAN_CLIENT_SECRET, PAN_TSG_ID, PAN_REGION
scripts/install.sh        # Add clone/setup for prisma-sdwan-mcp
README.md                 # Add Prisma SD-WAN to architecture section
SOUL.md                   # Add prisma-sdwan-* skills to index
```

**Structure Decision**: Community MCP server integration pattern (similar to GitLab, Jenkins, Atlassian). Server is cloned into mcp-servers/, skills created in workspace/skills/, configuration updates to existing files.

## Complexity Tracking

> No violations requiring justification — all gates pass.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
