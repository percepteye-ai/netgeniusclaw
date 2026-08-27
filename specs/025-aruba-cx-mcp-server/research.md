# Research: Aruba CX MCP Server Integration

**Feature**: 025-aruba-cx-mcp-server
**Date**: 2026-04-08
**Status**: Complete

## Overview

Research findings for integrating the community Aruba CX MCP server into NetGeniusClaw.

## Decision 1: MCP Server Source

**Decision**: Use community server from https://github.com/slientnight/aruba-cx-mcp-server

**Rationale**:
- Provides 16 tools (11 read, 5 write) covering all spec requirements
- Built-in multi-switch management capability
- Supports ITSM integration flags (ITSM_ENABLED, ITSM_LAB_MODE)
- Python-based, consistent with NetGeniusClaw's MCP server stack
- Active maintenance with DOM diagnostics and VSF support

**Alternatives Considered**:
- Build custom MCP server: Rejected - community server already provides comprehensive functionality
- Use Aruba Central API: Rejected - targets switch REST API directly, no cloud dependency required

## Decision 2: Authentication Method

**Decision**: REST API authentication via environment variables (ARUBA_CX_TARGETS or ARUBA_CX_CONFIG)

**Rationale**:
- Consistent with NetGeniusClaw credential safety principles (Principle XIII)
- Supports multiple switch targets from single configuration
- Two configuration methods (env var JSON or config file) provide flexibility
- SSL verification enabled by default for security

**Configuration Format**:
```json
[
  {
    "name": "core-switch-1",
    "host": "10.1.1.1",
    "username": "admin",
    "password": "secret",
    "port": 443,
    "api_version": "v10.13",
    "verify_ssl": true
  }
]
```

**Alternatives Considered**:
- Hardcoded credentials: Rejected - violates Principle XIII
- Certificate-based auth: Not supported by community server at this time

## Decision 3: ITSM Integration

**Decision**: Use ITSM_ENABLED and ITSM_LAB_MODE environment variables for write operation gating

**Rationale**:
- Consistent with NetGeniusClaw constitution (Principle III - ITSM-Gated Changes)
- Community server already supports these flags
- Lab mode allows testing without ServiceNow integration
- Production environments require CR approval for write operations

**Behavior**:
- ITSM_ENABLED=true: Write operations require ServiceNow CR validation
- ITSM_LAB_MODE=true: CR format is validated but not checked against ServiceNow
- Both false: Write operations proceed without ITSM checks (development only)

## Decision 4: Skill Organization

**Decision**: Create 4 skills aligned with user stories from spec

| Skill | Tools | User Story |
|-------|-------|------------|
| aruba-cx-system | get_system_info, get_firmware, get_vsf_topology | P1: System Discovery |
| aruba-cx-interfaces | get_interfaces, get_lldp_neighbors, get_dom_diagnostics | P1: Interface Monitoring |
| aruba-cx-switching | get_vlans, get_mac_table, create_vlan, delete_vlan, configure_vlan | P2: Layer 2 Operations |
| aruba-cx-config | get_running_config, get_startup_config, save_config, issu_*, firmware_* | P2: Config Management |

**Rationale**:
- Maps directly to spec user stories for traceability
- Single responsibility per skill (Principle VII)
- Read-only skills (system, interfaces) vs mixed skills (switching, config) clearly separated
- Consistent with existing patterns (e.g., prisma-sdwan-topology, prisma-sdwan-config)

## Decision 5: Installation Method

**Decision**: Clone community server to mcp-servers/aruba-cx-mcp/ via install.sh

**Rationale**:
- Consistent with other community MCP server integrations (Prisma SD-WAN, GitLab, etc.)
- Allows for local customization if needed
- Dependencies installed via pip/uv from requirements.txt
- Updates via git pull in install.sh

**Install Pattern**:
```bash
ARUBA_CX_MCP_DIR="$MCP_DIR/aruba-cx-mcp"
if [ -d "$ARUBA_CX_MCP_DIR" ]; then
    git -C "$ARUBA_CX_MCP_DIR" pull --quiet
else
    git clone https://github.com/slientnight/aruba-cx-mcp-server.git "$ARUBA_CX_MCP_DIR"
fi
```

## Decision 6: Tool Mapping

**Decision**: Map all 16 community server tools to NetGeniusClaw

### Read-Only Tools (11)
| Tool | Purpose |
|------|---------|
| get_system_info | Hostname, model, serial, version, uptime |
| get_interfaces | Interface admin/oper state, speed, description |
| get_vlans | VLAN ID, name, port membership |
| get_running_config | Current active configuration |
| get_startup_config | Saved boot configuration |
| get_routing_table | IP routing entries |
| get_lldp_neighbors | LLDP neighbor device info |
| get_mac_table | MAC address to port mappings |
| get_dom_diagnostics | Optical transceiver power/temp with thresholds |
| get_issu_status | In-Service Software Upgrade state |
| get_firmware_info | Software version and image details |
| get_vsf_topology | VSF member roles and serial numbers |

### Write Tools (5)
| Tool | Purpose | ITSM Required |
|------|---------|---------------|
| configure_interface | Set interface admin state, description | Yes |
| create_vlan / configure_vlan / delete_vlan | VLAN management | Yes |
| save_config | Copy running to startup | Yes |
| issu_upgrade | Initiate In-Service Software Upgrade | Yes |
| upload_firmware / download_firmware | Firmware management | Yes |

## Decision 7: Environment Variables

**Decision**: Use the following environment variables

| Variable | Purpose | Required |
|----------|---------|----------|
| ARUBA_CX_TARGETS | JSON array of switch targets | Yes (or ARUBA_CX_CONFIG) |
| ARUBA_CX_CONFIG | Path to config file with targets | Alternative to ARUBA_CX_TARGETS |
| ARUBA_CX_TIMEOUT | Request timeout in seconds (default: 30) | No |
| ITSM_ENABLED | Enable ServiceNow CR validation | No (default: false) |
| ITSM_LAB_MODE | Validate CR format only (no ServiceNow call) | No (default: false) |

**Rationale**: Follows existing patterns from other MCP servers; credentials in env vars per Principle XIII.

## Open Questions Resolved

1. **Q: Does the server support all Aruba CX firmware versions?**
   A: Requires AOS-CX 10.x or later with REST API enabled. Default API version is v10.13.

2. **Q: How are multiple switches handled?**
   A: ARUBA_CX_TARGETS env var accepts JSON array; each query specifies target by name.

3. **Q: What happens if a switch is unreachable?**
   A: Server returns connection error with switch name; partial results for multi-switch queries.

4. **Q: Is VSF supported on all CX models?**
   A: VSF is model-dependent; get_vsf_topology returns "not configured" for non-VSF switches.

## References

- Community MCP Server: https://github.com/slientnight/aruba-cx-mcp-server
- Aruba CX REST API Documentation: https://developer.arubanetworks.com/aruba-cx/docs
- NetGeniusClaw Constitution: `.specify/memory/constitution.md`
- Similar Integration: specs/013-prisma-sdwan-mcp-server/
