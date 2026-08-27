# MCP Tool Contracts: Telemetry Receivers

**Feature Branch**: `010-telemetry-receivers`
**Date**: 2026-03-28

This document defines the MCP tool interfaces for the three telemetry receiver servers.

---

## Syslog MCP Server (`syslog-mcp`)

### Tool Inventory

| # | Tool | Description | Safety |
|---|------|-------------|--------|
| 1 | `syslog_start_receiver` | Start the syslog UDP receiver | N/A |
| 2 | `syslog_stop_receiver` | Stop the syslog UDP receiver | N/A |
| 3 | `syslog_get_status` | Get receiver status and statistics | Read-only |
| 4 | `syslog_query` | Query stored syslog messages | Read-only |
| 5 | `syslog_get_message` | Get a specific message by ID | Read-only |
| 6 | `syslog_get_severity_counts` | Get message counts by severity | Read-only |

### Tool Definitions

#### syslog_start_receiver

Start the syslog UDP receiver on the specified port.

```json
{
  "name": "syslog_start_receiver",
  "description": "Start the syslog receiver to listen for UDP messages",
  "inputSchema": {
    "type": "object",
    "properties": {
      "port": {
        "type": "integer",
        "description": "UDP port to listen on",
        "default": 514,
        "minimum": 1,
        "maximum": 65535
      },
      "bind_address": {
        "type": "string",
        "description": "Address to bind to",
        "default": "0.0.0.0"
      }
    },
    "required": []
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Syslog receiver started on 0.0.0.0:514",
  "status": { /* ReceiverStatus object */ }
}
```

---

#### syslog_stop_receiver

Stop the syslog UDP receiver.

```json
{
  "name": "syslog_stop_receiver",
  "description": "Stop the syslog receiver",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

---

#### syslog_get_status

Get current receiver status and statistics.

```json
{
  "name": "syslog_get_status",
  "description": "Get syslog receiver status including message counts and uptime",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

**Response:**
```json
{
  "receiver_type": "syslog",
  "port": 514,
  "bind_address": "0.0.0.0",
  "is_running": true,
  "started_at": "2026-03-28T12:00:00Z",
  "messages_received": 1523,
  "messages_deduplicated": 12,
  "errors": 3,
  "last_message_time": "2026-03-28T12:05:32Z",
  "rate_limited_count": 0
}
```

---

#### syslog_query

Query stored syslog messages with filters.

```json
{
  "name": "syslog_query",
  "description": "Query syslog messages by time, severity, facility, hostname, or content",
  "inputSchema": {
    "type": "object",
    "properties": {
      "start_time": {
        "type": "string",
        "format": "date-time",
        "description": "Start of time range (ISO 8601)"
      },
      "end_time": {
        "type": "string",
        "format": "date-time",
        "description": "End of time range (ISO 8601)"
      },
      "severity_min": {
        "type": "integer",
        "description": "Minimum severity (0=Emergency, 7=Debug)",
        "minimum": 0,
        "maximum": 7
      },
      "severity_max": {
        "type": "integer",
        "description": "Maximum severity",
        "minimum": 0,
        "maximum": 7
      },
      "facility": {
        "type": "integer",
        "description": "Facility code (0-23)",
        "minimum": 0,
        "maximum": 23
      },
      "hostname": {
        "type": "string",
        "description": "Filter by hostname (exact match)"
      },
      "source_ip": {
        "type": "string",
        "description": "Filter by source IP address"
      },
      "message_contains": {
        "type": "string",
        "description": "Substring search in message content"
      },
      "limit": {
        "type": "integer",
        "description": "Maximum results to return",
        "default": 100,
        "maximum": 1000
      },
      "offset": {
        "type": "integer",
        "description": "Offset for pagination",
        "default": 0
      }
    },
    "required": []
  }
}
```

**Response:**
```json
{
  "total": 150,
  "returned": 100,
  "messages": [
    {
      "id": "uuid-1234",
      "received_at": "2026-03-28T12:05:30Z",
      "source_ip": "10.1.1.1",
      "severity": 3,
      "severity_name": "ERROR",
      "facility": 23,
      "facility_name": "LOCAL7",
      "hostname": "switch-01",
      "app_name": "SYS",
      "message": "%LINK-3-UPDOWN: Interface GigabitEthernet1/0/1, changed state to down"
    }
  ]
}
```

---

#### syslog_get_message

Get a specific syslog message by ID.

```json
{
  "name": "syslog_get_message",
  "description": "Get full details of a specific syslog message",
  "inputSchema": {
    "type": "object",
    "properties": {
      "message_id": {
        "type": "string",
        "description": "UUID of the message to retrieve"
      }
    },
    "required": ["message_id"]
  }
}
```

---

#### syslog_get_severity_counts

Get message counts grouped by severity level.

```json
{
  "name": "syslog_get_severity_counts",
  "description": "Get count of messages by severity level for a time range",
  "inputSchema": {
    "type": "object",
    "properties": {
      "start_time": {
        "type": "string",
        "format": "date-time"
      },
      "end_time": {
        "type": "string",
        "format": "date-time"
      }
    },
    "required": []
  }
}
```

**Response:**
```json
{
  "time_range": {
    "start": "2026-03-28T11:00:00Z",
    "end": "2026-03-28T12:00:00Z"
  },
  "counts": {
    "EMERGENCY": 0,
    "ALERT": 0,
    "CRITICAL": 2,
    "ERROR": 15,
    "WARNING": 45,
    "NOTICE": 120,
    "INFO": 890,
    "DEBUG": 0
  },
  "total": 1072
}
```

---

## SNMP Trap MCP Server (`snmptrap-mcp`)

### Tool Inventory

| # | Tool | Description | Safety |
|---|------|-------------|--------|
| 1 | `snmptrap_start_receiver` | Start the SNMP trap receiver | N/A |
| 2 | `snmptrap_stop_receiver` | Stop the SNMP trap receiver | N/A |
| 3 | `snmptrap_get_status` | Get receiver status and statistics | Read-only |
| 4 | `snmptrap_configure_v3_user` | Configure SNMPv3 USM user | N/A |
| 5 | `snmptrap_query` | Query stored traps | Read-only |
| 6 | `snmptrap_get_trap` | Get a specific trap by ID | Read-only |
| 7 | `snmptrap_get_link_events` | Get link up/down traps | Read-only |

### Tool Definitions

#### snmptrap_start_receiver

```json
{
  "name": "snmptrap_start_receiver",
  "description": "Start the SNMP trap receiver",
  "inputSchema": {
    "type": "object",
    "properties": {
      "port": {
        "type": "integer",
        "default": 162,
        "minimum": 1,
        "maximum": 65535
      },
      "bind_address": {
        "type": "string",
        "default": "0.0.0.0"
      },
      "community": {
        "type": "string",
        "description": "SNMPv2c community string for authentication"
      }
    },
    "required": []
  }
}
```

---

#### snmptrap_configure_v3_user

Configure an SNMPv3 USM user for authenticated traps.

```json
{
  "name": "snmptrap_configure_v3_user",
  "description": "Add or update an SNMPv3 user for trap authentication",
  "inputSchema": {
    "type": "object",
    "properties": {
      "user_name": {
        "type": "string",
        "description": "USM user name"
      },
      "auth_protocol": {
        "type": "string",
        "enum": ["MD5", "SHA", "SHA256", "SHA384", "SHA512", "NONE"],
        "description": "Authentication protocol"
      },
      "auth_key": {
        "type": "string",
        "description": "Authentication key/password"
      },
      "priv_protocol": {
        "type": "string",
        "enum": ["DES", "3DES", "AES128", "AES192", "AES256", "NONE"],
        "description": "Privacy/encryption protocol"
      },
      "priv_key": {
        "type": "string",
        "description": "Privacy key/password"
      }
    },
    "required": ["user_name"]
  }
}
```

---

#### snmptrap_query

```json
{
  "name": "snmptrap_query",
  "description": "Query SNMP traps by time, OID, version, or source",
  "inputSchema": {
    "type": "object",
    "properties": {
      "start_time": {
        "type": "string",
        "format": "date-time"
      },
      "end_time": {
        "type": "string",
        "format": "date-time"
      },
      "version": {
        "type": "string",
        "enum": ["v2c", "v3"]
      },
      "trap_oid": {
        "type": "string",
        "description": "Filter by exact trap OID"
      },
      "trap_name_contains": {
        "type": "string",
        "description": "Filter by trap name substring"
      },
      "source_ip": {
        "type": "string"
      },
      "limit": {
        "type": "integer",
        "default": 100,
        "maximum": 1000
      },
      "offset": {
        "type": "integer",
        "default": 0
      }
    },
    "required": []
  }
}
```

**Response:**
```json
{
  "total": 25,
  "returned": 25,
  "traps": [
    {
      "id": "uuid-5678",
      "received_at": "2026-03-28T12:03:15Z",
      "source_ip": "10.1.1.1",
      "version": "v2c",
      "trap_oid": "1.3.6.1.6.3.1.1.5.3",
      "trap_name": "linkDown",
      "varbinds": [
        {
          "oid": "1.3.6.1.2.1.2.2.1.1.1",
          "oid_name": "ifIndex",
          "value": 1,
          "value_type": "Integer"
        },
        {
          "oid": "1.3.6.1.2.1.2.2.1.2.1",
          "oid_name": "ifDescr",
          "value": "GigabitEthernet1/0/1",
          "value_type": "OctetString"
        }
      ]
    }
  ]
}
```

---

#### snmptrap_get_link_events

Convenience tool for getting interface link events.

```json
{
  "name": "snmptrap_get_link_events",
  "description": "Get linkUp and linkDown traps with interface details",
  "inputSchema": {
    "type": "object",
    "properties": {
      "start_time": {
        "type": "string",
        "format": "date-time"
      },
      "end_time": {
        "type": "string",
        "format": "date-time"
      },
      "source_ip": {
        "type": "string"
      },
      "event_type": {
        "type": "string",
        "enum": ["linkDown", "linkUp", "all"],
        "default": "all"
      },
      "limit": {
        "type": "integer",
        "default": 100
      }
    },
    "required": []
  }
}
```

---

## IPFIX MCP Server (`ipfix-mcp`)

### Tool Inventory

| # | Tool | Description | Safety |
|---|------|-------------|--------|
| 1 | `ipfix_start_receiver` | Start the IPFIX/NetFlow receiver | N/A |
| 2 | `ipfix_stop_receiver` | Stop the IPFIX/NetFlow receiver | N/A |
| 3 | `ipfix_get_status` | Get receiver status and statistics | Read-only |
| 4 | `ipfix_query_flows` | Query stored flow records | Read-only |
| 5 | `ipfix_get_top_talkers` | Get top N talkers by bytes/packets | Read-only |
| 6 | `ipfix_get_protocol_summary` | Get traffic breakdown by protocol | Read-only |
| 7 | `ipfix_list_templates` | List cached IPFIX templates | Read-only |

### Tool Definitions

#### ipfix_start_receiver

```json
{
  "name": "ipfix_start_receiver",
  "description": "Start the IPFIX/NetFlow v9 receiver",
  "inputSchema": {
    "type": "object",
    "properties": {
      "port": {
        "type": "integer",
        "default": 2055,
        "minimum": 1,
        "maximum": 65535
      },
      "bind_address": {
        "type": "string",
        "default": "0.0.0.0"
      }
    },
    "required": []
  }
}
```

---

#### ipfix_query_flows

```json
{
  "name": "ipfix_query_flows",
  "description": "Query flow records with filters",
  "inputSchema": {
    "type": "object",
    "properties": {
      "start_time": {
        "type": "string",
        "format": "date-time"
      },
      "end_time": {
        "type": "string",
        "format": "date-time"
      },
      "source_ip": {
        "type": "string",
        "description": "Source IP or CIDR prefix"
      },
      "destination_ip": {
        "type": "string",
        "description": "Destination IP or CIDR prefix"
      },
      "protocol": {
        "type": "integer",
        "description": "IP protocol number (6=TCP, 17=UDP, etc.)"
      },
      "port": {
        "type": "integer",
        "description": "Match source or destination port"
      },
      "min_bytes": {
        "type": "integer",
        "description": "Minimum bytes threshold"
      },
      "exporter_ip": {
        "type": "string",
        "description": "Filter by exporting device"
      },
      "limit": {
        "type": "integer",
        "default": 100,
        "maximum": 1000
      },
      "offset": {
        "type": "integer",
        "default": 0
      }
    },
    "required": []
  }
}
```

**Response:**
```json
{
  "total": 5420,
  "returned": 100,
  "flows": [
    {
      "id": "uuid-9012",
      "received_at": "2026-03-28T12:04:00Z",
      "exporter_ip": "10.1.1.1",
      "source_ip": "192.168.1.100",
      "destination_ip": "8.8.8.8",
      "source_port": 52341,
      "destination_port": 443,
      "protocol": 6,
      "protocol_name": "TCP",
      "bytes": 1523456,
      "packets": 1024,
      "flow_start": "2026-03-28T12:03:45Z",
      "flow_end": "2026-03-28T12:03:59Z"
    }
  ]
}
```

---

#### ipfix_get_top_talkers

```json
{
  "name": "ipfix_get_top_talkers",
  "description": "Get top N talkers by bytes or packets",
  "inputSchema": {
    "type": "object",
    "properties": {
      "start_time": {
        "type": "string",
        "format": "date-time"
      },
      "end_time": {
        "type": "string",
        "format": "date-time"
      },
      "group_by": {
        "type": "string",
        "enum": ["source_ip", "destination_ip", "source_destination_pair", "5_tuple"],
        "default": "source_ip",
        "description": "How to aggregate flows"
      },
      "sort_by": {
        "type": "string",
        "enum": ["bytes", "packets", "flows"],
        "default": "bytes"
      },
      "limit": {
        "type": "integer",
        "default": 10,
        "maximum": 100
      }
    },
    "required": []
  }
}
```

**Response:**
```json
{
  "time_range": {
    "start": "2026-03-28T11:00:00Z",
    "end": "2026-03-28T12:00:00Z"
  },
  "group_by": "source_ip",
  "sort_by": "bytes",
  "top_talkers": [
    {
      "key": "192.168.1.100",
      "total_bytes": 1523456789,
      "total_packets": 1024567,
      "flow_count": 342,
      "first_seen": "2026-03-28T11:02:15Z",
      "last_seen": "2026-03-28T11:59:45Z"
    }
  ]
}
```

---

#### ipfix_get_protocol_summary

```json
{
  "name": "ipfix_get_protocol_summary",
  "description": "Get traffic breakdown by IP protocol",
  "inputSchema": {
    "type": "object",
    "properties": {
      "start_time": {
        "type": "string",
        "format": "date-time"
      },
      "end_time": {
        "type": "string",
        "format": "date-time"
      },
      "exporter_ip": {
        "type": "string"
      }
    },
    "required": []
  }
}
```

**Response:**
```json
{
  "time_range": {
    "start": "2026-03-28T11:00:00Z",
    "end": "2026-03-28T12:00:00Z"
  },
  "protocols": [
    {
      "protocol": 6,
      "protocol_name": "TCP",
      "total_bytes": 1234567890,
      "total_packets": 987654,
      "flow_count": 5432,
      "percentage_bytes": 78.5
    },
    {
      "protocol": 17,
      "protocol_name": "UDP",
      "total_bytes": 234567890,
      "total_packets": 123456,
      "flow_count": 1234,
      "percentage_bytes": 14.9
    }
  ]
}
```

---

#### ipfix_list_templates

```json
{
  "name": "ipfix_list_templates",
  "description": "List cached IPFIX/NetFlow templates",
  "inputSchema": {
    "type": "object",
    "properties": {
      "exporter_ip": {
        "type": "string",
        "description": "Filter by exporter IP"
      }
    },
    "required": []
  }
}
```

**Response:**
```json
{
  "templates": [
    {
      "template_id": 256,
      "exporter_ip": "10.1.1.1",
      "observation_domain_id": 0,
      "field_count": 12,
      "received_at": "2026-03-28T12:00:00Z",
      "expires_at": "2026-03-28T12:30:00Z",
      "fields": ["sourceIPv4Address", "destinationIPv4Address", "protocolIdentifier", "sourceTransportPort", "destinationTransportPort", "octetDeltaCount", "packetDeltaCount"]
    }
  ]
}
```

---

## Environment Variables

### Syslog MCP Server

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SYSLOG_PORT` | No | 514 | UDP port for syslog receiver |
| `SYSLOG_BIND_ADDRESS` | No | 0.0.0.0 | Address to bind receiver |
| `SYSLOG_RETENTION_HOURS` | No | 24 | Hours to retain messages |
| `SYSLOG_RATE_LIMIT` | No | 1000 | Max messages per second |
| `SYSLOG_DEDUP_WINDOW` | No | 5 | Deduplication window in seconds |

### SNMP Trap MCP Server

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SNMPTRAP_PORT` | No | 162 | UDP port for trap receiver |
| `SNMPTRAP_BIND_ADDRESS` | No | 0.0.0.0 | Address to bind receiver |
| `SNMPTRAP_COMMUNITY` | No | public | SNMPv2c community string |
| `SNMPTRAP_V3_USERS` | No | - | JSON array of SNMPv3 users |
| `SNMPTRAP_RETENTION_HOURS` | No | 24 | Hours to retain traps |
| `SNMPTRAP_RATE_LIMIT` | No | 500 | Max traps per second |

### IPFIX MCP Server

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `IPFIX_PORT` | No | 2055 | UDP port for IPFIX/NetFlow receiver |
| `IPFIX_BIND_ADDRESS` | No | 0.0.0.0 | Address to bind receiver |
| `IPFIX_TEMPLATE_TIMEOUT` | No | 1800 | Template expiration in seconds |
| `IPFIX_RETENTION_HOURS` | No | 24 | Hours to retain flow records |
| `IPFIX_RATE_LIMIT` | No | 5000 | Max flows per second |
