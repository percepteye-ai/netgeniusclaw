# Data Model: Telemetry & Event Receiver Capabilities

**Feature Branch**: `010-telemetry-receivers`
**Date**: 2026-03-28
**Spec**: [spec.md](./spec.md)

## Overview

This document defines the data models for the three telemetry receiver MCP servers. All data is stored in-memory only (per clarification decision). Models use Pydantic for validation and serialization.

---

## Shared Models

### ReceiverStatus

Tracks the operational status of each receiver.

```python
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class ReceiverType(str, Enum):
    SYSLOG = "syslog"
    SNMPTRAP = "snmptrap"
    IPFIX = "ipfix"

class ReceiverStatus(BaseModel):
    """Operational status of a receiver (FR-019)"""
    receiver_type: ReceiverType
    port: int
    bind_address: str = "0.0.0.0"
    is_running: bool = False
    started_at: datetime | None = None
    messages_received: int = 0
    messages_deduplicated: int = 0
    errors: int = 0
    last_message_time: datetime | None = None
    rate_limited_count: int = 0
```

### QueryFilter

Common filter parameters for querying stored messages.

```python
class TimeRange(BaseModel):
    """Time range filter for queries"""
    start: datetime | None = None
    end: datetime | None = None

class QueryFilter(BaseModel):
    """Base filter for all query operations"""
    time_range: TimeRange | None = None
    source_ip: str | None = None
    limit: int = 100
    offset: int = 0
```

---

## Syslog MCP Server Models

### SyslogMessage

Represents a parsed syslog message (RFC 5424 or RFC 3164).

```python
from typing import Dict, List, Any

class SyslogFacility(int, Enum):
    """Syslog facility codes (0-23)"""
    KERN = 0
    USER = 1
    MAIL = 2
    DAEMON = 3
    AUTH = 4
    SYSLOG = 5
    LPR = 6
    NEWS = 7
    UUCP = 8
    CRON = 9
    AUTHPRIV = 10
    FTP = 11
    NTP = 12
    AUDIT = 13
    ALERT = 14
    CLOCK = 15
    LOCAL0 = 16
    LOCAL1 = 17
    LOCAL2 = 18
    LOCAL3 = 19
    LOCAL4 = 20
    LOCAL5 = 21
    LOCAL6 = 22
    LOCAL7 = 23

class SyslogSeverity(int, Enum):
    """Syslog severity levels (0-7, lower = more severe)"""
    EMERGENCY = 0   # System is unusable
    ALERT = 1       # Action must be taken immediately
    CRITICAL = 2    # Critical conditions
    ERROR = 3       # Error conditions
    WARNING = 4     # Warning conditions
    NOTICE = 5      # Normal but significant
    INFO = 6        # Informational
    DEBUG = 7       # Debug-level messages

class StructuredDataElement(BaseModel):
    """RFC 5424 Structured Data Element"""
    sd_id: str
    params: Dict[str, str]

class SyslogMessage(BaseModel):
    """Parsed syslog message (FR-001 through FR-005)"""
    id: str                                    # Unique message ID (UUID)
    received_at: datetime                      # When NetGeniusClaw received it
    source_ip: str                             # Source device IP
    source_port: int                           # Source UDP port

    # RFC 5424 fields
    version: int | None = None                 # Protocol version (1 for RFC 5424)
    facility: SyslogFacility
    severity: SyslogSeverity
    timestamp: datetime | None = None          # Message timestamp from device
    hostname: str | None = None
    app_name: str | None = None
    process_id: str | None = None
    message_id: str | None = None
    structured_data: List[StructuredDataElement] = []
    message: str                               # MSG content

    # Metadata
    rfc_format: str = "5424"                   # "5424" or "3164"
    raw_message: str | None = None             # Original unparsed message
    parse_errors: List[str] = []               # Any parsing warnings

    @property
    def priority(self) -> int:
        """Calculate PRI value: facility * 8 + severity"""
        return self.facility.value * 8 + self.severity.value

class SyslogQueryFilter(QueryFilter):
    """Syslog-specific query filters"""
    severity_min: SyslogSeverity | None = None  # Minimum severity (0-7)
    severity_max: SyslogSeverity | None = None  # Maximum severity (0-7)
    facility: SyslogFacility | None = None
    hostname: str | None = None
    app_name: str | None = None
    message_contains: str | None = None
```

---

## SNMP Trap MCP Server Models

### SNMPTrap

Represents a received SNMP trap (v2c or v3).

```python
class SNMPVersion(str, Enum):
    V2C = "v2c"
    V3 = "v3"

class SNMPSecurityLevel(str, Enum):
    """SNMPv3 security levels"""
    NO_AUTH_NO_PRIV = "noAuthNoPriv"
    AUTH_NO_PRIV = "authNoPriv"
    AUTH_PRIV = "authPriv"

class VarBind(BaseModel):
    """SNMP Variable Binding"""
    oid: str                    # Full OID string (e.g., "1.3.6.1.2.1.1.3.0")
    oid_name: str | None = None # Resolved name (e.g., "sysUpTime")
    value: Any                  # Value (type varies)
    value_type: str             # ASN.1 type (Integer, OctetString, etc.)

class SNMPTrap(BaseModel):
    """Received SNMP trap (FR-006 through FR-011)"""
    id: str                                    # Unique trap ID (UUID)
    received_at: datetime                      # When NetGeniusClaw received it
    source_ip: str                             # Source device IP
    source_port: int                           # Source UDP port

    # SNMP version and auth
    version: SNMPVersion
    community: str | None = None               # v2c community string
    security_name: str | None = None           # v3 USM user
    security_level: SNMPSecurityLevel | None = None  # v3 security level

    # Trap identification
    trap_oid: str                              # snmpTrapOID value
    trap_name: str | None = None               # Resolved trap name
    enterprise_oid: str | None = None          # Enterprise OID (v1 style)
    generic_trap: int | None = None            # Generic trap type (v1)
    specific_trap: int | None = None           # Specific trap type (v1)

    # System info from trap
    sys_uptime: int | None = None              # sysUpTime.0 value
    agent_address: str | None = None           # Agent address (v1)

    # Variable bindings
    varbinds: List[VarBind] = []

    # Metadata
    raw_pdu: str | None = None                 # Hex-encoded raw PDU
    mib_resolution_errors: List[str] = []      # OIDs that couldn't be resolved

class TrapQueryFilter(QueryFilter):
    """SNMP trap-specific query filters"""
    version: SNMPVersion | None = None
    trap_oid: str | None = None
    trap_name_contains: str | None = None
    # Standard trap shortcuts
    is_link_down: bool | None = None
    is_link_up: bool | None = None

# Well-known trap OIDs (FR-010)
STANDARD_TRAP_OIDS = {
    "1.3.6.1.6.3.1.1.5.1": "coldStart",
    "1.3.6.1.6.3.1.1.5.2": "warmStart",
    "1.3.6.1.6.3.1.1.5.3": "linkDown",
    "1.3.6.1.6.3.1.1.5.4": "linkUp",
    "1.3.6.1.6.3.1.1.5.5": "authenticationFailure",
}
```

---

## IPFIX MCP Server Models

### FlowRecord

Represents an IPFIX/NetFlow flow record.

```python
class IPProtocol(int, Enum):
    """Common IP protocol numbers"""
    ICMP = 1
    TCP = 6
    UDP = 17
    GRE = 47
    ESP = 50
    ICMPV6 = 58

class FlowRecord(BaseModel):
    """IPFIX/NetFlow flow record (FR-012 through FR-016)"""
    id: str                                    # Unique record ID (UUID)
    received_at: datetime                      # When NetGeniusClaw received it
    exporter_ip: str                           # Source device IP
    exporter_port: int                         # Source UDP port

    # Flow timing
    flow_start: datetime | None = None         # Flow start time
    flow_end: datetime | None = None           # Flow end time
    duration_ms: int | None = None             # Flow duration

    # 5-tuple
    source_ip: str
    destination_ip: str
    source_port: int | None = None
    destination_port: int | None = None
    protocol: int                              # IP protocol number

    # Counters
    bytes: int = 0                             # octetDeltaCount
    packets: int = 0                           # packetDeltaCount
    bytes_per_second: float | None = None      # Calculated rate

    # Additional fields (may not always be present)
    tcp_flags: int | None = None               # TCP flags bitmask
    tos: int | None = None                     # Type of service
    input_interface: int | None = None         # SNMP ifIndex
    output_interface: int | None = None        # SNMP ifIndex
    src_as: int | None = None                  # Source AS number
    dst_as: int | None = None                  # Destination AS number
    src_mask: int | None = None                # Source prefix length
    dst_mask: int | None = None                # Destination prefix length
    next_hop: str | None = None                # Next hop IP

    # Template info
    template_id: int | None = None             # IPFIX template ID used
    observation_domain_id: int | None = None   # Observation domain

class IPFIXTemplate(BaseModel):
    """Cached IPFIX template (FR-013)"""
    template_id: int
    exporter_ip: str
    observation_domain_id: int
    fields: List[Dict[str, Any]]               # Field definitions
    received_at: datetime
    expires_at: datetime                       # Template expiration (30 min default)

class FlowQueryFilter(QueryFilter):
    """Flow-specific query filters"""
    source_ip_prefix: str | None = None        # CIDR prefix filter
    destination_ip_prefix: str | None = None
    protocol: int | None = None
    min_bytes: int | None = None
    min_packets: int | None = None
    port: int | None = None                    # Match either src or dst port

class TopTalkersResult(BaseModel):
    """Aggregated top talkers result"""
    key: str                                   # Aggregation key (IP, IP pair, etc.)
    total_bytes: int
    total_packets: int
    flow_count: int
    first_seen: datetime
    last_seen: datetime
```

---

## Entity Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                        MessageStore                              │
│  (In-memory, per MCP server, 24-hour retention, dedup enabled)  │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  SyslogMessage  │  │    SNMPTrap     │  │   FlowRecord    │
│  (syslog-mcp)   │  │  (snmptrap-mcp) │  │   (ipfix-mcp)   │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ • id            │  │ • id            │  │ • id            │
│ • received_at   │  │ • received_at   │  │ • received_at   │
│ • source_ip     │  │ • source_ip     │  │ • exporter_ip   │
│ • severity      │  │ • trap_oid      │  │ • 5-tuple       │
│ • facility      │  │ • varbinds[]    │  │ • bytes/packets │
│ • message       │  │ • version       │  │ • template_id   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │     VarBind     │
                     ├─────────────────┤
                     │ • oid           │
                     │ • oid_name      │
                     │ • value         │
                     │ • value_type    │
                     └─────────────────┘

                     ┌─────────────────┐
                     │  IPFIXTemplate  │
                     │  (Template cache)│
                     ├─────────────────┤
                     │ • template_id   │
                     │ • exporter_ip   │
                     │ • fields[]      │
                     │ • expires_at    │
                     └─────────────────┘
```

---

## Validation Rules

### SyslogMessage
- `facility` must be in range 0-23
- `severity` must be in range 0-7
- `source_ip` must be valid IPv4 or IPv6
- `timestamp` should be within reasonable range (not future, not ancient)

### SNMPTrap
- `trap_oid` must be valid OID format (dot-separated numbers)
- `version` determines which auth fields are required
- If `version == v3`, then `security_name` is required
- If `version == v2c`, then `community` is required

### FlowRecord
- `source_ip` and `destination_ip` must be valid IP addresses
- `protocol` must be valid IP protocol number (1-255)
- `bytes` and `packets` must be non-negative
- `source_port` and `destination_port` valid only for TCP/UDP (protocol 6 or 17)

---

## State Transitions

These receivers are passive listeners with no complex state machines. The only state tracked is:

1. **Receiver State**: STOPPED → RUNNING → STOPPED
2. **Template State** (IPFIX only): UNKNOWN → CACHED → EXPIRED

```
Receiver Lifecycle:
┌────────┐  start()  ┌─────────┐  stop()  ┌────────┐
│STOPPED │──────────▶│ RUNNING │─────────▶│STOPPED │
└────────┘           └─────────┘          └────────┘
                          │
                          │ on_message()
                          ▼
                    [Parse & Store]
                          │
                    [GAIT Log]
```
