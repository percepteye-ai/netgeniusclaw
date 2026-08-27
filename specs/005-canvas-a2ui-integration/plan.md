# Implementation Plan: Canvas / A2UI Integration

**Branch**: `005-canvas-a2ui-integration` | **Date**: 2026-03-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-canvas-a2ui-integration/spec.md`

## Summary

Deliver an OpenClaw skill (`canvas-network-viz`) that transforms data from existing MCP servers (pyATS, Grafana, Prometheus, ServiceNow, NetBox, SuzieQ, Batfish) into inline Canvas/A2UI visualizations within the OpenClaw chat interface. Visualization types include topology maps, dashboard panels, alert cards, change timelines, diff views, path traces, and health scorecards. All rendering uses A2UI JSON output format with HTML/CSS/JS Canvas components. This complements the existing Three.js HUD at `ui/netclaw-visual/` without replacing it.

## Technical Context

**Language/Version**: JavaScript (ES2022) / HTML5 / CSS3 for Canvas components; SKILL.md for skill definition
**Primary Dependencies**: OpenClaw Canvas/A2UI framework (rendering primitives), existing MCP servers (data sources)
**Storage**: N/A (stateless visualization — all data fetched on demand from MCP servers)
**Testing**: Manual acceptance testing per user story scenarios; visual regression snapshots
**Target Platform**: OpenClaw chat interface (browser-based Canvas/A2UI rendering)
**Project Type**: Skill + visualization component library
**Performance Goals**: Topology render < 10s for 200 devices (SC-001); dashboard data staleness < 60s (SC-002)
**Constraints**: Must not modify `ui/netclaw-visual/`; must not establish direct device connections; must render inline (no separate tabs); large topologies (500+ nodes) require clustering/pagination
**Scale/Scope**: Networks up to 500 devices, thousands of interfaces, hundreds of alerts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Safety-First Operations | PASS | Read-only visualization; no device commands issued. All data sourced from existing MCP servers. |
| II. Read-Before-Write | PASS | No writes performed. Pure observation/rendering. |
| III. ITSM-Gated Changes | PASS | No production changes. Visualization of CR status is read-only. |
| IV. Immutable Audit Trail | PASS | FR-011 requires GAIT logging of all visualization events. |
| V. MCP-Native Integration | PASS | All data sourced via existing MCP servers. Skill itself is an OpenClaw skill (not a new MCP server). |
| VI. Multi-Vendor Neutrality | PASS | Visualization layer is vendor-agnostic; vendor-specific data handled by underlying MCP servers. |
| VII. Skill Modularity | PASS | Single skill (`canvas-network-viz`) with well-defined scope: visualization rendering. |
| VIII. Verify After Every Change | PASS | No changes to verify. Read-only visualization. |
| IX. Security by Default | PASS | No new credentials required; uses existing MCP server auth. |
| X. Observability as a First-Class Citizen | PASS | This feature IS the observability visualization layer. Three.js HUD update required per checklist. |
| XI. Artifact Coherence | REQUIRES ACTION | Must update: README.md, install.sh, SOUL.md, SKILL.md, .env.example, TOOLS.md, config/openclaw.json, ui/netclaw-visual/ |
| XII. Documentation-as-Code | REQUIRES ACTION | SKILL.md must be created for the new skill. |
| XIII. Credential Safety | PASS | No new credentials introduced. |
| XIV. Human-in-the-Loop | PASS | No external communications. Visualization is local to the chat session. |
| XV. Backwards Compatibility | PASS | Additive only. Existing skills and MCP servers untouched. Three.js HUD unmodified (new node added, not changed). |
| XVI. Spec-Driven Development | PASS | Following full SDD workflow. |

**Gate Result**: PASS (with 2 action items tracked for implementation phase)

## Project Structure

### Documentation (this feature)

```text
specs/005-canvas-a2ui-integration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
workspace/skills/canvas-network-viz/
├── SKILL.md                        # Skill documentation (purpose, tools, workflow)
├── components/
│   ├── topology-map.js             # Graph visualization (nodes, edges, health coloring)
│   ├── topology-map.css            # Topology styles
│   ├── dashboard-panel.js          # Metric display panels (gauges, counters, status)
│   ├── dashboard-panel.css         # Dashboard styles
│   ├── alert-card.js               # Severity-colored alert cards
│   ├── alert-card.css              # Alert card styles
│   ├── change-timeline.js          # CR lifecycle timeline visualization
│   ├── change-timeline.css         # Timeline styles
│   ├── diff-view.js                # Config/route/ACL diff visualization
│   ├── diff-view.css               # Diff view styles
│   ├── path-trace.js               # Hop-by-hop forwarding path diagram
│   ├── path-trace.css              # Path trace styles
│   ├── health-scorecard.js         # Aggregated health scores with drill-down
│   └── health-scorecard.css        # Scorecard styles
├── lib/
│   ├── a2ui-renderer.js            # A2UI JSON output builder
│   ├── data-fetcher.js             # MCP server data retrieval abstraction
│   ├── graph-layout.js             # Force-directed / hierarchical layout engine
│   ├── color-scale.js              # Health-to-color mapping (green/amber/red)
│   ├── filter-engine.js            # Scope filtering (device, site, role, severity, time)
│   └── gait-logger.js              # GAIT audit event emitter for visualization events
└── tests/
    ├── topology-map.test.js        # Topology rendering tests
    ├── dashboard-panel.test.js     # Dashboard rendering tests
    ├── alert-card.test.js          # Alert card rendering tests
    ├── data-fetcher.test.js        # Data fetching tests
    └── filter-engine.test.js       # Filter logic tests
```

**Structure Decision**: Single skill directory under `workspace/skills/canvas-network-viz/` following the existing NetGeniusClaw skill pattern. Components are organized by visualization type with shared library utilities. This is NOT an MCP server — it is a skill that consumes existing MCP server data and renders A2UI output.

## Complexity Tracking

No constitution violations requiring justification. All principles pass or have tracked action items for the implementation phase.
