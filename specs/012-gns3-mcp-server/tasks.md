# Tasks: GNS3 MCP Server and Skills

**Input**: Design documents from `/specs/012-gns3-mcp-server/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/gns3-mcp-tools.md, quickstart.md

**Tests**: Not explicitly requested in spec. Manual verification via quickstart.md scenarios.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

```text
mcp-servers/gns3-mcp-server/
├── gns3_mcp_server.py       # Main FastMCP server
├── README.md                 # Server documentation
├── requirements.txt          # Dependencies
├── .env.example              # Environment template
└── tests/
    └── test_gns3_mcp_server.py

workspace/skills/
├── gns3-project-lifecycle/SKILL.md
├── gns3-node-operations/SKILL.md
├── gns3-link-management/SKILL.md
├── gns3-packet-capture/SKILL.md
└── gns3-snapshot-ops/SKILL.md
```

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic server structure

- [x] T001 Create mcp-servers/gns3-mcp-server/ directory structure
- [x] T002 [P] Create mcp-servers/gns3-mcp-server/requirements.txt with fastmcp, httpx, python-dotenv
- [x] T003 [P] Create mcp-servers/gns3-mcp-server/.env.example with GNS3_URL, GNS3_USER, GNS3_PASSWORD
- [x] T004 [P] Create mcp-servers/gns3-mcp-server/README.md with overview, installation, and usage

**Checkpoint**: Project structure ready for implementation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story tools can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create mcp-servers/gns3-mcp-server/gns3_mcp_server.py with FastMCP initialization and imports
- [x] T006 Implement GNS3Client class with authentication (token caching) in gns3_mcp_server.py
- [x] T007 Implement auto-authentication decorator in gns3_mcp_server.py
- [x] T008 Implement error handling utilities (GNS3 error codes to structured responses) in gns3_mcp_server.py
- [x] T009 Implement project/node name-to-UUID resolution helper in gns3_mcp_server.py
- [x] T010 Implement GAIT audit logging decorator in gns3_mcp_server.py
- [x] T011 [P] Implement gns3_list_templates utility tool in gns3_mcp_server.py
- [x] T012 [P] Implement gns3_list_computes utility tool in gns3_mcp_server.py

**Checkpoint**: Foundation ready - GNS3 client authenticated, error handling in place, user story tools can begin

---

## Phase 3: User Story 1 - Project Lifecycle Management (Priority: P1) MVP

**Goal**: Users can create, manage, and tear down GNS3 projects through natural language commands

**Independent Test**: Create a new GNS3 project, list existing projects, open/close the project, and delete it when done

### Implementation for User Story 1

- [x] T013 [US1] Implement gns3_list_projects tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T014 [US1] Implement gns3_create_project tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T015 [US1] Implement gns3_get_project tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T016 [US1] Implement gns3_open_project tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T017 [US1] Implement gns3_close_project tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T018 [US1] Implement gns3_delete_project tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T019 [US1] Implement gns3_clone_project tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T020 [US1] Implement gns3_export_project tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T021 [US1] Implement gns3_import_project tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T022 [US1] Create workspace/skills/gns3-project-lifecycle/SKILL.md with all 9 project tools documented

**Checkpoint**: User Story 1 complete - Users can manage GNS3 project lifecycle through natural language

---

## Phase 4: User Story 2 - Node Operations (Priority: P2)

**Goal**: Users can add network devices from templates, control their power state, and access their consoles

**Independent Test**: Add a router node from a template, start the node, verify it's running, stop the node, and remove it

### Implementation for User Story 2

- [x] T023 [US2] Implement gns3_list_nodes tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T024 [US2] Implement gns3_create_node tool with template fuzzy matching in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T025 [US2] Implement gns3_start_node tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T026 [US2] Implement gns3_stop_node tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T027 [US2] Implement gns3_suspend_node tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T028 [US2] Implement gns3_reload_node tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T029 [US2] Implement gns3_bulk_node_action tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T030 [US2] Implement gns3_get_node_console tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T031 [US2] Create workspace/skills/gns3-node-operations/SKILL.md with all 8 node tools documented

**Checkpoint**: User Story 2 complete - Users can manage nodes and access consoles

---

## Phase 5: User Story 3 - Link Management and Topology Building (Priority: P3)

**Goal**: Users can create and manage links between node interfaces, enabling network connectivity

**Independent Test**: Create a link between two nodes, verify connectivity, delete the link

### Implementation for User Story 3

- [x] T032 [US3] Implement gns3_list_links tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T033 [US3] Implement interface name parsing helper (eth0, Gi0/0, etc.) in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T034 [US3] Implement gns3_create_link tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T035 [US3] Implement gns3_delete_link tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T036 [US3] Implement gns3_isolate_node tool (isolate/unisolate) in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T037 [US3] Create workspace/skills/gns3-link-management/SKILL.md with all 4 link tools documented

**Checkpoint**: User Story 3 complete - Users can build and modify lab topologies

---

## Phase 6: User Story 4 - Packet Capture (Priority: P4)

**Goal**: Users can start and stop packet captures on links and retrieve the captured data

**Independent Test**: Start a capture on a link, generate some traffic, stop the capture, and retrieve/stream the PCAP data

### Implementation for User Story 4

- [x] T038 [US4] Implement gns3_start_capture tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T039 [US4] Implement gns3_stop_capture tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T040 [US4] Implement gns3_get_capture tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T041 [US4] Create workspace/skills/gns3-packet-capture/SKILL.md with all 3 capture tools documented

**Checkpoint**: User Story 4 complete - Users can capture and retrieve network traffic

---

## Phase 7: User Story 5 - Snapshot Management (Priority: P5)

**Goal**: Users can create snapshots and restore to previous states for safe experimentation

**Independent Test**: Create a snapshot of a project, make changes, restore the snapshot, verify state is restored

### Implementation for User Story 5

- [x] T042 [US5] Implement gns3_list_snapshots tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T043 [US5] Implement gns3_create_snapshot tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T044 [US5] Implement gns3_restore_snapshot tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T045 [US5] Implement gns3_delete_snapshot tool in mcp-servers/gns3-mcp-server/gns3_mcp_server.py
- [x] T046 [US5] Create workspace/skills/gns3-snapshot-ops/SKILL.md with all 4 snapshot tools documented

**Checkpoint**: User Story 5 complete - Users can save and restore lab states

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, integration, and final verification

- [x] T047 Update config/openclaw.json with gns3 MCP server registration
- [x] T048 [P] Update .env.example in repository root with GNS3_URL, GNS3_USER, GNS3_PASSWORD
- [x] T049 [P] Update README.md with GNS3 MCP server in architecture section
- [x] T050 [P] Update SOUL.md with gns3-* skills in skill index
- [x] T051 Verify all 23 tools return consistent JSON response format per contracts
- [x] T052 Run quickstart.md validation scenarios manually
- [x] T053 Verify GAIT audit logging works for all tool invocations
- [x] T054 Create mcp-servers/gns3-mcp-server/tests/test_gns3_mcp_server.py with basic smoke tests
- [ ] T055 Draft WordPress blog post per Constitution XVII (milestone documentation)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can proceed sequentially in priority order (P1 → P2 → P3 → P4 → P5)
  - US2-US5 depend on US1 (need project to exist) for testing but can be implemented in parallel
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational - Requires US1 for testing (needs a project)
- **User Story 3 (P3)**: Can start after Foundational - Requires US1+US2 for testing (needs project and nodes)
- **User Story 4 (P4)**: Can start after Foundational - Requires US3 for testing (needs links)
- **User Story 5 (P5)**: Can start after Foundational - Requires US1 for testing (needs a project)

### Within Each User Story

- Implement all tools for the skill
- Create SKILL.md documentation
- Story complete before checkpoint

### Parallel Opportunities

- T002, T003, T004: All setup files can be created in parallel
- T011, T012: Utility tools can be implemented in parallel
- T047, T048, T049, T050: Polish documentation updates can be done in parallel
- Tools within a user story are sequential (same file gns3_mcp_server.py)

---

## Parallel Example: Setup Phase

```bash
# Launch all setup tasks in parallel:
Task: "Create requirements.txt in mcp-servers/gns3-mcp-server/"
Task: "Create .env.example in mcp-servers/gns3-mcp-server/"
Task: "Create README.md in mcp-servers/gns3-mcp-server/"
```

---

## Parallel Example: Polish Phase

```bash
# Launch all documentation updates in parallel:
Task: "Update .env.example in repository root"
Task: "Update README.md with GNS3 server info"
Task: "Update SOUL.md with gns3-* skills"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - authentication, error handling)
3. Complete Phase 3: User Story 1 (project lifecycle)
4. **STOP and VALIDATE**: Test project create/list/open/close/delete
5. Deploy/demo if ready - users can now create and manage GNS3 labs

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **MVP functional!**
3. Add User Story 2 → Test independently → Node operations work
4. Add User Story 3 → Test independently → Topology building works
5. Add User Story 4 → Test independently → Packet capture works
6. Add User Story 5 → Test independently → Snapshots work
7. Each story adds value without breaking previous stories

### Single Developer Strategy (Recommended)

1. Complete phases 1-3 sequentially (US1 = MVP)
2. Then proceed US2 → US3 → US4 → US5 in order
3. Run Polish phase after all user stories
4. Total: 55 tasks

---

## Task Summary

| Phase | Tasks | Parallel Opportunities |
|-------|-------|------------------------|
| Setup | 4 | T002, T003, T004 |
| Foundational | 8 | T011, T012 |
| US1: Project Lifecycle | 10 | None (same file) |
| US2: Node Operations | 9 | None (same file) |
| US3: Link Management | 6 | None (same file) |
| US4: Packet Capture | 4 | None (same file) |
| US5: Snapshot Ops | 5 | None (same file) |
| Polish | 9 | T047, T048, T049, T050 |
| **Total** | **55** | |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- All 23 tools + 3 utility tools defined in contracts/gns3-mcp-tools.md
- 5 SKILL.md files required (one per skill category)
- All tools implemented in single gns3_mcp_server.py file (monolithic pattern)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
