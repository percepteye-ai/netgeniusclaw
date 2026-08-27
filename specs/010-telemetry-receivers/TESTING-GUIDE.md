# Telemetry Receivers Testing Guide

## Overview

This guide covers testing the three new telemetry receiver MCP servers with a Cisco Catalyst 9300.

**Receivers:**
| Receiver | Protocol | Default Port | Non-Root Port |
|----------|----------|--------------|---------------|
| syslog-mcp | UDP | 514 | 10514 |
| snmptrap-mcp | UDP | 162 | 10162 |
| ipfix-mcp | UDP | 2055 | 2055 |

> **Note:** Ports below 1024 require root privileges. Use higher ports for testing.

---

## Step 1: Install Dependencies

```bash
# Install syslog-mcp dependencies
cd /home/johncapobianco/netclaw/mcp-servers/syslog-mcp
pip install -r requirements.txt

# Install snmptrap-mcp dependencies
cd /home/johncapobianco/netclaw/mcp-servers/snmptrap-mcp
pip install -r requirements.txt

# Install ipfix-mcp dependencies
cd /home/johncapobianco/netclaw/mcp-servers/ipfix-mcp
pip install -r requirements.txt
```

---

## Step 2: the agent Desktop MCP Configuration

Add these entries to your the agent Desktop MCP settings (`~/.config/agent-code/settings.json` or similar):

```json
{
  "mcpServers": {
    "syslog-mcp": {
      "command": "python",
      "args": ["-m", "syslog_mcp_server"],
      "cwd": "/home/johncapobianco/netclaw/mcp-servers/syslog-mcp",
      "env": {
        "SYSLOG_PORT": "10514",
        "SYSLOG_BIND_ADDRESS": "0.0.0.0"
      }
    },
    "snmptrap-mcp": {
      "command": "python",
      "args": ["-m", "snmptrap_mcp_server"],
      "cwd": "/home/johncapobianco/netclaw/mcp-servers/snmptrap-mcp",
      "env": {
        "SNMPTRAP_PORT": "10162",
        "SNMPTRAP_BIND_ADDRESS": "0.0.0.0"
      }
    },
    "ipfix-mcp": {
      "command": "python",
      "args": ["-m", "ipfix_mcp_server"],
      "cwd": "/home/johncapobianco/netclaw/mcp-servers/ipfix-mcp",
      "env": {
        "IPFIX_PORT": "2055",
        "IPFIX_BIND_ADDRESS": "0.0.0.0"
      }
    }
  }
}
```

**After adding, restart Claude Desktop/Claude Code.**

---

## Step 3: UDP Tunnel Setup (If Router is Remote)

Since ngrok doesn't support UDP, use one of these alternatives:

### Option A: Pinggy (Recommended for Quick Testing)

```bash
# Syslog tunnel
ssh -R 0:localhost:10514 a.pinggy.io

# SNMP trap tunnel (separate terminal)
ssh -R 0:localhost:10162 a.pinggy.io

# NetFlow tunnel (separate terminal)
ssh -R 0:localhost:2055 a.pinggy.io
```

### Option B: Tailscale (Recommended for Persistent Access)

1. Install Tailscale on both your machine and a jump host near the router
2. Use Tailscale IP addresses in router configuration

---

## Step 4: Cisco Catalyst 9300 Configuration

Replace `<NETCLAW_IP>` with your machine's IP (or tunnel endpoint).

### 4.1 Syslog Configuration

```
! Enable syslog to NetGeniusClaw
logging host <NETCLAW_IP> transport udp port 10514
logging trap informational
logging source-interface GigabitEthernet1/0/1
logging on

! Generate test syslog messages
logging buffered 4096
```

### 4.2 SNMP Trap Configuration

```
! SNMPv2c traps
snmp-server community netgeniusclaw RO
snmp-server enable traps
snmp-server enable traps snmp linkdown linkup coldstart warmstart
snmp-server enable traps config
snmp-server host <NETCLAW_IP> version 2c netgeniusclaw udp-port 10162

! Optional: SNMPv3 (more secure)
snmp-server group NETGENIUSCLAW v3 priv
snmp-server user netclawuser NETGENIUSCLAW v3 auth sha AuthPass123 priv aes 128 PrivPass123
snmp-server host <NETCLAW_IP> version 3 priv netclawuser udp-port 10162
snmp-server enable traps
```

### 4.3 NetFlow/IPFIX Configuration

```
! Define flow record
flow record NETCLAW-RECORD
 match ipv4 source address
 match ipv4 destination address
 match transport source-port
 match transport destination-port
 match ipv4 protocol
 collect counter bytes
 collect counter packets

! Define exporter
flow exporter NETCLAW-EXPORTER
 destination <NETCLAW_IP>
 transport udp 2055
 export-protocol ipfix
 template data timeout 60

! Define monitor
flow monitor NETCLAW-MONITOR
 record NETCLAW-RECORD
 exporter NETCLAW-EXPORTER

! Apply to interface (adjust interface name as needed)
interface GigabitEthernet1/0/1
 ip flow monitor NETCLAW-MONITOR input
 ip flow monitor NETCLAW-MONITOR output
```

---

## Step 5: Start Receivers and Test

### 5.1 Start Syslog Receiver

In the agent/NetClaw:
```
Start the syslog receiver on port 10514
```

Or via MCP tool:
```json
{"tool": "syslog_start_receiver", "arguments": {"port": 10514}}
```

### 5.2 Generate Test Syslog Messages

On the Cisco router:
```
! Generate syslog by toggling interface
configure terminal
interface GigabitEthernet1/0/24
 shutdown
 no shutdown
end

! Or generate config change syslog
configure terminal
hostname Cat9300-Test
end
```

### 5.3 Verify Syslog Reception

In the agent/NetClaw:
```
Show the syslog receiver status
Query syslog messages from the last 5 minutes
Show syslog severity counts
```

---

### 5.4 Start SNMP Trap Receiver

In the agent/NetClaw:
```
Start the SNMP trap receiver on port 10162
```

### 5.5 Generate Test SNMP Traps

On the Cisco router:
```
! Generate linkDown/linkUp traps
configure terminal
interface GigabitEthernet1/0/24
 shutdown
 no shutdown
end

! Force a trap
snmp-server enable traps
```

### 5.6 Verify SNMP Trap Reception

In the agent/NetClaw:
```
Show the SNMP trap receiver status
Query SNMP traps received
Show trap counts by type
```

---

### 5.7 Start IPFIX Receiver

In the agent/NetClaw:
```
Start the IPFIX/NetFlow receiver on port 2055
```

### 5.8 Generate Test Flow Data

On the Cisco router, generate traffic:
```
! Ping from router to generate flows
ping 8.8.8.8 repeat 100

! Or SSH to another device through this router
```

### 5.9 Verify IPFIX Reception

In the agent/NetClaw:
```
Show the IPFIX receiver status
Query flow records received
Show top talkers
List cached templates
```

---

## Step 6: Verification Checklist

### Syslog Receiver
- [ ] Receiver started successfully on port 10514
- [ ] Messages received count > 0
- [ ] Can query by severity (ERROR, WARNING, INFO)
- [ ] Can query by source IP
- [ ] Message content is readable (RFC 5424 or 3164 parsed)

### SNMP Trap Receiver
- [ ] Receiver started successfully on port 10162
- [ ] Traps received count > 0
- [ ] linkDown/linkUp traps captured
- [ ] Trap OIDs decoded correctly
- [ ] Variable bindings visible

### IPFIX Receiver
- [ ] Receiver started successfully on port 2055
- [ ] Templates received from exporter
- [ ] Flow records received count > 0
- [ ] Can query by source/destination IP
- [ ] Top talkers shows traffic breakdown

---

## Troubleshooting

### No Messages Received

1. **Check firewall:** Ensure UDP ports are open
   ```bash
   sudo ufw allow 10514/udp
   sudo ufw allow 10162/udp
   sudo ufw allow 2055/udp
   ```

2. **Verify router config:** Check router can reach NetGeniusClaw IP
   ```
   ping <NETCLAW_IP>
   ```

3. **Check receiver status:** Ensure receiver is running
   ```
   Show the syslog/snmptrap/ipfix receiver status
   ```

### Parser Errors

- Check `parse_errors` field in message queries
- Syslog: May fall back to RFC 3164 format
- SNMP: Ensure community string matches
- IPFIX: Templates must be received before data flows

### Rate Limiting

If messages are being dropped:
```
# Increase rate limit via environment variable
SYSLOG_RATE_LIMIT=5000
SNMPTRAP_RATE_LIMIT=5000
IPFIX_RATE_LIMIT=50000
```

---

## Success Criteria for Blog

Document these results:
1. Screenshot of receiver status showing messages received
2. Sample query results from each receiver
3. Router configuration used
4. Any Catalyst 9300-specific notes

Once verified, report back for blog post creation!
