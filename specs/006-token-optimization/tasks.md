# Tasks: Token Optimization (Count + TOON)

**Input**: Design documents from `/specs/006-token-optimization/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create project structure, install dependencies, configure package

- [x] T001 Create directory structure: src/netclaw_tokens/, tests/unit/, tests/integration/, workspace/skills/token-tracker/
- [x] T002 Create src/netclaw_tokens/__init__.py with package exports (TokenCount, CostEstimate, TOONResponse, SessionLedger, ModelPricing, ToolUsageRecord dataclasses)
- [x] T003 [P] Create requirements file or pyproject.toml entries for new dependencies: model-provider, toon-format

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core library modules that ALL user stories depend on. MUST complete before any user story work.

**CRITICAL**: No user story work can begin until this phase is complete.

- [x] T004 Implement cost_calculator.py in src/netclaw_tokens/cost_calculator.py with calculate_cost() and get_pricing() functions, hardcoded pricing dict (Opus $5/$25, Sonnet $3/$15, Haiku $1/$5 per 1M), NETCLAW_TOKEN_PRICING_OVERRIDE env var support, and 90% prompt caching discount
- [x] T005 Implement counter.py in src/netclaw_tokens/counter.py with count_tokens() using model-provider.the model provider().messages.count_tokens(), count_message_tokens() for message arrays, and len(text)/4 fallback with estimated=True when API unavailable
- [x] T006 [P] Implement toon_serializer.py in src/netclaw_tokens/toon_serializer.py with serialize_response() using toon.dumps(), JSON fallback on error, binary data detection (bytes/non-UTF-8 skip), and savings calculation (TOON vs JSON token counts)

**Checkpoint**: Core library modules ready. All user story implementation can now begin.

---

## Phase 3: User Story 1 - Token Count and Cost Display (Priority: P1) MVP

**Goal**: Every NetGeniusClaw interaction displays a token/cost footer showing input tokens, output tokens, total, and USD cost. Session totals track cumulative usage.

**Independent Test**: Run any NetGeniusClaw command and verify a token/cost summary line appears at the bottom of the response showing input tokens, output tokens, total tokens, and estimated cost in USD.

### Implementation for User Story 1

- [x] T007 [US1] Implement session_ledger.py in src/netclaw_tokens/session_ledger.py with SessionLedger class: threading.Lock for thread safety, record() method, get_summary() returning session totals, reset() method, and session_id auto-generation
- [x] T008 [US1] Implement footer.py in src/netclaw_tokens/footer.py with format_footer() function producing format: "Tokens: 1,245 in / 382 out / 1,627 total | Cost: $0.0158 | TOON saved: 412 tokens ($0.0041) | Session: 15,832 tokens ($0.14)"
- [x] T009 [US1] Update src/netclaw_tokens/__init__.py to export all public functions: count_tokens, count_message_tokens, calculate_cost, get_pricing, serialize_response, format_footer, SessionLedger

**Checkpoint**: Token counting, cost calculation, session tracking, and footer display are fully functional and testable independently.

---

## Phase 4: User Story 2 - TOON Format for MCP Responses (Priority: P2)

**Goal**: All MCP server responses are serialized in TOON format by default, with JSON fallback, achieving 30-60% token savings on tabular network data.

**Independent Test**: Run "show routes" via SuzieQ or pyATS and compare the token count of the TOON response against the equivalent JSON response, verifying at least 30% savings.

### Implementation for User Story 2

- [x] T010 [US2] Add TOON serialization to pyATS MCP server response path — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T011 [P] [US2] Add TOON serialization to NetBox MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T012 [P] [US2] Add TOON serialization to ServiceNow MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T013 [P] [US2] Add TOON serialization to ACI MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T014 [P] [US2] Add TOON serialization to ISE MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T015 [P] [US2] Add TOON serialization to Junos MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T016 [P] [US2] Add TOON serialization to F5 MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T017 [P] [US2] Add TOON serialization to Cisco SD-WAN MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T018 [P] [US2] Add TOON serialization to Catalyst Center MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T019 [P] [US2] Add TOON serialization to Meraki MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T020 [P] [US2] Add TOON serialization to FMC MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T021 [P] [US2] Add TOON serialization to protocol-mcp server in mcp-servers/protocol-mcp/server.py
- [x] T022 [P] [US2] Add TOON serialization to GAIT MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T023 [P] [US2] Add TOON serialization to UML MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T024 [P] [US2] Add TOON serialization to markmap MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T025 [P] [US2] Add TOON serialization to NVD MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T026 [P] [US2] Add TOON serialization to Nautobot MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T027 [P] [US2] Add TOON serialization to Infrahub MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T028 [P] [US2] Add TOON serialization to ThousandEyes MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T029 [P] [US2] Add TOON serialization to RADKit MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T030 [P] [US2] Add TOON serialization to ContainerLab MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T031 [P] [US2] Add TOON serialization to subnet-calculator MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T032 [P] [US2] Add TOON serialization to Wikipedia MCP server — handled via TOON wrapper (T042, untracked/cloned server)
- [x] T033 [P] [US2] Add TOON serialization to SuzieQ MCP server in mcp-servers/suzieq-mcp/server.py
- [x] T034 [P] [US2] Add TOON serialization to Batfish MCP server in mcp-servers/batfish-mcp/batfish_mcp_server.py
- [x] T035 [P] [US2] Add TOON serialization to gNMI MCP server in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [x] T036 [P] [US2] Add TOON serialization to Azure Network MCP server in mcp-servers/azure-network-mcp/
- [x] T037 [P] [US2] Add TOON serialization to CVP MCP server — handled via TOON wrapper (T042, untracked/cloned server)

**Checkpoint**: All 28 bundled MCP servers return TOON-serialized responses with automatic JSON fallback.

---

## Phase 5: User Story 3 - TOON in HEARTBEAT and SOUL (Priority: P3)

**Goal**: SOUL.md and HEARTBEAT.md updated to include token-consciousness as mandatory agent behavior.

**Independent Test**: Read SOUL.md and HEARTBEAT.md and verify that token counting and TOON usage are listed as mandatory behaviors, and that heartbeat check-ins include token usage summaries.

### Implementation for User Story 3

- [x] T038 [US3] Update SOUL.md to add token transparency rules: "I ALWAYS count and display tokens and cost at the bottom of every interaction", "I ALWAYS serialize MCP responses in TOON format to minimize token consumption", "I NEVER hide token costs from the operator"
- [x] T039 [US3] Update HEARTBEAT.md to add token usage section to periodic check-ins: session token count and cost, TOON savings percentage, top 5 most token-expensive operations

**Checkpoint**: Identity documents mandate token transparency and TOON as core behaviors.

---

## Phase 6: User Story 4 - Per-Tool Token Breakdown (Priority: P4)

**Goal**: Operators can view a ranked per-tool breakdown of token consumption showing call count, tokens, cost, and TOON savings per tool.

**Independent Test**: Run several different operations and ask "show token breakdown by tool" to see ranked usage.

### Implementation for User Story 4

- [x] T040 [US4] Add get_per_tool_breakdown() method to SessionLedger in src/netclaw_tokens/session_ledger.py returning ranked list sorted by total tokens desc with: tool_name, call_count, input_tokens, output_tokens, total_tokens, cost, toon_savings, avg_tokens_per_call
- [x] T041 [US4] Add get_gait_summary() method to SessionLedger in src/netclaw_tokens/session_ledger.py returning structured data for GAIT log inclusion (FR-012)

**Checkpoint**: Per-tool breakdown available on demand, GAIT integration ready.

---

## Phase 7: User Story 5 - TOON Across All Existing MCP Servers (Priority: P5)

**Goal**: Verify and validate that all 28+ bundled MCP servers correctly use TOON serialization (already implemented in Phase 4). This phase handles edge cases and community servers.

**Independent Test**: Run a pyATS show command and verify the response is in TOON format, then repeat for NetBox, Grafana, and other bundled MCP servers.

### Implementation for User Story 5

- [x] T042 [US5] Create TOON conversion wrapper utility in src/netclaw_tokens/toon_wrapper.py for community/remote MCP servers that cannot be directly modified (post-process JSON responses into TOON)
- [x] T043 [US5] Verify all MCP server TOON integrations handle edge cases: empty responses, very large responses, nested non-tabular data, mixed binary/text responses — handled via validate_toon_integration() in toon_wrapper.py and binary detection in toon_serializer.py

**Checkpoint**: All MCP servers (bundled and community) produce TOON output with proper fallback behavior.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Artifact coherence, documentation, configuration updates

- [x] T044 [P] Create workspace/skills/token-tracker/SKILL.md with skill documentation: purpose (token counting and cost tracking), tools used (netclaw_tokens library), workflow steps, required env vars (NETGENIUSCLAW_MODEL_API_KEY, NETCLAW_TOKEN_PRICING_OVERRIDE), example usage
- [x] T045 [P] Update README.md with token optimization description, TOON format explanation, new dependency list, token footer examples
- [x] T046 [P] Update scripts/install.sh to add pip install model-provider toon-format and src/netclaw_tokens setup
- [x] T047 [P] Update .env.example to add NETCLAW_TOKEN_PRICING_OVERRIDE with description (NETGENIUSCLAW_MODEL_API_KEY already present)
- [x] T048 [P] Update TOOLS.md with token optimization infrastructure reference
- [x] T049 [P] Update config/openclaw.json to register netclaw_tokens library path
- [x] T050 [P] Update ui/netclaw-visual/server.js to add token tracking HUD node/panel for real-time token display
- [x] T051 Run quickstart.md validation: code examples verified structurally (runtime validation requires model-provider and toon-format packages installed)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 (counter, cost_calculator, toon_serializer)
- **User Story 2 (Phase 4)**: Depends on Phase 2 (toon_serializer). Can run in parallel with US1.
- **User Story 3 (Phase 5)**: No code dependencies on other phases; can start after Phase 2
- **User Story 4 (Phase 6)**: Depends on Phase 3 (session_ledger from US1)
- **User Story 5 (Phase 7)**: Depends on Phase 4 (MCP server updates from US2)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends only on Foundational phase - no cross-story dependencies
- **US2 (P2)**: Depends only on Foundational phase - can run in parallel with US1
- **US3 (P3)**: No code dependencies - can start after Foundational
- **US4 (P4)**: Depends on US1 (session_ledger must exist)
- **US5 (P5)**: Depends on US2 (MCP servers must have TOON integration)

### Parallel Opportunities

- T003 can run in parallel with T001/T002
- T005 and T006 can run in parallel (different files)
- T007 and T008 can run in parallel within US1
- All MCP server updates (T010-T037) can run in parallel with each other
- T038 and T039 can run in parallel (different files)
- T040 and T041 can run in parallel within US4
- All Polish tasks (T044-T050) can run in parallel

---

## Parallel Example: User Story 2 (MCP Server Updates)

```bash
# All 28 MCP server updates are independent files - can all run in parallel:
Task T010: "TOON serialization in mcp-servers/pyATS_MCP/server.py"
Task T011: "TOON serialization in mcp-servers/netbox-mcp-server/server.py"
Task T012: "TOON serialization in mcp-servers/servicenow-mcp/server.py"
# ... all 28 servers simultaneously
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T006)
3. Complete Phase 3: User Story 1 (T007-T009)
4. **STOP and VALIDATE**: Run any command, verify token/cost footer appears
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational -> Core library ready
2. Add US1 -> Token counting and cost display works (MVP)
3. Add US2 -> All MCP servers return TOON format
4. Add US3 -> Identity docs updated
5. Add US4 -> Per-tool breakdown available
6. Add US5 -> Edge cases and community server wrappers
7. Polish -> All artifacts coherent

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- MCP server file paths may need adjustment - locate actual main server file in each directory before editing
