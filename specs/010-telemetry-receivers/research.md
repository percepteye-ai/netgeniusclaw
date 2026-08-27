# Research: Telemetry & Event Receiver Capabilities

**Feature Branch**: `010-telemetry-receivers`
**Date**: 2026-03-28
**Spec**: [spec.md](./spec.md)

## Research Summary

This document consolidates research findings for implementing three telemetry receiver MCP servers (syslog-mcp, snmptrap-mcp, ipfix-mcp) and validating the existing gnmi-mcp.

---

## R1: Syslog Parsing Libraries (RFC 5424/3164)

### Decision: Custom parser with fallback logic

### Rationale

The existing [syslog-rfc5424-parser](https://github.com/EasyPost/syslog-rfc5424-parser) library from EasyPost uses the Lark parser-generator and can parse approximately 4,300 messages per second on a single thread. This exceeds our 1,000 msg/sec requirement (SC-001). However, the library:
- Has low recent maintenance (no new releases in 12 months)
- Only supports RFC 5424, not the legacy RFC 3164 BSD syslog format

For RFC 3164 fallback (FR-003), we need to implement our own parser or combine libraries.

### Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| syslog-rfc5424-parser | RFC 5424 compliant, 4,300 msg/sec | No RFC 3164 support, low maintenance |
| loggerglue.rfc5424 | Full SyslogEntry object | Less documented, older |
| Custom parser | Full control, both RFC formats | More development time |

### Implementation Approach

1. Use `syslog-rfc5424-parser` for RFC 5424 messages (primary)
2. Implement simple regex-based RFC 3164 fallback parser
3. Detection logic: RFC 5424 starts with `<PRI>VERSION`, RFC 3164 starts with `<PRI>TIMESTAMP`

### RFC 5424 Message Format (from research)

```
SYSLOG-MSG = HEADER SP STRUCTURED-DATA [SP MSG]
HEADER = PRI VERSION SP TIMESTAMP SP HOSTNAME SP APP-NAME SP PROCID SP MSGID
PRI = "<" PRIVAL ">" (range 0-191)
```

- Facility: 0-23 (kernel, user, mail, daemon, auth, syslog, lpr, news, uucp, clock, auth-priv, ftp, ntp, audit, alert, clock2, local0-7)
- Severity: 0-7 (Emergency, Alert, Critical, Error, Warning, Notice, Info, Debug)
- PRIVAL = Facility * 8 + Severity

---

## R2: SNMP Trap Receiver (SNMPv2c/v3)

### Decision: PySNMP 7.1.x with asyncio

### Rationale

[PySNMP](https://github.com/pysnmp/pysnmp) is the standard Python SNMP library, now maintained by LeXtudio Inc. (since 2022). Version 7.1.x provides:
- Full SNMPv1, SNMPv2c, and SNMPv3 support
- USM Extended Security Options (3DES, AES-192/256)
- Native asyncio integration
- Notification receiver (trap listener) examples

The library meets all our requirements (FR-006 through FR-011):
- SNMPv2c community string authentication
- SNMPv3 USM with noAuthNoPriv, authNoPriv, authPriv
- MD5/SHA for auth, DES/AES for priv (with cryptography package)

### Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| pysnmp 7.1.x | Actively maintained, full asyncio, SNMPv3 | Heavy dependency tree |
| pynetsnmp | Faster (C bindings) | No asyncio, less maintained |
| easysnmp | Simple API | No trap receiver support |

### Implementation Notes

- Use `pysnmp.hlapi.v3arch.asyncio` for trap receiver
- Configure USM users with `UsmUserData` class
- Handle trap OIDs with standard MIB resolution (RFC 3418)
- Standard traps: linkDown (1.3.6.1.6.3.1.1.5.3), linkUp (1.3.6.1.6.3.1.1.5.4), coldStart (1.3.6.1.6.3.1.1.5.1), warmStart (1.3.6.1.6.3.1.1.5.2), authenticationFailure (1.3.6.1.6.3.1.1.5.5)

---

## R3: IPFIX/NetFlow Receiver (RFC 7011)

### Decision: netflow library (PyPI) with template caching

### Rationale

The [netflow](https://pypi.org/project/netflow/) Python package (by bitkeks) provides:
- NetFlow v1, v5, v9 parser and collector
- IPFIX support (based on NetFlow v9, standardized by IETF)
- Template management for v9/IPFIX
- CLI reference collector implementation

Key consideration from documentation: "In NetFlow v9 and IPFIX, templates are used instead of a fixed set of fields. You must store received templates in between exports and pass them to the parser when new packets arrive."

This directly maps to our FR-013 (cache IPFIX template records) and FR-014 (standard Information Elements).

### Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| netflow (PyPI) | Python 3, v9+IPFIX, maintained | Moderate performance |
| python-ipfix (britram) | Pure IPFIX | Older, Python 2.7 era |
| Custom decoder | Full control | Significant effort |

### Implementation Notes

- Use `netflow.parse_packet()` as main API
- Maintain template cache dictionary keyed by (source_ip, template_id)
- Templates expire after 30 minutes (Cisco default)
- Standard Information Elements: sourceIPv4Address (8), destinationIPv4Address (12), protocolIdentifier (4), sourceTransportPort (7), destinationTransportPort (11), octetDeltaCount (1), packetDeltaCount (2)

---

## R4: UDP Tunnel Limitation (CRITICAL)

### Decision: Use alternatives to ngrok OR TCP/TLS transport

### Rationale

**ngrok does NOT support UDP tunnels.** This is a critical finding that affects our testing approach since:
- Syslog default: UDP 514
- SNMP traps default: UDP 162
- IPFIX/NetFlow default: UDP 2055

### Alternatives for UDP Tunneling

| Service | UDP Support | Notes |
|---------|-------------|-------|
| [Pinggy](https://pinggy.io/blog/ngrok_udp_alternative/) | Yes | CLI + Web App, recommended |
| [LocalXpose](https://localxpose.io/) | Yes | Full protocol support |
| [Localtonet](https://localtonet.com/) | Yes | TCP + UDP + mixed tunnels |
| [Tailscale](https://tailscale.com/) | Yes | VPN-based, any IP protocol |
| [Playit.gg](https://playit.gg/) | Yes | Free tier with UDP tunnels |

### Alternative: TCP/TLS Transport

For syslog specifically, Cisco Catalyst 9300 supports **Syslog over TLS** (TCP port 6514) since IOS-XE 17.2:
- Configuration: `logging host <IP> transport tls profile <PROFILE>`
- Requires certificate setup (PKI)
- Provides confidentiality, integrity, and mutual authentication

This could eliminate the need for UDP tunneling for syslog, but SNMP traps and IPFIX remain UDP-only.

### Recommendation

1. **Primary approach**: Use Pinggy or Tailscale for UDP tunnel support
2. **Backup approach**: Support both UDP and TCP/TLS for syslog receiver
3. Document both approaches in quickstart.md

---

## R5: Cisco Catalyst 9300 Telemetry Configuration

### gNMI (Existing)

Already implemented in gnmi-mcp. Catalyst 9300 supports gNMI with:
- NETCONF-YANG feature (IOS-XE 16.x+)
- Default port: 57400 (Cisco IOS-XE)
- JSON_IETF encoding
- ON_CHANGE subscriptions supported

### Syslog

```
! UDP (default)
logging host <IP> transport udp port 514

! TCP/TLS (IOS-XE 17.2+)
logging host <IP> transport tls profile <PROFILE> port 6514
```

### SNMP Traps

```
snmp-server enable traps
snmp-server host <IP> version 2c <COMMUNITY>
! or SNMPv3
snmp-server host <IP> version 3 auth <USM-USER>
```

### Flexible NetFlow (IPFIX Export)

```
flow record NETCLAW-RECORD
 match ipv4 source address
 match ipv4 destination address
 match transport source-port
 match transport destination-port
 match ipv4 protocol
 collect counter bytes
 collect counter packets

flow exporter NETCLAW-EXPORTER
 destination <IP>
 transport udp 2055
 export-protocol ipfix

flow monitor NETCLAW-MONITOR
 record NETCLAW-RECORD
 exporter NETCLAW-EXPORTER

interface GigabitEthernet1/0/1
 ip flow monitor NETCLAW-MONITOR input
```

---

## R6: Asyncio UDP Server Pattern

### Decision: asyncio.DatagramProtocol with create_datagram_endpoint

### Rationale

Python's asyncio provides native UDP support through `DatagramProtocol`. This pattern allows:
- Non-blocking packet reception
- Integration with FastMCP's async event loop
- Concurrent handling of multiple receivers

### Example Pattern

```python
import asyncio

class UDPReceiverProtocol(asyncio.DatagramProtocol):
    def __init__(self, message_handler):
        self.message_handler = message_handler

    def datagram_received(self, data: bytes, addr: tuple):
        asyncio.create_task(self.message_handler(data, addr))

async def start_receiver(host: str, port: int, handler):
    loop = asyncio.get_event_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPReceiverProtocol(handler),
        local_addr=(host, port)
    )
    return transport
```

This pattern will be used consistently across all three receiver MCP servers.

---

## R7: In-Memory Storage with Deduplication

### Decision: Collections with TTL-based expiration and hash-based dedup

### Rationale

Per clarifications:
- In-memory only (no persistence)
- 24-hour retention (FR-020)
- 5-second deduplication window (FR-022)

### Implementation Approach

```python
from collections import OrderedDict
import hashlib
import time

class MessageStore:
    def __init__(self, retention_hours=24, dedup_window_sec=5):
        self.messages = OrderedDict()  # Ordered by insertion time
        self.dedup_cache = {}  # hash -> timestamp
        self.retention_sec = retention_hours * 3600
        self.dedup_window = dedup_window_sec

    def add(self, message: dict) -> bool:
        # Check dedup
        msg_hash = hashlib.sha256(str(message).encode()).hexdigest()[:16]
        now = time.time()

        if msg_hash in self.dedup_cache:
            if now - self.dedup_cache[msg_hash] < self.dedup_window:
                return False  # Duplicate

        self.dedup_cache[msg_hash] = now
        self.messages[id(message)] = (now, message)
        self._cleanup()
        return True

    def _cleanup(self):
        now = time.time()
        # Remove expired messages
        while self.messages:
            key, (ts, _) = next(iter(self.messages.items()))
            if now - ts > self.retention_sec:
                del self.messages[key]
            else:
                break
        # Clean dedup cache
        self.dedup_cache = {k: v for k, v in self.dedup_cache.items()
                           if now - v < self.dedup_window}
```

---

## R8: Rate Limiting

### Decision: Token bucket algorithm

### Rationale

FR-021 requires rate limiting to prevent receiver overload. Token bucket provides:
- Burst tolerance (important for syslog storms)
- Configurable sustained rate
- Simple implementation

### Implementation

```python
import time

class RateLimiter:
    def __init__(self, rate: float, burst: int):
        self.rate = rate  # messages per second
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()

    def allow(self) -> bool:
        now = time.time()
        self.tokens = min(self.burst,
                         self.tokens + (now - self.last_update) * self.rate)
        self.last_update = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
```

Default configuration: 1000 msg/sec rate, 5000 burst (allows 5-second spikes).

---

## Sources

- [RFC 5424 - The Syslog Protocol](https://datatracker.ietf.org/doc/html/rfc5424)
- [RFC 7011 - IPFIX Protocol Specification](https://datatracker.ietf.org/doc/html/rfc7011)
- [PySNMP 7.1 Documentation](https://docs.lextudio.com/pysnmp/v7.1/)
- [PySNMP GitHub](https://github.com/pysnmp/pysnmp)
- [netflow PyPI Package](https://pypi.org/project/netflow/)
- [netflow GitHub](https://github.com/bitkeks/python-netflow-v9-softflowd)
- [syslog-rfc5424-parser GitHub](https://github.com/EasyPost/syslog-rfc5424-parser)
- [Configuring SYSLOG TLS on Catalyst 9000](https://community.cisco.com/t5/networking-knowledge-base/configuring-syslog-tls-on-catalyst-9000/ta-p/4664499)
- [Pinggy - ngrok UDP Alternative](https://pinggy.io/blog/ngrok_udp_alternative/)
- [LocalXpose - Best ngrok Alternatives](https://localxpose.io/blog/best-ngrok-alternatives)
