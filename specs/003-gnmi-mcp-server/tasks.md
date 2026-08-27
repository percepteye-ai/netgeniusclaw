# Tasks: gNMI Streaming Telemetry MCP Server

**Input**: Design documents from `/specs/003-gnmi-mcp-server/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, directory structure, and dependency configuration

- [X] T001 Create MCP server directory structure: mcp-servers/gnmi-mcp/ with empty __init__.py
- [X] T002 Create requirements.txt with dependencies (fastmcp, grpcio, grpcio-tools, pygnmi, protobuf, cryptography, pydantic) in mcp-servers/gnmi-mcp/requirements.txt
- [X] T003 [P] Create skill directory structure: workspace/skills/gnmi-telemetry/
- [X] T004 [P] Create Dockerfile for gnmi-mcp server in mcp-servers/gnmi-mcp/Dockerfile

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement Pydantic data models for GnmiTarget, YangPath, GnmiGetRequest, GnmiGetResponse, PathResult, GnmiSetRequest, GnmiSetResponse, SetOperation, SubscriptionRequest, Subscription, SubscriptionUpdate, YangCapability in mcp-servers/gnmi-mcp/models.py
- [X] T006 Implement vendor dialect abstraction with default ports, encodings, path prefixes, and origin handling for Cisco IOS-XR, Juniper, Arista, Nokia SR OS in mcp-servers/gnmi-mcp/vendor_dialects.py
- [X] T007 Implement gNMI client wrapper using pygnmi with TLS configuration (mandatory TLS, mTLS support, CA cert verification, skip-verify for lab mode), connection management, and encoding negotiation in mcp-servers/gnmi-mcp/gnmi_client.py
- [X] T008 Implement target configuration loader that reads GNMI_TARGETS JSON array and TLS env vars (GNMI_TLS_CA_CERT, GNMI_TLS_CLIENT_CERT, GNMI_TLS_CLIENT_KEY, GNMI_TLS_SKIP_VERIFY) from environment variables in mcp-servers/gnmi-mcp/gnmi_client.py
- [X] T009 Implement YANG path parsing and validation utility (path must start with /, no consecutive slashes, key-value selector validation) in mcp-servers/gnmi-mcp/yang_utils.py
- [X] T010 Implement response size handling with configurable truncation threshold (default 1MB via GNMI_MAX_RESPONSE_SIZE env var) in mcp-servers/gnmi-mcp/gnmi_client.py
- [X] T011 Implement structured error handling for all gNMI error types (CONNECTION_ERROR, TLS_ERROR, AUTH_ERROR, PATH_ERROR, ENCODING_ERROR, RPC_ERROR) that never exposes credentials or certificate contents in mcp-servers/gnmi-mcp/gnmi_client.py
- [X] T012 Initialize FastMCP server skeleton with stdio transport, initialize and tools/list lifecycle methods in mcp-servers/gnmi-mcp/gnmi_mcp_server.py

**Checkpoint**: Foundation ready - gNMI client can connect to devices with TLS, vendor dialects are configured, models are defined. User story implementation can now begin.

---

## Phase 3: User Story 1 - Query Device State via gNMI Get (Priority: P1) MVP

**Goal**: Enable operators to query device operational and configuration state using structured YANG model paths via gNMI Get, receiving machine-parseable model-driven data instead of unstructured CLI output.

**Independent Test**: Issue a gNMI Get request for a known YANG path (e.g., openconfig-interfaces) against a single gNMI-capable device and verify structured JSON data is returned with correct values matching the device state.

### Implementation for User Story 1

- [X] T013 [US1] Implement gnmi_get MCP tool that accepts target name, YANG paths list, optional encoding override, and optional data_type filter (ALL/CONFIG/STATE/OPERATIONAL) in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T014 [US1] Implement gnmi_list_targets MCP tool that returns all configured targets with name, host, port, vendor, and connection reachability status in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T015 [US1] Implement response formatting that converts protobuf/gNMI-encoded data into structured human-readable output organized by YANG module and subtree in mcp-servers/gnmi-mcp/gnmi_client.py
- [X] T016 [US1] Implement truncation handling in gnmi_get: when response exceeds size threshold, return first portion with truncation notice and total size in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T017 [US1] Implement GAIT audit logging for gNMI Get operations (operator identity, target device, YANG paths, timestamp, result status) via gait_mcp integration in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T018 [US1] Handle error cases: unreachable device (CONNECTION_ERROR), TLS handshake failure (TLS_ERROR), invalid YANG path (PATH_ERROR), encoding mismatch (ENCODING_ERROR) with descriptive messages in mcp-servers/gnmi-mcp/gnmi_mcp_server.py

**Checkpoint**: Operators can connect to any supported vendor device and retrieve structured state data via gNMI Get. This is the MVP deliverable.

---

## Phase 4: User Story 2 - Subscribe to Real-Time Telemetry Streams (Priority: P2)

**Goal**: Enable operators to set up streaming telemetry subscriptions for YANG paths (interface counters, BGP state changes, CPU/memory) and receive real-time state change notifications.

**Independent Test**: Create a STREAM subscription for interface oper-status on a device, toggle an interface, and verify the subscription delivers the state change notification within seconds.

### Implementation for User Story 2

- [X] T019 [US2] Implement subscription manager with in-memory tracking, UUID assignment, max 50 concurrent subscription limit (configurable via GNMI_MAX_SUBSCRIPTIONS), and asyncio task management in mcp-servers/gnmi-mcp/subscription_manager.py
- [X] T020 [US2] Implement gnmi_subscribe MCP tool that accepts target, YANG paths, mode (SAMPLE/ON_CHANGE), and sample_interval_seconds; creates and tracks a new subscription; returns subscription UUID in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T021 [US2] Implement gnmi_unsubscribe MCP tool that cleanly terminates the gRPC stream for a given subscription UUID and confirms cancellation in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T022 [US2] Implement gnmi_get_subscriptions MCP tool that lists all active subscriptions with ID, target, paths, mode, status, creation time, and last update time in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T023 [US2] Implement gnmi_get_subscription_updates MCP tool that returns the latest N updates (default 10) from a specific subscription with path, value, and timestamp in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T024 [US2] Implement subscription error handling: report subscription loss on device unreachability with device identity and reason; handle unsupported YANG paths for streaming; enforce subscription limit with SUBSCRIPTION_LIMIT error in mcp-servers/gnmi-mcp/subscription_manager.py
- [X] T025 [US2] Implement GAIT audit logging for subscription operations (create, cancel) with subscription ID, target, paths, mode, and timestamp in mcp-servers/gnmi-mcp/gnmi_mcp_server.py

**Checkpoint**: Operators can create SAMPLE and ON_CHANGE telemetry subscriptions, list active subscriptions, retrieve updates, and cancel subscriptions. Subscription failures are reported clearly.

---

## Phase 5: User Story 3 - Apply Configuration via gNMI Set (Priority: P3)

**Goal**: Enable operators to apply configuration changes via gNMI Set using structured YANG models, with mandatory ITSM gating via ServiceNow Change Request approval.

**Independent Test**: Request a gNMI Set to change an interface description, verify the system checks for a valid ServiceNow CR number before proceeding, apply the change, and confirm the new description via a subsequent gNMI Get.

### Implementation for User Story 3

- [X] T026 [US3] Implement ITSM gate module that validates ServiceNow Change Request number format (CHG\d+) and verifies CR is in "Implement" state via servicenow-mcp MCP tool calls in mcp-servers/gnmi-mcp/itsm_gate.py
- [X] T027 [US3] Implement gnmi_set MCP tool that accepts target, change_request_number, updates (merge), replaces (overwrite), and deletes operations in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T028 [US3] Implement read-before-write workflow in gnmi_set: capture baseline state via gNMI Get before applying Set, then verify via gNMI Get after Set to confirm changes applied correctly in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T029 [US3] Implement ITSM rejection handling: refuse operation with clear message when no CR provided or CR not in "Implement" state; halt immediately if CR is withdrawn mid-execution in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T030 [US3] Implement Set error handling: return device error responses (invalid path, invalid value, type mismatch) in actionable format; report partial failures showing which operations succeeded and which failed in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T031 [US3] Implement GAIT audit logging for gNMI Set operations including CR number, operator, target, YANG paths, operation type (update/replace/delete), baseline state, result state, and timestamp in mcp-servers/gnmi-mcp/gnmi_mcp_server.py

**Checkpoint**: Operators can apply configuration changes via gNMI Set with full ITSM gating, read-before-write verification, and comprehensive audit logging. Operations are refused without a valid CR.

---

## Phase 6: User Story 4 - Browse YANG Model Capabilities (Priority: P4)

**Goal**: Enable operators to explore what YANG modules and paths are available on a specific device so they can construct valid gNMI requests without consulting external documentation.

**Independent Test**: Request "show YANG capabilities on router1" and verify the system returns a list of supported YANG modules with version, organization, and available paths.

### Implementation for User Story 4

- [X] T032 [US4] Implement gnmi_capabilities MCP tool that retrieves supported YANG modules (name, version, organization) and supported encodings from a device via gNMI Capabilities RPC in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T033 [US4] Implement gnmi_browse_yang_paths MCP tool that explores available YANG paths under a specific module on a device with configurable depth (default 3) using gNMI Get with prefix paths in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T034 [US4] Handle edge cases: device does not support Capabilities RPC (clear error message); vendor-specific vs OpenConfig model differentiation in capabilities listing in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T035 [US4] Implement GAIT audit logging for capabilities and browse operations with target, module, and timestamp in mcp-servers/gnmi-mcp/gnmi_mcp_server.py

**Checkpoint**: Operators can discover YANG model capabilities and browse available paths on any supported device. Model lists clearly distinguish shared OpenConfig models from vendor-native models.

---

## Phase 7: User Story 5 - Compare gNMI State vs CLI State (Priority: P5)

**Goal**: Enable operators to compare gNMI-retrieved state against CLI-retrieved state (via pyATS MCP) for validation during the transition from CLI to gNMI.

**Independent Test**: Request "compare interface state on router1 between gNMI and CLI" and verify a side-by-side comparison showing matching and differing fields.

### Implementation for User Story 5

- [X] T036 [US5] Implement gnmi_compare_with_cli MCP tool that accepts target and data_type (interfaces, bgp_neighbors, routes) in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T037 [US5] Implement data retrieval orchestration: call gnmi_get for gNMI data and pyATS_MCP tools for CLI data, then normalize both into comparable structures in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T038 [US5] Implement field-level comparison logic with variance tolerance for timing-sensitive fields (counters, uptime) flagged as "expected variance" rather than true discrepancies in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T039 [US5] Handle edge cases: device reachable via gNMI but not CLI (return gNMI data with unavailability message); device reachable via CLI but not gNMI (return CLI data with unavailability message) in mcp-servers/gnmi-mcp/gnmi_mcp_server.py
- [X] T040 [US5] Implement GAIT audit logging for comparison operations with target, data type, and result summary in mcp-servers/gnmi-mcp/gnmi_mcp_server.py

**Checkpoint**: Operators can validate gNMI data accuracy by comparing it against CLI data for interfaces, BGP neighbors, and routes, with clear field-level results.

---

## Phase 8: Polish & Cross-Cutting Concerns (Artifact Coherence)

**Purpose**: Artifact coherence checklist completion, documentation, and cross-cutting improvements required by the NetGeniusClaw Constitution (Principle XI)

- [X] T041 [P] Create MCP server README with tool inventory, environment variables, transport protocol, installation instructions, and usage examples in mcp-servers/gnmi-mcp/README.md
- [X] T042 [P] Create SKILL.md documenting purpose, MCP tools used, workflow steps, required environment variables, and example usage in workspace/skills/gnmi-telemetry/SKILL.md
- [X] T043 [P] Update .env.example with all new gNMI environment variables (GNMI_TARGETS, GNMI_TLS_CA_CERT, GNMI_TLS_CLIENT_CERT, GNMI_TLS_CLIENT_KEY, GNMI_TLS_SKIP_VERIFY, GNMI_MAX_RESPONSE_SIZE, GNMI_MAX_SUBSCRIPTIONS) with descriptions in .env.example
- [X] T044 [P] Update config/openclaw.json to register gnmi-mcp server with command, args, and env configuration in config/openclaw.json
- [X] T045 [P] Update README.md with gNMI MCP server description, architecture reference, tool count update, and setup instructions in README.md
- [X] T046 [P] Update SOUL.md with gnmi-telemetry skill definition, identity references, and capability summary in SOUL.md
- [X] T047 [P] Update TOOLS.md with gNMI infrastructure reference (tools, vendor support, YANG model support) in TOOLS.md
- [X] T048 [P] Update scripts/install.sh with installation steps for gNMI dependencies (grpcio, pygnmi, protobuf, cryptography) in scripts/install.sh
- [X] T049 [P] Update ui/netclaw-visual/ with Three.js HUD node for gNMI MCP server integration status in ui/netclaw-visual/
- [X] T050 Verify existing NetGeniusClaw skills and MCP servers remain functional after addition (backwards compatibility check per SC-009)
- [X] T051 Run quickstart.md validation: follow all steps in specs/003-gnmi-mcp-server/quickstart.md and verify each operation works as documented
- [X] T052 Record GAIT session log for feature completion

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion - MVP deliverable
- **User Story 2 (Phase 4)**: Depends on Phase 2 completion - can run in parallel with US1
- **User Story 3 (Phase 5)**: Depends on Phase 2 completion - can run in parallel with US1/US2
- **User Story 4 (Phase 6)**: Depends on Phase 2 completion - can run in parallel with US1/US2/US3
- **User Story 5 (Phase 7)**: Depends on Phase 2 and Phase 3 (US1, needs gnmi_get working) - also requires pyATS MCP server availability
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Foundational phase only. No dependencies on other stories.
- **User Story 2 (P2)**: Foundational phase only. Independent of other stories.
- **User Story 3 (P3)**: Foundational phase only. Independent of other stories (uses gNMI Get internally for baseline/verify but implements its own calls).
- **User Story 4 (P4)**: Foundational phase only. Independent of other stories.
- **User Story 5 (P5)**: Depends on US1 (needs gnmi_get functionality) and external pyATS_MCP availability.

### Within Each User Story

- Models/infrastructure before service logic
- Core implementation before error handling
- Error handling before GAIT logging
- Story complete before moving to next priority

### Parallel Opportunities

- T003, T004 can run in parallel with T001, T002 (different directories)
- T005, T006, T009 can run in parallel (different files, no dependencies)
- T007, T008, T010, T011 are sequential (same file: gnmi_client.py)
- T013, T014 can run in parallel (different tool implementations, same file but independent functions)
- T019 can run in parallel with Phase 3 tasks (different file: subscription_manager.py)
- T032, T033 can run in parallel (independent tool implementations)
- T036-T040 are sequential (same feature, shared comparison logic)
- All Phase 8 [P] tasks (T041-T049) can run in parallel (different files)

---

## Parallel Example: User Story 1

```bash
# After Foundational phase completes, launch US1 tasks:
Task T013: "Implement gnmi_get MCP tool in mcp-servers/gnmi-mcp/gnmi_mcp_server.py"
Task T014: "Implement gnmi_list_targets MCP tool in mcp-servers/gnmi-mcp/gnmi_mcp_server.py"
# (T013 and T014 are independent tool implementations)

# Then sequential:
Task T015: "Implement response formatting in mcp-servers/gnmi-mcp/gnmi_client.py"
Task T016: "Implement truncation handling in mcp-servers/gnmi-mcp/gnmi_mcp_server.py"
Task T017: "Implement GAIT audit logging in mcp-servers/gnmi-mcp/gnmi_mcp_server.py"
Task T018: "Handle error cases in mcp-servers/gnmi-mcp/gnmi_mcp_server.py"
```

## Parallel Example: Artifact Coherence (Phase 8)

```bash
# All artifact coherence tasks can run in parallel (different files):
Task T041: "Create README in mcp-servers/gnmi-mcp/README.md"
Task T042: "Create SKILL.md in workspace/skills/gnmi-telemetry/SKILL.md"
Task T043: "Update .env.example"
Task T044: "Update config/openclaw.json"
Task T045: "Update README.md"
Task T046: "Update SOUL.md"
Task T047: "Update TOOLS.md"
Task T048: "Update scripts/install.sh"
Task T049: "Update ui/netclaw-visual/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T012) - CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T013-T018)
4. **STOP and VALIDATE**: Test gNMI Get against a real device
5. Deploy/demo if ready - operators can query device state via gNMI

### Incremental Delivery

1. Setup + Foundational -> Foundation ready
2. Add User Story 1 -> Test gNMI Get independently -> Deploy (MVP!)
3. Add User Story 2 -> Test subscriptions independently -> Deploy
4. Add User Story 3 -> Test gNMI Set with ITSM gate -> Deploy
5. Add User Story 4 -> Test YANG browsing -> Deploy
6. Add User Story 5 -> Test CLI comparison -> Deploy
7. Complete Phase 8: Artifact coherence -> Final PR ready

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (gNMI Get) + User Story 4 (Capabilities)
   - Developer B: User Story 2 (Subscriptions)
   - Developer C: User Story 3 (gNMI Set + ITSM)
3. After US1 complete: Developer D can start User Story 5 (Comparison)
4. All developers: Phase 8 artifact coherence (parallel on different files)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All MCP tools must follow the contract schemas defined in specs/003-gnmi-mcp-server/contracts/mcp-tools.md
- All error responses must follow the error code table in the contracts
- GAIT logging is required for every gNMI operation per Constitution Principle IV
- TLS is mandatory for all device connections per Constitution Principle IX and FR-010
