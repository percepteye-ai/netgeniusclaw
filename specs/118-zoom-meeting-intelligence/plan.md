# Implementation Plan: NetGeniusClaw for Zoom — Meeting Intelligence (MVP)

**Branch**: `118-zoom-meeting-intelligence` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/118-zoom-meeting-intelligence/spec.md`

## Summary

Give the Border Claw a new sensory/human-interface surface: Zoom meetings, built on Realtime Media
Streams (RTMS) rather than a Meeting SDK bot (Zoom reserves Meeting SDK for human participants). A new
MCP server, `zoom-rtms-mcp`, ingests per-meeting transcript/chat/active-speaker/screen-share signals
via Zoom's official RTMS SDK into a bounded, in-memory live-context buffer, and runs a deterministic
extractor that recognizes present-tense, first-person investigation requests (location + technology +
time-window). Recognized requests are forwarded over a new loopback-only, restricted channel
(`bgp/federation/zoom_channel.py`, modeled on the existing `EdgeChannel`/`EDGE_METHODS` pattern) to the
Border daemon, which autonomously triggers an agent turn via the existing `run_agent_turn()` — the
same mechanism `chat.py` already uses for inbound peer chat — and pushes the synthesized,
evidence-backed answer back. A companion WebSocket on `zoom-rtms-mcp` feeds a Zoom App side panel
(avatar + live status + results, Collaborate/Guest Mode) and, optionally, a Layers API camera overlay
on a consenting participant's own video. The official Zoom Meetings MCP is registered as a remote/
OAuth integration for historical meeting correlation. No new write-approval mechanism is introduced —
the extractor's classification is the only new safety-relevant logic; any actual configuration change
still passes through NetGeniusClaw's existing device-write approval gate unchanged.

## Technical Context

**Language/Version**: Python 3.10+ (`zoom-rtms-mcp`, `bgp/federation/zoom_channel.py` — matches every
other NetGeniusClaw MCP server and the existing federation daemon); JavaScript (ES2022) for the Zoom App
frontend (`ui/netclaw-zoom-app/`), consistent with the Zoom Apps SDK's browser runtime.
**Primary Dependencies**: FastMCP (MCP framework, matching repo convention), Zoom's official RTMS
Python SDK (research.md R4), Zoom Apps SDK (`@zoom/appssdk`, browser-side, for Collaborate Mode/Guest
Mode/Layers API), existing `bgp/federation/*` modules (`gateway.py`'s `run_agent_turn`, `edge.py`'s
channel pattern as a template, GAIT emission helpers already used by `chat.py`/`invocation.py`).
**Storage**: N/A — `MeetingSession`/`LiveContextBuffer`/avatar state are in-memory only inside
`zoom-rtms-mcp`, discarded at meeting end (FR-014); `InvestigationRequest`/`ApprovalDecision` records
ride the existing GAIT git-based audit trail (no new database); `HistoricalMeetingReference` data is
never persisted, fetched live from the official Zoom MCP per call.
**Testing**: pytest, matching `tests/n2n/test_*` convention for the new `zoom_channel.py` module; a
parallel `mcp-servers/zoom-rtms-mcp/tests/` for the extractor and MCP tool surface.
**Target Platform**: Linux server (Border host) for `zoom-rtms-mcp` and `zoom_channel.py`; browser
(inside the Zoom client's embedded webview) for the Zoom App panel.
**Project Type**: Multi-component addition to an existing single-repo project — one new MCP server,
one new Border-daemon module, one new browser-facing UI surface, one new skill, one new external/
remote MCP registration. No new top-level service boundary.
**Performance Goals**: Panel avatar-state updates and investigation results should reach all current
viewers within a short, perceptible delay (SC-009) — no hard numeric target set in the spec; informed
by NetGeniusClaw's existing turn-latency work (specs 116/117: ~9s cold / ~3.9s warm per turn) as the
dominant cost, not transport latency.
**Constraints**: No independent video-tile participant, no synthesized/injected meeting audio
(FR-016) — a hard scope boundary, not a performance constraint. Live buffer is bounded (size/duration
TBD at `/speckit.tasks`) per spec Assumptions ("recent minutes," not full meeting duration).
**Scale/Scope**: MVP handles one or a small number of concurrently listened-to meetings per Border
instance; no multi-tenant/multi-Border sharding is in scope.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design below.*

| Principle | Assessment |
|---|---|
| I–III (Safety-First, Read-Before-Write, ITSM-Gated) | **Pass, unchanged.** This feature adds no new device-write path; any write attempt still flows through the existing, untouched device-level approval gate (research.md R7). |
| IV (Immutable Audit Trail) | **Pass.** `InvestigationRequest`/`ApprovalDecision` ride the existing GAIT mechanism (data-model.md); no new store. |
| V (MCP-Native Integration) | **Pass.** `zoom-rtms-mcp` is a proper FastMCP server with `tools/list`/`tools/call`. The internal `zoom_channel.py` is NCFED-internal transport, not itself an MCP server — same treatment `edge.py`/`internal_channel.py` already get. |
| VI (Multi-Vendor Neutrality) | **N/A** — no vendor device logic here; routing still delegates to whichever Member Claws are already registered. |
| VII (Skill Modularity) | **Pass.** `zoom-meeting-context` skill has one job: recognize + correlate historical meetings; it delegates investigation execution to the existing routing path rather than duplicating it. |
| VIII (Verify After Every Change) | **N/A** — no device changes originate from this feature itself. |
| IX (Security by Default) | **Pass.** New `zoom_channel.py` uses an explicit method allowlist (`ZOOM_METHODS`, contracts/zoom-channel-internal.md), least-privilege, loopback-only. |
| X (Observability) | **Action required at tasks/implement time**: `ui/netclaw-visual/` HUD gains a node reflecting Zoom listening status, per the checklist. |
| XI (Full-Stack Artifact Coherence) | **Action required at tasks/implement time** (not a plan-time violation): README.md, `scripts/lib/catalog.sh`, `scripts/lib/install-steps.sh`, `scripts/verify-catalog-coverage.py`, `ui/netclaw-visual/`, `SOUL.md`, `workspace/skills/zoom-meeting-context/SKILL.md`, `.env.example`, `TOOLS.md`, `config/openclaw.json` (for `zoom-rtms-mcp` only — the official Zoom MCP is external/remote per R6 and doesn't get a config entry), `mcp-servers/zoom-rtms-mcp/README.md`, `EXTERNAL_INTEGRATIONS` in `scripts/verify-inventory-counts.py`. |
| XII (Documentation-as-Code) | Satisfied by the above, same PR. |
| XIII (Credential Safety) | **Pass, by design.** `ZOOM_CLIENT_ID`/`ZOOM_CLIENT_SECRET`/`ZOOM_ACCOUNT_ID`/`ZOOM_RTMS_WEBHOOK_SECRET` (and the Zoom MCP's own credential, once confirmed) go in `.env`, documented (no values) in `.env.example`. |
| XIV (Human-in-the-Loop for External Communications) | **N/A directly** — this feature's outputs render inside the Zoom App panel (a NetClaw-owned surface), not an outbound message to a third-party channel like Slack/WebEx. |
| XV (Backwards Compatibility) | **Pass.** No existing MCP tool schema, env var, or shared interface changes; `run_agent_turn()` is called with existing parameters only (no new `origin` value introduced — research.md decided against threading a new origin through gateway.py, since the panel wants default/structured composition, not voice-terse). |
| XVI (Spec-Driven Development) | **Pass** — this plan follows a ratified spec. |
| XVII (Milestone Documentation) | Deferred to post-implementation, per existing workflow. |

**Result**: No violations requiring justification. Complexity Tracking table below is empty.

## Project Structure

### Documentation (this feature)

```text
specs/118-zoom-meeting-intelligence/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── zoom-rtms-mcp-tools.md
│   ├── zoom-channel-internal.md
│   └── zoom-app-panel-feed.md
└── tasks.md             # Phase 2 output (/speckit.tasks — not created here)
```

### Source Code (repository root)

```text
mcp-servers/zoom-rtms-mcp/
├── server.py                 # FastMCP entrypoint — tools per contracts/zoom-rtms-mcp-tools.md
├── rtms_listener.py           # Zoom RTMS SDK session lifecycle per meeting (research.md R4)
├── webhook.py                 # Receives Zoom's RTMS-start/meeting-end webhook (research.md R5)
├── extractor.py               # Deterministic intent/entity recognition (research.md R2)
├── panel_feed.py               # Companion WebSocket for the Zoom App panel (research.md R3, contracts/zoom-app-panel-feed.md)
├── zoom_channel_client.py     # Loopback client side of bgp/federation/zoom_channel.py
├── README.md
└── tests/
    ├── test_extractor.py
    └── test_panel_feed.py

mcp-servers/protocol-mcp/bgp/federation/
└── zoom_channel.py            # Border-side handler — ZOOM_METHODS, calls run_agent_turn (research.md R1)

mcp-servers/protocol-mcp/tests/
└── test_zoom_channel.py

ui/netclaw-zoom-app/
├── manifest.json               # Zoom App manifest (Collaborate Mode, Guest Mode, Layers API entitlements)
├── panel.html / panel.js       # Side-panel UI: avatar, status, investigation results
└── overlay.js                  # Layers API Camera-mode overlay (User Story 5)

workspace/skills/zoom-meeting-context/
└── SKILL.md                   # Historical-correlation skill (User Story 2) — calls zoom_search_historical_meetings

docs/
├── ZOOM-MEETING-INTELLIGENCE.md  # NEW — consolidated operator setup guide (Polish phase)
└── (existing ADDING-AN-MCP.md / N2N-RISK.md referenced, not modified)
```

**Structure Decision**: New MCP server (`mcp-servers/zoom-rtms-mcp/`) plus one new module inside the
existing federation daemon (`bgp/federation/zoom_channel.py`, alongside `edge.py`/`internal_channel.py`
— same subsystem specs 057/060/063/066 already extend) plus one new browser-facing UI surface
(`ui/netclaw-zoom-app/`, separate from the Three.js HUD in `ui/netclaw-visual/`, which gets only a
status node per Principle X). No new top-level service boundary or repository.

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none — no gate violations)* | — | — |
