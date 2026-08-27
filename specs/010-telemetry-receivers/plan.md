# Implementation Plan: Telemetry & Event Receiver Capabilities

**Branch**: `010-telemetry-receivers` | **Date**: 2026-03-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-telemetry-receivers/spec.md`

## Summary

Add three new MCP servers to NetGeniusClaw for receiving network telemetry and events: **syslog-mcp** (RFC 5424/3164 syslog messages), **snmptrap-mcp** (SNMPv2c/v3 traps), and **ipfix-mcp** (IPFIX/NetFlow v9 flow records). Additionally, validate the existing **gnmi-mcp** streaming telemetry capability. All receivers store data in-memory, expose MCP tools for querying, and support ngrok tunnel integration for live testing with Cisco Catalyst 9300 devices.

## Technical Context

**Language/Version**: Python 3.10+ (consistent with existing NetGeniusClaw MCP servers)
**Primary Dependencies**: FastMCP (MCP framework), asyncio (UDP receivers), pysnmp (SNMP trap decoding), python-syslog-rfc5424 (syslog parsing), xflow (IPFIX/NetFlow decoding)
**Storage**: In-memory only (data lost on restart, acceptable for demo/testing scope)
**Testing**: pytest with asyncio fixtures, mock UDP packets for unit tests
**Target Platform**: Linux server (WSL2 compatible), ngrok for remote device connectivity
**Project Type**: Three MCP servers (syslog-mcp, snmptrap-mcp, ipfix-mcp) + existing gnmi-mcp validation
**Performance Goals**: Syslog 1000 msg/sec, SNMP trap decode <100ms, IPFIX 95% decode rate
**Constraints**: 24-hour in-memory retention, configurable rate limiting, message deduplication (5-second window)
**Scale/Scope**: Single-instance deployment, live testing with 1 Catalyst 9300

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Safety-First Operations | N/A | Receivers are passive listeners, no device configuration |
| II. Read-Before-Write | N/A | No write operations to devices |
| III. ITSM-Gated Changes | N/A | No production changes, demo/testing scope |
| IV. Immutable Audit Trail | PASS | FR-018 requires GAIT logging for all received events |
| V. MCP-Native Integration | PASS | All receivers implemented as FastMCP servers |
| VI. Multi-Vendor Neutrality | PASS | Receivers are protocol-based, vendor-agnostic |
| VII. Skill Modularity | PASS | Separate MCP server per protocol (clarification decision) |
| VIII. Verify After Every Change | N/A | No device changes |
| IX. Security by Default | PASS | SNMPv3 authPriv supported, open receivers acceptable for demo |
| X. Observability as First-Class | PASS | FR-019 provides receiver statistics tool |
| XI. Artifact Coherence | PENDING | Checklist items must be completed in tasks |
| XII. Documentation-as-Code | PENDING | SKILL.md and README.md required |
| XIII. Credential Safety | PASS | SNMP credentials via environment variables |
| XIV. Human-in-the-Loop | N/A | No external communications from receivers |
| XV. Backwards Compatibility | PASS | New MCP servers, no existing interface changes |
| XVI. Spec-Driven Development | PASS | This plan follows SDD workflow |
| XVII. Milestone Documentation | PENDING | WordPress blog post required at completion |

**Gate Status**: PASS (no violations, pending items deferred to implementation)

## Project Structure

### Documentation (this feature)

```text
specs/010-telemetry-receivers/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── mcp-tools.md     # MCP tool definitions for all 3 servers
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
mcp-servers/
├── syslog-mcp/
│   ├── __init__.py
│   ├── syslog_mcp_server.py    # FastMCP server with UDP receiver
│   ├── syslog_parser.py        # RFC 5424/3164 parsing
│   ├── message_store.py        # In-memory storage with dedup
│   ├── models.py               # Pydantic models
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── snmptrap-mcp/
│   ├── __init__.py
│   ├── snmptrap_mcp_server.py  # FastMCP server with UDP receiver
│   ├── trap_decoder.py         # SNMPv2c/v3 trap decoding
│   ├── mib_resolver.py         # OID to name resolution
│   ├── message_store.py        # In-memory storage with dedup
│   ├── models.py               # Pydantic models
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── ipfix-mcp/
│   ├── __init__.py
│   ├── ipfix_mcp_server.py     # FastMCP server with UDP receiver
│   ├── template_cache.py       # IPFIX template management
│   ├── flow_decoder.py         # IPFIX/NetFlow v9 decoding
│   ├── flow_aggregator.py      # 5-tuple aggregation
│   ├── message_store.py        # In-memory storage with dedup
│   ├── models.py               # Pydantic models
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
└── gnmi-mcp/                   # Existing (validation only)

workspace/skills/
├── syslog-receiver/
│   └── SKILL.md                # Syslog skill documentation
├── snmptrap-receiver/
│   └── SKILL.md                # SNMP trap skill documentation
├── ipfix-receiver/
│   └── SKILL.md                # IPFIX/NetFlow skill documentation
└── telemetry-ops/
    └── SKILL.md                # Cross-receiver correlation skill
```

**Structure Decision**: Following NetGeniusClaw convention with separate MCP server directories under `mcp-servers/`. Each server is self-contained with its own requirements.txt and Dockerfile. Skills are organized per-receiver with a unified telemetry-ops skill for cross-protocol queries.

## Complexity Tracking

No complexity violations. The design follows existing patterns:
- Separate MCP servers (consistent with gnmi-mcp, suzieq-mcp, etc.)
- In-memory storage (simple, no external database dependency)
- Standard FastMCP + asyncio pattern
