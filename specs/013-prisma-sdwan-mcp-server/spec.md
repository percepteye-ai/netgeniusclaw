# Feature Specification: Prisma SD-WAN MCP Server Integration

**Feature Branch**: `013-prisma-sdwan-mcp-server`
**Created**: 2026-04-03
**Status**: Draft
**Input**: User description: "Add Palo Alto Networks Prisma SD-WAN MCP server integration. Community MCP server from https://github.com/iamdheerajdubey/prisma-sdwan-mcp provides 15 read-only tools: get_sites, get_elements, get_machines, get_interfaces, get_wan_interfaces, get_policy_sets, get_security_zones, get_bgp_peers, get_static_routes, get_element_status, get_software_status, get_app_defs, get_topology, get_events, get_alarms, plus generate_site_config for YAML generation. Uses OAuth2 auth via prisma_sase SDK with PAN_CLIENT_ID, PAN_CLIENT_SECRET, PAN_TSG_ID, PAN_REGION env vars. Skills should include: prisma-sdwan-topology (sites, elements, topology), prisma-sdwan-status (element status, software status, events, alarms), prisma-sdwan-config (interfaces, routes, BGP, policies, security zones), prisma-sdwan-apps (app definitions). Read-only operations - no ServiceNow CR gating required. Need to update install.sh, README.md, openclaw.json, SOUL.md skill index, and create SKILL.md files."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - SD-WAN Topology Discovery (Priority: P1)

When NetGeniusClaw needs to understand the Prisma SD-WAN fabric topology, it can discover all sites, ION devices (elements), and their interconnections through natural language queries, providing visibility into the entire SD-WAN deployment.

**Why this priority**: Topology discovery is the foundation — understanding what sites and devices exist is required before any operational queries about status, configuration, or troubleshooting can be meaningful.

**Independent Test**: Query sites and elements from the Prisma SD-WAN controller, display the topology, and verify the data matches the controller dashboard.

**Acceptance Scenarios**:

1. **Given** NetGeniusClaw is connected to Prisma SD-WAN, **When** the user asks to "list all SD-WAN sites", **Then** all sites are returned with names, IDs, and element counts
2. **Given** a Prisma SD-WAN deployment with multiple sites, **When** the user asks to "show elements at site headquarters", **Then** all ION devices at that site are listed with status
3. **Given** a complex SD-WAN fabric, **When** the user asks to "show the SD-WAN topology", **Then** a complete topology view is returned showing site-to-site relationships
4. **Given** a Prisma SD-WAN deployment, **When** the user asks to "show hardware inventory", **Then** machine details (serial numbers, models) are displayed

---

### User Story 2 - SD-WAN Health and Status Monitoring (Priority: P2)

When NetGeniusClaw needs to assess the health of the SD-WAN fabric, it can query element status, software versions, active alarms, and recent events to identify issues and verify operational state.

**Why this priority**: After knowing what exists (topology), the next most valuable capability is understanding the current health and any active issues requiring attention.

**Independent Test**: Query element status and alarms from Prisma SD-WAN, verify status matches controller, and confirm events are returned in chronological order.

**Acceptance Scenarios**:

1. **Given** a running SD-WAN fabric, **When** the user asks to "check status of all ION devices", **Then** operational health status is returned for each element
2. **Given** ION devices running different software versions, **When** the user asks to "show software versions for all elements", **Then** current versions and upgrade state are displayed
3. **Given** active issues in the fabric, **When** the user asks to "show SD-WAN alarms", **Then** critical and major alarms are listed with severity and affected components
4. **Given** ongoing operations, **When** the user asks to "show recent SD-WAN events", **Then** the most recent events are returned with timestamps and descriptions

---

### User Story 3 - SD-WAN Configuration Inspection (Priority: P3)

When NetGeniusClaw needs to inspect SD-WAN configuration details, it can query interfaces, routing (BGP peers, static routes), policies, and security zones to understand how traffic is being handled.

**Why this priority**: Configuration inspection enables troubleshooting and verification of SD-WAN behavior, building on topology and status knowledge.

**Independent Test**: Query interfaces, BGP peers, and static routes for a specific site/element, verify data matches controller configuration.

**Acceptance Scenarios**:

1. **Given** an ION device at a site, **When** the user asks to "show interfaces on element router1", **Then** all LAN and WAN interfaces are listed with configuration details
2. **Given** a site with WAN connectivity, **When** the user asks to "show WAN interfaces at site branch1", **Then** WAN interface configurations are displayed
3. **Given** an element with BGP peering, **When** the user asks to "show BGP peers on element router1", **Then** BGP peer configurations are returned
4. **Given** an element with static routing, **When** the user asks to "show static routes on element router1", **Then** static route tables are displayed
5. **Given** a policy-driven fabric, **When** the user asks to "list SD-WAN policy sets", **Then** all policy set definitions are returned
6. **Given** security segmentation, **When** the user asks to "show security zones", **Then** security zone definitions are displayed

---

### User Story 4 - Application Visibility (Priority: P4)

When NetGeniusClaw needs to understand application awareness in the SD-WAN fabric, it can query application definitions to see what applications are recognized and how they're classified.

**Why this priority**: Application definitions drive SD-WAN policy decisions. Understanding what apps are defined completes the configuration picture.

**Independent Test**: Query application definitions and verify the list matches the Prisma SD-WAN controller application library.

**Acceptance Scenarios**:

1. **Given** a Prisma SD-WAN deployment with application awareness, **When** the user asks to "list SD-WAN application definitions", **Then** all defined applications are returned with classification details
2. **Given** specific application needs, **When** the user asks to "show details for application Office365", **Then** the application definition and policies are displayed

---

### Edge Cases

- What happens when Prisma SD-WAN API credentials are invalid or expired?
- How does the system handle queries for sites or elements that don't exist?
- What happens when the Prisma SD-WAN controller is unreachable?
- How are large responses handled (deployments with hundreds of sites)?
- What happens when querying a site with no elements deployed?
- How does the system handle regional API endpoints (americas vs europe)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST connect to Prisma SD-WAN controller and authenticate via OAuth2
- **FR-002**: System MUST support configuration via environment variables (PAN_CLIENT_ID, PAN_CLIENT_SECRET, PAN_TSG_ID, PAN_REGION)
- **FR-003**: System MUST list all SD-WAN sites with names, IDs, and summary information
- **FR-004**: System MUST list ION devices (elements) with status and site association
- **FR-005**: System MUST retrieve hardware inventory (machines) with serial numbers and models
- **FR-006**: System MUST display interface configurations (LAN and WAN) per element
- **FR-007**: System MUST retrieve BGP peer configurations per site/element
- **FR-008**: System MUST retrieve static route tables per site/element
- **FR-009**: System MUST list policy set definitions
- **FR-010**: System MUST list security zone definitions
- **FR-011**: System MUST retrieve element operational health status
- **FR-012**: System MUST retrieve software version and upgrade state per element
- **FR-013**: System MUST list application definitions
- **FR-014**: System MUST retrieve network topology graph
- **FR-015**: System MUST retrieve recent events with configurable limit
- **FR-016**: System MUST retrieve active alarms (critical and major)
- **FR-017**: System MUST support YAML configuration generation for sites (generate_site_config)
- **FR-018**: System MUST NOT require ServiceNow Change Request gating (read-only operations)
- **FR-019**: System MUST record all operations in GAIT audit trail
- **FR-020**: System MUST handle API errors gracefully with informative error messages

### Key Entities

- **Site**: A physical or logical location in the SD-WAN fabric. Has a unique ID, name, and contains one or more elements.
- **Element**: An ION device (router/edge device) deployed at a site. Has status, software version, interfaces, and routing configuration.
- **Machine**: Hardware inventory information for an element (serial number, model, hardware details).
- **Interface**: Network interface on an element (LAN or WAN). Has configuration details like IP addressing and circuit information.
- **Policy Set**: Traffic handling rules defining how applications are routed across the SD-WAN fabric.
- **Security Zone**: Network segmentation definitions for security policy enforcement.
- **Application Definition**: Classification rules for identifying application traffic.
- **Alarm**: Active alert indicating an issue requiring attention (critical or major severity).
- **Event**: Operational occurrence recorded for audit and troubleshooting purposes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can discover complete SD-WAN topology (sites, elements, connections) through natural language queries
- **SC-002**: All 4 skill categories (topology, status, config, apps) are functional and documented
- **SC-003**: Operations complete within 10 seconds for single-item requests (get site, get element status, etc.)
- **SC-004**: Health status queries return accurate element operational state matching controller dashboard
- **SC-005**: Alarms and events are retrievable with user-configurable limits
- **SC-006**: System handles authentication errors gracefully with clear remediation guidance
- **SC-007**: All operations are recorded in GAIT audit trail for session traceability
- **SC-008**: Integration works with both Americas and Europe regional API endpoints

## Assumptions

- Prisma SD-WAN controller is accessible over the network
- User has valid Palo Alto Networks service account credentials with appropriate API access
- The community MCP server (https://github.com/iamdheerajdubey/prisma-sdwan-mcp) is stable and functional
- MCP server will be cloned/installed via install.sh similar to other community MCP servers
- Read-only operations are acceptable for this scope (no configuration changes)
- This is an observability/monitoring feature — no production network changes, no ServiceNow CR gating required
- YAML configuration generation (generate_site_config) creates local files only, does not push to controller
- Environment variables will be provided via .env file (PAN_CLIENT_ID, PAN_CLIENT_SECRET, PAN_TSG_ID, PAN_REGION)
