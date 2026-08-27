# MCP Tool Contracts: SuzieQ MCP Server

**Feature**: 001-suzieq-mcp-server
**Date**: 2026-03-26
**Transport**: stdio

## Tool 1: suzieq_show

**Description**: Query detailed network state data from any SuzieQ table. Supports filtering by device, namespace, time range, and columns. Use for current or historical (time-travel) network state queries.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| table | string | Yes | SuzieQ table name (e.g., "bgp", "route", "interface", "ospf", "arpnd", "mac", "lldp", "vlan", "mlag", "device", "evpnVni", "ifCounters", "address", "inventory") |
| namespace | string | No | Filter by SuzieQ namespace |
| hostname | string | No | Filter by device hostname |
| columns | string | No | Comma-separated column names to return (default: all columns) |
| start_time | string | No | Start time for time-travel query (ISO 8601 or relative e.g. "1h", "2d") |
| end_time | string | No | End time for time-travel query (ISO 8601 or relative) |
| view | string | No | Data view: "latest" (default), "all", or "changes" |
| filters | string | No | Additional filters as key=value pairs separated by ampersand (e.g. "state=Established&vrf=default") |

**Returns**: JSON string with query results including table name, row count, and array of records. Returns descriptive message if no data found.

**Example invocations**:
- Show all BGP peers: `suzieq_show(table="bgp")`
- Show routes on specific device: `suzieq_show(table="route", hostname="spine01")`
- Time-travel query: `suzieq_show(table="interface", start_time="2026-03-25T14:00:00")`
- Filtered query: `suzieq_show(table="bgp", namespace="datacenter1", filters="state=Established")`

---

## Tool 2: suzieq_summarize

**Description**: Get aggregated statistics and summary views of any SuzieQ network table. Returns counts, distributions, and per-device breakdowns rather than individual records.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| table | string | Yes | SuzieQ table name |
| namespace | string | No | Filter by SuzieQ namespace |
| hostname | string | No | Filter by device hostname |
| start_time | string | No | Start time for historical summary |
| end_time | string | No | End time for historical summary |

**Returns**: JSON string with summarized statistics including counts, distributions, and per-device/namespace breakdowns.

**Example invocations**:
- Summarize routes: `suzieq_summarize(table="route")`
- Summarize interfaces in namespace: `suzieq_summarize(table="interface", namespace="datacenter1")`

---

## Tool 3: suzieq_assert

**Description**: Run validation assertions against network state. Checks conditions like "all BGP peers should be established" or "no interface should have errors". Only supported for tables: bgp, ospf, interface, evpnVni.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| table | string | Yes | Table to assert against. Must be one of: bgp, ospf, interface, evpnVni |
| namespace | string | No | Filter by SuzieQ namespace |
| hostname | string | No | Filter by device hostname |

**Returns**: JSON string with assertion results including pass/fail counts and per-device details on any failures.

**Example invocations**:
- Assert BGP health: `suzieq_assert(table="bgp")`
- Assert OSPF in namespace: `suzieq_assert(table="ospf", namespace="datacenter1")`
- Assert interfaces on device: `suzieq_assert(table="interface", hostname="leaf01")`

---

## Tool 4: suzieq_unique

**Description**: Get distinct values and their counts for a specific column in a SuzieQ table. Useful for understanding the distribution of values (e.g., unique VRFs, unique interface states, unique BGP peer ASNs).

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| table | string | Yes | SuzieQ table name |
| column | string | Yes | Column name to get unique values for |
| namespace | string | No | Filter by SuzieQ namespace |
| hostname | string | No | Filter by device hostname |

**Returns**: JSON string with distinct values and their occurrence counts.

**Example invocations**:
- Unique BGP states: `suzieq_unique(table="bgp", column="state")`
- Unique VRFs in routes: `suzieq_unique(table="route", column="vrf")`

---

## Tool 5: suzieq_path

**Description**: Trace the forwarding path between two endpoints through the network. Returns hop-by-hop path with ingress/egress interfaces and forwarding decisions at each node.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| namespace | string | Yes | SuzieQ namespace (required for path resolution) |
| source | string | Yes | Source IP address |
| destination | string | Yes | Destination IP address |
| vrf | string | No | VRF name (default: "default") |

**Returns**: JSON string with hop-by-hop forwarding path including ingress/egress interfaces, next-hops, and forwarding decisions.

**Example invocations**:
- Trace path: `suzieq_path(namespace="datacenter1", source="10.0.1.1", destination="10.0.2.1")`
- Trace in VRF: `suzieq_path(namespace="datacenter1", source="10.0.1.1", destination="10.0.2.1", vrf="mgmt")`

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| SUZIEQ_API_URL | Yes | SuzieQ REST API base URL (e.g., http://suzieq-host:8000) |
| SUZIEQ_API_KEY | Yes | SuzieQ REST API access token |
| SUZIEQ_VERIFY_SSL | No | Verify SSL certificates (default: true) |
| SUZIEQ_TIMEOUT | No | Query timeout in seconds (default: 30) |

## Error Responses

All tools return structured error messages for:
- **Connection failure**: "SuzieQ API unreachable at {url}: {detail}"
- **Authentication failure**: "SuzieQ authentication failed. Verify SUZIEQ_API_KEY is correct."
- **Invalid table for assert**: "Table '{table}' does not support assertions. Supported: bgp, ospf, interface, evpnVni."
- **No data**: "No data found for {table} with the specified filters." (not treated as error)
- **Timeout**: "SuzieQ query timed out after {timeout}s. Try narrowing filters."
