# Feature Specification: Batfish MCP Server

**Feature Branch**: `002-batfish-mcp-server`
**Created**: 2026-03-26
**Status**: Draft
**Input**: User description: "Build a new MCP server wrapping the Batfish network configuration analysis platform (pybatfish). No one has built a Batfish MCP server yet, making this a first-of-its-kind. Batfish enables pre-deployment config validation, reachability analysis, what-if analysis, ACL/firewall tracing, routing policy analysis, configuration compliance, differential analysis, and multi-vendor support."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pre-Change Configuration Validation (Priority: P1)

As a network engineer preparing to deploy a configuration change, I want
to upload my proposed configuration to Batfish and receive a pass/fail
validation report BEFORE I push the change to a live device, so I can
catch errors, policy violations, and unintended side effects before they
cause an outage.

**Why this priority**: This is the core value proposition of the entire
MCP server. Pre-deployment validation directly supports constitution
principles I (Safety-First), II (Read-Before-Write), and VIII (Verify
After Every Change). Without this capability, the Batfish MCP server has
no reason to exist. This makes the pyats-config-mgmt skill dramatically
safer by enabling a "validate before push" workflow.

**Independent Test**: Can be fully tested by uploading a set of router
configurations, running Batfish analysis, and verifying that the system
returns a structured pass/fail report identifying any parse errors,
undefined references, or structural issues.

**Acceptance Scenarios**:

1. **Given** Batfish is running and accessible,
   **When** the operator uploads a proposed Cisco IOS configuration for
   a single router,
   **Then** the system initializes a Batfish snapshot, runs configuration
   analysis, and returns a structured report indicating whether the
   configuration parsed successfully, listing any warnings, undefined
   references, or structural errors.

2. **Given** Batfish is running and accessible,
   **When** the operator uploads proposed configurations for an entire
   site (multiple devices, multiple vendors),
   **Then** the system analyzes all configurations together as a network
   snapshot and returns a per-device validation report with an overall
   pass/fail status.

3. **Given** the operator uploads a configuration with a syntax error
   (e.g., a malformed ACL entry or invalid interface reference),
   **When** Batfish analyzes the configuration,
   **Then** the system returns a failure result with the specific line(s)
   causing the issue and a human-readable explanation of the error.

4. **Given** the operator uploads an empty configuration file or a file
   that is not a network device configuration,
   **When** the system attempts to create a Batfish snapshot,
   **Then** the system returns a clear error indicating the file could
   not be parsed as a valid device configuration.

---

### User Story 2 - Reachability Testing (Priority: P2)

As a network engineer, I want to test whether traffic can flow between
two endpoints (given a set of configurations) so I can verify that my
routing, ACLs, and firewall rules allow the intended traffic paths before
deploying changes.

**Why this priority**: Reachability is the most common question network
engineers ask: "Can A talk to B?" This builds directly on the snapshot
created in US1 and is the natural next step after validating that
configurations parse correctly.

**Independent Test**: Can be tested by uploading a known set of
configurations, running a reachability query between two IP addresses,
and verifying the result matches the expected forwarding behavior.

**Acceptance Scenarios**:

1. **Given** a Batfish snapshot has been created from a set of valid
   configurations,
   **When** the operator asks "can 10.1.1.1 reach 10.2.2.1 on TCP
   port 443",
   **Then** the system returns a reachability result showing the
   forwarding path, any ACLs or firewall rules encountered, and whether
   the traffic is ultimately permitted or denied.

2. **Given** a Batfish snapshot with a firewall blocking traffic between
   two subnets,
   **When** the operator queries reachability between hosts in those
   subnets,
   **Then** the system returns a "denied" result identifying the
   specific firewall rule that blocks the traffic and the device on
   which it is applied.

3. **Given** a Batfish snapshot where multiple equal-cost paths exist
   between source and destination,
   **When** the operator queries reachability,
   **Then** the system returns all possible forwarding paths, not just
   one.

4. **Given** the operator specifies a source or destination IP that does
   not exist in any device's routing table in the snapshot,
   **When** the reachability query is executed,
   **Then** the system returns a clear result indicating no route exists
   for the specified address.

---

### User Story 3 - ACL and Firewall Rule Trace (Priority: P3)

As a network engineer troubleshooting access control, I want to trace a
specific packet (defined by source IP, destination IP, protocol, and
port) through the ACLs and firewall rules on a given device so I can
determine exactly which rule permits or denies the traffic.

**Why this priority**: ACL troubleshooting is one of the most
time-consuming tasks in network operations. Being able to trace a packet
through rules without logging into the device or reading through
hundreds of ACL lines saves significant time and reduces human error.

**Independent Test**: Can be tested by uploading a configuration with
known ACL rules, tracing a packet that should be permitted and one that
should be denied, and verifying the system identifies the correct
matching rule in each case.

**Acceptance Scenarios**:

1. **Given** a Batfish snapshot containing a device with an extended ACL,
   **When** the operator traces a packet (src: 10.1.1.100,
   dst: 10.2.2.200, protocol: TCP, port: 22) through that ACL,
   **Then** the system returns the specific ACL line that matches the
   packet, whether the action is permit or deny, and the line number
   in the ACL.

2. **Given** a Batfish snapshot containing a Palo Alto firewall with
   zone-based security policies,
   **When** the operator traces a packet through the firewall rules,
   **Then** the system returns the matching security policy, the zones
   involved, and the permit/deny decision.

3. **Given** a packet that matches no explicit ACL rule and falls through
   to the implicit deny,
   **When** the trace is executed,
   **Then** the system reports that the packet was denied by the
   implicit deny at the end of the ACL.

4. **Given** a device configuration with multiple ACLs applied to
   different interfaces,
   **When** the operator traces a packet entering a specific interface,
   **Then** the system evaluates only the ACLs applied to that
   interface in the correct direction (inbound/outbound).

---

### User Story 4 - Differential Analysis (Priority: P4)

As a network engineer planning a change, I want to compare my proposed
configuration against the current configuration and see exactly what
will change in terms of routing, reachability, and ACL behavior so I
can understand the full impact of my change before deploying it.

**Why this priority**: Differential analysis is the "what changed and
what broke" capability. While it depends on the ability to create
snapshots (US1), it provides uniquely powerful change impact analysis
that no other NetGeniusClaw tool offers.

**Independent Test**: Can be tested by creating two snapshots (before
and after a known change), running a differential analysis, and verifying
the system correctly identifies all routing, reachability, and ACL
differences.

**Acceptance Scenarios**:

1. **Given** two Batfish snapshots exist (a "before" snapshot with the
   current config and an "after" snapshot with the proposed config),
   **When** the operator requests a differential analysis,
   **Then** the system returns a structured comparison showing routes
   added, removed, or changed between the two snapshots.

2. **Given** the proposed configuration adds a new ACL that blocks
   traffic previously permitted,
   **When** the differential analysis is run,
   **Then** the system identifies the specific traffic flows that would
   be newly denied and the ACL rule responsible.

3. **Given** two identical snapshots (no changes),
   **When** the differential analysis is run,
   **Then** the system reports that no differences were detected.

4. **Given** the proposed configuration changes a BGP route-map that
   alters path selection,
   **When** the differential analysis is run,
   **Then** the system identifies the routes whose best path changed
   and the old and new next-hops.

---

### User Story 5 - Configuration Compliance Checking (Priority: P5)

As a network engineer responsible for standards compliance, I want to
validate device configurations against a set of organizational policy
rules (e.g., "all interfaces must have descriptions", "NTP must be
configured", "no default routes in production") so I can identify
non-compliant devices before audits or deployments.

**Why this priority**: Compliance checking is a high-value governance
capability but depends on all prior features. It extends the validation
from US1 beyond syntax correctness into organizational policy
enforcement.

**Independent Test**: Can be tested by uploading configurations that
intentionally violate known policy rules and verifying the system flags
each violation with the specific device, interface, or setting that is
non-compliant.

**Acceptance Scenarios**:

1. **Given** a Batfish snapshot and a policy rule "all interfaces must
   have descriptions",
   **When** the compliance check is run,
   **Then** the system returns a list of all interfaces across all
   devices that lack a description, with the device name and interface
   name for each violation.

2. **Given** a Batfish snapshot and a policy rule "no device should have
   a default route (0.0.0.0/0)",
   **When** the compliance check is run against production devices,
   **Then** the system identifies every device with a default route and
   reports the route source (static, BGP, OSPF).

3. **Given** all devices in the snapshot are fully compliant with the
   requested policy,
   **When** the compliance check is run,
   **Then** the system returns a passing result confirming full
   compliance.

4. **Given** the operator requests a compliance check for a policy type
   that Batfish does not support,
   **When** the check is attempted,
   **Then** the system returns a clear message indicating the policy
   type is not supported, rather than an error.

---

### Edge Cases

- What happens when the Batfish service is unreachable or returns a
  connection timeout?
- How does the system handle configurations from a vendor that Batfish
  does not support?
- What happens when an uploaded configuration file exceeds Batfish's
  maximum snapshot size?
- How does the system behave when a Batfish analysis takes longer than
  the expected timeout (e.g., very large snapshots with thousands of
  routes)?
- What happens when the operator references a snapshot that has been
  deleted or expired?
- How does the system handle concurrent snapshot creation requests from
  multiple users?
- What happens when a configuration file has encoding issues (e.g.,
  non-UTF-8 characters)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept device configuration files and create
  Batfish network snapshots for analysis.
- **FR-002**: System MUST validate uploaded configurations and return
  structured parse/warning results including per-device pass/fail status.
- **FR-003**: System MUST support reachability queries between two
  endpoints with source IP, destination IP, protocol, and port
  parameters.
- **FR-004**: System MUST support ACL/firewall rule tracing for a
  defined packet header against a specific device or interface.
- **FR-005**: System MUST support differential analysis comparing two
  snapshots and returning routing, reachability, and ACL differences.
- **FR-006**: System MUST support configuration compliance checking
  against predefined policy rules.
- **FR-007**: System MUST be strictly read-only — it analyzes
  configurations uploaded to Batfish and NEVER modifies any network
  device, file system, or external system.
- **FR-008**: System MUST handle multi-vendor configurations including
  Cisco IOS, IOS-XE, NX-OS, Juniper JunOS, Arista EOS, Palo Alto,
  and F5.
- **FR-009**: System MUST return structured, parseable results with
  clear descriptions for all analysis operations.
- **FR-010**: System MUST log all analysis operations to the GAIT audit
  trail, including the analysis type, snapshot identifier, query
  parameters, and result summary.
- **FR-011**: All connection credentials (Batfish service URL, any
  authentication tokens) MUST be read from environment variables at
  runtime.
- **FR-012**: System MUST handle Batfish service errors gracefully,
  returning descriptive error messages without exposing internal details,
  stack traces, or credentials.
- **FR-013**: System MUST support querying Batfish for routing table
  contents, BGP session status, and OSPF adjacency state from a
  snapshot.
- **FR-014**: System MUST support managing multiple named snapshots
  simultaneously to enable differential analysis workflows.

### Key Entities

- **Snapshot**: A point-in-time collection of device configurations
  uploaded to Batfish for analysis. A snapshot represents the network
  state at a given moment and is the foundation for all analysis
  operations.
- **Reachability Result**: The outcome of a traffic flow query showing
  the forwarding path, ACL/firewall decisions, and final
  permit/deny status between two endpoints.
- **ACL Trace**: A detailed walk-through of a packet through a device's
  access control lists, identifying the specific rule that matches.
- **Differential Report**: A comparison between two snapshots showing
  what changed in routing, reachability, and security policy behavior.
- **Compliance Report**: A per-device, per-policy pass/fail result
  identifying specific configuration elements that violate
  organizational policies.
- **Analysis Log**: A GAIT audit record capturing the who, what, when,
  and result of every Batfish analysis operation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can upload configurations for up to 200 devices
  and receive a validation report within 60 seconds.
- **SC-002**: Reachability queries return correct permit/deny results
  when validated against known ACL and routing configurations in a
  controlled test environment.
- **SC-003**: ACL trace results correctly identify the matching rule
  for 100% of test packets when validated against manual ACL reading
  in a controlled environment.
- **SC-004**: Differential analysis correctly identifies all routing
  and ACL changes when comparing two snapshots with known differences.
- **SC-005**: Compliance checks correctly flag 100% of known violations
  when run against configurations with intentionally non-compliant
  settings.
- **SC-006**: All artifact coherence checklist items are complete
  (README, install.sh, UI, SOUL.md, SKILL.md, .env.example, TOOLS.md,
  config/openclaw.json).
- **SC-007**: Existing NetGeniusClaw skills and MCP servers remain fully
  functional after the addition (backwards compatibility verified).
- **SC-008**: 100% of analysis operations are recorded in the GAIT
  audit trail with analysis type, parameters, and result summary.
- **SC-009**: Multi-vendor configurations (Cisco IOS, JunOS, Arista EOS,
  Palo Alto) all parse and analyze successfully when uploaded as a
  mixed-vendor snapshot.

## Assumptions

- Batfish is already deployed and accessible as a service from the
  machine running the MCP server. This MCP server does not manage
  Batfish installation, deployment, or lifecycle.
- The MCP server communicates with Batfish via the pybatfish Python
  library, which connects to a running Batfish service. Network
  connectivity between the MCP server and Batfish is pre-configured.
- Configuration files are provided by the operator or by other NetGeniusClaw
  skills (e.g., pyats-config-mgmt). The Batfish MCP server does not
  collect configurations from live devices itself.
- The MCP server is strictly read-only by design — it uploads
  configurations to Batfish for analysis but never modifies any network
  device or external system.
- No existing Batfish MCP server is available in the community. This
  is a first-of-its-kind integration, so there is no prior reference
  implementation to follow. The implementation follows NetGeniusClaw's MCP
  server standards (FastMCP, GAIT integration, constitution compliance).
- Batfish supports the vendor configuration formats relevant to the
  target network. If a vendor is not supported by Batfish, the system
  will return a clear unsupported-vendor message.
- Snapshot storage is ephemeral — snapshots are created for analysis
  and may be cleaned up by Batfish's internal lifecycle management.
  Persistent storage of analysis results is handled by GAIT logging.
