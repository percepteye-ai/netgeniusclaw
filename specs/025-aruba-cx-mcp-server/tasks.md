# Tasks: Aruba CX MCP Server Integration

**Input**: Design documents from `/specs/025-aruba-cx-mcp-server/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/aruba-cx-tools.md, quickstart.md

**Tests**: Not explicitly requested - tests are OPTIONAL for this integration (manual verification via quickstart.md).

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Includes exact file paths in descriptions

## Path Conventions

- **MCP Server**: `mcp-servers/aruba-cx-mcp/` (cloned from GitHub)
- **Skills**: `workspace/skills/aruba-cx-*/SKILL.md`
- **Configuration**: `config/openclaw.json`, `.env.example`, `scripts/install.sh`
- **Documentation**: `README.md`, `SOUL.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Clone community MCP server and configure NetGeniusClaw integration

- [x] T001 Add Aruba CX MCP server git clone to scripts/install.sh
- [x] T002 [P] Add pip/uv dependency installation for aruba-cx-mcp to scripts/install.sh
- [x] T003 [P] Add ARUBA_CX environment variables to .env.example
- [x] T004 Register aruba-cx-mcp server in config/openclaw.json

**Checkpoint**: MCP server cloned and registered - ready for skill creation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core skill infrastructure that enables all user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create workspace/skills/aruba-cx-system/ directory structure
- [x] T006 [P] Create workspace/skills/aruba-cx-interfaces/ directory structure
- [x] T007 [P] Create workspace/skills/aruba-cx-switching/ directory structure
- [x] T008 [P] Create workspace/skills/aruba-cx-config/ directory structure

**Checkpoint**: Foundation ready - skill directories exist, user story implementation can begin

---

## Phase 3: User Story 1 - System and Firmware Discovery (Priority: P1) 🎯 MVP

**Goal**: Enable network engineers to discover switch system info, firmware versions, and VSF topology

**Independent Test**: Query any Aruba CX switch for system info, firmware details, and VSF membership per quickstart.md Scenario 1

### Implementation for User Story 1

- [x] T009 [US1] Create aruba-cx-system SKILL.md with YAML frontmatter in workspace/skills/aruba-cx-system/SKILL.md
- [x] T010 [US1] Document get_system_info tool usage in workspace/skills/aruba-cx-system/SKILL.md
- [x] T011 [US1] Document get_firmware_info tool usage in workspace/skills/aruba-cx-system/SKILL.md
- [x] T012 [US1] Document get_vsf_topology tool usage in workspace/skills/aruba-cx-system/SKILL.md
- [x] T013 [US1] Add workflow examples for system discovery in workspace/skills/aruba-cx-system/SKILL.md
- [x] T014 [US1] Add error handling documentation for US1 in workspace/skills/aruba-cx-system/SKILL.md

**Checkpoint**: User Story 1 complete - system discovery skill fully documented and functional

---

## Phase 4: User Story 2 - Interface and Connectivity Monitoring (Priority: P1)

**Goal**: Enable network engineers to view interface status, LLDP neighbors, and optical transceiver health

**Independent Test**: Query interface states, LLDP neighbors, and DOM diagnostics per quickstart.md Scenario 2

### Implementation for User Story 2

- [x] T015 [US2] Create aruba-cx-interfaces SKILL.md with YAML frontmatter in workspace/skills/aruba-cx-interfaces/SKILL.md
- [x] T016 [US2] Document get_interfaces tool usage in workspace/skills/aruba-cx-interfaces/SKILL.md
- [x] T017 [US2] Document get_lldp_neighbors tool usage in workspace/skills/aruba-cx-interfaces/SKILL.md
- [x] T018 [US2] Document get_dom_diagnostics tool usage with threshold alerts in workspace/skills/aruba-cx-interfaces/SKILL.md
- [x] T019 [US2] Add workflow examples for interface troubleshooting in workspace/skills/aruba-cx-interfaces/SKILL.md
- [x] T020 [US2] Add error handling documentation for US2 in workspace/skills/aruba-cx-interfaces/SKILL.md

**Checkpoint**: User Story 2 complete - interface monitoring skill fully documented and functional

---

## Phase 5: User Story 3 - Switching and Layer 2 Operations (Priority: P2)

**Goal**: Enable network engineers to view VLANs and MAC address tables for Layer 2 visibility

**Independent Test**: Query VLAN configurations and MAC address tables per quickstart.md Scenario 3

### Implementation for User Story 3

- [x] T021 [US3] Create aruba-cx-switching SKILL.md with YAML frontmatter in workspace/skills/aruba-cx-switching/SKILL.md
- [x] T022 [US3] Document get_vlans tool usage in workspace/skills/aruba-cx-switching/SKILL.md
- [x] T023 [US3] Document get_mac_table tool usage in workspace/skills/aruba-cx-switching/SKILL.md
- [x] T024 [US3] Document create_vlan, configure_vlan, delete_vlan write tools with ITSM gating in workspace/skills/aruba-cx-switching/SKILL.md
- [x] T025 [US3] Add workflow examples for MAC tracking and VLAN management in workspace/skills/aruba-cx-switching/SKILL.md
- [x] T026 [US3] Add error handling documentation for US3 in workspace/skills/aruba-cx-switching/SKILL.md

**Checkpoint**: User Story 3 complete - switching operations skill fully documented and functional

---

## Phase 6: User Story 4 - Configuration and Change Management (Priority: P2)

**Goal**: Enable network engineers to view configs, save changes, and perform ISSU upgrades with ITSM gating

**Independent Test**: View configs, save changes, and ISSU operations per quickstart.md Scenarios 4-5

### Implementation for User Story 4

- [x] T027 [US4] Create aruba-cx-config SKILL.md with YAML frontmatter in workspace/skills/aruba-cx-config/SKILL.md
- [x] T028 [US4] Document get_running_config and get_startup_config tool usage in workspace/skills/aruba-cx-config/SKILL.md
- [x] T029 [US4] Document get_routing_table tool usage in workspace/skills/aruba-cx-config/SKILL.md
- [x] T030 [US4] Document save_config write tool with ITSM gating in workspace/skills/aruba-cx-config/SKILL.md
- [x] T031 [US4] Document get_issu_status and issu_upgrade tools with ITSM gating in workspace/skills/aruba-cx-config/SKILL.md
- [x] T032 [US4] Document upload_firmware and download_firmware tools with ITSM gating in workspace/skills/aruba-cx-config/SKILL.md
- [x] T033 [US4] Add workflow examples for config management and ISSU in workspace/skills/aruba-cx-config/SKILL.md
- [x] T034 [US4] Add ITSM integration documentation (ITSM_ENABLED, ITSM_LAB_MODE) in workspace/skills/aruba-cx-config/SKILL.md
- [x] T035 [US4] Add error handling documentation for US4 in workspace/skills/aruba-cx-config/SKILL.md

**Checkpoint**: User Story 4 complete - config management skill fully documented and functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Full-stack artifact coherence and documentation updates

- [x] T036 [P] Update README.md with Aruba CX MCP server in architecture section
- [x] T037 [P] Update README.md with skill count and integration count
- [x] T038 [P] Add aruba-cx-system, aruba-cx-interfaces, aruba-cx-switching, aruba-cx-config to SOUL.md skill index
- [x] T039 [P] Add Aruba CX skills to appropriate category section in SOUL.md
- [x] T040 Run quickstart.md validation scenarios (manual verification - requires live switches)
- [x] T041 Verify install.sh successfully clones and installs aruba-cx-mcp
- [x] T042 Verify all 4 skills appear in NetGeniusClaw skill inventory
- [x] T043 [P] Create mcp-servers/aruba-cx-mcp/README.md if not provided by community server (N/A - community provides)

**Checkpoint**: All artifacts coherent - ready for PR review

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on T004 (openclaw.json registration)
- **User Story 1-4 (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can proceed in parallel or sequentially in priority order
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories - MVP candidate
- **User Story 2 (P1)**: No dependencies on other stories - can run parallel to US1
- **User Story 3 (P2)**: No dependencies on US1/US2 - can start after Foundational
- **User Story 4 (P2)**: No dependencies on US1-3 - can start after Foundational

### Within Each User Story

- SKILL.md created first (frontmatter defines skill)
- Tools documented in dependency order (read tools before write tools)
- Workflow examples after tool documentation
- Error handling last

### Parallel Opportunities

**Phase 1 Parallel Tasks**:
- T002, T003 can run in parallel (different files)

**Phase 2 Parallel Tasks**:
- T005, T006, T007, T008 can ALL run in parallel (different directories)

**User Stories Parallel**:
- US1, US2, US3, US4 can ALL run in parallel after Phase 2 (different skill directories)

**Phase 7 Parallel Tasks**:
- T036, T037, T038, T039, T043 can run in parallel (different files)

---

## Parallel Example: Full Team Execution

```bash
# Phase 1 - Sequential (dependencies)
T001: Add git clone to install.sh
T002 & T003: [PARALLEL] Add pip install + env vars
T004: Register in openclaw.json

# Phase 2 - Parallel (independent directories)
T005 & T006 & T007 & T008: [PARALLEL] Create all skill directories

# Phase 3-6 - Parallel (independent user stories)
Developer A: T009-T014 (User Story 1 - System Discovery)
Developer B: T015-T020 (User Story 2 - Interface Monitoring)
Developer C: T021-T026 (User Story 3 - Switching Operations)
Developer D: T027-T035 (User Story 4 - Config Management)

# Phase 7 - Parallel then Sequential
T036 & T037 & T038 & T039 & T043: [PARALLEL] Documentation updates
T040-T042: [SEQUENTIAL] Validation
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T008)
3. Complete Phase 3: User Story 1 (T009-T014)
4. **STOP and VALIDATE**: Test system discovery per quickstart.md Scenario 1
5. Deploy/demo if ready - engineers can now inventory switches

### Incremental Delivery

1. Setup + Foundational → MCP server cloned and registered
2. Add US1 → System Discovery available → Demo MVP!
3. Add US2 → Interface Monitoring available → Demo
4. Add US3 → Switching Operations available → Demo
5. Add US4 → Config Management available → Full feature complete
6. Polish → All artifacts coherent → PR ready

### Single Developer Strategy

Execute in priority order:
1. Phase 1: Setup
2. Phase 2: Foundational
3. Phase 3: User Story 1 (P1) - MVP
4. Phase 4: User Story 2 (P1)
5. Phase 5: User Story 3 (P2)
6. Phase 6: User Story 4 (P2)
7. Phase 7: Polish

---

## Notes

- [P] tasks = different files, no dependencies
- [US#] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Manual verification via quickstart.md scenarios (no automated tests)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All write operations (US3, US4) must document ITSM gating per constitution
