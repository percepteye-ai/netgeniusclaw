# Research: SuzieQ MCP Server

**Feature**: 001-suzieq-mcp-server
**Date**: 2026-03-26

## R1: SuzieQ REST API Endpoint Patterns

**Decision**: Use SuzieQ REST API v2 with the URL pattern `{base_url}/api/v2/{table}/{verb}` and query parameters for filtering.

**Rationale**: The SuzieQ REST API mirrors its CLI command structure. The v2 API is the current stable version and uses FastAPI with automatic OpenAPI documentation. The URL pattern is `GET /api/v2/{table}/{verb}?param=value&access_token={key}`. This is well-documented and the community suzieq-mcp project (PovedaAqui/suzieq-mcp) has validated this approach.

**Alternatives considered**:
- Importing SuzieQ as a Python library: Rejected because the spec explicitly requires REST API integration, and library import would couple the MCP server to SuzieQ's internal APIs and dependencies.
- Using SuzieQ CLI subprocess calls: Rejected as fragile, slower, and harder to parse than structured JSON from the REST API.

## R2: SuzieQ Tables and Verbs

**Decision**: Support the following tables and verbs based on SuzieQ's documented capabilities:

**Tables** (network data types):
- `arpnd` - ARP/Neighbor Discovery
- `bgp` - BGP peers and routing
- `device` - Device inventory
- `evpnVni` - EVPN VNI information
- `interface` - Network interfaces
- `ifCounters` - Interface counters/statistics
- `lldp` - LLDP neighbor discovery
- `mac` - MAC address table
- `mlag` - MLAG/vPC state
- `ospf` - OSPF neighbors and state
- `route` - Routing table
- `sqPoller` - SuzieQ poller status
- `vlan` - VLAN configuration
- `address` - IP address assignments
- `inventory` - Hardware inventory
- `namespace` - Namespace listing
- `network` - Network find/topology
- `devconfig` - Device configuration
- `topology` - Network topology (alpha)
- `fs` - Filesystem information

**Verbs** (operations):
- `show` - Query detailed records (all tables)
- `summarize` - Aggregated statistics (all tables)
- `assert` - Validation assertions (bgp, ospf, interface, evpnVni only)
- `unique` - Distinct values with counts (all tables)
- `path` - Forwarding path trace (path table only, requires namespace/src/dest)

**Rationale**: This covers all tables documented in SuzieQ's analyzer documentation and CLI help. The `top` verb is excluded per the REST API docs which note it is not supported via REST.

**Alternatives considered**:
- Exposing only show and summarize (like PovedaAqui/suzieq-mcp): Rejected because the spec explicitly requires assert (FR-005) and path (FR-006) capabilities, and unique provides valuable operational insight.
- One generic tool for all operations: Rejected in favor of dedicated tools per verb for clearer tool descriptions and parameter validation.

## R3: HTTP Client Library

**Decision**: Use `httpx` with async support for all SuzieQ REST API calls.

**Rationale**: httpx is the standard async HTTP client in the Python ecosystem, used by the community suzieq-mcp project. It supports async/await natively, has excellent error handling, and handles both HTTP and HTTPS (including self-signed certificates which SuzieQ uses by default).

**Alternatives considered**:
- `aiohttp`: Heavier dependency, less Pythonic API. httpx is preferred in modern Python.
- `requests`: Synchronous only. FastMCP tools are async, so blocking calls would degrade performance.

## R4: Authentication Method

**Decision**: Pass the SuzieQ API key as an `access_token` query parameter on every request, read from the `SUZIEQ_API_KEY` environment variable.

**Rationale**: SuzieQ's REST API authenticates via an `access_token` query parameter (or Authorization header). The community project uses env vars for credentials, which aligns with NetGeniusClaw Constitution Principle XIII (Credential Safety). We will support both query parameter and Bearer token header for flexibility.

**Alternatives considered**:
- Hardcoded API key: Explicitly forbidden by Constitution XIII.
- Config file: Constitution XIII requires env vars, not config files.

## R5: SSL/TLS Handling

**Decision**: Support both HTTPS (default) and HTTP connections. For HTTPS, allow disabling certificate verification via `SUZIEQ_VERIFY_SSL` environment variable (default: true).

**Rationale**: SuzieQ defaults to HTTPS with self-signed certificates. In lab and development environments, certificate verification may need to be disabled. Production deployments should use proper certificates with verification enabled.

**Alternatives considered**:
- Always verify SSL: Would break most lab/dev setups where SuzieQ uses self-signed certs.
- Always skip verification: Security risk in production.

## R6: GAIT Audit Integration

**Decision**: Log all tool invocations to GAIT by calling the gait_mcp tools (gait_log_action or equivalent) at the start and end of each query. The MCP server itself will log via Python logging to stderr; GAIT integration will be handled at the skill level via the suzieq-observability skill.

**Rationale**: Following the NetGeniusClaw pattern where MCP servers focus on their domain and GAIT logging is coordinated by the orchestrating skill. This keeps the MCP server focused and testable independently.

**Alternatives considered**:
- Embedding GAIT calls directly in the MCP server: Would create a circular dependency and complicate testing.
- No GAIT logging: Violates Constitution IV (Immutable Audit Trail).

## R7: MCP Tool Design

**Decision**: Expose 5 MCP tools, one per SuzieQ verb:

1. `suzieq_show` - Query network table data with optional filters
2. `suzieq_summarize` - Get aggregated statistics for a table
3. `suzieq_assert` - Run validation assertions (bgp, ospf, interface, evpnVni)
4. `suzieq_unique` - Get distinct values for a column in a table
5. `suzieq_path` - Trace forwarding path between endpoints

Each tool accepts a `table` parameter (string) and optional filter parameters (namespace, hostname, start_time, end_time, columns, view, plus additional key-value filters).

**Rationale**: One tool per verb provides clear semantics and enables the LLM to select the right operation. The community project's two-tool approach (show + summarize) was too limited for the spec requirements. A single generic tool would make it harder for the LLM to understand available operations.

**Alternatives considered**:
- Single generic `suzieq_query` tool: Rejected for poor discoverability and unclear semantics.
- One tool per table (15+ tools): Too many tools, most with identical signatures. Verb-based grouping is more natural.
- Two tools like community project: Does not meet FR-005 (assert) and FR-006 (path) requirements.

## R8: Error Handling Strategy

**Decision**: Return structured error responses with descriptive messages for all failure modes:
- Connection errors: "SuzieQ API unreachable at {url}: {error}"
- Authentication errors: "SuzieQ authentication failed. Check SUZIEQ_API_KEY."
- Invalid table/verb: "Table '{table}' does not support '{verb}' operation."
- No data: "No data found for {table} with the specified filters." (not an error, per spec)
- Timeout: "SuzieQ query timed out after {timeout}s."

**Rationale**: FR-009 requires graceful error handling without exposing internals or credentials. The spec edge cases explicitly ask about unreachable API, unsupported tables, and empty results.

**Alternatives considered**:
- Raw exception passthrough: Would expose internal details, violating FR-009.
- Generic error messages: Would make debugging impossible for operators.
