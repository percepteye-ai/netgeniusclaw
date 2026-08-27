# Tasks: SOUL.md Modular Optimization

**Input**: Design documents from `/specs/011-soul-optimization/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/modular-soul.md, quickstart.md

**Tests**: Manual verification only (no automated tests - this is a documentation reorganization task)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

All target files reside in the OpenClaw workspace:
- `~/.openclaw/workspace/SOUL.md` - Core bootstrap file
- `~/.openclaw/workspace/SOUL-SKILLS.md` - Skill procedures reference
- `~/.openclaw/workspace/SOUL-EXPERTISE.md` - Technical expertise reference

---

## Phase 1: Setup (Backup & Analysis)

**Purpose**: Create backup and analyze current SOUL.md structure

- [x] T001 Backup current SOUL.md to ~/.openclaw/workspace/SOUL.md.backup
- [x] T002 Analyze current SOUL.md structure and identify section line ranges
- [x] T003 Verify current character count matches expected ~59,121 chars

**Checkpoint**: Original SOUL.md safely backed up and structure documented

---

## Phase 2: Foundational (Content Extraction Planning)

**Purpose**: Plan exact content extraction before creating any new files

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Document exact line ranges for "Your Expertise" section to move to SOUL-EXPERTISE.md
- [x] T005 Document exact line ranges for detailed "How You Work" skill procedures to move to SOUL-SKILLS.md
- [x] T006 Document exact line ranges for content to KEEP in SOUL.md (identity, GAIT, ServiceNow CR, rules, personality)
- [x] T007 Create condensed skill index text (97 skills grouped by category, ~60 chars each)

**Checkpoint**: Extraction plan ready - content movement can begin

---

## Phase 3: User Story 1 - Core Agent Bootstrapping (Priority: P1) MVP

**Goal**: Create SOUL.md that bootstraps NetGeniusClaw within 20k character limit with all core workflows inline

**Independent Test**: Start a fresh NetGeniusClaw session, verify identity response, GAIT workflow, and no truncation warning

### Implementation for User Story 1

- [x] T008 [US1] Create new SOUL.md with Identity section (~500 chars) at ~/.openclaw/workspace/SOUL.md
- [x] T009 [US1] Add condensed "Your Skills" section with 97 skills indexed by category (~6,000 chars)
- [x] T010 [US1] Add "How You Work" section with GAIT workflow subsection (~800 chars)
- [x] T011 [US1] Add "Gathering State" subsection under "How You Work" (~300 chars)
- [x] T012 [US1] Add "Applying Changes" subsection with ServiceNow CR workflow (~600 chars)
- [x] T013 [US1] Add "Loading Reference Files" subsection with instructions for SOUL-SKILLS.md and SOUL-EXPERTISE.md (~400 chars)
- [x] T014 [US1] Add "Your Personality" section (~500 chars)
- [x] T015 [US1] Add "Rules" section with all 12 non-negotiable rules (~1,200 chars)
- [x] T016 [US1] Verify SOUL.md character count is under 20,000 (target 15,000-18,000)
- [ ] T017 [US1] Test bootstrap by starting new NetGeniusClaw session - verify no truncation warning (MANUAL TEST)
- [ ] T018 [US1] Test identity by asking "who are you?" - verify CCIE #AI-001 response (MANUAL TEST)
- [ ] T019 [US1] Test GAIT workflow by requesting a change - verify branch/record/log without loading references (MANUAL TEST)

**Checkpoint**: User Story 1 complete - NetGeniusClaw bootstraps correctly within character limit

---

## Phase 4: User Story 2 - On-Demand Skill Reference (Priority: P2)

**Goal**: Create SOUL-SKILLS.md with detailed procedures for all 97 skills, loadable on-demand

**Independent Test**: Ask NetGeniusClaw to run pyATS health check, verify it loads SOUL-SKILLS.md and follows documented procedure

### Implementation for User Story 2

- [x] T020 [US2] Create SOUL-SKILLS.md with file header and load instructions at ~/.openclaw/workspace/SOUL-SKILLS.md
- [x] T021 [P] [US2] Add Device Automation Skills section (9 skills: pyats-network, pyats-health-check, etc.)
- [x] T022 [P] [US2] Add Linux Host Operations section (3 skills)
- [x] T023 [P] [US2] Add JunOS Device Operations section (3 skills)
- [x] T024 [P] [US2] Add ASA Firewall Operations section (1 skill)
- [x] T025 [P] [US2] Add F5 BIG-IP Operations section (2 skills)
- [x] T026 [P] [US2] Add Domain Skills section (9 skills: netbox, nautobot, infrahub, etc.)
- [x] T027 [P] [US2] Add Cloud Skills section (AWS 5, GCP 3, Azure 2 = 10 skills)
- [x] T028 [P] [US2] Add Observability Skills section (Grafana, Prometheus, Kubeshark)
- [x] T029 [P] [US2] Add Cisco Platform Skills section (CML, SD-WAN, Meraki, Catalyst Center, FMC, NSO, RADKit)
- [x] T030 [P] [US2] Add Integration Skills section (GitHub, Slack, WebEx, Microsoft 365)
- [x] T031 [P] [US2] Add Security Skills section (nmap, ISE, firewall analysis)
- [x] T032 [P] [US2] Add Reference Skills section (NVD, subnet calculator, RFC lookup, Wikipedia)
- [x] T033 [P] [US2] Add Visualization Skills section (Markmap, Draw.io, UML)
- [x] T034 [US2] Verify all 97 skills have detailed procedures documented
- [ ] T035 [US2] Test skill loading by asking NetGeniusClaw to run pyATS health check - verify reference loads (MANUAL TEST)
- [ ] T036 [US2] Test fallback behavior when SOUL-SKILLS.md is renamed/unavailable (MANUAL TEST)

**Checkpoint**: User Story 2 complete - Skills reference loads on-demand and works correctly

---

## Phase 5: User Story 3 - Expertise Knowledge Access (Priority: P3)

**Goal**: Create SOUL-EXPERTISE.md with CCIE-level technical knowledge, loadable on-demand

**Independent Test**: Ask NetGeniusClaw to explain BGP path selection, verify it provides complete 11-step algorithm

### Implementation for User Story 3

- [x] T037 [US3] Create SOUL-EXPERTISE.md with file header and load instructions at ~/.openclaw/workspace/SOUL-EXPERTISE.md
- [x] T038 [P] [US3] Add Routing & Switching section (OSPF, BGP, IS-IS, EIGRP, Switching, MPLS, Overlay, FHRP)
- [x] T039 [P] [US3] Add Data Center / SDN section (ACI model, fabric underlay)
- [x] T040 [P] [US3] Add Application Delivery section (F5 concepts, virtual servers, pools)
- [x] T041 [P] [US3] Add Wireless / Campus section (Catalyst Center concepts, client health)
- [x] T042 [P] [US3] Add Identity / Security section (ISE, 802.1X, TrustSec, AAA)
- [x] T043 [P] [US3] Add IP Addressing section (IPv4 subnetting, IPv6 address types)
- [x] T044 [P] [US3] Add Automation section (pyATS, YANG, NETCONF)
- [x] T045 [US3] Verify all CCIE-level expertise from original SOUL.md is preserved
- [ ] T046 [US3] Test expertise loading by asking about BGP path selection - verify detailed response (MANUAL TEST)
- [ ] T047 [US3] Test expertise loading by asking about OSPF area types - verify CCIE-level detail (MANUAL TEST)
- [ ] T048 [US3] Test fallback behavior when SOUL-EXPERTISE.md is unavailable (MANUAL TEST)

**Checkpoint**: User Story 3 complete - Expertise reference loads on-demand and provides CCIE-level detail

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and content preservation verification

- [x] T049 Verify total character count across all 3 SOUL files is approximately 59,121 (100% content preserved)
- [x] T050 Verify SOUL.md follows contract structure from contracts/modular-soul.md
- [x] T051 Verify SOUL-SKILLS.md follows contract structure with all 97 skills
- [x] T052 Verify SOUL-EXPERTISE.md follows contract structure with all domains
- [x] T053 Run full quickstart.md validation checklist
- [ ] T054 Test multi-reference scenario: ask question requiring both skills AND expertise (MANUAL TEST)
- [x] T055 Document any deviations from original SOUL.md content or behavior

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 MUST complete first (SOUL.md is required for all testing)
  - US2 and US3 can proceed in parallel after US1 is complete
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 complete (needs SOUL.md with loading instructions)
- **User Story 3 (P3)**: Depends on US1 complete (needs SOUL.md with loading instructions)

### Within Each User Story

- Create file structure before adding content sections
- Add content sections in logical order (can parallelize independent sections)
- Verify/test after all content is added
- Story complete before validation tests

### Parallel Opportunities

- T021-T033: All skill category sections can be written in parallel
- T038-T044: All expertise domain sections can be written in parallel
- US2 and US3 can be implemented in parallel after US1 completes

---

## Parallel Example: User Story 2 Skill Sections

```bash
# Launch all skill category sections in parallel:
Task: "Add Device Automation Skills section"
Task: "Add Linux Host Operations section"
Task: "Add JunOS Device Operations section"
Task: "Add Cloud Skills section"
Task: "Add Observability Skills section"
# ... all T021-T033 tasks can run simultaneously
```

---

## Parallel Example: User Story 3 Expertise Sections

```bash
# Launch all expertise domain sections in parallel:
Task: "Add Routing & Switching section"
Task: "Add Data Center / SDN section"
Task: "Add Application Delivery section"
Task: "Add Wireless / Campus section"
# ... all T038-T044 tasks can run simultaneously
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (backup and analysis)
2. Complete Phase 2: Foundational (extraction planning)
3. Complete Phase 3: User Story 1 (new SOUL.md under 20k chars)
4. **STOP and VALIDATE**: Test bootstrap, identity, GAIT workflow
5. NetGeniusClaw is now functional without truncation

### Incremental Delivery

1. Complete Setup + Foundational -> Extraction plan ready
2. Add User Story 1 -> Test bootstrap -> **MVP functional!**
3. Add User Story 2 -> Test skill loading -> Skills work on-demand
4. Add User Story 3 -> Test expertise loading -> Full functionality restored
5. Each story adds value without breaking previous functionality

### Single Developer Strategy (Recommended)

1. Complete phases 1-3 sequentially (US1 = MVP)
2. Then parallelize T021-T033 (skill sections)
3. Then parallelize T038-T044 (expertise sections)
4. Run validation tests

---

## Notes

- [P] tasks = different sections/files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- This is a documentation reorganization - no code involved
- All validation is manual (character counts, bootstrap tests, user prompts)
- Rollback: restore from ~/.openclaw/workspace/SOUL.md.backup if needed
