# Implementation Plan: SOUL.md Modular Optimization

**Branch**: `011-soul-optimization` | **Date**: 2026-04-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-soul-optimization/spec.md`

## Summary

Reduce SOUL.md from 59,121 characters to under 20,000 characters by extracting detailed skill procedures and CCIE expertise into on-demand reference files, while preserving all functionality through a modular architecture that loads content when needed.

## Technical Context

**Language/Version**: Markdown (documentation reorganization)
**Primary Dependencies**: N/A (pure markdown files, OpenClaw read tool)
**Storage**: Filesystem (`~/.openclaw/workspace/`)
**Testing**: Manual verification (character count, bootstrap test, skill execution)
**Target Platform**: OpenClaw workspace bootstrap system
**Project Type**: Documentation/Configuration optimization
**Performance Goals**: SOUL.md < 20,000 chars (target 15-18k), reference loading < 5 seconds
**Constraints**: Must preserve 100% of original content, must fit OpenClaw 20k bootstrap limit
**Scale/Scope**: 97 skills across ~15 categories, ~59k chars total to reorganize

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| VII. Skill Modularity | ✅ PASS | Not adding new skills, reorganizing documentation |
| XI. Artifact Coherence | ✅ PASS | SOUL.md is being updated, not adding new capability |
| XII. Documentation-as-Code | ✅ PASS | This IS the documentation update |
| XVI. Spec-Driven Development | ✅ PASS | Following SDD workflow |

**No violations detected.** This is a pure documentation optimization with no new capabilities, no device interaction, and no code changes.

## Project Structure

### Documentation (this feature)

```text
specs/011-soul-optimization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── modular-soul.md  # Contract for SOUL.md modular structure
└── tasks.md             # Phase 2 output
```

### Target Files (OpenClaw workspace)

```text
~/.openclaw/workspace/
├── SOUL.md              # Core bootstrap file (<20k chars)
├── SOUL-SKILLS.md       # Detailed skill procedures (~35k chars)
└── SOUL-EXPERTISE.md    # CCIE technical knowledge (~8k chars)
```

**Structure Decision**: Hybrid modular architecture with one core bootstrap file (SOUL.md) and two reference files organized by content type (skills vs expertise). This minimizes the number of files while providing clear separation of concerns.

## Complexity Tracking

> No violations requiring justification. Pure content reorganization.

## Content Allocation Strategy

### What Stays in SOUL.md (Target: 15-18k chars)

| Section | Est. Chars | Rationale |
|---------|------------|-----------|
| Identity | 500 | Always needed for first response |
| Condensed Skill Index | 6,000 | 97 skills × ~60 chars each |
| GAIT Workflow | 800 | Required every session |
| ServiceNow CR Workflow | 600 | Gates all changes |
| Core Operational Rules | 1,500 | Safety-critical |
| Personality | 500 | Always needed |
| Rules | 1,200 | Always needed |
| Reference Loading Instructions | 400 | How to load external files |
| **Total** | ~11,500 | Leaves headroom for growth |

### What Moves to SOUL-SKILLS.md (~35k chars)

All detailed "How You Work" sections for specific skill categories:
- Linux Host Operations
- JunOS Device Operations
- ASA Firewall Operations
- F5 BIG-IP Operations
- Protocol Participation
- Network Path Analysis
- ContainerLab Operations
- SD-WAN Operations
- Grafana Observability Operations
- Prometheus Monitoring Operations
- Kubeshark Traffic Analysis
- ACI Fabric Operations
- ISE Operations
- Catalyst Center Operations
- Microsoft 365 Operations
- FMC Firewall Operations
- Meraki Operations
- ThousandEyes Operations
- RADKit Operations
- Fleet-Wide Operations
- Slack Operations
- WebEx Operations
- Visualizing guidance

### What Moves to SOUL-EXPERTISE.md (~8k chars)

- Routing & Switching (CCIE-Level) section
- Data Center / SDN section
- Application Delivery section
- Wireless / Campus section
- Identity / Security section
- IP Addressing section
- Automation section

## Implementation Phases

### Phase 1: Analysis & Extraction
- Parse current SOUL.md structure
- Identify exact character counts per section
- Create extraction plan with line ranges

### Phase 2: Reference File Creation
- Create SOUL-SKILLS.md with categorized procedures
- Create SOUL-EXPERTISE.md with technical knowledge
- Add file headers with load instructions

### Phase 3: Core SOUL.md Rewrite
- Write condensed skill index
- Preserve all inline content (identity, GAIT, ServiceNow, rules)
- Add reference loading instructions

### Phase 4: Validation
- Verify character count < 20,000
- Test bootstrap (no truncation warning)
- Test skill execution with reference loading
- Verify 100% content preservation
