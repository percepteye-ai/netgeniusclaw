# Feature Specification: GNS3 MCP Server and Skills

**Feature Branch**: `012-gns3-mcp-server`
**Created**: 2026-04-02
**Status**: Draft
**Input**: User description: "Add GNS3 network lab management MCP server and skills. Similar to cml-* and clab-* skills. GNS3 REST API v3 provides: project lifecycle (create, open, close, delete, clone, export/import), node operations (create from templates, start, stop, suspend, reload, isolate, console access), link management (create, delete, packet capture start/stop/stream), snapshot management (create, restore, delete), template management (list, create, duplicate), compute server management (list Docker/VirtualBox/VMware VMs), and file operations. Skills should include: gns3-project-lifecycle, gns3-node-operations, gns3-link-management, gns3-packet-capture, gns3-snapshot-ops. Lab-only operations - no ServiceNow CR gating required. Must support remote GNS3 servers via compute API."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Project Lifecycle Management (Priority: P1)

When NetGeniusClaw needs to set up a network lab environment for testing, training, or proof-of-concept work, it can create, manage, and tear down GNS3 projects (labs) through natural language commands, similar to existing CML and ContainerLab skills.

**Why this priority**: Project management is the foundation — without the ability to create and manage projects, no other GNS3 operations are possible. This is the minimum viable functionality.

**Independent Test**: Create a new GNS3 project, list existing projects, open/close the project, and delete it when done. Verifies basic connectivity and core operations.

**Acceptance Scenarios**:

1. **Given** NetGeniusClaw is connected to a GNS3 server, **When** the user asks to "create a new GNS3 lab called routing-test", **Then** a new project is created and the project ID is returned
2. **Given** multiple GNS3 projects exist, **When** the user asks to "list my GNS3 labs", **Then** all projects are listed with names, status, and node counts
3. **Given** an existing GNS3 project, **When** the user asks to "close the routing-test lab", **Then** the project is closed and resources are released
4. **Given** an existing GNS3 project, **When** the user asks to "delete the routing-test lab", **Then** the project and all associated resources are removed

---

### User Story 2 - Node Operations (Priority: P2)

When NetGeniusClaw needs to build out a lab topology, it can add network devices from templates, control their power state, and access their consoles to configure or troubleshoot them.

**Why this priority**: After creating a project, users need to populate it with devices. Node operations are essential for any meaningful lab work.

**Independent Test**: Add a router node from a template, start the node, verify it's running, stop the node, and remove it. Demonstrates full node lifecycle.

**Acceptance Scenarios**:

1. **Given** an open GNS3 project and available templates, **When** the user asks to "add a Cisco IOSv router to my lab", **Then** a node is created from the matching template with appropriate defaults
2. **Given** a project with nodes, **When** the user asks to "start all nodes in routing-test", **Then** all nodes in the project are powered on
3. **Given** a running node, **When** the user asks to "show console output for router1", **Then** the console connection information or recent output is displayed
4. **Given** a running node, **When** the user asks to "stop router1", **Then** the node is gracefully stopped
5. **Given** a project with nodes, **When** the user asks to "isolate router1", **Then** all links to that node are disabled without deleting them

---

### User Story 3 - Link Management and Topology Building (Priority: P3)

When NetGeniusClaw needs to connect devices in a lab topology, it can create and manage links between node interfaces, enabling network connectivity for testing scenarios.

**Why this priority**: Links connect nodes into a functional topology. Without links, nodes are isolated and cannot communicate.

**Independent Test**: Create a link between two nodes, verify connectivity, delete the link. Demonstrates topology manipulation.

**Acceptance Scenarios**:

1. **Given** two nodes in a project, **When** the user asks to "connect router1 eth0 to switch1 eth0", **Then** a link is created between the specified interfaces
2. **Given** an existing link, **When** the user asks to "list all links in routing-test", **Then** all links are displayed with source/destination node and interface information
3. **Given** an existing link, **When** the user asks to "delete the link between router1 and switch1", **Then** the link is removed

---

### User Story 4 - Packet Capture (Priority: P4)

When NetGeniusClaw needs to troubleshoot network issues in a lab or capture traffic for analysis, it can start and stop packet captures on links and retrieve the captured data.

**Why this priority**: Packet capture is essential for network troubleshooting and learning. It enables deep analysis of lab traffic.

**Independent Test**: Start a capture on a link, generate some traffic, stop the capture, and retrieve/stream the PCAP data.

**Acceptance Scenarios**:

1. **Given** an active link between two nodes, **When** the user asks to "start capturing traffic on the link between router1 and router2", **Then** packet capture begins on that link
2. **Given** an active capture, **When** the user asks to "stop the capture on router1-router2 link", **Then** the capture stops and the PCAP file is available
3. **Given** a completed capture, **When** the user asks to "get the capture file from router1-router2", **Then** the PCAP data can be retrieved or handed off to packet-analysis skill

---

### User Story 5 - Snapshot Management (Priority: P5)

When NetGeniusClaw needs to save or restore lab state (e.g., before testing a risky configuration), it can create snapshots and restore to previous states.

**Why this priority**: Snapshots enable safe experimentation by allowing rollback. Important for training and testing scenarios.

**Independent Test**: Create a snapshot of a project, make changes, restore the snapshot, verify state is restored.

**Acceptance Scenarios**:

1. **Given** an open project with configured nodes, **When** the user asks to "create a snapshot called baseline", **Then** a snapshot of the current project state is saved
2. **Given** a project with snapshots, **When** the user asks to "list snapshots for routing-test", **Then** all available snapshots are listed with names and timestamps
3. **Given** an existing snapshot, **When** the user asks to "restore routing-test to baseline snapshot", **Then** the project is restored to the saved state

---

### Edge Cases

- What happens when the GNS3 server is unreachable or authentication fails?
- How does the system handle requests for templates that don't exist?
- What happens when trying to start a node without sufficient compute resources?
- How are operations handled when a project is locked by another user?
- What happens when trying to delete a project with running nodes?
- How does the system handle remote compute servers that are offline?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST connect to GNS3 server and verify connectivity before operations
- **FR-002**: System MUST support GNS3 REST API v3 authentication (username/password or token)
- **FR-003**: System MUST list, create, open, close, delete, clone, and export/import projects
- **FR-004**: System MUST list available node templates from the GNS3 server
- **FR-005**: System MUST create nodes from templates with configurable properties (name, position, startup config)
- **FR-006**: System MUST start, stop, suspend, reload, and delete individual nodes
- **FR-007**: System MUST start, stop, suspend, and reload all nodes in a project with a single command
- **FR-008**: System MUST isolate and un-isolate nodes (disable/enable all links without deletion)
- **FR-009**: System MUST create and delete links between node interfaces
- **FR-010**: System MUST start, stop, and stream packet captures on links
- **FR-011**: System MUST create, list, and restore project snapshots
- **FR-012**: System MUST delete snapshots
- **FR-013**: System MUST list available compute servers (local, remote Docker, VirtualBox, VMware)
- **FR-014**: System MUST retrieve node console connection information (telnet/VNC details)
- **FR-015**: System MUST NOT require ServiceNow Change Request gating (lab-only operations)
- **FR-016**: System MUST record all operations in GAIT audit trail

### Key Entities

- **Project**: A GNS3 lab environment containing nodes, links, and drawings. Has a unique ID, name, and status (opened/closed).
- **Node**: A network device instance in a project (router, switch, firewall, etc.). Created from a template, has interfaces and power state.
- **Link**: A connection between two node interfaces. Can have packet capture enabled.
- **Template**: A device definition that can be instantiated as nodes (e.g., "Cisco IOSv", "Arista vEOS").
- **Snapshot**: A saved state of a project that can be restored.
- **Compute**: A server (local or remote) that runs the actual node emulations (QEMU, Docker, VirtualBox, VMware, Dynamips).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create and fully populate a GNS3 lab topology through natural language in under 5 minutes
- **SC-002**: All 5 skill categories (project, node, link, capture, snapshot) are functional and documented
- **SC-003**: Operations complete within 10 seconds for single-item requests (create node, start node, etc.)
- **SC-004**: Packet captures can be started/stopped and PCAP data retrieved successfully
- **SC-005**: Snapshots can be created and restored, returning the lab to the exact saved state
- **SC-006**: System handles GNS3 server errors gracefully with informative error messages
- **SC-007**: All operations are recorded in GAIT audit trail for session traceability

## Assumptions

- GNS3 server is running and accessible over the network (local or remote)
- GNS3 server has REST API v3 enabled (GNS3 version 2.2.0 or later)
- User has valid credentials for GNS3 server authentication
- Node templates are pre-configured on the GNS3 server (template management is read-only in this scope)
- Compute resources (local or remote) are available and configured on the GNS3 server
- This is a lab-only feature — no production network impact, no ServiceNow CR gating required
- Packet captures will be handed off to existing packet-analysis skill for deep inspection
- GNS3 server URL and credentials will be provided via environment variables (GNS3_URL, GNS3_USER, GNS3_PASSWORD)
