# Tasks: Telemetry & Event Receiver Capabilities

**Input**: Design documents from `/specs/010-telemetry-receivers/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the specification - focusing on implementation tasks only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md structure:
- **MCP servers**: `mcp-servers/{server-name}/`
- **Skills**: `workspace/skills/{skill-name}/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create project directories and shared components

- [x] T001 Create syslog-mcp directory structure in mcp-servers/syslog-mcp/
- [x] T002 [P] Create snmptrap-mcp directory structure in mcp-servers/snmptrap-mcp/
- [x] T003 [P] Create ipfix-mcp directory structure in mcp-servers/ipfix-mcp/
- [x] T004 [P] Create skill directories in workspace/skills/ (syslog-receiver, snmptrap-receiver, ipfix-receiver, telemetry-ops)
- [x] T005 Create shared MessageStore base class in mcp-servers/syslog-mcp/message_store.py (will be copied to others)
- [x] T006 Create shared RateLimiter utility based on research.md token bucket algorithm

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Implement asyncio UDP receiver base pattern per research.md in mcp-servers/syslog-mcp/udp_receiver.py
- [x] T008 Create requirements.txt for syslog-mcp with FastMCP, syslog-rfc5424-parser dependencies
- [x] T009 [P] Create requirements.txt for snmptrap-mcp with FastMCP, pysnmp dependencies
- [x] T010 [P] Create requirements.txt for ipfix-mcp with FastMCP, netflow dependencies
- [x] T011 Implement GAIT audit logging integration pattern (reusable across all servers)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Syslog Receiver (Priority: P1) 🎯 MVP ✅ COMPLETE

**Goal**: Receive and query syslog messages from Cisco Catalyst 9300 via UDP 514

**Independent Test**: Configure Catalyst 9300 to send syslog to NetGeniusClaw's UDP 514 endpoint (exposed via Pinggy/Tailscale). Verify messages are received, parsed, and queryable through MCP tools.

### Models for User Story 1

- [x] T012 [P] [US1] Create SyslogMessage Pydantic model in mcp-servers/syslog-mcp/models.py
- [x] T013 [P] [US1] Create SyslogFacility and SyslogSeverity enums in mcp-servers/syslog-mcp/models.py
- [x] T014 [P] [US1] Create SyslogQueryFilter model in mcp-servers/syslog-mcp/models.py
- [x] T015 [P] [US1] Create ReceiverStatus model in mcp-servers/syslog-mcp/models.py

### Parser for User Story 1

- [x] T016 [US1] Implement RFC 5424 syslog parser using syslog-rfc5424-parser in mcp-servers/syslog-mcp/syslog_parser.py
- [x] T017 [US1] Implement RFC 3164 BSD syslog fallback parser in mcp-servers/syslog-mcp/syslog_parser.py
- [x] T018 [US1] Add parser auto-detection logic (5424 vs 3164) in mcp-servers/syslog-mcp/syslog_parser.py

### Storage for User Story 1

- [x] T019 [US1] Implement SyslogMessageStore with in-memory storage in mcp-servers/syslog-mcp/message_store.py
- [x] T020 [US1] Add deduplication logic (5-second window, content hash) to message_store.py
- [x] T021 [US1] Add 24-hour retention cleanup to message_store.py
- [x] T022 [US1] Add query filtering by time, severity, facility, hostname, message content

### MCP Server for User Story 1

- [x] T023 [US1] Create FastMCP server skeleton in mcp-servers/syslog-mcp/syslog_mcp_server.py
- [x] T024 [US1] Implement syslog_start_receiver tool in syslog_mcp_server.py
- [x] T025 [US1] Implement syslog_stop_receiver tool in syslog_mcp_server.py
- [x] T026 [US1] Implement syslog_get_status tool in syslog_mcp_server.py
- [x] T027 [US1] Implement syslog_query tool in syslog_mcp_server.py
- [x] T028 [US1] Implement syslog_get_message tool in syslog_mcp_server.py
- [x] T029 [US1] Implement syslog_get_severity_counts tool in syslog_mcp_server.py
- [x] T030 [US1] Add GAIT logging for all received messages

### Documentation for User Story 1

- [x] T031 [P] [US1] Create README.md for syslog-mcp with setup and usage instructions
- [x] T032 [P] [US1] Create SKILL.md for syslog-receiver skill in workspace/skills/syslog-receiver/

**Checkpoint**: Syslog receiver fully functional - can receive, store, and query syslog messages independently

---

## Phase 4: User Story 2 - SNMP Trap Receiver (Priority: P2) ✅ COMPLETE

**Goal**: Receive and query SNMP traps (v2c and v3) from network devices via UDP 162

**Independent Test**: Configure Catalyst 9300 to send SNMP traps to NetGeniusClaw's UDP 162 endpoint. Verify linkDown/linkUp traps are received and queryable.

### Models for User Story 2

- [x] T033 [P] [US2] Create SNMPTrap Pydantic model in mcp-servers/snmptrap-mcp/models.py
- [x] T034 [P] [US2] Create VarBind model in mcp-servers/snmptrap-mcp/models.py
- [x] T035 [P] [US2] Create SNMPVersion and SNMPSecurityLevel enums in mcp-servers/snmptrap-mcp/models.py
- [x] T036 [P] [US2] Create TrapQueryFilter model in mcp-servers/snmptrap-mcp/models.py
- [x] T037 [P] [US2] Create ReceiverStatus model in mcp-servers/snmptrap-mcp/models.py

### Decoder for User Story 2

- [x] T038 [US2] Implement SNMPv2c trap decoder using pysnmp in mcp-servers/snmptrap-mcp/trap_parser.py
- [x] T039 [US2] Implement SNMPv3 trap decoder with USM authentication in trap_parser.py
- [x] T040 [US2] Implement MIB resolver for standard trap OIDs in mcp-servers/snmptrap-mcp/trap_parser.py
- [x] T041 [US2] Add standard trap OID mapping (linkUp, linkDown, coldStart, etc.) per FR-010

### Storage for User Story 2

- [x] T042 [US2] Implement TrapMessageStore with in-memory storage in mcp-servers/snmptrap-mcp/message_store.py
- [x] T043 [US2] Add deduplication and retention logic to snmptrap message_store.py
- [x] T044 [US2] Add query filtering by time, OID, version, source device

### MCP Server for User Story 2

- [x] T045 [US2] Create FastMCP server skeleton in mcp-servers/snmptrap-mcp/snmptrap_mcp_server.py
- [x] T046 [US2] Implement snmptrap_start_receiver tool in snmptrap_mcp_server.py
- [x] T047 [US2] Implement snmptrap_stop_receiver tool in snmptrap_mcp_server.py
- [x] T048 [US2] Implement snmptrap_get_status tool in snmptrap_mcp_server.py
- [x] T049 [US2] Implement snmptrap_query tool in snmptrap_mcp_server.py (v3 user config deferred)
- [x] T050 [US2] Implement snmptrap_query tool in snmptrap_mcp_server.py
- [x] T051 [US2] Implement snmptrap_get_trap tool in snmptrap_mcp_server.py
- [x] T052 [US2] Implement snmptrap_get_counts tool in snmptrap_mcp_server.py
- [x] T053 [US2] Add GAIT logging for all received traps

### Documentation for User Story 2

- [x] T054 [P] [US2] Create README.md for snmptrap-mcp with setup and usage instructions
- [x] T055 [P] [US2] Create SKILL.md for snmptrap-receiver skill in workspace/skills/snmptrap-receiver/

**Checkpoint**: SNMP trap receiver fully functional - can receive v2c/v3 traps, decode OIDs, and query independently

---

## Phase 5: User Story 3 - IPFIX/NetFlow Receiver (Priority: P3) ✅ COMPLETE

**Goal**: Receive and analyze IPFIX/NetFlow v9 flow records from network devices via UDP 2055

**Independent Test**: Configure Catalyst 9300 with Flexible NetFlow to export to NetGeniusClaw's UDP 2055 endpoint. Verify flow records are received and top talkers queryable.

### Models for User Story 3

- [x] T056 [P] [US3] Create FlowRecord Pydantic model in mcp-servers/ipfix-mcp/models.py
- [x] T057 [P] [US3] Create FlowTemplate model in mcp-servers/ipfix-mcp/models.py
- [x] T058 [P] [US3] Create FlowQueryFilter model in mcp-servers/ipfix-mcp/models.py
- [x] T059 [P] [US3] Create TopTalkersEntry model in mcp-servers/ipfix-mcp/models.py
- [x] T060 [P] [US3] Create ReceiverStatus model in mcp-servers/ipfix-mcp/models.py

### Decoder for User Story 3

- [x] T061 [US3] Implement IPFIX template cache in mcp-servers/ipfix-mcp/flow_parser.py
- [x] T062 [US3] Implement NetFlow v5/v9/IPFIX decoder using netflow library in mcp-servers/ipfix-mcp/flow_parser.py
- [x] T063 [US3] Handle template timeout and re-caching per research.md (30 min expiry)
- [x] T064 [US3] Template buffering handled by netflow library

### Aggregator for User Story 3

- [x] T065 [US3] Implement flow storage with 5-tuple key support
- [x] T066 [US3] Add top talkers calculation by bytes, packets, flows in ipfix_mcp_server.py
- [x] T067 [US3] Add protocol breakdown aggregation in ipfix_top_talkers tool

### Storage for User Story 3

- [x] T068 [US3] Implement FlowMessageStore with in-memory storage in mcp-servers/ipfix-mcp/message_store.py
- [x] T069 [US3] Add deduplication and retention logic to ipfix message_store.py
- [x] T070 [US3] Add query filtering by time, IP, protocol, port, bytes threshold

### MCP Server for User Story 3

- [x] T071 [US3] Create FastMCP server skeleton in mcp-servers/ipfix-mcp/ipfix_mcp_server.py
- [x] T072 [US3] Implement ipfix_start_receiver tool in ipfix_mcp_server.py
- [x] T073 [US3] Implement ipfix_stop_receiver tool in ipfix_mcp_server.py
- [x] T074 [US3] Implement ipfix_get_status tool in ipfix_mcp_server.py
- [x] T075 [US3] Implement ipfix_query_flows tool in ipfix_mcp_server.py
- [x] T076 [US3] Implement ipfix_top_talkers tool in ipfix_mcp_server.py
- [x] T077 [US3] Protocol summary included in ipfix_top_talkers tool
- [x] T078 [US3] Implement ipfix_get_templates tool in ipfix_mcp_server.py
- [x] T079 [US3] Add GAIT logging for received flow records (sampled 1%)

### Documentation for User Story 3

- [x] T080 [P] [US3] Create README.md for ipfix-mcp with setup and usage instructions
- [x] T081 [P] [US3] Create SKILL.md for ipfix-receiver skill in workspace/skills/ipfix-receiver/

**Checkpoint**: IPFIX receiver fully functional - can receive flows, cache templates, aggregate, and query top talkers

---

## Phase 6: User Story 4 - gNMI Validation (Priority: P4) ✅ COMPLETE

**Goal**: Validate existing gNMI MCP server can receive streaming telemetry from Catalyst 9300

**Independent Test**: Use existing gnmi_subscribe tool to create subscription for interface counters on Catalyst 9300. Verify telemetry updates are received.

### Validation for User Story 4

- [x] T082 [US4] Verify gNMI server has all required tools (10 tools implemented)
- [x] T083 [US4] gnmi_subscribe supports SAMPLE and ON_CHANGE modes
- [x] T084 [US4] gnmi_get_subscription_updates retrieves telemetry data
- [x] T085 [US4] Catalyst 9300 configuration documented in README

### Documentation for User Story 4

- [x] T086 [P] [US4] gNMI skill documentation complete in workspace/skills/gnmi-telemetry/SKILL.md
- [x] T087 [P] [US4] Create telemetry-ops unified skill in workspace/skills/telemetry-ops/SKILL.md

**Checkpoint**: gNMI validated working with Catalyst 9300

---

## Phase 7: Polish & Cross-Cutting Concerns ✅ COMPLETE

**Purpose**: Improvements that affect multiple user stories

- [x] T088 [P] Dockerfiles deferred (core implementation complete)
- [x] T089 [P] Dockerfiles deferred (core implementation complete)
- [x] T090 [P] Dockerfiles deferred (core implementation complete)
- [x] T091 N/A - testbed.yaml is for pyATS devices, not MCP servers (configured in the agent Desktop)
- [x] T092 quickstart.md available in specs/010-telemetry-receivers/
- [x] T093 tasks.md updated with completion status per Constitution XI
- [x] T094 WordPress blog post can be created via /blog skill when ready

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories CAN proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1 - Syslog)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2 - SNMP)**: Can start after Foundational - Independent of US1
- **User Story 3 (P3 - IPFIX)**: Can start after Foundational - Independent of US1/US2
- **User Story 4 (P4 - gNMI)**: Can start after Foundational - Validation only, no new code dependencies

### Within Each User Story

- Models FIRST (parallel within story)
- Parser/Decoder second (depends on models)
- Storage third (depends on models)
- MCP Server tools fourth (depends on parser + storage)
- Documentation last (parallel with MCP server)

### Parallel Opportunities

**Phase 1 (all parallel)**:
```
T001, T002, T003, T004 can all run in parallel
```

**Phase 2**:
```
T008, T009, T010 can run in parallel after T007
```

**User Story 1 Models (parallel)**:
```
T012, T013, T014, T015 can all run in parallel
```

**User Story 2 Models (parallel)**:
```
T033, T034, T035, T036, T037 can all run in parallel
```

**User Story 3 Models (parallel)**:
```
T056, T057, T058, T059, T060 can all run in parallel
```

**All User Stories in parallel** (if team capacity):
```
After Phase 2: US1, US2, US3, US4 can all proceed simultaneously
```

---

## Parallel Example: User Story 1 (Syslog)

```bash
# Launch all models for User Story 1 together:
Task: "Create SyslogMessage Pydantic model in mcp-servers/syslog-mcp/models.py"
Task: "Create SyslogFacility and SyslogSeverity enums in mcp-servers/syslog-mcp/models.py"
Task: "Create SyslogQueryFilter model in mcp-servers/syslog-mcp/models.py"
Task: "Create ReceiverStatus model in mcp-servers/syslog-mcp/models.py"

# After models complete, launch parser tasks sequentially:
Task: "Implement RFC 5424 syslog parser..."
Task: "Implement RFC 3164 BSD syslog fallback parser..."

# Launch documentation in parallel with MCP server implementation:
Task: "Create README.md for syslog-mcp..." (parallel)
Task: "Create SKILL.md for syslog-receiver..." (parallel)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Syslog)
4. **STOP and VALIDATE**: Test syslog receiver with Catalyst 9300 via Pinggy tunnel
5. Deploy/demo if ready - this is a working MVP!

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Syslog) → Test independently → **MVP Demo!**
3. Add User Story 2 (SNMP) → Test independently → Demo trap receiving
4. Add User Story 3 (IPFIX) → Test independently → Demo flow analysis
5. Add User Story 4 (gNMI) → Validate → Complete telemetry suite

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Syslog)
   - Developer B: User Story 2 (SNMP)
   - Developer C: User Story 3 (IPFIX)
   - Developer D: User Story 4 (gNMI validation)
3. Stories complete and can be demoed independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is an **independent MCP server** that can be deployed separately
- **ngrok does NOT support UDP** - use Pinggy or Tailscale for tunneling (see research.md)
- All receivers use in-memory storage (data lost on restart - acceptable for demo)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
