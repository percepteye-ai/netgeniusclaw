# Implementation Plan: Azure Networking MCP Server

**Branch**: `004-azure-network-mcp` | **Date**: 2026-03-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-azure-network-mcp/spec.md`

## Summary

Build a Python-based MCP server for Microsoft Azure networking services using the FastMCP framework and Azure SDK for Python. The server provides read-only access to Azure VNet topology, NSG rules and compliance auditing, ExpressRoute/VPN Gateway health, Azure Firewall policies, Load Balancer/Application Gateway health, Route Tables, Network Watcher, Private Link, and DNS. Completes the NetGeniusClaw multi-cloud story alongside existing AWS and GCP MCP servers. All operations are GAIT-logged and write operations are ITSM-gated.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: FastMCP (MCP framework), azure-mgmt-network, azure-mgmt-resource, azure-identity (DefaultAzureCredential), gait_mcp (audit logging)
**Storage**: N/A (stateless; reads from Azure ARM APIs)
**Testing**: pytest with unittest.mock for Azure SDK mocking; contract tests for MCP tool schemas
**Target Platform**: Linux/macOS (stdio transport, invoked by OpenClaw gateway)
**Project Type**: MCP server (stdio transport)
**Performance Goals**: Single subscription query < 30 seconds; support up to 5 concurrent subscriptions
**Constraints**: Azure ARM API rate limits (~1200 reads/5min per tenant); max 5 concurrent subscription queries; read-only by default
**Scale/Scope**: ~18 MCP tools covering 10 Azure networking service areas; 2 companion skills

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Safety-First Operations | PASS | Read-only by default; all observation before any action |
| II. Read-Before-Write | PASS | Write operations gated behind ITSM; read is the primary mode |
| III. ITSM-Gated Changes | PASS | FR-013 requires ITSM approval for any write operation |
| IV. Immutable Audit Trail | PASS | FR-014 requires GAIT logging for all operations |
| V. MCP-Native Integration | PASS | Built as FastMCP server with stdio transport |
| VI. Multi-Vendor Neutrality | PASS | Azure-specific logic in dedicated MCP server; skills are cross-referenceable |
| VII. Skill Modularity | PASS | Two focused skills: azure-network-ops, azure-security-audit |
| VIII. Verify After Every Change | PASS | Write ops follow baseline-apply-verify pattern |
| IX. Security by Default | PASS | CIS Azure Foundations Benchmark auditing built in; Reader RBAC minimum |
| X. Observability as a First-Class Citizen | PASS | Network Watcher integration; health probes exposed |
| XI. Full-Stack Artifact Coherence | PASS | FR-019 mandates full artifact set; plan includes all coherence items |
| XII. Documentation-as-Code | PASS | SKILL.md, README, TOOLS.md updates planned |
| XIII. Credential Safety | PASS | Credentials via env vars only; .env.example documented |
| XIV. Human-in-the-Loop | PASS | No external communications; read-only operations |
| XV. Backwards Compatibility | PASS | New server; does not modify existing servers or skills |
| XVI. Spec-Driven Development | PASS | Following SDD workflow: specify -> plan -> task -> implement |

**Gate Result**: ALL PASS -- proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/004-azure-network-mcp/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (MCP tool schemas)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
mcp-servers/azure-network-mcp/
├── README.md                    # MCP server documentation
├── azure_network_mcp_server.py  # Main FastMCP server entry point
├── requirements.txt             # Python dependencies
├── tools/
│   ├── __init__.py
│   ├── vnet.py                  # VNet topology tools
│   ├── nsg.py                   # NSG rules and compliance audit tools
│   ├── expressroute.py          # ExpressRoute circuit tools
│   ├── vpn_gateway.py           # VPN Gateway tools
│   ├── firewall.py              # Azure Firewall policy tools
│   ├── load_balancer.py         # Load Balancer tools
│   ├── app_gateway.py           # Application Gateway / Front Door tools
│   ├── network_watcher.py       # Network Watcher tools
│   ├── private_link.py          # Private Link / Private Endpoint tools
│   ├── route_table.py           # Route Table / UDR tools
│   └── dns.py                   # Azure DNS tools
├── clients/
│   ├── __init__.py
│   └── azure_client.py          # Azure SDK client factory (credential mgmt, subscription switching)
├── models/
│   ├── __init__.py
│   └── responses.py             # Structured response models
├── compliance/
│   ├── __init__.py
│   └── cis_azure.py             # CIS Azure Foundations Benchmark rules
└── utils/
    ├── __init__.py
    ├── pagination.py            # Azure API pagination handler
    ├── rate_limiter.py          # Rate limiting / retry-after handler
    └── constants.py             # Pinned API versions per resource type

workspace/skills/azure-network-ops/
└── SKILL.md                     # Skill documentation

workspace/skills/azure-security-audit/
└── SKILL.md                     # Existing; update with Azure audit workflows

tests/
├── contract/
│   └── test_azure_network_mcp_tools.py  # MCP tool schema contract tests
├── unit/
│   ├── test_vnet.py
│   ├── test_nsg.py
│   ├── test_compliance.py
│   ├── test_expressroute.py
│   ├── test_vpn_gateway.py
│   ├── test_firewall.py
│   ├── test_load_balancer.py
│   └── test_azure_client.py
└── integration/
    └── test_azure_network_live.py  # Live Azure integration tests (requires credentials)
```

**Structure Decision**: Single MCP server project under `mcp-servers/azure-network-mcp/` following the established NetGeniusClaw pattern. Tools are organized by Azure service area in the `tools/` subdirectory. A shared Azure client factory handles credential management and subscription switching. Two companion skills provide workflow guidance.

## Complexity Tracking

> No constitution violations to justify. All gates pass.
