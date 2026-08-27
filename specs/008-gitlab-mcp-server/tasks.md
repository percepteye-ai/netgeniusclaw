# Tasks: GitLab MCP Server Integration

**Input**: Design documents from `/specs/008-gitlab-mcp-server/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/mcp-tools.md, quickstart.md

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. This is a configuration integration — no MCP server code is authored by netgeniusclaw. The community @zereight/mcp-gitlab package (TypeScript/Node.js) is installed via `npx` and spawned as a local process. Tasks focus on registration, documentation, skill authoring, and artifact coherence.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Directory structure creation and MCP server registration

- [x] T001 Create MCP server directory: `mcp-servers/gitlab-mcp/`
- [x] T002 [P] Create skill directory: `workspace/skills/gitlab-devops/`
- [x] T003 [P] Register gitlab-mcp server in `config/openclaw.json` under mcpServers with command: `npx`, args: `["-y", "@zereight/mcp-gitlab"]`, env: `GITLAB_PERSONAL_ACCESS_TOKEN`, `GITLAB_API_URL` (defaulting to `https://gitlab.com`) per research.md R4

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: MCP server README that documents the community server, its 98+ tools, authentication, and setup for both gitlab.com and self-hosted

**CRITICAL**: No user story skill work can begin until the MCP server documentation is in place

- [x] T004 Create MCP server README in `mcp-servers/gitlab-mcp/README.md` with: server overview (community @zereight/mcp-gitlab, 98+ tools, TypeScript/Node.js, MIT license), transport protocol (stdio via `npx -y @zereight/mcp-gitlab`), environment variables table (GITLAB_PERSONAL_ACCESS_TOKEN, GITLAB_API_URL, GITLAB_READ_ONLY_MODE), authentication instructions (PAT with api or read_api scope), self-hosted GitLab support (GITLAB_API_URL override, self-signed TLS cert handling via NODE_TLS_REJECT_UNAUTHORIZED with security warning), read-only mode (GITLAB_READ_ONLY_MODE=true), tool categories summary (Issues, Merge Requests, Pipelines, Repository, Projects, Labels, Milestones, Releases, Wiki), and example usage. Note the official GitLab MCP server as alternative for Premium/Ultimate teams.
- [x] T005 [P] Update `.env.example` with new environment variables: GITLAB_PERSONAL_ACCESS_TOKEN, GITLAB_API_URL, GITLAB_READ_ONLY_MODE (with descriptions, no values, including notes on PAT scopes and self-hosted URL format)

**Checkpoint**: Foundation ready — MCP server documented and registered. Skill authoring can begin.

---

## Phase 3: User Story 1 — Query Issues and Merge Requests (Priority: P1) MVP

**Goal**: Skill workflow for searching, listing, and inspecting GitLab issues and merge requests using list_issues, get_issue, list_issue_comments, list_merge_requests, get_merge_request, list_projects, search_projects tools.

**Independent Test**: Ask "show me open issues in project network-automation" and verify the skill invokes list_issues with appropriate filters and returns accurate issue data.

### Implementation for User Story 1

- [x] T006 [US1] Create skill documentation in `workspace/skills/gitlab-devops/SKILL.md` with YAML front matter (name: gitlab-devops, description, mcp_servers: [gitlab-mcp], tools_used listing). Include Purpose section describing DevOps-focused GitLab project management, pipeline monitoring, and repository browsing. Start with issue and MR read workflows.
- [x] T007 [US1] Add issue and MR query workflow section to `workspace/skills/gitlab-devops/SKILL.md`: step-by-step workflow for (1) listing/searching projects via list_projects or search_projects, (2) listing issues via list_issues with filters (state, labels, assignee, milestone), (3) retrieving issue details via get_issue, (4) listing issue comments via list_issue_comments, (5) listing merge requests via list_merge_requests with filters (state, labels, source/target branch), (6) retrieving MR details via get_merge_request (includes diff stats, approval status). Include example natural language prompts and expected tool invocations.
- [x] T008 [US1] Add GAIT audit logging section to `workspace/skills/gitlab-devops/SKILL.md`: document that all GitLab interactions must be logged to GAIT audit trail via gait_mcp tools at skill invocation level (per research.md R7). Include logging pattern: log tool name, parameters, and result summary for each operation.
- [x] T009 [US1] Add read-only mode section to `workspace/skills/gitlab-devops/SKILL.md`: document behavior when GITLAB_READ_ONLY_MODE=true — skill restricts to read tools only (list_*, get_*, search_*). Write tools (create_*, update_*, delete_*, merge_*) are skipped with a message indicating read-only mode is enabled. Per research.md R5.

**Checkpoint**: User Story 1 complete. Skill documents issue and MR query workflows with GAIT logging and read-only mode.

---

## Phase 4: User Story 2 — Monitor CI/CD Pipelines (Priority: P2)

**Goal**: Extend skill with pipeline monitoring and control workflows using list_pipelines, get_pipeline, get_pipeline_jobs, get_pipeline_job_log, create_pipeline, retry_pipeline, cancel_pipeline tools.

**Independent Test**: Ask "show pipelines for project network-configs" and verify the skill invokes list_pipelines and returns accurate pipeline data.

### Implementation for User Story 2

- [x] T010 [US2] Add pipeline monitoring workflow section to `workspace/skills/gitlab-devops/SKILL.md`: step-by-step workflow for (1) listing pipelines via list_pipelines with filters (status, ref, source), (2) retrieving pipeline details via get_pipeline, (3) listing pipeline jobs via get_pipeline_jobs with stage/status info, (4) retrieving job logs via get_pipeline_job_log for troubleshooting. Include example prompts for monitoring and troubleshooting workflows.
- [x] T011 [US2] Add pipeline control workflow section to `workspace/skills/gitlab-devops/SKILL.md`: step-by-step workflow for (1) triggering new pipeline via create_pipeline on a branch with human confirmation, (2) retrying failed pipeline via retry_pipeline with confirmation, (3) canceling running pipeline via cancel_pipeline with confirmation. Emphasize read-before-write (verify pipeline state before control actions) and human-in-the-loop (Constitution XIV). Note: skipped in read-only mode.

**Checkpoint**: User Story 2 complete. Skill documents pipeline monitoring and control.

---

## Phase 5: User Story 3 — Browse Repositories and Files (Priority: P3)

**Goal**: Extend skill with repository browsing workflows using list_repository_tree, get_file_content, list_commits, get_commit, compare_branches tools.

**Independent Test**: Ask "show the directory structure of project network-configs" and verify the skill invokes list_repository_tree and returns file/folder listing.

### Implementation for User Story 3

- [x] T012 [US3] Add repository browsing workflow section to `workspace/skills/gitlab-devops/SKILL.md`: step-by-step workflow for (1) listing repository tree via list_repository_tree with path and ref filters, (2) retrieving file content via get_file_content at a specific ref/branch, (3) listing commits via list_commits with branch/path/date filters, (4) retrieving commit details and diff via get_commit, (5) comparing branches via compare_branches for change review. Include example prompts for code review and change analysis workflows.

**Checkpoint**: User Story 3 complete. Skill documents repository browsing and commit history.

---

## Phase 6: User Story 4 — Manage Issues and Merge Requests (Priority: P4)

**Goal**: Extend skill with issue and MR write workflows using create_issue, update_issue, add_issue_comment, create_merge_request, update_merge_request, merge_merge_request, add_merge_request_comment tools. All write operations gated by human-in-the-loop (Constitution XIV).

**Independent Test**: Ask "create an issue in project network-automation titled 'BGP peer flapping on router-01'" and verify the skill documents the confirmation step before invoking create_issue.

### Implementation for User Story 4

- [x] T013 [US4] Add issue management workflow section to `workspace/skills/gitlab-devops/SKILL.md`: step-by-step workflow for (1) creating issues via create_issue with title, description, labels, assignee — with human confirmation, (2) updating issues via update_issue (state, labels, assignee, milestone) with confirmation, (3) adding comments via add_issue_comment. Emphasize read-before-write and human-in-the-loop. Note: skipped in read-only mode.
- [x] T014 [US4] Add merge request management workflow section to `workspace/skills/gitlab-devops/SKILL.md`: step-by-step workflow for (1) creating MRs via create_merge_request with source/target branches, title, description — with human confirmation, (2) updating MRs via update_merge_request with confirmation, (3) adding comments via add_merge_request_comment, (4) merging MRs via merge_merge_request with explicit confirmation (noting squash/remove-source-branch options). Emphasize human-in-the-loop for all write operations. Note: skipped in read-only mode.

**Checkpoint**: User Story 4 complete. Skill documents issue and MR write operations with safety gates.

---

## Phase 7: User Story 5 — Manage Labels, Milestones, and Releases (Priority: P5)

**Goal**: Extend skill with project management entity workflows using label, milestone, release, and wiki tools.

**Independent Test**: Ask "list milestones for project network-automation" and verify the skill invokes list_milestones and returns milestone data.

### Implementation for User Story 5

- [x] T015 [US5] Add project management entities section to `workspace/skills/gitlab-devops/SKILL.md`: workflows for (1) label management — list_labels, create_label, update_label, delete_label with confirmation for write ops, (2) milestone management — list_milestones, create_milestone, update_milestone with confirmation, (3) release management — list_releases, get_release, create_release with confirmation, (4) wiki page management — list_wiki_pages, get_wiki_page, create_wiki_page, update_wiki_page, delete_wiki_page with confirmation. Note: write operations skipped in read-only mode.

**Checkpoint**: All user stories complete. Skill fully documents GitLab DevOps workflows.

---

## Phase 8: Polish & Artifact Coherence

**Purpose**: Artifact coherence checklist completion (Constitution XI) and cross-cutting documentation updates

- [x] T016 [P] Update `TOOLS.md` with GitLab MCP server entry: server name (gitlab-mcp), 98+ tools across categories (Issues, Merge Requests, Pipelines, Repository, Projects, Labels, Milestones, Releases, Wiki), brief descriptions
- [x] T017 [P] Update `SOUL.md` with gitlab-devops skill definition and GitLab MCP server capability summary
- [x] T018 [P] Update `README.md` with GitLab MCP server description, updated tool/skill counts, and architecture reference
- [x] T019 [P] Update `scripts/install.sh` with GitLab MCP server dependency note (Node.js 18+ required for npx, npm package auto-installed via npx -y)
- [x] T020 [P] Update `ui/netclaw-visual/` Three.js HUD with new GitLab MCP server node representing the DevOps integration
- [x] T021 Validate quickstart.md instructions by reviewing server startup and tool invocation flows in `specs/008-gitlab-mcp-server/quickstart.md`
- [x] T022 Verify backwards compatibility — confirm all existing MCP servers and skills remain functional after additions (Constitution XV, FR-020)
- [ ] T023 Draft WordPress blog post documenting GitLab MCP integration milestone (Constitution XVII) — submit to John for review before publishing

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phases 3-7)**: All depend on Foundational phase completion
  - US1 (Phase 3): No dependencies on other stories — MVP target
  - US2 (Phase 4): Independent of US1 (different tool category — Pipelines vs Issues/MRs)
  - US3 (Phase 5): Independent of US1/US2 (different tool category — Repository)
  - US4 (Phase 6): Depends on US1 (extends issue/MR section with write operations)
  - US5 (Phase 7): Independent of US1-US4 (different tool categories — Labels, Milestones, Releases, Wiki)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Foundational only. MVP target.
- **US2 (P2)**: Foundational only. Can run in parallel with US1.
- **US3 (P3)**: Foundational only. Can run in parallel with US1/US2.
- **US4 (P4)**: Depends on US1 (adds write operations to issue/MR skill section).
- **US5 (P5)**: Foundational only. Can run in parallel with US1-US3.

### Within Each User Story

- Read existing skill content before extending
- Core workflow documentation before edge case handling
- Story complete before moving to next priority

### Parallel Opportunities

- T001, T002, T003 (Setup) can all run in parallel
- T004 and T005 (Foundational) can run in parallel
- US1, US2, US3, and US5 can all run in parallel after Foundational
- T013 and T014 (US4) are in the same file but sequential sections
- All Phase 8 tasks marked [P] can run in parallel

---

## Parallel Example: Phase 1 (Setup)

```bash
# All setup tasks are independent:
Task: "T001 Create mcp-servers/gitlab-mcp/ directory"
Task: "T002 Create workspace/skills/gitlab-devops/ directory"
Task: "T003 Register gitlab-mcp in config/openclaw.json"
```

## Parallel Example: Phase 8 (Polish)

```bash
# All documentation updates can run in parallel:
Task: "T016 Update TOOLS.md"
Task: "T017 Update SOUL.md"
Task: "T018 Update README.md"
Task: "T019 Update scripts/install.sh"
Task: "T020 Update ui/netclaw-visual/ HUD"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T005)
3. Complete Phase 3: User Story 1 (T006-T009)
4. **STOP and VALIDATE**: Verify skill documentation covers issue and MR query workflows with GAIT logging and read-only mode
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready (registration + README)
2. Add US1 (Issue/MR queries) → Test → MVP!
3. Add US2 (Pipeline monitoring) → Test → CI/CD observability
4. Add US3 (Repository browsing) → Test → Code context
5. Add US4 (Issue/MR management) → Test → Write operations
6. Add US5 (Labels/Milestones/Releases/Wiki) → Test → Project management
7. Phase 8 (Polish + Artifact Coherence) → Feature complete

### Suggested MVP Scope

User Story 1 (Query Issues and Merge Requests) is the MVP. It delivers the foundational GitLab read capability — searching issues, viewing MR details, and understanding project status. After US1 is validated, each additional story adds independent value.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- This is a configuration integration — no server.py or TypeScript code is authored by netgeniusclaw
- The community @zereight/mcp-gitlab package handles all tool implementation
- Node.js 18+ is required as a runtime dependency (for npx)
- GAIT audit logging is coordinated at skill level via gait_mcp tools, not embedded in the MCP server
- Write operations require human-in-the-loop confirmation (Constitution XIV)
- Read-only mode (GITLAB_READ_ONLY_MODE=true) restricts skill to observation-only tools
- Self-hosted GitLab is supported via GITLAB_API_URL override
