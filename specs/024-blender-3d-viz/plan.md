# Implementation Plan: Blender 3D Network Visualization

**Branch**: `024-blender-3d-viz` | **Date**: 2026-04-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/024-blender-3d-viz/spec.md`

## Summary

Integrate the community Blender MCP server (`blender-mcp` via uvx) to enable 3D network topology visualization. Network engineers can request topology drawings via natural language in Slack, and NetGeniusClaw translates CDP/LLDP neighbor data into 3D rendering commands sent to a locally-running Blender instance. The MCP server connects to Blender's addon via socket on port 9876.

## Technical Context

**Language/Version**: Python 3.10+ (consistent with NetGeniusClaw MCP servers)
**Primary Dependencies**: blender-mcp (community, via uvx), Blender 3.0+ (user-installed)
**Storage**: N/A (stateless - visualization is ephemeral in Blender)
**Testing**: Manual integration testing (Blender GUI required)
**Target Platform**: WSL2 (NetGeniusClaw) + Windows (Blender GUI)
**Project Type**: MCP integration + skill definition (no custom server code)
**Performance Goals**: Render up to 25 devices within 30 seconds
**Constraints**: Requires user to have Blender running with addon connected; cross-OS socket connectivity (WSL→Windows)
**Scale/Scope**: Up to 25 network devices per topology visualization

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Safety-First Operations | PASS | Read-only visualization; no device modifications |
| II. Read-Before-Write | PASS | Reads CDP data before rendering; no device writes |
| III. ITSM-Gated Changes | N/A | No production changes; visualization only |
| IV. Immutable Audit Trail | PASS | GAIT logging for sessions |
| V. MCP-Native Integration | PASS | Uses community blender-mcp server via MCP protocol |
| VI. Multi-Vendor Neutrality | PASS | Visualization is vendor-agnostic |
| VII. Skill Modularity | PASS | Single-purpose skill (blender-3d-viz) |
| VIII. Verify After Every Change | N/A | No changes to verify |
| IX. Security by Default | PASS | No elevated privileges required |
| X. Observability | PASS | Error messages for connection failures |
| XI. Full-Stack Artifact Coherence | REQUIRED | Must update README, SOUL.md, openclaw.json, etc. |
| XII. Documentation-as-Code | REQUIRED | Must create SKILL.md |
| XIII. Credential Safety | PASS | No credentials required (local socket) |
| XIV. Human-in-the-Loop | N/A | No external communications |
| XV. Backwards Compatibility | PASS | New capability; no breaking changes |
| XVI. Spec-Driven Development | PASS | Following SDD workflow |
| XVII. Milestone Documentation | REQUIRED | Blog post after completion |

**Gate Status**: PASS - No violations. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/024-blender-3d-viz/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (MCP tool schemas)
├── checklists/          # Quality checklists
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
# Configuration files (modified)
config/openclaw.json         # Add blender-mcp server registration
.env.example                 # Add BLENDER_HOST, BLENDER_PORT

# Skill definition (new)
workspace/skills/blender-3d-viz/
└── SKILL.md                 # Skill documentation

# Documentation (modified)
SOUL.md                      # Add blender-3d-viz skill
README.md                    # Add to MCP server table
scripts/install.sh           # Add Blender setup instructions
```

**Structure Decision**: No custom source code required. This integration uses the existing community `blender-mcp` package via uvx. Implementation consists of:
1. MCP server registration in `openclaw.json`
2. Skill definition in `workspace/skills/blender-3d-viz/SKILL.md`
3. Documentation updates across standard touchpoints

## Complexity Tracking

No violations requiring justification. This is a straightforward MCP integration following established NetGeniusClaw patterns.
