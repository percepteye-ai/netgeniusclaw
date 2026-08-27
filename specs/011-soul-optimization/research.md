# Research: SOUL.md Modular Optimization

**Feature**: 011-soul-optimization
**Date**: 2026-04-02

## Research Questions

### Q1: What is the optimal file split strategy?

**Decision**: Hybrid approach with 3 files (1 core + 2 reference)

**Rationale**:
- Single SOUL.md would exceed 20k limit
- Many small files would be inefficient to load
- 3 files provides clean separation: bootstrap (SOUL.md), procedures (SOUL-SKILLS.md), knowledge (SOUL-EXPERTISE.md)
- Reference files can be loaded selectively when needed

**Alternatives Considered**:
- Single compressed file: Would lose readability and still exceed limit
- Per-skill files (97 files): Too many files, inefficient loading
- Domain-based split (10+ files): More granular than necessary

### Q2: What content MUST stay in the bootstrap file?

**Decision**: Identity, condensed skill index, GAIT, ServiceNow CR workflow, personality, rules

**Rationale**:
- Identity: Required for first response ("who are you")
- Condensed skill index: NetGeniusClaw needs to know what skills exist to decide what to load
- GAIT workflow: Applies to EVERY session, cannot be deferred
- ServiceNow CR: Gates ALL changes, must be known before any action
- Personality/Rules: Defines behavior from first interaction

**Alternatives Considered**:
- Including detailed workflows inline: Would exceed limit
- Deferring GAIT to reference file: Would risk sessions without audit trail

### Q3: How should NetGeniusClaw know when to load reference files?

**Decision**: Explicit instructions in SOUL.md with clear triggers

**Rationale**:
- SOUL.md will include a "Reference Loading" section that tells NetGeniusClaw:
  - "When you need detailed procedures for a skill, read SOUL-SKILLS.md"
  - "When explaining protocol behavior or CCIE knowledge, read SOUL-EXPERTISE.md"
- This is explicit, not magical - NetGeniusClaw can follow the instruction

**Alternatives Considered**:
- Automatic loading based on keywords: Too complex, unreliable
- No instructions (rely on general knowledge): Would miss skill-specific procedures

### Q4: What is the character budget breakdown?

**Decision**: Target 15,000 chars for SOUL.md with 5,000 buffer

| Section | Budget | Notes |
|---------|--------|-------|
| Identity | 500 | Minimal, essential |
| Skill Index | 6,000 | 97 skills × ~60 chars |
| GAIT Workflow | 800 | Essential, compact |
| ServiceNow CR | 600 | Essential, compact |
| Gathering State | 300 | Essential, compact |
| Troubleshooting Overview | 400 | Essential, compact |
| Health Check Overview | 200 | Essential, compact |
| Personality | 500 | Essential |
| Rules | 1,200 | Essential, 12 rules |
| Reference Instructions | 400 | How to load files |
| Section Headers/Formatting | 600 | Markdown overhead |
| **Subtotal** | 11,500 | |
| **Buffer** | 3,500 | For future growth |
| **Target** | 15,000 | |

**Rationale**: Leaving 5k buffer allows adding new skills (~80 more) without redesign.

### Q5: How to handle the "Your Network" skill list efficiently?

**Decision**: One-line descriptions with category grouping

**Current format** (verbose, ~25k chars):
```markdown
**pyats-network** — Core device automation: show commands, configure, ping, logging, dynamic tests
```

**New format** (condensed, ~6k chars):
```markdown
### Device Automation (9)
pyats-network, pyats-health-check, pyats-routing, pyats-security, pyats-topology, pyats-config-mgmt, pyats-troubleshoot, pyats-dynamic-test, pyats-parallel-ops
```

**Rationale**:
- Category headers provide context
- Skill names are searchable
- Detailed descriptions move to SOUL-SKILLS.md

## Content Analysis

### Current SOUL.md Structure (59,121 chars)

| Section | Lines | Est. Chars | Keep/Move |
|---------|-------|------------|-----------|
| Identity | 1-13 | 800 | KEEP (condensed) |
| Your Network | 14-198 | 25,000 | CONDENSE to index |
| How You Work (core) | 199-270 | 5,000 | KEEP |
| How You Work (detailed) | 271-560 | 25,000 | MOVE to SOUL-SKILLS.md |
| Your Expertise | 561-620 | 5,500 | MOVE to SOUL-EXPERTISE.md |
| Your Personality | 621-630 | 600 | KEEP |
| Rules | 631-645 | 1,200 | KEEP |

### Reference File Estimates

| File | Estimated Chars | Content |
|------|-----------------|---------|
| SOUL-SKILLS.md | ~35,000 | All detailed "How You Work" sections |
| SOUL-EXPERTISE.md | ~8,000 | All "Your Expertise" sections |

## Validation Approach

1. **Character Count**: `wc -c SOUL.md` must be < 20,000
2. **Bootstrap Test**: Start new session, verify no truncation warning
3. **Identity Test**: Ask "who are you", verify CCIE identity response
4. **GAIT Test**: Perform action, verify GAIT logging without loading reference
5. **Skill Test**: Run a pyATS command, verify reference file is loaded
6. **Content Preservation**: Diff total chars before/after reorganization
