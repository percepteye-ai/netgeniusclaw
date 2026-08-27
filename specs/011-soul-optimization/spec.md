# Feature Specification: SOUL.md Modular Optimization

**Feature Branch**: `011-soul-optimization`
**Created**: 2026-04-02
**Status**: Draft
**Input**: User description: "Optimize NetGeniusClaw SOUL.md from 59k to under 20k chars. Options: 1) Split into parent SOUL.md + reference files, 2) Compress without losing functionality, 3) Hybrid approach. Must preserve all 97 skills, GAIT workflow, and CCIE expertise."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Agent Bootstrapping (Priority: P1)

When OpenClaw starts a session, NetGeniusClaw must receive its complete identity, personality, rules, and workflow instructions within the 20,000 character bootstrap limit so that the agent operates correctly from the first message.

**Why this priority**: Without successful bootstrapping, NetGeniusClaw cannot function at all. The truncation warning indicates the agent is currently missing critical instructions.

**Independent Test**: Start a fresh NetGeniusClaw session and verify the agent responds with correct identity, follows GAIT workflow, and knows its rules without any truncation warnings.

**Acceptance Scenarios**:

1. **Given** OpenClaw starts a NetGeniusClaw session, **When** the bootstrap injects SOUL.md, **Then** no truncation warning appears in logs
2. **Given** a bootstrapped session, **When** the user asks "who are you?", **Then** NetGeniusClaw responds with CCIE identity and coworker personality
3. **Given** a bootstrapped session, **When** the user requests a network change, **Then** NetGeniusClaw follows the GAIT and ServiceNow CR workflow without needing to read additional files

---

### User Story 2 - On-Demand Skill Reference (Priority: P2)

When NetGeniusClaw needs detailed instructions for a specific skill (e.g., pyats-health-check, f5-troubleshoot), it can load the relevant reference file to get complete operational procedures without bloating the bootstrap context.

**Why this priority**: Skills are used selectively per session. Loading all 97 skill details upfront wastes context; loading on-demand preserves context for actual work.

**Independent Test**: Ask NetGeniusClaw to perform a pyATS health check and verify it loads the skill reference, follows the documented procedure, and completes successfully.

**Acceptance Scenarios**:

1. **Given** a bootstrapped session, **When** NetGeniusClaw needs to use the pyats-health-check skill, **Then** it reads the skills reference file and follows the 8-step procedure
2. **Given** a bootstrapped session, **When** NetGeniusClaw uses multiple skills in one session, **Then** it loads each skill's details only when needed
3. **Given** the skill reference file is unavailable, **When** NetGeniusClaw attempts to load it, **Then** it falls back to the condensed skill summary in SOUL.md

---

### User Story 3 - Expertise Knowledge Access (Priority: P3)

When NetGeniusClaw needs to explain protocol behavior or apply CCIE-level knowledge (e.g., BGP path selection, OSPF LSA types), it can reference the expertise documentation to provide accurate technical details.

**Why this priority**: Deep technical knowledge is needed for troubleshooting and education but not for every interaction. On-demand loading keeps bootstrap lean.

**Independent Test**: Ask NetGeniusClaw to explain BGP path selection and verify it provides the complete 11-step algorithm with correct details.

**Acceptance Scenarios**:

1. **Given** a user asks about OSPF area types, **When** NetGeniusClaw responds, **Then** it provides accurate CCIE-level detail (stub, NSSA, totally stubby)
2. **Given** a user asks about BGP communities, **When** NetGeniusClaw responds, **Then** it explains standard, extended, and large communities correctly
3. **Given** the expertise reference is unavailable, **When** NetGeniusClaw needs technical details, **Then** it provides reasonable answers from general knowledge

---

### Edge Cases

- What happens when a reference file is missing or corrupted?
- How does NetGeniusClaw handle requests that span multiple reference files?
- What if the user session exhausts context before loading needed references?
- How does NetGeniusClaw prioritize which reference to load when multiple apply?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: SOUL.md MUST be under 20,000 characters to avoid OpenClaw bootstrap truncation
- **FR-002**: SOUL.md MUST contain complete identity, personality, rules, and core workflows inline (no external references for critical behavior)
- **FR-003**: SOUL.md MUST contain a condensed skill index with skill names and one-line descriptions for all 97 skills
- **FR-004**: System MUST provide reference files for detailed skill procedures, loadable on-demand via the read tool
- **FR-005**: System MUST provide reference files for CCIE expertise knowledge, loadable on-demand
- **FR-006**: SOUL.md MUST instruct NetGeniusClaw how and when to load reference files
- **FR-007**: Reference files MUST be organized by category for efficient loading (skills by domain, expertise by topic)
- **FR-008**: All content from the original 59k SOUL.md MUST be preserved across the modular file structure (no functionality loss)
- **FR-009**: GAIT workflow instructions MUST remain in SOUL.md (not externalized) as they apply to every session
- **FR-010**: ServiceNow change management workflow MUST remain in SOUL.md as it gates all configuration changes

### Key Entities

- **SOUL.md**: The core bootstrap file injected into every session context. Contains identity, condensed skills, core workflows, personality, and rules.
- **Skills Reference Files**: Detailed operational procedures organized by skill category (e.g., `SKILLS-PYATS.md`, `SKILLS-CLOUD.md`, `SKILLS-OBSERVABILITY.md`)
- **Expertise Reference File**: CCIE-level technical knowledge (`EXPERTISE.md`) covering routing protocols, switching, security, and automation

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: SOUL.md character count is under 20,000 (target: 15,000-18,000 for headroom)
- **SC-002**: Zero truncation warnings appear in OpenClaw logs during NetGeniusClaw session bootstrap
- **SC-003**: NetGeniusClaw correctly identifies as CCIE #AI-001 coworker in first response of any session
- **SC-004**: NetGeniusClaw follows GAIT workflow (branch creation, turn recording, audit log) without loading external files
- **SC-005**: NetGeniusClaw can execute any of the 97 skills after loading the appropriate reference file
- **SC-006**: 100% of original SOUL.md content is preserved across the modular file structure
- **SC-007**: Reference file loading adds less than 5 seconds to skill execution workflows

## Assumptions

- OpenClaw's read tool can load reference files from the workspace directory (~/.openclaw/workspace/)
- Reference files are loaded into the session context and persist for the duration of the session
- OpenClaw's 20,000 character limit applies only to the bootstrap file (SOUL.md), not to files loaded during the session
- The existing SOUL.md structure and content are correct and should be preserved, just reorganized
- Skills are used selectively (typically 2-5 per session), making on-demand loading more efficient than upfront loading
- The OpenClaw workspace directory structure supports subdirectories for organizing reference files
