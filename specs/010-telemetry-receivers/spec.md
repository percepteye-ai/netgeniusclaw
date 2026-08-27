# Feature Specification: Telemetry & Event Receiver Capabilities

**Feature Branch**: `010-telemetry-receivers`
**Created**: 2026-03-28
**Status**: Draft
**Input**: User description: "Add 4 telemetry/event receiver capabilities to NetGeniusClaw: 1) gNMI streaming telemetry receiver (confirm existing), 2) Syslog receiver (RFC 5424/UDP 514), 3) SNMP trap receiver (SNMPv2c/v3 traps UDP 162), 4) IPFIX/NetFlow receiver (RFC 7011/UDP 2055). Target: Cisco Catalyst 9300. Will use ngrok to expose receivers for live testing."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Receive Syslog Messages from Network Devices (Priority: P1)

As a network operator, I want NetGeniusClaw to receive and process syslog messages from my Cisco Catalyst 9300 switches so that I can correlate log events with network state and ask natural language questions about recent events.

**Why this priority**: Syslog is the most ubiquitous event source in network infrastructure. Every network device supports syslog, making this the highest-value receiver capability. It provides the foundation for event correlation and root cause analysis.

**Independent Test**: Configure a Cisco Catalyst 9300 to send syslog messages to NetGeniusClaw's receiver endpoint (exposed via ngrok). Verify messages are received, parsed, and queryable through natural language ("What errors occurred in the last hour?").

**Acceptance Scenarios**:

1. **Given** a Catalyst 9300 configured to send syslog to NetGeniusClaw's UDP 514 endpoint, **When** an interface goes down, **Then** NetGeniusClaw receives and stores the %LINK-3-UPDOWN message within 1 second.
2. **Given** syslog messages have been received, **When** I ask "show me critical syslog events from the last 5 minutes", **Then** NetGeniusClaw returns filtered results with severity levels 0-2 (Emergency, Alert, Critical).
3. **Given** an RFC 5424 structured syslog message is received, **When** the message includes STRUCTURED-DATA, **Then** NetGeniusClaw parses and extracts all SD-ELEMENTs for querying.

---

### User Story 2 - Receive SNMP Traps from Network Devices (Priority: P2)

As a network operator, I want NetGeniusClaw to receive SNMP traps (v2c and v3) from my network devices so that I can be notified of significant events like link failures, threshold crossings, and configuration changes.

**Why this priority**: SNMP traps provide structured event notification with standardized OIDs for vendor-agnostic alerting. While less ubiquitous than syslog, traps offer richer metadata and are standard in enterprise monitoring.

**Independent Test**: Configure a Catalyst 9300 to send SNMP traps to NetGeniusClaw's UDP 162 endpoint. Verify linkDown/linkUp traps are received and queryable through natural language.

**Acceptance Scenarios**:

1. **Given** a Catalyst 9300 configured with SNMP trap receiver pointing to NetGeniusClaw, **When** interface GigabitEthernet1/0/1 goes down, **Then** NetGeniusClaw receives the linkDown trap (OID 1.3.6.1.6.3.1.1.5.3) within 1 second.
2. **Given** SNMPv3 authentication is configured with authPriv, **When** a trap is sent with AES encryption, **Then** NetGeniusClaw successfully decrypts and processes the trap.
3. **Given** SNMP traps have been received, **When** I ask "show interface traps from the last hour", **Then** NetGeniusClaw returns linkUp/linkDown events with interface names and timestamps.

---

### User Story 3 - Receive IPFIX/NetFlow Records from Network Devices (Priority: P3)

As a network operator, I want NetGeniusClaw to receive IPFIX (RFC 7011) and NetFlow v9 flow records from my network devices so that I can analyze traffic patterns, detect anomalies, and answer questions about network utilization.

**Why this priority**: Flow data provides visibility into actual traffic patterns that cannot be obtained from device state alone. Essential for capacity planning, security analysis, and troubleshooting application performance.

**Independent Test**: Configure a Catalyst 9300 with Flexible NetFlow to export to NetGeniusClaw's UDP 2055 endpoint. Verify flow records are received and queryable ("What are the top talkers in the last 10 minutes?").

**Acceptance Scenarios**:

1. **Given** a Catalyst 9300 configured with Flexible NetFlow exporting to NetGeniusClaw, **When** traffic flows through monitored interfaces, **Then** NetGeniusClaw receives flow records containing source IP, destination IP, protocol, bytes, and packets.
2. **Given** flow records have been received, **When** I ask "show top 10 traffic flows by bytes", **Then** NetGeniusClaw returns aggregated flow data sorted by byte count.
3. **Given** IPFIX template records are received, **When** data records reference those templates, **Then** NetGeniusClaw correctly decodes the variable-length fields using cached templates.

---

### User Story 4 - Confirm gNMI Streaming Telemetry Receiver (Priority: P4)

As a network operator, I want to confirm that NetGeniusClaw's existing gNMI MCP server can receive streaming telemetry subscriptions from my Catalyst 9300 so that I have real-time visibility into device metrics.

**Why this priority**: gNMI streaming telemetry is already implemented in NetGeniusClaw (gnmi_subscribe tool). This story confirms functionality and validates the testing approach with Catalyst 9300.

**Independent Test**: Use the existing gnmi_subscribe tool to create a subscription for interface counters on Catalyst 9300. Verify telemetry updates are received continuously.

**Acceptance Scenarios**:

1. **Given** a Catalyst 9300 with gNMI enabled (NETCONF-YANG), **When** I create a subscription for openconfig-interfaces counters, **Then** NetGeniusClaw receives periodic updates at the specified sample interval.
2. **Given** an active gNMI subscription exists, **When** I call gnmi_get_subscription_updates, **Then** I receive the latest telemetry data from the device.

---

### Edge Cases

- What happens when syslog messages exceed the maximum UDP payload (65535 bytes)? NetGeniusClaw truncates with metadata indicating truncation.
- How does the system handle malformed syslog messages (non-RFC 5424 compliant)? Fall back to RFC 3164 BSD syslog parsing.
- What happens when SNMP trap OIDs reference unknown MIBs? Store raw OID with flag indicating unresolved MIB.
- How does the system handle IPFIX templates that arrive after data records? Buffer data records and apply templates retroactively within a 5-minute window.
- What happens when multiple devices send to the same receiver port? Include source IP in stored records for differentiation.
- How does the system handle ngrok disconnections? Automatic reconnection with configurable retry interval; buffer messages during outage.

## Requirements *(mandatory)*

### Functional Requirements

**Syslog Receiver (RFC 5424)**

- **FR-001**: System MUST receive UDP syslog messages on configurable port (default 514).
- **FR-002**: System MUST parse RFC 5424 format including PRI, VERSION, TIMESTAMP, HOSTNAME, APP-NAME, PROCID, MSGID, and STRUCTURED-DATA.
- **FR-003**: System MUST fall back to RFC 3164 (BSD syslog) parsing when RFC 5424 parsing fails.
- **FR-004**: System MUST extract severity level (0-7) and facility (0-23) from PRI field.
- **FR-005**: System MUST expose syslog data through MCP tools for querying by time range, severity, facility, hostname, and message content.

**SNMP Trap Receiver (RFC 3416)**

- **FR-006**: System MUST receive SNMP traps on configurable port (default 162).
- **FR-007**: System MUST support SNMPv2c trap format with community string authentication.
- **FR-008**: System MUST support SNMPv3 trap format with USM authentication (noAuthNoPriv, authNoPriv, authPriv).
- **FR-009**: System MUST support SNMPv3 encryption algorithms: MD5/SHA for auth, DES/AES for priv.
- **FR-010**: System MUST decode standard trap OIDs (linkUp, linkDown, coldStart, warmStart, authenticationFailure).
- **FR-011**: System MUST expose trap data through MCP tools for querying by time range, OID, source device, and varbind values.

**IPFIX/NetFlow Receiver (RFC 7011)**

- **FR-012**: System MUST receive IPFIX/NetFlow v9 records on configurable port (default 2055).
- **FR-013**: System MUST cache IPFIX template records and apply them to subsequent data records.
- **FR-014**: System MUST support standard IPFIX Information Elements: sourceIPv4Address, destinationIPv4Address, protocolIdentifier, sourceTransportPort, destinationTransportPort, octetDeltaCount, packetDeltaCount.
- **FR-015**: System MUST aggregate flow records by configurable keys (5-tuple default).
- **FR-016**: System MUST expose flow data through MCP tools for querying top talkers, traffic by protocol, and time-based analysis.

**Cross-Cutting Requirements**

- **FR-017**: System MUST support ngrok tunnel integration for exposing receivers to remote devices.
- **FR-018**: System MUST log all received events to GAIT audit trail.
- **FR-019**: System MUST provide MCP tool to list active receivers and their statistics (messages received, errors, uptime).
- **FR-020**: System MUST support configurable retention period for received data (default 24 hours).
- **FR-021**: System MUST provide rate limiting to prevent receiver overload (configurable messages/second).
- **FR-022**: System MUST deduplicate received messages using content hash within a configurable time window (default 5 seconds) to discard retransmissions.

### Key Entities

- **SyslogMessage**: Timestamp, severity, facility, hostname, app_name, process_id, message_id, structured_data, message_content, source_ip.
- **SNMPTrap**: Timestamp, version (v2c/v3), trap_oid, enterprise_oid, generic_trap, specific_trap, varbinds[], source_ip, community/security_name.
- **FlowRecord**: Start_time, end_time, source_ip, destination_ip, source_port, destination_port, protocol, bytes, packets, flags, source_device.
- **ReceiverStatus**: Receiver_type, port, bind_address, messages_received, errors, uptime, last_message_time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Syslog receiver processes 1,000 messages per second without message loss on standard hardware.
- **SC-002**: SNMP trap receiver decodes and stores traps within 100ms of receipt.
- **SC-003**: IPFIX receiver correctly decodes 95% of flow records using standard Cisco templates.
- **SC-004**: Users can query received events using natural language with response time under 2 seconds.
- **SC-005**: All four receiver types successfully receive data from Cisco Catalyst 9300 in live testing via ngrok.
- **SC-006**: System maintains 99.9% uptime for receiver processes during 24-hour test period.
- **SC-007**: Network operators can identify root cause of interface down event within 3 minutes by querying syslog, trap, and telemetry data (manual correlation via natural language queries).

## Clarifications

### Session 2026-03-28

- Q: Should received telemetry data be stored in-memory or persisted to disk/database? → A: In-memory only (data lost on restart, suitable for demo/testing)
- Q: Should receivers accept telemetry from any source IP or only whitelisted devices? → A: Accept from any source (open receivers, rely on ngrok URL obscurity)
- Q: Should receivers actively correlate events or just store raw data for user queries? → A: Raw storage only (users correlate via queries - MVP approach)
- Q: Should receivers deduplicate messages or store all including duplicates? → A: Deduplicate (hash content + timestamp window, discard duplicates)
- Q: Should receivers be one unified MCP server or separate servers per protocol? → A: Separate servers (syslog-mcp, snmptrap-mcp, ipfix-mcp - independent deployment)

## Assumptions

- All received telemetry data is stored in-memory only; data is lost on receiver restart (acceptable for demo/testing scope).
- Receivers accept data from any source IP; access control relies on ngrok tunnel URL obscurity (no IP whitelisting for demo scope).
- Each receiver protocol is implemented as a separate MCP server (syslog-mcp, snmptrap-mcp, ipfix-mcp) for independent deployment and modularity.
- Cisco Catalyst 9300 is accessible in the cloud and can be configured to send telemetry to external endpoints.
- ngrok (or similar tunneling service) can reliably expose UDP ports (514, 162, 2055) to remote devices.
- Network allows outbound connections from Catalyst 9300 to ngrok tunnel endpoints.
- gNMI is enabled on Catalyst 9300 with NETCONF-YANG feature (IOS-XE 16.x+).
- SNMP credentials (community strings for v2c, USM users for v3) will be provided during testing.
- Standard Cisco MIBs are available for trap OID resolution.
- Retention of 24 hours of data is sufficient for testing and demonstration purposes.
- Single-instance deployment is acceptable (no clustering requirement for MVP).
