# Research: gNMI Streaming Telemetry MCP Server

**Feature**: 003-gnmi-mcp-server | **Date**: 2026-03-26

## Research Tasks & Findings

### 1. gNMI Client Library Selection

**Decision**: Use `pygnmi` as the primary gNMI client library.

**Rationale**: pygnmi provides a high-level Pythonic API over gRPC for all four gNMI RPCs (Get, Set, Subscribe, Capabilities). It handles protobuf serialization/deserialization, supports multiple encoding formats (JSON, JSON_IETF, PROTO, ASCII), and has active maintenance. It abstracts the low-level gRPC channel management while still exposing enough control for TLS configuration and connection tuning.

**Alternatives considered**:
- `cisco-gnmi` (cisco_gnmi): Cisco-maintained, but vendor-biased and less actively maintained. API is more verbose for multi-vendor use cases. Rejected because pygnmi is more vendor-neutral.
- `grpcio` directly with compiled gNMI proto stubs: Maximum flexibility but requires manually managing protobuf compilation, serialization, and all RPC lifecycle. Too much boilerplate for the scope of this feature. Rejected because pygnmi already handles this.
- `gnmi-py`: Less mature, smaller community. Rejected for lower adoption and fewer examples.

### 2. Multi-Vendor gNMI Dialect Differences

**Decision**: Implement a vendor dialect abstraction layer that normalizes path encoding, origin prefixes, and encoding preferences per vendor.

**Rationale**: While gNMI is a standard protocol (defined by OpenConfig), vendors implement it with differences:
- **Cisco IOS-XR**: Uses `origin` field to distinguish OpenConfig vs. native YANG models (e.g., `openconfig` vs `Cisco-IOS-XR-*`). Supports JSON_IETF encoding primarily. gNMI port typically 57400.
- **Juniper Junos**: Uses flat path encoding. Supports JSON_IETF. gNMI port typically 32767 or 50051. Requires `target` field in path for multi-routing-engine.
- **Arista EOS**: Strong OpenConfig support. Supports JSON and JSON_IETF encoding. gNMI port typically 6030. Supports `cli-origin` for native CLI paths.
- **Nokia SR OS**: Uses gNMI with SR OS native YANG models alongside OpenConfig. JSON_IETF encoding. gNMI port typically 57400. Path encoding follows Nokia-specific conventions for some models.

The dialect layer will map vendor identifiers to default ports, preferred encodings, path prefix conventions, and origin handling.

**Alternatives considered**:
- No dialect layer (pass vendor differences to the user): Rejected because it violates Constitution Principle VI (Multi-Vendor Neutrality) which requires vendor-specific logic to be transparent to operators.
- Per-vendor MCP server: Rejected as it would create 4+ nearly-identical servers. A single server with dialect abstraction is more maintainable.

### 3. TLS Configuration Approach

**Decision**: Require TLS for all connections. Support both server-only TLS (CA verification) and mutual TLS (mTLS with client certificates). All TLS material referenced via environment variables.

**Rationale**: Constitution Principle IX (Security by Default) and FR-010 mandate TLS. Real-world gNMI deployments universally require TLS. The env var approach follows Constitution Principle XIII (Credential Safety).

**Environment variables for TLS**:
- `GNMI_TLS_CA_CERT`: Path to CA certificate bundle for verifying device certificates
- `GNMI_TLS_CLIENT_CERT`: Path to client certificate (for mTLS, optional)
- `GNMI_TLS_CLIENT_KEY`: Path to client private key (for mTLS, optional)
- `GNMI_TLS_SKIP_VERIFY`: Set to `true` only in lab mode (still uses TLS, but skips cert verification)

**Alternatives considered**:
- Allow plaintext (insecure) connections: Rejected per FR-010 and Constitution Principle IX.
- Embed certificates in env vars as base64: Rejected because file paths are simpler, more standard, and avoid env var size limits.

### 4. Subscription Management Architecture

**Decision**: In-memory subscription manager with asyncio tasks. Maximum 50 concurrent subscriptions enforced. Each subscription tracked by a UUID with metadata (device, path, mode, creation time).

**Rationale**: gNMI subscriptions are long-lived gRPC streams. Each subscription is an asyncio task that reads from the gRPC stream and buffers the latest updates. The 50-subscription limit prevents resource exhaustion. Subscriptions are ephemeral (lost on server restart) which is acceptable for an MCP server that runs as a stdio process.

**Alternatives considered**:
- Persistent subscription state in a database: Rejected because the MCP server uses stdio transport and runs per-session. Subscription persistence would require an external store and reconnection logic, adding complexity without clear benefit.
- No subscription limit: Rejected because unbounded gRPC streams can exhaust file descriptors and memory.

### 5. ITSM Gate Implementation for gNMI Set

**Decision**: Integrate with the existing `servicenow-mcp` server via MCP tool calls to validate Change Request status before executing gNMI Set operations.

**Rationale**: The existing ServiceNow MCP server (`mcp-servers/servicenow-mcp/`) already provides CR lifecycle management tools. The gNMI Set workflow will call the ServiceNow MCP to verify the CR exists and is in "Implement" state before proceeding. This reuses existing infrastructure rather than building a new ServiceNow integration.

**Alternatives considered**:
- Direct ServiceNow API calls from gnmi-mcp: Rejected because it duplicates the ServiceNow integration and violates Constitution Principle VII (Skill Modularity - don't duplicate functionality).
- Trust-based (user asserts they have a CR): Rejected because Constitution Principle III is NON-NEGOTIABLE - programmatic verification is required.

### 6. GAIT Audit Integration

**Decision**: Use the existing `gait_mcp` MCP server for audit logging. Every gNMI operation (Get, Set, Subscribe, Capabilities) will generate a GAIT audit record.

**Rationale**: The existing `mcp-servers/gait_mcp/` provides audit trail functionality. Reusing it follows Constitution Principle VII (don't duplicate). Each audit record will include: operation type, operator identity, target device, YANG path(s), timestamp, result status, and (for Set) the ServiceNow CR number.

**Alternatives considered**:
- Custom audit logging: Rejected as it duplicates gait_mcp functionality.
- Log only Set operations: Rejected per FR-008 which requires logging ALL operations.

### 7. Response Size Handling for Large gNMI Get Results

**Decision**: Implement response truncation with a configurable size threshold (default 1MB of formatted output). When exceeded, return the first portion with a truncation notice and the total size.

**Rationale**: gNMI Get on broad paths (e.g., root "/") can return very large responses. MCP tool responses need to be consumable by the LLM context window. A 1MB default balances usefulness with context window limits.

**Alternatives considered**:
- No truncation (return everything): Rejected because it could overwhelm LLM context windows and cause timeouts.
- Pagination via multiple tool calls: More complex to implement and requires stateful cursors. Rejected for initial implementation; can be added later.

### 8. gNMI-vs-CLI Comparison Implementation

**Decision**: Implement comparison as a skill-level workflow in `gnmi-telemetry` skill that calls both gNMI MCP tools and pyATS MCP tools, then performs field-level comparison with variance tolerance for timing-sensitive fields.

**Rationale**: The comparison requires data from two different MCP servers (gnmi-mcp and pyATS_MCP). A skill is the correct abstraction layer to orchestrate multi-server workflows per Constitution Principle VII.

**Alternatives considered**:
- Implement comparison inside gnmi-mcp server: Rejected because it would create a dependency on pyATS_MCP inside the gNMI server, violating separation of concerns.
- Standalone comparison MCP server: Overkill for a single comparison function. A skill workflow is simpler and more aligned with existing patterns.
