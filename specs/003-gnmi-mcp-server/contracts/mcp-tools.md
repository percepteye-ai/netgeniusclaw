# MCP Tool Contracts: gNMI MCP Server

**Feature**: 003-gnmi-mcp-server | **Date**: 2026-03-26
**Transport**: stdio
**Protocol**: MCP (Model Context Protocol) via FastMCP

## Tools

### 1. gnmi_get

**Description**: Retrieve device state or configuration data via gNMI Get using YANG model paths.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Device name (must match configured target) |
| paths | string[] | Yes | YANG paths to query (e.g., ["/interfaces/interface/state"]) |
| encoding | string | No | Encoding override: JSON_IETF, JSON, PROTO, ASCII |
| data_type | string | No | Data type filter: ALL, CONFIG, STATE, OPERATIONAL (default: ALL) |

**Returns**: Structured JSON with device name, timestamp, and path-value results. Truncated if response exceeds size threshold.

**Safety**: Read-only. No ITSM gate required.

**GAIT**: Logs operation type, target, paths, timestamp, result status.

---

### 2. gnmi_set

**Description**: Apply configuration changes to a device via gNMI Set. REQUIRES an approved ServiceNow Change Request.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Device name |
| change_request_number | string | Yes | ServiceNow CR number (e.g., "CHG0012345") |
| updates | object[] | No | Update (merge) operations: [{path, value}] |
| replaces | object[] | No | Replace (overwrite) operations: [{path, value}] |
| deletes | string[] | No | YANG paths to delete |

**Returns**: Confirmation of applied operations, success/failure status, and any device error messages.

**Safety**: WRITE operation. ITSM-gated. Workflow: validate CR -> Get baseline -> Set -> Get verify -> GAIT log.

**GAIT**: Logs CR number, operator, target, paths, operation type, baseline state, result state, timestamp.

---

### 3. gnmi_subscribe

**Description**: Create a streaming telemetry subscription for real-time state updates.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Device name |
| paths | string[] | Yes | YANG paths to subscribe to |
| mode | string | Yes | Subscription mode: SAMPLE or ON_CHANGE |
| sample_interval_seconds | integer | No | Polling interval for SAMPLE mode (default: 10, min: 1) |

**Returns**: Subscription ID (UUID) and confirmation of active subscription.

**Safety**: Read-only (subscribes to state updates only). No ITSM gate required.

**Constraints**: Maximum 50 concurrent subscriptions. Returns error if limit reached.

**GAIT**: Logs subscription creation with target, paths, mode, subscription ID.

---

### 4. gnmi_unsubscribe

**Description**: Cancel an active telemetry subscription.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription_id | string | Yes | UUID of the subscription to cancel |

**Returns**: Confirmation of cancellation.

**GAIT**: Logs subscription cancellation with subscription ID and target.

---

### 5. gnmi_get_subscriptions

**Description**: List all active telemetry subscriptions.

**Parameters**: None.

**Returns**: Array of active subscriptions with ID, target, paths, mode, status, creation time, and last update time.

---

### 6. gnmi_get_subscription_updates

**Description**: Retrieve the latest updates received from a specific subscription.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription_id | string | Yes | UUID of the subscription |
| max_updates | integer | No | Maximum number of recent updates to return (default: 10) |

**Returns**: Array of recent telemetry updates with path, value, and timestamp.

---

### 7. gnmi_capabilities

**Description**: Retrieve supported YANG models, versions, and encodings from a device via gNMI Capabilities RPC.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Device name |

**Returns**: List of supported YANG modules (name, version, organization) and supported encodings.

**GAIT**: Logs capabilities query with target and timestamp.

---

### 8. gnmi_browse_yang_paths

**Description**: Browse available YANG paths under a specific module on a device.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Device name |
| module | string | Yes | YANG module name (e.g., "openconfig-interfaces") |
| depth | integer | No | Maximum tree depth to return (default: 3) |

**Returns**: Tree of available YANG paths under the specified module.

**GAIT**: Logs browse operation with target, module, timestamp.

---

### 9. gnmi_compare_with_cli

**Description**: Compare gNMI-retrieved state with CLI-retrieved state from pyATS for the same device and data type.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Device name (must be reachable via both gNMI and CLI/pyATS) |
| data_type | string | Yes | Data type to compare: interfaces, bgp_neighbors, routes |

**Returns**: Side-by-side comparison with field-level match/mismatch indicators. Timing-sensitive fields flagged as "expected variance."

**GAIT**: Logs comparison operation with target, data type, and result summary.

---

### 10. gnmi_list_targets

**Description**: List all configured gNMI target devices.

**Parameters**: None.

**Returns**: Array of configured targets with name, host, port, vendor (if set), and connection status (reachable/unreachable).

## Error Responses

All tools return structured error messages for:

| Error Code | Description |
|------------|-------------|
| CONNECTION_ERROR | Device unreachable, timeout, or connection refused |
| TLS_ERROR | TLS handshake failure, certificate mismatch, or CA verification failure |
| AUTH_ERROR | Authentication failure (invalid username/password) |
| PATH_ERROR | Invalid or unsupported YANG path on the target device |
| ENCODING_ERROR | Requested encoding not supported by the device |
| ITSM_ERROR | ServiceNow CR not found, not approved, or not in "Implement" state |
| SUBSCRIPTION_LIMIT | Maximum concurrent subscription limit (50) reached |
| SUBSCRIPTION_NOT_FOUND | Referenced subscription ID does not exist |
| RPC_ERROR | gNMI RPC-level error returned by the device |
| TRUNCATED | Response truncated due to size threshold |

Error messages NEVER expose credentials, certificate contents, or full connection strings.
