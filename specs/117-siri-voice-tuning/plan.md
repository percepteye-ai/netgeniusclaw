# Implementation Plan: Siri Voice Window Tuning and Origin Marker (Pass 3 of 3)

**Branch**: `117-siri-voice-tuning` | **Date**: 2026-08-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/117-siri-voice-tuning/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Pass 2 (spec 116) cut the Border's real per-turn latency from ~38s to ~9s cold/~3.9s warm and built
(but did not wire up) voice-aware answer composition via `run_agent_turn(origin="voice")`. This pass
closes both gaps for real: (1) shrink the phone's flat 18s `askBorderFastWindow` to 12s, sized
against Pass 2's actual measurements with margin, and (2) thread a new optional `origin` field on
the existing `n2n/edge/ask` wire request from `ask_border_headless.dart` (Siri's headless entry
point) through the Border's `service.py::_edge_on_ask()` handler into the already-built
`run_agent_turn(origin=...)` call. Both changes are additive and backward-compatible — no existing
caller changes behavior. Final verification (User Story 3) requires a real, enrolled, unlocked
phone and is the one part of this feature that cannot be completed from an automated test run.

## Technical Context

**Language/Version**: Dart 3.x / Flutter (SDK `^3.12.2` per `mobile/netclaw-mobile/pubspec.yaml`);
Python 3.10+ (`mcp-servers/protocol-mcp/bgp/federation/service.py`) — same stack as specs 066-116,
unchanged.
**Primary Dependencies**: None new. Reuses `EdgeAskClient`/`EdgeRpcSource` (Dart, `edge_ask_client.dart`),
`run_agent_turn()`'s existing `origin` parameter (Python, spec 116), `TaskManager` (spec 053).
**Storage**: N/A — no new persisted state (data-model.md: value-only constant change, request-scoped
marker with no new storage).
**Testing**: `flutter test` (`mobile/netclaw-mobile/test/ask_border_headless_test.dart`), `pytest`
(`tests/n2n/test_edge_ask.py`) — both existing suites, extended, not new frameworks.
**Target Platform**: iOS 16+ (AppIntents, unchanged from spec 111) talking to the Linux Border host
over the existing NCFED edge WebSocket channel (feature 066).
**Project Type**: mobile-app + existing Border service (same repo layout as every prior 06x-11x
mobile spec).
**Performance Goals**: A cold (first-in-session) Siri question should be spoken, not fall back to
acknowledgment, in the large majority of real attempts (SC-001); a warm (second+) question, nearly
always (SC-002) — both against the new 12s window and Pass 2's ~9s/~3.9s measured Border latency.
**Constraints**: Zero behavior change for any non-Siri caller (FR-004); zero behavior change for a
Border build that doesn't yet read the new field (FR-005); no new wire method, no schema change.
**Scale/Scope**: One Dart constant value change, one new optional Dart method parameter, one new
optional Python handler parameter read — the smallest change that closes the two gaps Pass 2 left
open. Explicitly excludes touching `gateway.py`/`gateway_ws.py` (spec 116's own dispatch-mechanism
files) and excludes any new prioritization/queueing work (spec 116 already investigated and
rejected that).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Safety-First Operations**: N/A — no device configuration changes; this is a latency/UX
  tuning feature over an existing, already-authenticated phone-to-Border channel.
- **II. Read-Before-Write**: N/A — no state mutation beyond the existing `delegated_task`/
  `ConversationStore` writes spec 067 already performs identically today.
- **IV. Immutable Audit Trail**: Satisfied — `origin` retention for after-the-fact inspection reuses
  spec 116's existing FR-013 mechanism; no new audit surface needed or added.
- **V. MCP-Native Integration**: N/A — this is NCFED edge-channel and mobile-app code, not a new MCP
  server or tool.
- **VII. Skill Modularity**: N/A — no skill changes.
- **XI. Full-Stack Artifact Coherence**: Satisfied — this plan's own agent-context update
  (`update-agent-context.sh`) keeps `CLAUDE.md` in sync, per the same discipline every prior spec in
  this series followed.

No violations. Gate passes without complexity justification.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
mobile/netclaw-mobile/
├── lib/ncfed/
│   ├── ask_border_headless.dart     # askBorderFastWindow constant (18s → 12s); runAskBorder()
│   │                                 # passes origin: 'voice' to EdgeAskClient.ask()
│   └── edge_ask_client.dart         # ask() gains optional `origin` param, wire field
└── test/
    └── ask_border_headless_test.dart  # extended: asserts origin sent, window value

mcp-servers/protocol-mcp/bgp/federation/
└── service.py                       # _edge_on_ask() reads params.get("origin"), forwards to
                                       # run_agent_turn(origin=...) — the one Border-side edit

tests/n2n/
└── test_edge_ask.py                 # extended: origin field reaches run_agent_turn unchanged;
                                       # absent origin is byte-identical to today
```

**Structure Decision**: Same two-sided layout every 066+ mobile spec uses — Dart changes in
`mobile/netclaw-mobile/`, the one Border-side change in `mcp-servers/protocol-mcp/bgp/federation/`.
No new directories, no new files beyond what the spec's own docs need — this is a small, additive
change to four existing files plus their existing test suites.

## Complexity Tracking

*No constitution violations — this section is not applicable.*
