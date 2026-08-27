# NetGeniusClaw 🦞

> *An AI agent that owns your network.*

NetGeniusClaw is a CCIE-level digital coworker built on OpenClaw. It connects to your real network infrastructure through MCP servers, runs Genie-parsed show commands, applies configuration changes safely, audits policy, reconciles your source of truth, and tracks every action in an immutable Git-based audit trail.

**Reach. Grab. Execute.**

---

## What NetGeniusClaw Is

NetGeniusClaw is not a chatbot that talks about networks. It is an agent that **operates** networks.

It holds CCIE R&S #AI-001. It has opinions about your OSPF area design. It will tell you your BGP path selection is wrong and explain the 11-step algorithm. It will not touch a device without a pre-change baseline and a ServiceNow Change Request. It will commit every action to GAIT so there is always an answer to "what did the AI do and why."

---

## Architecture

```
Human ──► NetGeniusClaw (CCIE Agent)
               │
               ├── MCP: pyATS         ─► IOS-XE / NX-OS / IOS-XR devices
               ├── MCP: NetBox        ─► DCIM/IPAM source of truth (read-write)
               ├── MCP: ServiceNow    ─► Incidents, Changes, CMDB
               ├── MCP: GAIT          ─► Git-based AI audit trail
               ├── MCP: Cisco ACI     ─► APIC / ACI fabric
               ├── MCP: Cisco ISE     ─► Identity, posture, TrustSec
               ├── MCP: Wikipedia     ─► Technology context
               ├── MCP: RFC Lookup    ─► IETF standards reference
               ├── MCP: NVD CVE       ─► Vulnerability database
               ├── MCP: Markmap       ─► Mind map visualizations
               └── MCP: Draw.io       ─► Network topology diagrams
```

---

## MCP Servers

| MCP Server | Repository | Function |
|---|---|---|
| pyATS | *(internal)* | Device automation, Genie parsers, config push, dynamic test execution |
| NetBox | `netboxlabs/netbox-mcp-server` | Read-write DCIM/IPAM source of truth |
| ServiceNow | `echelon-ai-labs/servicenow-mcp` | Incidents, change requests, CMDB |
| GAIT | `automateyournetwork/gait_mcp` | Git-based AI tracking and audit |
| Cisco ACI | `automateyournetwork/ACI_MCP` | APIC interaction, policy management, fabric health |
| Cisco ISE | `automateyournetwork/ISE_MCP` | Identity policy, posture, TrustSec, endpoint control |
| Wikipedia | `automateyournetwork/Wikipedia_MCP` | Standards and technology context |
| RFC Lookup | *(internal)* | IETF standards reference |
| NVD CVE | *(internal)* | NIST vulnerability database |
| Markmap | *(internal)* | Hierarchical mind map generation |
| Draw.io | *(internal)* | Network topology diagram generation |

---

## Skills (18)

### pyATS Skills

| Skill | What It Does |
|---|---|
| `pyats-health-check` | 8-step health assessment with threshold-based severity ratings. Cross-references NetBox for expected vs actual interface state. Runs in parallel across all devices in scope via pCall. |
| `pyats-routing` | Deep analysis of OSPF, BGP (full 11-step path selection), EIGRP, IS-IS, and redistribution. |
| `pyats-security` | 9-step CIS-style audit: management plane, AAA, ACLs, CoPP, routing auth, SNMP, encryption. Integrates ISE and NVD CVE. Fleet-wide parallel execution via pCall. |
| `pyats-topology` | CDP/LLDP/ARP/routing peer discovery via pCall across all devices simultaneously. Reconciles against NetBox cables. Outputs Draw.io and Markmap. |
| `pyats-config-mgmt` | 5-phase change workflow. Auto-creates ServiceNow Change Request. GAIT commits at every phase. |
| `pyats-troubleshoot` | Symptom-based OSI layer-by-layer diagnosis. Uses pCall for rapid parallel state collection from all suspect hops. Checks NetBox source of truth during investigation. |
| `pyats-dynamic-test` | Generates and executes deterministic pyATS aetest scripts with embedded TEST_DATA. |
| `pyats-parallel-ops` | Governs multi-device operations at scale. pCall grouping by role/site, failure isolation, result aggregation, severity-sorted fleet reporting. |

### NetBox Skills

| Skill | What It Does |
|---|---|
| `netbox-reconcile` | Diffs NetBox intent vs device reality. Flags IP drift, undocumented links, missing interfaces. Opens ServiceNow incidents. |

### ACI Skills

| Skill | What It Does |
|---|---|
| `aci-fabric-audit` | Fabric health, policy audit (contracts, EPGs, BDs), fault analysis, endpoint learning verification. |
| `aci-change-deploy` | Safe ACI policy change workflow with ServiceNow gating, pre/post fault diff, GAIT audit. |

### ISE Skills

| Skill | What It Does |
|---|---|
| `ise-posture-audit` | Reviews authorization policies, posture compliance, profiling gaps, and TrustSec SGT matrix for over-permissiveness. |
| `ise-incident-response` | Rapid endpoint investigation and quarantine (human-authorized). Opens ServiceNow Security Incident. |

### ITSM Skills

| Skill | What It Does |
|---|---|
| `servicenow-change-workflow` | Full ITSM-gated change: CR creation → approval gate → execution → verification → closure. |

### Audit Skills

| Skill | What It Does |
|---|---|
| `gait-session-tracking` | Mandatory Git-based audit trail. Every session starts with branch creation, ends with audit log display. |

### Reference Skills

| Skill | What It Does |
|---|---|
| `wikipedia-research` | Protocol history, standards evolution, technology context for human teammates. |

---

## Standard Workflows

### Health Check
```
pyats-health-check
→ CPU/memory/interface/BGP/OSPF/log/environmental assessment
→ Cross-reference NetBox for expected interface states
→ Severity ratings: HEALTHY / WARNING / CRITICAL / UNKNOWN
→ GAIT audit trail
```

### Source of Truth Reconciliation
```
netbox-reconcile
→ NetBox intent pull (devices, interfaces, IPs, VLANs, cables)
→ pyATS actual state collection
→ Diff engine: IP_DRIFT / MISSING / UNDOCUMENTED / CABLE_MISMATCH
→ ServiceNow incident per CRITICAL discrepancy
→ Markmap drift summary
→ GAIT commit
```

### Configuration Change
```
servicenow-change-workflow + pyats-config-mgmt
→ Pre-check: no open P1/P2 on affected CIs
→ ServiceNow CR created, approved
→ pyats-config-mgmt: baseline → apply → verify
→ ServiceNow CR closed
→ GAIT full session audit
```

### ACI Policy Change
```
servicenow-change-workflow + aci-change-deploy
→ CR created with tenant/policy scope
→ Fabric baseline (faults, contract counters)
→ APIC change applied
→ Fault delta check
→ CR closed / escalated
→ GAIT full session audit
```

### Security Audit
```
pyats-security
→ Management plane, AAA, ACLs, CoPP, routing auth, SNMP, encryption
→ ISE: verify device registered as NAD
→ NVD CVE: software version vulnerability scan (CVSS ≥ 7.0)
→ Exposure correlation: CVE + running-config
→ GAIT commit
```

### Endpoint Incident Response
```
ise-incident-response
→ Endpoint lookup by MAC/IP/username
→ Auth history, posture, profile review
→ Human decision point
→ [If authorized] ISE quarantine
→ ServiceNow Security Incident
→ GAIT audit trail
```

### Vulnerability Audit
```
pyats-security (CVE module)
→ show version → NVD CVE search
→ CVSS scoring → exposure check vs running-config
→ Prioritized remediation: CRITICAL / HIGH / MEDIUM
→ GAIT commit
```

### Topology Discovery
```
pyats-topology
→ CDP/LLDP/ARP/routing peer collection
→ NetBox cable reconciliation (documented / undocumented / missing)
→ Draw.io diagram (color-coded by reconciliation status)
→ Markmap mind map
→ GAIT commit
```

---

## Safety Model

NetGeniusClaw enforces these non-negotiable constraints:

**Never guesses device state** — runs a show command or queries NetBox first, always.

**Never touches a device without a baseline** — pre-change state is captured and committed to GAIT before any config push.

**Never skips the Change Request** — ServiceNow CR must exist and be in `Approved` state before execution (except Emergency changes, which require immediate human notification).

**Never runs destructive commands** — `write erase`, `erase`, `reload`, `delete`, `format` are refused.

**Never auto-quarantines an endpoint** — ISE endpoint group modification always requires explicit human confirmation.

**NetBox is read-write** — NetGeniusClaw has full API access to create and update NetBox objects. During reconciliation, discrepancies are reported and ticketed first. Updates to NetBox require explicit human authorization.

**Always verifies after changes** — if post-change verification fails, the Change Request is not closed and the human is notified.

**Always commits to GAIT** — every session ends with `gait_show` so the human can see the full audit trail.

---

## GAIT Audit Trail

Every NetGeniusClaw session produces an immutable Git-based record of:
- What was asked
- What data was collected (and from where)
- What was analyzed (and what conclusions were reached)
- What was changed (and on what device)
- What the verification result was
- What ServiceNow tickets were created or updated

This is not optional. It is how NetGeniusClaw earns trust in production environments.

---

## Expertise

NetGeniusClaw holds CCIE-level depth across:

- **Routing:** OSPF, BGP, IS-IS, EIGRP, redistribution, policy routing
- **Switching:** STP variants, VLANs, EtherChannel, VTP, port security
- **MPLS:** LDP, RSVP-TE, L3VPN, L2VPN
- **Overlay:** VXLAN/EVPN, DMVPN, FlexVPN, GRE/IPsec, LISP
- **ACI/SDN:** Tenant/VRF/BD/EPG/Contract model, fabric underlay, APIC REST
- **Identity:** ISE 802.1X, MAB, TrustSec SGT/SGACL, posture, profiling
- **Security:** AAA, CoPP, uRPF, first-hop security, MACsec, SNMP hardening
- **Automation:** pyATS/Genie, YANG/NETCONF/RESTCONF, MCP orchestration

---

## Missions

| Mission | Status | Summary |
|---|---|---|
| MISSION01 | ✅ Complete | Core pyATS agent, 7 skills, Markmap, Draw.io, RFC, NVD CVE, SOUL v1 |
| MISSION02 | 🟡 Active | NetBox, ServiceNow, GAIT, ACI, ISE, Wikipedia — 6 new MCPs, 7 new skills, 4 enhanced skills, SOUL v2 |

---

## Repository Structure

```
netgeniusclaw/
├── README.md
├── SOUL.md               ← System prompt (load into your agent)
├── MISSION01.md          ← Completed
├── MISSION02.md          ← Active
├── skills/               ← Skill procedure documents
│   ├── pyats-*.md
│   ├── netbox-reconcile.md
│   ├── aci-*.md
│   ├── ise-*.md
│   ├── servicenow-change-workflow.md
│   └── gait-session-tracking.md
└── tools/                ← MCP server reference docs
    ├── pyats-mcp.md
    ├── netbox-mcp.md
    ├── servicenow-mcp.md
    ├── gait-mcp.md
    ├── aci-mcp.md
    ├── ise-mcp.md
    ├── wikipedia-mcp.md
    ├── rfc-lookup.md
    ├── nvd-cve.md
    ├── markmap.md
    └── drawio.md
```

---

*NetGeniusClaw — CCIE R&S #AI-001 — Reach. Grab. Execute.*

