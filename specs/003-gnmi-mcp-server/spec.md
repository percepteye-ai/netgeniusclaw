# Feature Specification: gNMI Streaming Telemetry MCP Server

**Feature Branch**: `003-gnmi-mcp-server`
**Created**: 2026-03-26
**Status**: Draft
**Input**: User description: "gNMI Streaming Telemetry MCP Server - Build a new MCP server for gNMI (gRPC Network Management Interface) streaming telemetry. Enables model-driven telemetry subscriptions, gNMI Get/Set operations, and real-time network state streaming."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Query Device State via gNMI Get (Priority: P1)

As a network engineer, I want to query device operational and
configuration state using structured YANG model paths via gNMI Get
(e.g., interfaces, BGP neighbors, OSPF adjacencies, system health)
so I receive machine-parseable, model-driven data instead of
unstructured CLI output that requires fragile regex parsing.

**Why this priority**: gNMI Get is the foundational read operation.
Every other capability (subscriptions, set, model browsing) depends
on the ability to connect to a gNMI-enabled device and retrieve
structured state. This replaces the brittle CLI-scraping approach
for any gNMI-capable device, delivering immediate value for
day-to-day operational queries.

**Independent Test**: Can be fully tested by issuing a gNMI Get
request for a known YANG path (e.g., openconfig-interfaces) against
a single gNMI-capable device and verifying structured JSON/protobuf
data is returned with correct values matching the device state.

*Acceptance Scenarios**:*

1. **Given** a gNMI-capable device is reachable and credentials are
   configured via environment variables,
   **When** the operator requests "get interface state from device
   router1 using gNMI",
   **Then** the system returns structured interface data (name,
   oper-status, admin-status, counters, description, IP addresses)
   organized by the OpenConfig or native YANG model hierarchy.

2. **Given** a gNMI-capable device with BGP configured,
   **When** the operator requests "get BGP neighbors from router1
   via gNMI",
   **Then** the system returns all BGP neighbor entries with
   peer-address, peer-AS, session-state, prefixes-received, and
   uptime in structured format.

3. **Given** a gNMI-capable device is reachable,
   **When** the operator requests a gNMI Get for a YANG path that
   does not exist on the device,
   **Then** the system returns a clear error message indicating the
   path is not supported by the device, without exposing internal
   connection details or credentials.

4. **Given** a gNMI-capable device is reachable,
   **When** the operator requests a gNMI Get with a broad path
   (e.g., "/" root path),
   **Then** the system returns the data organized by YANG module
   and subtree, truncating or paginating if the response exceeds
   a reasonable size threshold, with a message indicating the
   result was truncated.

5. **Given** the target device is unreachable or the gNMI port is
   closed,
   **When** the operator attempts a gNMI Get,
   **Then** the system returns a descriptive connectivity error
   (timeout, connection refused, TLS handshake failure) without
   exposing credentials or certificate contents.

---

### User Story 2 - Subscribe to Real-Time Telemetry Streams (Priority: P2)

As a network engineer monitoring a live network, I want to set up
streaming telemetry subscriptions for specific YANG paths (interface
counters, BGP state changes, CPU utilization, memory usage) so I
receive real-time state change notifications instead of relying on
periodic polling or CLI scraping intervals.

**Why this priority**: Streaming telemetry is the primary
differentiator of gNMI over traditional SNMP or CLI-based monitoring.
It enables event-driven awareness of network state changes (link
flaps, BGP session drops, threshold breaches) in real time, which
is critical for rapid incident detection and response.

**Independent Test**: Can be tested by creating a STREAM subscription
for interface oper-status on a device, toggling an interface
administratively, and verifying the subscription delivers the state
change notification within seconds.

**Acceptance Scenarios**:

1. **Given** a gNMI-capable device supports streaming telemetry,
   **When** the operator requests "subscribe to interface counters
   on router1 every 10 seconds",
   **Then** the system creates a SAMPLE subscription and returns
   periodic counter updates (in-octets, out-octets, in-errors,
   out-errors) at the requested interval in structured format.

2. **Given** a gNMI-capable device supports ON_CHANGE subscriptions,
   **When** the operator requests "subscribe to BGP neighbor state
   changes on router1",
   **Then** the system creates an ON_CHANGE subscription and
   delivers a notification each time a BGP neighbor transitions
   between states (Idle, Active, Established, etc.).

3. **Given** an active telemetry subscription is running,
   **When** the operator requests "stop subscription" or
   "unsubscribe",
   **Then** the system cleanly terminates the gRPC stream and
   confirms the subscription has been cancelled.

4. **Given** a subscription is active and the device becomes
   unreachable (link failure, device reboot),
   **When** the gRPC stream is interrupted,
   **Then** the system reports the subscription loss with the
   device identity and reason, and does not silently fail.

5. **Given** the operator requests a subscription for a YANG path
   the device does not support for streaming,
   **When** the subscription request is sent,
   **Then** the system returns a clear error indicating the path
   is not available for subscription on that device.

---

### User Story 3 - Apply Configuration via gNMI Set (Priority: P3)

As a network engineer making a controlled change, I want to apply
configuration changes to devices via gNMI Set using structured YANG
models (instead of CLI commands) so that configuration changes are
validated against the YANG schema before being applied, reducing
the risk of syntax errors and misconfigurations.

**Why this priority**: gNMI Set is a write operation. Per the
NetGeniusClaw constitution, all write operations MUST be gated by ITSM
(ServiceNow Change Request) approval. This is lower priority than
read operations because it carries inherent risk and requires the
ITSM gating infrastructure to be in place.

**Independent Test**: Can be tested by requesting a gNMI Set to
change an interface description, verifying the system checks for a
valid ServiceNow CR number before proceeding, applying the change,
and confirming the new description via a subsequent gNMI Get.

**Acceptance Scenarios**:

1. **Given** a valid ServiceNow Change Request number is provided
   and the CR is in "Implement" state,
   **When** the operator requests "set interface Loopback0
   description to 'Management' on router1 via gNMI",
   **Then** the system validates the CR, applies the gNMI Set
   (update operation), and returns confirmation of the applied
   change with the YANG path and new value.

2. **Given** no ServiceNow Change Request number is provided,
   **When** the operator requests a gNMI Set operation,
   **Then** the system refuses the operation and returns a message
   stating that all configuration changes require an approved
   ServiceNow Change Request per the NetGeniusClaw constitution.

3. **Given** a valid CR is provided but the gNMI Set payload
   references an invalid YANG path or value,
   **When** the device rejects the Set operation,
   **Then** the system returns the device's error response
   (invalid path, invalid value, type mismatch) in a clear,
   actionable format without exposing credentials.

4. **Given** a valid CR is provided,
   **When** the operator requests a gNMI Set with a delete
   operation (e.g., remove a BGP neighbor),
   **Then** the system applies the delete, returns confirmation,
   and the GAIT audit trail records the CR number, operator,
   device, YANG path, operation type (delete), and timestamp.

5. **Given** a gNMI Set operation fails mid-transaction on the
   device,
   **When** the device returns an error after partial application,
   **Then** the system reports the failure clearly, including
   which parts succeeded and which failed, so the operator can
   take corrective action.

---

### User Story 4 - Browse YANG Model Capabilities (Priority: P4)

As a network engineer unfamiliar with a device's supported YANG
models, I want to explore what YANG modules and paths are available
on a specific device so I can construct valid gNMI Get, Set, or
Subscribe requests without consulting external documentation or
vendor-specific YANG model repositories.

**Why this priority**: Model browsing is a discovery and
enablement capability. While not required for core operations, it
dramatically improves usability by letting operators discover what
data is queryable on each device. This reduces trial-and-error
and support burden.

**Independent Test**: Can be tested by requesting "show YANG
capabilities on router1" and verifying the system returns a list
of supported YANG modules with version, organization, and
available paths.

**Acceptance Scenarios**:

1. **Given** a gNMI-capable device supports the gNMI Capabilities
   RPC,
   **When** the operator requests "show YANG capabilities on
   router1",
   **Then** the system returns a list of supported YANG models
   with module name, version/revision, and organization (e.g.,
   openconfig-interfaces 2.0.0, cisco-ios-xr-ifmgr-oper).

2. **Given** the operator knows a YANG module name,
   **When** the operator requests "show paths under
   openconfig-interfaces on router1",
   **Then** the system returns the tree of available YANG paths
   under that module (e.g., /interfaces/interface/state/oper-status,
   /interfaces/interface/state/counters/in-octets).

3. **Given** two devices from different vendors (e.g., Cisco IOS-XR
   and Arista EOS),
   **When** the operator requests YANG capabilities from both,
   **Then** the system returns vendor-specific and OpenConfig model
   lists for each, making it clear which models are shared and
   which are vendor-native.

4. **Given** a device that does not support the gNMI Capabilities
   RPC,
   **When** the operator requests YANG capabilities,
   **Then** the system returns a clear message indicating the
   device does not advertise its capabilities via gNMI.

---

### User Story 5 - Compare gNMI State vs CLI State for Validation (Priority: P5)

As a network engineer validating data accuracy, I want to compare
the state data returned by gNMI Get against the equivalent data
from CLI (via pyATS/existing MCP servers) for the same device so I
can confirm consistency between model-driven and CLI-scraped data
sources during the transition from CLI to gNMI.

**Why this priority**: This is a validation and migration-support
capability. During the transition period where NetGeniusClaw uses both
CLI scraping and gNMI, operators need confidence that gNMI returns
equivalent data. This builds trust in the new data source before
retiring CLI-based queries.

**Independent Test**: Can be tested by requesting "compare
interface state on router1 between gNMI and CLI" and verifying the
system returns a side-by-side comparison showing matching and
differing fields.

**Acceptance Scenarios**:

1. **Given** a device is reachable via both gNMI and CLI (pyATS),
   **When** the operator requests "compare interface state on
   router1 between gNMI and CLI",
   **Then** the system returns a structured comparison showing
   each interface with fields from both sources, highlighting
   any discrepancies in values (e.g., counter differences due to
   timing, naming convention differences).

2. **Given** a device is reachable via gNMI but not via CLI,
   **When** the operator requests a comparison,
   **Then** the system returns the gNMI data and a clear message
   indicating CLI data is unavailable for comparison.

3. **Given** both data sources return data but with expected
   differences (e.g., counter values differ slightly due to
   collection timing),
   **When** the comparison is presented,
   **Then** the system flags timing-sensitive fields as
   "expected variance" rather than true discrepancies.

---

### Edge Cases

- What happens when the device supports gNMI but uses a non-standard
  gRPC port?
- How does the system handle devices that require mutual TLS (mTLS)
  with client certificates for gNMI authentication?
- What happens when a gNMI Get request returns a response larger
  than the gRPC maximum message size?
- How does the system behave when a device supports gNMI but only
  for a subset of YANG models (e.g., OpenConfig but not native)?
- What happens when the operator specifies a vendor-specific YANG
  path (e.g., Cisco native model) against a device from a different
  vendor?
- How does the system handle encoding mismatches (e.g., requesting
  JSON_IETF when the device only supports PROTO)?
- What happens when multiple concurrent subscriptions are active
  and one device reboots?
- How does the system behave when a gNMI Set is attempted on a
  device that only supports gNMI Get (read-only gNMI)?
- What happens when the TLS certificate presented by the device
  does not match the expected hostname or CA?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support gNMI Get operations to retrieve
  device state and configuration data using YANG model paths.
- **FR-002**: System MUST support gNMI Subscribe operations with
  SAMPLE, ON_CHANGE, and TARGET_DEFINED subscription modes for
  streaming telemetry.
- **FR-003**: System MUST support gNMI Set operations (update,
  replace, delete) for applying configuration changes via YANG
  models.
- **FR-004**: System MUST gate all gNMI Set operations behind
  ServiceNow Change Request validation — no configuration change
  is permitted without an approved CR in "Implement" state.
- **FR-005**: System MUST support the gNMI Capabilities RPC to
  retrieve supported YANG models, versions, and encodings from
  target devices.
- **FR-006**: System MUST support multiple gNMI-capable vendor
  platforms including Cisco IOS-XR, Juniper Junos, Arista EOS,
  Nokia SR OS, and SONiC.
- **FR-007**: System MUST handle vendor-specific gNMI dialect
  differences (path encoding, origin prefixes, encoding formats)
  transparently so the operator does not need to know vendor
  internals.
- **FR-008**: System MUST log all gNMI operations (Get, Set,
  Subscribe, Capabilities) to the GAIT audit trail, including
  operator identity, target device, YANG path, operation type,
  timestamp, and result status.
- **FR-009**: All connection credentials (device IP addresses,
  gNMI ports, TLS certificates, CA bundles, usernames, passwords,
  tokens) MUST be read from environment variables at runtime.
- **FR-010**: System MUST support TLS-encrypted gNMI connections
  and MUST NOT allow insecure (plaintext) connections by default.
- **FR-011**: System MUST return structured, parseable results
  from gNMI responses, converting protobuf/gNMI-encoded data into
  human-readable structured output.
- **FR-012**: System MUST handle gNMI errors gracefully (connection
  refused, TLS failures, invalid paths, permission denied, RPC
  errors) and return descriptive messages without exposing
  credentials or certificate contents.
- **FR-013**: System MUST support comparison of gNMI-retrieved
  state data against CLI-retrieved data from existing pyATS-based
  MCP servers for the same device and data type.
- **FR-014**: System MUST support management of active telemetry
  subscriptions, including listing active subscriptions and
  cancelling them on demand.

### Key Entities

- **gNMI Target**: A network device reachable via the gNMI protocol,
  identified by IP address, gNMI port, and TLS credentials. May
  be any vendor that supports gNMI.
- **YANG Path**: A structured path identifying a specific piece of
  network state or configuration within the YANG model hierarchy
  (e.g., /interfaces/interface[name=Ethernet1]/state/oper-status).
- **Telemetry Subscription**: An active gRPC stream between the MCP
  server and a gNMI target, delivering periodic or event-driven
  updates for specified YANG paths.
- **gNMI Operation**: A single Get, Set, Subscribe, or Capabilities
  request-response interaction with a gNMI target, recorded in the
  GAIT audit trail.
- **YANG Module**: A YANG data model supported by a gNMI target,
  characterized by module name, revision/version, and organization
  (e.g., openconfig-bgp, 9.0.0, OpenConfig).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can retrieve structured state data via gNMI
  Get from any supported vendor device and receive results within
  5 seconds for standard YANG paths (interfaces, BGP, OSPF, system).
- **SC-002**: Streaming telemetry subscriptions deliver state change
  notifications within 2 seconds of the actual change on the device
  for ON_CHANGE subscriptions.
- **SC-003**: gNMI Set operations are blocked 100% of the time when
  no valid ServiceNow Change Request is provided.
- **SC-004**: The system successfully communicates with gNMI-capable
  devices from at least 3 different vendors (e.g., Cisco IOS-XR,
  Arista EOS, Nokia SR OS) using the same operator workflow.
- **SC-005**: YANG model browsing returns the complete list of
  supported models and navigable paths for any gNMI-capable device
  that supports the Capabilities RPC.
- **SC-006**: gNMI-vs-CLI comparison produces accurate field-level
  results for at least interfaces, BGP neighbors, and routes on
  devices reachable by both methods.
- **SC-007**: 100% of gNMI operations are recorded in the GAIT
  audit trail with operator, device, path, operation type, and
  timestamp.
- **SC-008**: All artifact coherence checklist items are complete
  (README, install.sh, UI, SOUL.md, SKILL.md, .env.example,
  TOOLS.md, config/openclaw.json).
- **SC-009**: Existing NetGeniusClaw skills and MCP servers remain fully
  functional after the addition (backwards compatibility verified).

## Assumptions

- Target devices are already configured with gNMI enabled (gRPC
  server running on a known port with TLS credentials provisioned).
  This MCP server does not manage gNMI enablement on devices.
- Target devices support at least gNMI specification version 0.7.0
  or later, which includes Get, Set, Subscribe, and Capabilities
  RPCs.
- TLS certificates and CA bundles for device authentication are
  available on the host machine and referenced via environment
  variables. Certificate lifecycle management is out of scope.
- The existing pyATS-based CLI MCP servers remain operational
  during and after deployment, enabling side-by-side gNMI-vs-CLI
  comparison workflows.
- OpenConfig YANG models are the primary model set used across
  vendors, with vendor-native models supported as a secondary
  option where OpenConfig coverage is incomplete.
- The gNMI MCP server communicates directly with devices over
  gRPC — there is no intermediate telemetry collector or broker
  (e.g., no Telegraf or gNMI collector in between).
- Network connectivity between the MCP server host and gNMI target
  devices on the configured gRPC port is pre-established (firewall
  rules, routing, etc. are already in place).
