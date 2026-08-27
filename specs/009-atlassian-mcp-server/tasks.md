# Tasks: Atlassian MCP Server Integration

**Input**: Design documents from `/specs/009-atlassian-mcp-server/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/mcp-tools.md, quickstart.md

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. This is a configuration integration — no MCP server code is authored by netgeniusclaw. The community mcp-atlassian package (by sooperset) is installed via `uvx` and spawned as a local process. Tasks focus on registration, documentation, skill authoring, and artifact coherence.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Directory structure creation and MCP server registration

- [X] T001 Create MCP server directory: `mcp-servers/atlassian-mcp/`
- [X] T002 [P] Create skill directory: `workspace/skills/atlassian-itsm/`
- [X] T003 [P] Register atlassian-mcp server in `config/openclaw.json` under mcpServers with command: `uvx`, args: `["mcp-atlassian"]`, env: `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`, `CONFLUENCE_URL`, `CONFLUENCE_USERNAME`, `CONFLUENCE_API_TOKEN` (all referencing `${ENV_VAR}` syntax)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: MCP server README that documents the community server, its tools, authentication, and setup for both Cloud and Server/DC

**CRITICAL**: No user story skill work can begin until the MCP server documentation is in place

- [X] T004 Create MCP server README in `mcp-servers/atlassian-mcp/README.md` with: server overview (community mcp-atlassian by sooperset, 72 tools, Python, Apache 2.0), transport protocol (stdio via `uvx mcp-atlassian`), environment variables table (JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN, CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN), authentication instructions for both Cloud (API token) and Server/DC (PAT), graceful degradation when only one product is configured, tool categories summary (Jira Issues, Transitions, Comments, Projects, Fields, Links, Confluence Pages, Comments, Spaces), and example usage
- [X] T005 [P] Update `.env.example` with new environment variables: JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN, CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN (with descriptions, no values, noting Cloud vs Server/DC authentication differences)

**Checkpoint**: Foundation ready — MCP server documented and registered. Skill authoring can begin.

---

## Phase 3: User Story 1 — Search and View Jira Issues (Priority: P1) MVP

**Goal**: Skill workflow for searching, filtering, and inspecting Jira issues from the AI assistant using jira_search, jira_get_issue, jira_get_issue_comments, jira_get_projects, jira_get_fields, jira_get_issue_types tools.

**Independent Test**: Ask "show me open issues in project NET assigned to me" and verify the skill invokes jira_search with appropriate JQL and returns accurate issue data.

### Implementation for User Story 1

- [X] T006 [US1] Create skill documentation in `workspace/skills/atlassian-itsm/SKILL.md` with YAML front matter (name: atlassian-itsm, description, mcp_servers: [atlassian-mcp], tools_used listing). Include Purpose section describing ITSM-focused Jira issue tracking and Confluence documentation management. Start with Jira read workflows: searching issues with JQL, retrieving issue details, listing project issues, viewing comments.
- [X] T007 [US1] Add Jira read workflow section to `workspace/skills/atlassian-itsm/SKILL.md`: step-by-step workflow for (1) listing accessible projects via jira_get_projects, (2) searching issues via jira_search with JQL examples (project, status, assignee, label filters), (3) retrieving full issue details via jira_get_issue, (4) viewing comments via jira_get_issue_comments. Include example natural language prompts and expected tool invocations.
- [X] T008 [US1] Add GAIT audit logging section to `workspace/skills/atlassian-itsm/SKILL.md`: document that all Atlassian interactions must be logged to GAIT audit trail via gait_mcp tools at skill invocation level (per research.md R8). Include logging pattern: log tool name, parameters, and result summary for each operation.

**Checkpoint**: User Story 1 complete. Skill documents Jira read operations with GAIT logging.

---

## Phase 4: User Story 2 — Search and Read Confluence Pages (Priority: P2)

**Goal**: Extend skill with Confluence read workflows using confluence_search, confluence_get_page, confluence_get_spaces, confluence_get_space, confluence_get_page_comments tools.

**Independent Test**: Ask "search Confluence for 'BGP runbook'" and verify the skill invokes confluence_search and returns matching page results.

### Implementation for User Story 2

- [X] T009 [US2] Add Confluence read workflow section to `workspace/skills/atlassian-itsm/SKILL.md`: step-by-step workflow for (1) listing spaces via confluence_get_spaces, (2) searching pages via confluence_search with CQL examples (space, title, content filters), (3) retrieving page content via confluence_get_page, (4) viewing page comments via confluence_get_page_comments. Include example prompts and tool invocations.

**Checkpoint**: User Story 2 complete. Skill covers both Jira and Confluence read operations.

---

## Phase 5: User Story 3 — Create and Update Jira Issues (Priority: P3)

**Goal**: Extend skill with Jira write workflows using jira_create_issue, jira_update_issue, jira_transition_issue, jira_add_comment, jira_get_transitions tools. All write operations gated by human-in-the-loop (Constitution XIV).

**Independent Test**: Ask "create a Jira issue in project NET titled 'Router-01 BGP peer down' with priority Critical" and verify the skill documents the confirmation step before invoking jira_create_issue.

### Implementation for User Story 3

- [X] T010 [US3] Add Jira write workflow section to `workspace/skills/atlassian-itsm/SKILL.md`: step-by-step workflow for (1) querying available issue types via jira_get_issue_types before creating, (2) creating issues via jira_create_issue with human confirmation, (3) querying available transitions via jira_get_transitions before transitioning, (4) transitioning issues via jira_transition_issue with confirmation, (5) updating issue fields via jira_update_issue with confirmation, (6) adding comments via jira_add_comment. Emphasize read-before-write pattern (Constitution II) and human-in-the-loop (Constitution XIV) for all write operations.

**Checkpoint**: User Story 3 complete. Skill documents Jira write operations with safety gates.

---

## Phase 6: User Story 4 — Create and Update Confluence Pages (Priority: P4)

**Goal**: Extend skill with Confluence write workflows using confluence_create_page, confluence_update_page, confluence_add_comment, confluence_delete_page tools. All write operations gated by human-in-the-loop.

**Independent Test**: Ask "create a Confluence page in space NET-DOCS titled 'Incident Postmortem: Router-01 Outage'" and verify the skill documents the confirmation step before invoking confluence_create_page.

### Implementation for User Story 4

- [X] T011 [US4] Add Confluence write workflow section to `workspace/skills/atlassian-itsm/SKILL.md`: step-by-step workflow for (1) verifying target space via confluence_get_space before creating, (2) creating pages via confluence_create_page with human confirmation, (3) updating pages via confluence_update_page with confirmation (noting version increment), (4) adding comments via confluence_add_comment, (5) deleting pages via confluence_delete_page with explicit confirmation. Emphasize read-before-write and human-in-the-loop.

**Checkpoint**: User Story 4 complete. Skill documents Confluence write operations with safety gates.

---

## Phase 7: User Story 5 — Cross-Product Linking and Bulk Operations (Priority: P5)

**Goal**: Extend skill with cross-product linking and bulk operations using jira_link_issues, jira_get_issue_links, jira_get_link_types, jira_batch_create_issues tools.

**Independent Test**: Ask "create 5 Jira issues in project NET for the following tasks" and verify the skill documents bulk creation workflow with confirmation.

### Implementation for User Story 5

- [X] T012 [US5] Add cross-product and bulk operations section to `workspace/skills/atlassian-itsm/SKILL.md`: (1) linking Jira issues via jira_link_issues with available link types from jira_get_link_types, (2) viewing issue links via jira_get_issue_links, (3) bulk issue creation via jira_batch_create_issues with human confirmation for the full batch. Include workflow for creating a Jira incident and linking it to a Confluence postmortem page.

**Checkpoint**: All user stories complete. Skill fully documents Jira + Confluence ITSM workflows.

---

## Phase 8: Polish & Artifact Coherence

**Purpose**: Artifact coherence checklist completion (Constitution XI) and cross-cutting documentation updates

- [X] T013 [P] Update `TOOLS.md` with Atlassian MCP server entry: server name (atlassian-mcp), 72 tools across categories (Jira Issues, Transitions, Comments, Projects, Fields, Links, Confluence Pages, Comments, Spaces), brief descriptions
- [X] T014 [P] Update `SOUL.md` with atlassian-itsm skill definition and Atlassian MCP server capability summary
- [X] T015 [P] Update `README.md` with Atlassian MCP server description, updated tool/skill counts, and architecture reference
- [X] T016 [P] Update `scripts/install.sh` with Atlassian MCP server dependency note (uvx/uv required for mcp-atlassian, Python 3.10+ prerequisite)
- [X] T017 [P] Update `ui/netclaw-visual/` Three.js HUD with new Atlassian MCP server node representing the ITSM integration
- [X] T018 Validate quickstart.md instructions by reviewing server startup and tool invocation flows in `specs/009-atlassian-mcp-server/quickstart.md`
- [X] T019 Verify backwards compatibility — confirm all existing MCP servers and skills remain functional after additions (Constitution XV, FR-018)
- [ ] T020 Draft WordPress blog post documenting Atlassian MCP integration milestone (Constitution XVII) — submit to John for review before publishing

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phases 3-7)**: All depend on Foundational phase completion
  - US1 (Phase 3): No dependencies on other stories — MVP target
  - US2 (Phase 4): Independent of US1 (different product — Confluence vs Jira)
  - US3 (Phase 5): Depends on US1 (extends Jira section with write operations)
  - US4 (Phase 6): Depends on US2 (extends Confluence section with write operations)
  - US5 (Phase 7): Depends on US3 and US4 (cross-product linking requires both)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Foundational only. MVP target.
- **US2 (P2)**: Foundational only. Can run in parallel with US1.
- **US3 (P3)**: Depends on US1 (adds write operations to Jira skill section).
- **US4 (P4)**: Depends on US2 (adds write operations to Confluence skill section).
- **US5 (P5)**: Depends on US3 and US4 (cross-product linking spans both Jira and Confluence).

### Within Each User Story

- Read existing skill content before extending
- Core workflow documentation before edge case handling
- Story complete before moving to next priority

### Parallel Opportunities

- T001, T002, T003 (Setup) can all run in parallel
- T004 and T005 (Foundational) can run in parallel
- US1 and US2 can run in parallel after Foundational
- All Phase 8 tasks marked [P] can run in parallel

---

## Parallel Example: Phase 1 (Setup)

```bash
# All setup tasks are independent:
Task: "T001 Create mcp-servers/atlassian-mcp/ directory"
Task: "T002 Create workspace/skills/atlassian-itsm/ directory"
Task: "T003 Register atlassian-mcp in config/openclaw.json"
```

## Parallel Example: Phase 8 (Polish)

```bash
# All documentation updates can run in parallel:
Task: "T013 Update TOOLS.md"
Task: "T014 Update SOUL.md"
Task: "T015 Update README.md"
Task: "T016 Update scripts/install.sh"
Task: "T017 Update ui/netclaw-visual/ HUD"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T005)
3. Complete Phase 3: User Story 1 (T006-T008)
4. **STOP and VALIDATE**: Verify skill documentation covers Jira read workflows with GAIT logging
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready (registration + README)
2. Add US1 (Jira read) → Test → MVP!
3. Add US2 (Confluence read) → Test → Full read coverage
4. Add US3 (Jira write) → Test → Incident management workflow
5. Add US4 (Confluence write) → Test → Documentation management workflow
6. Add US5 (Bulk + cross-product) → Test → Power user operations
7. Phase 8 (Polish + Artifact Coherence) → Feature complete

### Suggested MVP Scope

User Story 1 (Search and View Jira Issues) is the MVP. It delivers the foundational Jira read capability that all other stories build on. After US1 is validated, each additional story adds independent value.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- This is a configuration integration — no server.py or Python code is authored by netgeniusclaw
- The community mcp-atlassian package handles all tool implementation
- GAIT audit logging is coordinated at skill level via gait_mcp tools, not embedded in the MCP server
- Write operations require human-in-the-loop confirmation (Constitution XIV)
- The skill degrades gracefully if only Jira or only Confluence is configured (research.md R6)
