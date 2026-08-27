# Data Model: gNMI Streaming Telemetry MCP Server

**Feature**: 003-gnmi-mcp-server | **Date**: 2026-03-26

## Entities

### GnmiTarget

Represents a network device reachable via gNMI.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str | Yes | Logical device name (e.g., "router1") |
| host | str | Yes | IP address or hostname |
| port | int | Yes | gNMI/gRPC port (default varies by vendor) |
| username | str | Yes | Authentication username |
| password | str | Yes | Authentication password |
| tls_ca_cert | str | Yes | Path to CA certificate for server verification |
| tls_client_cert | str | No | Path to client certificate (for mTLS) |
| tls_client_key | str | No | Path to client private key (for mTLS) |
| tls_skip_verify | bool | No | Skip TLS verification (lab mode only, default False) |
| vendor | str | No | Vendor identifier (cisco-iosxr, juniper, arista, nokia) for dialect selection |
| encoding | str | No | Preferred encoding (JSON_IETF, JSON, PROTO, ASCII; auto-detected if not set) |

**Validation Rules**:
- `host` must be a valid IPv4/IPv6 address or resolvable hostname
- `port` must be between 1 and 65535
- `tls_ca_cert` must point to an existing file
- If `tls_client_cert` is set, `tls_client_key` must also be set (and vice versa)
- `vendor` must be one of: `cisco-iosxr`, `juniper`, `arista`, `nokia`, or empty (auto-detect)
- `encoding` must be one of: `JSON_IETF`, `JSON`, `PROTO`, `ASCII`, or empty (auto-detect)

**Source**: Environment variables. Targets are defined via `GNMI_TARGETS` env var as a JSON array or comma-separated `host:port` list.

---

### YangPath

Represents a YANG model path used in gNMI operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| path | str | Yes | YANG path string (e.g., "/interfaces/interface[name=Ethernet1]/state") |
| origin | str | No | YANG model origin (e.g., "openconfig", "cisco-ios-xr") |

**Validation Rules**:
- `path` must start with "/"
- `path` must not contain consecutive slashes
- Key-value selectors must use `[key=value]` syntax

---

### GnmiGetRequest

Input model for gNMI Get tool calls.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| target | str | Yes | Device name (must match a configured GnmiTarget) |
| paths | list[str] | Yes | One or more YANG paths to retrieve |
| encoding | str | No | Override encoding for this request |
| data_type | str | No | One of: ALL, CONFIG, STATE, OPERATIONAL (default: ALL) |

---

### GnmiGetResponse

Output model for gNMI Get results.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| target | str | Yes | Device name |
| timestamp | str | Yes | ISO 8601 timestamp of the response |
| results | list[PathResult] | Yes | List of path-value pairs |
| truncated | bool | No | True if response was truncated |
| total_size_bytes | int | No | Original response size before truncation |

---

### PathResult

A single path-value pair from a gNMI response.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| path | str | Yes | YANG path of the returned data |
| value | dict | str | Yes | The returned value (structured dict or scalar) |
| timestamp | int | No | Nanosecond timestamp from the device |

---

### GnmiSetRequest

Input model for gNMI Set tool calls.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| target | str | Yes | Device name |
| change_request_number | str | Yes | ServiceNow CR number (e.g., "CHG0012345") |
| updates | list[SetOperation] | No | Update operations (merge) |
| replaces | list[SetOperation] | No | Replace operations (overwrite) |
| deletes | list[str] | No | YANG paths to delete |

**Validation Rules**:
- At least one of `updates`, `replaces`, or `deletes` must be non-empty
- `change_request_number` must match pattern `CHG\d+`
- CR must be validated against ServiceNow (in "Implement" state) before execution

---

### SetOperation

A single update or replace operation for gNMI Set.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| path | str | Yes | YANG path to modify |
| value | dict | str | Yes | New value to set |

---

### GnmiSetResponse

Output model for gNMI Set results.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| target | str | Yes | Device name |
| timestamp | str | Yes | ISO 8601 timestamp |
| change_request_number | str | Yes | The CR used for this operation |
| operations_applied | list[str] | Yes | Summary of applied operations |
| success | bool | Yes | Whether all operations succeeded |
| errors | list[str] | No | Error messages for failed operations |

---

### SubscriptionRequest

Input model for gNMI Subscribe tool calls.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| target | str | Yes | Device name |
| paths | list[str] | Yes | YANG paths to subscribe to |
| mode | str | Yes | One of: SAMPLE, ON_CHANGE |
| sample_interval_seconds | int | No | Interval for SAMPLE mode (default: 10) |

**Validation Rules**:
- `mode` must be one of: `SAMPLE`, `ON_CHANGE`
- `sample_interval_seconds` must be >= 1 if mode is SAMPLE
- Total active subscriptions must not exceed 50

---

### Subscription

Represents an active telemetry subscription.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | str (UUID) | Yes | Unique subscription identifier |
| target | str | Yes | Device name |
| paths | list[str] | Yes | Subscribed YANG paths |
| mode | str | Yes | SAMPLE or ON_CHANGE |
| sample_interval_seconds | int | No | Interval for SAMPLE mode |
| created_at | str | Yes | ISO 8601 creation timestamp |
| status | str | Yes | One of: ACTIVE, ERROR, CANCELLED |
| last_update | str | No | ISO 8601 timestamp of last received update |
| error_message | str | No | Error description if status is ERROR |

**State Transitions**:
- ACTIVE -> CANCELLED (operator cancels)
- ACTIVE -> ERROR (device unreachable, stream interrupted)
- ERROR -> ACTIVE (not supported; must create new subscription)

---

### SubscriptionUpdate

A telemetry update received from a subscription.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| subscription_id | str | Yes | Reference to the Subscription |
| target | str | Yes | Device name |
| path | str | Yes | YANG path of the update |
| value | dict | str | Yes | Updated value |
| timestamp | str | Yes | ISO 8601 timestamp |

---

### YangCapability

Represents a YANG module advertised by a device via gNMI Capabilities.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str | Yes | YANG module name (e.g., "openconfig-interfaces") |
| organization | str | No | Publishing organization (e.g., "OpenConfig") |
| version | str | No | Module version/revision (e.g., "2.0.0") |

---

### VendorDialect

Configuration for vendor-specific gNMI behavior.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| vendor_id | str | Yes | Vendor identifier (cisco-iosxr, juniper, arista, nokia) |
| default_port | int | Yes | Default gNMI port for this vendor |
| default_encoding | str | Yes | Default encoding preference |
| path_prefix | str | No | Default path origin/prefix |
| supports_on_change | bool | Yes | Whether ON_CHANGE subscriptions are supported |

## Entity Relationships

```
GnmiTarget 1──* GnmiGetRequest
GnmiTarget 1──* GnmiSetRequest
GnmiTarget 1──* SubscriptionRequest
GnmiTarget 1──* YangCapability (via Capabilities RPC)
GnmiTarget *──1 VendorDialect (optional, for dialect normalization)

Subscription 1──* SubscriptionUpdate
SubscriptionRequest 1──1 Subscription (created from request)

GnmiGetRequest 1──1 GnmiGetResponse
GnmiSetRequest 1──1 GnmiSetResponse
GnmiGetResponse 1──* PathResult
```
