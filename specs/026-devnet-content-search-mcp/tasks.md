# Tasks: DevNet Content Search MCP Server Integration

**Input**: Design documents from `/specs/026-devnet-content-search-mcp/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: No automated tests required - manual verification via MCP tool invocation per quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This is a configuration-only integration. Files affected:
- `config/openclaw.json` - MCP server registration
- `~/.openclaw/config/openclaw.json` - Running gateway config
- `workspace/skills/` - Skill definitions
- `README.md`, `SOUL.md` - Documentation

---

## Phase 1: Setup (MCP Server Registration)

**Purpose**: Register the remote DevNet Content Search MCP server

- [x] T001 Register devnet-content-search MCP server in config/openclaw.json with URL endpoint
- [x] T002 Copy devnet-content-search config to running gateway at ~/.openclaw/config/openclaw.json
- [ ] T003 Restart OpenClaw gateway to load new MCP server (USER ACTION REQUIRED)

**Checkpoint**: MCP server registered and gateway restarted

---

## Phase 2: Foundational (Skill Directory Setup)

**Purpose**: Create skill directory structure before skill implementation

- [x] T004 [P] Create devnet-meraki-search skill directory at workspace/skills/devnet-meraki-search/
- [x] T005 [P] Create devnet-catalyst-search skill directory at workspace/skills/devnet-catalyst-search/

**Checkpoint**: Skill directories ready for SKILL.md files

---

## Phase 3: User Story 1 - Search Meraki API Documentation (Priority: P1)

**Goal**: Enable network engineers to search Meraki API documentation for firewall, VLAN, and wireless configurations

**Independent Test**: Search for "L3 firewall rules" and verify API endpoints are returned with descriptions per quickstart.md Scenario 1

### Implementation for User Story 1

- [x] T006 [US1] Create devnet-meraki-search SKILL.md with YAML frontmatter in workspace/skills/devnet-meraki-search/SKILL.md
- [x] T007 [US1] Document Meraki-API-Doc-Search tool usage in workspace/skills/devnet-meraki-search/SKILL.md
- [x] T008 [US1] Document Meraki-API-OperationId-Search tool usage in workspace/skills/devnet-meraki-search/SKILL.md
- [x] T009 [US1] Add workflow examples for Meraki API search in workspace/skills/devnet-meraki-search/SKILL.md
- [x] T010 [US1] Add error handling documentation for US1 in workspace/skills/devnet-meraki-search/SKILL.md

**Checkpoint**: User Story 1 complete - Meraki API search skill fully documented and functional

---

## Phase 4: User Story 2 - Search Catalyst Center API Documentation (Priority: P1)

**Goal**: Enable network engineers to search Catalyst Center API documentation for device management and policy automation

**Independent Test**: Search for "device inventory" and verify Catalyst Center APIs are returned per quickstart.md Scenario 2

### Implementation for User Story 2

- [x] T011 [US2] Create devnet-catalyst-search SKILL.md with YAML frontmatter in workspace/skills/devnet-catalyst-search/SKILL.md
- [x] T012 [US2] Document CatalystCenter-API-Doc-Search tool usage in workspace/skills/devnet-catalyst-search/SKILL.md
- [x] T013 [US2] Add workflow examples for Catalyst Center API search in workspace/skills/devnet-catalyst-search/SKILL.md
- [x] T014 [US2] Add error handling documentation for US2 in workspace/skills/devnet-catalyst-search/SKILL.md

**Checkpoint**: User Story 2 complete - Catalyst Center API search skill fully documented and functional

---

## Phase 5: User Story 3 - Lookup Specific Meraki Operation by ID (Priority: P2)

**Goal**: Enable developers to lookup specific Meraki operation IDs for exact API specifications

**Independent Test**: Lookup "updateNetworkApplianceFirewallL3FirewallRules" and verify complete OpenAPI spec is returned per quickstart.md Scenario 3

### Implementation for User Story 3

- [x] T015 [US3] Enhance devnet-meraki-search SKILL.md with operation ID lookup section in workspace/skills/devnet-meraki-search/SKILL.md
- [x] T016 [US3] Add workflow example for operation ID lookup in workspace/skills/devnet-meraki-search/SKILL.md

**Checkpoint**: User Story 3 complete - Operation ID lookup documented in Meraki skill

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates and validation

- [x] T017 [P] Update README.md with DevNet Content Search MCP entry (MCP #71)
- [x] T018 [P] Update README.md skill count (add 2 skills)
- [x] T019 [P] Update SOUL.md with devnet-meraki-search and devnet-catalyst-search skills
- [x] T020 [P] Add DevNet skills to appropriate category section in SOUL.md
- [x] T021 Copy skills to running OpenClaw at ~/.openclaw/workspace/skills/
- [ ] T022 Run quickstart.md validation scenarios (Scenarios 1-5) (USER ACTION: Restart gateway first)
- [ ] T023 Verify all 3 MCP tools are accessible via NetGeniusClaw skills (USER ACTION: Restart gateway first)

**Checkpoint**: All artifacts coherent - ready for PR review

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion
- **User Stories (Phase 3-5)**: Depend on Foundational phase completion
  - US1 and US2 can proceed in parallel (both P1 priority)
  - US3 enhances US1 skill, so should follow US1
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Independent of US1
- **User Story 3 (P2)**: Enhances US1 skill - should complete after US1

### Parallel Opportunities

**Phase 2 Parallel**:
```
T004 [P] Create devnet-meraki-search directory
T005 [P] Create devnet-catalyst-search directory
```

**Phase 3 & 4 Parallel** (different skills):
```
US1: T006-T010 (devnet-meraki-search)
US2: T011-T014 (devnet-catalyst-search)
```

**Phase 6 Parallel**:
```
T017 [P] Update README.md MCP entry
T018 [P] Update README.md skill count
T019 [P] Update SOUL.md skills
T020 [P] Update SOUL.md categories
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T005)
3. Complete Phase 3: User Story 1 (T006-T010)
4. **STOP and VALIDATE**: Test Meraki search independently
5. Deploy if ready - users can search Meraki docs

### Incremental Delivery

1. Complete Setup + Foundational → MCP server registered
2. Add User Story 1 → Test Meraki search → Deploy (MVP!)
3. Add User Story 2 → Test Catalyst Center search → Deploy
4. Add User Story 3 → Test operation ID lookup → Deploy
5. Each story adds value without breaking previous stories

### Full Implementation

Execute all 23 tasks in order:
- Phase 1: 3 tasks
- Phase 2: 2 tasks
- Phase 3 (US1): 5 tasks
- Phase 4 (US2): 4 tasks
- Phase 5 (US3): 2 tasks
- Phase 6 (Polish): 7 tasks

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- This is a configuration-only integration - no source code to write
- All verification is manual via MCP tool invocation
- Skills are defined via SKILL.md files, not code
- Remote MCP server requires internet connectivity to devnet.cisco.com
