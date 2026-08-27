# Tasks: Blender 3D Network Visualization

**Input**: Design documents from `/specs/024-blender-3d-viz/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Manual integration testing only (Blender GUI required). No automated tests for this feature.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This is an MCP integration feature - no custom source code. Paths are configuration and documentation files:
- `config/openclaw.json` - MCP server registration
- `.env.example` - Environment variables
- `workspace/skills/blender-3d-viz/SKILL.md` - Skill documentation
- `SOUL.md`, `README.md`, `scripts/install.sh` - Project documentation

---

## Phase 1: Setup (MCP Registration)

**Purpose**: Register the Blender MCP server and configure environment

- [x] T001 Add blender-mcp server to config/openclaw.json
- [x] T002 [P] Add BLENDER_HOST and BLENDER_PORT to .env.example

**Checkpoint**: MCP server registered, environment variables documented

---

## Phase 2: Foundational (Skill Definition)

**Purpose**: Create the skill definition that enables natural language interaction

**⚠️ CRITICAL**: Skill must be defined before user stories can be demonstrated

- [x] T003 Create workspace/skills/blender-3d-viz/ directory
- [x] T004 Create SKILL.md with tool documentation in workspace/skills/blender-3d-viz/SKILL.md
- [x] T005 Add blender-3d-viz skill entry to SOUL.md
- [x] T006 [P] Update skill count in SOUL.md header (156→157 skills, 69→70 MCPs)

**Checkpoint**: Skill defined and registered in SOUL.md

---

## Phase 3: User Story 1 - Draw Network Topology from CDP Data (Priority: P1) 🎯 MVP

**Goal**: Network engineer can say "draw the network topology using CDP data" and see a 3D visualization in Blender

**Independent Test**: Send topology request via Slack/CLI, verify devices and connections render in Blender within 30 seconds

### Implementation for User Story 1

- [x] T007 [US1] Document topology rendering workflow in workspace/skills/blender-3d-viz/SKILL.md
- [x] T008 [US1] Add device type color mapping documentation (router=blue, switch=green, firewall=red)
- [x] T009 [US1] Document 25-device limit and truncation warning behavior
- [x] T010 [US1] Add example queries for topology visualization to SKILL.md
- [x] T011 [US1] Document error handling for Blender connection unavailable

**Checkpoint**: User Story 1 documented and testable - users can request topology visualizations

---

## Phase 4: User Story 2 - Export Visualization for Documentation (Priority: P2)

**Goal**: Network engineer can export the 3D topology as a PNG or video file

**Independent Test**: Request "export as PNG" after rendering a topology, verify image file is created

### Implementation for User Story 2

- [x] T012 [US2] Add export commands documentation to workspace/skills/blender-3d-viz/SKILL.md
- [x] T013 [US2] Document PNG export workflow using execute_blender_code
- [x] T014 [US2] Document video export workflow (if supported by blender-mcp)
- [x] T015 [US2] Add example export queries to SKILL.md

**Checkpoint**: User Story 2 documented - users can export visualizations

---

## Phase 5: User Story 3 - Customize Visualization Appearance (Priority: P3)

**Goal**: Network engineer can customize colors, add labels, and highlight specific devices

**Independent Test**: Request "color router-1 red" after rendering, verify color changes in Blender

### Implementation for User Story 3

- [x] T016 [US3] Add color customization documentation to workspace/skills/blender-3d-viz/SKILL.md
- [x] T017 [US3] Document label addition workflow using execute_blender_code
- [x] T018 [US3] Document device highlighting commands
- [x] T019 [US3] Add example customization queries to SKILL.md

**Checkpoint**: User Story 3 documented - users can customize visualizations

---

## Phase 6: Polish & Artifact Coherence

**Purpose**: Complete all documentation updates per Constitution Principle XI

- [x] T020 [P] Add blender-mcp to README.md MCP server table
- [x] T021 [P] Add Blender setup instructions to scripts/install.sh
- [x] T022 [P] Update README.md skill count
- [x] T023 Copy quickstart.md setup guide to workspace/skills/blender-3d-viz/
- [x] T024 Run Artifact Coherence Checklist verification
- [x] T025 Commit all changes with proper commit message
- [x] T026 Push branch and create PR
- [x] T027 Draft WordPress blog post for milestone documentation (Constitution XVII)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion
- **User Stories (Phase 3-5)**: Depend on Foundational phase completion
  - User stories can proceed sequentially (recommended) or in parallel
- **Polish (Phase 6)**: Depends on all user stories being documented

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Phase 2 - Assumes US1 workflow exists but independently testable
- **User Story 3 (P3)**: Can start after Phase 2 - Assumes US1 workflow exists but independently testable

### Within Each User Story

- Document core workflow first
- Add examples after workflow is documented
- Add error handling documentation last

### Parallel Opportunities

- T001 and T002 can run in parallel (different files)
- T005 and T006 can run in parallel (same file but different sections)
- All Phase 6 tasks T020-T022 can run in parallel (different files)
- User stories 1-3 can be documented in parallel after Phase 2

---

## Parallel Example: Setup Phase

```bash
# Launch both setup tasks together:
Task: "Add blender-mcp server to config/openclaw.json"
Task: "Add BLENDER_HOST and BLENDER_PORT to .env.example"
```

## Parallel Example: Polish Phase

```bash
# Launch all documentation updates together:
Task: "Add blender-mcp to README.md MCP server table"
Task: "Add Blender setup instructions to scripts/install.sh"
Task: "Update README.md skill count"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T006)
3. Complete Phase 3: User Story 1 (T007-T011)
4. **STOP and VALIDATE**: Test topology rendering manually
5. Proceed to next stories or deploy MVP

### Incremental Delivery

1. Setup + Foundational → MCP registered, skill defined
2. Add User Story 1 → Test topology rendering → MVP complete!
3. Add User Story 2 → Test export functionality
4. Add User Story 3 → Test customization
5. Complete Polish phase → PR ready

### Single Developer Strategy (Recommended)

1. Complete all phases sequentially
2. Test each user story before moving to next
3. Total estimated tasks: 27
4. Minimal code - primarily documentation and configuration

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- This feature has NO custom source code - all tasks are configuration and documentation
- Blender must be running on Windows with addon connected for manual testing
- WSL must be configured to reach Windows host IP for cross-OS connectivity
- Blog post (T027) is required by Constitution Principle XVII
