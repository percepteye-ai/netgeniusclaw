# Implementation Plan: GNS3 MCP Server and Skills

**Branch**: `012-gns3-mcp-server` | **Date**: 2026-04-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/012-gns3-mcp-server/spec.md`

## Summary

Add GNS3 network lab management capabilities to NetGeniusClaw through a new MCP server and 5 skills. The GNS3 MCP server will wrap the GNS3 REST API v3 to enable project lifecycle management, node operations, link management, packet capture, and snapshot operations. This follows established patterns from existing clab-mcp-server and CML skills, providing natural language control over GNS3 lab environments without requiring ServiceNow CR gating (lab-only operations).

## Technical Context

**Language/Version**: Python 3.10+ (consistent with existing NetGeniusClaw MCP servers)
**Primary Dependencies**: FastMCP (MCP framework), httpx (async HTTP client), python-dotenv (environment variables)
**Storage**: N/A (stateless proxy to GNS3 REST API)
**Testing**: pytest with httpx mock responses
**Target Platform**: Linux server (primary), macOS/Windows (development)
**Project Type**: MCP server + skill definitions
**Performance Goals**: Operations complete within 10 seconds for single-item requests (per SC-003)
**Constraints**: GNS3 server must be running with REST API v3 enabled (GNS3 2.2.0+)
**Scale/Scope**: Single GNS3 server per MCP instance, multiple projects/labs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Safety-First | ✅ PASS | Lab-only operations; no production device impact |
| II. Read-Before-Write | ✅ PASS | All tools observe state before modification |
| III. ITSM-Gated Changes | ✅ PASS | Lab mode exemption applies (FR-015) |
| IV. Immutable Audit Trail | ✅ PASS | GAIT logging required (FR-016) |
| V. MCP-Native Integration | ✅ PASS | FastMCP server following MCP standard |
| VI. Multi-Vendor Neutrality | ✅ PASS | GNS3-specific server, no vendor logic leakage |
| VII. Skill Modularity | ✅ PASS | 5 focused skills, each single-purpose |
| VIII. Verify After Every Change | ✅ PASS | Tools verify state after operations |
| IX. Security by Default | ✅ PASS | Token-based auth, least privilege |
| X. Observability | ✅ PASS | Server status, project stats exposed |
| XI. Full-Stack Artifact Coherence | ⚠️ PENDING | Requires all artifacts at implementation |
| XII. Documentation-as-Code | ⚠️ PENDING | SKILL.md files required |
| XIII. Credential Safety | ✅ PASS | Env vars only, .env.example provided |
| XIV. Human-in-the-Loop | ✅ PASS | No external communications |
| XV. Backwards Compatibility | ✅ PASS | New server, no breaking changes |
| XVI. Spec-Driven Development | ✅ PASS | Following SDD workflow |
| XVII. Milestone Documentation | ⚠️ PENDING | WordPress post at completion |

**Gate Result**: PASS - No violations requiring justification

## Project Structure

### Documentation (this feature)

```text
specs/012-gns3-mcp-server/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── gns3-mcp-tools.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
mcp-servers/gns3-mcp-server/
├── README.md                    # Server documentation
├── requirements.txt             # Dependencies
├── .env.example                 # Environment variable template
├── gns3_mcp_server.py          # Main FastMCP server (monolithic)
└── tests/
    └── test_gns3_mcp_server.py  # pytest tests with mocked responses

workspace/skills/
├── gns3-project-lifecycle/
│   └── SKILL.md                 # Project CRUD operations
├── gns3-node-operations/
│   └── SKILL.md                 # Node create/start/stop/isolate
├── gns3-link-management/
│   └── SKILL.md                 # Link create/delete/list
├── gns3-packet-capture/
│   └── SKILL.md                 # Capture start/stop/stream
└── gns3-snapshot-ops/
    └── SKILL.md                 # Snapshot create/restore/delete
```

**Structure Decision**: Monolithic server pattern (like clab-mcp-server) with separate skill files for each of the 5 skill categories. This matches the established NetGeniusClaw pattern for network lab servers.

## Complexity Tracking

No violations requiring justification. Design follows established patterns.

---

## Post-Design Constitution Re-Check

*Re-evaluated after Phase 1 design completion*

| Principle | Pre-Design | Post-Design | Notes |
|-----------|------------|-------------|-------|
| XI. Full-Stack Artifact Coherence | ⚠️ PENDING | ⚠️ PENDING | Will be addressed during implementation |
| XII. Documentation-as-Code | ⚠️ PENDING | ⚠️ PENDING | SKILL.md files defined in contracts |
| XVII. Milestone Documentation | ⚠️ PENDING | ⚠️ PENDING | WordPress post after implementation |

**Design Artifacts Created**:
- ✅ research.md — Technical decisions documented
- ✅ data-model.md — 6 entities with validation rules
- ✅ contracts/gns3-mcp-tools.md — 23 tools across 5 skills
- ✅ quickstart.md — Installation and usage guide

**Post-Design Gate Result**: PASS — Design is complete and ready for task generation

---

## Phase Completion Status

| Phase | Status | Output |
|-------|--------|--------|
| Phase 0: Research | ✅ Complete | research.md |
| Phase 1: Design | ✅ Complete | data-model.md, contracts/, quickstart.md |
| Phase 2: Tasks | ⏳ Pending | Run `/speckit.tasks` |
| Phase 3: Implement | ⏳ Pending | Run `/speckit.implement` |

---

## Next Steps

1. **Generate Tasks**: Run `/speckit.tasks` to create dependency-ordered task list
2. **Implement**: Run `/speckit.implement` to execute tasks
3. **Coherence Check**: Verify all artifacts updated per Constitution XI
4. **Blog Post**: Draft WordPress post per Constitution XVII
