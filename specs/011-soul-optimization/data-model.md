# Data Model: SOUL.md Modular Architecture

**Feature**: 011-soul-optimization
**Date**: 2026-04-02

## Entities

### SOUL.md (Core Bootstrap File)

**Purpose**: Injected into every OpenClaw session context at startup

**Constraints**:
- Maximum 20,000 characters (hard limit from OpenClaw)
- Target 15,000-18,000 characters (with growth buffer)
- Must be self-contained for basic operations

**Structure**:
```
# NetGeniusClaw: CCIE-Level Digital Coworker

## Identity
[~500 chars - who NetGeniusClaw is, CCIE #AI-001]

## Your Skills
[~6,000 chars - condensed index of 97 skills by category]

## How You Work

### GAIT: Always-On Audit Trail
[~800 chars - branch/record/log workflow]

### Gathering State
[~300 chars - always observe before acting]

### Applying Changes
[~600 chars - ServiceNow CR workflow]

### Loading Reference Files
[~400 chars - when/how to load SOUL-SKILLS.md and SOUL-EXPERTISE.md]

## Your Personality
[~500 chars - direct, technical, safety-conscious]

## Rules
[~1,200 chars - 12 non-negotiable rules]
```

**Relationships**:
- References → SOUL-SKILLS.md (on-demand)
- References → SOUL-EXPERTISE.md (on-demand)

---

### SOUL-SKILLS.md (Detailed Procedures Reference)

**Purpose**: Loaded on-demand when NetGeniusClaw needs detailed operational procedures

**Constraints**:
- No character limit (not part of bootstrap)
- Should be organized for efficient partial loading if needed
- Must cover all 97 skills with complete procedures

**Structure**:
```
# NetGeniusClaw Skill Procedures Reference

## Device Automation Skills
### pyats-network
[detailed procedures]
### pyats-health-check
[8-step assessment procedure]
...

## Linux Host Skills
...

## JunOS Skills
...

## Cloud Skills
...

[continues for all skill categories]
```

**Content Sections**:
- Device Automation (9 skills)
- Linux Host Operations (3 skills)
- JunOS Operations (3 skills)
- ASA Firewall Operations (1 skill)
- F5 BIG-IP Operations (2 skills)
- Domain Skills (9 skills)
- Cloud Skills (AWS 5, GCP 3, Azure 2)
- Observability Skills (Grafana, Prometheus, Kubeshark)
- Cisco Platform Skills (CML, SD-WAN, Meraki, Catalyst Center, FMC, NSO, RADKit)
- Integration Skills (GitHub, Slack, WebEx, Microsoft 365)
- Security Skills (nmap, ISE, firewall analysis)
- Reference Skills (NVD, subnet calculator, RFC lookup, Wikipedia)
- Visualization Skills (Markmap, Draw.io, UML)

---

### SOUL-EXPERTISE.md (Technical Knowledge Reference)

**Purpose**: Loaded on-demand when NetGeniusClaw needs CCIE-level technical details

**Constraints**:
- No character limit
- Organized by technology domain
- Factual reference, not operational procedures

**Structure**:
```
# NetGeniusClaw Technical Expertise Reference

## Routing & Switching

### OSPF
[Area types, LSA types, DR/BDR election, SPF, authentication, etc.]

### BGP
[Path selection algorithm, route reflectors, communities, etc.]

### IS-IS
[Levels, NET addressing, wide metrics, etc.]

### EIGRP
[DUAL, feasibility condition, variance, etc.]

### Switching
[STP variants, VLANs, trunking, EtherChannel, etc.]

### MPLS
[LDP, RSVP-TE, L3VPN, L2VPN, TE, etc.]

### Overlay
[VXLAN, EVPN, LISP, DMVPN, etc.]

### FHRP
[HSRP, VRRP, GLBP]

## Data Center / SDN
[ACI model, fabric underlay, etc.]

## Application Delivery
[F5 concepts, virtual servers, pools, etc.]

## Wireless / Campus
[Catalyst Center concepts, client health, etc.]

## Identity / Security
[ISE, 802.1X, TrustSec, AAA, etc.]

## IP Addressing
[IPv4 subnetting, IPv6 address types, etc.]

## Automation
[pyATS, YANG, NETCONF, etc.]
```

## File Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaw Bootstrap                        │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    SOUL.md                           │   │
│  │               (< 20,000 chars)                       │   │
│  │                                                      │   │
│  │  • Identity                                          │   │
│  │  • Condensed Skill Index                            │   │
│  │  • GAIT Workflow                                     │   │
│  │  • ServiceNow CR Workflow                           │   │
│  │  • Personality & Rules                              │   │
│  │  • Reference Loading Instructions                   │   │
│  └──────────────────┬────────────────┬─────────────────┘   │
│                     │                │                       │
│         ┌───────────▼───────┐   ┌───▼───────────────┐      │
│         │  SOUL-SKILLS.md   │   │ SOUL-EXPERTISE.md │      │
│         │   (~35,000 chars) │   │   (~8,000 chars)  │      │
│         │                   │   │                   │      │
│         │ Detailed skill    │   │ CCIE technical    │      │
│         │ procedures        │   │ knowledge         │      │
│         │ (loaded on-demand)│   │ (loaded on-demand)│      │
│         └───────────────────┘   └───────────────────┘      │
│                                                              │
│                    On-Demand via read tool                  │
└─────────────────────────────────────────────────────────────┘
```

## State Transitions

N/A - These are static documentation files, not stateful entities.

## Validation Rules

| Rule | File | Validation |
|------|------|------------|
| Character limit | SOUL.md | `wc -c` < 20,000 |
| Content preservation | All 3 files | Combined chars ≈ 59,121 (original) |
| Skill coverage | SOUL.md + SOUL-SKILLS.md | All 97 skills documented |
| No truncation | SOUL.md | OpenClaw logs show no warning |
| Reference loadable | SOUL-*.md | Can be read via OpenClaw read tool |
