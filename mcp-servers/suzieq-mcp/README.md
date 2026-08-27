# SuzieQ MCP Server

Read-only MCP server for the [SuzieQ](https://suzieq.readthedocs.io/) network observability platform. Wraps the SuzieQ REST API and exposes network state queries, assertions, summaries, and path tracing as MCP tools via stdio transport.

## Tools (5)

| Tool | Description |
|------|-------------|
| `suzieq_show` | Query current or historical network state from any SuzieQ table with filtering by device, namespace, time range, and columns |
| `suzieq_summarize` | Get aggregated statistics and summary views of any network table |
| `suzieq_assert` | Run validation assertions against network state (bgp, ospf, interface, evpnVni) |
| `suzieq_unique` | Get distinct values and counts for a specific column in a table |
| `suzieq_path` | Trace the forwarding path between two endpoints hop-by-hop |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUZIEQ_API_URL` | Yes | SuzieQ REST API base URL (e.g., `http://suzieq-host:8000`) |
| `SUZIEQ_API_KEY` | Yes | SuzieQ REST API access token |
| `SUZIEQ_VERIFY_SSL` | No | Verify SSL certificates (default: `true`) |
| `SUZIEQ_TIMEOUT` | No | Query timeout in seconds (default: `30`) |

## Transport

**stdio** (JSON-RPC 2.0) — standard MCP stdio transport via FastMCP.

## Installation

```bash
cd mcp-servers/suzieq-mcp/
pip install -r requirements.txt
```

## Usage

### Standalone test

```bash
export SUZIEQ_API_URL="http://your-suzieq-host:8000"
export SUZIEQ_API_KEY="your-api-key"
python3 -u mcp-servers/suzieq-mcp/server.py
```

### Via MCP client

Once registered in `config/openclaw.json`:

- "Show me all BGP peers" -> `suzieq_show(table="bgp")`
- "Summarize route table" -> `suzieq_summarize(table="route")`
- "Assert BGP health" -> `suzieq_assert(table="bgp")`
- "Unique BGP states" -> `suzieq_unique(table="bgp", column="state")`
- "Trace path from 10.0.1.1 to 10.0.2.1" -> `suzieq_path(namespace="dc1", source="10.0.1.1", destination="10.0.2.1")`

## Supported Tables

address, arpnd, bgp, device, devconfig, evpnVni, fs, ifCounters, interface, inventory, lldp, mac, mlag, namespace, network, ospf, route, sqPoller, topology, vlan

## Assertion-Capable Tables

bgp, ospf, interface, evpnVni
