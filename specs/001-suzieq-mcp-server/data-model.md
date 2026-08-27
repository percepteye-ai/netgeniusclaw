# Data Model: SuzieQ MCP Server

**Feature**: 001-suzieq-mcp-server
**Date**: 2026-03-26

## Entities

### SuzieQConfig

Runtime configuration for the SuzieQ REST API connection, sourced entirely from environment variables.

| Field | Type | Source | Default | Validation |
|-------|------|--------|---------|------------|
| api_url | str | `SUZIEQ_API_URL` | (required) | Must be valid HTTP/HTTPS URL |
| api_key | str | `SUZIEQ_API_KEY` | (required) | Non-empty string |
| verify_ssl | bool | `SUZIEQ_VERIFY_SSL` | `true` | "true"/"false" |
| timeout | int | `SUZIEQ_TIMEOUT` | `30` | Positive integer (seconds) |

**Validation rules**:
- `api_url` must not have a trailing slash
- `api_url` must include the base path (e.g., `http://suzieq-host:8000`)
- Server must fail to start if `SUZIEQ_API_URL` or `SUZIEQ_API_KEY` are not set

### QueryRequest

Represents a query to the SuzieQ REST API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| table | str | Yes | SuzieQ table name (e.g., "bgp", "route", "interface") |
| verb | str | Yes | Operation: "show", "summarize", "assert", "unique" |
| namespace | str | No | Filter by SuzieQ namespace |
| hostname | str | No | Filter by device hostname |
| columns | str | No | Comma-separated list of columns to return |
| start_time | str | No | Start of time range (ISO 8601 or relative like "1h") |
| end_time | str | No | End of time range (ISO 8601 or relative) |
| view | str | No | Data view: "latest" (default), "all", or "changes" |
| query_filters | dict | No | Additional key-value filters passed as query parameters |

**Validation rules**:
- `table` must be a non-empty string (validated against known tables list for helpful errors, but unknown tables are still forwarded to SuzieQ)
- `verb` must be one of: show, summarize, assert, unique
- `assert` verb only valid for tables: bgp, ospf, interface, evpnVni
- `start_time` and `end_time` enable time-travel queries (US2)

### PathRequest

Represents a path trace query (separate from QueryRequest due to different required parameters).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| namespace | str | Yes | SuzieQ namespace (required for path) |
| source | str | Yes | Source IP address or hostname |
| destination | str | Yes | Destination IP address or hostname |
| vrf | str | No | VRF name (default: "default") |

**Validation rules**:
- All three required fields must be non-empty
- `source` and `destination` should be valid IP addresses or hostnames

### QueryResponse

Standardized response wrapper for all SuzieQ queries.

| Field | Type | Description |
|-------|------|-------------|
| success | bool | Whether the query completed successfully |
| table | str | The table that was queried |
| verb | str | The verb/operation performed |
| data | list[dict] | Array of result records (empty list if no data) |
| row_count | int | Number of records returned |
| error | str | None | Error message if success is False |
| filters_applied | dict | Echo of filters that were applied |

**State transitions**: N/A (stateless request/response model)

### AssertionResult

Specialized response for assert operations.

| Field | Type | Description |
|-------|------|-------------|
| success | bool | Whether the query completed successfully |
| table | str | The table assertions were run against |
| pass_count | int | Number of passing assertions |
| fail_count | int | Number of failing assertions |
| data | list[dict] | Detailed per-device assertion results |
| error | str | None | Error message if query itself failed |

## Relationships

```
SuzieQConfig --[configures]--> SuzieQClient
SuzieQClient --[executes]--> QueryRequest --> QueryResponse
SuzieQClient --[executes]--> PathRequest --> QueryResponse
QueryResponse --[specializes]--> AssertionResult (when verb == "assert")
```

## Known SuzieQ Tables

For validation and user guidance (not enforcement -- unknown tables are forwarded):

```python
KNOWN_TABLES = [
    "address", "arpnd", "bgp", "device", "devconfig",
    "evpnVni", "fs", "ifCounters", "interface", "inventory",
    "lldp", "mac", "mlag", "namespace", "network",
    "ospf", "route", "sqPoller", "topology", "vlan",
]

ASSERT_TABLES = ["bgp", "ospf", "interface", "evpnVni"]
```

## API URL Construction

```
Base pattern:  {api_url}/api/v2/{table}/{verb}
Path pattern:  {api_url}/api/v2/path/show

Query params:  ?access_token={api_key}&namespace={ns}&hostname={host}&...
```
