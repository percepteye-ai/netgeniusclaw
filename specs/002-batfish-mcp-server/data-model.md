# Data Model: Batfish MCP Server

**Feature Branch**: `002-batfish-mcp-server`
**Date**: 2026-03-26

## Entities

### Snapshot

A point-in-time collection of device configurations uploaded to Batfish for analysis.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| name | str | Unique snapshot identifier | Required; alphanumeric + hyphens; max 128 chars |
| network | str | Batfish network name (namespace) | Default: "netgeniusclaw"; alphanumeric + hyphens |
| configs | dict[str, str] | Device name → config content mapping | At least one device required |
| config_path | str \| None | Path to directory containing config files | Optional; mutually exclusive with configs |
| created_at | str | ISO 8601 timestamp of creation | Auto-generated |

**State transitions**: Created → Active → (Deleted by Batfish garbage collection)

**Notes**: Snapshots are ephemeral within Batfish. The MCP server does not manage snapshot lifecycle beyond creation.

---

### ValidationResult

Output of configuration validation for a snapshot.

| Field | Type | Description |
|-------|------|-------------|
| snapshot_name | str | Snapshot that was validated |
| overall_status | str | "PASS" or "FAIL" |
| device_results | list[DeviceValidation] | Per-device parse results |
| warnings | list[str] | Non-fatal warnings across all devices |
| timestamp | str | ISO 8601 timestamp |

### DeviceValidation

| Field | Type | Description |
|-------|------|-------------|
| device_name | str | Name of the device |
| status | str | "PASS", "FAIL", or "PARTIALLY_PARSED" |
| file_name | str | Original config file name |
| parse_warnings | list[str] | Parser warnings for this device |
| errors | list[str] | Parse errors for this device |
| vendor | str | Detected vendor (e.g., "CISCO_IOS", "JUNIPER") |

---

### ReachabilityResult

Outcome of a traffic flow query between two endpoints.

| Field | Type | Description |
|-------|------|-------------|
| snapshot_name | str | Snapshot used for analysis |
| src_ip | str | Source IP address |
| dst_ip | str | Destination IP address |
| protocol | str | Protocol (TCP, UDP, ICMP) |
| dst_port | int \| None | Destination port (if TCP/UDP) |
| disposition | str | "ACCEPTED", "DENIED", "NO_ROUTE", "NULL_ROUTED" |
| traces | list[Trace] | All forwarding paths found |
| timestamp | str | ISO 8601 timestamp |

### Trace

| Field | Type | Description |
|-------|------|-------------|
| disposition | str | Final disposition of this path |
| hops | list[Hop] | Ordered list of hops in the path |

### Hop

| Field | Type | Description |
|-------|------|-------------|
| node | str | Device name at this hop |
| steps | list[str] | Actions taken at this hop (e.g., "FORWARDED", "FILTERED by acl-in") |

---

### AclTraceResult

Detailed trace of a packet through ACLs on a specific device.

| Field | Type | Description |
|-------|------|-------------|
| snapshot_name | str | Snapshot used for analysis |
| device | str | Device name where trace was performed |
| filter_name | str | ACL or filter name traced |
| src_ip | str | Source IP of the test packet |
| dst_ip | str | Destination IP of the test packet |
| protocol | str | Protocol of the test packet |
| dst_port | int \| None | Destination port (if TCP/UDP) |
| action | str | "PERMIT" or "DENY" |
| matching_line | str | The ACL line that matched the packet |
| line_number | int \| None | Line number in the ACL (if available) |
| timestamp | str | ISO 8601 timestamp |

---

### DiffResult

Comparison between two snapshots showing behavioral differences.

| Field | Type | Description |
|-------|------|-------------|
| reference_snapshot | str | "Before" snapshot name |
| candidate_snapshot | str | "After" snapshot name |
| route_diffs | list[RouteDiff] | Routes added, removed, or changed |
| reachability_diffs | list[ReachabilityDiff] | Flows that changed disposition |
| timestamp | str | ISO 8601 timestamp |

### RouteDiff

| Field | Type | Description |
|-------|------|-------------|
| device | str | Device where route differs |
| network | str | Route prefix (e.g., "10.0.0.0/24") |
| change_type | str | "ADDED", "REMOVED", or "CHANGED" |
| old_next_hop | str \| None | Previous next-hop (for CHANGED/REMOVED) |
| new_next_hop | str \| None | New next-hop (for CHANGED/ADDED) |
| protocol | str | Route protocol (STATIC, BGP, OSPF, etc.) |

### ReachabilityDiff

| Field | Type | Description |
|-------|------|-------------|
| src_ip | str | Source IP |
| dst_ip | str | Destination IP |
| old_disposition | str | Disposition in reference snapshot |
| new_disposition | str | Disposition in candidate snapshot |

---

### ComplianceResult

Per-device, per-policy pass/fail compliance report.

| Field | Type | Description |
|-------|------|-------------|
| snapshot_name | str | Snapshot that was checked |
| policy_type | str | Policy rule checked (e.g., "interface_descriptions") |
| overall_status | str | "COMPLIANT" or "NON_COMPLIANT" |
| violations | list[Violation] | Specific violations found |
| checked_devices | int | Number of devices checked |
| timestamp | str | ISO 8601 timestamp |

### Violation

| Field | Type | Description |
|-------|------|-------------|
| device | str | Device name |
| element | str | Specific element (e.g., interface name, route prefix) |
| description | str | Human-readable violation description |
| severity | str | "ERROR" or "WARNING" |

---

### AnalysisLog (GAIT Record)

Audit record for every Batfish analysis operation.

| Field | Type | Description |
|-------|------|-------------|
| session_id | str | GAIT session identifier |
| analysis_type | str | Tool name (e.g., "validate_config", "test_reachability") |
| snapshot_name | str | Snapshot used |
| parameters | dict | Query parameters passed to the tool |
| result_summary | str | Brief result (e.g., "PASS: 5/5 devices valid") |
| timestamp | str | ISO 8601 timestamp |

## Supported Policy Types (Compliance)

| Policy Type | Description | Batfish Query Used |
|-------------|-------------|-------------------|
| `interface_descriptions` | All interfaces must have descriptions | `interfaceProperties()` — check `Description` column |
| `no_default_route` | No device should have a 0.0.0.0/0 route | `routes()` — filter for 0.0.0.0/0 prefix |
| `ntp_configured` | All devices must have NTP servers configured | `nodeProperties()` — check `NTP_Servers` column |
| `no_shutdown_interfaces` | No administratively down interfaces | `interfaceProperties()` — check `Active` column |
| `bgp_sessions_established` | All BGP sessions must be established | `bgpSessionStatus()` — check status column |
| `ospf_adjacencies` | All OSPF adjacencies must be full | `ospfSessionCompatibility()` — check compatibility |
