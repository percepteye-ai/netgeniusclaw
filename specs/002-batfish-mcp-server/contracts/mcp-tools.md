# MCP Tool Contracts: Batfish MCP Server

**Transport**: stdio
**Server Name**: `batfish-mcp`

## Tool 1: upload_snapshot

**Description**: Upload device configurations to Batfish and create a named network snapshot for analysis.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| snapshot_name | string | yes | Unique name for the snapshot |
| configs | object | no | Dictionary mapping device names to configuration content (inline) |
| config_path | string | no | Path to directory containing configuration files |
| network | string | no | Batfish network name (default: "netgeniusclaw") |

**Constraints**: Either `configs` or `config_path` must be provided, not both. At least one device configuration is required.

**Returns**: JSON object with `snapshot_name`, `network`, `device_count`, `devices` (list of device names), and `status`.

**Errors**:
- `BATFISH_UNREACHABLE`: Batfish service not available
- `INVALID_INPUT`: No configs provided or both configs and config_path specified
- `SNAPSHOT_CREATION_FAILED`: Batfish failed to create the snapshot

---

## Tool 2: validate_config

**Description**: Validate device configurations in a snapshot and return a structured parse report with per-device pass/fail status.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| snapshot_name | string | yes | Name of the snapshot to validate |
| network | string | no | Batfish network name (default: "netgeniusclaw") |

**Returns**: JSON object with `snapshot_name`, `overall_status` ("PASS"/"FAIL"), `device_results` (array of per-device results with status, vendor, warnings, errors), and `warnings`.

**Errors**:
- `BATFISH_UNREACHABLE`: Batfish service not available
- `SNAPSHOT_NOT_FOUND`: The specified snapshot does not exist

---

## Tool 3: test_reachability

**Description**: Test whether traffic can flow between two endpoints in a snapshot, showing the forwarding path, ACL decisions, and final permit/deny status.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| snapshot_name | string | yes | Name of the snapshot to query |
| src_ip | string | yes | Source IP address |
| dst_ip | string | yes | Destination IP address |
| protocol | string | no | Protocol: "TCP", "UDP", or "ICMP" (default: "TCP") |
| dst_port | integer | no | Destination port (required for TCP/UDP) |
| src_port | integer | no | Source port (optional) |
| network | string | no | Batfish network name (default: "netgeniusclaw") |

**Returns**: JSON object with `snapshot_name`, `src_ip`, `dst_ip`, `protocol`, `dst_port`, `disposition` ("ACCEPTED"/"DENIED"/"NO_ROUTE"/"NULL_ROUTED"), `traces` (array of paths with hops and per-hop steps).

**Errors**:
- `BATFISH_UNREACHABLE`: Batfish service not available
- `SNAPSHOT_NOT_FOUND`: The specified snapshot does not exist
- `INVALID_HEADERS`: Invalid IP address or port values

---

## Tool 4: trace_acl

**Description**: Trace a specific packet through the ACLs and firewall rules on a given device to determine which rule permits or denies the traffic.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| snapshot_name | string | yes | Name of the snapshot to query |
| device | string | yes | Device name to trace on |
| filter_name | string | yes | ACL or filter name to trace through |
| src_ip | string | yes | Source IP of test packet |
| dst_ip | string | yes | Destination IP of test packet |
| protocol | string | no | Protocol: "TCP", "UDP", or "ICMP" (default: "TCP") |
| dst_port | integer | no | Destination port (required for TCP/UDP) |
| network | string | no | Batfish network name (default: "netgeniusclaw") |

**Returns**: JSON object with `device`, `filter_name`, `action` ("PERMIT"/"DENY"), `matching_line` (the ACL line that matched), `line_number`, and full `trace_details`.

**Errors**:
- `BATFISH_UNREACHABLE`: Batfish service not available
- `SNAPSHOT_NOT_FOUND`: The specified snapshot does not exist
- `DEVICE_NOT_FOUND`: The specified device is not in the snapshot
- `FILTER_NOT_FOUND`: The specified ACL/filter does not exist on the device

---

## Tool 5: diff_configs

**Description**: Compare two snapshots and return differences in routing, reachability, and ACL behavior.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| reference_snapshot | string | yes | "Before" snapshot name |
| candidate_snapshot | string | yes | "After" snapshot name |
| include_routes | boolean | no | Include route differences (default: true) |
| include_reachability | boolean | no | Include reachability differences (default: true) |
| network | string | no | Batfish network name (default: "netgeniusclaw") |

**Returns**: JSON object with `reference_snapshot`, `candidate_snapshot`, `route_diffs` (array of added/removed/changed routes), `reachability_diffs` (array of flows that changed disposition), and `summary` (counts of each change type).

**Errors**:
- `BATFISH_UNREACHABLE`: Batfish service not available
- `SNAPSHOT_NOT_FOUND`: One or both snapshots do not exist

---

## Tool 6: check_compliance

**Description**: Validate device configurations against organizational policy rules and report violations.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| snapshot_name | string | yes | Name of the snapshot to check |
| policy_type | string | yes | Policy to check: "interface_descriptions", "no_default_route", "ntp_configured", "no_shutdown_interfaces", "bgp_sessions_established", "ospf_adjacencies" |
| network | string | no | Batfish network name (default: "netgeniusclaw") |

**Returns**: JSON object with `snapshot_name`, `policy_type`, `overall_status` ("COMPLIANT"/"NON_COMPLIANT"), `violations` (array with device, element, description, severity), and `checked_devices` count.

**Errors**:
- `BATFISH_UNREACHABLE`: Batfish service not available
- `SNAPSHOT_NOT_FOUND`: The specified snapshot does not exist
- `UNSUPPORTED_POLICY`: The specified policy type is not supported

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| BATFISH_HOST | no | localhost | Batfish service hostname or IP |
| BATFISH_PORT | no | 9997 | Batfish coordinator port |
| BATFISH_NETWORK | no | netgeniusclaw | Default Batfish network name |
