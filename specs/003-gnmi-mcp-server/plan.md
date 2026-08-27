# Implementation Plan: gNMI Streaming Telemetry MCP Server

**Branch**: `003-gnmi-mcp-server` | **Date**: 2026-03-26 | **Spec**: `specs/003-gnmi-mcp-server/spec.md`
**Input**: Feature specification from `/specs/003-gnmi-mcp-server/spec.md`

## Summary

Build a new MCP server providing gNMI (gRPC Network Management Interface) streaming telemetry capabilities for NetGeniusClaw. The server exposes gNMI Get, Set, Subscribe, and Capabilities operations as MCP tools, supporting multi-vendor devices (Cisco IOS-XR, Juniper, Arista, Nokia SR OS) through OpenConfig and vendor-native YANG models. gNMI Get is read-only (safe); gNMI Set is ITSM-gated via ServiceNow. A companion skill provides higher-level telemetry workflows. Built with Python 3.10+ using FastMCP framework and grpcio/pygnmi for gNMI transport over mandatory TLS.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: FastMCP (MCP framework), grpcio + grpcio-tools (gRPC transport), pygnmi (gNMI client library), protobuf, cryptography (TLS handling)
**Storage**: N/A (stateless server; subscription state held in-memory during runtime)
**Testing**: pytest with pytest-asyncio, mock gNMI server stubs via grpcio-testing
**Target Platform**: Linux server, macOS (development)
**Project Type**: MCP server (stdio transport) + skill
**Performance Goals**: gNMI Get responses within 5 seconds for standard paths; ON_CHANGE subscription delivery within 2 seconds; max 50 concurrent subscriptions
**Constraints**: TLS mandatory for all device connections; max 50 concurrent subscriptions; gRPC max message size 16MB default; all credentials from environment variables
**Scale/Scope**: 4 vendor platforms, 10+ MCP tools, 1 skill with multiple workflows

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Safety-First Operations | PASS | gNMI Get is read-only observation. Set operations require explicit ITSM gate. Unreachable devices halt and report. |
| II. Read-Before-Write | PASS | gNMI Set workflow will capture baseline via gNMI Get before applying changes. |
| III. ITSM-Gated Changes | PASS | FR-004 explicitly requires ServiceNow CR validation for all gNMI Set operations. |
| IV. Immutable Audit Trail | PASS | FR-008 requires GAIT logging for all operations via existing gait_mcp integration. |
| V. MCP-Native Integration | PASS | Built as FastMCP server with stdio transport, proper JSON-RPC lifecycle. |
| VI. Multi-Vendor Neutrality | PASS | Server supports 4+ vendors via pygnmi abstraction; vendor-specific dialects handled transparently. |
| VII. Skill Modularity | PASS | Single skill (gnmi-telemetry) for telemetry workflows; delegates to MCP tools. |
| VIII. Verify After Every Change | PASS | gNMI Set workflow: Get baseline -> Set -> Get verify -> report. |
| IX. Security by Default | PASS | TLS mandatory, credentials from env vars, no insecure connections permitted. |
| X. Observability | PASS | Telemetry subscriptions provide real-time observability; HUD update planned. |
| XI. Artifact Coherence | PASS | All artifacts in checklist will be updated (README, install.sh, UI, SOUL.md, SKILL.md, .env.example, TOOLS.md, openclaw.json). |
| XII. Documentation-as-Code | PASS | MCP server README, SKILL.md, and tool documentation included in plan. |
| XIII. Credential Safety | PASS | All credentials (device IPs, ports, TLS certs, usernames, passwords) from env vars. |
| XIV. Human-in-the-Loop | PASS | gNMI Set is gated by ITSM approval; no autonomous external communications. |
| XV. Backwards Compatibility | PASS | New MCP server and skill; no changes to existing servers or skills. |
| XVI. Spec-Driven Development | PASS | Following full SDD workflow: specify -> plan -> task -> implement. |

**Gate Result**: ALL PASS. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/003-gnmi-mcp-server/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (MCP tool schemas)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
mcp-servers/gnmi-mcp/
├── gnmi_mcp_server.py       # Main FastMCP server with tool definitions
├── gnmi_client.py           # gNMI client wrapper (pygnmi-based)
├── subscription_manager.py  # Manages active telemetry subscriptions
├── vendor_dialects.py       # Vendor-specific gNMI dialect handling
├── yang_utils.py            # YANG path parsing and validation utilities
├── itsm_gate.py             # ServiceNow CR validation for Set operations
├── models.py                # Pydantic data models for requests/responses
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container image for deployment
└── README.md                # MCP server documentation

workspace/skills/gnmi-telemetry/
└── SKILL.md                 # Skill documentation
```

**Structure Decision**: Follows existing NetGeniusClaw pattern of `mcp-servers/<name>/` for the MCP server and `workspace/skills/<name>/` for the skill. Single flat module structure within the MCP server directory (matching pyATS_MCP pattern) with separate modules for client, subscriptions, vendor dialects, and ITSM gating.

## Complexity Tracking

No constitution violations to justify. All principles are satisfied by the design.
