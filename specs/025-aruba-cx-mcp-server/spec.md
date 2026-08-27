# Feature Specification: Aruba CX MCP Server Integration

**Feature Branch**: `025-aruba-cx-mcp-server`
**Created**: 2026-04-08
**Status**: Draft
**Input**: User description: "Integrate community Aruba CX MCP server into NetGeniusClaw with 16 tools (11 read-only, 5 write) for managing Aruba CX switches, creating 4 skills and updating all full-stack artifacts"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - System and Firmware Discovery (Priority: P1)

As a network engineer, I want to discover Aruba CX switch system information, firmware versions, and VSF (Virtual Switching Framework) topology so I can inventory my switching infrastructure and plan upgrades.

**Why this priority**: System discovery is the foundational capability - engineers need to understand what switches exist, their versions, and cluster topology before performing any other operations. This is read-only and safe to use without change management.

**Independent Test**: Can be fully tested by querying any Aruba CX switch for system info, firmware details, and VSF membership. Delivers immediate value for inventory and audit use cases.

**Acceptance Scenarios**:

1. **Given** valid switch credentials are configured, **When** I request system information, **Then** I receive hostname, model, serial number, uptime, and software version
2. **Given** a VSF-enabled switch cluster, **When** I query VSF topology, **Then** I see all member switches with their roles (commander/standby/member) and serial numbers
3. **Given** a standalone switch (no VSF), **When** I query VSF topology, **Then** I receive a clear indication that VSF is not configured
4. **Given** multiple switches configured as targets, **When** I query a specific switch by name, **Then** only that switch's information is returned

---

### User Story 2 - Interface and Connectivity Monitoring (Priority: P1)

As a network engineer, I want to view interface status, LLDP neighbor relationships, and optical transceiver health so I can troubleshoot connectivity issues and monitor link quality.

**Why this priority**: Interface monitoring is essential for day-to-day network operations. Engineers need visibility into port status, neighbor discovery, and optics health to resolve connectivity problems quickly. This is read-only and safe.

**Independent Test**: Can be tested by querying interface states, LLDP neighbors, and DOM (Digital Optical Monitoring) data from any Aruba CX switch. Delivers immediate troubleshooting value.

**Acceptance Scenarios**:

1. **Given** a switch with active interfaces, **When** I request interface status, **Then** I see each interface's admin state, operational state, speed, and description
2. **Given** a switch connected to LLDP-enabled neighbors, **When** I query LLDP neighbors, **Then** I see remote device name, port, and capabilities for each discovered neighbor
3. **Given** interfaces with optical transceivers, **When** I request DOM diagnostics, **Then** I see TX/RX power levels, temperature, and threshold violation alerts
4. **Given** a DOM reading exceeds warning thresholds, **When** I view optics health, **Then** the threshold violation is clearly flagged

---

### User Story 3 - Switching and Layer 2 Operations (Priority: P2)

As a network engineer, I want to view VLANs and MAC address tables so I can understand Layer 2 segmentation and track endpoint locations across my switching fabric.

**Why this priority**: VLAN and MAC visibility supports network segmentation verification and endpoint troubleshooting. Slightly lower priority than P1 because system/interface visibility is typically needed first.

**Independent Test**: Can be tested by querying VLAN configurations and MAC address tables from any Aruba CX switch. Useful for security audits and endpoint location.

**Acceptance Scenarios**:

1. **Given** a switch with configured VLANs, **When** I request VLAN information, **Then** I see VLAN IDs, names, and associated interfaces
2. **Given** a switch with learned MAC addresses, **When** I query the MAC table, **Then** I see MAC addresses, associated VLANs, and learned ports
3. **Given** a specific MAC address search, **When** I query for that MAC, **Then** I find which switch port the MAC is learned on

---

### User Story 4 - Configuration and Change Management (Priority: P2)

As a network engineer, I want to view running and startup configurations, save configuration changes, and perform software upgrades (ISSU) so I can manage switch configurations through proper change control workflows.

**Why this priority**: Configuration management and ISSU are critical for maintaining network stability but involve write operations. These require ITSM gating per the NetGeniusClaw constitution for production environments.

**Independent Test**: Can be tested in a lab environment by viewing configs, saving changes, and performing ISSU operations. Production use requires change request approval.

**Acceptance Scenarios**:

1. **Given** valid credentials with read access, **When** I request running configuration, **Then** I receive the current active configuration
2. **Given** valid credentials with read access, **When** I request startup configuration, **Then** I receive the saved configuration that loads on reboot
3. **Given** write access and an approved change request (if ITSM enabled), **When** I save the running configuration, **Then** the configuration persists to startup
4. **Given** a firmware image available and ITSM approval, **When** I initiate an ISSU operation, **Then** the switch upgrades with minimal traffic disruption
5. **Given** ITSM is enabled without an approved change request, **When** I attempt a write operation, **Then** the operation is blocked with a clear message

---

### Edge Cases

- What happens when switch credentials are invalid or expired? System returns clear authentication error without exposing credential details
- What happens when a switch is unreachable? System returns connection timeout with the specific switch name that failed
- What happens when querying a switch model that doesn't support certain features (e.g., DOM on non-optical ports)? System returns appropriate "not applicable" response
- What happens when VSF split-brain occurs? System reflects the topology state visible from the queried member
- What happens when ISSU fails mid-upgrade? System reports the failure state and current firmware status
- What happens when multiple switches are configured but only some are reachable? System returns partial results with clear indication of which switches failed

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow querying system information (hostname, model, serial, version, uptime) from configured Aruba CX switches
- **FR-002**: System MUST allow querying interface status including admin state, operational state, speed, and description
- **FR-003**: System MUST allow querying VLAN configurations with IDs, names, and port assignments
- **FR-004**: System MUST allow querying running and startup configurations
- **FR-005**: System MUST allow querying routing table entries
- **FR-006**: System MUST allow querying LLDP neighbor information with remote device details
- **FR-007**: System MUST allow querying MAC address tables with VLAN and port associations
- **FR-008**: System MUST allow querying optical transceiver DOM data with threshold violation detection
- **FR-009**: System MUST allow querying ISSU (In-Service Software Upgrade) status
- **FR-010**: System MUST allow querying firmware/software version details
- **FR-011**: System MUST allow querying VSF topology including member roles and serial numbers
- **FR-012**: System MUST allow configuring interface parameters (admin state, description) with ITSM gating
- **FR-013**: System MUST allow creating, modifying, and deleting VLANs with ITSM gating
- **FR-014**: System MUST allow saving running configuration to startup with ITSM gating
- **FR-015**: System MUST allow initiating ISSU operations with ITSM gating
- **FR-016**: System MUST allow firmware upload and download operations with ITSM gating
- **FR-017**: System MUST support multiple switch targets from a single configuration
- **FR-018**: System MUST use credentials from environment variables only (no hardcoded secrets)
- **FR-019**: System MUST integrate with ITSM (ServiceNow) for write operation approval when enabled
- **FR-020**: System MUST provide clear error messages for authentication, connectivity, and operational failures

### Key Entities

- **Switch Target**: A configured Aruba CX switch with name, host address, credentials, and connection parameters
- **Interface**: A physical or logical port on a switch with status, configuration, and optional DOM data
- **VLAN**: A Layer 2 broadcast domain with ID, name, and port membership
- **VSF Member**: A switch participating in a Virtual Switching Framework cluster with role and serial number
- **Configuration**: The running or startup configuration state of a switch
- **Firmware**: Software image information including version, status, and upgrade capability

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Network engineers can retrieve system information from any configured Aruba CX switch within 5 seconds
- **SC-002**: Network engineers can view interface status across all ports on a switch within 10 seconds
- **SC-003**: Network engineers can identify LLDP neighbors for troubleshooting in a single query
- **SC-004**: Network engineers can locate a MAC address across the switching fabric within 30 seconds
- **SC-005**: Network engineers can view optical health with threshold alerts without manual threshold comparison
- **SC-006**: All 16 tools (11 read, 5 write) are accessible through natural language requests via NetGeniusClaw
- **SC-007**: Write operations are blocked without ITSM approval when ITSM integration is enabled
- **SC-008**: Installation completes successfully with a single command (install.sh)
- **SC-009**: New skills appear in NetGeniusClaw's skill inventory after installation (4 new skills)
- **SC-010**: 95% of switch queries complete successfully when the target switch is reachable

## Assumptions

- Users have network connectivity to their Aruba CX switches from the NetGeniusClaw host
- Users have valid REST API credentials for their Aruba CX switches (username/password with appropriate privileges)
- Aruba CX switches are running firmware that supports the REST API (AOS-CX 10.x or later)
- The community MCP server (https://github.com/slientnight/aruba-cx-mcp-server) is maintained and functional
- Users understand the difference between read-only operations (safe) and write operations (require change control)
- Lab mode (ITSM_LAB_MODE) is available for testing write operations without ServiceNow integration
- Default connection parameters (port 443, API version v10.13, SSL verification enabled) are appropriate for most deployments
- Users will configure switch targets via environment variable (ARUBA_CX_TARGETS) or config file (aruba-cx-config.json)
