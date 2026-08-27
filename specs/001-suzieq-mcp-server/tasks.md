# Tasks: SuzieQ MCP Server

**Input**: Design documents from `/specs/001-suzieq-mcp-server/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/mcp-tools.md, quickstart.md

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, directory structure, and dependency configuration

- [x] T001 Create MCP server directory structure: `mcp-servers/suzieq-mcp/`
- [x] T002 Create requirements.txt with dependencies (mcp, httpx, python-dotenv) in `mcp-servers/suzieq-mcp/requirements.txt`
- [x] T003 [P] Create skill directory: `workspace/skills/suzieq-observability/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Implement SuzieQ REST API client class with connection setup, authentication (access_token), SSL configuration, and base request method in `mcp-servers/suzieq-mcp/suzieq_client.py`. Must read SUZIEQ_API_URL, SUZIEQ_API_KEY, SUZIEQ_VERIFY_SSL, SUZIEQ_TIMEOUT from environment variables. URL pattern: `{api_url}/api/v2/{table}/{verb}?access_token={key}&{filters}`
- [x] T005 Implement error handling in `mcp-servers/suzieq-mcp/suzieq_client.py`: connection errors, authentication failures (401/403), timeouts, invalid responses. Return structured error messages per contracts/mcp-tools.md error response spec. Never expose credentials in error messages.
- [x] T006 Create FastMCP server skeleton with stdio transport in `mcp-servers/suzieq-mcp/server.py`. Initialize FastMCP("suzieq-mcp"), configure logging to stderr, validate required env vars on startup (SUZIEQ_API_URL, SUZIEQ_API_KEY). Import and instantiate SuzieQClient.
- [x] T007 [P] Define known tables list and assert-capable tables constant in `mcp-servers/suzieq-mcp/suzieq_client.py`: KNOWN_TABLES = ["address", "arpnd", "bgp", "device", "devconfig", "evpnVni", "fs", "ifCounters", "interface", "inventory", "lldp", "mac", "mlag", "namespace", "network", "ospf", "route", "sqPoller", "topology", "vlan"] and ASSERT_TABLES = ["bgp", "ospf", "interface", "evpnVni"]

**Checkpoint**: Foundation ready - SuzieQ client can connect and make authenticated requests. Server skeleton runs via stdio.

---

## Phase 3: User Story 1 - Query Current Network State (Priority: P1) MVP

**Goal**: Enable querying current state of any network table (routes, interfaces, BGP, OSPF, etc.) with filtering by device, namespace, and columns.

**Independent Test**: Issue `suzieq_show(table="bgp")` and verify results return from SuzieQ with device, namespace, and table data.

### Implementation for User Story 1

- [x] T008 [US1] Implement `suzieq_show` tool in `mcp-servers/suzieq-mcp/server.py` with parameters: table (required), namespace, hostname, columns, start_time, end_time, view, filters. Build query parameters dict, call SuzieQClient.query(table, "show", params), return formatted JSON response with table name, row_count, and data array.
- [x] T009 [US1] Implement query parameter builder helper in `mcp-servers/suzieq-mcp/suzieq_client.py` that converts tool parameters (namespace, hostname, columns, start_time, end_time, view, plus additional filters string) into SuzieQ REST API query parameters dict. Parse filters string (key=value&key=value format) into dict entries.
- [x] T010 [US1] Implement response formatter in `mcp-servers/suzieq-mcp/server.py` that wraps SuzieQ JSON responses into standardized output: includes table name, verb, row_count, filters_applied, and data. Handle empty results with descriptive "No data found" message (not an error).
- [x] T011 [US1] Add stderr logging for all tool invocations in `mcp-servers/suzieq-mcp/server.py`: log table, verb, filters at INFO level on each call. Log errors at ERROR level with details but without credentials.

**Checkpoint**: User Story 1 complete. Can query any SuzieQ table with filters and get structured results.

---

## Phase 4: User Story 2 - Time-Travel Queries (Priority: P2)

**Goal**: Enable querying historical network state at a specific timestamp or within a time range.

**Independent Test**: Issue `suzieq_show(table="bgp", start_time="2026-03-25T14:00:00")` and verify results reflect historical snapshot.

### Implementation for User Story 2

- [x] T012 [US2] Extend query parameter builder in `mcp-servers/suzieq-mcp/suzieq_client.py` to handle start_time and end_time parameters. Pass as `start-time` and `end-time` query params to SuzieQ REST API. Support both ISO 8601 format and relative time strings (e.g., "1h", "2d").
- [x] T013 [US2] Extend `suzieq_show` tool in `mcp-servers/suzieq-mcp/server.py` to support `view` parameter ("latest", "all", "changes"). When start_time is provided without view, default view to "all" to show historical data. Add descriptive message when no historical data exists for requested time period.

**Checkpoint**: User Story 2 complete. Time-travel queries work via start_time/end_time on suzieq_show.

---

## Phase 5: User Story 3 - Network Assertions (Priority: P3)

**Goal**: Run validation assertions against network state (e.g., all BGP peers established, no interface errors).

**Independent Test**: Issue `suzieq_assert(table="bgp")` and verify pass/fail results with per-device details.

### Implementation for User Story 3

- [x] T014 [US3] Implement `suzieq_assert` tool in `mcp-servers/suzieq-mcp/server.py` with parameters: table (required, must be in ASSERT_TABLES), namespace, hostname. Validate table is in ASSERT_TABLES before calling API; return clear error if not. Call SuzieQClient.query(table, "assert", params).
- [x] T015 [US3] Implement assertion result formatter in `mcp-servers/suzieq-mcp/server.py` that presents pass/fail counts and per-device failure details. Handle case where table has no data (report assertion cannot be evaluated due to missing data, per spec acceptance scenario 3).

**Checkpoint**: User Story 3 complete. Can run assertions on bgp, ospf, interface, evpnVni tables.

---

## Phase 6: User Story 4 - Summarized Network Views (Priority: P4)

**Goal**: Get aggregated summary views of network tables (counts, distributions, per-device breakdowns).

**Independent Test**: Issue `suzieq_summarize(table="route")` and verify aggregated counts and distributions returned.

### Implementation for User Story 4

- [x] T016 [US4] Implement `suzieq_summarize` tool in `mcp-servers/suzieq-mcp/server.py` with parameters: table (required), namespace, hostname, start_time, end_time. Call SuzieQClient.query(table, "summarize", params). Return formatted summary statistics.
- [x] T017 [P] [US4] Implement `suzieq_unique` tool in `mcp-servers/suzieq-mcp/server.py` with parameters: table (required), column (required), namespace, hostname. Call SuzieQClient.query(table, "unique", params) with `columns={column}` in query. Return distinct values with counts.

**Checkpoint**: User Story 4 complete. Can get summarized and unique views of any table.

---

## Phase 7: User Story 5 - Network Path Analysis (Priority: P5)

**Goal**: Trace forwarding path between two endpoints through the network.

**Independent Test**: Issue `suzieq_path(namespace="dc1", source="10.0.1.1", destination="10.0.2.1")` and verify hop-by-hop path returned.

### Implementation for User Story 5

- [x] T018 [US5] Implement `suzieq_path` tool in `mcp-servers/suzieq-mcp/server.py` with parameters: namespace (required), source (required), destination (required), vrf (optional, default "default"). Call SuzieQ path endpoint: `{api_url}/api/v2/path/show?namespace={ns}&src={src}&dest={dst}&vrf={vrf}`. Return hop-by-hop path with ingress/egress interfaces. Handle gaps where unmonitored devices exist.

**Checkpoint**: User Story 5 complete. All 5 MCP tools are functional.

---

## Phase 8: Polish & Artifact Coherence

**Purpose**: Documentation, configuration, and artifact coherence checklist completion (Constitution XI)

- [x] T019 [P] Create MCP server README in `mcp-servers/suzieq-mcp/README.md` with: tool inventory (5 tools with names, descriptions, parameters), environment variables, transport protocol (stdio), installation instructions, and example usage
- [x] T020 [P] Create skill documentation in `workspace/skills/suzieq-observability/SKILL.md` with: purpose, MCP tools used (all 5), workflow steps, required environment variables, and example usage following existing SKILL.md pattern from workspace/skills/pyats-network/SKILL.md
- [x] T021 [P] Update `.env.example` with new environment variables: SUZIEQ_API_URL, SUZIEQ_API_KEY, SUZIEQ_VERIFY_SSL, SUZIEQ_TIMEOUT (with descriptions, no values)
- [x] T022 [P] Update `TOOLS.md` with SuzieQ MCP server entry: server name, 5 tools, brief descriptions
- [x] T023 [P] Update `SOUL.md` with suzieq-observability skill definition and SuzieQ MCP server capability summary
- [x] T024 [P] Update `README.md` with SuzieQ MCP server description, architecture reference, and updated tool/skill counts
- [x] T025 Update `config/openclaw.json` to register suzieq-mcp server with command, args, and env configuration
- [x] T026 [P] Update `scripts/install.sh` with SuzieQ MCP server dependency installation steps (pip install for mcp-servers/suzieq-mcp/requirements.txt)
- [x] T027 [P] Update `ui/netclaw-visual/` Three.js HUD with new SuzieQ MCP server node representing the observability integration
- [x] T028 Validate quickstart.md instructions by reviewing server startup and tool invocation flows in `specs/001-suzieq-mcp-server/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-7)**: All depend on Foundational phase completion
  - US1 (Phase 3): No dependencies on other stories
  - US2 (Phase 4): Extends US1 implementation (start_time/end_time on suzieq_show)
  - US3 (Phase 5): Independent of US1/US2 (different tool: suzieq_assert)
  - US4 (Phase 6): Independent of US1-US3 (different tools: suzieq_summarize, suzieq_unique)
  - US5 (Phase 7): Independent of US1-US4 (different tool: suzieq_path)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Foundational only. MVP target.
- **US2 (P2)**: Extends US1 (adds time parameters to suzieq_show). Must follow US1.
- **US3 (P3)**: Foundational only. Can run in parallel with US1.
- **US4 (P4)**: Foundational only. Can run in parallel with US1/US3.
- **US5 (P5)**: Foundational only. Can run in parallel with US1/US3/US4.

### Within Each User Story

- Tool implementation before response formatting
- Core functionality before edge case handling
- Story complete before moving to next priority

### Parallel Opportunities

- T002 and T003 (Setup) can run in parallel
- T004 and T007 (Foundational) can run in parallel
- US3, US4, US5 can run in parallel with each other after Foundational
- All Phase 8 tasks marked [P] can run in parallel
- T016 and T017 (US4) can run in parallel

---

## Parallel Example: User Story 1

```bash
# After Foundational phase completes:
# T008 and T009 can partially overlap (T008 defines the tool, T009 the parameter builder)
# But T010 depends on T008 and T009 for the response formatting
# T011 (logging) can be added after T008

Task: "T008 [US1] Implement suzieq_show tool in server.py"
Task: "T009 [US1] Implement query parameter builder in suzieq_client.py"
# Then:
Task: "T010 [US1] Implement response formatter in server.py"
Task: "T011 [US1] Add stderr logging in server.py"
```

## Parallel Example: Phase 8 (Polish)

```bash
# All documentation tasks can run in parallel:
Task: "T019 Create README in mcp-servers/suzieq-mcp/README.md"
Task: "T020 Create SKILL.md in workspace/skills/suzieq-observability/SKILL.md"
Task: "T021 Update .env.example"
Task: "T022 Update TOOLS.md"
Task: "T023 Update SOUL.md"
Task: "T024 Update README.md"
Task: "T026 Update scripts/install.sh"
Task: "T027 Update ui/netclaw-visual/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T007)
3. Complete Phase 3: User Story 1 (T008-T011)
4. **STOP and VALIDATE**: Test suzieq_show independently against a live SuzieQ instance
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational -> Foundation ready
2. Add US1 (suzieq_show) -> Test -> MVP!
3. Add US2 (time-travel on show) -> Test -> Enhanced queries
4. Add US3 (suzieq_assert) -> Test -> Validation capability
5. Add US4 (suzieq_summarize + suzieq_unique) -> Test -> Summary views
6. Add US5 (suzieq_path) -> Test -> Path analysis
7. Phase 8 (Polish + Artifact Coherence) -> Feature complete

### Suggested MVP Scope

User Story 1 (Query Current Network State) is the MVP. It delivers the foundational `suzieq_show` tool that all other capabilities build on. After US1 is validated, each additional story adds independent value.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All MCP tools are read-only per Constitution Principle I and FR-007
- GAIT audit logging coordinated at skill level, not embedded in MCP server
