# Tasks: Prisma SD-WAN MCP Server Integration

**Input**: Design documents from `/specs/013-prisma-sdwan-mcp-server/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/prisma-sdwan-tools.md, quickstart.md

**Tests**: Manual verification via quickstart.md scenarios (no automated tests requested)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

```text
# Community MCP server (cloned by install.sh)
mcp-servers/prisma-sdwan-mcp/
├── (cloned from https://github.com/iamdheerajdubey/prisma-sdwan-mcp)
└── README.md

# NetGeniusClaw skills
workspace/skills/
├── prisma-sdwan-topology/SKILL.md
├── prisma-sdwan-status/SKILL.md
├── prisma-sdwan-config/SKILL.md
└── prisma-sdwan-apps/SKILL.md

# Configuration updates
config/openclaw.json
.env.example
scripts/install.sh
README.md
SOUL.md
```

---

## Phase 1: Setup (MCP Server Installation)

**Purpose**: Clone community MCP server and configure NetGeniusClaw integration

- [x] T001 Update scripts/install.sh to clone prisma-sdwan-mcp from https://github.com/iamdheerajdubey/prisma-sdwan-mcp to mcp-servers/prisma-sdwan-mcp/
- [x] T002 [P] Update .gitignore to add exception !mcp-servers/prisma-sdwan-mcp/
- [x] T003 [P] Update .env.example with PAN_CLIENT_ID, PAN_CLIENT_SECRET, PAN_TSG_ID, PAN_REGION variables and descriptions
- [x] T004 [P] Update config/openclaw.json to register prisma-sdwan MCP server with environment variable mappings

**Checkpoint**: MCP server cloned and registered in NetGeniusClaw configuration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Documentation updates that MUST be complete before skill creation

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Update README.md to add Prisma SD-WAN to architecture section and MCP server list
- [x] T006 [P] Update SOUL.md to add prisma-sdwan-* skills to the skill index (4 skills: topology, status, config, apps)
- [ ] T007 Verify MCP server can be started and connects to Prisma SASE API (manual connectivity test)

**Checkpoint**: Foundation ready - skill documentation can now begin

---

## Phase 3: User Story 1 - SD-WAN Topology Discovery (Priority: P1) MVP

**Goal**: Enable NetGeniusClaw to discover all sites, ION devices (elements), and topology from Prisma SD-WAN

**Independent Test**: Ask "list all SD-WAN sites" and verify sites are returned with names, IDs, and element counts

### Implementation for User Story 1

- [x] T008 [US1] Create workspace/skills/prisma-sdwan-topology/ directory
- [x] T009 [US1] Create workspace/skills/prisma-sdwan-topology/SKILL.md with get_sites tool documentation
- [x] T010 [US1] Add get_elements tool documentation to workspace/skills/prisma-sdwan-topology/SKILL.md
- [x] T011 [US1] Add get_machines tool documentation to workspace/skills/prisma-sdwan-topology/SKILL.md
- [x] T012 [US1] Add get_topology tool documentation to workspace/skills/prisma-sdwan-topology/SKILL.md
- [x] T013 [US1] Add workflow examples and natural language query examples to workspace/skills/prisma-sdwan-topology/SKILL.md
- [ ] T014 [US1] Test US1 by asking NetGeniusClaw to "list all SD-WAN sites" - verify response (MANUAL TEST)

**Checkpoint**: User Story 1 complete - Users can discover SD-WAN topology through natural language

---

## Phase 4: User Story 2 - SD-WAN Health and Status Monitoring (Priority: P2)

**Goal**: Enable NetGeniusClaw to query element status, software versions, alarms, and events

**Independent Test**: Ask "show SD-WAN alarms" and verify active alarms are returned with severity

### Implementation for User Story 2

- [x] T015 [US2] Create workspace/skills/prisma-sdwan-status/ directory
- [x] T016 [US2] Create workspace/skills/prisma-sdwan-status/SKILL.md with get_element_status tool documentation
- [x] T017 [US2] Add get_software_status tool documentation to workspace/skills/prisma-sdwan-status/SKILL.md
- [x] T018 [US2] Add get_events tool documentation to workspace/skills/prisma-sdwan-status/SKILL.md
- [x] T019 [US2] Add get_alarms tool documentation to workspace/skills/prisma-sdwan-status/SKILL.md
- [x] T020 [US2] Add workflow examples and natural language query examples to workspace/skills/prisma-sdwan-status/SKILL.md
- [ ] T021 [US2] Test US2 by asking NetGeniusClaw to "show SD-WAN alarms" - verify response (MANUAL TEST)

**Checkpoint**: User Story 2 complete - Users can monitor SD-WAN health and status

---

## Phase 5: User Story 3 - SD-WAN Configuration Inspection (Priority: P3)

**Goal**: Enable NetGeniusClaw to query interfaces, routing, policies, and security zones

**Independent Test**: Ask "show interfaces on element [name]" and verify interface details are returned

### Implementation for User Story 3

- [x] T022 [US3] Create workspace/skills/prisma-sdwan-config/ directory
- [x] T023 [US3] Create workspace/skills/prisma-sdwan-config/SKILL.md with get_interfaces tool documentation
- [x] T024 [US3] Add get_wan_interfaces tool documentation to workspace/skills/prisma-sdwan-config/SKILL.md
- [x] T025 [US3] Add get_bgp_peers tool documentation to workspace/skills/prisma-sdwan-config/SKILL.md
- [x] T026 [US3] Add get_static_routes tool documentation to workspace/skills/prisma-sdwan-config/SKILL.md
- [x] T027 [US3] Add get_policy_sets tool documentation to workspace/skills/prisma-sdwan-config/SKILL.md
- [x] T028 [US3] Add get_security_zones tool documentation to workspace/skills/prisma-sdwan-config/SKILL.md
- [x] T029 [US3] Add generate_site_config tool documentation to workspace/skills/prisma-sdwan-config/SKILL.md
- [x] T030 [US3] Add workflow examples and natural language query examples to workspace/skills/prisma-sdwan-config/SKILL.md
- [ ] T031 [US3] Test US3 by asking NetGeniusClaw to "list SD-WAN policy sets" - verify response (MANUAL TEST)

**Checkpoint**: User Story 3 complete - Users can inspect SD-WAN configuration

---

## Phase 6: User Story 4 - Application Visibility (Priority: P4)

**Goal**: Enable NetGeniusClaw to query application definitions

**Independent Test**: Ask "list SD-WAN application definitions" and verify applications are returned

### Implementation for User Story 4

- [x] T032 [US4] Create workspace/skills/prisma-sdwan-apps/ directory
- [x] T033 [US4] Create workspace/skills/prisma-sdwan-apps/SKILL.md with get_app_defs tool documentation
- [x] T034 [US4] Add workflow examples and natural language query examples to workspace/skills/prisma-sdwan-apps/SKILL.md
- [ ] T035 [US4] Test US4 by asking NetGeniusClaw to "list SD-WAN application definitions" - verify response (MANUAL TEST)

**Checkpoint**: User Story 4 complete - Users can view application definitions

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and artifact coherence

- [ ] T036 Run full quickstart.md validation scenarios (all 6 scenarios) (MANUAL TEST)
- [x] T037 [P] Verify all 4 SKILL.md files are complete and consistent
- [x] T038 [P] Verify SOUL.md skill index includes all 4 prisma-sdwan-* skills
- [x] T039 [P] Verify README.md accurately reflects Prisma SD-WAN capabilities
- [x] T040 [P] Verify config/openclaw.json has correct MCP server registration
- [x] T041 [P] Verify .env.example has all 4 PAN_* variables documented
- [x] T042 [P] Verify install.sh correctly clones and sets up prisma-sdwan-mcp
- [x] T043 Draft WordPress blog post documenting Prisma SD-WAN integration milestone (Constitution XVII) - Post ID 1568

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1-US4 can proceed sequentially in priority order (P1 → P2 → P3 → P4)
  - Or in parallel if desired (different SKILL.md files, no cross-dependencies)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - No dependencies on other stories

### Within Each User Story

- Create directory first
- Add tool documentation sequentially
- Add workflow examples after all tools documented
- Manual test after skill is complete

### Parallel Opportunities

- T002, T003, T004: All setup config files can be updated in parallel
- T005, T006: README and SOUL.md can be updated in parallel
- US1-US4: All user stories can be implemented in parallel (different directories)
- T037-T042: All verification tasks can run in parallel

---

## Parallel Example: Setup Phase

```bash
# Launch all setup tasks in parallel:
Task: "Update .gitignore for prisma-sdwan-mcp"
Task: "Update .env.example with PAN_* variables"
Task: "Update config/openclaw.json with MCP registration"
```

---

## Parallel Example: All User Stories

```bash
# After Foundational phase, launch all skills in parallel:
Task: "Create prisma-sdwan-topology SKILL.md"
Task: "Create prisma-sdwan-status SKILL.md"
Task: "Create prisma-sdwan-config SKILL.md"
Task: "Create prisma-sdwan-apps SKILL.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (clone MCP server, configure)
2. Complete Phase 2: Foundational (README, SOUL.md updates)
3. Complete Phase 3: User Story 1 (topology discovery skill)
4. **STOP and VALIDATE**: Test "list all SD-WAN sites"
5. Deploy/demo if ready - users can now discover SD-WAN topology

### Incremental Delivery

1. Complete Setup + Foundational → MCP server registered and ready
2. Add User Story 1 → Test independently → **MVP functional!**
3. Add User Story 2 → Test independently → Health monitoring works
4. Add User Story 3 → Test independently → Config inspection works
5. Add User Story 4 → Test independently → App visibility works
6. Each story adds value without breaking previous stories

### Single Developer Strategy (Recommended)

1. Complete phases 1-3 sequentially (US1 = MVP)
2. Then proceed US2 → US3 → US4 in order
3. Run Polish phase after all user stories
4. Total: 43 tasks

---

## Task Summary

| Phase | Tasks | Parallel Opportunities |
|-------|-------|------------------------|
| Setup | 4 | T002, T003, T004 |
| Foundational | 3 | T005, T006 |
| US1: Topology Discovery | 7 | None (same file) |
| US2: Health/Status | 7 | None (same file) |
| US3: Config Inspection | 10 | None (same file) |
| US4: App Visibility | 4 | None (same file) |
| Polish | 8 | T037-T042 |
| **Total** | **43** | |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- 4 SKILL.md files required (one per skill category)
- Community MCP server is cloned, not modified
- All SKILL.md files document existing MCP tools (no code to write)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
