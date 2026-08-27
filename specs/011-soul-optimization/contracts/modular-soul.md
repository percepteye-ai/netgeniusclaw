# Contract: Modular SOUL Architecture

**Feature**: 011-soul-optimization
**Date**: 2026-04-02
**Type**: File Structure Contract

## Overview

This contract defines the structure and relationships between the modular SOUL files used for NetGeniusClaw agent bootstrapping.

## File Locations

All SOUL files reside in the OpenClaw workspace directory:

```
~/.openclaw/workspace/
├── SOUL.md              # Core bootstrap (REQUIRED)
├── SOUL-SKILLS.md       # Skill procedures (OPTIONAL, loaded on-demand)
└── SOUL-EXPERTISE.md    # Technical knowledge (OPTIONAL, loaded on-demand)
```

## SOUL.md Contract

### Required Sections

| Section | Purpose | Max Chars |
|---------|---------|-----------|
| `# NetGeniusClaw: ...` | Title and identity | 100 |
| `## Identity` | Who NetGeniusClaw is | 500 |
| `## Your Skills` | Condensed skill index | 6,000 |
| `## How You Work` | Core workflows | 2,000 |
| `## Your Personality` | Behavioral traits | 500 |
| `## Rules` | Non-negotiable rules | 1,200 |

### Required Subsections under "How You Work"

| Subsection | Purpose |
|------------|---------|
| `### GAIT: Always-On Audit Trail` | Branch/record/log workflow |
| `### Gathering State` | Observe before acting |
| `### Applying Changes` | ServiceNow CR workflow |
| `### Loading Reference Files` | When/how to load references |

### Character Limit

- **Hard limit**: 20,000 characters
- **Target**: 15,000-18,000 characters
- **Measurement**: `wc -c ~/.openclaw/workspace/SOUL.md`

### Reference Loading Instruction Format

The "Loading Reference Files" section MUST include:

```markdown
### Loading Reference Files

When you need detailed procedures for any skill, read `SOUL-SKILLS.md`.
When explaining protocol behavior or applying CCIE-level technical knowledge, read `SOUL-EXPERTISE.md`.

Use the read tool: `read("~/.openclaw/workspace/SOUL-SKILLS.md")` or `read("~/.openclaw/workspace/SOUL-EXPERTISE.md")`
```

## SOUL-SKILLS.md Contract

### Required Structure

```markdown
# NetGeniusClaw Skill Procedures Reference

> Load this file when you need detailed operational procedures for any skill.
> This is a reference document - core workflows are in SOUL.md.

## [Category Name] Skills

### [skill-name]

[Detailed procedures, commands, workflows, best practices]

---

[Repeat for all skills]
```

### Content Requirements

- All 97 skills MUST have detailed procedures
- Skills MUST be grouped by category (matching SOUL.md index)
- Each skill section MUST include specific commands/tools to use
- Procedures MUST be actionable (not just descriptions)

## SOUL-EXPERTISE.md Contract

### Required Structure

```markdown
# NetGeniusClaw Technical Expertise Reference

> Load this file when explaining protocol behavior or applying CCIE-level knowledge.
> This is a reference document for technical facts and best practices.

## [Technology Domain]

### [Protocol/Technology]

[Technical details, algorithms, best practices, parameters]

---

[Repeat for all domains]
```

### Content Requirements

- All CCIE-level knowledge from original SOUL.md MUST be preserved
- Organized by technology domain (Routing, Switching, Security, etc.)
- Factual and reference-oriented (not operational procedures)

## Validation Contract

| Check | Expected Result |
|-------|-----------------|
| `wc -c SOUL.md` | < 20,000 |
| OpenClaw bootstrap | No truncation warning |
| "Who are you?" test | CCIE #AI-001 identity |
| GAIT test | Logging without loading references |
| Skill execution | References load correctly |
| `wc -c SOUL*.md | sum` | ≈ 59,121 (original content) |

## Backwards Compatibility

- NetGeniusClaw MUST function correctly if reference files are missing
- Missing reference: Fall back to condensed info in SOUL.md
- This is degraded mode, not failure mode
