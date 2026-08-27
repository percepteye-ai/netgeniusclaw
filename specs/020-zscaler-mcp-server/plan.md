# Implementation Plan: Zscaler MCP Server Integration

**Branch**: `020-zscaler-mcp-server` | **Date**: 2026-04-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/020-zscaler-mcp-server/spec.md`

## Summary

Integrate the official Zscaler MCP server to provide comprehensive Zero Trust security management within NetGeniusClaw. This is the largest single integration with 300+ tools across all 9 Zscaler services (ZIA, ZPA, ZDX, ZMS, ZTW, Z-Insights, ZIdentity, EASM, ZCC).

## Technical Context

**Language/Version**: Go (official Zscaler MCP server)
**Primary Dependencies**: zscaler-mcp-server (official), Zscaler OneAPI
**Storage**: N/A (stateless proxy to Zscaler APIs)
**Testing**: Manual verification via quickstart.md scenarios
**Target Platform**: Linux/macOS (OpenClaw runtime)
**Project Type**: MCP server integration (community server + NetGeniusClaw skills)
**Performance Goals**: N/A (API proxy, latency dependent on Zscaler APIs)
**Constraints**: Requires Zscaler OneAPI credentials
**Scale/Scope**: 300+ tools, 5 skills, 1 MCP server registration

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| V. MCP-Native Integration | ✅ PASS | Official Zscaler MCP server |
| VII. Skill Modularity | ✅ PASS | 5 focused skills (zpa, zia, zdx, identity, insights) |
| XI. Full-Stack Artifact Coherence | ⏳ PENDING | Will update all artifacts |
| XII. Documentation-as-Code | ⏳ PENDING | SKILL.md files to be created |
| XIII. Credential Safety | ✅ PASS | OAuth credentials via env vars |
| XVI. Spec-Driven Development | ✅ PASS | Following SDD workflow |
| XVII. Milestone Documentation | ⏳ PENDING | Blog post after implementation |

**Gate Status**: PASS - No violations requiring justification

## Project Structure

### Documentation (this feature)

```text
specs/020-zscaler-mcp-server/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── zscaler-tools.md
└── tasks.md             # Phase 2 output (from /speckit.tasks)
```

### Source Code (repository root)

```text
# Community MCP server (installed via go install or binary)
# No local server code - uses official zscaler-mcp-server binary

# NetGeniusClaw skills
workspace/skills/
├── zscaler-zpa/SKILL.md
├── zscaler-zia/SKILL.md
├── zscaler-zdx/SKILL.md
├── zscaler-identity/SKILL.md
└── zscaler-insights/SKILL.md

# Configuration updates
config/openclaw.json          # MCP server registration
.env.example                  # Environment variables
scripts/install.sh            # Installation instructions
README.md                     # Architecture and counts
SOUL.md                       # Skill index update
ui/netclaw-visual/server.js   # UI integration catalog
```

**Structure Decision**: Community MCP server pattern - no local server code, skills only. The official zscaler-mcp-server binary is used directly.

## Complexity Tracking

> No violations requiring justification - standard community MCP integration pattern (largest tool count in NetGeniusClaw).
