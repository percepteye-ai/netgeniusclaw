# Feature Specification: Blender 3D Network Visualization

**Feature Branch**: `024-blender-3d-viz`
**Created**: 2026-04-05
**Status**: Draft
**Input**: User description: "Integrate the community Blender MCP server (github.com/ahujasid/blender-mcp) to enable 3D network topology visualization. Goal: User says draw the network topology using CDP data in Slack and local Blender renders a 3D visualization. Blender runs on Windows, NetGeniusClaw in WSL. MCP server connects via socket on port 9876."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Draw Network Topology from CDP Data (Priority: P1)

A network engineer wants to visualize their network topology in 3D by asking NetGeniusClaw to draw the network using CDP neighbor information. They type a natural language command in Slack, and Blender renders a 3D scene showing devices as objects connected by links.

**Why this priority**: This is the core use case that delivers immediate value - transforming abstract network neighbor data into a tangible 3D visualization that aids understanding and documentation.

**Independent Test**: Can be fully tested by sending a Slack message to NetGeniusClaw requesting a topology drawing and observing that Blender renders devices and connections. Delivers immediate visual value even without other features.

**Acceptance Scenarios**:

1. **Given** Blender is running with the MCP addon connected, **When** user says "draw the network topology using CDP data" in Slack, **Then** Blender renders 3D objects representing network devices with connections between neighbors.

2. **Given** CDP data shows 5 devices with neighbor relationships, **When** user requests topology visualization, **Then** all 5 devices appear as distinct 3D objects with visible connections between adjacent devices.

3. **Given** network has different device types (routers, switches, firewalls), **When** topology is rendered, **Then** each device type is visually distinguishable (different colors or shapes).

---

### User Story 2 - Export Visualization for Documentation (Priority: P2)

A network engineer has created a 3D topology visualization and wants to export it as an image or video for inclusion in documentation, presentations, or reports.

**Why this priority**: Extends the value of P1 by making visualizations shareable and permanent. Without export, visualizations are ephemeral and limited to local viewing.

**Independent Test**: Can be tested by requesting an export of the current Blender scene and verifying an image file is created that can be opened in standard viewers.

**Acceptance Scenarios**:

1. **Given** a 3D topology is rendered in Blender, **When** user says "export the topology as PNG", **Then** an image file is created and the file path is returned.

2. **Given** a rendered topology, **When** user requests a video export, **Then** a video file is created showing the 3D scene.

---

### User Story 3 - Customize Visualization Appearance (Priority: P3)

A network engineer wants to modify the appearance of the 3D visualization, such as changing colors, adding labels, or highlighting specific devices.

**Why this priority**: Enhances usability but not essential for core functionality. Users can work with default visualizations initially.

**Independent Test**: Can be tested by requesting a color change for a specific device and observing the visual update in Blender.

**Acceptance Scenarios**:

1. **Given** a rendered topology, **When** user says "color router-1 red", **Then** the specified device changes to red in Blender.

2. **Given** a rendered topology, **When** user says "add labels to all devices", **Then** device hostnames appear as text labels near each 3D object.

---

### Edge Cases

- What happens when Blender is not running or the addon is not connected? System should return a clear error message indicating Blender connection is unavailable.
- What happens when CDP data is empty or contains no neighbors? System should inform user that no topology data is available to visualize.
- What happens when the network exceeds 25 devices? System renders up to 25 devices and displays a warning that the topology has been truncated due to complexity limits.
- How does the system handle devices with the same hostname? Each device should be rendered as a distinct object even if names conflict.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST connect to a local Blender instance via socket connection
- **FR-002**: System MUST translate natural language topology requests into 3D rendering commands
- **FR-003**: System MUST render network devices as distinct 3D objects in Blender
- **FR-004**: System MUST render connections between neighbor devices as visual links
- **FR-005**: System MUST support exporting the current Blender scene as an image file
- **FR-006**: System MUST differentiate device types visually (routers vs switches vs firewalls)
- **FR-007**: System MUST provide clear error messages when Blender is unavailable
- **FR-008**: System MUST allow users to modify object colors via natural language commands
- **FR-009**: System MUST support cross-network connectivity (WSL to Windows Blender)
- **FR-010**: System MUST render up to 25 devices and warn users when topology exceeds this limit

### Key Entities

- **Network Device**: A node in the topology representing a router, switch, firewall, or other network equipment. Attributes include hostname, device type, and neighbor relationships.
- **Connection/Link**: A visual representation of the relationship between two neighboring devices discovered via CDP/LLDP.
- **3D Scene**: The Blender workspace containing all rendered devices and connections that can be manipulated and exported.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can request a 3D topology visualization using natural language and see results in Blender within 30 seconds
- **SC-002**: 100% of devices from CDP neighbor data are represented in the rendered topology
- **SC-003**: Users can export visualizations to shareable image formats with a single command
- **SC-004**: Device types are visually distinguishable without requiring user customization
- **SC-005**: System provides clear feedback when Blender connection is unavailable (no silent failures)
- **SC-006**: Users unfamiliar with Blender can create topology visualizations without Blender knowledge

## Clarifications

### Session 2026-04-05

- Q: What is the device count threshold for topology rendering? → A: Render up to 25 devices; warn above that

## Assumptions

- User has Blender 3.0+ installed locally on Windows (Blender is a GUI application requiring a display)
- User has installed and enabled the BlenderMCP addon in Blender
- User has started the Blender MCP connection before issuing commands
- NetGeniusClaw runs in WSL and can reach the Windows host via network (socket connection)
- CDP/LLDP neighbor data is available from existing pyATS or device query capabilities
- Default visual representations (cube for router, etc.) are acceptable; custom 3D models are out of scope for v1
- Real-time streaming of topology changes is out of scope; visualizations are point-in-time snapshots
- Animation of traffic flows is out of scope for initial implementation
