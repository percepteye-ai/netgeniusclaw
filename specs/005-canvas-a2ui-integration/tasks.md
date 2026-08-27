# Tasks: Canvas / A2UI Network Visualization

**Input**: Design documents from `/specs/005-canvas-a2ui-integration/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Test tasks omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Skill directory**: `workspace/skills/canvas-network-viz/`
- **Components**: `workspace/skills/canvas-network-viz/components/`
- **Library**: `workspace/skills/canvas-network-viz/lib/`
- **Tests**: `workspace/skills/canvas-network-viz/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the skill directory structure and foundational files

- [X] T001 Create skill directory structure per implementation plan at workspace/skills/canvas-network-viz/ with subdirectories components/, lib/, and tests/
- [X] T002 Create SKILL.md with skill metadata frontmatter (name, description, user-invocable, openclaw requires) at workspace/skills/canvas-network-viz/SKILL.md following the grafana-observability SKILL.md pattern
- [X] T003 [P] Create color-scale.js with three-tier health-to-color mapping (green/amber/red/gray) and WCAG 2.1 AA compliant color values, thresholds at 70% warning and 90% critical at workspace/skills/canvas-network-viz/lib/color-scale.js
- [X] T004 [P] Create filter-engine.js with scope filtering by device name, site, device role, severity level, and time range at workspace/skills/canvas-network-viz/lib/filter-engine.js

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core library modules that ALL visualization types depend on. MUST complete before any user story.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 Implement a2ui-renderer.js with the root A2UI JSON envelope builder (version, type, component, props) and error-card output per the A2UI output contract at workspace/skills/canvas-network-viz/lib/a2ui-renderer.js
- [X] T006 Implement data-fetcher.js with MCP tool invocation abstraction supporting pyATS, Grafana, Prometheus, ServiceNow, SuzieQ, and Batfish servers; include per-source status tracking (ok/partial/unavailable) and latency measurement at workspace/skills/canvas-network-viz/lib/data-fetcher.js
- [X] T007 Implement gait-logger.js that emits GAIT audit log entries for each visualization event (type, dataSources, scope, status, renderDurationMs, timestamp) using the existing gait-session-tracking skill mechanism at workspace/skills/canvas-network-viz/lib/gait-logger.js
- [X] T008 Implement graph-layout.js with force-directed layout algorithm for arbitrary topologies and hierarchical layout with spine/leaf detection for structured fabrics; support up to 500 nodes at workspace/skills/canvas-network-viz/lib/graph-layout.js

**Checkpoint**: Foundation ready - all shared libraries operational. User story implementation can begin.

---

## Phase 3: User Story 1 - Render Network Topology Maps Inline (Priority: P1) MVP

**Goal**: Render auto-generated network topology maps inline in the OpenClaw chat interface from CDP/LLDP discovery data, color-coded by device health status.

**Independent Test**: Ask "show me the network topology" after CDP/LLDP discovery data has been collected. Verify an inline visual map appears with devices as nodes, links as edges, and health-based color coding. Verify GAIT log entry recorded.

### Implementation for User Story 1

- [X] T009 [P] [US1] Create topology-map.css with styles for topology nodes (circles with health-colored fills), edges (lines with status-colored strokes), labels (device hostnames), cluster containers (dashed border for site groupings), and the color legend at workspace/skills/canvas-network-viz/components/topology-map.css
- [X] T010 [P] [US1] Create topology-map.js Canvas component that accepts TopologyContent data model (nodes, edges, clusters, legend), applies graph-layout.js positioning, renders nodes with health-colored fills from color-scale.js, renders edges with interface labels, and includes an expandable color legend at workspace/skills/canvas-network-viz/components/topology-map.js
- [X] T011 [US1] Implement topology data pipeline in data-fetcher.js: fetch CDP/LLDP neighbor data via pyATS MCP tools (pyats_show_cdp_neighbors, pyats_show_lldp_neighbors), fetch health metrics (CPU, memory, interface errors, BGP/OSPF state) from pyATS/Grafana/Prometheus, transform into TopologyNode[] and TopologyEdge[] per data-model.md at workspace/skills/canvas-network-viz/lib/data-fetcher.js
- [X] T012 [US1] Implement site-based clustering logic: when topology exceeds 200 nodes, group by site metadata from pyATS/NetBox into TopologyCluster[] entities with expandable/collapsible behavior; warn if no site metadata available at workspace/skills/canvas-network-viz/components/topology-map.js
- [X] T013 [US1] Implement topology filtering: support filter by site name ("show topology for Site-A") and device role ("show spine topology") using filter-engine.js; render only matching subset of nodes and edges at workspace/skills/canvas-network-viz/components/topology-map.js
- [X] T014 [US1] Implement graceful degradation for topology: when health metric sources are unavailable, render topology with node health set to "unknown" (gray) and display Warning entry listing unavailable data sources at workspace/skills/canvas-network-viz/components/topology-map.js
- [X] T015 [US1] Implement empty-data handling: when no CDP/LLDP data exists, return an A2UI error-card with message explaining discovery data is required and suggesting running a discovery operation first at workspace/skills/canvas-network-viz/components/topology-map.js
- [X] T016 [US1] Wire topology-map component into the a2ui-renderer.js: register "topology-map" component type, build the full A2UI JSON envelope with dataSources, scope, warnings, and TopologyContent, and emit GAIT log via gait-logger.js at workspace/skills/canvas-network-viz/lib/a2ui-renderer.js

**Checkpoint**: Topology map visualization fully functional. Operator can request "show me the network topology" and see an inline map. GAIT logging verified.

---

## Phase 4: User Story 2 - Display Real-Time Dashboard Panels (Priority: P2)

**Goal**: Render inline dashboard panels showing interface counters, BGP peer status, OSPF adjacency state, and CPU/memory metrics for individual devices or sites.

**Independent Test**: Ask "show health dashboard for R1" with Grafana/Prometheus/pyATS data available. Verify inline panels appear with current metric values for CPU, memory, interface errors, BGP peers, OSPF adjacencies.

### Implementation for User Story 2

- [X] T017 [P] [US2] Create dashboard-panel.css with styles for gauge displays (circular/bar), counter panels, status-list items (up/down/warning indicators), sparkline containers, threshold-based coloring (green/amber/red), and multi-device summary grid layout at workspace/skills/canvas-network-viz/components/dashboard-panel.css
- [X] T018 [P] [US2] Create dashboard-panel.js Canvas component that accepts DashboardContent data model (panels[], deviceSummary), renders each DashboardPanel by type (gauge, counter, status-list, bar, sparkline), applies ThresholdConfig coloring, and renders StatusItem lists for BGP/OSPF at workspace/skills/canvas-network-viz/components/dashboard-panel.js
- [X] T019 [US2] Implement dashboard data pipeline in data-fetcher.js: fetch device metrics from Grafana (grafana_query_prometheus), Prometheus (prometheus_instant_query), and pyATS (pyats_show_interfaces, pyats_show_bgp_summary, pyats_show_ospf_neighbors), transform into DashboardPanel[] per data-model.md at workspace/skills/canvas-network-viz/lib/data-fetcher.js
- [X] T020 [US2] Implement multi-device site dashboard: when operator requests site-level dashboard, aggregate per-device metrics into a summary grid with per-device health indicators and aggregate statistics at workspace/skills/canvas-network-viz/components/dashboard-panel.js
- [X] T021 [US2] Implement dashboard graceful degradation: when Grafana/Prometheus unreachable but pyATS available, render partial dashboard with available pyATS data and display Warning indicators for unavailable panels at workspace/skills/canvas-network-viz/components/dashboard-panel.js
- [X] T022 [US2] Wire dashboard-panel component into a2ui-renderer.js: register "dashboard-panel" component type, build A2UI JSON envelope, emit GAIT log at workspace/skills/canvas-network-viz/lib/a2ui-renderer.js

**Checkpoint**: Dashboard panels fully functional. Single-device and site-level dashboards render inline with graceful degradation.

---

## Phase 5: User Story 3 - Visualize Alerts and Incidents (Priority: P3)

**Goal**: Render severity-colored alert cards inline with source information, timestamps, and filtering, consolidating alerts from Grafana, Prometheus, and syslog.

**Independent Test**: Ask "show current alerts" when active alerts exist in Grafana/Prometheus. Verify severity-colored alert cards appear sorted by severity (critical first) with severity counts summary.

### Implementation for User Story 3

- [X] T023 [P] [US3] Create alert-card.css with styles for alert cards (severity-colored borders/backgrounds: red critical, amber warning, blue info), severity summary bar, filter indicator, and "all clear" status card at workspace/skills/canvas-network-viz/components/alert-card.css
- [X] T024 [P] [US3] Create alert-card.js Canvas component that accepts AlertContent data model (summary, alerts[], filter, unfilteredCount), renders severity summary counts at top, renders individual AlertCard entries sorted by severity, and handles the "all clear" state at workspace/skills/canvas-network-viz/components/alert-card.js
- [X] T025 [US3] Implement alert data pipeline in data-fetcher.js: fetch active alerts from Grafana (grafana_list_alerts), Prometheus alertmanager (prometheus_alerts), and syslog from pyATS; apply severity mapping per data-model.md (Prometheus critical/warning, Grafana alerting/pending, syslog level 0-7) at workspace/skills/canvas-network-viz/lib/data-fetcher.js
- [X] T026 [US3] Implement alert filtering: support severity filter ("show critical alerts only"), device filter ("show alerts for R2"), and syslog-specific filter ("show syslog alerts for R1") using filter-engine.js; display active filter description and unfiltered total count at workspace/skills/canvas-network-viz/components/alert-card.js
- [X] T027 [US3] Wire alert-card component into a2ui-renderer.js: register "alert-card" component type, build A2UI JSON envelope, emit GAIT log at workspace/skills/canvas-network-viz/lib/a2ui-renderer.js

**Checkpoint**: Alert visualization fully functional. Operators see severity-sorted alert cards with filtering and "all clear" state handling.

---

## Phase 6: User Story 4 - Show Change Management Workflow Status (Priority: P4)

**Goal**: Render ServiceNow change request lifecycle as a visual timeline showing all stages (assess, authorize, implement, review) with current state indication.

**Independent Test**: Ask "show change request CR-12345 status" with ServiceNow data available. Verify an inline timeline renders showing lifecycle stages with current stage highlighted and completed stages marked.

### Implementation for User Story 4

- [X] T028 [P] [US4] Create change-timeline.css with styles for horizontal timeline visualization (stage nodes connected by progress line), stage status indicators (completed checkmark, active pulse, pending gray, failed X), compact multi-CR row layout, and rejection/rollback indicators at workspace/skills/canvas-network-viz/components/change-timeline.css
- [X] T029 [P] [US4] Create change-timeline.js Canvas component that accepts TimelineContent data model (changeRequests[]), renders each ChangeRequestTimeline as a horizontal stage progression (assess/authorize/implement/review), highlights current stage, marks completed stages, shows rejection reason and linked incidents when applicable at workspace/skills/canvas-network-viz/components/change-timeline.js
- [X] T030 [US4] Implement change management data pipeline in data-fetcher.js: fetch CR data from ServiceNow MCP (servicenow_get_change_request, servicenow_list_change_requests), transform into ChangeRequestTimeline[] with stage mapping per data-model.md at workspace/skills/canvas-network-viz/lib/data-fetcher.js
- [X] T031 [US4] Implement multi-CR summary view: when operator requests "show all active change requests", render compact timeline rows with CR number, description, current stage, assignee, and scheduled window at workspace/skills/canvas-network-viz/components/change-timeline.js
- [X] T032 [US4] Implement ServiceNow unavailable handling: when ServiceNow MCP is unreachable, return A2UI error-card indicating ServiceNow is unavailable and suggesting retry at workspace/skills/canvas-network-viz/components/change-timeline.js
- [X] T033 [US4] Wire change-timeline component into a2ui-renderer.js: register "change-timeline" component type, build A2UI JSON envelope, emit GAIT log at workspace/skills/canvas-network-viz/lib/a2ui-renderer.js

**Checkpoint**: Change management timeline fully functional. Single CR and multi-CR views render with rejection/rollback indication.

---

## Phase 7: User Story 5 - Render Path Trace and Diff Visualizations (Priority: P5)

**Goal**: Render hop-by-hop forwarding path diagrams and before/after configuration diff comparisons inline.

**Independent Test**: Ask "trace path from 10.0.1.1 to 10.0.2.1" with routing data available. Verify inline diagram shows hop-by-hop path with interfaces and next-hops labeled. Ask "show config diff for R1" and verify color-coded diff appears.

### Implementation for User Story 5

- [X] T034 [P] [US5] Create path-trace.css with styles for directed path diagram (hop nodes connected by arrows), ECMP parallel branches, interface/next-hop labels, black hole error indicator (red X with failure message), and hop numbering at workspace/skills/canvas-network-viz/components/path-trace.css
- [X] T035 [P] [US5] Create path-trace.js Canvas component that accepts PathTraceContent data model (source, destination, paths[], blackHole), renders hop-by-hop directed graph with per-hop device/interface/next-hop labels, shows ECMP parallel branches with load-sharing indicators, and marks black hole failure points at workspace/skills/canvas-network-viz/components/path-trace.js
- [X] T036 [P] [US5] Create diff-view.css with styles for unified/side-by-side diff display (green background for additions, red for deletions, neutral for context), hunk section headers, line numbers, and long-diff scroll container at workspace/skills/canvas-network-viz/components/diff-view.css
- [X] T037 [P] [US5] Create diff-view.js Canvas component that accepts DiffContent data model (diffType, device, hunks[]), renders DiffHunk sections with headers, renders DiffLine entries with type-based coloring (added green, removed red, context neutral) at workspace/skills/canvas-network-viz/components/diff-view.js
- [X] T038 [US5] Implement path trace data pipeline in data-fetcher.js: fetch routing/forwarding data from pyATS (pyats_show_ip_route) and SuzieQ, trace hop-by-hop path from source to destination, detect ECMP paths and black holes, transform into PathTraceContent per data-model.md at workspace/skills/canvas-network-viz/lib/data-fetcher.js
- [X] T039 [US5] Implement diff data pipeline in data-fetcher.js: fetch current and previous config/routing/ACL snapshots from pyATS (pyats_show_running_config, pyats_show_ip_route, pyats_show_access_lists), compute diff hunks, transform into DiffContent per data-model.md at workspace/skills/canvas-network-viz/lib/data-fetcher.js
- [X] T040 [US5] Wire path-trace and diff-view components into a2ui-renderer.js: register "path-trace" and "diff-view" component types, build A2UI JSON envelopes, emit GAIT logs at workspace/skills/canvas-network-viz/lib/a2ui-renderer.js

**Checkpoint**: Path trace and diff visualizations fully functional. ECMP paths, black hole detection, and config/route/ACL diffs all render inline.

---

## Phase 8: Health Scorecard (Implicit from FR-014/FR-015)

**Goal**: Render aggregated health scorecards with per-device and per-site health scores supporting drill-down, and OSI-layer troubleshooting flow diagrams.

**Independent Test**: Ask "show health scorecard for Site-A" and verify a scorecard renders with per-device health scores and drill-down capability.

### Implementation for Phase 8

- [X] T041 [P] [US1+] Create health-scorecard.css with styles for scorecard grid (site-level summary rows, device-level detail rows), composite health score display (0-100 with color), per-indicator status badges, and drill-down expand/collapse at workspace/skills/canvas-network-viz/components/health-scorecard.css
- [X] T042 [P] [US1+] Create health-scorecard.js Canvas component that accepts ScorecardContent data model (level, entries[]), renders ScorecardEntry rows with overall health color, composite score, HealthIndicator badges, and drill-down toggle from site to device level at workspace/skills/canvas-network-viz/components/health-scorecard.js
- [X] T043 [US1+] Implement health score calculation in data-fetcher.js: fetch CPU, memory, interface, BGP, and OSPF metrics from pyATS/Grafana/Prometheus, compute weighted composite score per data-model.md formula (CPU 20%, memory 20%, interfaces 25%, BGP 20%, OSPF 15%), handle missing indicators by redistributing weights at workspace/skills/canvas-network-viz/lib/data-fetcher.js
- [X] T044 [US1+] Wire health-scorecard component into a2ui-renderer.js: register "health-scorecard" component type, build A2UI JSON envelope, emit GAIT log at workspace/skills/canvas-network-viz/lib/a2ui-renderer.js

**Checkpoint**: Health scorecards render with composite scores and drill-down from site to device level.

---

## Phase 9: Polish & Cross-Cutting Concerns (Artifact Coherence)

**Purpose**: Artifact coherence checklist items and cross-cutting improvements required by Constitution Principle XI.

- [X] T045 [P] Update README.md at repository root: add Canvas/A2UI visualization capability description, update architecture diagram to show Canvas visualization layer, update skill count at /Users/john.capobianco/netclaw/README.md
- [X] T046 [P] Update scripts/install.sh: add any Canvas visualization dependencies (if needed; skill may be zero-dependency JavaScript) at /Users/john.capobianco/netclaw/scripts/install.sh
- [X] T047 [P] Update SOUL.md: add canvas-network-viz skill entry with description and capability summary to the skill listing at /Users/john.capobianco/netclaw/SOUL.md
- [X] T048 [P] Update TOOLS.md: add Canvas/A2UI visualization reference to infrastructure documentation at /Users/john.capobianco/netclaw/TOOLS.md
- [X] T049 [P] Update .env.example: add any new environment variables with descriptions (note: no new credentials expected, but document any Canvas/A2UI configuration variables) at /Users/john.capobianco/netclaw/.env.example
- [X] T050 [P] Update ui/netclaw-visual/: add a new HUD node representing the Canvas visualization capability in the Three.js system topology view at /Users/john.capobianco/netclaw/ui/netclaw-visual/
- [X] T051 [P] Update config/openclaw.json: add canvas-network-viz skill registration if required by OpenClaw skill discovery at /Users/john.capobianco/netclaw/config/openclaw.json
- [X] T052 Verify backwards compatibility: confirm all existing NetGeniusClaw skills and MCP servers remain functional after Canvas/A2UI addition (run existing skill invocations, verify no breakage)
- [X] T053 Run quickstart.md validation: follow the steps in specs/005-canvas-a2ui-integration/quickstart.md to verify end-to-end functionality
- [X] T054 Record GAIT session log for the Canvas/A2UI integration feature completion

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-8)**: All depend on Foundational phase completion
  - US1 (Topology Maps): Can start after Phase 2
  - US2 (Dashboard Panels): Can start after Phase 2 (independent of US1)
  - US3 (Alert Cards): Can start after Phase 2 (independent of US1/US2)
  - US4 (Change Timelines): Can start after Phase 2 (independent of US1-US3)
  - US5 (Path Trace + Diff): Can start after Phase 2 (independent of US1-US4)
  - Health Scorecards: Can start after Phase 2 (shares data pipeline patterns with US1/US2)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (Topology Maps, P1)**: No dependencies on other stories. Uses graph-layout.js, color-scale.js, filter-engine.js from Phase 2.
- **US2 (Dashboard Panels, P2)**: No dependencies on other stories. Uses color-scale.js from Phase 2.
- **US3 (Alert Cards, P3)**: No dependencies on other stories. Uses filter-engine.js from Phase 2.
- **US4 (Change Timelines, P4)**: No dependencies on other stories. ServiceNow-specific.
- **US5 (Path Trace + Diff, P5)**: No dependencies on other stories. Path trace benefits from topology context (US1) but is independently functional.
- **Health Scorecards**: Shares health metric fetching patterns with US1 and US2 but is independently implementable.

### Within Each User Story

- CSS and JS component files can be created in parallel [P]
- Data pipeline implementation depends on data-fetcher.js from Phase 2
- Component wiring into a2ui-renderer.js depends on component and pipeline completion
- GAIT logging depends on gait-logger.js from Phase 2

### Parallel Opportunities

- T003 and T004 (Phase 1) can run in parallel
- T005, T006, T007, T008 have minimal overlap but T006 (data-fetcher) and T007 (gait-logger) can be parallelized
- Within each user story: CSS and JS component creation can run in parallel
- All user stories (Phases 3-8) can proceed in parallel after Phase 2
- All Phase 9 artifact coherence items (T045-T051) can run in parallel

---

## Parallel Example: User Story 1 (Topology Maps)

```bash
# Launch CSS and JS component creation in parallel:
Task: "Create topology-map.css at workspace/skills/canvas-network-viz/components/topology-map.css"
Task: "Create topology-map.js at workspace/skills/canvas-network-viz/components/topology-map.js"

# Then sequentially:
Task: "Implement topology data pipeline in data-fetcher.js"
Task: "Implement site-based clustering logic"
Task: "Implement topology filtering"
Task: "Implement graceful degradation"
Task: "Implement empty-data handling"
Task: "Wire topology-map into a2ui-renderer.js"
```

## Parallel Example: Phase 9 (Artifact Coherence)

```bash
# Launch all artifact updates in parallel:
Task: "Update README.md"
Task: "Update scripts/install.sh"
Task: "Update SOUL.md"
Task: "Update TOOLS.md"
Task: "Update .env.example"
Task: "Update ui/netclaw-visual/"
Task: "Update config/openclaw.json"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T008)
3. Complete Phase 3: User Story 1 - Topology Maps (T009-T016)
4. **STOP and VALIDATE**: Test topology map with "show me the network topology"
5. Deploy/demo if ready - this alone delivers significant visual value

### Incremental Delivery

1. Setup + Foundational -> Foundation ready
2. Add Topology Maps (US1) -> Test independently -> Deploy/Demo (MVP!)
3. Add Dashboard Panels (US2) -> Test independently -> Deploy/Demo
4. Add Alert Cards (US3) -> Test independently -> Deploy/Demo
5. Add Change Timelines (US4) -> Test independently -> Deploy/Demo
6. Add Path Trace + Diffs (US5) -> Test independently -> Deploy/Demo
7. Add Health Scorecards -> Test independently -> Deploy/Demo
8. Polish + Artifact Coherence -> Final release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Topology Maps) + Health Scorecards
   - Developer B: US2 (Dashboard Panels) + US3 (Alert Cards)
   - Developer C: US4 (Change Timelines) + US5 (Path Trace + Diffs)
3. Stories complete and integrate independently
4. Team completes Phase 9 (Artifact Coherence) together

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All visualizations output A2UI JSON per contracts/a2ui-output-contract.md
- All visualization events GAIT-logged per FR-011
- No new MCP servers created; skill consumes existing MCP tools only
- Three.js HUD at ui/netclaw-visual/ remains untouched until Phase 9 (new node added only)
