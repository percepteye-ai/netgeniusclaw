# Tasks: Batfish MCP Server

**Input**: Design documents from `/specs/002-batfish-mcp-server/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/mcp-tools.md, quickstart.md

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted. Integration testing is covered via quickstart validation in the Polish phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, directory structure, and dependency configuration

- [x] T001 Create MCP server directory structure at mcp-servers/batfish-mcp/
- [x] T002 Create requirements.txt with pybatfish, mcp[cli], python-dotenv dependencies in mcp-servers/batfish-mcp/requirements.txt
- [x] T003 [P] Create skill directory at workspace/skills/batfish-config-analysis/
- [x] T004 [P] Create Dockerfile for the Batfish MCP server in mcp-servers/batfish-mcp/Dockerfile

**Checkpoint**: Directory structure and dependency files exist. Ready for foundational implementation.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core server skeleton, Batfish session management, error handling, and GAIT logging infrastructure that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create FastMCP server skeleton with environment variable loading (BATFISH_HOST, BATFISH_PORT) and logging setup in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T006 Implement Batfish session manager (pybatfish Session creation, connection validation, graceful error handling for unreachable service) in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T007 Implement GAIT audit logging helper function that logs analysis_type, snapshot_name, parameters, and result_summary via gait_mcp in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T008 Implement shared error handling wrapper that catches pybatfish exceptions and returns structured error responses without exposing stack traces or credentials (FR-012) in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T009 Implement snapshot directory builder helper that creates temp directories with Batfish-expected configs/ structure from either inline configs dict or config_path parameter in mcp-servers/batfish-mcp/batfish_mcp_server.py

**Checkpoint**: Foundation ready — server starts, connects to Batfish, handles errors gracefully, and logs to GAIT. User story implementation can now begin.

---

## Phase 3: User Story 1 — Pre-Change Configuration Validation (Priority: P1) MVP

**Goal**: Operators can upload device configurations and receive a structured pass/fail validation report identifying parse errors, warnings, and structural issues.

**Independent Test**: Upload a set of router configurations (single device, multi-device, intentionally broken config, non-config file), run validation, and verify structured pass/fail reports match expected results per acceptance scenarios 1-4 in spec.md.

### Implementation for User Story 1

- [x] T010 [US1] Implement upload_snapshot tool that accepts configs (dict) or config_path (str), creates Batfish snapshot via bf.init_snapshot(), and returns snapshot_name, device_count, and device list in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T011 [US1] Implement validate_config tool that runs bf.q.fileParseStatus() and bf.q.nodeProperties() on a snapshot and returns per-device ValidationResult with status, vendor, warnings, and errors in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T012 [US1] Add input validation for upload_snapshot (reject empty configs, validate mutually exclusive configs/config_path, handle encoding issues) in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T013 [US1] Add GAIT logging calls to upload_snapshot and validate_config tools in mcp-servers/batfish-mcp/batfish_mcp_server.py

**Checkpoint**: User Story 1 complete. Operators can upload configs, create snapshots, and receive structured validation reports. This is the MVP.

---

## Phase 4: User Story 2 — Reachability Testing (Priority: P2)

**Goal**: Operators can test whether traffic flows between two endpoints, seeing the forwarding path, ACL decisions, and permit/deny status.

**Independent Test**: Upload known configurations, run reachability queries for permitted traffic, denied traffic, multi-path scenarios, and non-routable addresses. Verify results match expected forwarding behavior per acceptance scenarios 1-4 in spec.md.

### Implementation for User Story 2

- [x] T014 [US2] Implement test_reachability tool that builds a HeaderConstraints object from src_ip, dst_ip, protocol, dst_port parameters and runs bf.q.traceroute() in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T015 [US2] Implement trace result parser that converts pybatfish traceroute DataFrame into structured ReachabilityResult with disposition, traces, hops, and per-hop steps in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T016 [US2] Add input validation for test_reachability (validate IP addresses, port range 1-65535, require dst_port for TCP/UDP) in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T017 [US2] Add GAIT logging call to test_reachability tool in mcp-servers/batfish-mcp/batfish_mcp_server.py

**Checkpoint**: User Stories 1 and 2 both work independently. Operators can upload, validate, and test reachability.

---

## Phase 5: User Story 3 — ACL and Firewall Rule Trace (Priority: P3)

**Goal**: Operators can trace a specific packet through ACLs and firewall rules on a device to determine which rule permits or denies the traffic.

**Independent Test**: Upload configs with known ACLs, trace packets that should be permitted, denied, and fall through to implicit deny. Verify correct matching rule identification per acceptance scenarios 1-4 in spec.md.

### Implementation for User Story 3

- [x] T018 [US3] Implement trace_acl tool that runs bf.q.testFilters() with device, filter_name, and packet header parameters and returns AclTraceResult with action, matching_line, and line_number in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T019 [US3] Implement ACL trace result parser that extracts the specific matching rule, line number, and permit/deny action from the pybatfish testFilters DataFrame in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T020 [US3] Add input validation for trace_acl (validate device exists in snapshot, filter_name exists on device, valid packet headers) in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T021 [US3] Add GAIT logging call to trace_acl tool in mcp-servers/batfish-mcp/batfish_mcp_server.py

**Checkpoint**: User Stories 1, 2, and 3 all work independently.

---

## Phase 6: User Story 4 — Differential Analysis (Priority: P4)

**Goal**: Operators can compare two snapshots and see exactly what changed in routing, reachability, and ACL behavior.

**Independent Test**: Create two snapshots with known differences (added route, removed ACL rule, changed BGP path), run differential analysis, and verify all changes are correctly identified per acceptance scenarios 1-4 in spec.md.

### Implementation for User Story 4

- [x] T022 [US4] Implement diff_configs tool that sets reference and candidate snapshots via bf.set_snapshot() and bf.set_reference_snapshot(), then runs bf.q.differentialReachability() in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T023 [US4] Implement route diff logic that compares bf.q.routes() output between two snapshots and categorizes routes as ADDED, REMOVED, or CHANGED in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T024 [US4] Implement diff result formatter that produces structured DiffResult with route_diffs, reachability_diffs, and summary counts in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T025 [US4] Add input validation for diff_configs (validate both snapshots exist, handle identical snapshots gracefully) in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T026 [US4] Add GAIT logging call to diff_configs tool in mcp-servers/batfish-mcp/batfish_mcp_server.py

**Checkpoint**: User Stories 1-4 all work independently.

---

## Phase 7: User Story 5 — Configuration Compliance Checking (Priority: P5)

**Goal**: Operators can validate device configurations against organizational policy rules and identify non-compliant devices.

**Independent Test**: Upload configs that intentionally violate each supported policy type, run compliance checks, and verify each violation is flagged with device name, element, and description per acceptance scenarios 1-4 in spec.md.

### Implementation for User Story 5

- [x] T027 [US5] Implement check_compliance tool that dispatches to the correct Batfish query based on policy_type parameter in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T028 [P] [US5] Implement interface_descriptions compliance check using bf.q.interfaceProperties() to find interfaces without descriptions in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T029 [P] [US5] Implement no_default_route compliance check using bf.q.routes() to find devices with 0.0.0.0/0 routes in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T030 [P] [US5] Implement ntp_configured compliance check using bf.q.nodeProperties() to find devices without NTP servers in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T031 [P] [US5] Implement no_shutdown_interfaces compliance check using bf.q.interfaceProperties() to find administratively down interfaces in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T032 [P] [US5] Implement bgp_sessions_established and ospf_adjacencies compliance checks using bf.q.bgpSessionStatus() and bf.q.ospfSessionCompatibility() in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T033 [US5] Add unsupported policy type handling that returns clear message instead of error (acceptance scenario 4) in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T034 [US5] Add GAIT logging call to check_compliance tool in mcp-servers/batfish-mcp/batfish_mcp_server.py

**Checkpoint**: All 5 user stories complete and independently functional.

---

## Phase 8: Polish & Cross-Cutting Concerns (Artifact Coherence)

**Purpose**: Documentation, artifact coherence checklist items, and integration with the broader NetGeniusClaw ecosystem

- [x] T035 [P] Create MCP server README with tool inventory, environment variables, transport protocol, and installation instructions in mcp-servers/batfish-mcp/README.md
- [x] T036 [P] Create SKILL.md documenting purpose, MCP tools used, workflow steps, required environment variables, and example usage in workspace/skills/batfish-config-analysis/SKILL.md
- [x] T037 [P] Update .env.example with BATFISH_HOST, BATFISH_PORT, and BATFISH_NETWORK variables with descriptions in .env.example
- [x] T038 [P] Update TOOLS.md with Batfish MCP server infrastructure reference in TOOLS.md
- [x] T039 [P] Update SOUL.md with batfish-config-analysis skill definition and capability summary in SOUL.md
- [x] T040 Update README.md with Batfish MCP server description, tool count, architecture updates, and setup instructions in README.md
- [x] T041 Update scripts/install.sh with Batfish MCP server dependency installation steps (pip install pybatfish, Docker pull batfish/batfish) in scripts/install.sh
- [x] T042 Update config/openclaw.json with Batfish MCP server registration in config/openclaw.json
- [x] T043 Update ui/netclaw-visual/ with new HUD node for Batfish integration in ui/netclaw-visual/
- [x] T044 Run quickstart.md validation — follow all steps in specs/002-batfish-mcp-server/quickstart.md and verify end-to-end workflow
- [x] T045 Verify existing NetGeniusClaw skills and MCP servers remain functional after addition (backwards compatibility check per SC-007)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **User Stories (Phases 3-7)**: All depend on Phase 2 completion
  - User stories can proceed sequentially in priority order (P1 through P5)
  - US2-US5 all depend on upload_snapshot from US1 (shared snapshot creation)
  - US4 (diff_configs) requires ability to create multiple snapshots (US1)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories. This IS the MVP.
- **US2 (P2)**: Depends on upload_snapshot from US1 (needs a snapshot to query)
- **US3 (P3)**: Depends on upload_snapshot from US1 (needs a snapshot to query)
- **US4 (P4)**: Depends on upload_snapshot from US1 (needs two snapshots to compare)
- **US5 (P5)**: Depends on upload_snapshot from US1 (needs a snapshot to check)

**Note**: US2, US3, and US5 can run in parallel after US1 completes. US4 also only needs US1 but is lower priority.

### Within Each User Story

- Core tool implementation first
- Result parsing/formatting second
- Input validation third
- GAIT logging last (depends on working tool)

### Parallel Opportunities

- T003, T004 can run in parallel (Phase 1)
- T028, T029, T030, T031, T032 can run in parallel (Phase 7 compliance checks — all different policy types, same file but independent functions)
- T035, T036, T037, T038, T039 can run in parallel (Phase 8 — all different files)
- After US1 completes: US2, US3, and US5 can start in parallel

---

## Parallel Example: User Story 5

```bash
# Launch all compliance check implementations together (different functions, same file, no dependencies):
Task: T028 "Implement interface_descriptions compliance check"
Task: T029 "Implement no_default_route compliance check"
Task: T030 "Implement ntp_configured compliance check"
Task: T031 "Implement no_shutdown_interfaces compliance check"
Task: T032 "Implement bgp_sessions_established and ospf_adjacencies compliance checks"
```

---

## Parallel Example: Phase 8 Artifact Coherence

```bash
# Launch all documentation updates together (all different files):
Task: T035 "Create MCP server README"
Task: T036 "Create SKILL.md"
Task: T037 "Update .env.example"
Task: T038 "Update TOOLS.md"
Task: T039 "Update SOUL.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T009)
3. Complete Phase 3: User Story 1 (T010-T013)
4. **STOP and VALIDATE**: Upload configs to Batfish, run validate_config, verify structured reports
5. Deploy/demo if ready — this alone provides significant value

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready
2. Add US1 (upload + validate) -> Test independently -> MVP
3. Add US2 (reachability) -> Test independently -> Deploy/Demo
4. Add US3 (ACL trace) -> Test independently -> Deploy/Demo
5. Add US4 (diff analysis) -> Test independently -> Deploy/Demo
6. Add US5 (compliance) -> Test independently -> Deploy/Demo
7. Complete Phase 8 (artifact coherence) -> Feature complete

### Single Developer Strategy

Work sequentially through priorities:
1. Phase 1 + Phase 2: ~1 session
2. US1 (MVP): ~1 session
3. US2 + US3: ~1 session (related packet analysis tools)
4. US4 + US5: ~1 session (comparison and compliance tools)
5. Phase 8 (polish): ~1 session

---

## Notes

- [P] tasks = different files or independent functions, no blocking dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable after completion
- All 6 MCP tools live in a single file (mcp-servers/batfish-mcp/batfish_mcp_server.py) following NetGeniusClaw convention
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
