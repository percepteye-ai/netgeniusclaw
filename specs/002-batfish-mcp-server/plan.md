# Implementation Plan: Batfish MCP Server

**Branch**: `002-batfish-mcp-server` | **Date**: 2026-03-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-batfish-mcp-server/spec.md`

## Summary

Build a first-of-its-kind MCP server wrapping the Batfish network configuration analysis platform via the pybatfish Python client library. The server exposes six core tools (upload_snapshot, validate_config, test_reachability, trace_acl, diff_configs, check_compliance) through the FastMCP framework over stdio transport. Batfish runs as a Docker container on localhost; the MCP server connects via pybatfish using environment variables for host/port configuration. All operations are strictly read-only and logged via GAIT.

## Technical Context

**Language/Version**: Python 3.10+ with FastMCP framework
**Primary Dependencies**: pybatfish (Batfish Python client), mcp[cli] (FastMCP), python-dotenv, gait_mcp
**Storage**: Ephemeral — Batfish manages snapshot storage internally; no persistent database
**Testing**: pytest with mocked pybatfish sessions for unit tests; integration tests against live Batfish container
**Target Platform**: Linux/macOS (runs alongside Batfish Docker container on localhost)
**Project Type**: MCP server (stdio transport)
**Performance Goals**: Configuration validation for up to 200 devices within 60 seconds (per SC-001)
**Constraints**: Strictly read-only — never modifies network devices. All credentials from environment variables.
**Scale/Scope**: Multi-vendor support (Cisco IOS/IOS-XE/NX-OS, JunOS, Arista EOS, Palo Alto, F5). Up to 200 devices per snapshot.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Safety-First Operations | PASS | Server is strictly read-only; analyzes configs uploaded to Batfish, never touches live devices |
| II. Read-Before-Write | PASS | No write operations exist — entire server is read/analysis only |
| III. ITSM-Gated Changes | N/A | No production changes are made — analysis only |
| IV. Immutable Audit Trail | PASS | All analysis operations logged via GAIT (FR-010) |
| V. MCP-Native Integration | PASS | Built as FastMCP server with stdio transport, proper JSON-RPC lifecycle |
| VI. Multi-Vendor Neutrality | PASS | Batfish natively supports multi-vendor; no vendor-specific logic in MCP server |
| VII. Skill Modularity | PASS | Single-purpose MCP server (config analysis); companion skill for workflows |
| VIII. Verify After Every Change | N/A | No changes to verify — read-only analysis |
| IX. Security by Default | PASS | Read-only, least-privilege, credentials from env vars only |
| X. Observability | PASS | Logging to stderr, GAIT audit trail, structured results |
| XI. Artifact Coherence | PENDING | All artifacts listed in checklist will be created during implementation |
| XII. Documentation-as-Code | PENDING | README.md, SKILL.md, TOOLS.md updates planned |
| XIII. Credential Safety | PASS | BATFISH_HOST and BATFISH_PORT from env vars; .env.example updated |
| XIV. Human-in-the-Loop | N/A | No external communications |
| XV. Backwards Compatibility | PASS | New server, isolated dependencies, no changes to existing servers |
| XVI. Spec-Driven Development | PASS | Following full SDD workflow |

**Gate Result**: PASS — no violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/002-batfish-mcp-server/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (MCP tool schemas)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
mcp-servers/batfish-mcp/
├── batfish_mcp_server.py   # Main FastMCP server with all tools
├── requirements.txt        # Python dependencies (pybatfish, mcp[cli], python-dotenv)
├── Dockerfile              # Container build for the MCP server
└── README.md               # MCP server documentation (tools, env vars, setup)

workspace/skills/batfish-config-analysis/
└── SKILL.md                # Skill documentation (purpose, tools, workflow)

tests/
├── unit/
│   └── test_batfish_mcp.py       # Unit tests with mocked pybatfish
└── integration/
    └── test_batfish_integration.py  # Integration tests against live Batfish
```

**Structure Decision**: Single MCP server module following the existing NetGeniusClaw pattern (see pyATS_MCP as reference). One Python file for the server, companion skill directory with SKILL.md, tests in a dedicated directory.

## Complexity Tracking

> No constitution violations detected — this section is intentionally empty.
