# Phase 1 Data Model: Siri Voice Window Tuning and Origin Marker (Pass 3 of 3)

This feature introduces no new persistent entity and no schema change. It adjusts one existing
constant's value and threads one existing, already-defined concept (`origin`, spec 116) one hop
further through an existing request.

## Spoken-answer window (existing constant, value changes only)

- **What it is**: `askBorderFastWindow` in `ask_border_headless.dart` — a `Duration` constant, not
  persisted anywhere, read fresh on every headless process launch.
- **Change**: value only, `18` seconds → `12` seconds (research.md R1). No new field, no new
  storage, no migration.

## Voice-origin marker (existing concept, new transport hop)

- **What it is**: the string `"voice"`, already a first-class value `run_agent_turn(origin=...)`
  recognizes (spec 116, `_normalize_origin()`). Not a new entity — this feature adds one new place
  the value is produced (the phone's Siri-originated ask request) and one new place it is read and
  forwarded (the Border's ask-request handler).
- **Representation on the wire**: an optional `"origin"` string field on the existing
  `n2n/edge/ask` JSON-RPC request (contracts/edge-ask-origin-field.md). Absent for any non-Siri
  request, exactly like the existing optional `attachment` field.
- **Lifecycle**: request-scoped only. Not stored in `ConversationStore` (the phone's local turn
  history), not stored in `delegated_task` (the Border's task table) beyond whatever `run_agent_turn`
  itself already does for `origin` retention (spec 116 FR-013, reusing an existing field — no new
  column here). This feature does not add a new place origin is remembered; it only makes sure it
  reaches the place spec 116 already built to consume it.
