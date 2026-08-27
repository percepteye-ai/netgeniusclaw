# Implementation Plan: HashiCorp Vault MCP Server Integration

**Branch**: `019-vault-mcp-server` | **Date**: 2026-04-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/019-vault-mcp-server/spec.md`

## Summary

Integrate the official HashiCorp Vault MCP server to provide secrets management capabilities within NetGeniusClaw. This is a community MCP server integration following the established pattern (clone → register → skills → documentation). The server provides 15+ tools for KV secrets, PKI certificates, and mount management with strict secret value protection.

## Technical Context

**Language/Version**: Go (official HashiCorp Vault MCP server)
**Primary Dependencies**: vault-mcp-server (official), Vault API
**Storage**: N/A (stateless proxy to Vault API)
**Testing**: Manual verification via quickstart.md scenarios
**Target Platform**: Linux/macOS (OpenClaw runtime)
**Project Type**: MCP server integration (community server + NetGeniusClaw skills)
**Performance Goals**: N/A (API proxy, latency dependent on Vault performance)
**Constraints**: Requires VAULT_TOKEN with appropriate policies
**Scale/Scope**: 15+ tools, 3 skills, 1 MCP server registration

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| V. MCP-Native Integration | ✅ PASS | Official HashiCorp MCP server |
| VII. Skill Modularity | ✅ PASS | 3 focused skills (secrets, pki, mounts) |
| XI. Full-Stack Artifact Coherence | ⏳ PENDING | Will update all artifacts |
| XII. Documentation-as-Code | ⏳ PENDING | SKILL.md files to be created |
| XIII. Credential Safety | ✅ PASS | Token via VAULT_TOKEN, secrets never displayed |
| XVI. Spec-Driven Development | ✅ PASS | Following SDD workflow |
| XVII. Milestone Documentation | ⏳ PENDING | Blog post after implementation |

**Gate Status**: PASS - No violations requiring justification

## Project Structure

### Documentation (this feature)

```text
specs/019-vault-mcp-server/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── vault-tools.md
└── tasks.md             # Phase 2 output (from /speckit.tasks)
```

### Source Code (repository root)

```text
# Community MCP server (installed via go install or binary)
# No local server code - uses official vault-mcp-server binary

# NetGeniusClaw skills
workspace/skills/
├── vault-secrets/SKILL.md
├── vault-pki/SKILL.md
└── vault-mounts/SKILL.md

# Configuration updates
config/openclaw.json          # MCP server registration
.env.example                  # Environment variables
scripts/install.sh            # Installation instructions
README.md                     # Architecture and counts
SOUL.md                       # Skill index update
ui/netclaw-visual/server.js   # UI integration catalog
```

**Structure Decision**: Community MCP server pattern - no local server code, skills only. The official vault-mcp-server binary is used directly.

## Complexity Tracking

> No violations requiring justification - standard community MCP integration pattern.
