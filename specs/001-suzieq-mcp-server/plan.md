# Implementation Plan: SuzieQ MCP Server

**Branch**: `001-suzieq-mcp-server` | **Date**: 2026-03-26 | **Spec**: `specs/001-suzieq-mcp-server/spec.md`
**Input**: Feature specification from `/specs/001-suzieq-mcp-server/spec.md`

## Summary

Build a read-only MCP server that wraps the SuzieQ network observability platform's REST API, exposing show, summarize, assert, path, and unique operations as MCP tools. The server uses Python 3.10+ with FastMCP framework, communicates via stdio transport, reads all credentials from environment variables, and logs all queries to the GAIT audit trail. This enables network engineers to query current and historical network state, run validation assertions, and trace forwarding paths through natural language via any MCP client.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: FastMCP (mcp SDK), httpx (async HTTP client), python-dotenv
**Storage**: N/A (stateless proxy to SuzieQ REST API)
**Testing**: pytest with pytest-asyncio, httpx mock for unit tests
**Target Platform**: Linux/macOS server (stdio MCP transport)
**Project Type**: MCP server (stdio transport)
**Performance Goals**: Query responses within 5 seconds for networks up to 500 devices (per SC-001)
**Constraints**: Read-only operations only; no write/delete/configuration operations
**Scale/Scope**: Wraps ~15 SuzieQ tables across 5 verbs (show, summarize, assert, unique, path)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Safety-First Operations | PASS | Server is strictly read-only (FR-007). Only show/summarize/assert/path/unique operations exposed. No configuration changes possible. |
| II. Read-Before-Write | PASS | No write operations exist. All operations are observational queries. |
| III. ITSM-Gated Changes | PASS | No production changes made. Read-only queries do not require CRs. |
| IV. Immutable Audit Trail | PASS | All queries logged to GAIT via gait_mcp integration (FR-010). |
| V. MCP-Native Integration | PASS | Built as FastMCP server with stdio transport, proper JSON-RPC lifecycle. |
| VI. Multi-Vendor Neutrality | PASS | SuzieQ itself is multi-vendor. MCP server is vendor-agnostic proxy. |
| VII. Skill Modularity | PASS | Single well-defined function: SuzieQ observability queries. Companion skill in workspace/skills/suzieq-observability/. |
| VIII. Verify After Every Change | PASS | No changes made. Assertions tool enables verification of network state. |
| IX. Security by Default | PASS | Credentials from env vars only. Read-only access. No elevated permissions required. |
| X. Observability as First-Class | PASS | This IS an observability integration. Three.js HUD will be updated. |
| XI. Artifact Coherence | PENDING | Will be completed during implementation (README, install.sh, UI, SOUL.md, SKILL.md, .env.example, TOOLS.md, openclaw.json). |
| XII. Documentation-as-Code | PENDING | MCP server README and SKILL.md will be created during implementation. |
| XIII. Credential Safety | PASS | SUZIEQ_API_URL and SUZIEQ_API_KEY read from env vars. .env.example documents them without values. |
| XIV. Human-in-the-Loop | PASS | No external communications. Read-only queries only. |
| XV. Backwards Compatibility | PASS | New MCP server in isolated directory. No changes to existing servers or skills. |
| XVI. Spec-Driven Development | PASS | Following full SDD workflow: specify -> plan -> task -> implement. |

## Project Structure

### Documentation (this feature)

```text
specs/001-suzieq-mcp-server/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (MCP tool schemas)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
mcp-servers/suzieq-mcp/
├── server.py            # FastMCP server with all tool definitions
├── suzieq_client.py     # Async HTTP client for SuzieQ REST API
├── requirements.txt     # Python dependencies
└── README.md            # MCP server documentation

workspace/skills/suzieq-observability/
└── SKILL.md             # Skill documentation
```

**Structure Decision**: Single-directory MCP server following the established NetGeniusClaw pattern (e.g., protocol-mcp/server.py). The server is a thin proxy layer with an HTTP client module separated for testability. No subdirectories needed given the small scope (~2 source files).

## Complexity Tracking

> No constitution violations requiring justification. All principles satisfied by design (read-only, env-var credentials, GAIT logging, isolated directory).
