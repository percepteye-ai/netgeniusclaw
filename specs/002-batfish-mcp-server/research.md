# Research: Batfish MCP Server

**Feature Branch**: `002-batfish-mcp-server`
**Date**: 2026-03-26

## Research Task 1: pybatfish Client Library API and Session Management

**Decision**: Use `pybatfish` Python client library with `Session` as the primary interface to Batfish.

**Rationale**: pybatfish is the official Python client for Batfish, maintained by Intentionet (the Batfish creators). It provides a high-level `Session` class that handles REST communication with the Batfish service. The `Session` object manages network initialization, snapshot creation, and all analysis queries. This is the only supported Python interface for Batfish.

**Key API patterns**:
- `Session(host=BATFISH_HOST)` — creates a session to the Batfish service
- `bf.set_network(name)` / `bf.init_snapshot(path, name)` — create snapshots from config directories
- `bf.q.nodeProperties()`, `bf.q.fileParseStatus()` — validation queries
- `bf.q.traceroute()`, `bf.q.reachability()` — reachability analysis
- `bf.q.searchFilters()`, `bf.q.testFilters()` — ACL/filter tracing
- `bfq.differentialReachability()` — cross-snapshot comparison
- All queries return Pandas DataFrames

**Alternatives considered**:
- Direct REST API calls: Lower-level, more maintenance burden, less readable. Rejected because pybatfish abstracts all REST calls and handles serialization/deserialization.
- Batfish Java API: Not suitable for Python MCP server. Rejected.

## Research Task 2: Batfish Docker Container Setup and Connectivity

**Decision**: Batfish runs as a pre-existing Docker container (`batfish/batfish`) on localhost. The MCP server connects via environment variables `BATFISH_HOST` (default: `localhost`) and `BATFISH_PORT` (default: `9997`).

**Rationale**: The standard Batfish deployment model is `docker run -d -p 9997:9997 -p 9996:9996 batfish/batfish`. Port 9997 is the Batfish coordinator service; port 9996 is the worker. pybatfish connects to the coordinator on 9997 by default. This MCP server does not manage the Docker container lifecycle — it assumes Batfish is already running.

**Alternatives considered**:
- Embedded Batfish (Java process): Too heavy, requires JVM. Rejected.
- Batfish-as-a-Service (cloud): No official hosted Batfish service exists. Rejected.
- MCP server starts Batfish container: Violates separation of concerns and requires Docker access. Rejected.

## Research Task 3: Snapshot Creation from Configuration Files

**Decision**: Configurations are provided as file paths or inline content. The MCP server creates a temporary directory with the Batfish-expected structure (`configs/` subdirectory), writes config files there, and calls `bf.init_snapshot()`.

**Rationale**: Batfish expects snapshots to be a directory containing a `configs/` subdirectory with device configuration files. Each file is named after the device (e.g., `router1.cfg`). pybatfish's `init_snapshot()` accepts a local directory path and uploads it to the Batfish service. Using `tempfile.mkdtemp()` for ephemeral working directories is clean and avoids filesystem pollution.

**Alternatives considered**:
- Accept raw config text via MCP tool parameter: Possible for single-device, but multi-device needs file structure. Decision: support both — inline config for single device, directory path for multi-device.
- Accept ZIP archives: Adds complexity. Can be a future enhancement.

## Research Task 4: FastMCP Server Pattern for NetGeniusClaw

**Decision**: Follow the existing pyATS_MCP pattern — single Python file, FastMCP constructor, `@mcp.tool()` decorators, stdio transport, environment variables via `python-dotenv`.

**Rationale**: All existing NetGeniusClaw MCP servers follow this pattern. Consistency reduces cognitive load and ensures compatibility with the OpenClaw gateway configuration. The pyATS_MCP server is the closest reference implementation.

**Alternatives considered**:
- Multi-file package structure: Overkill for 6 tools. Rejected in favor of single-file simplicity.
- SSE transport: stdio is the NetGeniusClaw standard and simpler to configure. Rejected.

## Research Task 5: GAIT Audit Logging Integration

**Decision**: Import and use the `gait_mcp` module for audit logging. Each tool invocation logs the analysis type, snapshot identifier, query parameters, and result summary.

**Rationale**: FR-010 requires all analysis operations to be recorded in the GAIT audit trail. The existing `gait_mcp` module provides the logging interface used by other NetGeniusClaw MCP servers. Following this pattern ensures consistency.

**Alternatives considered**:
- Custom logging to files: Does not integrate with GAIT. Rejected.
- Git-commit-based logging: Too heavy for per-query logging. GAIT handles this internally. Rejected.

## Research Task 6: Multi-Vendor Configuration Support

**Decision**: Batfish natively handles multi-vendor parsing. The MCP server does not need vendor-specific logic — it passes configurations to Batfish and reports parse results.

**Rationale**: Batfish supports Cisco IOS, IOS-XE, NX-OS, Juniper JunOS, Arista EOS, Palo Alto PAN-OS, and F5 BIG-IP configurations. The vendor is auto-detected from configuration syntax. The MCP server simply reports what Batfish finds, including any parse warnings for unsupported features or vendors.

**Alternatives considered**:
- Vendor detection in MCP server: Unnecessary duplication since Batfish already does this. Rejected.
- Vendor-specific tools: Would fragment the API. Rejected in favor of vendor-neutral tools that work across all supported platforms.

## Research Task 7: Compliance Checking Implementation

**Decision**: Use Batfish's built-in assertion queries (e.g., `bf.q.interfaceProperties()`, `bf.q.routes()`, `bf.q.nodeProperties()`) to implement compliance rules. The `check_compliance` tool accepts a policy type (e.g., `interface_descriptions`, `no_default_route`, `ntp_configured`) and runs the corresponding Batfish query with pass/fail evaluation.

**Rationale**: Batfish does not have a native "compliance engine" but its rich query library can answer any structural question about a network snapshot. By mapping common policy rules to specific Batfish queries, we can provide a compliance checking experience. A set of predefined policy types covers the most common use cases (per US5 acceptance scenarios).

**Alternatives considered**:
- Custom policy DSL: Too complex for initial release. Can be a future enhancement.
- External compliance engine (e.g., Batfish Policycheck): No maintained external tool exists. Rejected.

## Research Task 8: Error Handling for Batfish Service Failures

**Decision**: Wrap all pybatfish calls in try/except blocks. Connection failures return a structured error message indicating the Batfish service is unreachable. Analysis timeouts return a timeout message with the snapshot ID. Never expose stack traces or credentials in error responses (FR-012).

**Rationale**: The edge cases in the spec explicitly ask about connection timeouts, unsupported vendors, and large snapshot handling. Graceful error handling is critical for a good operator experience and for security (no credential leakage).

**Alternatives considered**:
- Let exceptions propagate to FastMCP: Would expose internal details. Rejected.
- Retry logic: May mask problems. Decision: no automatic retries — report the error and let the operator decide.
