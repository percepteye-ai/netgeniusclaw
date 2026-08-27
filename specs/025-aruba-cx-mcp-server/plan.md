# Implementation Plan: Aruba CX MCP Server Integration

**Branch**: `025-aruba-cx-mcp-server` | **Date**: 2026-04-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/025-aruba-cx-mcp-server/spec.md`

## Summary

Integrate the community Aruba CX MCP server (https://github.com/slientnight/aruba-cx-mcp-server) to provide visibility and management capabilities for Aruba CX switches. The integration includes 16 MCP tools (11 read-only, 5 write) organized into 4 skills (system, interfaces, switching, config), REST API authentication via environment variables, ITSM gating for write operations, and full artifact coherence updates (install.sh, README.md, openclaw.json, SOUL.md, SKILL.md files).

## Technical Context

**Language/Version**: Python 3.10+ (community MCP server with Aruba CX REST API client)
**Primary Dependencies**: aruba-cx-mcp-server (community), httpx or requests (REST client)
**Storage**: N/A (stateless proxy to Aruba CX REST API)
**Testing**: Manual verification via quickstart.md scenarios
**Target Platform**: Linux server (NetGeniusClaw runtime environment)
**Project Type**: MCP server integration (community server, NetGeniusClaw skills)
**Performance Goals**: Read operations complete within 10 seconds; ISSU operations may take longer
**Constraints**: Write operations require ITSM approval when ITSM_ENABLED=true
**Scale/Scope**: Switch environments with multiple Aruba CX devices (standalone or VSF clusters)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Safety-First Operations | PASS | Read operations are safe; write operations gated by ITSM |
| II. Read-Before-Write | PASS | Config viewing before changes; ISSU status checks before upgrades |
| III. ITSM-Gated Changes | PASS | Write ops require ServiceNow CR when ITSM_ENABLED (per spec FR-012-016, FR-019) |
| IV. Immutable Audit Trail | PASS | All operations logged via GAIT |
| V. MCP-Native Integration | PASS | Community MCP server follows MCP standard |
| VI. Multi-Vendor Neutrality | PASS | Aruba-specific logic in dedicated MCP server |
| VII. Skill Modularity | PASS | 4 focused skills (system, interfaces, switching, config) |
| VIII. Verify After Every Change | PASS | Write operations verify state post-change |
| IX. Security by Default | PASS | Credentials via env vars, SSL verification enabled by default |
| X. Observability | PASS | Interface status, DOM diagnostics, firmware details tools |
| XI. Full-Stack Artifact Coherence | REQUIRED | Must update all artifacts per checklist |
| XII. Documentation-as-Code | REQUIRED | SKILL.md files + README updates needed |
| XIII. Credential Safety | PASS | ARUBA_CX_* credentials in .env, not hardcoded |
| XIV. Human-in-the-Loop | N/A | No external communications (Slack, etc.) |
| XV. Backwards Compatibility | PASS | New integration, no breaking changes |
| XVI. Spec-Driven Development | PASS | Following SDD workflow |
| XVII. Milestone Documentation | REQUIRED | Blog post at completion |

**Gate Status**: PASS — No violations requiring justification

## Project Structure

### Documentation (this feature)

```text
specs/025-aruba-cx-mcp-server/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── aruba-cx-tools.md
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
# Community MCP server (cloned by install.sh)
mcp-servers/aruba-cx-mcp/
├── (cloned from https://github.com/slientnight/aruba-cx-mcp-server)
└── README.md             # Community server docs

# NetGeniusClaw skills
workspace/skills/
├── aruba-cx-system/SKILL.md       # System info, firmware, VSF topology
├── aruba-cx-interfaces/SKILL.md   # Interfaces, LLDP, optics/DOM
├── aruba-cx-switching/SKILL.md    # VLANs, MAC tables
└── aruba-cx-config/SKILL.md       # Configs, ISSU, save operations

# Configuration updates
config/openclaw.json      # Add aruba-cx-mcp server registration
.env.example              # Add ARUBA_CX_TARGETS, ARUBA_CX_CONFIG, etc.
scripts/install.sh        # Add clone/setup for aruba-cx-mcp
README.md                 # Add Aruba CX to architecture section
SOUL.md                   # Add aruba-cx-* skills to index
```

**Structure Decision**: Community MCP server integration pattern (similar to Prisma SD-WAN, GitLab, Jenkins). Server is cloned into mcp-servers/, skills created in workspace/skills/, configuration updates to existing files.

## Complexity Tracking

> No violations requiring justification — all gates pass.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
